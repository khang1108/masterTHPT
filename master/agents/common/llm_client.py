"""
Unified LangChain chat model factory: Google Gemini, FPT AI Cloud, or any OpenAI-compatible API (vLLM, LM Studio, Ollama w/ OpenAI layer, remote GPU host, etc.).
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Any, Optional, Union
from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel

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


def _normalize_openai_base_url(url: str) -> str:
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        u = f"http://{u}"
    u = u.rstrip("/")
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _openai_base_url_for_role(agent_role: Optional[str]) -> Optional[str]:
    """
    Resolve OpenAI-compatible base URL (…/v1) from env.

    Priority per role (e.g. teacher):
      1. OPENAI_COMPATIBLE_BASE_URL_TEACHER (uppercase role)
      2. OPENAI_COMPATIBLE_BASE_URL
      3. FPT_BASE_URL
      4. OPENAI_API_BASE
      5. LLM_BASE_URL
      6. Build from VLLM_BASE_URL host + VLLM_*_PORT (legacy layout)
    """
    role = (agent_role or "").strip().lower()
    if role:
        specific = os.getenv(f"OPENAI_COMPATIBLE_BASE_URL_{role.upper()}")
        if specific:
            return _normalize_openai_base_url(specific)

    for key in (
        "OPENAI_COMPATIBLE_BASE_URL",
        "FPT_BASE_URL",
        "OPENAI_API_BASE",
        "LLM_BASE_URL",
    ):
        v = os.getenv(key)
        if v:
            return _normalize_openai_base_url(v)

    host = os.getenv("VLLM_BASE_URL", "").strip()
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
        os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        or os.getenv("FPT_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
        or os.getenv("LLM_BASE_URL")
        or os.getenv("VLLM_TEACHER_PORT")
        or os.getenv("VLLM_BASE_URL")
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
            mname = "gemini-2.5-flash"
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

            b = base_url or _openai_base_url_for_role(agent_role)
            if not b:
                raise ValueError(
                    "OpenAI-compatible provider selected but no base URL found. Set "
                    "OPENAI_COMPATIBLE_BASE_URL (full URL to …/v1) or FPT_BASE_URL or VLLM_BASE_URL + VLLM_TEACHER_PORT."
                )
            key = api_key or os.getenv("FPT_API_KEY") or os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY") or "EMPTY"
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
