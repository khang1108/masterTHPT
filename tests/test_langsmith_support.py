"""Unit tests for the optional LangSmith tracing helpers."""

from __future__ import annotations

from master.agents.common.langsmith import (
    build_langsmith_invoke_config,
    build_langsmith_metadata,
    build_langsmith_tags,
)
from master.agents.common.llm_client import LLMClient


def test_build_langsmith_tags_and_metadata_are_stable() -> None:
    """Helper output should include the key routing information for traces."""

    tags = build_langsmith_tags(
        agent_role="teacher",
        provider="openai_compatible",
        extra_tags=["draft", "draft"],
    )
    metadata = build_langsmith_metadata(
        agent_role="teacher",
        provider="openai_compatible",
        model_name="gemma-4-31B-it",
        extra_metadata={"phase": "draft"},
    )
    config = build_langsmith_invoke_config(
        run_name="TeacherAgent.run_draft",
        agent_role="teacher",
        provider="openai_compatible",
        model_name="gemma-4-31B-it",
        thread_id="thread-123",
        extra_tags=["draft"],
        extra_metadata={"phase": "draft"},
    )

    assert "project:master" in tags
    assert "agent:teacher" in tags
    assert "provider:openai_compatible" in tags
    assert tags.count("draft") == 1

    assert metadata["agent_role"] == "teacher"
    assert metadata["llm_provider"] == "openai_compatible"
    assert metadata["ls_model_name"] == "gemma-4-31B-it"
    assert metadata["phase"] == "draft"

    assert config["run_name"] == "TeacherAgent.run_draft"
    assert config["configurable"]["thread_id"] == "thread-123"
    assert "agent:teacher" in config["tags"]
    assert config["metadata"]["ls_model_name"] == "gemma-4-31B-it"


def test_llm_client_attaches_langsmith_metadata_to_model() -> None:
    """Constructed chat models should carry LangSmith-friendly tags and metadata."""

    llm = LLMClient.chat_model(
        provider="openai_compatible",
        base_url="http://localhost:1234/v1",
        api_key="test-key",
        model="demo-model",
        agent_role="adaptive",
    )

    assert "agent:adaptive" in llm.tags
    assert "provider:openai_compatible" in llm.tags
    assert llm.metadata["agent_role"] == "adaptive"
    assert llm.metadata["llm_model"] == "demo-model"
    assert llm.metadata["ls_model_name"] == "demo-model"
