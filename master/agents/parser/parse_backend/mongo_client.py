from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from pymongo import MongoClient

from config import config
from extractor import ExamDocument


class MongoDBClient:
    def __init__(self):
        self.uri = config.MONGO_URI
        self.db_name = config.MONGO_DB
        self.collection_exams = config.MONGO_COLLECTION_EXAMS
        self.collection_questions = config.MONGO_COLLECTION_QUESTIONS

        self.client: MongoClient | None = None
        self.db = None
        self.exams_col = None
        self.questions_col = None


    def is_configured(self) -> bool:
        return bool(self.uri and self.db_name)


    def connect(self) -> None:
        if not self.is_configured():
            raise ValueError("MongoDB chưa được cấu hình đầy đủ MONGO_URI/MONGO_DB.")

        if self.client is not None:
            return

        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.exams_col = self.db[self.collection_exams]
        self.questions_col = self.db[self.collection_questions]
        self._ensure_indexes()


    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            self.exams_col = None
            self.questions_col = None


    def _ensure_indexes(self) -> None:
        self.exams_col.create_index("id", unique=True)
        self.questions_col.create_index("id", unique=True)
        self.questions_col.create_index([("exam_id", 1), ("question_index", 1)], unique=True)
        self.questions_col.create_index("question_index")
        self.questions_col.create_index("has_image")

    @staticmethod
    def _normalize_created_at(created_at: str | None) -> datetime:
        if created_at:
            return datetime.fromisoformat(created_at)
        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_question_doc(question: Dict[str, Any], exam_id: str) -> Dict[str, Any]:
        topic_tags = []
        for tag in question.get("topic_tags", []):
            topic_tags.append(tag.value if hasattr(tag, "value") else str(tag))

        return {
            **question,
            "exam_id": exam_id,
            "topic_tags": topic_tags,
        }

    def push_parser_output(self, parser_output: ExamDocument) -> bool:
        try:
            self.connect()

            question_docs: List[Dict[str, Any]] = []
            question_ids: List[str] = []
            for question in parser_output.questions:
                q_doc = self._normalize_question_doc(
                    question.model_dump(),
                    exam_id=parser_output.id,
                )
                question_docs.append(q_doc)
                question_ids.append(q_doc["id"])

            exam_doc = {
                "id": parser_output.id,
                "file_type": parser_output.file_type,
                "subject": parser_output.subject,
                "grade": parser_output.grade,
                "exam_type": parser_output.exam_type,
                "year": parser_output.year,
                "source": parser_output.source,
                "total_questions": parser_output.total_questions,
                "generated": parser_output.generated,
                "duration": parser_output.duration,
                "metadata": parser_output.metadata,
                "created_at": self._normalize_created_at(parser_output.created_at),
                "question_ids": question_ids,
            }

            if question_docs:
                for q_doc in question_docs:
                    self.questions_col.replace_one({"id": q_doc["id"]}, q_doc, upsert=True)

            self.exams_col.replace_one({"id": exam_doc["id"]}, exam_doc, upsert=True)

            print(
                f"[MongoDB] Upsert thành công exam {exam_doc['id']} | "
                f"questions={len(question_docs)} | "
                f"collections=({self.collection_exams}, {self.collection_questions})"
            )
            return True
        except Exception as e:
            print(f"[MongoDB] Lỗi push dữ liệu: {e}")
            import traceback
            traceback.print_exc()
            return False

