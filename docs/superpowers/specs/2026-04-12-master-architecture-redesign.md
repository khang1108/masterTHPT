# MASTER Architecture Redesign: StateGraph Orchestrator + GenAL-Inspired Adaptive

**Date:** 2026-04-12
**Status:** Draft
**Context:** GDGoC Hackathon Vietnam 2026, Round 2 deadline 2026-04-19

## 1. Problem Statement

The original MASTER architecture (Tabs_Engineers.md) uses a Director-Employees pattern with a Manager Agent (LLM) orchestrating Teacher, Verifier, Parser, and Adaptive agents. After reviewing current research (IntelliCode EACL 2026, GenAL AAAI 2025, HPO AAAI 2026, CIKT 2025), several issues emerge:

- **Manager Agent as LLM is wasteful:** Routing 6 fixed intents is deterministic business logic, not a reasoning task. Each request costs 1 unnecessary LLM call.
- **Adaptive Agent wrapping BKT/IRT in an "agent" is over-engineering:** BKT/IRT/CAT are probabilistic algorithms that run in <1ms with NumPy. They don't need LLM reasoning.
- **CAT (Fisher Information) ignores semantic content:** Question selection based purely on mathematical information gain misses "student is weak at integrals because they don't understand antiderivatives" reasoning.
- **Teacher-Verifier debate on all questions is expensive:** Multiple-choice exact-match questions don't need multi-round LLM debate.

## 2. Design Principles

1. **Graph is the orchestrator, LLM is the reasoner.** The StateGraph decides flow; LLMs decide content.
2. **Use LLM only where human-like reasoning is needed.** Grading multiple choice, routing intents, updating BKT parameters — these are code, not LLM tasks.
3. **Two-tier selection: math first, then semantics.** BKT/IRT pre-filters for mathematical soundness (ZPD boundary), then LLM reasons about semantic relevance.
4. **Selective LLM usage.** Solution generation and verification focus on wrong answers and complex questions.

## 3. Architecture Overview

The system has two major pipelines: Offline (Crawler) and Online (User-Facing).

### 3.1 Offline Pipeline: Crawler

Runs continuously/scheduled. Independent from user requests.

```
toanmath.com / thithu.edu.vn / ...
       │
       ▼
   Crawler (Playwright/Scrapy, scheduled)
       │
       ▼
   PDF Storage (GCS / local)
       │
       ▼
   Parser Agent (PaddleOCR + PP-OCRv5 + VLM)
       │
       ▼
   Schema Validator (Pydantic)
       │
       ├──▶ MongoDB (QuestionExam collection)
       └──▶ Embedding Indexer (vector store for RAG)
```

- Crawler downloads exam PDFs from configured sources.
- Parser Agent extracts structured JSON (subject, questions, options, difficulty_estimate, topic_tags).
- Validated questions are stored in `QuestionExam` collection with embeddings for vector search.
- Knowledge Graph nodes are updated with new KCs discovered from questions.

### 3.2 Online Pipeline: StateGraph Orchestrator

Replaces Manager Agent. A single LangGraph StateGraph handles all user intents.

#### 3.2.1 Shared State Schema

```python
class MasterState(TypedDict):
    # Request
    request: MessageRequest
    intent: Intent  # EXAM_PRACTICE, GRADE_SUBMISSION, VIEW_ANALYSIS, ASK_HINT, REVIEW_MISTAKE

    # Learner context
    student_id: str
    learner_profile: LearnerProfile  # BKT mastery per KC, IRT theta, history

    # Exam context
    exam_id: Optional[str]
    questions: list[Question]
    student_answers: Optional[dict]

    # Auto-grading (exact match)
    auto_grade_result: Optional[AutoGradeResult]  # score, per-question correct/incorrect

    # Solution generation
    solutions: Optional[list[SolutionStep]]  # Teacher-generated step-by-step solutions
    verified_solutions: Optional[list[SolutionStep]]  # After Verifier review

    # Adaptive
    selected_questions: Optional[list[Question]]
    profile_updates: Optional[dict]

    # Response
    response: Optional[MessageResponse]
```

#### 3.2.2 Intent Routing (Replaces Manager Agent CoT)

```python
def classify_intent(state: MasterState) -> MasterState:
    """Rule-based intent classification. No LLM needed for 6 fixed intents."""
    request = state["request"]
    metadata = request.metadata or {}

    if metadata.get("intent"):
        state["intent"] = Intent(metadata["intent"])
    else:
        # Keyword-based fallback
        text = request.content.lower()
        if any(kw in text for kw in ["làm đề", "thi thử", "luyện"]):
            state["intent"] = Intent.EXAM_PRACTICE
        elif any(kw in text for kw in ["chấm", "nộp bài"]):
            state["intent"] = Intent.GRADE_SUBMISSION
        # ... etc
    return state

def route_by_intent(state: MasterState) -> str:
    routes = {
        Intent.EXAM_PRACTICE: "exam_practice_router",
        Intent.GRADE_SUBMISSION: "auto_grade",
        Intent.VIEW_ANALYSIS: "build_analysis",
        Intent.ASK_HINT: "teacher_hint",
        Intent.REVIEW_MISTAKE: "build_review",
    }
    return routes.get(state["intent"], "clarification_loop")
```

#### 3.2.3 EXAM_PRACTICE Flow

Two modes:

**Browse & Pick:** User browses exam bank, selects a specific exam. No LLM needed.

```
enrich_context → query_exam_bank (filter by subject/year/source)
  → return_exam_list (for UI)
  → [user selects] → load_selected_exam → prepare_exam_session
```

**Personalized Gen:** System generates personalized exam using GenAL-style selection.

```
enrich_context → get_learner_profile
  → bkt_irt_prefilter (ZPD + content balance, ~20 candidates)
  → rag_retrieve (QuestionExam embeddings + KG context)
  → genal_question_select (LLM semantic reasoning)
  → assemble_exam → prepare_exam_session
```

Routing logic:
```python
def route_exam_practice(state: MasterState) -> str:
    metadata = state["request"].metadata or {}
    if metadata.get("exam_id"):
        return "load_selected_exam"    # User picked specific exam
    if metadata.get("mode") == "personalized":
        return "get_learner_profile"   # Gen personalized exam
    return "query_exam_bank"           # Default: browse
```

#### 3.2.4 Post-Submission Flow: Auto-Grade + Solution Generation

Key insight: multiple-choice grading is exact match (no LLM). Teacher and Verifier focus on generating and verifying step-by-step solutions.

```
[student submits answers]
  → auto_grade (Python exact match: correct/incorrect per question, total score)
  → calculate_score
  → teacher_generate_solutions (TeacherAgent: step-by-step for all questions)
  → solution_quality_gate
      ├─ [wrong answers / complex questions] → verifier_review_solutions (VerifierAgent)
      └─ [correct + simple] → skip verification
  → update_profile (LearnerProfileService)
  → format_response (score + solutions to UI)
```

**auto_grade:** Pure Python. Student answers arrive as JSON from the web UI (user selects A/B/C/D during exam session). For each question: `student_answers[q_id] == correct_answers[q_id]`. Returns score and per-question status. Note: image/PDF-based answer extraction (via Parser Agent) is a future extension, not part of the primary flow.

**teacher_generate_solutions:** TeacherAgent generates detailed step-by-step solutions. Focus on:
- Wrong answers: explain what the correct approach is, where the student likely went wrong
- Right answers: brief confirmation with key concept
- Uses RAG to retrieve textbook context and rubric

**solution_quality_gate:** Selective Verifier activation:
```python
def route_solution_quality(state: MasterState) -> str:
    wrong_count = sum(1 for q in state["auto_grade_result"].per_question if not q.is_correct)
    has_complex = any(q.question_type in ("essay", "long_answer") for q in state["questions"])

    if wrong_count > 0 or has_complex:
        return "verifier_review_solutions"
    return "update_profile"
```

**verifier_review_solutions:** VerifierAgent reviews Teacher's solutions for:
- Logical correctness (are the steps valid?)
- Completeness (any missing steps?)
- Clarity (understandable for THPT students?)
- Formula accuracy (correct formulas cited?)

**Important change from current code:** The existing `GradingPipeline` runs up to 3 debate rounds between Teacher and Verifier (score negotiation). The redesign simplifies this to a **single-pass review** focused on solution quality, not score agreement. Scores are determined by exact match (no negotiation needed). If Verifier finds issues with solution logic/clarity, it annotates corrections directly. Multi-round debate is eliminated for MVP; it can be reintroduced for future essay/free-response support where scoring is subjective.

#### 3.2.5 ASK_HINT Flow

```
[user clicks ask_hint on question Q]
  → rag_retrieve (textbook context + similar solved examples for Q's topic)
  → teacher_hint (TeacherAgent with scaffolding prompt)
      Level 1: Remind relevant formula/concept
      Level 2: Show approach direction
      Level 3: Show partial solution
      Level 4: Show full solution (SHOW_SOLUTION)
  → format_response
```

Hint levels escalate on repeated requests for the same question.

#### 3.2.6 VIEW_ANALYSIS and REVIEW_MISTAKE Flows

These are primarily database query + formatting flows, minimal LLM usage.

**VIEW_ANALYSIS:**
```
enrich_context → get_learner_profile → kg_trace_weaknesses
  → format_analysis (mastery per topic, trend, weak KCs, prerequisite gaps)
```

**REVIEW_MISTAKE:**
```
enrich_context → query_error_history → kg_map_errors
  → format_review (errors by taxonomy, impact ranking, recommended remediation)
```

## 4. AdaptiveService: BKT/IRT + RAG + Knowledge Graph

Not an "agent" — a Python service combining deterministic algorithms with retrieval.

### 4.1 Components

**LearnerProfileService** (pure Python):
- Manages BKT parameters per Knowledge Component (KC): P(L), P(T), P(S), P(G)
- Manages IRT theta (student ability estimate)
- Updates after each grading session using standard BKT/IRT formulas
- Generates text narrative for GenAL QuestionSelector (template-based, not LLM)

**Knowledge Graph** (NetworkX or Neo4j):
- Nodes: Knowledge Components (e.g., "tích phân bất định", "nguyên hàm")
- Edges: `prerequisite_of`, `related_to`, `harder_than`
- `trace_weaknesses(weak_kcs)`: follows prerequisite chains to find root-cause KCs
- Populated from question topic_tags during Crawler pipeline

**RAG Module** (vector search):
- Sources: QuestionExam collection (primary), Textbook chunks, Rubric store
- Used by: GenAL QuestionSelector, Teacher (solutions), ASK_HINT

### 4.2 GenAL-Inspired Question Selection

Two-tier approach:

**Tier 1 - BKT/IRT Pre-filter (< 1ms):**
```python
def pre_filter(theta: float, question_bank: list, answered: set) -> list:
    candidates = [q for q in question_bank if q.id not in answered]
    zpd_candidates = [q for q in candidates if abs(theta - q.difficulty) < 1.5]
    balanced = apply_content_balance(zpd_candidates, max_per_topic=3)
    return balanced[:20]
```

**Tier 2 - GenAL LLM Selection (~2-3s):**

Input to LLM:
1. Learner narrative (from LearnerProfileService.generate_narrative())
2. KG context (prerequisite chains, root-cause KCs)
3. RAG context (similar questions from QuestionExam, textbook sections)
4. 20 candidate questions with full text content

Output: Ordered list of 10 questions with reasoning for each selection.

The LLM understands semantic relationships that BKT/IRT miss: "student struggles with definite integrals because they don't fully grasp antiderivatives" → select questions that scaffold from antiderivative review to definite integral application.

### 4.3 Profile Narrative Generation

Template-based (not LLM), feeds into GenAL QuestionSelector:

```python
def generate_narrative(profile: LearnerProfile, kg_context: dict) -> str:
    weak_kcs = [kc for kc, m in profile.kc_mastery.items() if m < 0.6]
    strong_kcs = [kc for kc, m in profile.kc_mastery.items() if m > 0.85]
    root_causes = kg_context.get("root_cause_kcs", [])

    return f"""
    Student ability (IRT theta): {profile.theta:.2f}
    Overall: {len(strong_kcs)} strong KCs, {len(weak_kcs)} weak KCs
    Weakest areas: {', '.join(weak_kcs[:5])}
    Root-cause gaps (from KG): {', '.join(root_causes[:3])}
    Recent error patterns: {', '.join(profile.top_error_types[:3])}
    Trend: {'improving' if profile.trend > 0 else 'needs attention'}
    Sessions completed: {profile.session_count}
    """
```

### 4.4 SGK / CTGDPT 2018 knowledge graph (Toán 10–12)

**Anchor (đã chọn):** Neo toàn bộ skill theo **Chương trình GDPT 2018** (mục tiêu / nội dung / chuẩn kiến thức–kỹ năng), **không** lấy id trực tiếp từ một bộ SGK nhà xuất bản. Các bộ sách (Kết nối tri thức, Cánh Diều, Chân trời sáng tạo, …) chỉ dùng làm **tài liệu tham chiếu** khi gán nhãn tiếng Việt và khi cần bảng **alias chương → skill_id** (optional).

**Mô hình đồ thị:**

- **Node (skill):** một đơn vị nhỏ hơn “cả chương” nhưng gắn với **chương / mục** trong khung CT (ví dụ: “Giải phương trình bậc hai một ẩn” thuộc chương Đại số lớp 10). Mỗi node có metadata: `grade` (10|11|12), `domain` (Đại số / Hình học / Giải tích / Xác suất–Thống kê / … theo cách chia trong CT), `chapter_label` (nhãn hiển thị), `ct_anchor` (mã hoặc đoạn trích tham chiếu tới văn bản CT nếu có), `aliases[]` (tên gọi trong các SGK khác nhau).
- **Node tùy chọn (chapter container):** nếu UI cần nhóm theo chương, có thể thêm node loại `chapter` và cạnh `PART_OF` từ skill → chapter; MVP có thể chỉ dùng field `chapter_id` trên skill để giảm số node.
- **Cạnh (quan hệ giữa skill):** tập hữu hạn, có kiểu:
  - `PREREQUISITE` — A là điều kiện nền trước B (dùng cho `trace_weaknesses`, lộ trình ôn).
  - `RELATED` — liên quan ngang hàng (ôn tổng hợp, mở rộng).
  - `EXTENDS_ACROSS_GRADE` — nội dung lớp sau mở rộng lớp trước (ví dụ hàm số → đạo hàm).
  - `SAME_TOPIC_FAMILY` — cùng họ ý tưởng (tùy chọn, để tránh trùng lặp khi chọn câu).

**Nguồn dữ liệu để xây graph (không tự động “đọc SGK” là đủ):**

1. **Khung CT chính thức** (Bộ GD&ĐT): liệt kê mục tiêu / nội dung theo lớp → tạo danh sách skill gốc và id ổn định.
2. **Sách giáo khoa Toán 10, 11, 12** (một hoặc nhiều bộ): đối chiếu mục lục chương–bài với skill CT để viết mô tả ngắn, synonym, và (nếu cần) bảng map `sgk_chapter_ref → skill_id`.
3. **Quy trình xây dựng (đề xuất):** (a) bảng CSV/YAML `skills` theo CT; (b) bảng `edges` do chuyên môn hoặc LLM gợi ý + **review người**; (c) validate: không chu trình prerequisite vô lý, mỗi skill lớp 11–12 có ít nhất một đường prerequisite về lớp thấp hơn khi phù hợp.
4. **Tích hợp hệ thống:** export `graph.json` (nodes + edges) hoặc nạp vào NetworkX (Python in-process) **hoặc Neo4j**; câu hỏi trong `QuestionExam` gắn `skill_ids[]` để BKT/RAG/Adaptive dùng chung một namespace với KG. **Runtime Node.js:** có thể triển khai KG trên **Neo4j** và truy cập bằng driver chính thức (`neo4j-driver`) từ **NestJS** (REST/GraphQL nội bộ); Python agents gọi HTTP tới API đó hoặc dùng driver Python cùng một DB — không bắt buộc dùng NetworkX trong Python.

**Phạm vi hackathon:** có thể ship **một phần** Toán (ví dụ chỉ Đại số + Giải tích lớp 12) rồi mở rộng dần; quan trọng là **chuẩn hóa schema và id** theo CT trước khi nhân rộng nội dung.

## 5. Technology Mapping

| Component | Technology | Notes |
|-----------|-----------|-------|
| StateGraph Orchestrator | LangGraph StateGraph | Already in codebase for Teacher/Verifier |
| TeacherAgent | LangGraph + Qwen3-14B / Gemma 3 | Existing, needs prompt update for solution generation focus |
| VerifierAgent | LangGraph + Qwen3-4B / Gemma 3 | Existing, needs prompt update for solution review focus |
| LearnerProfileService | Python + NumPy | New, pure computation |
| Knowledge Graph | NetworkX (Python MVP) **hoặc** Neo4j + **Node.js** (NestJS + `neo4j-driver`) | CTGDPT 2018–anchored skills (Toán 10–12); edges PREREQUISITE / RELATED / EXTENDS; optional SGK alias tables; Python agents consume KG qua API hoặc shared Neo4j |
| RAG Module | LangChain + vector store | Embedding search over QuestionExam |
| GenAL QuestionSelector | LLM (same as Teacher model) | New, 1 LLM call per personalized exam gen |
| Crawler | Playwright (existing in tools.py) / Scrapy | New pipeline |
| Parser Agent | PaddleOCR + PP-OCRv5 + VLM | Per original spec |
| Auto-grading | Python exact match | New, trivial |
| Intent classifier | Rule-based Python | New, trivial |
| API Server | FastAPI | Needs implementation (server.py currently empty) |

## 6. LLM Call Budget per Intent

| Intent | LLM Calls | Details |
|--------|-----------|---------|
| EXAM_PRACTICE (browse) | 0 | Pure DB query |
| EXAM_PRACTICE (personalized) | 1 | GenAL QuestionSelector |
| GRADE_SUBMISSION | 1-2 | Teacher solutions + optional Verifier review |
| ASK_HINT | 1 | Teacher with RAG context |
| VIEW_ANALYSIS | 0 | DB query + formatting |
| REVIEW_MISTAKE | 0 | DB query + formatting |

Average: ~1.2 LLM calls per request (down from ~3 in original architecture with Manager + Teacher + Verifier on every request).

## 7. Research Backing

| Design Decision | Supporting Research |
|----------------|-------------------|
| StateGraph over Manager Agent | IntelliCode (EACL 2026): StateGraph Orchestrator with 6 specialized agents, centralized learner state |
| GenAL-style question selection | GenAL (AAAI 2025): Global Thinking + Local Teaching agents, outperforms BKT/IRT baselines |
| Selective solution verification | HPO (AAAI 2026): Adversarial debate for pedagogical assessment, 8B model outperforms GPT-4o |
| Multi-agent solution generation | RES (EMNLP 2025): Dialectical reasoning +34.86% QWK; Multi-agent Essay Grading (Jan 2026): few-shot calibration +26% |
| BKT/IRT + LLM hybrid | CIKT (2025): LLM-enhanced KT; Hybrid BKT+IRT (JEDM 2025): within 0.04 AUC-ROC of SOTA while interpretable |

## 8. Differences from Original Architecture (Tabs_Engineers.md)

| Aspect | Original | Redesign |
|--------|----------|----------|
| Orchestration | Manager Agent (LLM, CoT per request) | StateGraph (deterministic routing) |
| Grading | Teacher grades + Verifier debates score | Auto-grade (exact match) + Teacher generates solutions + Verifier reviews solutions |
| Adaptive | Agent wrapping BKT/IRT/CAT | Service: BKT/IRT (Python) + RAG + KG + GenAL LLM selection |
| Question selection | CAT with Fisher Information only | Two-tier: BKT/IRT pre-filter + GenAL semantic LLM selection |
| Debate scope | All questions go through debate | Selective: only wrong/complex questions get Verifier review |
| Token efficiency | ~3 LLM calls/request | ~1.2 LLM calls/request average |
| Crawler | Mentioned but not designed | Explicit offline pipeline: Crawl → Parse → Validate → Store → Index |

## 9. Hackathon MVP Scope

For the 7-day hackathon window (April 12-19):

**Must have:**
- StateGraph Orchestrator with EXAM_PRACTICE (browse) and GRADE_SUBMISSION flows
- Auto-grading (exact match)
- Teacher solution generation (update existing TeacherAgent prompts)
- FastAPI server.py exposing orchestrator to NestJS
- LearnerProfileService with basic BKT update

**Should have:**
- Personalized Gen with GenAL QuestionSelector
- Selective Verifier review
- Knowledge Graph (NetworkX): skill nodes anchored to **CTGDPT 2018** for Math 10–12, edges for prerequisites; subset of chapters for MVP; question bank tags use same `skill_id` namespace

**Could have (post-hackathon):**
- Crawler pipeline automation
- RAG integration for Teacher/Hint
- Full KG with auto-discovery from parsed questions
- ASK_HINT with scaffolding levels
- VIEW_ANALYSIS and REVIEW_MISTAKE flows
