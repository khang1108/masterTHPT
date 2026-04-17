# SGK / CTGDPT Math 10–12 Knowledge Graph — Implementation Plan

**See also:** [2026-04-14-pdf-to-skill-set-pipeline.md](2026-04-14-pdf-to-skill-set-pipeline.md) — full steps **PDF SGK → draft skills → align CT → YAML** trước khi nạp vào graph.

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a versioned knowledge graph whose nodes are **skills** (aligned to Chương trình GDPT 2018 for Mathematics grades 10–12) and whose edges express **pedagogical relationships** between skills, with optional mapping from commercial textbook chapters to canonical `skill_id`s.

**Architecture:** Authoritative identifiers come from the **official curriculum framework** (not from a single publisher). SGK books supply Vietnamese labels, chapter ordering, and synonyms via an **alias table**. The graph ships as structured data (YAML/JSON) and loads into either an in-process graph library or a graph database.

**Tech Stack (chọn một trong hai):**

| Option | Khi nào dùng | Ghi chú |
|--------|----------------|--------|
| **A — Python + NetworkX** | MVP nhanh, logic KG chỉ chạy trong Python agents | File `knowledge_graph.py`, không cần DB riêng |
| **B — Node.js + Neo4j** | Muốn KG là nguồn dùng chung cho **NestJS**, web, và sau này nhiều service | Neo4j lưu nodes/edges; **NestJS** dùng `neo4j-driver` (Bolt); seed/import có thể viết bằng script Node hoặc `cypher-shell` từ YAML/JSON đã chuẩn hóa |

**Có thể xây KG bằng Node.js:** **Có.** Đây thường là **Neo4j + ứng dụng Node** (hoặc module trong `master/apps/api`), không xung đột với spec — dữ liệu canonical vẫn là YAML/JSON theo CT; chỉ khác **nơi load và truy vấn** (Cypher vs Python `nx`).

**Tích hợp Python agents:** Gọi REST nội bộ (ví dụ `GET /internal/kg/trace?skill_id=...`) do NestJS implement, **hoặc** Python dùng `neo4j` Python driver trỏ cùng instance Neo4j (tránh trùng logic nếu chỉ muốn một lớp API).

---

## File map (when implementing)

| File | Responsibility |
|------|----------------|
| `data/knowledge_graph/math_ct_skills.yaml` | Canonical skill nodes (id, grade, domain, chapter_label, ct_anchor, aliases) |
| `data/knowledge_graph/math_ct_edges.yaml` | Directed/typed edges (source, target, relation) |
| `data/knowledge_graph/sgk_chapter_aliases.yaml` | Optional: publisher → chapter ref → `skill_id` |
| `master/agents/services/knowledge_graph.py` | **Option A:** Load YAML → `nx.DiGraph`, APIs nội bộ Python |
| `master/apps/api/src/.../knowledge-graph/` (hoặc module tương đương) | **Option B:** Neo4j queries (Cypher), endpoints nội bộ cho agents và UI |
| `scripts/seed-kg.ts` hoặc `scripts/import-kg.cypher` | **Option B:** Import YAML/JSON → Neo4j (một lần hoặc migration) |

---

## Task 1: Schema and conventions

- [ ] **Define skill_id naming:** Stable, URL-safe keys, e.g. `math.g10.algebra.quadratic_eq.one_var` (prefix `math`, grade, domain slug, short skill slug). Document in `data/knowledge_graph/README.md`.
- [ ] **Define edge relation enum:** `PREREQUISITE`, `RELATED`, `EXTENDS_ACROSS_GRADE`, `SAME_TOPIC_FAMILY` (subset used in MVP).
- [ ] **Decide chapter representation:** MVP uses `chapter_label` + optional `chapter_id` string on each skill; defer separate `chapter` nodes unless UI needs them.

---

## Task 2: Extract skill inventory from CTGDPT 2018

- [ ] **Collect official sources:** PDF/HTML khung chương trình Toán 10, 11, 12 (Bộ GD&ĐT) — list mục tiêu/nội dung theo từng lớp.
- [ ] **Transcribe to YAML:** One record per atomic skill (not entire chapters only); Vietnamese `title` matching curriculum wording where possible.
- [ ] **Scope for first milestone:** One vertical slice (e.g. grade 12: Giải tích + một phần Đại số) to validate pipeline before filling 10–11.

---

## Task 3: Cross-check with SGK (10, 11, 12)

- [ ] **Pick reference SGK** (one publisher for mapping first): use mục lục chương–bài to attach `aliases` and optional `sgk_chapter_aliases` rows.
- [ ] **Repeat for second publisher** only if product needs multi-book UX; otherwise keep aliases minimal.

---

## Task 4: Edge authoring

- [ ] **Prerequisites:** For each skill in the MVP slice, add `PREREQUISITE` edges where the curriculum implies order (e.g. limits before derivatives).
- [ ] **Cross-grade:** Add `EXTENDS_ACROSS_GRADE` where 11/12 explicitly builds on 10.
- [ ] **Validation script:** Python *hoặc* Node script checks: no unexpected cycles in `PREREQUISITE` subgraph (or allow cycles only if documented); all `source`/`target` ids exist.

---

## Task 5: Loader and API

**Option A (Python / NetworkX)**

- [ ] **Implement `KnowledgeGraphService`:** Load YAML → `nx.DiGraph`; filter by `grade`, `domain`.
- [ ] **Implement `trace_weaknesses(weak_skill_ids)`:** Walk predecessors via `PREREQUISITE` to suggest root causes (bounded depth).
- [ ] **Unit tests:** Small fixture graph + tests for traversal and missing-node handling.

**Option B (Node.js / Neo4j)** — dùng khi muốn KG trong stack NestJS

- [ ] **Provision Neo4j** (Docker Compose hoặc cloud dev): một database cho dev/staging.
- [ ] **Schema Cypher:** `(:Skill {id, grade, domain, chapter_label, ...})`, `[:PREREQUISITE]`, `[:RELATED]`, … (relation type hoặc property `relation` tùy chọn thiết kế).
- [ ] **Seed:** Import từ cùng file YAML/JSON canonical (Task 1–2) bằng script Node hoặc batch `LOAD CSV` / `UNWIND`.
- [ ] **NestJS module:** Service wrap `neo4j-driver`, method `traceWeaknesses(skillIds: string[], maxDepth: number)` chạy Cypher (walk ngược prerequisite).
- [ ] **API nội bộ:** `GET/POST` cho Python agents (hoặc Python gọi Bolt trực tiếp nếu team thống nhất).
- [ ] **Tests:** Integration test với Neo4j Testcontainers hoặc instance local.

---

## Task 6: Integration hooks

- [ ] **Question tagging contract:** `QuestionExam` (or equivalent) stores `skill_ids: string[]` referencing the same ids as the graph.
- [ ] **Adaptive / GenAL:** Pass `kg_context` string built from `trace_weaknesses` + neighbor skills into the selector prompt (per architecture spec).

---

## Self-review (plan vs spec)

- Spec section **4.4** in `docs/superpowers/specs/2026-04-12-master-architecture-redesign.md` defines CT anchoring, node/edge types, and SGK role; this plan operationalizes that content.
- **Node.js + Neo4j** is an explicit alternative to Python NetworkX; spec §5 Technology Mapping reflects this.
- Remaining gap until implementation: exact file paths under `master/` may match repo layout at implementation time; adjust imports accordingly.

---

## Execution choice (after plan approval)

1. **Subagent-driven:** One task per checkbox with review between tasks.  
2. **Inline:** Implement sequentially in one session with checkpoints after Task 2 and Task 4 (data complete before code).
