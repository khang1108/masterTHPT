"""
LLM configuration for MASTER services

- GPU host (vLLM / OpenAI-compatible)
- FPT AI Cloud (AI Marketplace)
- Gemini (Google GenAI)

Usage:
    - If you use FPT AI Inference Marketplace, set ``FPT_LLM_BASE_URL`` = "https://mkp-api.fptcloud.com" to the base URL of the FPT AI Inference Marketplace.
    - If you use Gemini, set ``GEMINI_API_KEY`` = "YOUR_GEMINI_API_KEY" to the API key of the Gemini server.
    - If you use vLLM, set ``VLLM_BASE_URL`` = "http://PUBLIC_IP:8000/v1" to the base URL of the vLLM server.
    - If you use OpenAI-compatible, set ``OPENAI_COMPATIBLE_BASE_URL`` = "http://PUBLIC_IP:8000/v1" to the base URL of the OpenAI-compatible server.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

def _env_float(name: str, default: float) -> float:
    """Get a float from the environment variable."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    """Get an int from the environment variable."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    return int(raw)


def _normalize_gpu_openai_base(url: str) -> str:
    """
    Ensure OpenAI-compatible URL ends with /v1 (vLLM, local GPU, etc.).

    Args:
        url: The URL to normalize.

    Returns:
        The normalized URL.
    """
    u = url.strip()
    if not u.startswith(("http://", "https://")):
        u = f"http://{u}"
    u = u.rstrip("/")
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _gpu_base_url_for_role(agent_role: str | None) -> str | None:
    """
    Get the base URL for the GPU host.

    Args:
        agent_role: The role of the agent.

    Returns:
        The base URL for the GPU host.
    """
    role = (agent_role or "").strip().lower()
    if role:
        specific = os.getenv(f"OPENAI_COMPATIBLE_BASE_URL_{role.upper()}")
        if specific:
            return _normalize_gpu_openai_base(specific)
    for key in ("OPENAI_COMPATIBLE_BASE_URL", "OPENAI_API_BASE", "LLM_BASE_URL"):
        v = os.getenv(key)
        if v:
            return _normalize_gpu_openai_base(v)

    # Get the base URL for the GPU host
    host = os.getenv("VLLM_BASE_URL", "").strip()

    if not host:
        return None

    # Get the port for the GPU host
    port_map = {
        "manager": ("VLLM_MANAGER_PORT", "8080"),
        "teacher": ("VLLM_TEACHER_PORT", "8081"),
        "verifier": ("VLLM_VERIFIER_PORT", "8082"),
    }

    # Get the port for the GPU host
    if role in port_map:
        env_key, default_p = port_map[role]
        port = os.getenv(env_key, default_p)
    else:
        port = os.getenv("VLLM_TEACHER_PORT", os.getenv("VLLM_MANAGER_PORT", "8081"))
    
    # Get the root of the base URL (http:// or https://)
    if host.startswith(("http://", "https://")):
        root = host.rstrip("/")
    else:
        root = f"http://{host}"

    # Normalize the base URL (…/v1)
    return _normalize_gpu_openai_base(f"{root}:{port}")


def _fpt_base_url() -> str:
    """
    FPT AI Marketplace (OpenAI-style chat completions).

    Docs: https://ai-docs.fptcloud.com/ — default host ``mkp-api.fptcloud.com``.
    FPT endpoint chỉ cần raw host (vd: ``https://mkp-api.fptcloud.com``),
    LangChain ChatOpenAI sẽ tự thêm ``/chat/completions``.
    Set ``FPT_LLM_APPEND_OPENAI_V1=true`` chỉ khi deployment yêu cầu prefix ``/v1``.
    """
    raw = (os.getenv("FPT_LLM_BASE_URL") or os.getenv("FPT_BASE_URL") or "https://mkp-api.fptcloud.com").strip().rstrip("/")
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    append = os.getenv("FPT_LLM_APPEND_OPENAI_V1", "false").lower() in ("1", "true", "yes")
    if append and not raw.endswith("/v1"):
        return f"{raw}/v1"
    return raw


def _model_for_role(agent_role: str | None, **kwargs: Any) -> str:
    """
    Get the model for the given agent role.

    Args:
        agent_role: The role of the agent.
        kwargs: Override the model for the given agent role.

    Returns:
        The model for the given agent role.
    """
    # Get the role of the agent
    role = (agent_role or "").strip().lower()
    model = kwargs.get("model")
    provider = kwargs.get("provider")

    # If the model is provided, return it
    if model:
        return model.strip()

    if provider == "fpt_ai_cloud":
        model = os.getenv("FPT_LLM_MODEL")
        if model:
            return model.strip()
    if provider == "google_genai":
        model = os.getenv("GEMINI_MODEL")
        if model:
            return model.strip()    
    model = os.getenv(f"LLM_MODEL_{role.upper()}")
    if model:
        return model.strip()
    return os.getenv("LLM_MODEL", "").strip()


@dataclass
class LLMConfig:
    """
    LLM Config for all MASTER services.

    Resolved settings for one LLM endpoint (GPU OpenAI-compatible, FPT Cloud, or Gemini).

    Args:
        provider: The provider of the LLM.
        model: The model to use.
        api_key: The API key to use.
        base_url: The base URL to use.
        temperature: The temperature of the model.
        max_tokens: The maximum number of tokens to generate.
        top_p: The top p of the model.
        extra_headers: The extra headers to use.
        agent_role: The role of the agent.
        provider_name: The name of the provider.
        max_concurrency: The maximum concurrency of the model.
        requests_per_minute: The requests per minute of the model.
        metadata: The metadata of the model.
    """

    provider: str
    model: str
    api_key: str
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float | None = None
    extra_headers: dict[str, str] | None = None
    agent_role: str | None = None
    provider_name: str = "routing"
    max_concurrency: int = 20
    requests_per_minute: int = 600
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_env(agent_role: str | None = None, **kwargs: Any) -> LLMConfig:
        """
        Load ``LLMConfig`` from environment (and optional per-agent role for URLs/models).

        Args:
            agent_role: The role of the agent.
            kwargs: Override the LLMConfig.

        Returns:
            A ``LLMConfig`` object.
        """
        # Detect the backend
        role = agent_role   
        provider = kwargs.get("provider") or os.getenv("LLM_PROVIDER", "gpu_openai")
        model = _model_for_role(agent_role, provider=provider, **kwargs)
        temp = kwargs.get("temperature", _env_float("LLM_DEFAULT_TEMPERATURE", 0.7))
        mx = kwargs.get("max_tokens", _env_int("LLM_DEFAULT_MAX_TOKENS", 4096))
        top_p = kwargs.get("top_p", None)
        extra_headers = kwargs.get("extra_headers", None)

        if provider == "fpt_ai_cloud":
            # Get the API key from the environment variable
            key = (
                os.getenv("FPT_API_KEY")
                or os.getenv("FPT_LLM_API_KEY")
                or os.getenv("OPENAI_API_KEY")
                or ""
            )
            if not model:
                model = os.getenv("FPT_LLM_MODEL", "").strip()
            return LLMConfig(
                provider="fpt_ai_cloud",
                model=model,
                api_key=key,
                base_url=_fpt_base_url(),
                temperature=temp,
                max_tokens=mx,
                top_p=top_p,
                extra_headers=extra_headers or None,
                agent_role=role,
                provider_name="fpt_ai_cloud",
            )

        if provider == "google_genai":
            api_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            if not model:
                model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()
            
            return LLMConfig(
                provider="google_genai",
                model=model,
                api_key=api_key,
                base_url=None,
                temperature=temp,
                max_tokens=mx,
                top_p=top_p,
                extra_headers=extra_headers or None,
                agent_role=role,
                provider_name="google_genai",
            )

        # gpu_openai — vLLM / VLM on GPU host, LM Studio, etc.
        key = (
            os.getenv("OPENAI_COMPATIBLE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or "EMPTY"
        )
        base = _gpu_base_url_for_role(role)
        if not base:
            base = _normalize_gpu_openai_base(
                #! TODO: Get the base URL from the environment variable
                os.getenv("GPU_LLM_BASE_URL", "http://127.0.0.1:8000/v1")
            )
        if not model:
            model = os.getenv("LLM_TEACHER_MODEL", "Qwen3-8B").strip() or "Qwen3-8B"
        return LLMConfig(
            provider="gpu_openai",
            model=model,
            api_key=key,
            base_url=base,
            temperature=temp,
            max_tokens=mx,
            top_p=top_p,
            extra_headers=extra_headers or None,
            agent_role=role,
            provider_name="gpu_openai",
        )


def get_llm_config(agent_role: str | None = None) -> LLMConfig:
    """Load ``LLMConfig`` from environment (and optional per-agent role for URLs/models)."""
    return LLMConfig.from_env(agent_role=agent_role)
