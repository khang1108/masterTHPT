"""Adaptive-facing helpers built on top of the shared knowledge-graph engine."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, Field

from master.data.knowledge import KnowledgeGraph


def _dedupe_preserve_order(values: Sequence[str]) -> list[str]:
    """Remove duplicates from a topic sequence while keeping first-seen order."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


class TopicContext(BaseModel):
    """Resolved topic metadata used by the adaptive selector."""

    topic: str
    resolved_topic: str | None = None
    label: str
    mastery: float | None = None
    prerequisites: list[str] = Field(default_factory=list)
    prerequisite_labels: list[str] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)


class AdaptiveGraph:
    """Thin adapter that exposes KG context in adaptive-learning terms."""

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph | None = None,
        *,
        graph_data_dir: str | Path | None = None,
    ) -> None:
        """Create an adaptive KG facade.

        Args:
            knowledge_graph: Optional pre-built KG instance, useful for tests.
            graph_data_dir: Optional path to exported KG JSON files when a KG
                instance is not injected.
        """

        if knowledge_graph is not None:
            self.knowledge_graph = knowledge_graph
            return

        data_dir = Path(graph_data_dir) if graph_data_dir else self.default_outputs_dir()
        self.knowledge_graph = KnowledgeGraph(data_dir=data_dir)

    @staticmethod
    def default_outputs_dir() -> Path:
        """Locate the default graph-export directory inside the repo."""

        return Path(__file__).resolve().parents[2] / "data" / "knowledge" / "outputs"

    def resolve_topic(self, topic: str) -> str | None:
        """Resolve a raw topic string into a KG concept id when possible."""

        return self.knowledge_graph.resolve_concept_id(topic)

    def resolve_topics(self, topics: Sequence[str]) -> list[str]:
        """Resolve a sequence of topics and drop entries that cannot be mapped."""

        resolved = [self.resolve_topic(topic) for topic in topics]
        return _dedupe_preserve_order(
            [topic_id for topic_id in resolved if topic_id is not None]
        )

    def canonical_or_raw_topics(self, topics: Sequence[str]) -> list[str]:
        """Prefer canonical KG ids, but preserve unresolved raw topics."""

        canonical: list[str] = []
        for topic in topics:
            canonical.append(self.resolve_topic(topic) or topic)
        return _dedupe_preserve_order(canonical)

    def label_for(self, topic: str) -> str:
        """Return the KG label for a topic, falling back to the raw value."""

        metadata = self.knowledge_graph.get_kc_metadata(topic)
        if not metadata:
            return topic
        return metadata.get("label", topic)

    def prerequisite_topics(self, topic: str) -> list[str]:
        """Return prerequisite topic ids for a topic when available."""

        return self.knowledge_graph.get_prerequisites(topic)

    def prerequisite_labels(self, topic: str) -> list[str]:
        """Return prerequisite labels for display and explanation."""

        return self.knowledge_graph.labels_for(self.prerequisite_topics(topic))

    def related_topics(self, topic: str) -> list[str]:
        """Return related KG neighbors for a topic."""

        return self.knowledge_graph.get_related_kcs(topic)

    def topic_contexts(
        self,
        topics: Sequence[str],
        mastery_scores: dict[str, float],
    ) -> list[TopicContext]:
        """Build display-friendly topic contexts for adaptive decisions.

        Args:
            topics: Raw or canonical topic ids to resolve.
            mastery_scores: Per-topic mastery map from the learner profile.

        Returns:
            A list of resolved topic contexts enriched with labels, prerequisite
            metadata, and related topics from the KG.
        """

        contexts: list[TopicContext] = []
        for topic in self.canonical_or_raw_topics(topics):
            contexts.append(
                TopicContext(
                    topic=topic,
                    resolved_topic=self.resolve_topic(topic),
                    label=self.label_for(topic),
                    mastery=mastery_scores.get(topic),
                    prerequisites=self.prerequisite_topics(topic),
                    prerequisite_labels=self.prerequisite_labels(topic),
                    related_topics=self.related_topics(topic),
                )
            )
        return contexts

    def learning_targets(
        self,
        weak_topics: Sequence[str],
        mastery_scores: dict[str, float],
        *,
        threshold: float = 0.6,
        max_targets: int = 5,
    ) -> list[TopicContext]:
        """Return prioritized weak topics plus foundational gaps from the KG.

        Args:
            weak_topics: Topics currently identified as weak in the profile.
            mastery_scores: Per-topic mastery map from the learner profile.
            threshold: Gap threshold passed through to the KG gap finder.
            max_targets: Maximum number of prioritized targets to return.

        Returns:
            A compact list of topic contexts that mixes direct weak topics with
            prerequisite gaps that should be addressed first.
        """

        canonical_weak = self.canonical_or_raw_topics(weak_topics)
        gaps = self.knowledge_graph.find_knowledge_gaps(
            canonical_weak,
            mastery_scores=mastery_scores,
            threshold=threshold,
        )
        prioritized = _dedupe_preserve_order([*gaps, *canonical_weak])[:max_targets]
        return self.topic_contexts(prioritized, mastery_scores)
