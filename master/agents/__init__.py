"""Top-level package exports for agent modules.

This module intentionally uses lazy imports so lightweight subpackages such as
`master.agents.adaptive` can be imported in isolation without forcing the full
teacher/verifier stack to initialize.
"""

from __future__ import annotations

__all__ = ["BaseAgent"]


def __getattr__(name: str):
    """Resolve heavy exports lazily at attribute access time.

    Args:
        name: The attribute name requested from the package namespace.

    Returns:
        The lazily imported object for supported exports.

    Raises:
        AttributeError: If the requested export is not provided by this module.
    """

    if name == "BaseAgent":
        from .baseagent import BaseAgent

        return BaseAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
