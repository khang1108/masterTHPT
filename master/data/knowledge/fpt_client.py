"""LiteLLM-based FPT AI Cloud client helpers for notebook KG extraction."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .extract_pipeline import MarkdownChunk, build_extraction_message_payload


def _load_env_file_fallback(path: Path) -> None:
    """Minimal `.env` parser fallback when python-dotenv is unavailable."""

    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def _normalize_fpt_base_url(raw_url: str) -> str:
    """Normalize FPT base URL for OpenAI-compatible SDKs like LiteLLM."""

    url = raw_url.strip().strip("\"'").rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    for suffix in ("/v1/chat/completions", "/chat/completions", "/v1"):
        if url.endswith(suffix):
            return url[: -len(suffix)]
    return url


_INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", flags=re.DOTALL)
_PAREN_MATH_RE = re.compile(r"\\\((.+?)\\\)", flags=re.DOTALL)
_BRACKET_MATH_RE = re.compile(r"\\\[(.+?)\\\]", flags=re.DOTALL)
_DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$", flags=re.DOTALL)


@dataclass(frozen=True)
class FPTChatConfig:
    """Configuration for the FPT AI Cloud chat endpoint via LiteLLM."""

    base_url: str = "https://mkp-api.fptcloud.com"
    api_key: str | None = None
    model: str = "SaoLa-Llama3.1-planner"
    timeout_seconds: int = 180

    @classmethod
    def from_env(cls) -> "FPTChatConfig":
        """Load configuration from environment variables."""

        try:
            from dotenv import load_dotenv

            load_dotenv(override=False)
            repo_env = Path(__file__).resolve().parents[3] / ".env"
            if repo_env.exists():
                load_dotenv(repo_env, override=False)
        except Exception:
            _load_env_file_fallback(Path.cwd() / ".env")
            _load_env_file_fallback(Path(__file__).resolve().parents[3] / ".env")

        raw_base_url = (
            os.getenv("FPT_CHAT_URL")
            or os.getenv("FPT_LLM_BASE_URL")
            or os.getenv("FPT_BASE_URL")
            or cls.base_url
        )

        api_key = os.getenv("FPT_API_KEY") or os.getenv("FPT_LLM_API_KEY")
        if api_key is not None:
            api_key = api_key.strip().strip("\"'")

        return cls(
            base_url=_normalize_fpt_base_url(raw_base_url),
            api_key=api_key,
            model=(os.getenv("FPT_MODEL") or os.getenv("FPT_LLM_MODEL") or cls.model).strip(),
            timeout_seconds=int(os.getenv("FPT_TIMEOUT_SECONDS", "180")),
        )


def _extract_json_block(text: str) -> dict[str, Any]:
    """Recover a JSON object from raw model text."""

    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
        if match:
            stripped = match.group(1).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("FPT model response did not contain a JSON object.")
    candidate = stripped[start : end + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        # FPT responses for math-heavy chunks sometimes preserve raw LaTeX
        # (for example `\frac`, `\(`, `\alpha`) inside JSON strings.
        # Those backslashes are valid content but invalid JSON escapes unless
        # doubled, so we repair only the malformed escape sequences and retry.
        if "Invalid \\escape" not in str(exc):
            raise
        repaired = _escape_invalid_json_backslashes(candidate)
        return json.loads(repaired)


def _escape_invalid_json_backslashes(raw_json: str) -> str:
    """Double only malformed backslashes so JSON with LaTeX can be decoded."""

    result: list[str] = []
    i = 0
    valid_simple_escapes = {'"', "\\", "/", "b", "f", "n", "r", "t"}
    hex_digits = set("0123456789abcdefABCDEF")

    while i < len(raw_json):
        char = raw_json[i]
        if char != "\\":
            result.append(char)
            i += 1
            continue

        if i + 1 >= len(raw_json):
            result.append("\\\\")
            i += 1
            continue

        next_char = raw_json[i + 1]
        if next_char in valid_simple_escapes:
            result.append(char)
            result.append(next_char)
            i += 2
            continue

        if next_char == "u":
            unicode_suffix = raw_json[i + 2 : i + 6]
            if len(unicode_suffix) == 4 and all(ch in hex_digits for ch in unicode_suffix):
                result.append(char)
                result.append("u")
                result.extend(unicode_suffix)
                i += 6
                continue

        result.append("\\\\")
        result.append(next_char)
        i += 2

    return "".join(result)


def _normalize_math_delimiters(text: str) -> str:
    """Convert common math notations to `$$...$$` for downstream markdown use."""

    normalized = text.strip()

    normalized = _BRACKET_MATH_RE.sub(lambda match: f"$${match.group(1).strip()}$$", normalized)
    normalized = _PAREN_MATH_RE.sub(lambda match: f"$${match.group(1).strip()}$$", normalized)
    normalized = _INLINE_MATH_RE.sub(lambda match: f"$${match.group(1).strip()}$$", normalized)
    normalized = _DISPLAY_MATH_RE.sub(lambda match: f"$${match.group(1).strip()}$$", normalized)

    return normalized


def _normalize_math_payload(payload: Any) -> Any:
    """Recursively normalize math delimiters in parsed model payloads."""

    if isinstance(payload, dict):
        return {key: _normalize_math_payload(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_normalize_math_payload(item) for item in payload]
    if isinstance(payload, str):
        return _normalize_math_delimiters(payload)
    return payload


def _response_to_dict(response: Any) -> dict[str, Any]:
    """Convert LiteLLM/OpenAI-style response objects into plain dicts."""

    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "dict"):
        return response.dict()
    if isinstance(response, dict):
        return response
    return dict(response)


def call_fpt_chat(
    *,
    messages: list[dict[str, str]],
    config: FPTChatConfig,
) -> dict[str, Any]:
    """Call FPT AI Cloud through LiteLLM and return the raw response JSON."""

    if not config.api_key:
        raise ValueError("Missing FPT API key. Set FPT_API_KEY before running extraction.")

    try:
        from litellm import completion
    except ImportError as exc:
        raise RuntimeError(
            "LiteLLM is not installed. Add `litellm` to the environment before running FPT extraction."
        ) from exc

    try:
        response = completion(
            model=f"openai/{config.model}",
            messages=messages,
            api_key=config.api_key,
            api_base=config.base_url,
            temperature=0.1,
            stream=False,
            timeout=config.timeout_seconds,
        )
    except Exception as exc:
        detail = str(exc).strip()
        message = (
            "FPT LiteLLM request failed " f"(base_url={config.base_url}, model={config.model})."
        )
        if detail:
            message = f"{message} Detail: {detail}"
        raise RuntimeError(message) from exc

    return _response_to_dict(response)


def extract_graph_for_chunk_fpt(
    chunk: MarkdownChunk,
    *,
    config: FPTChatConfig,
) -> Any:
    """Extract one chunk graph using FPT AI Cloud via LiteLLM."""

    from .model import ExtractionDocument

    schema_instruction = (
        "\n\nReturn JSON only with this exact top-level shape:\n"
        "{\n"
        '  "chunk_id": "string",\n'
        '  "summary": "string",\n'
        '  "nodes": [\n'
        "    {\n"
        '      "id": "string",\n'
        '      "label": "string",\n'
        '      "type": "CONCEPT | THEOREM | FORMULA | EXAMPLE | METHOD",\n'
        '      "description": "string",\n'
        '      "grade": 10 | 11 | 12 | null,\n'
        '      "source_title": "string | null"\n'
        "    }\n"
        "  ],\n"
        '  "edges": [\n'
        "    {\n"
        '      "source": "string",\n'
        '      "target": "string",\n'
        '      "relation": "REQUIRES | PART_OF | RELATED_TO",\n'
        '      "rationale": "string | null"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Represent every mathematical formula in string fields using only the "
        "`$$...$$` delimiter. Do not use `$...$`, `\\(...\\)`, or `\\[...\\]`.\n"
        "If any JSON string contains LaTeX or other backslashes, escape each "
        "backslash for valid JSON. Example: write \\\\frac{a}{b}, not \\frac{a}{b}.\n"
        "Do not include markdown fences. Do not include any text before or after the JSON."
    )

    messages = build_extraction_message_payload(chunk)
    messages[0]["content"] += schema_instruction
    messages[1]["content"] = _normalize_math_delimiters(messages[1]["content"])
    raw_response = call_fpt_chat(messages=messages, config=config)
    content = raw_response["choices"][0]["message"]["content"]
    try:
        parsed = _normalize_math_payload(_extract_json_block(content))
        if "chunk_id" not in parsed or not parsed["chunk_id"]:
            parsed["chunk_id"] = chunk.chunk_id
        return ExtractionDocument.model_validate(parsed)
    except Exception as exc:
        preview = content[:800].replace("\n", "\\n")
        raise RuntimeError(
            f"Failed to parse FPT extraction for chunk {chunk.chunk_id}. "
            f"Response preview: {preview}"
        ) from exc
