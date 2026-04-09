# Module D: Data Engineering — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the knowledge graph (Math 10-12), exam bank with rubric templates, scrapers for toanmath.com and vietjack.com, seed script for MongoDB, and Docker Compose infrastructure.

**Architecture:** JSON-based knowledge graph representing the Math curriculum tree with prerequisite relationships. Scrapers produce exam JSON conforming to the canonical ExamData schema. A Python seed script loads everything into MongoDB.

**Tech Stack:** Python 3.11+, MongoDB, Docker Compose, requests, BeautifulSoup4

**Owner:** Nhật Huy (Data Engineer)

**Dependency:** None — can start immediately. DB schema decisions inform Nguyên Huy's Mongoose schemas.

---

## File Structure

```
master/data/
├── knowledge_graph/
│   └── math_10_12.json             ← Full Math curriculum tree
├── exam_bank/
│   ├── rubrics/
│   │   ├── thptqg_math.json        ← THPTQG scoring rubric
│   │   └── v_act_math.json         ← V-ACT scoring rubric
│   └── samples/
│       ├── thptqg_2025_math_01.json
│       └── thptqg_2025_math_02.json
├── scrapers/
│   ├── requirements.txt
│   ├── toanmath_scraper.py
│   ├── vietjack_scraper.py
│   └── post_processor.py
└── seed.py                          ← Load all data into MongoDB

infra/
├── docker-compose.yml               ← MongoDB + mongo-express
├── docker-compose.gpu.yml           ← vLLM instances (reference)
└── mongo-init.js                    ← DB initialization
```

---

## Chunk 1: Infrastructure + Knowledge Graph

### Task 1: Docker Compose for MongoDB

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `infra/mongo-init.js`

- [ ] **Step 1: Write docker-compose.yml**

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
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh --quiet
      interval: 10s
      timeout: 5s
      retries: 5

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
      mongodb:
        condition: service_healthy

volumes:
  mongodb_data:
```

- [ ] **Step 2: Write mongo-init.js**

```javascript
// infra/mongo-init.js
db = db.getSiblingDB('master_db');

db.createCollection('students');
db.createCollection('exams');
db.createCollection('exam_sessions');
db.createCollection('knowledge_nodes');
db.createCollection('rubrics');

db.students.createIndex({ "email": 1 }, { unique: true });
db.exams.createIndex({ "subject": 1, "exam_type": 1 });
db.exam_sessions.createIndex({ "student_id": 1, "status": 1 });
db.exam_sessions.createIndex({ "student_id": 1, "created_at": -1 });
db.knowledge_nodes.createIndex({ "node_id": 1 }, { unique: true });
db.rubrics.createIndex({ "exam_type": 1, "subject": 1 }, { unique: true });

print("✅ master_db initialized with collections and indexes");
```

- [ ] **Step 3: Test MongoDB starts**

Run:
```bash
cd infra
docker compose up -d
docker compose logs mongodb
```

Expected: MongoDB starts, logs show "master_db initialized".

Test connection:
```bash
mongosh "mongodb://master:master_dev_pw@localhost:27017/master_db?authSource=admin" --eval "db.stats()"
```

- [ ] **Step 4: Commit**

```bash
git add infra/
git commit -m "feat(infra): add Docker Compose with MongoDB 7 + mongo-express"
```

---

### Task 2: Knowledge Graph — Math 10-12

**Files:**
- Create: `master/data/knowledge_graph/math_10_12.json`

- [ ] **Step 1: Write the knowledge graph**

This is the **official** topic tag registry. All agents MUST use tags from this list.

```json
{
  "subject": "math",
  "version": "1.0",
  "description": "Cây kiến thức Toán THPT lớp 10-12 theo chương trình 2018",
  "nodes": [
    {
      "node_id": "math.10.ch1.sets",
      "subject": "math",
      "grade": 10,
      "chapter": "ch1",
      "topic": "sets",
      "display_name": "Mệnh đề - Tập hợp",
      "prerequisites": []
    },
    {
      "node_id": "math.10.ch2.functions",
      "subject": "math",
      "grade": 10,
      "chapter": "ch2",
      "topic": "functions",
      "display_name": "Hàm số bậc hai",
      "prerequisites": ["math.10.ch1.sets"]
    },
    {
      "node_id": "math.10.ch3.equations",
      "subject": "math",
      "grade": 10,
      "chapter": "ch3",
      "topic": "equations",
      "display_name": "Phương trình - Hệ phương trình",
      "prerequisites": ["math.10.ch2.functions"]
    },
    {
      "node_id": "math.10.ch4.inequalities",
      "subject": "math",
      "grade": 10,
      "chapter": "ch4",
      "topic": "inequalities",
      "display_name": "Bất đẳng thức - Bất phương trình",
      "prerequisites": ["math.10.ch3.equations"]
    },
    {
      "node_id": "math.10.ch5.trig_basic",
      "subject": "math",
      "grade": 10,
      "chapter": "ch5",
      "topic": "trig_basic",
      "display_name": "Hệ thức lượng trong tam giác",
      "prerequisites": []
    },
    {
      "node_id": "math.10.ch6.statistics",
      "subject": "math",
      "grade": 10,
      "chapter": "ch6",
      "topic": "statistics",
      "display_name": "Thống kê",
      "prerequisites": []
    },
    {
      "node_id": "math.10.ch7.vectors",
      "subject": "math",
      "grade": 10,
      "chapter": "ch7",
      "topic": "vectors",
      "display_name": "Vectơ",
      "prerequisites": []
    },
    {
      "node_id": "math.10.ch8.coordinate_geometry",
      "subject": "math",
      "grade": 10,
      "chapter": "ch8",
      "topic": "coordinate_geometry",
      "display_name": "Phương pháp tọa độ trong mặt phẳng",
      "prerequisites": ["math.10.ch7.vectors"]
    },
    {
      "node_id": "math.11.ch1.trig",
      "subject": "math",
      "grade": 11,
      "chapter": "ch1",
      "topic": "trig",
      "display_name": "Lượng giác",
      "prerequisites": ["math.10.ch5.trig_basic"]
    },
    {
      "node_id": "math.11.ch2.combinatorics",
      "subject": "math",
      "grade": 11,
      "chapter": "ch2",
      "topic": "combinatorics",
      "display_name": "Tổ hợp - Xác suất",
      "prerequisites": ["math.10.ch1.sets"]
    },
    {
      "node_id": "math.11.ch3.sequences",
      "subject": "math",
      "grade": 11,
      "chapter": "ch3",
      "topic": "sequences",
      "display_name": "Dãy số - Cấp số cộng - Cấp số nhân",
      "prerequisites": ["math.10.ch2.functions"]
    },
    {
      "node_id": "math.11.ch4.limits",
      "subject": "math",
      "grade": 11,
      "chapter": "ch4",
      "topic": "limits",
      "display_name": "Giới hạn",
      "prerequisites": ["math.11.ch3.sequences"]
    },
    {
      "node_id": "math.11.ch5.derivatives_intro",
      "subject": "math",
      "grade": 11,
      "chapter": "ch5",
      "topic": "derivatives_intro",
      "display_name": "Đạo hàm (nhập môn)",
      "prerequisites": ["math.11.ch4.limits"]
    },
    {
      "node_id": "math.11.ch6.solid_geometry_intro",
      "subject": "math",
      "grade": 11,
      "chapter": "ch6",
      "topic": "solid_geometry_intro",
      "display_name": "Hình học không gian (đường thẳng, mặt phẳng)",
      "prerequisites": ["math.10.ch7.vectors"]
    },
    {
      "node_id": "math.12.ch1.derivatives",
      "subject": "math",
      "grade": 12,
      "chapter": "ch1",
      "topic": "derivatives",
      "display_name": "Ứng dụng đạo hàm",
      "prerequisites": ["math.11.ch5.derivatives_intro"]
    },
    {
      "node_id": "math.12.ch1.exponential_log",
      "subject": "math",
      "grade": 12,
      "chapter": "ch1",
      "topic": "exponential_log",
      "display_name": "Hàm số mũ - Hàm số logarit",
      "prerequisites": ["math.12.ch1.derivatives"]
    },
    {
      "node_id": "math.12.ch2.integrals",
      "subject": "math",
      "grade": 12,
      "chapter": "ch2",
      "topic": "integrals",
      "display_name": "Nguyên hàm - Tích phân",
      "prerequisites": ["math.12.ch1.derivatives"]
    },
    {
      "node_id": "math.12.ch3.complex_numbers",
      "subject": "math",
      "grade": 12,
      "chapter": "ch3",
      "topic": "complex_numbers",
      "display_name": "Số phức",
      "prerequisites": ["math.10.ch3.equations"]
    },
    {
      "node_id": "math.12.ch4.solid_geometry",
      "subject": "math",
      "grade": 12,
      "chapter": "ch4",
      "topic": "solid_geometry",
      "display_name": "Khối đa diện - Khối tròn xoay",
      "prerequisites": ["math.11.ch6.solid_geometry_intro", "math.12.ch2.integrals"]
    },
    {
      "node_id": "math.12.ch5.coordinate_3d",
      "subject": "math",
      "grade": 12,
      "chapter": "ch5",
      "topic": "coordinate_3d",
      "display_name": "Phương pháp tọa độ trong không gian",
      "prerequisites": ["math.10.ch8.coordinate_geometry", "math.11.ch6.solid_geometry_intro"]
    },
    {
      "node_id": "math.12.ch6.probability",
      "subject": "math",
      "grade": 12,
      "chapter": "ch6",
      "topic": "probability",
      "display_name": "Xác suất nâng cao",
      "prerequisites": ["math.11.ch2.combinatorics"]
    }
  ]
}
```

> This covers the core Math curriculum for THPT (2018 program). Nhật Huy should expand with sub-topics as data becomes available.

- [ ] **Step 2: Commit**

```bash
git add master/data/knowledge_graph/
git commit -m "feat(data): add Math 10-12 knowledge graph with 21 topic nodes"
```

---

### Task 3: Rubric Templates

**Files:**
- Create: `master/data/exam_bank/rubrics/thptqg_math.json`
- Create: `master/data/exam_bank/rubrics/v_act_math.json`

- [ ] **Step 1: Write THPTQG Math rubric**

```json
{
  "exam_type": "THPTQG",
  "subject": "math",
  "description": "Cấu trúc đề thi tốt nghiệp THPT Quốc gia môn Toán",
  "duration_minutes": 90,
  "scoring": {
    "total_questions": 50,
    "multiple_choice": {
      "count": 50,
      "points_each": 0.2,
      "total": 10.0
    }
  },
  "difficulty_distribution": {
    "easy": { "range": [1, 20], "description": "Nhận biết" },
    "medium": { "range": [21, 35], "description": "Thông hiểu" },
    "hard": { "range": [36, 45], "description": "Vận dụng" },
    "very_hard": { "range": [46, 50], "description": "Vận dụng cao" }
  },
  "topic_distribution": {
    "math.12.ch1.derivatives": 5,
    "math.12.ch1.exponential_log": 5,
    "math.12.ch2.integrals": 5,
    "math.12.ch3.complex_numbers": 3,
    "math.12.ch4.solid_geometry": 5,
    "math.12.ch5.coordinate_3d": 5,
    "math.12.ch6.probability": 3,
    "math.11.ch1.trig": 4,
    "math.11.ch2.combinatorics": 3,
    "math.11.ch3.sequences": 3,
    "math.10.ch3.equations": 3,
    "math.10.ch4.inequalities": 3,
    "math.10.ch8.coordinate_geometry": 3
  }
}
```

- [ ] **Step 2: Write V-ACT Math rubric**

```json
{
  "exam_type": "V_ACT",
  "subject": "math",
  "description": "Cấu trúc đề thi Đánh giá năng lực ĐHQG (V-ACT) phần Toán",
  "duration_minutes": 150,
  "scoring": {
    "math_section": {
      "total_questions": 50,
      "multiple_choice": { "count": 50, "points_each": 1, "total": 50 }
    }
  },
  "difficulty_distribution": {
    "easy": { "range": [1, 15], "description": "Cơ bản" },
    "medium": { "range": [16, 35], "description": "Trung bình" },
    "hard": { "range": [36, 50], "description": "Nâng cao" }
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add master/data/exam_bank/rubrics/
git commit -m "feat(data): add THPTQG and V-ACT rubric templates"
```

---

### Task 4: Sample Exam Data

**Files:**
- Create: `master/data/exam_bank/samples/thptqg_2025_math_01.json`

- [ ] **Step 1: Write sample exam (first 10 questions as example)**

```json
{
  "exam_id": "sample-thptqg-2025-01",
  "source": "manual",
  "subject": "math",
  "exam_type": "THPTQG",
  "year": 2025,
  "total_questions": 10,
  "duration_minutes": 90,
  "sections": [
    {
      "type": "multiple_choice",
      "questions": [
        {
          "id": "q1",
          "question_index": 1,
          "type": "multiple_choice",
          "content": "Tìm nguyên hàm của hàm số f(x) = 2x + 1",
          "content_latex": "\\text{Tìm nguyên hàm của hàm số } f(x) = 2x + 1",
          "options": [
            "A. F(x) = x² + x + C",
            "B. F(x) = x² + C",
            "C. F(x) = 2x² + x + C",
            "D. F(x) = x + C"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -1.5,
          "topic_tags": ["math.12.ch2.integrals"],
          "max_score": 0.2
        },
        {
          "id": "q2",
          "question_index": 2,
          "type": "multiple_choice",
          "content": "Số phức liên hợp của z = 3 + 4i là",
          "content_latex": "\\text{Số phức liên hợp của } z = 3 + 4i \\text{ là}",
          "options": [
            "A. 3 - 4i",
            "B. -3 + 4i",
            "C. -3 - 4i",
            "D. 4 + 3i"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -2.0,
          "topic_tags": ["math.12.ch3.complex_numbers"],
          "max_score": 0.2
        },
        {
          "id": "q3",
          "question_index": 3,
          "type": "multiple_choice",
          "content": "Cho hàm số y = x³ - 3x + 2. Giá trị cực đại của hàm số là",
          "options": [
            "A. 4",
            "B. 0",
            "C. 2",
            "D. -2"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.2,
          "difficulty_b": -0.5,
          "topic_tags": ["math.12.ch1.derivatives"],
          "max_score": 0.2
        },
        {
          "id": "q4",
          "question_index": 4,
          "type": "multiple_choice",
          "content": "Tính tích phân I = ∫₀¹ (2x + 1)dx",
          "content_latex": "I = \\int_0^1 (2x + 1)\\,dx",
          "options": [
            "A. 2",
            "B. 1",
            "C. 3",
            "D. 0"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -1.0,
          "topic_tags": ["math.12.ch2.integrals"],
          "max_score": 0.2
        },
        {
          "id": "q5",
          "question_index": 5,
          "type": "multiple_choice",
          "content": "Cho log₂(x) = 3. Giá trị của x là",
          "options": [
            "A. 8",
            "B. 6",
            "C. 9",
            "D. 3"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -1.5,
          "topic_tags": ["math.12.ch1.exponential_log"],
          "max_score": 0.2
        },
        {
          "id": "q6",
          "question_index": 6,
          "type": "multiple_choice",
          "content": "Giải phương trình sin(x) = 1/2 trên [0, 2π)",
          "options": [
            "A. x = π/6, x = 5π/6",
            "B. x = π/3, x = 2π/3",
            "C. x = π/6",
            "D. x = π/3"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.1,
          "difficulty_b": -0.3,
          "topic_tags": ["math.11.ch1.trig"],
          "max_score": 0.2
        },
        {
          "id": "q7",
          "question_index": 7,
          "type": "multiple_choice",
          "content": "Tổ hợp C(5,2) bằng",
          "options": [
            "A. 10",
            "B. 20",
            "C. 5",
            "D. 25"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -2.0,
          "topic_tags": ["math.11.ch2.combinatorics"],
          "max_score": 0.2
        },
        {
          "id": "q8",
          "question_index": 8,
          "type": "multiple_choice",
          "content": "Cho cấp số cộng (uₙ) có u₁ = 2, d = 3. Tìm u₁₀",
          "options": [
            "A. 29",
            "B. 32",
            "C. 27",
            "D. 30"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -1.5,
          "topic_tags": ["math.11.ch3.sequences"],
          "max_score": 0.2
        },
        {
          "id": "q9",
          "question_index": 9,
          "type": "multiple_choice",
          "content": "Thể tích hình cầu bán kính R = 3 là",
          "options": [
            "A. 36π",
            "B. 27π",
            "C. 108π",
            "D. 12π"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.0,
          "difficulty_b": -1.0,
          "topic_tags": ["math.12.ch4.solid_geometry"],
          "max_score": 0.2
        },
        {
          "id": "q10",
          "question_index": 10,
          "type": "multiple_choice",
          "content": "Trong không gian Oxyz, khoảng cách từ điểm M(1,2,3) đến mặt phẳng (P): x + 2y + 2z - 3 = 0 là",
          "options": [
            "A. 2",
            "B. 3",
            "C. 1",
            "D. 4"
          ],
          "correct_answer": "A",
          "has_image": false,
          "difficulty_a": 1.3,
          "difficulty_b": 0.5,
          "topic_tags": ["math.12.ch5.coordinate_3d"],
          "max_score": 0.2
        }
      ]
    }
  ],
  "metadata": {
    "note": "Sample exam for development/testing. First 10 questions only."
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add master/data/exam_bank/samples/
git commit -m "feat(data): add sample THPTQG 2025 Math exam (10 questions)"
```

---

## Chunk 2: Seed Script + Scrapers

### Task 5: MongoDB Seed Script

**Files:**
- Create: `master/data/seed.py`

- [ ] **Step 1: Write seed script**

```python
# master/data/seed.py
"""Seed MongoDB with knowledge graph, rubrics, and sample exams."""

import json
import sys
from pathlib import Path

from pymongo import MongoClient

MONGO_URI = "mongodb://master:master_dev_pw@localhost:27017/master_db?authSource=admin"
DATA_DIR = Path(__file__).parent


def seed_knowledge_graph(db):
    kg_path = DATA_DIR / "knowledge_graph" / "math_10_12.json"
    with open(kg_path) as f:
        kg = json.load(f)

    nodes = kg["nodes"]
    db.knowledge_nodes.delete_many({})

    for node in nodes:
        db.knowledge_nodes.update_one(
            {"node_id": node["node_id"]},
            {"$set": node},
            upsert=True,
        )
    print(f"✅ Seeded {len(nodes)} knowledge nodes")


def seed_rubrics(db):
    rubrics_dir = DATA_DIR / "exam_bank" / "rubrics"
    db.rubrics.delete_many({})

    count = 0
    for path in rubrics_dir.glob("*.json"):
        with open(path) as f:
            rubric = json.load(f)
        db.rubrics.update_one(
            {"exam_type": rubric["exam_type"], "subject": rubric["subject"]},
            {"$set": rubric},
            upsert=True,
        )
        count += 1
    print(f"✅ Seeded {count} rubrics")


def seed_exams(db):
    samples_dir = DATA_DIR / "exam_bank" / "samples"

    count = 0
    for path in samples_dir.glob("*.json"):
        with open(path) as f:
            exam = json.load(f)
        db.exams.update_one(
            {"exam_id": exam.get("exam_id", path.stem)},
            {"$set": exam},
            upsert=True,
        )
        count += 1
    print(f"✅ Seeded {count} exams")


def main():
    uri = sys.argv[1] if len(sys.argv) > 1 else MONGO_URI
    client = MongoClient(uri)
    db = client.get_default_database()

    print(f"Seeding database: {db.name}")
    seed_knowledge_graph(db)
    seed_rubrics(db)
    seed_exams(db)
    print("🎉 All data seeded successfully!")

    client.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test seed script**

Run:
```bash
cd infra && docker compose up -d
cd ../master/data
pip install pymongo
python seed.py
```

Expected:
```
Seeding database: master_db
✅ Seeded 21 knowledge nodes
✅ Seeded 2 rubrics
✅ Seeded 1 exams
🎉 All data seeded successfully!
```

- [ ] **Step 3: Commit**

```bash
git add master/data/seed.py
git commit -m "feat(data): add MongoDB seed script for knowledge graph, rubrics, exams"
```

---

### Task 6: Toanmath.com Scraper

**Files:**
- Create: `master/data/scrapers/requirements.txt`
- Create: `master/data/scrapers/toanmath_scraper.py`

- [ ] **Step 1: Write scraper dependencies**

```txt
# master/data/scrapers/requirements.txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
pymongo>=4.7.0
```

- [ ] **Step 2: Write scraper**

```python
# master/data/scrapers/toanmath_scraper.py
"""Scraper for toanmath.com exam pages.

Usage: python toanmath_scraper.py --output ../exam_bank/scraped/
"""

import argparse
import json
import logging
import re
import time
import uuid
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://toanmath.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MASTER-Bot/1.0; educational research)"
}
DELAY = 2  # seconds between requests


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return None


def extract_exam_links(index_url: str) -> list[str]:
    """Extract exam page URLs from a listing page."""
    soup = fetch_page(index_url)
    if not soup:
        return []

    links = []
    for a in soup.select("article a[href]"):
        href = a["href"]
        if "de-thi" in href or "kiem-tra" in href:
            if href.startswith("/"):
                href = BASE_URL + href
            links.append(href)

    return list(set(links))


def parse_exam_page(url: str) -> dict | None:
    """Parse a single exam page into canonical ExamData format."""
    soup = fetch_page(url)
    if not soup:
        return None

    content = soup.select_one("article .entry-content, .post-content, main")
    if not content:
        return None

    text = content.get_text(separator="\n")

    # Basic question extraction (will be refined by post_processor.py)
    questions = []
    q_pattern = re.compile(r"Câu\s+(\d+)[.:]?\s*(.*?)(?=Câu\s+\d+[.:]|\Z)", re.DOTALL)
    for match in q_pattern.finditer(text):
        q_idx = int(match.group(1))
        body = match.group(2).strip()

        options = []
        opt_pattern = re.compile(r"([A-D])[.)]\s*(.*?)(?=[A-D][.)]|\Z)", re.DOTALL)
        opt_matches = opt_pattern.findall(body)

        if opt_matches:
            q_content = body[:body.find(opt_matches[0][0])].strip()
            options = [f"{letter}. {text.strip()}" for letter, text in opt_matches]
            q_type = "multiple_choice"
        else:
            q_content = body
            q_type = "essay"

        questions.append({
            "id": f"q{q_idx}",
            "question_index": q_idx,
            "type": q_type,
            "content": q_content[:500],
            "options": options if options else None,
            "correct_answer": None,
            "has_image": False,
            "difficulty_a": 1.0,
            "difficulty_b": 0.0,
            "topic_tags": [],
            "max_score": 0.2 if q_type == "multiple_choice" else 1.0,
        })

    if not questions:
        return None

    return {
        "exam_id": str(uuid.uuid4()),
        "source": url,
        "subject": "math",
        "exam_type": "THPTQG",
        "total_questions": len(questions),
        "duration_minutes": 90,
        "sections": [
            {
                "type": "multiple_choice",
                "questions": [q for q in questions if q["type"] == "multiple_choice"],
            },
        ],
        "metadata": {"scraped_from": url},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-url", default=f"{BASE_URL}/de-thi-thpt-quoc-gia-mon-toan/")
    parser.add_argument("--output", default="../exam_bank/scraped/")
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching exam links from %s", args.index_url)
    links = extract_exam_links(args.index_url)
    logger.info("Found %d exam links", len(links))

    count = 0
    for url in links[:args.max_pages]:
        logger.info("Parsing: %s", url)
        exam = parse_exam_page(url)
        if exam and exam["total_questions"] > 0:
            fname = output_dir / f"toanmath_{count:03d}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(exam, f, ensure_ascii=False, indent=2)
            count += 1
            logger.info("  → Saved %d questions to %s", exam["total_questions"], fname)
        time.sleep(DELAY)

    logger.info("Done! Scraped %d exams.", count)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add master/data/scrapers/
git commit -m "feat(data): add toanmath.com scraper with question extraction"
```

---

### Task 7: Post-Processor (topic tag assignment)

**Files:**
- Create: `master/data/scrapers/post_processor.py`

- [ ] **Step 1: Write post-processor**

```python
# master/data/scrapers/post_processor.py
"""Post-process scraped exams: clean text, assign topic tags, validate format."""

import json
import re
from pathlib import Path

TOPIC_KEYWORDS = {
    "math.12.ch2.integrals": ["nguyên hàm", "tích phân", "∫", "integral"],
    "math.12.ch1.derivatives": ["đạo hàm", "cực trị", "cực đại", "cực tiểu", "tiếp tuyến"],
    "math.12.ch1.exponential_log": ["logarit", "mũ", "log", "ln", "e^"],
    "math.12.ch3.complex_numbers": ["số phức", "phần thực", "phần ảo", "liên hợp"],
    "math.12.ch4.solid_geometry": ["hình chóp", "lăng trụ", "hình cầu", "thể tích", "khối"],
    "math.12.ch5.coordinate_3d": ["oxyz", "mặt phẳng", "đường thẳng", "khoảng cách"],
    "math.11.ch1.trig": ["sin", "cos", "tan", "lượng giác", "cot"],
    "math.11.ch2.combinatorics": ["tổ hợp", "chỉnh hợp", "hoán vị", "xác suất", "C("],
    "math.11.ch3.sequences": ["cấp số", "dãy số", "u_n", "số hạng"],
    "math.10.ch3.equations": ["phương trình", "nghiệm", "giải"],
    "math.10.ch4.inequalities": ["bất phương trình", "bất đẳng thức"],
}


def assign_topic_tags(content: str) -> list[str]:
    """Assign topic tags based on keyword matching."""
    content_lower = content.lower()
    tags = []
    for tag, keywords in TOPIC_KEYWORDS.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)
    return tags if tags else ["math.unknown"]


def process_exam_file(path: Path) -> dict:
    with open(path) as f:
        exam = json.load(f)

    for section in exam.get("sections", []):
        for q in section.get("questions", []):
            if not q.get("topic_tags"):
                q["topic_tags"] = assign_topic_tags(q.get("content", ""))

    return exam


def process_directory(input_dir: str, output_dir: str | None = None):
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path

    for fpath in input_path.glob("*.json"):
        exam = process_exam_file(fpath)
        out = output_path / fpath.name
        with open(out, "w", encoding="utf-8") as f:
            json.dump(exam, f, ensure_ascii=False, indent=2)
        print(f"✅ Processed {fpath.name}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python post_processor.py <input_dir> [output_dir]")
        sys.exit(1)
    process_directory(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
```

- [ ] **Step 2: Commit**

```bash
git add master/data/scrapers/post_processor.py
git commit -m "feat(data): add post-processor for topic tag assignment"
```

---

## Summary — What Nhật Huy Delivers

| Day | Deliverable |
|-----|-------------|
| 1 | `infra/docker-compose.yml` + MongoDB running |
| 1 | Knowledge graph JSON (21 nodes) |
| 2 | Rubric templates (THPTQG, V-ACT) |
| 2 | Sample exam JSON (10+ questions) |
| 2 | Seed script working |
| 3-4 | toanmath.com scraper |
| 5-6 | vietjack.com scraper (same pattern) |
| 6 | Post-processor for topic tag assignment |
| 7-9 | Scrape & process 20+ exams into DB |
| 10-12 | Data quality verification + manual additions |

**Critical deadlines:**
- Day 1: Docker Compose + sample exam JSON — team needs data to test against
- Day 2: Knowledge graph + rubrics — agents need topic tags and scoring info
