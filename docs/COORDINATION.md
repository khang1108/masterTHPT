# MASTER — Tài liệu thống nhất kỹ thuật giữa các thành viên

> Tài liệu này trả lời câu hỏi: **"Bắt đầu từ đâu, thống nhất cái gì, ai làm gì, code giao tiếp với nhau ra sao?"**
> Mọi thành viên **phải đọc toàn bộ tài liệu này** trước khi viết dòng code đầu tiên.

---

## 1. Bức tranh tổng quan — Hệ thống gồm những gì?

MASTER không phải một ứng dụng monolithic. Nó gồm **4 service chạy độc lập**, giao tiếp với nhau qua HTTP/JSON:

```
┌─────────────┐      HTTP/JSON       ┌──────────────────┐      HTTP/JSON       ┌─────────────────┐
│  Next.js     │ ──────────────────→  │  NestJS API      │ ──────────────────→  │  Agent Service   │
│  (Frontend)  │ ←──────────────────  │  (Backend)       │ ←──────────────────  │  (Python/FastAPI)│
│  Port 3000   │                      │  Port 3001       │                      │  Port 8000       │
└─────────────┘                      └───────┬──────────┘                      └────────┬─────────┘
                                             │                                          │
                                             │ Prisma ORM                               │ HTTP
                                             ▼                                          ▼
                                     ┌──────────────┐                          ┌─────────────────┐
                                     │  PostgreSQL   │                          │ Grading Engine   │
                                     │  Port 5432   │                          │ (Python/FastAPI) │
                                     └──────────────┘                          │ Port 8001        │
                                                                               └─────────────────┘
                                                                                        │
                                                                               ┌────────▼────────┐
                                                                               │  vLLM / Gemini  │
                                                                               │  (Model Serving)│
                                                                               │  Port 8080-8082 │
                                                                               └─────────────────┘
```

**Nguyên tắc cốt lõi:**
- Frontend **không bao giờ** gọi thẳng Agent Service. Mọi request đi qua NestJS API.
- Agent Service **không bao giờ** ghi thẳng vào PostgreSQL thông qua Prisma. Nó trả kết quả về NestJS API, NestJS lo việc lưu DB.
- Mỗi service có Dockerfile riêng, chạy trong container riêng.

---

## 2. Cấu trúc thư mục — Thống nhất trước khi viết code

```
GDGoC_HackathonVietnam/
├── master/
│   ├── apps/
│   │   ├── api/                      ← NestJS backend     (Nguyên Huy phụ trách)
│   │   ├── web/                      ← Next.js frontend   (Nguyên Huy phụ trách)
│   │   └── grading-engine/           ← SymPy microservice  (Phúc phụ trách)
│   │
│   ├── agents/                       ← Python agent service (Khang + Phúc phụ trách)
│   │   ├── src/
│   │   │   ├── common/               ← Code dùng chung cho mọi agent
│   │   │   ├── manager/              ← Khang
│   │   │   ├── parser/               ← Phúc
│   │   │   ├── teacher/              ← Phúc
│   │   │   ├── verifier/             ← Phúc + Khang
│   │   │   ├── adaptive/             ← Khang
│   │   │   └── server.py             ← FastAPI entry point
│   │   ├── tests/
│   │   └── requirements.txt
│   │
│   └── data/                         ← Scraping & seed data (Nhật Huy phụ trách)
│       ├── scrapers/
│       ├── knowledge_graph/
│       └── exam_bank/
│
├── infra/
│   ├── docker-compose.yml            ← Chạy local toàn bộ hệ thống
│   └── docker-compose.gpu.yml        ← Chạy trên GPU server
│
├── .env                              ← Biến môi trường (KHÔNG commit)
├── .gitignore
└── README.md
```

**Quy ước:**
- Mỗi người **chỉ** làm việc trong folder mình phụ trách. Nếu cần sửa code ở folder khác, **ping người phụ trách trước**.
- Folder `common/` trong agents là code dùng chung — thay đổi ở đây **cần báo cả Khang và Phúc**.

---

## 3. Những thứ phải thống nhất TRƯỚC KHI code

### 3.1. Giao thức giao tiếp: NestJS API ↔ Agent Service

Đây là **điểm kết nối quan trọng nhất**. Nguyên Huy (backend) gọi Khang/Phúc (agents) qua HTTP. Cả hai bên phải đồng ý format request/response.

**Agent Service chỉ expose 3 endpoint:**

#### `POST /api/agents/dispatch` — Endpoint chính, xử lý mọi loại yêu cầu

```json
// REQUEST (NestJS gửi đi)
{
  "student_id": "uuid-cua-student",
  "intent": "GRADE_SUBMISSION",          // Một trong 6 giá trị bên dưới
  "user_message": "Chấm bài cho tôi",    // Tin nhắn gốc của user
  "session_id": "uuid-cua-session",       // Nếu đang trong phiên thi
  "file_urls": ["/uploads/abc123.png"],   // Đường dẫn file đã upload (nếu có)
  "metadata": {                           // Dữ liệu bổ sung tùy intent
    "subject": "math",
    "exam_type": "THPTQG",
    "student_answers": {"q1": "A", "q2": "B"}
  }
}

// RESPONSE (Agent Service trả về)
{
  "task_id": "uuid",
  "status": "success",                    // "success" | "error"
  "result": { ... },                      // Kết quả chi tiết (tùy intent)
  "agent_trail": ["manager", "parser", "teacher", "verifier"]  // Audit trail
}
```

#### 6 giá trị `intent` hợp lệ — cả 2 bên phải dùng chính xác:

| intent | Khi nào NestJS gửi | Agent Service làm gì |
|--------|--------------------|-----------------------|
| `EXAM_PRACTICE` | User bấm "Bắt đầu làm bài" | Adaptive chọn đề → trả exam data |
| `GRADE_SUBMISSION` | User nộp bài (answers hoặc file) | Parser → Teacher → Verifier → Adaptive |
| `VIEW_ANALYSIS` | User xem phân tích năng lực | Adaptive trả profile |
| `ASK_HINT` | User xin gợi ý | Teacher trả hint |
| `REVIEW_MISTAKE` | User xem lại lỗi sai | Adaptive trả lịch sử lỗi |
| `UNKNOWN` | Không phân loại được | Manager hỏi lại |

#### `POST /api/agents/parse` — Upload file để parse riêng (nếu cần)

```json
// Gửi multipart/form-data với field "file" và "metadata"
// Trả về exam JSON đã được OCR
```

#### `GET /health` — Kiểm tra service còn sống không

```json
{"status": "ok"}
```

---

### 3.2. Cấu trúc dữ liệu exam — AI Core và Fullstack phải dùng chung

Đây là format JSON mà **Parser Agent trả ra**, **Teacher Agent nhận vào**, **NestJS lưu DB**, **Frontend render**. Tất cả phải hiểu cùng một cấu trúc.

```json
{
  "exam_id": "uuid",
  "source": "image",
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

**Quy ước tên `topic_tags`:** Dùng format `{subject}.{grade}.{chapter_code}.{topic_code}` (ví dụ: `math.12.ch2.integrals`). Nhật Huy định nghĩa danh sách chính thức trong Knowledge Graph, Phúc/Khang dùng đúng danh sách đó.

---

### 3.3. Cấu trúc Evaluation — Teacher trả ra, Verifier kiểm tra, Frontend hiển thị

```json
{
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
      "reasoning": "Đáp án đúng. Nguyên hàm F(x) = x² + x + C"
    },
    {
      "question_id": "q41",
      "student_answer": "...",
      "is_correct": false,
      "score": 0.5,
      "max_score": 1.0,
      "reasoning": "Học sinh xác định đúng hình chiếu H nhưng tính sai khoảng cách...",
      "error_analysis": {
        "error_type": "CALCULATION_ERROR",
        "root_cause": "Áp dụng sai định lý Pythagore 3D",
        "knowledge_component": "math.12.ch4.solid_geometry",
        "remedial": "Ôn lại: Khoảng cách từ điểm đến mặt phẳng"
      }
    }
  ],
  "overall_analysis": {
    "strengths": ["math.12.ch2.integrals", "math.12.ch1.derivatives"],
    "weaknesses": ["math.12.ch4.solid_geometry", "math.11.ch1.trig"]
  }
}
```

**5 loại error_type — cố định, không tự thêm:**

| error_type | Ý nghĩa |
|-----------|----------|
| `CONCEPT_GAP` | Hổng kiến thức nền tảng |
| `CALCULATION_ERROR` | Sai số tính toán |
| `INCOMPLETE_REASONING` | Thiếu bước trung gian |
| `MISINTERPRETATION` | Hiểu sai đề bài |
| `PRESENTATION_FLAW` | Trình bày không rõ ràng |

---

### 3.4. Database Schema — Nhật Huy thiết kế, Nguyên Huy implement bằng Prisma

Dưới đây là các bảng cần có. Nhật Huy thiết kế chi tiết, Nguyên Huy chuyển sang Prisma schema.

```
students
├── id (uuid, PK)
├── email (unique)
├── name
├── password_hash
├── grade (10 | 11 | 12)
├── created_at
└── updated_at

irt_profiles (1-1 với students)
├── id (uuid, PK)
├── student_id (FK → students, unique)
├── theta (float, default 0.0)         ← năng lực ước lượng IRT
├── theta_se (float, default 1.0)      ← sai số chuẩn
└── total_items (int, default 0)

mastery_scores (N records per student, mỗi KC một dòng)
├── id (uuid, PK)
├── student_id (FK → students)
├── knowledge_component (string)        ← ví dụ "math.12.ch2.integrals"
├── p_l (float, default 0.1)           ← P(L) trong BKT
├── total_attempts (int)
├── correct_attempts (int)
└── updated_at
    UNIQUE(student_id, knowledge_component)

exams
├── id (uuid, PK)
├── subject (string)
├── exam_type (string)                  ← "THPTQG", "V_ACT", "HSA"
├── year (int, nullable)
├── source (string, nullable)           ← "toanmath.com", "manual", etc.
├── total_questions (int)
├── duration (int, nullable)            ← phút
├── metadata (jsonb, nullable)
└── created_at

questions
├── id (uuid, PK)
├── exam_id (FK → exams)
├── question_index (int)
├── type (string)                       ← "multiple_choice" | "essay"
├── content (text)
├── content_latex (text, nullable)
├── options (jsonb, nullable)           ← ["A. ...", "B. ...", ...]
├── correct_answer (string, nullable)
├── has_image (boolean)
├── image_url (string, nullable)
├── difficulty_a (float, default 1.0)   ← IRT discrimination
├── difficulty_b (float, default 0.0)   ← IRT difficulty
├── topic_tags (text[])                 ← ["math.12.ch2.integrals"]
└── max_score (float)

exam_sessions
├── id (uuid, PK)
├── student_id (FK → students)
├── exam_id (FK → exams)
├── intent (string)                     ← "EXAM_PRACTICE" | "GRADE_SUBMISSION"
├── status (string)                     ← "IN_PROGRESS" | "SUBMITTED" | "GRADED"
├── started_at (timestamp)
├── submitted_at (timestamp, nullable)
├── total_score (float, nullable)
├── max_score (float, nullable)
├── confidence (float, nullable)
├── overall_analysis (jsonb, nullable)
└── uploaded_file_url (string, nullable)

student_responses
├── id (uuid, PK)
├── session_id (FK → exam_sessions)
├── question_id (FK → questions)
├── student_answer (text, nullable)
├── is_correct (boolean, nullable)
├── score (float, nullable)
├── max_score (float, nullable)
├── reasoning (text, nullable)
└── error_analysis (jsonb, nullable)

knowledge_nodes (Knowledge Graph)
├── id (uuid, PK)
├── subject (string)
├── grade (int)
├── chapter (string)
├── topic (string)
├── display_name (string)
├── prerequisites (text[])              ← danh sách ID của node tiên quyết
    UNIQUE(subject, grade, chapter, topic)

rubrics
├── id (uuid, PK)
├── exam_type (string)
├── subject (string)
├── content (jsonb)                     ← rubric chi tiết
    UNIQUE(exam_type, subject)
```

**Quan trọng:** Tất cả ID dùng UUID v4, không dùng auto-increment integer. Lý do: dữ liệu có thể sinh từ agent service trước khi lưu DB.

---

### 3.5. NestJS API Endpoints — Nguyên Huy implement, Frontend tự gọi

| Method | Path | Mô tả | Ai gọi |
|--------|------|--------|--------|
| `POST` | `/auth/register` | Đăng ký (email, name, password, grade) | Frontend |
| `POST` | `/auth/login` | Đăng nhập → trả JWT | Frontend |
| `GET` | `/exams` | Danh sách đề thi (filter: subject, type) | Frontend |
| `GET` | `/exams/:id` | Chi tiết đề thi + câu hỏi | Frontend |
| `POST` | `/exams/sessions` | Tạo phiên thi mới (studentId, examId) | Frontend |
| `POST` | `/exams/sessions/:id/submit` | Nộp bài + trigger chấm (gọi Agent Service) | Frontend |
| `GET` | `/exams/sessions/:id/results` | Kết quả chi tiết phiên thi | Frontend |
| `POST` | `/upload` | Upload file (ảnh/PDF) → trả file path | Frontend |
| `GET` | `/students/:id/profile` | Hồ sơ năng lực (mastery scores, IRT theta) | Frontend |
| `GET` | `/students/:id/history` | Lịch sử các phiên thi | Frontend |

**Auth:** Dùng JWT. Mọi endpoint trừ `/auth/*` đều yêu cầu header `Authorization: Bearer <token>`.

---

## 4. Luồng dữ liệu chính — Ai xử lý cái gì, theo thứ tự nào?

### 4.1. Luồng GRADE_SUBMISSION (User upload ảnh đề thi đã làm)

```
[User]                [Frontend]           [NestJS API]          [Agent Service]
  │                       │                     │                      │
  │── upload file ──────→ │                     │                      │
  │                       │── POST /upload ───→ │                      │
  │                       │←── file_path ──────│                      │
  │                       │                     │                      │
  │── bấm "Chấm bài" ──→│                     │                      │
  │                       │── POST /exams/     │                      │
  │                       │   sessions/:id/    │                      │
  │                       │   submit ────────→ │                      │
  │                       │                     │── POST /api/agents/ │
  │                       │                     │   dispatch ────────→│
  │                       │                     │                      │── Manager phân tích intent
  │                       │                     │                      │── Parser: OCR ảnh → JSON
  │                       │                     │                      │── Teacher: chấm bài
  │                       │                     │                      │── Verifier: kiểm tra chéo
  │                       │                     │                      │── Adaptive: cập nhật profile
  │                       │                     │←── evaluation ──────│
  │                       │                     │                      │
  │                       │                     │── lưu kết quả vào  │
  │                       │                     │   PostgreSQL         │
  │                       │←── session result ──│                      │
  │←── hiển thị kết quả ─│                     │                      │
```

### 4.2. Luồng EXAM_PRACTICE (User chọn đề thi và làm bài)

```
[User]                [Frontend]           [NestJS API]          [Agent Service]
  │                       │                     │                      │
  │── chọn đề thi ──────→│                     │                      │
  │                       │── GET /exams/:id ─→│                      │
  │                       │←── exam + questions─│                      │
  │                       │                     │                      │
  │                       │── POST /exams/     │                      │
  │                       │   sessions ───────→│                      │
  │                       │←── session_id ─────│                      │
  │                       │                     │                      │
  │── làm bài (timer) ──→│                     │                      │
  │── nộp bài ──────────→│                     │                      │
  │                       │── POST /exams/     │                      │
  │                       │   sessions/:id/    │                      │
  │                       │   submit ────────→ │                      │
  │                       │                     │── POST /api/agents/ │
  │                       │                     │   dispatch ────────→│
  │                       │                     │   (GRADE_SUBMISSION) │
  │                       │                     │                      │── Teacher chấm
  │                       │                     │                      │── Verifier kiểm tra
  │                       │                     │←── evaluation ──────│
  │                       │←── results ────────│                      │
  │←── kết quả chi tiết ─│                     │                      │
```

---

## 5. Phân công chi tiết — Ai làm gì, bắt đầu từ đâu?

### 🔵 Nguyên Huy (Fullstack) — Bắt đầu ngay

**Tuần 1 (Ngày 1-6): Backend + Frontend skeleton**

Thứ tự công việc:
1. **Khởi tạo NestJS project** trong `master/apps/api/`
   - Cài Prisma, viết schema theo mục 3.4 ở trên
   - Chạy `prisma migrate dev` để tạo DB
   - Tạo `PrismaService` và `PrismaModule` (global)

2. **Auth module** — Register + Login + JWT guard
   - Đây là thứ đầu tiên cần có, vì mọi API khác đều cần auth
   - Dùng `bcryptjs` để hash password, `@nestjs/jwt` để sign token

3. **Exam module** — CRUD đề thi + session management
   - `GET /exams`, `GET /exams/:id`, `POST /exams/sessions`
   - `POST /exams/sessions/:id/submit` — endpoint quan trọng nhất, nơi gọi Agent Service

4. **Upload module** — Nhận file, lưu local (MVP), trả path
   - Dùng `multer` qua `@nestjs/platform-express`

5. **Agent dispatch service** — Gọi Agent Service qua HTTP
   - Chỉ cần 1 service với 1 method `dispatch()` gọi `POST /api/agents/dispatch`
   - **QUAN TRỌNG:** Không cần chờ Agent Service hoàn thiện. Viết sẵn service, test bằng mock response.

**Tuần 2 (Ngày 7-12): Frontend**

6. **Khởi tạo Next.js project** trong `master/apps/web/`
   - Cài shadcn/ui, TailwindCSS, axios, react-query
   - Tạo API client (`lib/api.ts`) gọi NestJS API

7. **Trang login/register** — Form đơn giản, lưu JWT vào localStorage

8. **Trang dashboard** — Danh sách đề thi, 3 card action (luyện thi, nộp bài, phân tích)

9. **Trang exam room** — Đây là trang khó nhất:
   - Countdown timer (hết giờ → tự nộp)
   - Panel bên trái: danh sách câu hỏi (đánh dấu đã làm)
   - Nội dung câu hỏi + 4 đáp án click chọn
   - Nút "Nộp bài" → gọi API submit

10. **Trang kết quả** — Hiển thị điểm, từng câu đúng/sai, error analysis

11. **Trang upload** — Drag-and-drop file, gửi lên API

**Dependency:** Nguyên Huy **không bị block** bởi ai. Backend + Frontend có thể chạy độc lập. Dùng mock data / seed data để test trong khi chờ agent service.

---

### 🟣 Khang (AI Core 1, Leader) — Bắt đầu song song

**Ngày 1-2: Hạ tầng Agent Service**

1. **Setup GPU server** (nếu đã có) hoặc confirm Gemini API key hoạt động
   - Test thử gọi vLLM hoặc Gemini để đảm bảo model phản hồi được

2. **Viết `agents/src/common/`** — Code dùng chung:
   - `config.py` — URL + model ID cho từng agent
   - `llm_client.py` — Wrapper gọi LLM (OpenAI-compatible API cho vLLM, hoặc Google GenAI SDK cho Gemini)
   - `message.py` — Pydantic models cho `TaskRequest`, `TaskResponse`, `AgentMessage`, enum `Intent`
   - **Đây là code mà Phúc cũng sẽ dùng, nên phải viết xong trước khi Phúc bắt đầu agent.**

3. **Viết `agents/src/server.py`** — FastAPI app skeleton với endpoint `/api/agents/dispatch`

**Ngày 3-6: Manager Agent + Adaptive Agent**

4. **Manager Agent** (`agents/src/manager/`):
   - `intent.py` — Phân loại intent từ user message (regex trước, LLM sau)
   - `planner.py` — Xây DAG thực thi theo intent (bảng cứng, không cần AI)
   - `agent.py` — Nhận TaskRequest, phân loại intent, gọi các agent con theo thứ tự

5. **Adaptive Agent** (`agents/src/adaptive/`):
   - `bkt.py` — Bayesian Knowledge Tracing (4 tham số, update sau mỗi câu)
   - `irt.py` — Item Response Theory (ước lượng theta)
   - `cat.py` — Chọn câu hỏi tiếp theo (Maximum Fisher Information)
   - `agent.py` — Nhận evaluation, cập nhật profile học sinh

**Ngày 7-12: Tích hợp + sửa bug**

6. **Wire mọi agent lại** trong `server.py` — Manager gọi Parser → Teacher → Verifier → Adaptive
7. **Test E2E** — Gửi request thật, kiểm tra toàn bộ pipeline
8. **Tối ưu prompt** cho Manager (intent detection) và Adaptive (sinh lộ trình)

---

### 🟠 Phúc (AI Core 2) — Bắt đầu sau khi Khang viết xong `common/`

**Dependency:** Chờ Khang viết xong `common/llm_client.py` và `common/message.py` (khoảng ngày 2). Trong lúc chờ, có thể bắt đầu preprocessing (không cần LLM).

**Ngày 1-3: Parser Agent** (`agents/src/parser/`)

1. `preprocessing.py` — OpenCV: gray, denoise, deskew, enhance contrast
   - Nhận ảnh numpy → trả ảnh đã xử lý
   - Có thể bắt đầu **ngay ngày 1**, không cần chờ ai

2. `ocr.py` — PaddleOCR wrapper
   - Cài PaddleOCR + PaddlePaddle
   - Nhận ảnh → trả danh sách TextBlock (text + bbox + confidence)

3. `extractor.py` — Regex + logic tách câu hỏi
   - Nhận text thuần → trả list question dict
   - **Đây là phần khó nhất** của Parser vì đề thi Việt Nam format rất đa dạng

4. `agent.py` — Kết nối preprocessing → OCR → extraction

**Ngày 4-7: Teacher Agent** (`agents/src/teacher/`)

5. `grading.py` — Logic chấm theo loại câu hỏi:
   - Trắc nghiệm: exact match (không cần LLM)
   - Tự luận: gọi LLM với prompt + rubric + đáp án
   - Tính toán: gọi Grading Engine (SymPy)

6. `error_analysis.py` — Phân loại lỗi (5 loại cố định)

7. `agent.py` — Nhận exam_data + student_answers → trả evaluation

**Ngày 7-9: Verifier Agent** (`agents/src/verifier/`)

8. `discrepancy.py` — So sánh teacher_eval vs verifier_eval, tìm bất đồng
9. `debate.py` — Logic phản biện: max 3 rounds, evidence-based
10. `agent.py` — Nhận teacher_draft → chấm độc lập → debate → trả final evaluation

**Ngày 7 (song song): Grading Engine** (`master/apps/grading-engine/`)

11. `sympy_grader.py` — Verify biểu thức toán bằng SymPy
12. `main.py` — FastAPI endpoint `/verify/math` và `/verify/numeric`

---

### 🟢 Nhật Huy (Data Engineer) — Bắt đầu ngay

**Ngày 1-3: Database + Seed Data**

1. **Thiết kế chi tiết DB schema** — Review bảng ở mục 3.4, thêm index, constraints
   - Gửi cho Nguyên Huy để implement bằng Prisma
   - **QUAN TRỌNG:** Schema phải xong trong ngày 1 để Nguyên Huy migrate ngay

2. **Viết Knowledge Graph** — File JSON chứa cây kiến thức Toán 10-12
   - Format: `{subject, nodes: [{id, grade, chapter, topic, display_name, prerequisites}]}`
   - ID theo quy ước: `math.12.ch2.integrals`
   - Bao gồm prerequisites (topic nào cần học trước topic nào)

3. **Viết rubric templates** — JSON cho từng loại đề (THPTQG, V-ACT)
   - Bao gồm: cách tính điểm, điểm mỗi câu, thời gian, section breakdown

4. **Seed data script** — Script Python load KG + rubrics + sample exam vào PostgreSQL

**Ngày 3-6: Scraping Pipeline**

5. **Scraper cho toanmath.com** — Crawl danh sách đề, parse câu hỏi
6. **Scraper cho vietjack.com** — Tương tự
7. **Post-processing** — Clean data, chuẩn hóa format, gán topic_tags
8. **Load vào DB** — Script để insert exams + questions vào PostgreSQL

**Ngày 7-12: Data Quality + RAG**

9. **Verify data quality** — Kiểm tra số lượng, format, missing fields
10. **Thêm đề thi thủ công** (nếu scraper không đủ) — Ít nhất 20 đề Toán THPTQG
11. **Hỗ trợ tích hợp** — Fix data format mismatches khi agents consume data

---

## 6. Quy ước kỹ thuật — Thống nhất toàn team

### 6.1. Git workflow

```
main                    ← code đã review, hoạt động được
├── feat/api-auth       ← Nguyên Huy: module auth
├── feat/parser-ocr     ← Phúc: parser agent
├── feat/manager-agent  ← Khang: manager agent
└── feat/data-scraper   ← Nhật Huy: scraper
```

- Mỗi feature một branch. Tên branch: `feat/<tên-ngắn>` hoặc `fix/<tên-ngắn>`.
- **Không push thẳng vào `main`**. Tạo PR, ít nhất 1 người review (Leader review).
- Commit message tiếng Anh, format: `feat(module): mô tả ngắn` hoặc `fix(module): mô tả ngắn`.

### 6.2. Chạy local

Tất cả dùng Docker Compose để chạy local:

```bash
# Chạy PostgreSQL + toàn bộ services
docker compose up -d

# Hoặc chạy riêng từng service (cho dev)
docker compose up postgres -d          # DB luôn chạy
cd master/apps/api && npm run start:dev      # NestJS ở port 3001
cd master/apps/web && npm run dev            # Next.js ở port 3000
cd master/agents && uvicorn src.server:app --reload --port 8000  # Agents ở port 8000
```

### 6.3. Biến môi trường (`.env`)

```bash
# Database
DATABASE_URL=postgresql://master:master_dev_pw@localhost:5432/master_db

# JWT
JWT_SECRET=hackathon-dev-secret

# Agent Service
AGENT_SERVICE_URL=http://localhost:8000

# Grading Engine
GRADING_ENGINE_URL=http://localhost:8001

# LLM — Dùng 1 trong 2 cách:
# Cách 1: vLLM trên GPU server
VLLM_MANAGER_URL=http://gpu-server:8080/v1
VLLM_TEACHER_URL=http://gpu-server:8081/v1
VLLM_VERIFIER_URL=http://gpu-server:8082/v1

# Cách 2: Gemini API (fallback nếu chưa có GPU)
GEMINI_API_KEY=<key>
USE_GEMINI_FALLBACK=true
```

### 6.4. Test

- **Python (agents, grading-engine, data):** `pytest`
- **NestJS:** `npm run test` (unit) và `npm run test:e2e` (integration)
- Mỗi module mới phải có ít nhất 1 test file.
- Test **không cần** gọi LLM thật. Mock LLM response trong test.

---

## 7. Rủi ro và Fallback

| Rủi ro | Xác suất | Fallback |
|--------|---------|----------|
| GPU server chưa sẵn sàng | Cao | Dùng Gemini 2.5 Flash API cho **tất cả** agents (đã có key) |
| PaddleOCR accuracy thấp | Trung bình | Dùng Gemini Vision API để OCR thay PaddleOCR |
| Scraper bị block | Trung bình | Nhập đề thi thủ công (PDF → text), tối thiểu 20 đề |
| LLM chấm tự luận không ổn | Cao | MVP chỉ support trắc nghiệm (exact match, không cần LLM). Tự luận là bonus |
| NestJS ↔ Agent Service lỗi format | Trung bình | Dùng đúng JSON schema ở mục 3 — nếu lỗi, fix schema chứ không fix code |

---

## 8. Checklist ngày đầu tiên — Ai cũng phải làm xong

- [ ] **Tất cả:** Clone repo, chạy `docker compose up postgres -d`, confirm DB kết nối được
- [ ] **Nhật Huy:** Gửi file DB schema chi tiết (bảng, column, type, constraint) cho Nguyên Huy
- [ ] **Nguyên Huy:** Init NestJS project, cài Prisma, viết schema.prisma, chạy migration
- [ ] **Khang:** Viết xong `common/config.py`, `common/llm_client.py`, `common/message.py`, push lên
- [ ] **Phúc:** Cài PaddleOCR, test thử OCR 1 ảnh đề thi Toán, confirm output
- [ ] **Tất cả:** Mỗi người tạo branch riêng, push 1 commit đầu tiên

---

## 9. Lịch họp sync

| Khi nào | Nội dung | Thời lượng |
|---------|----------|------------|
| Mỗi sáng 9:00 | Standup: hôm qua làm gì, hôm nay làm gì, bị block gì | 10 phút |
| Ngày 4 (sau 3 ngày) | Demo nội bộ: mỗi người show cái đã làm, test integration lần 1 | 30 phút |
| Ngày 8 | Integration test: chạy full flow GRADE_SUBMISSION lần đầu | 1 giờ |
| Ngày 10 | Feature freeze: không thêm tính năng, chỉ fix bug | - |
| Ngày 11-12 | Demo rehearsal: chạy demo script, fix UI, chuẩn bị thuyết trình | - |
