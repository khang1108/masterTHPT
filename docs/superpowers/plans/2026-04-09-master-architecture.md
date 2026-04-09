# MASTER — Architecture Overview & System Design

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the complete system architecture, service boundaries, data contracts, and infrastructure needed to ship the MASTER MVP in 12 days.

**Architecture:** 4 independent services (Frontend, Backend API, Agent Service, Grading Engine) communicating via HTTP/JSON, backed by MongoDB and a GPU-hosted vLLM cluster serving 3 open-source models.

**Tech Stack:** Next.js 14, NestJS, Python/FastAPI, MongoDB, vLLM on A100, Qwen3-8B, Qwen3-14B-Q, Gemma-3-4B, PaddleOCR, SymPy, Docker Compose.

---

## 1. Service Topology

```
┌─────────────┐     HTTP/JSON      ┌──────────────────┐     HTTP/JSON      ┌──────────────────┐
│  Next.js 14  │ ────────────────→  │  NestJS API      │ ────────────────→  │  Agent Service   │
│  (Frontend)  │ ←────────────────  │  (Backend)       │ ←────────────────  │  (Python/FastAPI) │
│  Port 3000   │                    │  Port 3001       │                    │  Port 8000       │
└─────────────┘                    └───────┬──────────┘                    └───────┬──────────┘
                                           │                                       │
                                           │ Mongoose ODM                          │ HTTP
                                           ▼                                       ▼
                                   ┌──────────────┐                       ┌─────────────────┐
                                   │  MongoDB      │                       │ Grading Engine   │
                                   │  Port 27017   │                       │ (Python/FastAPI) │
                                   └──────────────┘                       │ Port 8001        │
                                                                          └─────────────────┘
                                                                                   │
                                                                          ┌────────▼────────┐
                                                                          │  vLLM Cluster   │
                                                                          │  (A100 GPU)     │
                                                                          │  Port 8080-8082 │
                                                                          └─────────────────┘
```

### Invariant Rules

1. **Frontend NEVER calls Agent Service directly.** All requests go through NestJS API.
2. **Agent Service NEVER writes to MongoDB directly.** It returns results to NestJS, which persists data.
3. **Each service runs in its own Docker container** with its own Dockerfile.
4. **All inter-service communication is HTTP/JSON** — no gRPC, no message queues in MVP.

---

## 2. Canonical Repository Layout

```
GDGoC_HackathonVietnam/
├── master/
│   ├── apps/
│   │   ├── api/                           ← NestJS backend (Nguyên Huy)
│   │   │   ├── src/
│   │   │   │   ├── auth/                  ← JWT register/login
│   │   │   │   ├── exams/                 ← Exam CRUD + session management
│   │   │   │   ├── upload/                ← File upload (multer)
│   │   │   │   ├── students/              ← Student profile endpoints
│   │   │   │   ├── agent-dispatch/        ← HTTP proxy to Agent Service
│   │   │   │   ├── common/                ← Guards, decorators, pipes
│   │   │   │   ├── app.module.ts
│   │   │   │   └── main.ts
│   │   │   ├── package.json
│   │   │   ├── tsconfig.json
│   │   │   └── Dockerfile
│   │   │
│   │   ├── web/                           ← Next.js frontend (Nguyên Huy)
│   │   │   ├── src/
│   │   │   │   ├── app/                   ← App Router pages
│   │   │   │   ├── components/            ← Reusable UI components
│   │   │   │   ├── lib/                   ← API client, utils
│   │   │   │   └── hooks/                 ← Custom React hooks
│   │   │   ├── package.json
│   │   │   └── Dockerfile
│   │   │
│   │   └── grading-engine/                ← SymPy microservice (Phúc)
│   │       ├── main.py
│   │       ├── sympy_grader.py
│   │       ├── requirements.txt
│   │       └── Dockerfile
│   │
│   ├── agents/                            ← Python Agent Service (Khang + Phúc)
│   │   ├── src/
│   │   │   ├── common/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py              ← Centralized configuration
│   │   │   │   ├── llm_client.py          ← Unified LLM client (vLLM + Gemini)
│   │   │   │   ├── message.py             ← Pydantic models + enums
│   │   │   │   └── tools.py               ← Tool registry base
│   │   │   ├── base_agent.py              ← Enhanced abstract base class
│   │   │   ├── manager/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── intent.py              ← Intent classifier
│   │   │   │   ├── planner.py             ← DAG execution planner
│   │   │   │   └── agent.py               ← ManagerAgent class
│   │   │   ├── parser/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── preprocessing.py       ← OpenCV image processing
│   │   │   │   ├── ocr.py                 ← PaddleOCR wrapper
│   │   │   │   ├── extractor.py           ← Question extraction logic
│   │   │   │   └── agent.py               ← ParserAgent class
│   │   │   ├── teacher/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── grading.py             ← Per-type grading strategies
│   │   │   │   ├── error_analysis.py      ← Error taxonomy classifier
│   │   │   │   └── agent.py               ← TeacherAgent class
│   │   │   ├── verifier/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── discrepancy.py         ← Teacher-vs-Verifier diff
│   │   │   │   ├── debate.py              ← Multi-round debate protocol
│   │   │   │   └── agent.py               ← VerifierAgent class
│   │   │   ├── adaptive/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── bkt.py                 ← Bayesian Knowledge Tracing
│   │   │   │   ├── irt.py                 ← Item Response Theory
│   │   │   │   ├── cat.py                 ← Computerized Adaptive Testing
│   │   │   │   └── agent.py               ← AdaptiveAgent class
│   │   │   └── server.py                  ← FastAPI entry point
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   ├── test_base_agent.py
│   │   │   ├── test_llm_client.py
│   │   │   ├── test_manager.py
│   │   │   ├── test_parser.py
│   │   │   ├── test_teacher.py
│   │   │   ├── test_verifier.py
│   │   │   └── test_adaptive.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── data/                              ← Data Engineering (Nhật Huy)
│       ├── knowledge_graph/
│       │   └── math_10_12.json            ← Math knowledge tree
│       ├── exam_bank/
│       │   ├── rubrics/
│       │   │   ├── thptqg_math.json
│       │   │   └── v_act_math.json
│       │   └── samples/
│       │       └── thptqg_2025_math_sample.json
│       ├── scrapers/
│       │   ├── toanmath_scraper.py
│       │   ├── vietjack_scraper.py
│       │   └── post_processor.py
│       └── seed.py                        ← Load all data into MongoDB
│
├── infra/
│   ├── docker-compose.yml                 ← Local dev (MongoDB + services)
│   ├── docker-compose.gpu.yml             ← GPU server (vLLM instances)
│   └── mongo-init.js                      ← MongoDB initialization
│
├── .env
├── .gitignore
└── README.md
```

---

## 3. Data Contracts (JSON Schemas)

These 3 schemas are the **binding contracts** between all 4 services. Any change MUST be agreed by all team members.

### 3.1 TaskRequest — NestJS → Agent Service

```json
{
  "student_id": "string (uuid)",
  "intent": "EXAM_PRACTICE | GRADE_SUBMISSION | VIEW_ANALYSIS | ASK_HINT | REVIEW_MISTAKE | UNKNOWN",
  "user_message": "string",
  "session_id": "string (uuid, optional)",
  "file_urls": ["string (optional)"],
  "metadata": {
    "subject": "string",
    "exam_type": "string",
    "student_answers": {"q1": "A", "q2": "B"},
    "question_id": "string (for ASK_HINT)"
  }
}
```

### 3.2 TaskResponse — Agent Service → NestJS

```json
{
  "task_id": "string (uuid)",
  "status": "success | error",
  "intent": "string",
  "result": {},
  "agent_trail": ["manager", "parser", "teacher", "verifier"],
  "error_message": "string (if status=error)"
}
```

### 3.3 Exam JSON — Parser output → Teacher input → DB → Frontend

```json
{
  "exam_id": "uuid",
  "source": "image | pdf | manual",
  "subject": "math",
  "exam_type": "THPTQG",
  "total_questions": 50,
  "sections": [
    {
      "type": "multiple_choice",
      "questions": [
        {
          "id": "q1",
          "question_index": 1,
          "type": "multiple_choice",
          "content": "Tìm nguyên hàm của f(x) = 2x + 1",
          "content_latex": "\\text{Tìm nguyên hàm của } f(x) = 2x + 1",
          "options": ["A. x² + x + C", "B. x² + C", "C. 2x² + x + C", "D. x + C"],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_b": 0.3,
          "topic_tags": ["math.12.ch2.integrals"]
        }
      ]
    },
    {
      "type": "essay",
      "questions": [
        {
          "id": "q41",
          "question_index": 41,
          "type": "essay",
          "content": "Cho hình chóp S.ABCD có đáy là hình vuông...",
          "has_image": true,
          "image_url": "/uploads/q41_figure.png",
          "max_score": 1.0,
          "topic_tags": ["math.12.ch4.solid_geometry"]
        }
      ]
    }
  ]
}
```

### 3.4 Evaluation JSON — Teacher output → Verifier input → DB → Frontend

```json
{
  "evaluation_id": "uuid",
  "exam_id": "uuid",
  "student_id": "uuid",
  "total_score": 7.25,
  "max_score": 10.0,
  "confidence": 0.85,
  "per_question": [
    {
      "question_id": "q1",
      "student_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "score": 0.2,
      "max_score": 0.2,
      "reasoning": "Đáp án đúng."
    },
    {
      "question_id": "q41",
      "student_answer": "...",
      "is_correct": false,
      "score": 0.5,
      "max_score": 1.0,
      "reasoning": "Xác định đúng hình chiếu H nhưng tính sai khoảng cách...",
      "error_analysis": {
        "error_type": "CALCULATION_ERROR",
        "root_cause": "Áp dụng sai định lý Pythagore 3D",
        "knowledge_component": "math.12.ch4.solid_geometry",
        "remedial": "Ôn lại: Khoảng cách từ điểm đến mặt phẳng"
      }
    }
  ],
  "overall_analysis": {
    "strengths": ["math.12.ch2.integrals"],
    "weaknesses": ["math.12.ch4.solid_geometry"],
    "recommended_topics": ["math.12.ch4.solid_geometry", "math.11.ch1.trig"]
  }
}
```

### 3.5 Error Type Taxonomy (fixed — do not extend)

| error_type | Meaning |
|---|---|
| `CONCEPT_GAP` | Missing foundational knowledge |
| `CALCULATION_ERROR` | Arithmetic/computation mistake |
| `INCOMPLETE_REASONING` | Missing intermediate steps |
| `MISINTERPRETATION` | Misunderstood the problem |
| `PRESENTATION_FLAW` | Unclear or improper notation |

### 3.6 topic_tags Convention

Format: `{subject}.{grade}.{chapter_code}.{topic_code}`

Examples:
- `math.12.ch2.integrals`
- `math.11.ch1.trig`
- `math.12.ch4.solid_geometry`
- `math.10.ch3.equations`

Nhật Huy defines the official list in `master/data/knowledge_graph/math_10_12.json`. All agents MUST use tags from this list.

---

## 4. MongoDB Schema Design

> Changed from PostgreSQL to MongoDB — each student's data is heterogeneous (mastery scores, evaluation payloads, error analyses vary per student).

### Collections

#### `students`
```json
{
  "_id": "ObjectId",
  "email": "string (unique)",
  "name": "string",
  "password_hash": "string",
  "grade": 10 | 11 | 12,
  "irt_profile": {
    "theta": 0.0,
    "theta_se": 1.0,
    "total_items": 0
  },
  "mastery_scores": {
    "math.12.ch2.integrals": {
      "p_l": 0.1,
      "total_attempts": 0,
      "correct_attempts": 0,
      "updated_at": "ISODate"
    }
  },
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### `exams`
```json
{
  "_id": "ObjectId",
  "subject": "math",
  "exam_type": "THPTQG",
  "year": 2025,
  "source": "toanmath.com",
  "total_questions": 50,
  "duration_minutes": 90,
  "sections": [
    {
      "type": "multiple_choice",
      "questions": [
        {
          "id": "q1",
          "question_index": 1,
          "type": "multiple_choice",
          "content": "...",
          "content_latex": "...",
          "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
          "correct_answer": "A",
          "has_image": false,
          "image_url": null,
          "difficulty_a": 1.0,
          "difficulty_b": 0.3,
          "topic_tags": ["math.12.ch2.integrals"],
          "max_score": 0.2
        }
      ]
    }
  ],
  "metadata": {},
  "created_at": "ISODate"
}
```

#### `exam_sessions`
```json
{
  "_id": "ObjectId",
  "student_id": "ObjectId (ref students)",
  "exam_id": "ObjectId (ref exams)",
  "intent": "EXAM_PRACTICE | GRADE_SUBMISSION",
  "status": "IN_PROGRESS | SUBMITTED | GRADED",
  "started_at": "ISODate",
  "submitted_at": "ISODate | null",
  "student_answers": {"q1": "A", "q2": "B"},
  "uploaded_file_url": "string | null",
  "evaluation": {
    "total_score": 7.25,
    "max_score": 10.0,
    "confidence": 0.85,
    "per_question": [],
    "overall_analysis": {}
  },
  "agent_trail": ["manager", "parser", "teacher", "verifier"]
}
```

#### `knowledge_nodes`
```json
{
  "_id": "ObjectId",
  "node_id": "math.12.ch2.integrals",
  "subject": "math",
  "grade": 12,
  "chapter": "ch2",
  "topic": "integrals",
  "display_name": "Nguyên hàm - Tích phân",
  "prerequisites": ["math.12.ch1.derivatives"]
}
```

#### `rubrics`
```json
{
  "_id": "ObjectId",
  "exam_type": "THPTQG",
  "subject": "math",
  "year": 2025,
  "scoring": {
    "multiple_choice": { "count": 40, "points_each": 0.2, "total": 8.0 },
    "essay": { "count": 10, "total": 2.0 }
  },
  "duration_minutes": 90,
  "sections_breakdown": {}
}
```

### Indexes

```javascript
db.students.createIndex({ "email": 1 }, { unique: true });
db.exams.createIndex({ "subject": 1, "exam_type": 1 });
db.exam_sessions.createIndex({ "student_id": 1, "status": 1 });
db.exam_sessions.createIndex({ "student_id": 1, "created_at": -1 });
db.knowledge_nodes.createIndex({ "node_id": 1 }, { unique: true });
db.rubrics.createIndex({ "exam_type": 1, "subject": 1 }, { unique: true });
```

---

## 5. LLM Infrastructure — vLLM on A100

### Model Serving Architecture

The A100 GPU server runs **3 vLLM instances**, each serving one model with OpenAI-compatible API:

| Port | Model | Agent | VRAM (est.) |
|------|-------|-------|-------------|
| 8080 | `Qwen/Qwen3-8B` | Manager | ~16 GB |
| 8081 | `Qwen/Qwen3-14B-GPTQ` | Teacher | ~12 GB (quantized) |
| 8082 | `google/gemma-3-4b-it` | Verifier | ~8 GB |

Total estimated VRAM: ~36 GB out of 80 GB available on A100.

### vLLM Launch Commands

```bash
# Manager model
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-8B \
  --port 8080 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.25

# Teacher model
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen3-14B-GPTQ-Int4 \
  --port 8081 \
  --max-model-len 8192 \
  --quantization gptq \
  --gpu-memory-utilization 0.30

# Verifier model
python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-3-4b-it \
  --port 8082 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.15
```

### Fallback Strategy

If GPU server is not ready, ALL agents fall back to **Gemini 2.5 Flash** via Google GenAI SDK:

```python
# Fallback check in config.py
USE_GEMINI_FALLBACK = os.getenv("USE_GEMINI_FALLBACK", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

### LLM Client Design

The `LLMClient` class provides a unified interface to both vLLM (OpenAI-compatible) and Gemini:

```python
class LLMClient:
    async def chat(self, messages: list[dict], model: str, **kwargs) -> str: ...
    async def chat_json(self, messages: list[dict], model: str, schema: type) -> dict: ...
```

- When `USE_GEMINI_FALLBACK=false`: uses `httpx.AsyncClient` to call vLLM's `/v1/chat/completions`
- When `USE_GEMINI_FALLBACK=true`: uses `google.generativeai` SDK to call Gemini 2.5 Flash
- Both paths return the same response format — agents don't know which backend is active

---

## 6. API Endpoints Summary

### Agent Service (Port 8000)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agents/dispatch` | Main dispatch — accepts TaskRequest, returns TaskResponse |
| `POST` | `/api/agents/parse` | Direct file parsing (multipart/form-data) |
| `GET` | `/health` | Liveness check |

### NestJS API (Port 3001)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `POST` | `/auth/register` | Register student | No |
| `POST` | `/auth/login` | Login → JWT | No |
| `GET` | `/exams` | List exams (filter: subject, type) | Yes |
| `GET` | `/exams/:id` | Exam detail + questions | Yes |
| `POST` | `/exams/sessions` | Create exam session | Yes |
| `POST` | `/exams/sessions/:id/submit` | Submit answers → trigger grading | Yes |
| `GET` | `/exams/sessions/:id/results` | Get grading results | Yes |
| `POST` | `/upload` | Upload image/PDF | Yes |
| `GET` | `/students/me/profile` | Current student mastery profile | Yes |
| `GET` | `/students/me/history` | Exam session history | Yes |

### Grading Engine (Port 8001)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/verify/math` | Verify math expression with SymPy |
| `POST` | `/verify/numeric` | Verify numeric equality |
| `GET` | `/health` | Liveness check |

---

## 7. Intent-to-Agent Flow Mapping

| Intent | Agent Pipeline | Description |
|--------|---------------|-------------|
| `EXAM_PRACTICE` | Manager → Adaptive → (return exam) → ... → Parser → Teacher → Verifier → Adaptive | Full exam flow |
| `GRADE_SUBMISSION` | Manager → Parser → Teacher → Verifier → Adaptive | Upload & grade |
| `VIEW_ANALYSIS` | Manager → Adaptive | Return student profile |
| `ASK_HINT` | Manager → Teacher | Scaffolded hint |
| `REVIEW_MISTAKE` | Manager → Adaptive | Historical errors |
| `UNKNOWN` | Manager → clarification | Ask user to clarify |

---

## 8. Docker Compose — Local Development

```yaml
# infra/docker-compose.yml
version: "3.8"

services:
  mongodb:
    image: mongo:7
    container_name: master-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: master
      MONGO_INITDB_ROOT_PASSWORD: master_dev_pw
      MONGO_INITDB_DATABASE: master_db
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro

  mongo-express:
    image: mongo-express:1
    container_name: master-mongo-ui
    ports:
      - "8888:8081"
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: master
      ME_CONFIG_MONGODB_ADMINPASSWORD: master_dev_pw
      ME_CONFIG_MONGODB_URL: mongodb://master:master_dev_pw@mongodb:27017/
    depends_on:
      - mongodb

volumes:
  mongodb_data:
```

### GPU Server Compose (separate)

```yaml
# infra/docker-compose.gpu.yml
version: "3.8"

services:
  vllm-manager:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    ports:
      - "8080:8000"
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
    command: >
      --model Qwen/Qwen3-8B
      --max-model-len 8192
      --gpu-memory-utilization 0.25
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  vllm-teacher:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    ports:
      - "8081:8000"
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
    command: >
      --model Qwen/Qwen3-14B-GPTQ-Int4
      --max-model-len 8192
      --quantization gptq
      --gpu-memory-utilization 0.30

  vllm-verifier:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    ports:
      - "8082:8000"
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
    command: >
      --model google/gemma-3-4b-it
      --max-model-len 4096
      --gpu-memory-utilization 0.15
```

---

## 9. Environment Variables

```bash
# .env (local development)

# MongoDB
MONGODB_URI=mongodb://master:master_dev_pw@localhost:27017/master_db?authSource=admin

# JWT
JWT_SECRET=hackathon-dev-secret-change-in-prod

# Service URLs
AGENT_SERVICE_URL=http://localhost:8000
GRADING_ENGINE_URL=http://localhost:8001

# LLM — vLLM on GPU server
VLLM_BASE_URL=http://<gpu-server-ip>
VLLM_MANAGER_PORT=8080
VLLM_TEACHER_PORT=8081
VLLM_VERIFIER_PORT=8082

# LLM model names
LLM_MANAGER_MODEL=Qwen3-8B
LLM_TEACHER_MODEL=Qwen3-14B-Quantized
LLM_VERIFIER_MODEL=Gemma-3-4B

# Gemini fallback
USE_GEMINI_FALLBACK=false
GEMINI_API_KEY=<your-key>
GEMINI_MODEL=gemini-2.5-flash
```

---

## 10. Critical Path & Dependencies

```
Day 1-2 (Foundation):
  Khang: common/ + base_agent.py + server.py skeleton   ← BLOCKS Phúc
  Nhật Huy: docker-compose + sample exam JSON            ← BLOCKS team testing
  Nguyên Huy: init NestJS + MongoDB + auth module        ← Independent
  Phúc: preprocessing.py + PaddleOCR install             ← Independent (no LLM needed)

Day 3-4 (Core Agents):
  Khang: Manager Agent (intent + planner + dispatch)
  Phúc: Parser Agent (OCR + extraction)                  ← Needs common/
  Nguyên Huy: Exam API + Session API
  Nhật Huy: Scrapers + knowledge graph

Day 5-7 (Grading Pipeline):
  Phúc: Teacher Agent + Verifier Agent
  Khang: Adaptive Agent (BKT + IRT + CAT)
  Nguyên Huy: Frontend (exam room, results)
  Nhật Huy: 20+ exams in DB

Day 8-9 (Integration):
  ALL: Full GRADE_SUBMISSION flow end-to-end
  Fix data format mismatches, prompt tuning

Day 10 (Feature Freeze):
  No new features. Bug fixes only.

Day 11-12 (Polish):
  UI polish, demo preparation, rehearsal
```

**Bottleneck:** Khang MUST push `common/` by end of Day 2 so Phúc is not blocked.

---

## 11. Module Plans (Separate Documents)

| Plan | Owner | File |
|------|-------|------|
| Module A: Agent Core Infrastructure | Khang | `2026-04-09-module-a-agent-core.md` |
| Module B: Grading Pipeline | Phúc | `2026-04-09-module-b-grading-pipeline.md` |
| Module C: Fullstack | Nguyên Huy | `2026-04-09-module-c-fullstack.md` |
| Module D: Data Engineering | Nhật Huy | `2026-04-09-module-d-data-engineering.md` |
