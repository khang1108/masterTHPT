"""Execution-plan schemas for short-lived request orchestration.

This module is intentionally separate from ``SharedPlanMemory``:

- ``SharedPlanMemory`` tracks long-lived learning strategy for a student
- ``ExecutionPlan`` tracks the per-request orchestration steps inside one run

The manager/orchestrator owns these models and may rebuild them when a replan
is needed. Specialist agents only consume the current step plus a compact
planner summary.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionAgent(str, Enum):
    """Normalized specialist identities referenced by request-level plans."""

    PARSER = "parser"
    TEACHER = "teacher"
    VERIFIER = "verifier"
    ADAPTIVE = "adaptive"


class StepStatus(str, Enum):
    """Lifecycle state for one execution step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FinalResponseMode(str, Enum):
    """High-level response category expected from the orchestration run."""

    ANSWER = "answer"
    HINT = "hint"
    REVIEW = "review"
    ADAPTIVE_RECOMMENDATION = "adaptive_recommendation"
    PREPROCESS_RESULT = "preprocess_result"
    FALLBACK = "fallback"


class ReplanSignal(BaseModel):
    """Compact signal that a specialist could not finish the assigned step."""

    model_config = ConfigDict(extra="forbid")

    requested: bool = False
    reason: str = ""
    requested_by: str | None = None


class ExecutionStep(BaseModel):
    """One orchestrated action assigned to a specialist agent."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    agent: ExecutionAgent
    objective: str
    allowed_tools: list[str] = Field(default_factory=list)
    stop_on_complete: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class StepResult(BaseModel):
    """Normalized execution output captured after one specialist step finishes."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    agent: ExecutionAgent
    step_status: StepStatus
    summary: str = ""
    step_output: dict[str, Any] = Field(default_factory=dict)
    tool_calls_used: list[str] = Field(default_factory=list)
    replan_signal: ReplanSignal | None = None


class ExecutionPlan(BaseModel):
    """Short-lived request orchestration plan built by the central planner."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(default_factory=lambda: f"exec-{uuid4()}")
    intent: str
    goal: str
    steps: list[ExecutionStep] = Field(default_factory=list)
    current_step_index: int = 0
    requires_verification: bool = False
    final_response_mode: FinalResponseMode = FinalResponseMode.FALLBACK
    metadata: dict[str, Any] = Field(default_factory=dict)

    def current_step(self) -> ExecutionStep | None:
        """Return the current step if the index still points to a valid item."""

        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def has_remaining_steps(self) -> bool:
        """Return whether the plan still contains work from the current index."""

        return self.current_step() is not None
