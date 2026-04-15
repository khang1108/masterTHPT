import json
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "masterthpt2026")
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "math_knowledge_base.json"


class MathKnowledgeGraphBuilder:

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connection()

    def _verify_connection(self):
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS ping")
            assert result.single()["ping"] == 1
        print("[✓] Connected to Neo4j at", NEO4J_URI)

    def close(self):
        self.driver.close()
        print("[✓] Neo4j driver closed.")

    # Schema constraints & indexes
    def create_constraints(self):
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subject) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Grade) REQUIRE g.level IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Lesson) REQUIRE l.id IS UNIQUE",
        ]
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (c:Chapter) ON (c.grade, c.number)",
            "CREATE INDEX IF NOT EXISTS FOR (l:Lesson) ON (l.grade)",
            "CREATE INDEX IF NOT EXISTS FOR (l:Lesson) ON (l.topic)",
        ]
        with self.driver.session() as session:
            for stmt in constraints + indexes:
                session.run(stmt)
        print("Constraints and indexes created.")

    def clear_graph(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("Graph cleared.")

    # Build: Subject → Grade → Chapter → Lesson + PREREQUISITE_OF edges
    def build_graph(self, json_path: str | Path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        subject = data["subject"]
        nodes = data["nodes"]

        with self.driver.session() as session:
            session.run("MERGE (s:Subject {name: $name})", name=subject)

            grades = set()
            chapters = {}

            for node in nodes:
                g = node["grade"]
                ch = node["chapter"]
                grades.add(g)
                ch_key = (g, str(ch))
                if ch_key not in chapters:
                    chapters[ch_key] = f"Chương {ch}" if isinstance(ch, int) else str(ch)

            for g in sorted(grades):
                session.run("""
                    MERGE (g:Grade {level: $level})
                    WITH g
                    MATCH (s:Subject {name: $subject})
                    MERGE (s)-[:HAS_GRADE]->(g)
                """, level=g, subject=subject)

            for (g, ch_raw), ch_display in chapters.items():
                session.run("""
                    MERGE (c:Chapter {grade: $grade, number: $number})
                    ON CREATE SET c.display_name = $display
                    WITH c
                    MATCH (g:Grade {level: $grade})
                    MERGE (g)-[:HAS_CHAPTER]->(c)
                """, grade=int(g), number=ch_raw, display=ch_display)

            for node in nodes:
                session.run("""
                    MERGE (l:Lesson {id: $id})
                    ON CREATE SET l.topic = $topic, l.display_name = $display_name,
                                  l.grade = $grade, l.chapter = $chapter
                    ON MATCH SET  l.topic = $topic, l.display_name = $display_name,
                                  l.grade = $grade, l.chapter = $chapter
                    WITH l
                    MATCH (c:Chapter {grade: $grade, number: $chapter})
                    MERGE (c)-[:HAS_LESSON]->(l)
                """,
                    id=node["id"], topic=node["topic"],
                    display_name=node["display_name"],
                    grade=node["grade"], chapter=str(node["chapter"]),
                )

            prereq_count = 0
            for node in nodes:
                for prereq_id in node.get("prerequisites", []):
                    session.run("""
                        MATCH (pre:Lesson {id: $pre_id})
                        MATCH (cur:Lesson {id: $cur_id})
                        MERGE (pre)-[:PREREQUISITE_OF]->(cur)
                    """, pre_id=prereq_id, cur_id=node["id"])
                    prereq_count += 1

        print(f"[✓] Graph built: {subject} | {len(grades)} grades | {len(chapters)} chapters | {len(nodes)} lessons | {prereq_count} edges")

    # Query: tất cả bài học + prerequisites
    def get_all_lessons(self) -> list[dict]:
        query = """
        MATCH (l:Lesson)
        OPTIONAL MATCH (pre:Lesson)-[:PREREQUISITE_OF]->(l)
        RETURN l.id AS id, l.grade AS grade, l.chapter AS chapter,
               l.topic AS topic, l.display_name AS display_name,
               collect(pre.id) AS prerequisites
        ORDER BY l.grade, l.chapter, l.id
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query)]

    # Query: bài học theo lớp
    def get_lessons_by_grade(self, grade: int) -> list[dict]:
        query = """
        MATCH (l:Lesson {grade: $grade})
        OPTIONAL MATCH (pre:Lesson)-[:PREREQUISITE_OF]->(l)
        RETURN l.id AS id, l.chapter AS chapter, l.topic AS topic,
               l.display_name AS display_name, collect(pre.id) AS prerequisites
        ORDER BY l.chapter, l.id
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query, grade=grade)]

    # Query: chuỗi kiến thức tiên quyết đầy đủ
    def get_prerequisite_chain(self, lesson_id: str) -> list[dict]:
        query = """
        MATCH path = (root:Lesson)-[:PREREQUISITE_OF*]->(target:Lesson {id: $id})
        WITH nodes(path) AS ns
        UNWIND ns AS n
        RETURN DISTINCT n.id AS id, n.grade AS grade,
               n.topic AS topic, n.display_name AS display_name
        ORDER BY n.grade, n.id
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query, id=lesson_id)]

    # Query: bài nào mở khóa sau khi học xong bài này
    def get_lessons_unlocked_by(self, lesson_id: str) -> list[dict]:
        query = """
        MATCH (l:Lesson {id: $id})-[:PREREQUISITE_OF]->(next:Lesson)
        RETURN next.id AS id, next.grade AS grade,
               next.topic AS topic, next.display_name AS display_name
        ORDER BY next.grade, next.id
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query, id=lesson_id)]

    # Query: thống kê graph
    def get_graph_stats(self) -> dict:
        query = """
        MATCH (l:Lesson) WITH count(l) AS lessons
        MATCH ()-[r:PREREQUISITE_OF]->() WITH lessons, count(r) AS prereqs
        MATCH (c:Chapter) WITH lessons, prereqs, count(c) AS chapters
        MATCH (g:Grade) WITH lessons, prereqs, chapters, count(g) AS grades
        RETURN grades, chapters, lessons, prereqs
        """
        with self.driver.session() as session:
            record = session.run(query).single()
            if record is None:
                return {"grades": 0, "chapters": 0, "lessons": 0, "prereqs": 0}
            return dict(record)

    # Query: tìm bài học theo từ khóa topic (case-insensitive)
    def find_lessons_by_topic(self, keyword: str) -> list[dict]:
        query = """
        MATCH (l:Lesson)
        WHERE toLower(l.topic) CONTAINS toLower($kw)
           OR toLower(l.display_name) CONTAINS toLower($kw)
        OPTIONAL MATCH (pre:Lesson)-[:PREREQUISITE_OF]->(l)
        RETURN l.id AS id, l.grade AS grade, l.chapter AS chapter,
               l.topic AS topic, l.display_name AS display_name,
               collect(pre.id) AS prerequisites
        ORDER BY l.grade, l.id
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query, kw=keyword)]

    # Export toàn bộ graph dạng JSON cho AI pipeline
    def export_for_ai(self) -> dict:
        return {
            "subject": "Mathematics",
            "stats": self.get_graph_stats(),
            "lessons": self.get_all_lessons(),
        }


# CLI entry point
def main():
    parser = argparse.ArgumentParser(description="Math THPT Knowledge Graph — Neo4j builder & query tool")
    parser.add_argument("--clear", action="store_true", help="Clear graph before rebuilding")
    parser.add_argument("--query-all", action="store_true", help="Print all lessons")
    parser.add_argument("--stats", action="store_true", help="Print graph statistics")
    parser.add_argument("--search", type=str, default=None, help="Search by topic keyword")
    parser.add_argument("--prereqs", type=str, default=None, help="Prerequisite chain for lesson id")
    parser.add_argument("--unlocks", type=str, default=None, help="Lessons unlocked by lesson id")
    parser.add_argument("--export-json", type=str, default=None, help="Export graph to JSON file")
    args = parser.parse_args()

    builder = MathKnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        builder.create_constraints()

        if args.clear:
            builder.clear_graph()

        if not (args.query_all or args.stats or args.search or args.prereqs or args.unlocks or args.export_json):
            builder.build_graph(KNOWLEDGE_BASE_PATH)
            print("\n Knowledge graph is ready.")
            print("    Neo4j Browser → http://localhost:7474")
            print("    Bolt endpoint → bolt://localhost:7687")

        if args.query_all:
            lessons = builder.get_all_lessons()
            print(f"\n{'='*80}\n  All Lessons ({len(lessons)} total)\n{'='*80}")
            for l in lessons:
                prereqs = ", ".join(l["prerequisites"]) if l["prerequisites"] else "—"
                print(f"  [{l['id']}] Lớp {l['grade']} | {l['display_name']}")
                print(f"      prerequisites: {prereqs}")

        if args.stats:
            stats = builder.get_graph_stats()
            print(f"\n📊 Graph Statistics:")
            print(f"    Grades: {stats['grades']} | Chapters: {stats['chapters']} | Lessons: {stats['lessons']} | Edges: {stats['prereqs']}")

        if args.search:
            results = builder.find_lessons_by_topic(args.search)
            print(f"\n'{args.search}': {len(results)} found")
            for r in results:
                print(f"  [{r['id']}] {r['display_name']}")

        if args.prereqs:
            chain = builder.get_prerequisite_chain(args.prereqs)
            print(f"\nPrerequisite chain for '{args.prereqs}': {len(chain)} lessons")
            for c in chain:
                print(f"  [{c['id']}] Lớp {c['grade']} | {c['display_name']}")

        if args.unlocks:
            unlocked = builder.get_lessons_unlocked_by(args.unlocks)
            print(f"\nUnlocked by '{args.unlocks}': {len(unlocked)} lessons")
            for u in unlocked:
                print(f"  [{u['id']}] Lớp {u['grade']} | {u['display_name']}")

        if args.export_json:
            export = builder.export_for_ai()
            with open(args.export_json, "w", encoding="utf-8") as f:
                json.dump(export, f, ensure_ascii=False, indent=2)
            print(f"\n[✓] Exported graph to {args.export_json}")

    finally:
        builder.close()


if __name__ == "__main__":
    main()
