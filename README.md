# MASTER - Multi-Agent System for Teaching, Evaluating & Reviewing

**MASTER** is an advanced EdTech platform fully powered by a **Multi-Agent System (MAS)**, specifically designed to help high school students optimize their learning and exam preparation process for various examinations (e.g. HSA, TSA, THPTQG, ...).

## Folder Structure
```bash
GDGoC_HackathonVietnam/
├── master/
│   ├── apps/
│   │   ├── api/                      ← NestJS backend     
│   │   ├── web/                      ← Next.js frontend   
│   │   └── grading-engine/           ← SymPy microservice 
│   │
│   ├── agents/                       ← Python agent service 
│   │   ├── common/               ← Code for all agents
│   │   ├── manager/              
│   │   ├── parser/               
│   │   ├── teacher/              
│   │   ├── verifier/             
│   │   ├── adaptive/             
│   │   ├── server.py             ← FastAPI entry point
│   │   └── requirements.txt
│   │
│   │── data/                         ← Scraping & seed data 
│   │   ├── scrapers/
│   │   ├── knowledge_graph/
│   │   └── exam_bank/
│   │
│   │── test/
│   │
│   ├── docker-compose.yml            ← For Local
│   └── docker-compose.gpu.yml        ← For GPU server
│                       
├── .gitignore
└── README.md
```

## Architecture
### NestJS API and Agent Service Communication
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

## Agents Architecture