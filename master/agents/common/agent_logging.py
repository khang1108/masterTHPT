"""Shared logging helpers for agent workflows.

These helpers intentionally log compact operational metadata only. They avoid
dumping full prompts, answers, or secrets while still giving enough signal to
trace request flow across manager, adaptive, and tool/database layers.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from master.agents.common.message import MessageRequest

try:
    from master.logging.logger import logger
except ImportError:  # pragma: no cover - docker shim compatibility fallback
    from master.logging.logger import Logger

    logger = Logger("master")


def _count(value: Any) -> int | None:
    """Return a safe count for list-like values."""

    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)):
        return None
    try:
        return len(value)
    except TypeError:
        return None


def _compact_list(values: Sequence[Any] | None, *, limit: int = 3) -> str | None:
    """Render a short preview for small list metadata."""

    if not values:
        return None
    preview = [str(item) for item in values[:limit] if item is not None]
    if not preview:
        return None
    if len(values) > limit:
        preview.append("...")
    return "|".join(preview)


def _format_value(value: Any) -> str | None:
    """Normalize scalar-ish values into one-line log-safe strings."""

    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Path):
        return value.name
    if isinstance(value, str):
        compact = value.strip().replace("\n", " ")
        if not compact:
            return None
        return compact[:120]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return str(len(value))
    if isinstance(value, Mapping):
        return str(len(value))
    return str(value)


def _request_fields(request: MessageRequest | None) -> list[str]:
    """Build a compact request summary."""

    if request is None:
        return []

    content_length = len(request.content or "")
    file_names = [Path(item).name for item in request.file_urls if isinstance(item, str) and item]

    pairs: list[tuple[str, Any]] = [
        ("intent", request.intent),
        ("student_id", request.student_id),
        ("user_id", request.user_id),
        ("exam_id", request.exam_id),
        ("question_id", request.question_id),
        ("answers", _count(request.student_answers)),
        ("files", _count(request.file_urls)),
        ("file_names", _compact_list(file_names)),
        ("metadata_keys", _count(request.metadata)),
        ("content_len", content_length if content_length else None),
    ]
    return [f"{key}={formatted}" for key, value in pairs if (formatted := _format_value(value))]


def _state_fields(state: Mapping[str, Any] | None) -> list[str]:
    """Build a compact runtime-state summary."""

    if not state:
        return []

    pairs: list[tuple[str, Any]] = [
        ("phase", state.get("phase")),
        ("intent", state.get("intent")),
        ("exam_id", state.get("exam_id")),
        ("round", state.get("round")),
        ("max_round", state.get("max_round")),
        ("questions", _count(state.get("questions"))),
        ("answers", _count(state.get("student_answers"))),
        ("selected", _count(state.get("selected_questions"))),
        ("debates", _count(state.get("debate_outputs"))),
        ("trail", _compact_list(state.get("agent_trail"))),
        ("has_profile", state.get("learner_profile") is not None if "learner_profile" in state else None),
        ("has_response", state.get("response") is not None if "response" in state else None),
    ]
    return [f"{key}={formatted}" for key, value in pairs if (formatted := _format_value(value))]


def _extra_fields(extra: Mapping[str, Any] | None) -> list[str]:
    """Build compact key/value metadata for one log event."""

    if not extra:
        return []

    rendered: list[str] = []
    for key, value in extra.items():
        if (formatted := _format_value(value)) is not None:
            rendered.append(f"{key}={formatted}")
    return rendered


def log_agent_event(
    component: str,
    event: str,
    *,
    state: Mapping[str, Any] | None = None,
    request: MessageRequest | None = None,
    extra: Mapping[str, Any] | None = None,
    mode: str = "info",
) -> None:
    """Emit one structured operational log line through the shared logger."""

    details = [* _request_fields(request), * _state_fields(state), * _extra_fields(extra)]
    message = f"[{component}] {event}"
    if details:
        message = f"{message} | {', '.join(details)}"

    emit = getattr(logger, mode, logger.info)
    emit(message)
