import json
from datetime import datetime, timezone
from config import config


class MongoDBClient:
    def __init__(self):
        self.uri = config.MONGO_URI
        self.db_name = config.MONGO_DB
        self.collection_exams = config.MONGO_COLLECTION_EXAMS
        self.collection_questions = config.MONGO_COLLECTION_QUESTIONS

        self.client = None
        self.db = None
        self.exams_col = None
        self.questions_col = None

    def push_exam(self, json_filepath: str) -> bool:
        """Đẩy file JSON lên MongoDB, tách ra 2 collections: exams và questions."""
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Tách exam document
            exam_doc = dict(data)
            sections = exam_doc.pop("sections", [])

            if exam_doc.get("created_at"):
                exam_doc["created_at"] = datetime.fromisoformat(exam_doc["created_at"])
            else:
                exam_doc["created_at"] = datetime.now(timezone.utc)

            exam_id = exam_doc.get("id", "unknown")

            # Tách questions documents
            question_docs = []
            for section in sections:
                section_type = section.get("type", "multiple_choice")
                for q in section.get("questions", []):
                    q_doc = dict(q)
                    q_doc["section_type"] = section_type
                    if q_doc.get("topic_tags"):
                        q_doc["topic_tags"] = [
                            tag if isinstance(tag, str) else tag
                            for tag in q_doc["topic_tags"]
                        ]
                    question_docs.append(q_doc)

            # Log dữ liệu (testing mode)
            print(f"\n{'='*60}")
            print(f"EXAM: {exam_id} | {exam_doc.get('subject')} | {exam_doc.get('exam_type')} | {exam_doc.get('total_questions')}Q")
            print(f"QUESTIONS: {len(question_docs)} docs")
            for i, qd in enumerate(question_docs[:5]):
                print(f"[{i+1}] id={qd.get('id', '?')[:16]}... | idx={qd.get('question_index')} | tags={qd.get('topic_tags')}")
            print(f"{'='*60}\n")
            return True

        except Exception as e:
            print(f"Lỗi khi insert: {e}")
            import traceback
            traceback.print_exc()
            return False
