"""Cac model trung gian cho plan-aware retrieval/generation cua Adaptive."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerationInstruction(BaseModel):
    """Chi dan ma Adaptive tao ra truoc khi retrieve va generate.

    Model nay co scope co y nho:
    - Khong thay the SharedPlanMemory
    - Khong thay the LearnerProfile
    - Chi dong vai tro "ban tom tat tac chien" cho mot luot retrieve/generate
    """

    based_on_plan_id: str | None = None
    learning_goal: str = ""
    active_step_title: str | None = None

    learner_theta: float = 0.0
    weak_topics: list[str] = Field(default_factory=list)
    strong_topics: list[str] = Field(default_factory=list)

    seed_topics: list[str] = Field(default_factory=list)
    target_topics: list[str] = Field(default_factory=list)
    prerequisite_topics: list[str] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)
    expanded_topics: list[str] = Field(default_factory=list)
    retrieval_topics: list[str] = Field(default_factory=list)

    difficulty_target: float = 0.0
    generation_limit: int = 3
    retrieval_top_k: int = 8
    kg_depth: int = 1

    strategy_summary: str = ""
    generator_constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
