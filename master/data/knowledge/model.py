"""Typed schemas for textbook-to-knowledge-graph extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


NodeType = Literal["CONCEPT", "THEOREM", "FORMULA", "EXAMPLE", "METHOD"]
RelationType = Literal["REQUIRES", "PART_OF", "RELATED_TO"]


class KnowledgeNode(BaseModel):
    """A canonical knowledge component extracted from textbook content."""

    id: str = Field(
        ...,
        description="Canonical uppercase identifier, for example C_HAM_SO_BAC_HAI.",
    )
    label: str = Field(..., description="Human-readable Vietnamese label.")
    type: NodeType = Field(..., description="High-level node category.")
    description: str = Field(
        ...,
        description="Short description that preserves important mathematical meaning.",
    )
    grade: int | None = Field(
        default=None,
        ge=10,
        le=12,
        description="Optional school grade inferred from the source textbook.",
    )
    source_title: str | None = Field(
        default=None,
        description="The source section title that introduced the node.",
    )


class KnowledgeEdge(BaseModel):
    """A typed semantic relationship between two knowledge nodes."""

    source: str = Field(..., description="Identifier of the source node.")
    target: str = Field(..., description="Identifier of the target node.")
    relation: RelationType = Field(..., description="Type of semantic relation.")
    rationale: str | None = Field(
        default=None,
        description="Short justification grounded in the source chunk.",
    )


class ExtractionDocument(BaseModel):
    """Structured response expected from the LLM for one markdown chunk."""

    chunk_id: str = Field(..., description="Stable identifier for the source chunk.")
    summary: str = Field(
        ...,
        description="Compact summary of what this chunk teaches.",
    )
    nodes: list[KnowledgeNode] = Field(
        default_factory=list,
        description="Knowledge nodes extracted from the chunk.",
    )
    edges: list[KnowledgeEdge] = Field(
        default_factory=list,
        description="Semantic relations extracted from the chunk.",
    )
