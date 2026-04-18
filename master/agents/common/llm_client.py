"""
Unified LangChain chat model factory: Google Gemini, FPT AI Cloud, or any OpenAI-compatible API (vLLM, LM Studio, Ollama w/ OpenAI layer, remote GPU host, etc.).
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Optional, Union
from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel

from .agent_logging import log_agent_event
from .langsmith import build_langsmith_metadata, build_langsmith_tags

load_dotenv(override=True)


class LLMProvider(str, Enum):
    GOOGLE_GENAI = "google_genai"
    OPENAI_COMPATIBLE = "openai_compatible"


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _clean_env_value(value: str | None) -> str | None:
    """Trim quotes and surrounding whitespace from environment values."""

    if value is None:
        return None
    cleaned = value.strip().strip("\"'")
    return cleaned or None


def _env_first(*names: str) -> str | None:
    """Return the first non-empty environment value among candidate names."""

    for name in names:
        value = _clean_env_value(os.getenv(name))
        if value:
            return value
    return None


def _env_bool(name: str, default: bool) -> bool:
    raw = _clean_env_value(os.getenv(name))
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _normalize_openai_base_url(url: str) -> str:
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        u = f"http://{u}"
    u = u.rstrip("/")
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _looks_like_fpt_base_url(url: str | None) -> bool:
    candidate = _clean_env_value(url)
    if not candidate:
        return False
    lowered = candidate.lower()
    return "fptcloud.com" in lowered or "mkp-api" in lowered


def _normalize_fpt_base_url(url: str) -> str:
    """
    Normalize FPT AI Marketplace base URL.

    FPT deployments may expose OpenAI-style chat completions either under the
    raw host (for example ``https://mkp-api.fptcloud.com``) or under ``/v1``.
    We therefore keep the raw host by default and only append ``/v1`` when the
    env flag explicitly asks for it.
    """

    u = url.strip()
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    u = u.rstrip("/")
    if _env_bool("FPT_LLM_APPEND_OPENAI_V1", False) and not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _normalize_openai_compatible_base_url(url: str) -> str:
    """Normalize explicit OpenAI-compatible base URLs with FPT-aware handling."""

    if _looks_like_fpt_base_url(url):
        return _normalize_fpt_base_url(url)
    return _normalize_openai_base_url(url)


def _openai_api_key() -> str:
    """Resolve the OpenAI-compatible/FPT API key from supported env aliases."""

    return (
        _env_first(
            "FPT_API_KEY",
            "FPT_AI_KEY",
            "FPT_LLM_API_KEY",
            "OPENAI_COMPATIBLE_API_KEY",
            "OPENAI_API_KEY",
        )
        or "EMPTY"
    )


def _openai_base_url_for_role(agent_role: Optional[str]) -> Optional[str]:
    """
    Resolve OpenAI-compatible base URL from env.

    Priority per role (e.g. teacher):
      1. FPT_BASE_URL_TEACHER / FPT_LLM_BASE_URL_TEACHER
      2. OPENAI_COMPATIBLE_BASE_URL_TEACHER
      3. FPT_LLM_BASE_URL / FPT_BASE_URL
      4. OPENAI_COMPATIBLE_BASE_URL / OPENAI_API_BASE / LLM_BASE_URL
      5. Build from VLLM_BASE_URL host + VLLM_*_PORT (legacy layout)

    FPT URLs are preserved as raw hosts by default and only receive ``/v1``
    when ``FPT_LLM_APPEND_OPENAI_V1=true``.
    """
    role = (agent_role or "").strip().lower()
    if role:
        fpt_specific = _env_first(
            f"FPT_BASE_URL_{role.upper()}",
            f"FPT_LLM_BASE_URL_{role.upper()}",
        )
        if fpt_specific:
            return _normalize_fpt_base_url(fpt_specific)

        specific = _env_first(f"OPENAI_COMPATIBLE_BASE_URL_{role.upper()}")
        if specific:
            return _normalize_openai_base_url(specific)

    shared_fpt_base = _env_first("FPT_LLM_BASE_URL", "FPT_BASE_URL", "OPENAI_COMPATIBLE_BASE_URL")
    if shared_fpt_base and _looks_like_fpt_base_url(shared_fpt_base):
        return _normalize_fpt_base_url(shared_fpt_base)

    shared_base = _env_first(
        "OPENAI_COMPATIBLE_BASE_URL",
        "OPENAI_API_BASE",
        "LLM_BASE_URL",
    )
    if shared_base:
        return _normalize_openai_base_url(shared_base)

    host = _clean_env_value(os.getenv("VLLM_BASE_URL")) or ""
    if not host:
        return None

    port_map = {
        "manager": ("VLLM_MANAGER_PORT", "8080"),
        "teacher": ("VLLM_TEACHER_PORT", "8081"),
        "verifier": ("VLLM_VERIFIER_PORT", "8082"),
    }
    if role in port_map:
        env_key, default_p = port_map[role]
        port = os.getenv(env_key, default_p)
    else:
        port = os.getenv("VLLM_TEACHER_PORT", os.getenv("VLLM_MANAGER_PORT", "8081"))

    if host.startswith(("http://", "https://")):
        root = host.rstrip("/")
    else:
        root = f"http://{host}"
    return _normalize_openai_base_url(f"{root}:{port}")


def _model_for_role(agent_role: Optional[str]) -> Optional[str]:
    role = (agent_role or "").strip().lower()
    if role:
        m = os.getenv(f"LLM_MODEL_{role.upper()}")
        if m:
            return m
    return os.getenv("LLM_MODEL") or os.getenv("GEMINI_MODEL")


def _resolve_provider(explicit: Optional[Union[str, LLMProvider]]) -> LLMProvider:
    if explicit is not None:
        v = explicit.value if isinstance(explicit, LLMProvider) else str(explicit).strip().lower()
        if v in ("google", "gemini", "google_genai"):
            return LLMProvider.GOOGLE_GENAI
        if v in ("openai", "openai_compatible", "vllm", "gpu", "local"):
            return LLMProvider.OPENAI_COMPATIBLE
        raise ValueError(f"Unknown LLM provider: {explicit!r}")

    p = os.getenv("LLM_PROVIDER", "").strip().lower()
    if p in ("google_genai", "google", "gemini"):
        return LLMProvider.GOOGLE_GENAI
    if p in ("openai_compatible", "openai", "vllm", "gpu", "local"):
        return LLMProvider.OPENAI_COMPATIBLE

    if (
        _env_first(
            "OPENAI_COMPATIBLE_BASE_URL",
            "FPT_LLM_BASE_URL",
            "FPT_BASE_URL",
            "OPENAI_API_BASE",
            "LLM_BASE_URL",
            "VLLM_BASE_URL",
        )
        or _clean_env_value(os.getenv("VLLM_TEACHER_PORT"))
    ):
        return LLMProvider.OPENAI_COMPATIBLE

    return LLMProvider.GOOGLE_GENAI


class LLMClient:
    """Factory for ``BaseChatModel`` instances driven by env vars and optional overrides."""

    @staticmethod
    def chat_model(
        *,
        provider: Optional[Union[str, LLMProvider]] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        agent_role: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        Build a LangChain chat model.

        **Google GenAI** (``LLM_PROVIDER=google_genai`` or default when no OpenAI base is set):

        - ``GEMINI_API_KEY`` / ``GOOGLE_API_KEY``
        - ``GEMINI_MODEL`` / ``LLM_MODEL``

        **OpenAI-compatible** (vLLM on GPU, FPT AI Cloud, etc.):

        - ``OPENAI_COMPATIBLE_BASE_URL`` or per-role ``OPENAI_COMPATIBLE_BASE_URL_TEACHER`` or ``FPT_BASE_URL``
        - ``OPENAI_COMPATIBLE_API_KEY`` or ``FPT_API_KEY`` (use ``EMPTY`` or any string if the server ignores it)
        - ``LLM_MODEL`` or ``LLM_MODEL_TEACHER``

        **Legacy GPU layout:** ``VLLM_BASE_URL`` (host or http URL) + ``VLLM_TEACHER_PORT`` etc.
        """
        prov = _resolve_provider(provider)
        temp = temperature if temperature is not None else _env_float("LLM_DEFAULT_TEMPERATURE", 0.3)
        mx = max_tokens if max_tokens is not None else _env_int("LLM_DEFAULT_MAX_TOKENS", 4096)
        tp = top_p if top_p is not None else _env_float("LLM_DEFAULT_TOP_P", 0.9)
        mname = model or _model_for_role(agent_role)
        if not mname:
            mname = "gemini-2.5-flash-lite"
        role_name = (agent_role or "").strip().lower() or None
        extra_tags = kwargs.pop("tags", None)
        extra_metadata = kwargs.pop("metadata", None)
        tags = build_langsmith_tags(
            agent_role=role_name,
            provider=prov.value,
            extra_tags=extra_tags,
        )
        metadata = build_langsmith_metadata(
            agent_role=role_name,
            provider=prov.value,
            model_name=mname,
            extra_metadata=extra_metadata,
        )

        if prov is LLMProvider.GOOGLE_GENAI:
            from langchain_google_genai import ChatGoogleGenerativeAI

            key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            return ChatGoogleGenerativeAI(
                model=mname,
                temperature=temp,
                max_output_tokens=mx,
                top_p=tp,
                api_key=key,
                tags=tags,
                metadata=metadata,
                **kwargs,
            )

        if prov is LLMProvider.OPENAI_COMPATIBLE:
            from langchain_openai import ChatOpenAI

            b = (
                _normalize_openai_compatible_base_url(base_url)
                if base_url
                else _openai_base_url_for_role(agent_role)
            )
            if not b:
                raise ValueError(
                    "OpenAI-compatible provider selected but no base URL found. Set "
                    "OPENAI_COMPATIBLE_BASE_URL (full URL to …/v1) or FPT_BASE_URL or VLLM_BASE_URL + VLLM_TEACHER_PORT."
                )
            key = _clean_env_value(api_key) or _openai_api_key()
            log_agent_event(
                "llm_client",
                "chat_model:openai_compatible",
                extra={
                    "agent_role": agent_role,
                    "provider": prov.value,
                    "model": mname,
                    "base_url": b,
                    "fpt_compatible": _looks_like_fpt_base_url(b),
                    "api_key_present": key != "EMPTY",
                },
                mode="progress",
            )
            return ChatOpenAI(
                model=mname,
                base_url=b,
                api_key=key,
                temperature=temp,
                max_tokens=mx,
                top_p=tp,
                tags=tags,
                metadata=metadata,
                **kwargs,
            )

        raise AssertionError("unreachable")
