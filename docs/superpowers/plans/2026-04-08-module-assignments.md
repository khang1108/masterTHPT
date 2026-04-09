# MASTER — Phân công theo Module

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Giao việc cụ thể cho 4 thành viên, mỗi người 1 module độc lập, code xong ghép lại chạy được.

**Architecture:** 4 module độc lập giao tiếp HTTP/JSON. Module A (agent common) là nền tảng — Module B (parser/teacher/verifier) dùng. Module C (backend/frontend) gọi Module A+B qua HTTP. Module D (data) nạp dữ liệu vào DB, các module khác đọc.

**Tech Stack:** Python 3.11+, FastAPI, MongoDB, Mongoose, NestJS, Next.js 14, PaddleOCR, vLLM/Gemini, Docker

---

## Cách đọc tài liệu này

- Mỗi **Module** là 1 phần độc lập, giao cho 1 người.
- Mỗi người **chỉ cần đọc Module của mình** + phần **Module SHARED** (mục 0).
- Các module giao tiếp qua **interface cố định** (JSON schema) — đã thống nhất trong `COORDINATION.md`.
- Thứ tự thực hiện trong mỗi module: **từ trên xuống dưới** — task trước là dependency của task sau.

---

## Module SHARED — Mọi người đều phải biết

### Cấu trúc folder cuối cùng

```
master/
├── agents/                   ← MODULE A + B (Khang + Phúc)
│   ├── src/
│   │   ├── common/           ← MODULE A: Khang viết, Phúc dùng
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── llm_client.py
│   │   │   ├── message.py
│   │   │   └── tool.py
│   │   ├── baseagent.py      ← MODULE A: Khang viết, Phúc kế thừa
│   │   ├── manager/          ← MODULE A: Khang
│   │   ├── adaptive/         ← MODULE A: Khang
│   │   ├── parser/           ← MODULE B: Phúc
│   │   ├── teacher/          ← MODULE B: Phúc
│   │   ├── verifier/         ← MODULE B: Phúc
│   │   └── server.py         ← MODULE A: Khang (entry point)
│   ├── tests/
│   └── requirements.txt
│
├── apps/
│   ├── api/                  ← MODULE C: Nguyên Huy (NestJS)
│   ├── web/                  ← MODULE C: Nguyên Huy (Next.js)
│   └── grading-engine/       ← MODULE B: Phúc (Python/FastAPI)
│
└── data/                     ← MODULE D: Nhật Huy
    ├── scrapers/
    ├── knowledge_graph/
    └── exam_bank/
```

### 3 JSON schema cố định — KHÔNG AI được tự ý thay đổi

Xem chi tiết tại `COORDINATION.md` mục 3.1, 3.2, 3.3. Tóm tắt:

1. **TaskRequest/TaskResponse** — NestJS gửi → Agent Service nhận → trả về
2. **Exam JSON** — Parser trả ra → Teacher nhận vào → DB lưu → Frontend render
3. **Evaluation JSON** — Teacher trả ra → Verifier kiểm tra → DB lưu → Frontend render

### Thứ tự dependency giữa các module

```
Ngày 1 ─── Khang: common/ + baseagent.py ──┐
           Phúc: preprocessing.py (no dep)  │
           Nguyên Huy: init NestJS + DB     │  (song song)
           Nhật Huy: DB schema + KG JSON    │
                                            │
Ngày 2 ─── Khang push common/ ─────────────┤
           Phúc: pull common/, bắt đầu      │
           parser agent.py, ocr.py          │
                                            │
Ngày 3+ ── Tất cả chạy song song ──────────┘
```

**Nút thắt duy nhất:** Phúc chờ Khang viết xong `common/` (ngày 2). Phúc dùng ngày 1 viết `preprocessing.py` (không cần `common/`).

---

## Module A — Khang (AI Core 1, Leader)

**Phụ trách:** `agents/src/common/`, `agents/src/baseagent.py`, `agents/src/manager/`, `agents/src/adaptive/`, `agents/src/server.py`

**Mục tiêu:** Xây nền tảng cho mọi agent, viết Manager điều phối, viết Adaptive đánh giá năng lực.

### Task A1: `common/config.py` — Model routing config

**Files:**
- Create: `master/agents/src/common/__init__.py`
- Create: `master/agents/src/common/config.py`

- [ ] **Step 1: Tạo `__init__.py` rỗng**

- [ ] **Step 2: Viết `config.py`**

```python
# agents/src/common/config.py
from dataclasses import dataclass
import os

@dataclass
class ModelConfig:
    name: str
    base_url: str
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.3

def _get_model(name: str, env_url: str, default_url: str, model_id: str) -> ModelConfig:
    return ModelConfig(
        name=name,
        base_url=os.getenv(env_url, default_url),
        model_id=model_id,
    )

MANAGER_MODEL = _get_model("manager", "VLLM_MANAGER_URL", "http://localhost:8080/v1", "Qwen/Qwen3-8B")
TEACHER_MODEL = _get_model("teacher", "VLLM_TEACHER_URL", "http://localhost:8081/v1", "google/gemma-3-4b-it")
VERIFIER_MODEL = _get_model("verifier", "VLLM_VERIFIER_URL", "http://localhost:8082/v1", "Qwen/Qwen3-14B-AWQ")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_GEMINI = os.getenv("USE_GEMINI_FALLBACK", "false").lower() == "true"
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/master_db")
```

- [ ] **Step 3: Test thử import**

Run: `cd master/agents && python -c "from src.common.config import MANAGER_MODEL; print(MANAGER_MODEL.name)"`
Expected: `manager`

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(common): add model routing config"
```

---

### Task A2: `common/tool.py` — Tool definition

**Files:**
- Create: `master/agents/src/common/tool.py`

- [ ] **Step 1: Viết Tool dataclass**

```python
# agents/src/common/tool.py
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Tool:
    name: str
    description: str
    function: Callable[..., Any]

    def to_prompt_description(self) -> str:
        return f"- {self.name}: {self.description}"

    async def execute(self, **kwargs) -> Any:
        import asyncio
        if asyncio.iscoroutinefunction(self.function):
            return await self.function(**kwargs)
        return self.function(**kwargs)
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat(common): add Tool dataclass"
```

---

### Task A3: `common/message.py` — Giao thức giao tiếp

**Files:**
- Create: `master/agents/src/common/message.py`

Đây là file **quan trọng nhất** — định nghĩa format mà NestJS gửi vào và Agent Service trả ra. Phải khớp 100% với COORDINATION.md mục 3.1.

- [ ] **Step 1: Viết message models**

```python
# agents/src/common/message.py
from pydantic import BaseModel
from typing import Any
from enum import Enum

class Intent(str, Enum):
    EXAM_PRACTICE = "EXAM_PRACTICE"
    GRADE_SUBMISSION = "GRADE_SUBMISSION"
    VIEW_ANALYSIS = "VIEW_ANALYSIS"
    ASK_HINT = "ASK_HINT"
    REVIEW_MISTAKE = "REVIEW_MISTAKE"
    UNKNOWN = "UNKNOWN"

class TaskRequest(BaseModel):
    student_id: str
    intent: Intent
    user_message: str
    session_id: str | None = None
    file_urls: list[str] = []
    metadata: dict[str, Any] = {}

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any]
    agent_trail: list[str] = []

class AgentMessage(BaseModel):
    from_agent: str
    to_agent: str
    task_id: str
    action: str
    payload: dict[str, Any]
```

- [ ] **Step 2: Test import**

Run: `python -c "from src.common.message import TaskRequest, Intent; print(Intent.GRADE_SUBMISSION.value)"`
Expected: `GRADE_SUBMISSION`

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(common): add TaskRequest/TaskResponse/Intent message protocol"
```

---

### Task A4: `common/llm_client.py` — Wrapper gọi LLM

**Files:**
- Create: `master/agents/src/common/llm_client.py`

LLM client phải hỗ trợ 2 backend: **vLLM** (OpenAI-compatible) và **Gemini** (fallback). Phúc sẽ dùng file này để gọi LLM trong Teacher/Verifier.

- [ ] **Step 1: Viết LLM client**

```python
# agents/src/common/llm_client.py
import json
from typing import Any
from .config import ModelConfig, USE_GEMINI, GEMINI_API_KEY

class LLMClient:
    def __init__(self, config: ModelConfig):
        self.config = config
        self._vllm_client = None
        self._gemini_model = None

    def _get_vllm(self):
        if not self._vllm_client:
            from openai import AsyncOpenAI
            self._vllm_client = AsyncOpenAI(
                base_url=self.config.base_url,
                api_key="not-needed",
            )
        return self._vllm_client

    def _get_gemini(self):
        if not self._gemini_model:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self._gemini_model = genai.GenerativeModel("gemini-2.5-flash")
        return self._gemini_model

    async def chat(self, messages: list[dict], **kwargs) -> str:
        if USE_GEMINI:
            return await self._chat_gemini(messages, **kwargs)
        return await self._chat_vllm(messages, **kwargs)

    async def chat_json(self, messages: list[dict], **kwargs) -> dict[str, Any]:
        raw = await self.chat(messages, **kwargs)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw)

    async def _chat_vllm(self, messages: list[dict], **kwargs) -> str:
        client = self._get_vllm()
        response = await client.chat.completions.create(
            model=self.config.model_id,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        return response.choices[0].message.content

    async def _chat_gemini(self, messages: list[dict], **kwargs) -> str:
        model = self._get_gemini()
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"[System] {content}")
            elif role == "user":
                prompt_parts.append(f"[User] {content}")
            else:
                prompt_parts.append(f"[Assistant] {content}")
        response = await model.generate_content_async("\n\n".join(prompt_parts))
        return response.text
```

- [ ] **Step 2: Test (cần Gemini API key trong .env)**

Run: `python -c "import asyncio; from src.common.llm_client import LLMClient; from src.common.config import MANAGER_MODEL; print('OK')"`
Expected: `OK` (chỉ test import, chưa gọi thật)

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(common): add LLM client with vLLM + Gemini fallback"
```

---

### Task A5: `baseagent.py` — Thiết kế lại Base Agent

**Files:**
- Modify: `master/agents/src/baseagent.py`

- [ ] **Step 1: Viết lại BaseAgent hoàn chỉnh**

```python
# agents/src/baseagent.py
from abc import ABC, abstractmethod
from typing import Any
import time
import uuid
import logging

from src.common.llm_client import LLMClient
from src.common.tool import Tool
from src.common.config import ModelConfig

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, name: str, llm_client: LLMClient, tools: list[Tool] | None = None):
        self.name = name
        self._llm = llm_client
        self._tools: dict[str, Tool] = {}
        self._history: list[dict] = []

        if tools:
            for tool in tools:
                self.register_tool(tool)

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Mỗi agent subclass bắt buộc định nghĩa system prompt riêng."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Mô tả ngắn agent này làm gì — Manager dùng để quyết định giao việc."""
        ...

    @abstractmethod
    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Logic nghiệp vụ chính. Mỗi agent override method này."""
        ...

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Entry point — wrap handle() với logging + error handling + timing.
        KHÔNG override method này. Override handle() thay vì run().
        """
        run_id = str(uuid.uuid4())[:8]
        start = time.time()
        logger.info(f"[{self.name}:{run_id}] START payload_keys={list(payload.keys())}")

        try:
            result = await self.handle(payload)
            elapsed = round(time.time() - start, 2)
            logger.info(f"[{self.name}:{run_id}] DONE in {elapsed}s")
            self._history.append({"run_id": run_id, "elapsed": elapsed, "status": "success"})
            return result
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            logger.error(f"[{self.name}:{run_id}] ERROR after {elapsed}s: {e}")
            self._history.append({"run_id": run_id, "elapsed": elapsed, "status": "error", "error": str(e)})
            return {"error": str(e), "agent": self.name}

    # --- LLM shortcuts ---

    async def think(self, messages: list[dict], **kwargs) -> str:
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages
        return await self._llm.chat(full_messages, **kwargs)

    async def think_json(self, messages: list[dict], **kwargs) -> dict:
        full_messages = [{"role": "system", "content": self.system_prompt}] + messages
        return await self._llm.chat_json(full_messages, **kwargs)

    # --- Tool management ---

    def register_tool(self, tool: Tool):
        self._tools[tool.name] = tool

    async def execute_tool(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not registered in agent '{self.name}'")
        return await self._tools[name].execute(**kwargs)

    def get_tool_descriptions(self) -> str:
        if not self._tools:
            return "No tools available."
        return "\n".join(t.to_prompt_description() for t in self._tools.values())
```

- [ ] **Step 2: Test baseagent**

```python
# agents/tests/test_baseagent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.baseagent import BaseAgent
from src.common.tool import Tool

class DummyAgent(BaseAgent):
    @property
    def system_prompt(self) -> str:
        return "You are a test agent."

    @property
    def description(self) -> str:
        return "Test agent for unit testing"

    async def handle(self, payload):
        return {"echo": payload.get("input", "")}

@pytest.fixture
def dummy_agent():
    mock_llm = MagicMock()
    return DummyAgent(name="dummy", llm_client=mock_llm)

@pytest.mark.asyncio
async def test_run_returns_handle_result(dummy_agent):
    result = await dummy_agent.run({"input": "hello"})
    assert result == {"echo": "hello"}

@pytest.mark.asyncio
async def test_run_catches_error():
    mock_llm = MagicMock()
    class FailAgent(BaseAgent):
        system_prompt = "fail"
        description = "fail"
        async def handle(self, payload):
            raise ValueError("boom")
    agent = FailAgent(name="fail", llm_client=mock_llm)
    result = await agent.run({})
    assert "error" in result

def test_register_and_list_tools(dummy_agent):
    dummy_agent.register_tool(Tool("greet", "Says hello", lambda: "hi"))
    assert "greet" in dummy_agent.get_tool_descriptions()
```

Run: `cd master/agents && python -m pytest tests/test_baseagent.py -v`
Expected: PASS (3 tests)

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: redesign BaseAgent with handle/run split, tool registry, LLM shortcuts"
```

---

### Task A6: `manager/` — Intent detection + orchestration

**Files:**
- Create: `master/agents/src/manager/__init__.py`
- Create: `master/agents/src/manager/intent.py`
- Create: `master/agents/src/manager/planner.py`
- Create: `master/agents/src/manager/agent.py`

- [ ] **Step 1: `intent.py` — keyword-based, LLM-enhanced**

```python
# agents/src/manager/intent.py
import re
from src.common.message import Intent

PATTERNS = {
    Intent.EXAM_PRACTICE: [r"(làm|thi|luyện).*(đề|exam|test)", r"ôn (luyện|thi)"],
    Intent.GRADE_SUBMISSION: [r"(chấm|grade|nộp)", r"chấm (bài|điểm)"],
    Intent.VIEW_ANALYSIS: [r"(phân tích|analysis|năng lực|thống kê)"],
    Intent.ASK_HINT: [r"(gợi ý|hint|giúp|hướng dẫn)"],
    Intent.REVIEW_MISTAKE: [r"(xem lại|review).*(lỗi|sai)"],
}

def classify_intent(message: str, has_file: bool = False) -> Intent:
    if has_file:
        return Intent.GRADE_SUBMISSION
    for intent, patterns in PATTERNS.items():
        for p in patterns:
            if re.search(p, message, re.IGNORECASE):
                return intent
    return Intent.UNKNOWN
```

- [ ] **Step 2: `planner.py` — DAG cứng theo intent**

```python
# agents/src/manager/planner.py
from src.common.message import Intent

FLOWS: dict[Intent, list[str]] = {
    Intent.GRADE_SUBMISSION: ["parser", "teacher", "verifier", "adaptive"],
    Intent.EXAM_PRACTICE: ["adaptive", "teacher"],
    Intent.VIEW_ANALYSIS: ["adaptive"],
    Intent.ASK_HINT: ["teacher"],
    Intent.REVIEW_MISTAKE: ["adaptive"],
}

def get_agent_flow(intent: Intent) -> list[str]:
    return FLOWS.get(intent, [])
```

- [ ] **Step 3: `agent.py` — Manager orchestration**

Manager không xử lý nghiệp vụ — nó chỉ **phân loại intent** và **gọi agent con theo thứ tự**.

```python
# agents/src/manager/agent.py
from typing import Any
import uuid
from src.baseagent import BaseAgent
from src.common.llm_client import LLMClient
from src.common.config import MANAGER_MODEL
from src.common.message import TaskRequest, TaskResponse
from .intent import classify_intent
from .planner import get_agent_flow

class ManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="manager", llm_client=LLMClient(MANAGER_MODEL))
        self._agents: dict[str, BaseAgent] = {}

    @property
    def system_prompt(self):
        return "You are the Manager Agent. You classify user intent and route to sub-agents."

    @property
    def description(self):
        return "Điều phối trung tâm: phân loại intent, gọi agent con theo DAG"

    def register_sub_agent(self, agent: BaseAgent):
        self._agents[agent.name] = agent

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = TaskRequest(**payload)
        task_id = str(uuid.uuid4())
        trail = ["manager"]

        intent = classify_intent(request.user_message, has_file=bool(request.file_urls))
        flow = get_agent_flow(intent)

        context = {
            "student_id": request.student_id,
            "intent": intent.value,
            "session_id": request.session_id,
            "file_urls": request.file_urls,
            "metadata": request.metadata,
        }

        result = context
        for agent_name in flow:
            agent = self._agents.get(agent_name)
            if not agent:
                continue
            result = await agent.run({**result, "previous_result": result})
            trail.append(agent_name)

        return TaskResponse(
            task_id=task_id,
            status="success",
            result=result,
            agent_trail=trail,
        ).model_dump()

    async def dispatch(self, request: TaskRequest) -> TaskResponse:
        raw = await self.run(request.model_dump())
        return TaskResponse(**raw)
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(manager): add intent detection, DAG planner, orchestration"
```

---

### Task A7: `adaptive/` — BKT + IRT + student profile

**Files:**
- Create: `master/agents/src/adaptive/__init__.py`
- Create: `master/agents/src/adaptive/bkt.py`
- Create: `master/agents/src/adaptive/irt.py`
- Create: `master/agents/src/adaptive/agent.py`

- [ ] **Step 1: `bkt.py`**

```python
# agents/src/adaptive/bkt.py
class BKTModel:
    def __init__(self, p_l=0.1, p_t=0.1, p_s=0.05, p_g=0.25):
        self.p_l = p_l
        self.p_t = p_t
        self.p_s = p_s
        self.p_g = p_g

    def update(self, correct: bool) -> float:
        if correct:
            num = self.p_l * (1 - self.p_s)
            den = num + (1 - self.p_l) * self.p_g
        else:
            num = self.p_l * self.p_s
            den = num + (1 - self.p_l) * (1 - self.p_g)
        p_l_obs = num / den if den else self.p_l
        self.p_l = p_l_obs + (1 - p_l_obs) * self.p_t
        return self.p_l

    @property
    def mastery(self) -> float:
        return self.p_l
```

- [ ] **Step 2: `irt.py`**

```python
# agents/src/adaptive/irt.py
import math

def irt_prob(theta: float, a: float = 1.0, b: float = 0.0) -> float:
    exp = max(min(-a * (theta - b), 500), -500)
    return 1.0 / (1.0 + math.exp(exp))

def fisher_info(theta: float, a: float, b: float) -> float:
    p = irt_prob(theta, a, b)
    return a * a * p * (1 - p)

def estimate_theta(responses: list[tuple[bool, float, float]], initial=0.0) -> float:
    theta = initial
    for _ in range(20):
        grad = sum(a * ((1.0 if c else 0.0) - irt_prob(theta, a, b)) for c, a, b in responses)
        theta = max(min(theta + 0.3 * grad, 4.0), -4.0)
    return theta
```

- [ ] **Step 3: `agent.py`**

```python
# agents/src/adaptive/agent.py
from typing import Any
from src.baseagent import BaseAgent
from src.common.llm_client import LLMClient
from src.common.config import MANAGER_MODEL
from .bkt import BKTModel
from .irt import estimate_theta

class AdaptiveAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="adaptive", llm_client=LLMClient(MANAGER_MODEL))
        self._bkt_cache: dict[str, dict[str, BKTModel]] = {}

    @property
    def system_prompt(self):
        return "You maintain student ability profiles using BKT and IRT."

    @property
    def description(self):
        return "Cập nhật năng lực học sinh, chọn câu hỏi tiếp theo"

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "update_profile")
        student_id = payload.get("student_id", "")

        if action == "update_profile":
            return self._update_profile(student_id, payload.get("previous_result", {}))
        return {"agent": "adaptive", "status": "no_action"}

    def _update_profile(self, student_id: str, evaluation: dict) -> dict:
        if student_id not in self._bkt_cache:
            self._bkt_cache[student_id] = {}

        topic_updates = {}
        responses = []

        for q in evaluation.get("per_question", []):
            is_correct = q.get("is_correct", False)
            a = q.get("difficulty_a", 1.0)
            b = q.get("difficulty_b", 0.0)
            responses.append((is_correct, a, b))

            for tag in q.get("topic_tags", []):
                if tag not in self._bkt_cache[student_id]:
                    self._bkt_cache[student_id][tag] = BKTModel()
                m = self._bkt_cache[student_id][tag].update(is_correct)
                topic_updates[tag] = round(m, 4)

        theta = round(estimate_theta(responses), 4) if responses else 0.0
        return {"student_id": student_id, "theta": theta, "mastery": topic_updates}
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(adaptive): add BKT, IRT, AdaptiveAgent with profile tracking"
```

---

### Task A8: `server.py` — FastAPI entry point

**Files:**
- Create: `master/agents/src/server.py`

Server.py là nơi **tất cả agent được wire lại**. Đây là file cuối cùng Khang viết, sau khi Phúc đã viết xong Parser/Teacher/Verifier.

- [ ] **Step 1: Viết server skeleton (đầu tiên chỉ có Manager + Adaptive)**

```python
# agents/src/server.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from src.common.message import TaskRequest, TaskResponse
from src.manager.agent import ManagerAgent
from src.adaptive.agent import AdaptiveAgent
import uuid, shutil, os

app = FastAPI(title="MASTER Agent Service", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = "/tmp/master_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

manager = ManagerAgent()
manager.register_sub_agent(AdaptiveAgent())

# Khi Phúc viết xong, thêm vào đây:
# from src.parser.agent import ParserAgent
# from src.teacher.agent import TeacherAgent
# from src.verifier.agent import VerifierAgent
# manager.register_sub_agent(ParserAgent())
# manager.register_sub_agent(TeacherAgent())
# manager.register_sub_agent(VerifierAgent())

@app.post("/api/agents/dispatch", response_model=TaskResponse)
async def dispatch(request: TaskRequest):
    return await manager.dispatch(request)

@app.post("/api/agents/parse-and-grade")
async def parse_and_grade(file: UploadFile = File(...), student_id: str = Form("anon")):
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    req = TaskRequest(student_id=student_id, intent="GRADE_SUBMISSION",
                      user_message="Grade uploaded file", file_urls=[path])
    return await manager.dispatch(req)

@app.get("/health")
async def health():
    agents = ["manager", "adaptive"] + [a for a in manager._agents]
    return {"status": "ok", "agents": agents}
```

- [ ] **Step 2: Test run**

Run: `cd master/agents && uvicorn src.server:app --port 8000 --reload`
Sau đó mở browser: `http://localhost:8000/health`
Expected: `{"status": "ok", "agents": [...]}`

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add FastAPI server with Manager + Adaptive wired"
```

---

## Module B — Phúc (AI Core 2)

**Phụ trách:** `agents/src/parser/`, `agents/src/teacher/`, `agents/src/verifier/`, `apps/grading-engine/`

**Mục tiêu:** Xây 3 agent xử lý nghiệp vụ chính: OCR, chấm bài, kiểm tra chéo.

**Dependency:** Chờ Khang push `common/` và `baseagent.py` (ngày 2). Ngày 1 viết `preprocessing.py` trước (không cần import common).

### Task B1: `parser/preprocessing.py` — Xử lý ảnh (bắt đầu ngày 1)

**Files:**
- Create: `master/agents/src/parser/__init__.py`
- Create: `master/agents/src/parser/preprocessing.py`
- Test: `master/agents/tests/test_preprocessing.py`

- [ ] **Step 1: Viết test**

```python
# agents/tests/test_preprocessing.py
import numpy as np
from src.parser.preprocessing import convert_to_gray, reduce_noise, preprocess_image

def test_convert_to_gray():
    color = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    gray = convert_to_gray(color)
    assert gray.shape == (100, 100)

def test_preprocess_returns_2d():
    img = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
    result = preprocess_image(img)
    assert len(result.shape) == 2
```

- [ ] **Step 2: Implement**

```python
# agents/src/parser/preprocessing.py
import cv2
import numpy as np

def convert_to_gray(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def reduce_noise(image: np.ndarray, h: int = 10) -> np.ndarray:
    return cv2.fastNlMeansDenoising(image, h=h)

def enhance_contrast(image: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)

def preprocess_image(image: np.ndarray) -> np.ndarray:
    gray = convert_to_gray(image)
    denoised = reduce_noise(gray)
    enhanced = enhance_contrast(denoised)
    return cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
```

- [ ] **Step 3: Test**

Run: `cd master/agents && python -m pytest tests/test_preprocessing.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(parser): add image preprocessing with OpenCV"
```

---

### Task B2: `parser/ocr.py` — PaddleOCR wrapper

**Files:**
- Create: `master/agents/src/parser/ocr.py`

- [ ] **Step 1: Implement OCR engine**

```python
# agents/src/parser/ocr.py
from paddleocr import PaddleOCR
import numpy as np
from dataclasses import dataclass

@dataclass
class TextBlock:
    text: str
    confidence: float
    bbox: list
    line_index: int = 0

class OCREngine:
    def __init__(self, lang="vi"):
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=False, show_log=False)

    def detect(self, image: np.ndarray) -> list[TextBlock]:
        results = self.ocr.ocr(image, cls=True)
        if not results or not results[0]:
            return []
        blocks = []
        for i, line in enumerate(results[0]):
            bbox, (text, conf) = line[0], line[1]
            blocks.append(TextBlock(text=text, confidence=conf, bbox=bbox, line_index=i))
        blocks.sort(key=lambda b: (b.bbox[0][1], b.bbox[0][0]))
        return blocks

    def full_text(self, image: np.ndarray) -> str:
        return "\n".join(b.text for b in self.detect(image))
```

- [ ] **Step 2: Test thủ công với 1 ảnh đề thi**

Run: `python -c "from src.parser.ocr import OCREngine; e=OCREngine(); print('OCR ready')"`
Expected: `OCR ready` (PaddleOCR downloads model on first run)

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(parser): add PaddleOCR wrapper for Vietnamese text detection"
```

---

### Task B3: `parser/extractor.py` + `parser/agent.py`

**Files:**
- Create: `master/agents/src/parser/extractor.py`
- Create: `master/agents/src/parser/agent.py`

- [ ] **Step 1: `extractor.py` — tách câu hỏi từ text**

```python
# agents/src/parser/extractor.py
import re, uuid
from typing import Any

class QuestionExtractor:
    Q_PAT = re.compile(r"(?:Câu|câu)\s*(\d+)\s*[:.]\s*(.*?)(?=(?:Câu|câu)\s*\d+|$)", re.DOTALL)
    OPT_PAT = re.compile(r"([A-D])\s*[.\)]\s*(.*?)(?=[A-D]\s*[.\)]|$)", re.DOTALL)

    def extract(self, text: str) -> list[dict[str, Any]]:
        questions = []
        for m in self.Q_PAT.finditer(text):
            num, body = int(m.group(1)), m.group(2).strip()
            opts = self.OPT_PAT.findall(body)
            content = body[:body.find(opts[0][0])] if opts else body
            q_type = "multiple_choice" if len(opts) == 4 else "essay"
            questions.append({
                "id": f"q{num}", "question_index": num, "type": q_type,
                "content": content.strip(),
                "options": [f"{l}. {t.strip()}" for l, t in opts] if opts else None,
                "has_image": False, "topic_tags": [], "max_score": 0.2 if q_type == "multiple_choice" else 1.0,
            })
        return questions

    def build_exam(self, questions: list[dict], subject="math", exam_type="THPTQG") -> dict:
        mc = [q for q in questions if q["type"] == "multiple_choice"]
        essay = [q for q in questions if q["type"] == "essay"]
        sections = []
        if mc: sections.append({"type": "multiple_choice", "questions": mc})
        if essay: sections.append({"type": "essay", "questions": essay})
        return {"exam_id": str(uuid.uuid4()), "source": "image", "subject": subject,
                "exam_type": exam_type, "total_questions": len(questions), "sections": sections}
```

- [ ] **Step 2: `agent.py` — Parser Agent kế thừa BaseAgent**

```python
# agents/src/parser/agent.py
import cv2
from typing import Any
from src.baseagent import BaseAgent
from src.common.llm_client import LLMClient
from src.common.config import MANAGER_MODEL
from .preprocessing import preprocess_image
from .ocr import OCREngine
from .extractor import QuestionExtractor

class ParserAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="parser", llm_client=LLMClient(MANAGER_MODEL))
        self._ocr = OCREngine()
        self._extractor = QuestionExtractor()

    @property
    def system_prompt(self):
        return "You extract questions from exam images using OCR."

    @property
    def description(self):
        return "OCR ảnh đề thi → JSON câu hỏi có cấu trúc"

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        file_urls = payload.get("file_urls", [])
        if not file_urls:
            return {"error": "No file provided"}

        image = cv2.imread(file_urls[0])
        if image is None:
            return {"error": f"Cannot read: {file_urls[0]}"}

        processed = preprocess_image(image)
        text = self._ocr.full_text(processed)
        questions = self._extractor.extract(text)
        subject = payload.get("metadata", {}).get("subject", "math")
        exam_type = payload.get("metadata", {}).get("exam_type", "THPTQG")
        exam = self._extractor.build_exam(questions, subject, exam_type)

        return {**payload, "exam_data": exam, "ocr_text": text}
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(parser): add QuestionExtractor and ParserAgent"
```

---

### Task B4: `teacher/` — Chấm bài

**Files:**
- Create: `master/agents/src/teacher/__init__.py`
- Create: `master/agents/src/teacher/grading.py`
- Create: `master/agents/src/teacher/agent.py`

- [ ] **Step 1: `grading.py` — logic chấm trắc nghiệm + LLM**

```python
# agents/src/teacher/grading.py
from typing import Any

ERROR_TYPES = ["CONCEPT_GAP", "CALCULATION_ERROR", "INCOMPLETE_REASONING", "MISINTERPRETATION", "PRESENTATION_FLAW"]

def grade_mc(student: str, correct: str, score_per_q: float = 0.2) -> dict[str, Any]:
    ok = student.strip().upper() == correct.strip().upper()
    return {"is_correct": ok, "score": score_per_q if ok else 0.0, "max_score": score_per_q,
            "student_answer": student, "correct_answer": correct,
            "reasoning": f"Đáp án đúng: {correct}" if ok else f"Sai. Đáp án đúng: {correct}"}

async def grade_essay(student_ans: str, question: str, rubric: dict, llm_client) -> dict:
    prompt = f"""Chấm bài tự luận.
Câu hỏi: {question}
Bài làm: {student_ans}
Rubric: {rubric}
Trả về JSON: {{"score": float, "max_score": float, "reasoning": str, "error_type": str, "root_cause": str}}"""
    return await llm_client.chat_json([{"role": "user", "content": prompt}])
```

- [ ] **Step 2: `agent.py`**

```python
# agents/src/teacher/agent.py
from typing import Any
from src.baseagent import BaseAgent
from src.common.llm_client import LLMClient
from src.common.config import TEACHER_MODEL
from .grading import grade_mc

class TeacherAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="teacher", llm_client=LLMClient(TEACHER_MODEL))

    @property
    def system_prompt(self):
        return "Bạn là giáo viên Toán THPT. Chấm bài nghiêm túc, phân tích lỗi chi tiết."

    @property
    def description(self):
        return "Chấm bài, phân tích lỗi tư duy, đưa ra feedback"

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        exam_data = payload.get("exam_data", {})
        answers = payload.get("metadata", {}).get("student_answers", {})
        per_question = []
        total = 0.0

        for section in exam_data.get("sections", []):
            for q in section.get("questions", []):
                ans = answers.get(q["id"])
                if not ans:
                    per_question.append({"question_id": q["id"], "score": 0.0, "max_score": q.get("max_score", 0.2),
                                         "reasoning": "Không trả lời"})
                    continue
                if q["type"] == "multiple_choice":
                    r = grade_mc(ans, q.get("correct_answer", ""), q.get("max_score", 0.2))
                    if not r["is_correct"]:
                        r["error_analysis"] = {"error_type": "CONCEPT_GAP",
                                               "knowledge_component": (q.get("topic_tags") or ["unknown"])[0],
                                               "remedial": f"Ôn lại: {', '.join(q.get('topic_tags', []))}"}
                else:
                    r = await self._grade_essay(ans, q)
                r["question_id"] = q["id"]
                r["topic_tags"] = q.get("topic_tags", [])
                r["difficulty_a"] = q.get("difficulty_a", 1.0)
                r["difficulty_b"] = q.get("difficulty_b", 0.0)
                per_question.append(r)
                total += r.get("score", 0)

        max_score = sum(q.get("max_score", 0.2) for q in per_question)
        strengths, weaknesses = self._analyze(per_question)

        return {**payload, "per_question": per_question, "total_score": round(total, 2),
                "max_score": round(max_score, 2), "confidence": 0.85,
                "overall_analysis": {"strengths": strengths, "weaknesses": weaknesses}}

    async def _grade_essay(self, ans: str, q: dict) -> dict:
        prompt = f"Chấm: Câu: {q['content']}\nBài làm: {ans}\nTrả JSON: {{\"score\": .., \"max_score\": .., \"reasoning\": .., \"is_correct\": ..}}"
        try:
            return await self.think_json([{"role": "user", "content": prompt}])
        except Exception:
            return {"score": 0.0, "max_score": q.get("max_score", 1.0), "reasoning": "Không thể chấm tự động", "is_correct": False}

    def _analyze(self, per_q: list[dict]) -> tuple[list, list]:
        topics: dict[str, dict] = {}
        for r in per_q:
            for t in r.get("topic_tags", []):
                if t not in topics: topics[t] = {"ok": 0, "total": 0}
                topics[t]["total"] += 1
                if r.get("is_correct"): topics[t]["ok"] += 1
        s = [t for t, v in topics.items() if v["total"] > 0 and v["ok"] / v["total"] >= 0.7]
        w = [t for t, v in topics.items() if v["total"] > 0 and v["ok"] / v["total"] < 0.5]
        return s, w
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(teacher): add TeacherAgent with MC grading and error analysis"
```

---

### Task B5: `verifier/` — Kiểm tra chéo

**Files:**
- Create: `master/agents/src/verifier/__init__.py`
- Create: `master/agents/src/verifier/agent.py`

- [ ] **Step 1: `agent.py` — Verifier kiểm tra độc lập + debate**

```python
# agents/src/verifier/agent.py
from typing import Any
from src.baseagent import BaseAgent
from src.common.llm_client import LLMClient
from src.common.config import VERIFIER_MODEL
from src.teacher.grading import grade_mc

MAX_ROUNDS = 3

class VerifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="verifier", llm_client=LLMClient(VERIFIER_MODEL))

    @property
    def system_prompt(self):
        return "Bạn là giám khảo phản biện. Kiểm tra lại kết quả chấm bài của Teacher."

    @property
    def description(self):
        return "Chấm độc lập, so sánh với Teacher, debate nếu bất đồng"

    async def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        teacher_pq = payload.get("per_question", [])
        exam_data = payload.get("exam_data", {})
        answers = payload.get("metadata", {}).get("student_answers", {})

        all_q = {}
        for sec in exam_data.get("sections", []):
            for q in sec.get("questions", []):
                all_q[q["id"]] = q

        discrepancies = []
        for tq in teacher_pq:
            qid = tq["question_id"]
            q = all_q.get(qid, {})
            if q.get("type") == "multiple_choice" and q.get("correct_answer"):
                v_result = grade_mc(answers.get(qid, ""), q["correct_answer"], q.get("max_score", 0.2))
                if abs(v_result["score"] - tq.get("score", 0)) > 0.01:
                    discrepancies.append({"question_id": qid, "teacher": tq["score"], "verifier": v_result["score"],
                                          "verifier_correct": v_result["is_correct"]})
                    tq["score"] = v_result["score"]
                    tq["is_correct"] = v_result["is_correct"]
                    tq["debate_resolution"] = "verifier_override"

        total = sum(q.get("score", 0) for q in teacher_pq)
        return {**payload, "per_question": teacher_pq, "total_score": round(total, 2),
                "verification": {"discrepancies": len(discrepancies), "details": discrepancies}}
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat(verifier): add VerifierAgent with independent grading and discrepancy check"
```

---

### Task B6: `grading-engine/` — SymPy microservice

**Files:**
- Create: `master/apps/grading-engine/src/__init__.py`
- Create: `master/apps/grading-engine/src/main.py`
- Create: `master/apps/grading-engine/src/sympy_grader.py`

- [ ] **Step 1: `sympy_grader.py`**

```python
# apps/grading-engine/src/sympy_grader.py
from sympy import sympify, simplify
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
T = standard_transformations + (implicit_multiplication_application,)

def verify_expression(student: str, reference: str) -> bool:
    try:
        s = sympify(student, transformations=T)
        r = sympify(reference, transformations=T)
        return simplify(s - r) == 0
    except Exception:
        return False

def verify_numeric(student: float, expected: float, tol: float = 0.01) -> bool:
    return abs(student - expected) <= tol
```

- [ ] **Step 2: `main.py`**

```python
# apps/grading-engine/src/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from .sympy_grader import verify_expression, verify_numeric

app = FastAPI(title="Grading Engine")

class MathReq(BaseModel):
    student: str
    reference: str

class NumReq(BaseModel):
    student: float
    expected: float
    tolerance: float = 0.01

@app.post("/verify/math")
async def math(r: MathReq):
    return {"is_correct": verify_expression(r.student, r.reference)}

@app.post("/verify/numeric")
async def numeric(r: NumReq):
    return {"is_correct": verify_numeric(r.student, r.expected, r.tolerance)}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(grading-engine): add SymPy math verification microservice"
```

---

## Module C — Nguyên Huy (Fullstack)

**Phụ trách:** `apps/api/` (NestJS), `apps/web/` (Next.js)

**Mục tiêu:** Backend API + Frontend UI. Không phụ thuộc vào agent service — dùng mock data để dev song song.

**DB:** MongoDB + Mongoose (thay cho PostgreSQL/Prisma).

### Task C1: Init NestJS + MongoDB

**Files:**
- Create: `master/apps/api/` (full NestJS project)

- [ ] **Step 1: Scaffold NestJS**

```bash
cd master/apps
npx @nestjs/cli new api --package-manager npm --skip-git
cd api
npm install @nestjs/mongoose mongoose @nestjs/jwt @nestjs/passport passport passport-jwt bcryptjs
npm install -D @types/bcryptjs @types/passport-jwt
npm install @nestjs/config class-validator class-transformer
```

- [ ] **Step 2: Tạo Mongoose schemas (thay cho Prisma)**

```typescript
// apps/api/src/schemas/student.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class Student extends Document {
  @Prop({ required: true, unique: true }) email: string;
  @Prop({ required: true }) name: string;
  @Prop({ required: true }) passwordHash: string;
  @Prop({ default: 12 }) grade: number;
  @Prop({ type: Object, default: { theta: 0, thetaSe: 1, totalItems: 0 } }) irtProfile: Record<string, number>;
  @Prop({ type: Object, default: {} }) mastery: Record<string, number>;
}
export const StudentSchema = SchemaFactory.createForClass(Student);
```

```typescript
// apps/api/src/schemas/exam.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MSchema } from 'mongoose';

@Schema({ timestamps: true })
export class Exam extends Document {
  @Prop({ required: true }) subject: string;
  @Prop({ required: true }) examType: string;
  @Prop() year: number;
  @Prop() source: string;
  @Prop({ required: true }) totalQuestions: number;
  @Prop({ default: 90 }) duration: number;
  @Prop({ type: [MSchema.Types.Mixed], default: [] }) questions: any[];
  @Prop({ type: MSchema.Types.Mixed }) metadata: any;
}
export const ExamSchema = SchemaFactory.createForClass(Exam);
```

```typescript
// apps/api/src/schemas/session.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Schema as MSchema } from 'mongoose';

@Schema({ timestamps: true })
export class ExamSession extends Document {
  @Prop({ required: true }) studentId: string;
  @Prop({ required: true }) examId: string;
  @Prop({ default: 'EXAM_PRACTICE' }) intent: string;
  @Prop({ default: 'IN_PROGRESS' }) status: string;
  @Prop() submittedAt: Date;
  @Prop() totalScore: number;
  @Prop() maxScore: number;
  @Prop() confidence: number;
  @Prop({ type: MSchema.Types.Mixed }) overallAnalysis: any;
  @Prop({ type: [MSchema.Types.Mixed], default: [] }) responses: any[];
  @Prop() uploadedFileUrl: string;
}
export const ExamSessionSchema = SchemaFactory.createForClass(ExamSession);
```

- [ ] **Step 3: Wire MongoDB trong app.module.ts**

```typescript
// apps/api/src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { MongooseModule } from '@nestjs/mongoose';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    MongooseModule.forRoot(process.env.MONGO_URI || 'mongodb://localhost:27017/master_db'),
    // AuthModule, ExamModule, ... sẽ thêm sau
  ],
})
export class AppModule {}
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(api): init NestJS with MongoDB/Mongoose schemas"
```

---

### Task C2: Auth module

**Files:**
- Create: `master/apps/api/src/modules/auth/` (module, service, controller, DTOs)

- [ ] **Step 1: Viết auth service + controller**

Service: `register()` hash password + tạo student + trả JWT. `login()` verify password + trả JWT.

Controller: `POST /auth/register`, `POST /auth/login`.

DTOs: `RegisterDto` (email, name, password, grade), `LoginDto` (email, password).

**Xem COORDINATION.md mục 3.5 cho endpoint spec.**

- [ ] **Step 2: Test bằng curl**

```bash
curl -X POST http://localhost:3001/auth/register -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","password":"123456","grade":12}'
```
Expected: `{"access_token": "...", "student_id": "..."}`

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(api): add auth module with register/login JWT"
```

---

### Task C3: Exam module + Agent dispatch

**Files:**
- Create: `master/apps/api/src/modules/exam/` (module, service, controller)
- Create: `master/apps/api/src/modules/agent/agent.service.ts`

- [ ] **Step 1: Agent dispatch service — 1 method gọi Agent Service**

```typescript
// apps/api/src/modules/agent/agent.service.ts
import { Injectable } from '@nestjs/common';

@Injectable()
export class AgentService {
  private baseUrl = process.env.AGENT_SERVICE_URL || 'http://localhost:8000';

  async dispatch(payload: {
    student_id: string; intent: string; user_message: string;
    session_id?: string; file_urls?: string[]; metadata?: any;
  }) {
    const res = await fetch(`${this.baseUrl}/api/agents/dispatch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  }
}
```

- [ ] **Step 2: Exam service — CRUD + submit + grade**

Endpoints (xem COORDINATION.md mục 3.5):
- `GET /exams` — list exams
- `GET /exams/:id` — exam + questions
- `POST /exams/sessions` — tạo session
- `POST /exams/sessions/:id/submit` — nộp + gọi agent dispatch + lưu kết quả
- `GET /exams/sessions/:id/results` — lấy kết quả

`submit` là endpoint quan trọng nhất: nhận `{responses, studentId}`, gọi `agentService.dispatch()`, lưu evaluation vào session document.

- [ ] **Step 3: Test submit mock (chưa cần Agent Service chạy)**

Nếu Agent Service chưa sẵn sàng, tạm trả mock evaluation.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat(api): add exam CRUD, session management, agent dispatch"
```

---

### Task C4-C8: Next.js Frontend

**Files:**
- Create: `master/apps/web/` (full Next.js project)

Thứ tự trang:

| Task | Trang | Mức khó | Ưu tiên |
|------|-------|---------|---------|
| C4 | Init Next.js + shadcn/ui + API client | Dễ | P0 |
| C5 | Login / Register | Dễ | P0 |
| C6 | Dashboard (danh sách đề, 3 action cards) | Trung bình | P0 |
| C7 | **Exam Room** (timer, câu hỏi, chọn đáp án, nộp) | **Khó nhất** | **P0** |
| C8 | Results page (điểm, từng câu, error analysis) | Trung bình | P0 |

**Exam Room (Task C7)** là trang khó nhất. Gồm:
- Header: tên đề, timer đếm ngược, nút nộp bài
- Sidebar trái: grid số câu (click để nhảy, đánh dấu đã làm bằng màu)
- Main: nội dung câu hỏi + 4 options click chọn
- Nút trước/sau
- Khi timer = 0 hoặc bấm nộp → confirm → gọi API submit → redirect trang results

**Mẹo:** Dùng `useState` lưu `answers: Record<string, string>`. Dark theme (bg-gray-900) cho cảm giác phòng thi.

Mỗi trang commit riêng:
```bash
git commit -m "feat(web): add login/register pages"
git commit -m "feat(web): add dashboard with exam list"
git commit -m "feat(web): add exam room with timer and question navigation"
git commit -m "feat(web): add results page with error analysis"
```

---

## Module D — Nhật Huy (Data Engineer)

**Phụ trách:** `master/data/`, MongoDB seed scripts, Knowledge Graph

**Mục tiêu:** Nạp dữ liệu vào MongoDB để team có data test. Cung cấp Knowledge Graph cho Adaptive Agent.

### Task D1: MongoDB schema review + docker-compose

**Files:**
- Create: `master/infra/docker-compose.yml`

- [ ] **Step 1: Docker compose với MongoDB**

```yaml
# infra/docker-compose.yml
version: "3.9"
services:
  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongodata:/data/db
    environment:
      MONGO_INITDB_DATABASE: master_db
volumes:
  mongodata:
```

- [ ] **Step 2: Chạy + verify**

```bash
cd infra && docker compose up -d
mongosh --eval "db.stats()"
```
Expected: kết nối thành công

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "infra: add docker-compose with MongoDB"
```

---

### Task D2: Knowledge Graph JSON

**Files:**
- Create: `master/data/knowledge_graph/math_kg.json`

- [ ] **Step 1: Viết KG Toán lớp 10-12**

Bao phủ tất cả chương chính. Mỗi node có `prerequisites`. Format:

```json
{
  "subject": "math",
  "nodes": [
    {"id": "math.10.ch1.sets", "grade": 10, "chapter": "Tập hợp", "topic": "Tập hợp và mệnh đề", "display_name": "Tập hợp", "prerequisites": []},
    {"id": "math.12.ch2.integrals", "grade": 12, "chapter": "Nguyên hàm - Tích phân", "topic": "Tích phân", "display_name": "Nguyên hàm và tích phân", "prerequisites": ["math.12.ch1.derivatives"]}
  ]
}
```

Tối thiểu **15-20 nodes** bao phủ các topic chính trong đề THPTQG.

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat(data): add Math knowledge graph with 20+ nodes"
```

---

### Task D3: Rubric templates + Sample exam

**Files:**
- Create: `master/data/exam_bank/rubrics/thptqg_math.json`
- Create: `master/data/exam_bank/sample_thptqg_2025.json`

- [ ] **Step 1: Viết rubric THPTQG Toán**

```json
{
  "exam_type": "THPTQG",
  "subject": "math",
  "grading_rules": {
    "multiple_choice": { "total": 50, "score_each": 0.2, "max_score": 10.0, "method": "exact_match" }
  },
  "time_limit_minutes": 90
}
```

- [ ] **Step 2: Viết 1 đề mẫu 10 câu (dùng cho toàn team test)**

File JSON theo đúng Exam JSON schema ở COORDINATION.md mục 3.2. Mỗi câu phải có `correct_answer`, `topic_tags`, `difficulty_b`.

**Đây là file quan trọng nhất** — cả Nguyên Huy (frontend), Khang (manager), Phúc (teacher) đều cần để test.

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(data): add THPTQG rubric and sample 10-question exam"
```

---

### Task D4: Seed script — Load vào MongoDB

**Files:**
- Create: `master/data/seed.py`

- [ ] **Step 1: Script insert KG + rubric + sample exam vào MongoDB**

```python
# data/seed.py
from pymongo import MongoClient
import json, os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/master_db")

def seed():
    client = MongoClient(MONGO_URI)
    db = client.master_db

    with open("knowledge_graph/math_kg.json", "r") as f:
        kg = json.load(f)
    db.knowledge_nodes.drop()
    db.knowledge_nodes.insert_many(kg["nodes"])
    print(f"Seeded {len(kg['nodes'])} KG nodes")

    with open("exam_bank/rubrics/thptqg_math.json", "r") as f:
        rubric = json.load(f)
    db.rubrics.update_one({"exam_type": "THPTQG", "subject": "math"}, {"$set": rubric}, upsert=True)
    print("Seeded rubric")

    with open("exam_bank/sample_thptqg_2025.json", "r") as f:
        exam = json.load(f)
    db.exams.update_one({"exam_type": "THPTQG", "source": "sample"}, {"$set": exam}, upsert=True)
    print(f"Seeded sample exam with {exam['total_questions']} questions")

if __name__ == "__main__":
    seed()
```

- [ ] **Step 2: Chạy seed**

Run: `cd master/data && python seed.py`
Expected: "Seeded X KG nodes", "Seeded rubric", "Seeded sample exam..."

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat(data): add MongoDB seed script for KG, rubrics, sample exam"
```

---

### Task D5-D7: Scraping (ngày 3-6)

- [ ] **D5:** Viết scraper cho toanmath.com — Crawl + parse câu hỏi
- [ ] **D6:** Post-process: chuẩn hóa format, gán topic_tags từ KG
- [ ] **D7:** Load scraped data vào MongoDB — Mục tiêu ít nhất **20 đề thi Toán**

Mỗi đề thi lưu vào MongoDB phải theo đúng Exam JSON schema (COORDINATION.md mục 3.2).

---

## Tổng kết: Thứ tự ưu tiên tuyệt đối

| Ưu tiên | Việc | Ai | Deadline |
|---------|------|----|----------|
| **P0** | `common/` (config, llm_client, message, tool) | Khang | Ngày 2 |
| **P0** | DB schema + docker-compose + seed data | Nhật Huy | Ngày 2 |
| **P0** | NestJS init + auth + exam API | Nguyên Huy | Ngày 4 |
| **P0** | `baseagent.py` + manager + server.py | Khang | Ngày 4 |
| **P0** | Parser agent (preprocessing + OCR + extractor) | Phúc | Ngày 4 |
| **P0** | Sample exam JSON (10 câu) cho test | Nhật Huy | Ngày 2 |
| **P1** | Teacher agent + Verifier agent | Phúc | Ngày 7 |
| **P1** | Adaptive agent (BKT + IRT) | Khang | Ngày 6 |
| **P1** | Frontend: login + dashboard + exam room | Nguyên Huy | Ngày 8 |
| **P1** | Scrape 20+ đề thi thật | Nhật Huy | Ngày 6 |
| **P2** | Frontend: results + upload page | Nguyên Huy | Ngày 10 |
| **P2** | Grading engine (SymPy) | Phúc | Ngày 8 |
| **P2** | Wire all agents + E2E test | Khang | Ngày 9 |
| **P3** | Bug fix + UI polish + demo prep | Tất cả | Ngày 11-12 |
