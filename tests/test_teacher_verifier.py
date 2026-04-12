"""Smoke tests: imports and optional live check (requires GEMINI_API_KEY)."""

from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.asyncio

async def test_teacher_and_verifier_setup_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid Playwright + Gemini: stub tools/LLMs and compile the debate graph."""

    async def fake_get_all_tools():
        return [], None, None

    from langchain_core.messages import AIMessage
    from master.agents.debate import EvaluatorOutput

    class _FakeTeacherLLM:
        def bind_tools(self, _tools):
            return self

        def invoke(self, _messages):
            return AIMessage(content="The answer is 4.")

    class _FakeVerifierLLM:
        def with_structured_output(self, _schema):
            return self

        def invoke(self, _messages):
            return EvaluatorOutput(
                feedback="OK",
                success_criteria_met=True,
                needs_user_input=False,
            )

    _llm_calls = {"n": 0}

    monkeypatch.setattr(
        "master.agents.debate.get_all_tools",
        fake_get_all_tools,
    )
    from master.agents.common.llm_client import LLMClient

    def _fake_chat_model(**_kwargs):
        _llm_calls["n"] += 1
        if _llm_calls["n"] % 2 == 1:
            return _FakeTeacherLLM()
        return _FakeVerifierLLM()

    monkeypatch.setattr(LLMClient, "get_chat_model", _fake_chat_model)

    from master.agents.debate import Debate
    from master.agents.teacher.teacher import TeacherAgent
    from master.agents.verifier.verifier import VerifierAgent

    debate = Debate()
    await debate.setup()
    assert debate.graph is not None

    teacher = TeacherAgent()
    await teacher.setup()
    assert teacher.graph is not None

    verifier = VerifierAgent()
    await verifier.setup()
    assert verifier.graph is not None


@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
async def test_debate_one_superstep_live() -> None:
    from master.agents.debate import Debate

    debate = Debate()
    try:
        await debate.setup()
        out = await debate.run_superstep(
            questions="2+2=?",
            success_criteria="Give the correct integer.",
            history=[],
        )
        assert len(out) >= 3
    finally:
        await debate.cleanup()
