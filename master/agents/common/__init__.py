"""Shared agent utilities exposed through lazy package-level imports.

The adaptive code only needs a subset of the common package, so this file keeps
imports lazy to avoid triggering unrelated runtime dependencies during tests.
"""

from __future__ import annotations

from importlib import import_module

__all__ = ["settings", "LLMClient", "AgentState", "SharedPlanMemory", "tools"]


def __getattr__(name: str):
    """Resolve package exports lazily for lightweight imports.

    Args:
        name: The attribute requested from `master.agents.common`.

    Returns:
        The requested object when it is part of the supported export surface.

    Raises:
        AttributeError: If the requested name is not exported here.
    """

    if name == "settings":
        from .config import settings

        return settings
    if name == "LLMClient":
        from .llm_client import LLMClient

        return LLMClient
    if name == "AgentState":
        from .state import AgentState

        return AgentState
    if name == "SharedPlanMemory":
        from .shared_plan_memory import SharedPlanMemory

        return SharedPlanMemory
    if name == "tools":
        return import_module(f"{__name__}.tools")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
