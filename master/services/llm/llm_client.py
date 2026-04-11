"""
LLM client for MASTER services: GPU host (OpenAI-compatible / vLLM / VLM) or FPT AI Cloud.
"""
from __future__ import annotations # Typehint
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel # LangChain chat model
from .config import LLMConfig, get_llm_config # LLM configuration

import os

class LLMClient:
    """Build LangChain chat models from :class:`LLMConfig` (env-driven via :func:`get_llm_config`)."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config if config is not None else get_llm_config()

    def get_chat_model(
                    self, 
                    **kwargs: Any) -> BaseChatModel:
        """
        Build a LangChain chat model from the LLM configuration.

        Args:
            model: The model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The temperature of the model.
            top_p: The top p of the model.
            kwargs: Override temperature, max_tokens, etc. for this instance only.

        Returns:
            A ``BaseChatModel`` (``bind_tools`` / ``with_structured_output`` / ``invoke``).
        """

        # Get the LLM configuration
        c = self.config
        temperature = kwargs.pop("temperature", c.temperature)
        max_tokens = kwargs.pop("max_tokens", c.max_tokens)
        top_p = kwargs.pop("top_p", c.top_p)

        # Build the chat model
        if c.provider == "google_genai":
            from langchain_google_genai import ChatGoogleGenerativeAI

            if not c.api_key:
                # Get the API key from the environment variable
                try: 
                    c.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                    if not c.api_key:
                        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not set. Please set the environment variable.")
                except KeyError:
                    raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is not set. Please set the environment variable.")

            params: dict[str, Any] = {
                "model": c.model,
                "api_key": c.api_key,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if top_p is not None:
                params["top_p"] = top_p
            params.update(kwargs)
            return ChatGoogleGenerativeAI(**params)

        if c.provider in ("gpu_openai", "fpt_ai_cloud"):
            from langchain_openai import ChatOpenAI

            if not c.base_url:
                raise ValueError(f"{c.provider} requires base_url (check env / LLMConfig)")
            if not c.model:
                raise ValueError(f"{c.provider} requires LLM_MODEL (or FPT_LLM_MODEL for FPT)")
            if not c.api_key and c.provider == "fpt_ai_cloud":
                raise ValueError("fpt_ai_cloud requires FPT_API_KEY or FPT_LLM_API_KEY")

            params2: dict[str, Any] = {
                "model": c.model,
                "api_key": c.api_key or "EMPTY",
                "base_url": c.base_url,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if top_p is not None:
                params2["top_p"] = top_p
            if c.extra_headers:
                params2["default_headers"] = c.extra_headers
            params2.update(kwargs)
            return ChatOpenAI(**params2)

        raise ValueError(f"Unknown LLM provider: {c.provider!r}")
