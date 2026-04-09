# Module A: Agent Core Infrastructure — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared agent infrastructure (config, LLM client, message protocol, BaseAgent, FastAPI server) plus Manager Agent and Adaptive Agent — everything Phúc depends on.

**Architecture:** A FastAPI server at port 8000 dispatches TaskRequests to a ManagerAgent which classifies intent, builds a DAG, and orchestrates sub-agents (Parser, Teacher, Verifier, Adaptive). Each agent extends BaseAgent and uses a shared LLMClient that transparently routes between vLLM (A100) and Gemini fallback.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, httpx (async), google-generativeai, uvicorn

---

## File Structure

```
master/agents/
├── src/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py              ← All env-based configuration
│   │   ├── llm_client.py          ← Unified vLLM + Gemini client
│   │   ├── message.py             ← Pydantic models, enums, schemas
│   │   └── tools.py               ← Tool registration framework
│   ├── base_agent.py              ← Abstract base class for all agents
│   ├── manager/
│   │   ├── __init__.py
│   │   ├── intent.py              ← Intent classification
│   │   ├── planner.py             ← DAG construction per intent
│   │   └── agent.py               ← ManagerAgent implementation
│   ├── adaptive/
│   │   ├── __init__.py
│   │   ├── bkt.py                 ← Bayesian Knowledge Tracing
│   │   ├── irt.py                 ← Item Response Theory
│   │   ├── cat.py                 ← Computerized Adaptive Testing
│   │   └── agent.py               ← AdaptiveAgent implementation
│   └── server.py                  ← FastAPI app + endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_llm_client.py
│   ├── test_message.py
│   ├── test_base_agent.py
│   ├── test_manager.py
│   └── test_adaptive.py
└── requirements.txt
```

---

## Chunk 1: Foundation — common/ + BaseAgent + FastAPI skeleton

### Task 1: Project Setup & Dependencies

**Files:**
- Create: `master/agents/requirements.txt`
- Create: `master/agents/src/__init__.py`
- Create: `master/agents/src/common/__init__.py`

- [ ] **Step 1: Write requirements.txt**

```txt
# master/agents/requirements.txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.27.0
google-generativeai>=0.8.0
python-multipart>=0.0.9
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

- [ ] **Step 2: Create virtual environment and install**

Run:
```bash
cd master/agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install successfully.

- [ ] **Step 3: Create __init__.py files**

```python
# master/agents/src/__init__.py
# (empty)
```

```python
# master/agents/src/common/__init__.py
from .config import settings
from .llm_client import LLMClient
from .message import TaskRequest, TaskResponse, Intent, ErrorType
```

- [ ] **Step 4: Commit**

```bash
git add master/agents/requirements.txt master/agents/src/__init__.py master/agents/src/common/__init__.py
git commit -m "feat(agents): init project with dependencies and package structure"
```

---

### Task 2: Configuration — `common/config.py`

**Files:**
- Create: `master/agents/src/common/config.py`
- Test: `master/agents/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_config.py
import os
import pytest


def test_settings_loads_defaults():
    """Settings should have sensible defaults even without .env"""
    from src.common.config import Settings
    s = Settings(
        MONGODB_URI="mongodb://localhost:27017/test",
        GEMINI_API_KEY="test-key",
    )
    assert s.AGENT_SERVICE_PORT == 8000
    assert s.USE_GEMINI_FALLBACK is False
    assert s.VLLM_BASE_URL == "http://localhost"


def test_settings_model_url_for_vllm():
    from src.common.config import Settings
    s = Settings(
        MONGODB_URI="mongodb://localhost:27017/test",
        GEMINI_API_KEY="test-key",
        VLLM_BASE_URL="http://gpu-server",
        VLLM_MANAGER_PORT=8080,
    )
    assert s.get_vllm_url("manager") == "http://gpu-server:8080/v1"


def test_settings_gemini_fallback():
    from src.common.config import Settings
    s = Settings(
        MONGODB_URI="mongodb://localhost:27017/test",
        GEMINI_API_KEY="test-key",
        USE_GEMINI_FALLBACK=True,
    )
    assert s.USE_GEMINI_FALLBACK is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_config.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/common/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    AGENT_SERVICE_PORT: int = 8000
    GRADING_ENGINE_URL: str = "http://localhost:8001"

    # MongoDB
    MONGODB_URI: str

    # vLLM endpoints (A100 GPU server)
    VLLM_BASE_URL: str = "http://localhost"
    VLLM_MANAGER_PORT: int = 8080
    VLLM_TEACHER_PORT: int = 8081
    VLLM_VERIFIER_PORT: int = 8082

    # Model identifiers (used in vLLM /v1/chat/completions "model" field)
    LLM_MANAGER_MODEL: str = "Qwen3-8B"
    LLM_TEACHER_MODEL: str = "Qwen3-14B-Quantized"
    LLM_VERIFIER_MODEL: str = "Gemma-3-4B"

    # Gemini fallback
    USE_GEMINI_FALLBACK: bool = False
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # LLM defaults
    LLM_DEFAULT_TEMPERATURE: float = 0.3
    LLM_DEFAULT_MAX_TOKENS: int = 4096

    def get_vllm_url(self, agent_role: str) -> str:
        port_map = {
            "manager": self.VLLM_MANAGER_PORT,
            "teacher": self.VLLM_TEACHER_PORT,
            "verifier": self.VLLM_VERIFIER_PORT,
        }
        port = port_map.get(agent_role, self.VLLM_MANAGER_PORT)
        return f"{self.VLLM_BASE_URL}:{port}/v1"

    def get_model_name(self, agent_role: str) -> str:
        model_map = {
            "manager": self.LLM_MANAGER_MODEL,
            "teacher": self.LLM_TEACHER_MODEL,
            "verifier": self.LLM_VERIFIER_MODEL,
        }
        return model_map.get(agent_role, self.LLM_MANAGER_MODEL)

    model_config = {"env_file": "../../.env", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_config.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/common/config.py master/agents/tests/test_config.py
git commit -m "feat(common): add Settings config with vLLM + Gemini fallback support"
```

---

### Task 3: Message Protocol — `common/message.py`

**Files:**
- Create: `master/agents/src/common/message.py`
- Test: `master/agents/tests/test_message.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_message.py
import pytest
from src.common.message import (
    Intent, ErrorType, TaskRequest, TaskResponse,
    ExamQuestion, ExamSection, ExamData,
    QuestionEvaluation, ErrorAnalysis, EvaluationResult,
    AgentMessage,
)


def test_intent_enum_has_all_values():
    assert Intent.EXAM_PRACTICE.value == "EXAM_PRACTICE"
    assert Intent.GRADE_SUBMISSION.value == "GRADE_SUBMISSION"
    assert Intent.VIEW_ANALYSIS.value == "VIEW_ANALYSIS"
    assert Intent.ASK_HINT.value == "ASK_HINT"
    assert Intent.REVIEW_MISTAKE.value == "REVIEW_MISTAKE"
    assert Intent.UNKNOWN.value == "UNKNOWN"


def test_error_type_enum():
    assert ErrorType.CONCEPT_GAP.value == "CONCEPT_GAP"
    assert len(ErrorType) == 5


def test_task_request_creation():
    req = TaskRequest(
        student_id="student-123",
        intent=Intent.GRADE_SUBMISSION,
        user_message="Chấm bài cho tôi",
    )
    assert req.intent == Intent.GRADE_SUBMISSION
    assert req.file_urls == []
    assert req.metadata == {}


def test_task_response_creation():
    resp = TaskResponse(
        task_id="task-1",
        status="success",
        intent=Intent.GRADE_SUBMISSION,
        result={"total_score": 7.25},
        agent_trail=["manager", "teacher"],
    )
    assert resp.status == "success"
    assert len(resp.agent_trail) == 2


def test_evaluation_result():
    err = ErrorAnalysis(
        error_type=ErrorType.CALCULATION_ERROR,
        root_cause="Wrong formula",
        knowledge_component="math.12.ch4.solid_geometry",
        remedial="Review chapter 4",
    )
    q_eval = QuestionEvaluation(
        question_id="q1",
        student_answer="A",
        correct_answer="B",
        is_correct=False,
        score=0.0,
        max_score=0.2,
        reasoning="Wrong answer",
        error_analysis=err,
    )
    result = EvaluationResult(
        evaluation_id="eval-1",
        exam_id="exam-1",
        student_id="student-1",
        total_score=0.0,
        max_score=10.0,
        confidence=0.9,
        per_question=[q_eval],
    )
    assert result.per_question[0].error_analysis.error_type == ErrorType.CALCULATION_ERROR


def test_exam_data_structure():
    q = ExamQuestion(
        id="q1",
        question_index=1,
        type="multiple_choice",
        content="What is 2+2?",
        options=["A. 3", "B. 4", "C. 5", "D. 6"],
        correct_answer="B",
        topic_tags=["math.10.ch1.arithmetic"],
        max_score=0.2,
    )
    section = ExamSection(type="multiple_choice", questions=[q])
    exam = ExamData(
        exam_id="exam-1",
        source="manual",
        subject="math",
        exam_type="THPTQG",
        total_questions=1,
        sections=[section],
    )
    assert exam.sections[0].questions[0].id == "q1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_message.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/common/message.py
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class Intent(str, Enum):
    EXAM_PRACTICE = "EXAM_PRACTICE"
    GRADE_SUBMISSION = "GRADE_SUBMISSION"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    UNKNOWN = "UNKNOWN"


class ErrorType(str, Enum):
    CONCEPT_GAP = "CONCEPT_GAP"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    INCOMPLETE_REASONING = "INCOMPLETE_REASONING"
    MISINTERPRETATION = "MISINTERPRETATION"
    PRESENTATION_FLAW = "PRESENTATION_FLAW"


# --- TaskRequest / TaskResponse (NestJS <-> Agent Service) ---

class TaskRequest(BaseModel):
    student_id: str
    intent: Intent
    user_message: str
    session_id: Optional[str] = None
    file_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str  # "success" | "error"
    intent: Intent
    result: dict[str, Any] = Field(default_factory=dict)
    agent_trail: list[str] = Field(default_factory=list)
    error_message: Optional[str] = None


# --- Exam JSON Schema ---

class ExamQuestion(BaseModel):
    id: str
    question_index: int
    type: str  # "multiple_choice" | "essay"
    content: str
    content_latex: Optional[str] = None
    options: Optional[list[str]] = None
    correct_answer: Optional[str] = None
    has_image: bool = False
    image_url: Optional[str] = None
    difficulty_a: float = 1.0
    difficulty_b: float = 0.0
    topic_tags: list[str] = Field(default_factory=list)
    max_score: float = 0.2


class ExamSection(BaseModel):
    type: str
    questions: list[ExamQuestion]


class ExamData(BaseModel):
    exam_id: str
    source: str  # "image" | "pdf" | "manual"
    subject: str
    exam_type: str
    total_questions: int
    sections: list[ExamSection]
    duration_minutes: Optional[int] = None


# --- Evaluation JSON Schema ---

class ErrorAnalysis(BaseModel):
    error_type: ErrorType
    root_cause: str
    knowledge_component: str
    remedial: str


class QuestionEvaluation(BaseModel):
    question_id: str
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: bool
    score: float
    max_score: float
    reasoning: str
    error_analysis: Optional[ErrorAnalysis] = None


class OverallAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    evaluation_id: str
    exam_id: str
    student_id: str
    total_score: float
    max_score: float
    confidence: float
    per_question: list[QuestionEvaluation] = Field(default_factory=list)
    overall_analysis: Optional[OverallAnalysis] = None


# --- Internal Agent Communication ---

class AgentMessage(BaseModel):
    """Message passed between agents in the pipeline."""
    from_agent: str
    to_agent: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_message.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/common/message.py master/agents/tests/test_message.py
git commit -m "feat(common): add Pydantic message models — TaskRequest, TaskResponse, Exam, Evaluation schemas"
```

---

### Task 4: LLM Client — `common/llm_client.py`

**Files:**
- Create: `master/agents/src/common/llm_client.py`
- Test: `master/agents/tests/test_llm_client.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_llm_client.py
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.common.llm_client import LLMClient


@pytest.fixture
def vllm_client():
    """LLMClient configured for vLLM (no Gemini fallback)."""
    return LLMClient(
        vllm_base_url="http://fake-gpu:8080/v1",
        model_name="Qwen3-8B",
        use_gemini=False,
    )


@pytest.fixture
def gemini_client():
    """LLMClient configured for Gemini fallback."""
    return LLMClient(
        gemini_api_key="fake-key",
        gemini_model="gemini-2.5-flash",
        use_gemini=True,
    )


@pytest.mark.asyncio
async def test_vllm_chat_builds_correct_request(vllm_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(vllm_client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await vllm_client.chat([
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ])
        assert result == "Hello!"


@pytest.mark.asyncio
async def test_vllm_chat_json_parses_response(vllm_client):
    json_str = '{"intent": "GRADE_SUBMISSION", "confidence": 0.95}'
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": json_str}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(vllm_client._http, "post", new_callable=AsyncMock, return_value=mock_response):
        result = await vllm_client.chat_json([
            {"role": "user", "content": "classify intent"},
        ])
        assert result["intent"] == "GRADE_SUBMISSION"
        assert result["confidence"] == 0.95


def test_client_initialization_vllm():
    client = LLMClient(
        vllm_base_url="http://gpu:8080/v1",
        model_name="Qwen3-8B",
        use_gemini=False,
    )
    assert client._use_gemini is False
    assert client._model_name == "Qwen3-8B"


def test_client_initialization_gemini():
    client = LLMClient(
        gemini_api_key="key",
        gemini_model="gemini-2.5-flash",
        use_gemini=True,
    )
    assert client._use_gemini is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_llm_client.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/common/llm_client.py
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client that transparently routes between vLLM and Gemini.

    vLLM mode: calls OpenAI-compatible /v1/chat/completions on GPU server.
    Gemini mode: calls Google GenAI SDK as fallback when GPU is unavailable.
    """

    def __init__(
        self,
        *,
        vllm_base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        use_gemini: bool = False,
        gemini_api_key: Optional[str] = None,
        gemini_model: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: float = 120.0,
    ):
        self._use_gemini = use_gemini
        self._temperature = temperature
        self._max_tokens = max_tokens

        if use_gemini:
            self._gemini_api_key = gemini_api_key
            self._gemini_model = gemini_model
            self._model_name = gemini_model
            self._gemini_client = None  # lazy init
        else:
            self._vllm_base_url = vllm_base_url
            self._model_name = model_name or "default"
            self._http = httpx.AsyncClient(
                base_url=vllm_base_url,
                timeout=timeout,
            )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send chat messages and return the assistant's text response."""
        temp = temperature if temperature is not None else self._temperature
        tokens = max_tokens if max_tokens is not None else self._max_tokens

        if self._use_gemini:
            return await self._chat_gemini(messages, temp, tokens)
        else:
            return await self._chat_vllm(messages, temp, tokens)

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """Send chat messages and parse the response as JSON."""
        messages_with_json_hint = list(messages)
        if messages_with_json_hint and messages_with_json_hint[-1]["role"] == "user":
            messages_with_json_hint[-1] = {
                **messages_with_json_hint[-1],
                "content": messages_with_json_hint[-1]["content"]
                + "\n\nRespond ONLY with valid JSON. No markdown, no explanation.",
            }

        raw = await self.chat(messages_with_json_hint, temperature=temperature, max_tokens=max_tokens)
        return self._extract_json(raw)

    # --- vLLM backend (OpenAI-compatible API) ---

    async def _chat_vllm(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> str:
        payload = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        logger.debug("vLLM request to %s: model=%s", self._vllm_base_url, self._model_name)

        response = await self._http.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    # --- Gemini backend ---

    async def _chat_gemini(
        self, messages: list[dict], temperature: float, max_tokens: int
    ) -> str:
        if self._gemini_client is None:
            import google.generativeai as genai
            genai.configure(api_key=self._gemini_api_key)
            self._gemini_client = genai.GenerativeModel(self._gemini_model)

        system_msg = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                chat_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                chat_messages.append({"role": "model", "parts": [msg["content"]]})

        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if system_msg:
            model = self._gemini_client
            # Gemini supports system_instruction in newer SDK versions
            try:
                import google.generativeai as genai
                model = genai.GenerativeModel(
                    self._gemini_model,
                    system_instruction=system_msg,
                    generation_config=generation_config,
                )
            except TypeError:
                chat_messages.insert(0, {"role": "user", "parts": [f"[System]: {system_msg}"]})
                model = self._gemini_client

        chat = model.start_chat(history=chat_messages[:-1] if len(chat_messages) > 1 else [])
        last_msg = chat_messages[-1]["parts"][0] if chat_messages else ""
        response = chat.send_message(last_msg)
        return response.text

    # --- JSON extraction ---

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code fences."""
        cleaned = text.strip()
        # Remove ```json ... ``` wrapper
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        return json.loads(cleaned)

    async def close(self):
        if hasattr(self, "_http"):
            await self._http.aclose()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_llm_client.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/common/llm_client.py master/agents/tests/test_llm_client.py
git commit -m "feat(common): add LLMClient with vLLM + Gemini dual-backend support"
```

---

### Task 5: Tool Registry — `common/tools.py`

**Files:**
- Create: `master/agents/src/common/tools.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/common/tools.py
from __future__ import annotations

import logging
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

ToolFunction = Callable[..., Awaitable[Any]]


class ToolDefinition:
    """Describes a tool that an agent can invoke."""

    def __init__(self, name: str, description: str, fn: ToolFunction):
        self.name = name
        self.description = description
        self.fn = fn

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
        }


class ToolRegistry:
    """Registry of tools available to an agent."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, fn: ToolFunction) -> None:
        self._tools[name] = ToolDefinition(name=name, description=description, fn=fn)
        logger.debug("Registered tool: %s", name)

    async def execute(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}. Available: {list(self._tools.keys())}")
        logger.info("Executing tool: %s with args: %s", name, list(kwargs.keys()))
        return await self._tools[name].fn(**kwargs)

    def list_schemas(self) -> list[dict]:
        return [t.to_schema() for t in self._tools.values()]

    def has(self, name: str) -> bool:
        return name in self._tools
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/common/tools.py
git commit -m "feat(common): add ToolRegistry for agent tool management"
```

---

### Task 6: Enhanced BaseAgent — `base_agent.py`

**Files:**
- Create: `master/agents/src/base_agent.py` (replaces old `master/agents/baseagent.py`)
- Test: `master/agents/tests/test_base_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_base_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.base_agent import BaseAgent
from src.common.llm_client import LLMClient
from src.common.tools import ToolRegistry


class MockAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return "You are a test agent."

    @property
    def description(self) -> str:
        return "A mock agent for testing."

    async def handle(self, payload: dict) -> dict:
        return {"echo": payload.get("input", "")}


@pytest.fixture
def mock_llm():
    client = MagicMock(spec=LLMClient)
    client.chat = AsyncMock(return_value="Hello from LLM")
    client.chat_json = AsyncMock(return_value={"key": "value"})
    return client


@pytest.fixture
def agent(mock_llm):
    return MockAgent(name="test-agent", llm_client=mock_llm)


def test_agent_name(agent):
    assert agent.name == "test-agent"


def test_agent_has_tool_registry(agent):
    assert isinstance(agent.tools, ToolRegistry)


@pytest.mark.asyncio
async def test_run_returns_handle_result(agent):
    result = await agent.run({"input": "hello"})
    assert result == {"echo": "hello"}


@pytest.mark.asyncio
async def test_run_catches_exceptions(mock_llm):
    class FailAgent(BaseAgent):
        @property
        def system_prompt(self):
            return "fail"

        @property
        def description(self):
            return "fail"

        async def handle(self, payload):
            raise ValueError("test error")

    agent = FailAgent(name="fail-agent", llm_client=mock_llm)
    result = await agent.run({})
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_think_calls_llm(agent, mock_llm):
    result = await agent.think("What is 2+2?")
    assert result == "Hello from LLM"
    mock_llm.chat.assert_called_once()


@pytest.mark.asyncio
async def test_think_json_calls_llm(agent, mock_llm):
    result = await agent.think_json("Return JSON")
    assert result == {"key": "value"}
    mock_llm.chat_json.assert_called_once()


@pytest.mark.asyncio
async def test_register_and_execute_tool(agent):
    async def add(a: int, b: int) -> int:
        return a + b

    agent.register_tool("add", "Add two numbers", add)
    assert agent.tools.has("add")
    result = await agent.execute_tool("add", a=1, b=2)
    assert result == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_base_agent.py -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/base_agent.py
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from .common.llm_client import LLMClient
from .common.tools import ToolRegistry

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all MASTER agents.

    Subclasses must implement:
        - system_prompt (property): the system-level instruction for this agent
        - description (property): one-line description of what this agent does
        - handle(payload) -> dict: the core logic
    """

    def __init__(self, name: str, llm_client: LLMClient):
        self.name = name
        self._llm = llm_client
        self.tools = ToolRegistry()

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute handle() with logging, timing, and error handling."""
        start = time.monotonic()
        logger.info("[%s] START — payload keys: %s", self.name, list(payload.keys()))
        try:
            result = await self.handle(payload)
            elapsed = time.monotonic() - start
            logger.info("[%s] DONE in %.2fs", self.name, elapsed)
            return result
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error("[%s] FAILED in %.2fs: %s", self.name, elapsed, e, exc_info=True)
            return {"error": str(e), "agent": self.name}

    async def think(self, user_message: str, **kwargs: Any) -> str:
        """Shortcut: send a message to the LLM with this agent's system prompt."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self._llm.chat(messages, **kwargs)

    async def think_json(self, user_message: str, **kwargs: Any) -> dict[str, Any]:
        """Shortcut: send a message and parse the response as JSON."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self._llm.chat_json(messages, **kwargs)

    def register_tool(self, name: str, description: str, fn: Any) -> None:
        self.tools.register(name, description, fn)

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        return await self.tools.execute(name, **kwargs)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_base_agent.py -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/base_agent.py master/agents/tests/test_base_agent.py
git commit -m "feat(agents): add enhanced BaseAgent with think/tools/error-handling"
```

---

### Task 7: FastAPI Server Skeleton — `server.py`

**Files:**
- Create: `master/agents/src/server.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/server.py
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .common.config import settings
from .common.llm_client import LLMClient
from .common.message import TaskRequest, TaskResponse, Intent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="MASTER Agent Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LLM Clients (one per agent role) ---

def _build_llm_client(role: str) -> LLMClient:
    if settings.USE_GEMINI_FALLBACK:
        return LLMClient(
            gemini_api_key=settings.GEMINI_API_KEY,
            gemini_model=settings.GEMINI_MODEL,
            use_gemini=True,
            temperature=settings.LLM_DEFAULT_TEMPERATURE,
            max_tokens=settings.LLM_DEFAULT_MAX_TOKENS,
        )
    return LLMClient(
        vllm_base_url=settings.get_vllm_url(role),
        model_name=settings.get_model_name(role),
        use_gemini=False,
        temperature=settings.LLM_DEFAULT_TEMPERATURE,
        max_tokens=settings.LLM_DEFAULT_MAX_TOKENS,
    )


manager_llm = _build_llm_client("manager")
teacher_llm = _build_llm_client("teacher")
verifier_llm = _build_llm_client("verifier")

# --- Agent instances (lazy-imported to allow Module B to implement later) ---
# These will be initialized properly once all agents are implemented.
# For now, the dispatch endpoint handles the routing logic.


@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-service"}


@app.post("/api/agents/dispatch", response_model=TaskResponse)
async def dispatch(request: TaskRequest):
    """Main dispatch endpoint.

    Receives a TaskRequest from NestJS API, routes to the appropriate agent
    pipeline based on intent, and returns a TaskResponse.
    """
    logger.info("Dispatch: student=%s intent=%s", request.student_id, request.intent)

    try:
        # Phase 1 (MVP): Simple intent-based routing
        # Phase 2: Manager Agent will handle this dynamically
        if request.intent == Intent.GRADE_SUBMISSION:
            result = await _handle_grade_submission(request)
        elif request.intent == Intent.EXAM_PRACTICE:
            result = await _handle_exam_practice(request)
        elif request.intent == Intent.VIEW_ANALYSIS:
            result = await _handle_view_analysis(request)
        elif request.intent == Intent.ASK_HINT:
            result = await _handle_ask_hint(request)
        elif request.intent == Intent.REVIEW_MISTAKE:
            result = await _handle_review_mistake(request)
        else:
            result = TaskResponse(
                status="error",
                intent=request.intent,
                error_message=f"Unknown intent: {request.intent}",
            )
        return result
    except Exception as e:
        logger.error("Dispatch failed: %s", e, exc_info=True)
        return TaskResponse(
            status="error",
            intent=request.intent,
            error_message=str(e),
        )


# --- Stub handlers (will be replaced with actual agent calls) ---

async def _handle_grade_submission(req: TaskRequest) -> TaskResponse:
    """Pipeline: Parser -> Teacher -> Verifier -> Adaptive"""
    # TODO: Wire actual agents once Module B is implemented
    return TaskResponse(
        status="success",
        intent=req.intent,
        result={"message": "GRADE_SUBMISSION pipeline not yet implemented"},
        agent_trail=["manager"],
    )


async def _handle_exam_practice(req: TaskRequest) -> TaskResponse:
    return TaskResponse(
        status="success",
        intent=req.intent,
        result={"message": "EXAM_PRACTICE pipeline not yet implemented"},
        agent_trail=["manager"],
    )


async def _handle_view_analysis(req: TaskRequest) -> TaskResponse:
    return TaskResponse(
        status="success",
        intent=req.intent,
        result={"message": "VIEW_ANALYSIS not yet implemented"},
        agent_trail=["manager"],
    )


async def _handle_ask_hint(req: TaskRequest) -> TaskResponse:
    return TaskResponse(
        status="success",
        intent=req.intent,
        result={"message": "ASK_HINT not yet implemented"},
        agent_trail=["manager"],
    )


async def _handle_review_mistake(req: TaskRequest) -> TaskResponse:
    return TaskResponse(
        status="success",
        intent=req.intent,
        result={"message": "REVIEW_MISTAKE not yet implemented"},
        agent_trail=["manager"],
    )


@app.post("/api/agents/parse")
async def parse_file():
    """Direct file parsing endpoint (multipart upload)."""
    # TODO: Implement when ParserAgent is ready (Module B)
    raise HTTPException(status_code=501, detail="Not implemented yet")


@app.on_event("shutdown")
async def shutdown():
    await manager_llm.close()
    await teacher_llm.close()
    await verifier_llm.close()
```

- [ ] **Step 2: Test server starts**

Run:
```bash
cd master/agents
USE_GEMINI_FALLBACK=true GEMINI_API_KEY=test MONGODB_URI=mongodb://localhost:27017/test \
  uvicorn src.server:app --host 0.0.0.0 --port 8000
```
Expected: Server starts at http://0.0.0.0:8000. Hit `GET /health` → `{"status":"ok"}`

- [ ] **Step 3: Commit**

```bash
git add master/agents/src/server.py
git commit -m "feat(agents): add FastAPI server skeleton with dispatch + health endpoints"
```

---

## Chunk 2: Manager Agent

### Task 8: Intent Classifier — `manager/intent.py`

**Files:**
- Create: `master/agents/src/manager/__init__.py`
- Create: `master/agents/src/manager/intent.py`
- Test: `master/agents/tests/test_manager.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.common.message import Intent


def test_classify_grade_submission_by_keywords():
    from src.manager.intent import classify_intent_by_rules
    assert classify_intent_by_rules("Chấm bài cho tôi") == Intent.GRADE_SUBMISSION
    assert classify_intent_by_rules("grade my submission") == Intent.GRADE_SUBMISSION


def test_classify_exam_practice_by_keywords():
    from src.manager.intent import classify_intent_by_rules
    assert classify_intent_by_rules("Tôi muốn làm đề thi thử Toán") == Intent.EXAM_PRACTICE
    assert classify_intent_by_rules("bắt đầu làm bài") == Intent.EXAM_PRACTICE


def test_classify_view_analysis():
    from src.manager.intent import classify_intent_by_rules
    assert classify_intent_by_rules("xem phân tích năng lực") == Intent.VIEW_ANALYSIS


def test_classify_ask_hint():
    from src.manager.intent import classify_intent_by_rules
    assert classify_intent_by_rules("cho tôi gợi ý câu 3") == Intent.ASK_HINT


def test_classify_review_mistake():
    from src.manager.intent import classify_intent_by_rules
    assert classify_intent_by_rules("xem lại lỗi sai") == Intent.REVIEW_MISTAKE


def test_classify_unknown_for_ambiguous():
    from src.manager.intent import classify_intent_by_rules
    assert classify_intent_by_rules("hello") == Intent.UNKNOWN
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/manager/__init__.py
# (empty)
```

```python
# master/agents/src/manager/intent.py
from __future__ import annotations

import re
from ..common.message import Intent
from ..common.llm_client import LLMClient

INTENT_RULES: list[tuple[Intent, list[str]]] = [
    (Intent.GRADE_SUBMISSION, [
        r"chấm\s*bài", r"grade", r"nộp\s*bài", r"submit", r"chấm\s*điểm",
        r"kiểm\s*tra\s*bài", r"xem\s*điểm\s*bài", r"upload.*bài",
    ]),
    (Intent.EXAM_PRACTICE, [
        r"làm\s*(đề|bài)\s*thi", r"luyện\s*thi", r"bắt\s*đầu\s*làm",
        r"thi\s*thử", r"practice", r"exam", r"làm\s*bài",
        r"đề\s*thi", r"kiểm\s*tra",
    ]),
    (Intent.VIEW_ANALYSIS, [
        r"phân\s*tích", r"năng\s*lực", r"analysis", r"profile",
        r"thống\s*kê", r"dashboard", r"tiến\s*độ",
    ]),
    (Intent.ASK_HINT, [
        r"gợi\s*ý", r"hint", r"trợ\s*giúp", r"help\s*me",
        r"hướng\s*dẫn", r"giải\s*thích",
    ]),
    (Intent.REVIEW_MISTAKE, [
        r"lỗi\s*sai", r"mistake", r"xem\s*lại", r"review",
        r"sai\s*ở\s*đâu", r"lịch\s*sử\s*lỗi",
    ]),
]


def classify_intent_by_rules(message: str) -> Intent:
    """Rule-based intent classification using regex patterns.
    Fast and deterministic — used as first pass before LLM fallback.
    """
    text = message.lower().strip()
    for intent, patterns in INTENT_RULES:
        for pattern in patterns:
            if re.search(pattern, text):
                return intent
    return Intent.UNKNOWN


async def classify_intent_with_llm(message: str, llm: LLMClient) -> Intent:
    """LLM-based intent classification — fallback for ambiguous messages."""
    prompt = f"""Classify the following user message into exactly one intent.

Valid intents: EXAM_PRACTICE, GRADE_SUBMISSION, VIEW_ANALYSIS, ASK_HINT, REVIEW_MISTAKE, UNKNOWN

User message: "{message}"

Respond with ONLY the intent name, nothing else."""

    result = await llm.chat([{"role": "user", "content": prompt}], temperature=0.0)
    result = result.strip().upper()

    try:
        return Intent(result)
    except ValueError:
        return Intent.UNKNOWN


async def classify_intent(message: str, llm: LLMClient | None = None) -> Intent:
    """Two-phase intent classification: rules first, LLM if UNKNOWN."""
    intent = classify_intent_by_rules(message)
    if intent != Intent.UNKNOWN or llm is None:
        return intent
    return await classify_intent_with_llm(message, llm)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_manager.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/manager/ master/agents/tests/test_manager.py
git commit -m "feat(manager): add intent classifier with rule-based + LLM fallback"
```

---

### Task 9: DAG Planner — `manager/planner.py`

**Files:**
- Create: `master/agents/src/manager/planner.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/manager/planner.py
from __future__ import annotations

from dataclasses import dataclass
from ..common.message import Intent


@dataclass
class PlanStep:
    agent: str
    action: str
    depends_on: list[str]


DAG_REGISTRY: dict[Intent, list[PlanStep]] = {
    Intent.GRADE_SUBMISSION: [
        PlanStep(agent="parser", action="parse_image", depends_on=[]),
        PlanStep(agent="teacher", action="grade", depends_on=["parser"]),
        PlanStep(agent="verifier", action="verify", depends_on=["teacher"]),
        PlanStep(agent="adaptive", action="update_profile", depends_on=["verifier"]),
    ],
    Intent.EXAM_PRACTICE: [
        PlanStep(agent="adaptive", action="select_exam", depends_on=[]),
    ],
    Intent.VIEW_ANALYSIS: [
        PlanStep(agent="adaptive", action="get_profile", depends_on=[]),
    ],
    Intent.ASK_HINT: [
        PlanStep(agent="teacher", action="generate_hint", depends_on=[]),
    ],
    Intent.REVIEW_MISTAKE: [
        PlanStep(agent="adaptive", action="get_mistake_history", depends_on=[]),
    ],
    Intent.UNKNOWN: [],
}


def get_execution_plan(intent: Intent) -> list[PlanStep]:
    """Return the ordered execution plan for a given intent.

    DAG is pre-defined (no dynamic LLM planning in MVP).
    Steps are returned in topological order.
    """
    return DAG_REGISTRY.get(intent, [])
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/manager/planner.py
git commit -m "feat(manager): add static DAG planner for all 6 intents"
```

---

### Task 10: Manager Agent — `manager/agent.py`

**Files:**
- Create: `master/agents/src/manager/agent.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/manager/agent.py
from __future__ import annotations

import logging
from typing import Any

from ..base_agent import BaseAgent
from ..common.llm_client import LLMClient
from ..common.message import Intent, TaskRequest, TaskResponse
from .intent import classify_intent
from .planner import get_execution_plan

logger = logging.getLogger(__name__)


class ManagerAgent(BaseAgent):
    """Central orchestrator that classifies intent and dispatches to sub-agents."""

    def __init__(self, llm_client: LLMClient, agent_registry: dict[str, BaseAgent] | None = None):
        super().__init__(name="manager", llm_client=llm_client)
        self._agents = agent_registry or {}

    @property
    def system_prompt(self) -> str:
        return (
            "You are the Manager Agent of MASTER, an EdTech multi-agent system. "
            "Your job is to understand the student's intent, plan the execution "
            "pipeline, and coordinate sub-agents to fulfill the request."
        )

    @property
    def description(self) -> str:
        return "Classifies user intent and orchestrates sub-agent execution pipeline."

    def register_agent(self, name: str, agent: BaseAgent) -> None:
        self._agents[name] = agent

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = TaskRequest(**payload) if not isinstance(payload, TaskRequest) else payload

        intent = request.intent
        if intent == Intent.UNKNOWN:
            intent = await classify_intent(request.user_message, self._llm)

        plan = get_execution_plan(intent)
        logger.info("[manager] Intent=%s, Plan=%s", intent, [s.agent for s in plan])

        agent_trail = ["manager"]
        context: dict[str, Any] = {"request": request.model_dump()}

        for step in plan:
            agent = self._agents.get(step.agent)
            if agent is None:
                logger.warning("[manager] Agent '%s' not registered, skipping", step.agent)
                continue

            step_payload = {
                "action": step.action,
                "request": request.model_dump(),
                "context": context,
            }
            result = await agent.run(step_payload)
            context[step.agent] = result
            agent_trail.append(step.agent)

            if "error" in result:
                return TaskResponse(
                    status="error",
                    intent=intent,
                    error_message=f"Agent {step.agent} failed: {result['error']}",
                    agent_trail=agent_trail,
                ).model_dump()

        final_result = context.get(plan[-1].agent, {}) if plan else {}
        return TaskResponse(
            status="success",
            intent=intent,
            result=final_result,
            agent_trail=agent_trail,
        ).model_dump()
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/manager/agent.py
git commit -m "feat(manager): add ManagerAgent with intent-to-DAG orchestration"
```

---

## Chunk 3: Adaptive Agent

### Task 11: Bayesian Knowledge Tracing — `adaptive/bkt.py`

**Files:**
- Create: `master/agents/src/adaptive/__init__.py`
- Create: `master/agents/src/adaptive/bkt.py`
- Test: `master/agents/tests/test_adaptive.py`

- [ ] **Step 1: Write the failing test**

```python
# master/agents/tests/test_adaptive.py
import pytest
from src.adaptive.bkt import BKTModel, BKTParams


def test_bkt_defaults():
    params = BKTParams()
    assert params.p_l0 == 0.1
    assert params.p_t == 0.1
    assert params.p_s == 0.05
    assert params.p_g == 0.25


def test_bkt_update_correct():
    model = BKTModel()
    params = BKTParams(p_l0=0.1)
    new_pl = model.update(params, correct=True)
    assert new_pl > params.p_l0, "P(L) should increase after correct answer"


def test_bkt_update_wrong():
    model = BKTModel()
    params = BKTParams(p_l0=0.5)
    new_pl = model.update(params, correct=False)
    # After wrong answer with moderate mastery, P(L) should decrease or stay low
    assert 0.0 <= new_pl <= 1.0


def test_bkt_mastery_increases_with_consecutive_correct():
    model = BKTModel()
    params = BKTParams(p_l0=0.1)
    pl = params.p_l0
    for _ in range(10):
        pl = model.update(BKTParams(p_l0=pl), correct=True)
    assert pl > 0.8, "10 consecutive correct should push mastery high"


def test_bkt_is_mastered():
    model = BKTModel(mastery_threshold=0.95)
    assert model.is_mastered(0.96) is True
    assert model.is_mastered(0.90) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_adaptive.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/adaptive/__init__.py
# (empty)
```

```python
# master/agents/src/adaptive/bkt.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BKTParams:
    """Parameters for a single Knowledge Component."""
    p_l0: float = 0.1   # P(L₀): prior probability of knowing the KC
    p_t: float = 0.1    # P(T): probability of learning after each attempt
    p_s: float = 0.05   # P(S): probability of slipping (knows but answers wrong)
    p_g: float = 0.25   # P(G): probability of guessing (doesn't know but answers right)


class BKTModel:
    """Bayesian Knowledge Tracing — tracks per-KC mastery."""

    def __init__(self, mastery_threshold: float = 0.95):
        self.mastery_threshold = mastery_threshold

    def update(self, params: BKTParams, correct: bool) -> float:
        """Update P(L) given student response. Returns new P(L)."""
        p_l = params.p_l0
        p_s = params.p_s
        p_g = params.p_g
        p_t = params.p_t

        if correct:
            # P(Lₙ | correct) = P(L) * (1-P(S)) / [P(L)*(1-P(S)) + (1-P(L))*P(G)]
            numerator = p_l * (1.0 - p_s)
            denominator = numerator + (1.0 - p_l) * p_g
        else:
            # P(Lₙ | wrong) = P(L) * P(S) / [P(L)*P(S) + (1-P(L))*(1-P(G))]
            numerator = p_l * p_s
            denominator = numerator + (1.0 - p_l) * (1.0 - p_g)

        p_l_given_obs = numerator / denominator if denominator > 0 else p_l

        # Apply learning transition: P(Lₙ) = P(Lₙ|obs) + (1 - P(Lₙ|obs)) * P(T)
        new_p_l = p_l_given_obs + (1.0 - p_l_given_obs) * p_t
        return min(max(new_p_l, 0.0), 1.0)

    def is_mastered(self, p_l: float) -> bool:
        return p_l >= self.mastery_threshold
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_adaptive.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/adaptive/ master/agents/tests/test_adaptive.py
git commit -m "feat(adaptive): add BKT model for per-KC mastery tracking"
```

---

### Task 12: Item Response Theory — `adaptive/irt.py`

**Files:**
- Create: `master/agents/src/adaptive/irt.py`

- [ ] **Step 1: Add tests to `tests/test_adaptive.py`**

```python
# Append to master/agents/tests/test_adaptive.py

from src.adaptive.irt import IRTModel
import math


def test_irt_probability_at_difficulty():
    model = IRTModel()
    # When theta == b, probability should be ~0.5
    p = model.probability(theta=0.0, a=1.0, b=0.0)
    assert abs(p - 0.5) < 0.01


def test_irt_high_ability_high_prob():
    model = IRTModel()
    p = model.probability(theta=2.0, a=1.0, b=0.0)
    assert p > 0.8


def test_irt_fisher_information():
    model = IRTModel()
    info = model.fisher_information(theta=0.0, a=1.0, b=0.0)
    # At theta=b, P=0.5, I = a² * 0.5 * 0.5 = 0.25
    assert abs(info - 0.25) < 0.01


def test_irt_update_theta_correct():
    model = IRTModel()
    old_theta = 0.0
    new_theta = model.update_theta(old_theta, a=1.0, b=0.0, correct=True)
    assert new_theta > old_theta


def test_irt_update_theta_wrong():
    model = IRTModel()
    old_theta = 0.0
    new_theta = model.update_theta(old_theta, a=1.0, b=0.0, correct=False)
    assert new_theta < old_theta
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd master/agents && python -m pytest tests/test_adaptive.py -v -k "irt"`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# master/agents/src/adaptive/irt.py
from __future__ import annotations

import math


class IRTModel:
    """2PL Item Response Theory model."""

    def probability(self, theta: float, a: float, b: float) -> float:
        """P(correct | theta, a, b) = 1 / (1 + exp(-a * (theta - b)))"""
        exponent = -a * (theta - b)
        exponent = max(min(exponent, 500), -500)  # prevent overflow
        return 1.0 / (1.0 + math.exp(exponent))

    def fisher_information(self, theta: float, a: float, b: float) -> float:
        """I(theta) = a² * P(theta) * (1 - P(theta))"""
        p = self.probability(theta, a, b)
        return a * a * p * (1.0 - p)

    def update_theta(
        self,
        theta: float,
        a: float,
        b: float,
        correct: bool,
        learning_rate: float = 0.3,
    ) -> float:
        """Newton-Raphson step to update ability estimate.

        Uses simplified EAP-like update:
            theta_new = theta + lr * (response - P(theta)) / I(theta)
        """
        p = self.probability(theta, a, b)
        info = self.fisher_information(theta, a, b)
        if info < 1e-10:
            return theta

        response = 1.0 if correct else 0.0
        delta = learning_rate * (response - p) / info
        # Clamp to avoid extreme jumps
        delta = max(min(delta, 1.0), -1.0)
        return theta + delta
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd master/agents && python -m pytest tests/test_adaptive.py -v -k "irt"`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add master/agents/src/adaptive/irt.py master/agents/tests/test_adaptive.py
git commit -m "feat(adaptive): add 2PL IRT model with theta estimation"
```

---

### Task 13: Computerized Adaptive Testing — `adaptive/cat.py`

**Files:**
- Create: `master/agents/src/adaptive/cat.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/adaptive/cat.py
from __future__ import annotations

from dataclasses import dataclass
from .irt import IRTModel


@dataclass
class ItemParams:
    """IRT parameters for a question item."""
    question_id: str
    a: float = 1.0  # discrimination
    b: float = 0.0  # difficulty
    topic_tags: list[str] | None = None


class CATSelector:
    """Maximum Fisher Information item selector with constraints.

    Selects the next question that maximizes information gain at the
    student's current ability level, subject to ZPD and content balance.
    """

    def __init__(self, zpd_range: float = 1.5, max_per_topic: int = 5):
        self.irt = IRTModel()
        self.zpd_range = zpd_range
        self.max_per_topic = max_per_topic

    def select_next(
        self,
        theta: float,
        item_bank: list[ItemParams],
        answered_ids: set[str],
        topic_counts: dict[str, int] | None = None,
    ) -> ItemParams | None:
        """Select the next item using Maximum Fisher Information."""
        topic_counts = topic_counts or {}
        candidates = [
            item for item in item_bank
            if item.question_id not in answered_ids
            and abs(theta - item.b) <= self.zpd_range
        ]

        # Content balance: skip topics already over-represented
        if topic_counts:
            balanced = []
            for item in candidates:
                tags = item.topic_tags or []
                if all(topic_counts.get(t, 0) < self.max_per_topic for t in tags):
                    balanced.append(item)
            if balanced:
                candidates = balanced

        if not candidates:
            return None

        best_item = max(
            candidates,
            key=lambda item: self.irt.fisher_information(theta, item.a, item.b),
        )
        return best_item
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/adaptive/cat.py
git commit -m "feat(adaptive): add CAT selector with Maximum Fisher Information"
```

---

### Task 14: Adaptive Agent — `adaptive/agent.py`

**Files:**
- Create: `master/agents/src/adaptive/agent.py`

- [ ] **Step 1: Write implementation**

```python
# master/agents/src/adaptive/agent.py
from __future__ import annotations

import logging
from typing import Any

from ..base_agent import BaseAgent
from ..common.llm_client import LLMClient
from ..common.message import ErrorType
from .bkt import BKTModel, BKTParams
from .irt import IRTModel

logger = logging.getLogger(__name__)


class AdaptiveAgent(BaseAgent):
    """Maintains student ability model and recommends learning paths."""

    def __init__(self, llm_client: LLMClient):
        super().__init__(name="adaptive", llm_client=llm_client)
        self.bkt = BKTModel()
        self.irt = IRTModel()

    @property
    def system_prompt(self) -> str:
        return (
            "You are the Adaptive Agent of MASTER. You maintain a model of each "
            "student's knowledge mastery using BKT and IRT. You analyze evaluation "
            "results, update mastery scores, and recommend topics to study next."
        )

    @property
    def description(self) -> str:
        return "Tracks student mastery via BKT/IRT and generates personalized learning paths."

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "update_profile")

        if action == "update_profile":
            return await self._update_profile(payload)
        elif action == "select_exam":
            return await self._select_exam(payload)
        elif action == "get_profile":
            return await self._get_profile(payload)
        elif action == "get_mistake_history":
            return await self._get_mistake_history(payload)
        else:
            return {"error": f"Unknown action: {action}"}

    async def _update_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Process evaluation results and update mastery scores."""
        context = payload.get("context", {})
        verifier_result = context.get("verifier", {})
        evaluation = verifier_result.get("evaluation", {})

        per_question = evaluation.get("per_question", [])
        mastery_updates: dict[str, float] = {}

        for q_eval in per_question:
            is_correct = q_eval.get("is_correct", False)
            error_analysis = q_eval.get("error_analysis")

            kc = None
            if error_analysis:
                kc = error_analysis.get("knowledge_component")
            if not kc:
                continue

            current_pl = mastery_updates.get(kc, 0.1)
            params = BKTParams(p_l0=current_pl)
            new_pl = self.bkt.update(params, correct=is_correct)
            mastery_updates[kc] = new_pl

        weaknesses = [kc for kc, pl in mastery_updates.items() if pl < 0.5]
        strengths = [kc for kc, pl in mastery_updates.items() if pl >= 0.8]

        return {
            "mastery_updates": mastery_updates,
            "weaknesses": weaknesses,
            "strengths": strengths,
            "evaluation": evaluation,
        }

    async def _select_exam(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Select an appropriate exam based on student profile.
        In MVP, returns a placeholder — real implementation needs DB access.
        """
        request_data = payload.get("request", {})
        student_id = request_data.get("student_id")
        metadata = request_data.get("metadata", {})

        return {
            "action": "select_exam",
            "student_id": student_id,
            "message": "Exam selection based on student profile",
            "filters": {
                "subject": metadata.get("subject", "math"),
                "exam_type": metadata.get("exam_type", "THPTQG"),
            },
        }

    async def _get_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_data = payload.get("request", {})
        return {
            "student_id": request_data.get("student_id"),
            "message": "Profile retrieval needs DB integration",
        }

    async def _get_mistake_history(self, payload: dict[str, Any]) -> dict[str, Any]:
        request_data = payload.get("request", {})
        return {
            "student_id": request_data.get("student_id"),
            "message": "Mistake history retrieval needs DB integration",
        }
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/adaptive/agent.py
git commit -m "feat(adaptive): add AdaptiveAgent with BKT/IRT mastery tracking"
```

---

### Task 15: Wire Manager + Adaptive into server.py

**Files:**
- Modify: `master/agents/src/server.py`

- [ ] **Step 1: Update server.py to use ManagerAgent**

Update the dispatch endpoint to use the ManagerAgent with the Adaptive agent registered:

```python
# In server.py, after building LLM clients, add:
from .manager.agent import ManagerAgent
from .adaptive.agent import AdaptiveAgent

adaptive_agent = AdaptiveAgent(llm_client=manager_llm)
manager_agent = ManagerAgent(llm_client=manager_llm, agent_registry={"adaptive": adaptive_agent})

# Update dispatch endpoint to use manager_agent:
@app.post("/api/agents/dispatch", response_model=TaskResponse)
async def dispatch(request: TaskRequest):
    logger.info("Dispatch: student=%s intent=%s", request.student_id, request.intent)
    try:
        result = await manager_agent.run(request.model_dump())
        if isinstance(result, dict) and "task_id" in result:
            return TaskResponse(**result)
        return TaskResponse(
            status="success",
            intent=request.intent,
            result=result,
            agent_trail=result.get("agent_trail", ["manager"]),
        )
    except Exception as e:
        logger.error("Dispatch failed: %s", e, exc_info=True)
        return TaskResponse(
            status="error",
            intent=request.intent,
            error_message=str(e),
        )
```

- [ ] **Step 2: Commit**

```bash
git add master/agents/src/server.py
git commit -m "feat(agents): wire ManagerAgent + AdaptiveAgent into FastAPI server"
```

---

## Summary — What Khang Delivers

| Day | Deliverable | Unblocks |
|-----|-------------|----------|
| 1 | `requirements.txt`, `common/__init__.py` | — |
| 1 | `common/config.py` with vLLM + Gemini config | Phúc |
| 1 | `common/message.py` with all Pydantic schemas | Phúc, Nguyên Huy |
| 2 | `common/llm_client.py` with dual-backend | Phúc |
| 2 | `common/tools.py`, `base_agent.py` | Phúc |
| 2 | `server.py` skeleton with /health and /dispatch | Nguyên Huy can test integration |
| 3 | `manager/intent.py` + `manager/planner.py` | — |
| 3 | `manager/agent.py` | — |
| 4 | `adaptive/bkt.py` + `adaptive/irt.py` | — |
| 4 | `adaptive/cat.py` + `adaptive/agent.py` | — |
| 5 | Wire all agents in `server.py` | Full pipeline testing |
