"""Shared procedural memory models for multi-agent study planning.

This module defines the durable "shared plan" layer that sits beside
``LearnerProfile``:

- ``LearnerProfile`` stores learner state such as mastery, theta, and history
- ``SharedPlanMemory`` stores the current cross-agent study strategy

The design is intentionally versioned and append-friendly so multiple agents
can propose updates while the manager/orchestrator decides which plan becomes
the active one.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PlanStatus(str, Enum):
    """Lifecycle status for a shared study plan."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PlanStepStatus(str, Enum):
    """Execution status for one curriculum/study step inside a plan."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class PlanNoteKind(str, Enum):
    """Kinds of notes that agents may attach to the shared plan."""

    OBSERVATION = "observation"
    PROPOSAL = "proposal"
    REFLECTION = "reflection"
    DECISION = "decision"


class PlanStep(BaseModel):
    """One actionable unit in the learner's cross-agent study roadmap."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    title: str
    description: str = ""
    sequence_order: int = 0
    priority: int = Field(default=50, ge=0, le=100)
    status: PlanStepStatus = PlanStepStatus.PENDING

    target_topics: list[str] = Field(default_factory=list)
    prerequisite_topics: list[str] = Field(default_factory=list)
    exam_matrix_refs: list[str] = Field(default_factory=list)
    kg_refs: list[str] = Field(default_factory=list)

    recommended_question_count: int | None = Field(default=None, ge=0)
    mastery_target: float | None = Field(default=None, ge=0.0, le=1.0)
    success_criteria: list[str] = Field(default_factory=list)


class PlanNote(BaseModel):
    """A compact audit/comment record attached to a shared plan."""

    model_config = ConfigDict(extra="forbid")

    note_id: str
    author_agent: str
    kind: PlanNoteKind = PlanNoteKind.OBSERVATION
    content: str
    created_at: datetime
    tags: list[str] = Field(default_factory=list)


class SharedPlanMemory(BaseModel):
    """Durable shared strategic memory used by multiple tutoring agents.

    This document is the "current study strategy" for a learner. Agents such as
    adaptive, teacher, verifier, and manager may all read it; writes should
    generally be coordinated by the orchestrator to avoid conflicting updates.
    """

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    user_id: str
    student_id: str | None = None

    status: PlanStatus = PlanStatus.DRAFT
    version: int = Field(default=1, ge=1)

    goal: str
    summary: str = ""
    rationale: str = ""
    evidence_summary: str = ""

    target_exam: str | None = None
    target_exam_name: str | None = None
    target_exam_type: str | None = None
    planning_horizon: str | None = None

    focus_topics: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    mastery_targets: dict[str, float] = Field(default_factory=dict)

    steps: list[PlanStep] = Field(default_factory=list)
    notes: list[PlanNote] = Field(default_factory=list)

    exam_matrix_refs: list[str] = Field(default_factory=list)
    kg_refs: list[str] = Field(default_factory=list)
    derived_from_history_ids: list[str] = Field(default_factory=list)
    derived_from_exam_ids: list[str] = Field(default_factory=list)

    created_by_agent: str
    updated_by_agent: str
    active_from: datetime | None = None
    active_until: datetime | None = None
    created_at: datetime
    updated_at: datetime

    metadata: dict[str, Any] = Field(default_factory=dict)


def shared_plan_memory_validator() -> dict[str, Any]:
    """Return the MongoDB JSON schema validator for ``shared_plan_memory``.

    The validator intentionally mirrors ``SharedPlanMemory`` rather than being
    generated dynamically. That makes it safe to copy into MongoDB collection
    creation commands or infrastructure scripts without importing application
    code at deploy time.
    """

    return {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "plan_id",
                "user_id",
                "status",
                "version",
                "goal",
                "focus_topics",
                "constraints",
                "mastery_targets",
                "steps",
                "notes",
                "exam_matrix_refs",
                "kg_refs",
                "derived_from_history_ids",
                "derived_from_exam_ids",
                "created_by_agent",
                "updated_by_agent",
                "created_at",
                "updated_at",
                "metadata",
            ],
            "properties": {
                "plan_id": {"bsonType": "string", "description": "Stable identifier for one plan version"},
                "user_id": {"bsonType": "string", "description": "Stable learner/user identifier"},
                "student_id": {"bsonType": ["string", "null"]},
                "status": {
                    "enum": [status.value for status in PlanStatus],
                    "description": "Lifecycle state of the shared plan",
                },
                "version": {"bsonType": ["int", "long"], "minimum": 1},
                "goal": {"bsonType": "string"},
                "summary": {"bsonType": "string"},
                "rationale": {"bsonType": "string"},
                "evidence_summary": {"bsonType": "string"},
                "target_exam": {"bsonType": ["string", "null"]},
                "target_exam_name": {"bsonType": ["string", "null"]},
                "target_exam_type": {"bsonType": ["string", "null"]},
                "planning_horizon": {"bsonType": ["string", "null"]},
                "focus_topics": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "constraints": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "mastery_targets": {"bsonType": "object"},
                "steps": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": [
                            "step_id",
                            "title",
                            "description",
                            "sequence_order",
                            "priority",
                            "status",
                            "target_topics",
                            "prerequisite_topics",
                            "exam_matrix_refs",
                            "kg_refs",
                            "success_criteria",
                        ],
                        "properties": {
                            "step_id": {"bsonType": "string"},
                            "title": {"bsonType": "string"},
                            "description": {"bsonType": "string"},
                            "sequence_order": {"bsonType": ["int", "long"]},
                            "priority": {
                                "bsonType": ["int", "long"],
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "status": {
                                "enum": [status.value for status in PlanStepStatus],
                            },
                            "target_topics": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                            "prerequisite_topics": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                            "exam_matrix_refs": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                            "kg_refs": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                            "recommended_question_count": {
                                "bsonType": ["int", "long", "null"],
                                "minimum": 0,
                            },
                            "mastery_target": {
                                "bsonType": ["double", "int", "long", "decimal", "null"],
                                "minimum": 0,
                                "maximum": 1,
                            },
                            "success_criteria": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                        },
                    },
                },
                "notes": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": [
                            "note_id",
                            "author_agent",
                            "kind",
                            "content",
                            "created_at",
                            "tags",
                        ],
                        "properties": {
                            "note_id": {"bsonType": "string"},
                            "author_agent": {"bsonType": "string"},
                            "kind": {
                                "enum": [kind.value for kind in PlanNoteKind],
                            },
                            "content": {"bsonType": "string"},
                            "created_at": {"bsonType": "date"},
                            "tags": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                        },
                    },
                },
                "exam_matrix_refs": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "kg_refs": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "derived_from_history_ids": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "derived_from_exam_ids": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                },
                "created_by_agent": {"bsonType": "string"},
                "updated_by_agent": {"bsonType": "string"},
                "active_from": {"bsonType": ["date", "null"]},
                "active_until": {"bsonType": ["date", "null"]},
                "created_at": {"bsonType": "date"},
                "updated_at": {"bsonType": "date"},
                "metadata": {"bsonType": "object"},
            },
        }
    }


def shared_plan_memory_index_specs() -> list[dict[str, Any]]:
    """Return recommended MongoDB index specs for the shared plan collection."""

    return [
        {
            "key": [("plan_id", 1)],
            "name": "shared_plan_memory_plan_id_key",
            "unique": True,
        },
        {
            "key": [("user_id", 1), ("status", 1)],
            "name": "shared_plan_memory_user_active_plan_key",
            "unique": True,
            "partialFilterExpression": {"status": PlanStatus.ACTIVE.value},
        },
        {
            "key": [("user_id", 1), ("updated_at", -1)],
            "name": "shared_plan_memory_user_updated_at_idx",
        },
        {
            "key": [("user_id", 1), ("target_exam", 1), ("status", 1)],
            "name": "shared_plan_memory_user_target_exam_status_idx",
        },
    ]
