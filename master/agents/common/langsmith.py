"""Helpers for optional LangSmith-friendly runnable configuration.

The project already uses LangChain and LangGraph, so enabling LangSmith mostly
comes down to:

- setting the documented environment variables
- attaching stable tags / metadata / run names so traces are easier to inspect

These helpers keep that configuration consistent across agents.
"""

from __future__ import annotations

import os
from typing import Any, Iterable


def langsmith_tracing_enabled() -> bool:
    """Return whether tracing has been enabled via LangSmith/LangChain env vars."""

    raw = os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2") or ""
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def build_langsmith_tags(
    *,
    agent_role: str | None = None,
    provider: str | None = None,
    extra_tags: Iterable[str] | None = None,
) -> list[str]:
    """Build stable tags that make traces easier to filter in LangSmith."""

    tags: list[str] = ["project:master"]
    if agent_role:
        tags.append(f"agent:{agent_role.strip().lower()}")
    if provider:
        tags.append(f"provider:{provider.strip().lower()}")
    if extra_tags:
        tags.extend(tag for tag in extra_tags if tag)

    seen: set[str] = set()
    deduped: list[str] = []
    for tag in tags:
        if tag in seen:
            continue
        seen.add(tag)
        deduped.append(tag)
    return deduped


def build_langsmith_metadata(
    *,
    agent_role: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build LangSmith metadata for a runnable or model invocation."""

    metadata: dict[str, Any] = {
        "component": "agents",
        "langsmith_tracing_enabled": langsmith_tracing_enabled(),
    }
    if agent_role:
        metadata["agent_role"] = agent_role.strip().lower()
    if provider:
        normalized_provider = provider.strip().lower()
        metadata["llm_provider"] = normalized_provider
        metadata["ls_provider"] = normalized_provider
    if model_name:
        metadata["llm_model"] = model_name
        metadata["ls_model_name"] = model_name
    if extra_metadata:
        metadata.update(extra_metadata)
    return metadata


def build_langsmith_invoke_config(
    *,
    run_name: str | None = None,
    agent_role: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    thread_id: str | None = None,
    extra_tags: Iterable[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a ``RunnableConfig``-shaped dict for LangChain/LangGraph invoke calls."""

    config: dict[str, Any] = {}
    if run_name:
        config["run_name"] = run_name

    tags = build_langsmith_tags(
        agent_role=agent_role,
        provider=provider,
        extra_tags=extra_tags,
    )
    metadata = build_langsmith_metadata(
        agent_role=agent_role,
        provider=provider,
        model_name=model_name,
        extra_metadata=extra_metadata,
    )

    if tags:
        config["tags"] = tags
    if metadata:
        config["metadata"] = metadata
    if thread_id is not None:
        config["configurable"] = {"thread_id": thread_id}
    return config
