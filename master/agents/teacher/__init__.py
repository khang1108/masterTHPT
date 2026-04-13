from .teacher import (
    TeacherAgent,
    Output,
    DraftResult,
    DebateResult,
    AgentState,
    DebateState,   # alias của AgentState — backward compat
)
from master.agents.common.message import Intent

__all__ = [
    "TeacherAgent",
    "Output",
    "DraftResult",
    "DebateResult",
    "AgentState",
    "DebateState",
    "Intent",
]
