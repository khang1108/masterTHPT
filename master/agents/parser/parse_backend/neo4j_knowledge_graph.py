import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "masterthpt2026")
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "math_knowledge_base.json"


class MathKnowledgeGraphBuilder:

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connection()


    def _verify_connection(self) -> None:
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS ping")
            assert result.single()["ping"] == 1
        print(f"[Neo4j] Connected to {NEO4J_URI}")


    def close(self) -> None:
        self.driver.close()
        print("[Neo4j] Connection closed")


    def create_constraints(self) -> None:
        """Create schema constraints and indexes."""
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
            for statement in constraints + indexes:
                session.run(statement)

        print("[Neo4j] Schema ready")


    def clear_graph(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("[Neo4j] Graph cleared")


    def build_graph(self, json_path: str | Path) -> None:
        """Build Subject > Grade > Chapter > Lesson nodes."""
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        subject = data["subject"]
        nodes = data["nodes"]

        with self.driver.session() as session:
            session.run("MERGE (s:Subject {name: $name})", name=subject)

            grades = set()
            chapters: dict[tuple[int, str], str] = {}

            for node in nodes:
                grade = node["grade"]
                chapter = node["chapter"]
                grades.add(grade)
                chapter_key = (grade, str(chapter))
                chapters.setdefault(
                    chapter_key,
                    f"Chương {chapter}" if isinstance(chapter, int) else str(chapter),
                )

            for grade in sorted(grades):
                session.run(
                    """
                    MERGE (g:Grade {level: $level})
                    WITH g
                    MATCH (s:Subject {name: $subject})
                    MERGE (s)-[:HAS_GRADE]->(g)
                    """,
                    level=grade,
                    subject=subject,
                )

            for (grade, chapter_raw), chapter_display in chapters.items():
                session.run(
                    """
                    MERGE (c:Chapter {grade: $grade, number: $number})
                    ON CREATE SET c.display_name = $display
                    WITH c
                    MATCH (g:Grade {level: $grade})
                    MERGE (g)-[:HAS_CHAPTER]->(c)
                    """,
                    grade=int(grade),
                    number=chapter_raw,
                    display=chapter_display,
                )

            for node in nodes:
                session.run(
                    """
                    MERGE (l:Lesson {id: $id})
                    ON CREATE SET l.topic = $topic, l.display_name = $display_name,
                                  l.grade = $grade, l.chapter = $chapter
                    ON MATCH SET  l.topic = $topic, l.display_name = $display_name,
                                  l.grade = $grade, l.chapter = $chapter
                    WITH l
                    MATCH (c:Chapter {grade: $grade, number: $chapter})
                    MERGE (c)-[:HAS_LESSON]->(l)
                    """,
                    id=node["id"],
                    topic=node["topic"],
                    display_name=node["display_name"],
                    grade=node["grade"],
                    chapter=str(node["chapter"]),
                )

            prerequisite_count = 0
            for node in nodes:
                for prerequisite_id in node.get("prerequisites", []):
                    session.run(
                        """
                        MATCH (pre:Lesson {id: $pre_id})
                        MATCH (cur:Lesson {id: $cur_id})
                        MERGE (pre)-[:PREREQUISITE_OF]->(cur)
                        """,
                        pre_id=prerequisite_id,
                        cur_id=node["id"],
                    )
                    prerequisite_count += 1

        print(
            f"[Neo4j] Graph built subject={subject} grades={len(grades)} "
            f"chapters={len(chapters)} lessons={len(nodes)} edges={prerequisite_count}"
        )


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


    def get_lessons_unlocked_by(self, lesson_id: str) -> list[dict]:
        query = """
        MATCH (l:Lesson {id: $id})-[:PREREQUISITE_OF]->(next:Lesson)
        RETURN next.id AS id, next.grade AS grade,
               next.topic AS topic, next.display_name AS display_name
        ORDER BY next.grade, next.id
        """
        with self.driver.session() as session:
            return [dict(record) for record in session.run(query, id=lesson_id)]


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


    def export_for_ai(self) -> dict:
        """Export the graph for downstream AI use."""
        return {
            "subject": "Mathematics",
            "stats": self.get_graph_stats(),
            "lessons": self.get_all_lessons(),
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Math THPT Knowledge Graph builder and query tool",
    )
    parser.add_argument("--clear", action="store_true", help="Clear graph before rebuilding")
    parser.add_argument("--query-all", action="store_true", help="Print all lessons")
    parser.add_argument("--stats", action="store_true", help="Print graph statistics")
    parser.add_argument("--search", type=str, default=None, help="Search by topic keyword")
    parser.add_argument("--prereqs", type=str, default=None, help="Show prerequisite chain")
    parser.add_argument("--unlocks", type=str, default=None, help="Show unlocked lessons")
    parser.add_argument("--export-json", type=str, default=None, help="Export graph to JSON")
    args = parser.parse_args()

    builder = MathKnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        builder.create_constraints()

        if args.clear:
            builder.clear_graph()

        if not any([args.query_all, args.stats, args.search, args.prereqs, args.unlocks, args.export_json]):
            builder.build_graph(KNOWLEDGE_BASE_PATH)
            print("[Neo4j] Graph ready")
            print("[Neo4j] Browser http://localhost:7474")
            print("[Neo4j] Bolt bolt://localhost:7687")

        if args.query_all:
            lessons = builder.get_all_lessons()
            print(f"[Neo4j] Lessons {len(lessons)}")
            for lesson in lessons:
                prerequisites = ", ".join(lesson["prerequisites"]) if lesson["prerequisites"] else "-"
                print(f"[{lesson['id']}] grade={lesson['grade']} name={lesson['display_name']}")
                print(f"prerequisites: {prerequisites}")

        if args.stats:
            stats = builder.get_graph_stats()
            print(
                f"[Neo4j] Stats grades={stats['grades']} chapters={stats['chapters']} "
                f"lessons={stats['lessons']} edges={stats['prereqs']}"
            )

        if args.search:
            results = builder.find_lessons_by_topic(args.search)
            print(f"[Neo4j] Search '{args.search}' results={len(results)}")
            for result in results:
                print(f"[{result['id']}] {result['display_name']}")

        if args.prereqs:
            chain = builder.get_prerequisite_chain(args.prereqs)
            print(f"[Neo4j] Prerequisite chain size={len(chain)}")
            for item in chain:
                print(f"[{item['id']}] grade={item['grade']} name={item['display_name']}")

        if args.unlocks:
            unlocked = builder.get_lessons_unlocked_by(args.unlocks)
            print(f"[Neo4j] Unlocked lessons={len(unlocked)}")
            for item in unlocked:
                print(f"[{item['id']}] grade={item['grade']} name={item['display_name']}")

        if args.export_json:
            export = builder.export_for_ai()
            with open(args.export_json, "w", encoding="utf-8") as file:
                json.dump(export, file, ensure_ascii=False, indent=2)
            print(f"[Neo4j] Exported {args.export_json}")
    finally:
        builder.close()


if __name__ == "__main__":
    main()
