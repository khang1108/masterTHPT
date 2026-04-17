"""Knowledge-graph engine built around exported textbook KG JSON files.

The extraction notebook writes graph exports such as
`master/data/knowledge/outputs/merged_graph_10.json`. This module turns those
files into a reusable query layer for prerequisite lookup, related-topic
discovery, and adaptive-learning path planning.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import deque
from pathlib import Path
from typing import Iterable, Sequence

import networkx as nx
from pydantic import BaseModel, Field


def _normalize_lookup_key(value: str) -> str:
    """Normalize topic-like text into a stable ASCII key for matching."""

    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    uppercase = without_accents.upper()
    collapsed = re.sub(r"[^A-Z0-9]+", "_", uppercase).strip("_")
    return collapsed


def _candidate_aliases(value: str) -> list[str]:
    """Generate conservative aliases for an identifier or display label."""

    normalized = _normalize_lookup_key(value)
    if not normalized:
        return []

    aliases = [normalized]
    if normalized.startswith("C_"):
        aliases.append(normalized.removeprefix("C_"))
    else:
        aliases.append(f"C_{normalized}")
    return aliases


class Node(BaseModel):
    """Typed KG node metadata."""

    id: str = Field(
        ...,
        description="Canonical knowledge-component identifier, often prefixed with C_.",
    )
    label: str = Field(..., description="Human-readable concept label.")
    type: str = Field(..., description="CONCEPT, THEOREM, or FORMULA.")
    description: str = Field(..., description="Short description with LaTeX preserved.")
    grade: int | None = Field(default=None, description="Optional school grade.")
    source_title: str | None = Field(
        default=None,
        description="Source textbook title when available.",
    )


class Edge(BaseModel, frozen=True):
    """Typed KG edge metadata."""

    source: str = Field(..., description="Upstream concept identifier.")
    target: str = Field(..., description="Downstream concept identifier.")
    relation: str = Field(..., description="REQUIRES, PART_OF, or RELATED_TO.")
    rationale: str | None = Field(
        default=None,
        description="Optional extraction rationale for the relationship.",
    )


class KnowledgeGraph:
    """Query layer over textbook knowledge-graph exports.

    The graph is stored as a directed NetworkX graph where the exported edge
    direction is preserved: prerequisite/parent concepts point to dependent or
    finer-grained concepts.
    """

    RELATION_PRIORITY = {
        "REQUIRES": 3,
        "PART_OF": 2,
        "RELATED_TO": 1,
    }

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.graph = nx.DiGraph()
        self.kc_metadata: dict[str, Node] = {}
        self.alias_to_id: dict[str, str] = {}

        if data_dir is not None:
            self.load_from_directory(data_dir)

    def load_from_directory(self, data_dir: str | Path) -> bool:
        """Load graph exports from a directory.

        The loader prefers `merged_graph_all.json` when present, otherwise it
        ingests every `merged_graph*.json` file and unions the results.
        """

        directory = Path(data_dir)
        if not directory.exists():
            raise FileNotFoundError(f"Knowledge-graph directory not found: {directory}")

        preferred = directory / "merged_graph_all.json"
        if preferred.exists():
            files = [preferred]
        else:
            files = sorted(directory.glob("merged_graph*.json"))

        if not files:
            raise FileNotFoundError(
                f"No merged graph exports found under {directory}"
            )

        for path in files:
            self.load_from_file(path)

        self._refresh_aliases()
        return True

    def load_from_file(self, path: str | Path) -> None:
        """Load a single graph export into the in-memory graph."""

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        for raw_node in payload.get("nodes", []):
            node = Node.model_validate(raw_node)
            self._upsert_node(node)
        for raw_edge in payload.get("edges", []):
            edge = Edge.model_validate(raw_edge)
            self._upsert_edge(edge)

    def _upsert_node(self, node: Node) -> None:
        """Insert or replace node metadata in both caches."""

        self.kc_metadata[node.id] = node
        self.graph.add_node(node.id, **node.model_dump())

    def _upsert_edge(self, edge: Edge) -> None:
        """Insert an edge, preserving the strongest relation if duplicated."""

        if self.graph.has_edge(edge.source, edge.target):
            current = self.graph.edges[edge.source, edge.target]
            current_relation = current.get("relation", "RELATED_TO")
            if self.RELATION_PRIORITY.get(edge.relation, 0) < self.RELATION_PRIORITY.get(
                current_relation, 0
            ):
                return

        self.graph.add_edge(edge.source, edge.target, **edge.model_dump())

    def _refresh_aliases(self) -> None:
        """Rebuild normalized aliases for ids and human-readable labels."""

        self.alias_to_id.clear()
        for node in self.kc_metadata.values():
            for candidate in (node.id, node.label, node.source_title or ""):
                for alias in _candidate_aliases(candidate):
                    self.alias_to_id.setdefault(alias, node.id)

    def resolve_concept_id(self, concept: str) -> str | None:
        """Resolve a raw topic string to the closest known KG node id."""

        if concept in self.kc_metadata:
            return concept

        for alias in _candidate_aliases(concept):
            resolved = self.alias_to_id.get(alias)
            if resolved:
                return resolved

        normalized = _normalize_lookup_key(concept)
        if not normalized:
            return None

        tokens = {token for token in normalized.split("_") if len(token) >= 4}
        if not tokens:
            return None

        best_id: str | None = None
        best_score = 0
        for node in self.kc_metadata.values():
            haystack = {
                token for token in _normalize_lookup_key(node.id).split("_") if token
            }
            haystack.update(
                token for token in _normalize_lookup_key(node.label).split("_") if token
            )
            overlap = len(tokens & haystack)
            if overlap > best_score and overlap >= 2:
                best_score = overlap
                best_id = node.id
        return best_id

    def get_kc_metadata(self, kc_id: str) -> dict | None:
        """Return node metadata for a resolved KC identifier."""

        resolved = self.resolve_concept_id(kc_id)
        if not resolved:
            return None
        node = self.kc_metadata.get(resolved)
        return node.model_dump() if node else None

    def get_prerequisites(self, kc_id: str, depth: int = -1) -> list[str]:
        """Return prerequisite concepts for a target concept.

        `REQUIRES` and `PART_OF` edges are both treated as dependency signals:
        parents and prerequisite concepts are traversed in the reverse direction.
        """

        resolved = self.resolve_concept_id(kc_id)
        if not resolved or resolved not in self.graph:
            return []

        dependency_edges = {"REQUIRES", "PART_OF"}
        queue: deque[tuple[str, int]] = deque([(resolved, 0)])
        visited: set[str] = {resolved}
        prerequisites: list[str] = []

        while queue:
            current, level = queue.popleft()
            if depth >= 0 and level >= depth:
                continue

            for predecessor in self.graph.predecessors(current):
                relation = self.graph.edges[predecessor, current].get("relation")
                if relation not in dependency_edges or predecessor in visited:
                    continue
                visited.add(predecessor)
                prerequisites.append(predecessor)
                queue.append((predecessor, level + 1))

        return prerequisites

    def get_prerequisite_chain(self, kc_id: str) -> list[str]:
        """Return prerequisite concepts in topological learning order."""

        resolved = self.resolve_concept_id(kc_id)
        if not resolved:
            return []

        prerequisites = set(self.get_prerequisites(resolved))
        if not prerequisites:
            return []

        induced_nodes = prerequisites | {resolved}
        subgraph = self.graph.subgraph(induced_nodes)
        try:
            ordered = list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            ordered = list(prerequisites)
        return [node for node in ordered if node != resolved]

    def find_knowledge_gaps(
        self,
        weak_kcs: Sequence[str],
        mastery_scores: dict[str, float],
        threshold: float = 0.6,
    ) -> list[str]:
        """Trace weak concepts backward and return foundational gaps."""

        candidates: set[str] = set()
        for kc in weak_kcs:
            resolved = self.resolve_concept_id(kc) or kc
            candidates.add(resolved)
            candidates.update(self.get_prerequisites(resolved))

        def mastery_for(node_id: str) -> float:
            for candidate in {node_id, _normalize_lookup_key(node_id)}:
                if candidate in mastery_scores:
                    return mastery_scores[candidate]
            return 0.0

        gaps = [node_id for node_id in candidates if mastery_for(node_id) < threshold]
        return sorted(gaps, key=lambda node_id: (mastery_for(node_id), node_id))

    def get_learning_path(
        self,
        target_kcs: Sequence[str],
        current_mastery: dict[str, float],
        mastery_threshold: float = 0.75,
    ) -> list[str]:
        """Build a topological learning path for unresolved prerequisite chains."""

        resolved_targets = [
            resolved
            for target in target_kcs
            if (resolved := self.resolve_concept_id(target)) is not None
        ]
        if not resolved_targets:
            return []

        closure: set[str] = set(resolved_targets)
        for target in resolved_targets:
            closure.update(self.get_prerequisites(target))

        subgraph = self.graph.subgraph(closure)
        try:
            ordered = list(nx.topological_sort(subgraph))
        except nx.NetworkXUnfeasible:
            ordered = sorted(closure)

        def mastery_for(node_id: str) -> float:
            return current_mastery.get(node_id, current_mastery.get(_normalize_lookup_key(node_id), 0.0))

        return [
            node_id
            for node_id in ordered
            if mastery_for(node_id) < mastery_threshold
        ]

    def get_related_kcs(self, kc_id: str) -> list[str]:
        """Return neighbors connected through RELATED_TO edges."""

        resolved = self.resolve_concept_id(kc_id)
        if not resolved or resolved not in self.graph:
            return []

        related: set[str] = set()
        for neighbor in self.graph.successors(resolved):
            if self.graph.edges[resolved, neighbor].get("relation") == "RELATED_TO":
                related.add(neighbor)
        for neighbor in self.graph.predecessors(resolved):
            if self.graph.edges[neighbor, resolved].get("relation") == "RELATED_TO":
                related.add(neighbor)
        return sorted(related)

    def get_all_kcs_for_grade(self, grade: int) -> list[str]:
        """Return all KC ids tagged with a given school grade."""

        return sorted(
            [
                node.id
                for node in self.kc_metadata.values()
                if node.grade == grade
            ]
        )

    def labels_for(self, concept_ids: Iterable[str]) -> list[str]:
        """Convert concept ids into display labels when possible."""

        labels: list[str] = []
        for concept_id in concept_ids:
            node = self.kc_metadata.get(concept_id)
            labels.append(node.label if node else concept_id)
        return labels
