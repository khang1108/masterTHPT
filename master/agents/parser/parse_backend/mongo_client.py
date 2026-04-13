import json
from datetime import datetime, timezone
# from pymongo import MongoClient
# from pymongo.errors import ConnectionFailure, ConfigurationError
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
        
        # Chỉ kết nối nếu có cấu hình
        # if self.uri and self.db_name:
        #     self._connect()
        # else:
        print("[MongoDB] ⚠️ DB connection DISABLED for testing. Chỉ in log dữ liệu ra.")

    # def _connect(self):
    #     try:
    #         self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
    #         self.client.admin.command('ping') # Kiểm tra kết nối
    #         self.db = self.client[self.db_name]
    #         self.exams_col = self.db[self.collection_exams]
    #         self.questions_col = self.db[self.collection_questions]
    #         print(f"[MongoDB] ✅ Đã kết nối tới database '{self.db_name}' thành công.")
    #         print(f"    📦 Collections: '{self.collection_exams}', '{self.collection_questions}'")
    #     except (ConnectionFailure, ConfigurationError) as e:
    #         print(f"[MongoDB] ❌ Không thể kết nối tới cơ sở dữ liệu: {e}")
    #         self.client = None

    def push_exam(self, json_filepath: str) -> bool:
        """
        Đẩy file JSON có sẵn lên MongoDB.
        Bóc tách ra 2 collections: exams và questions.
        """
        # if not self.client:
        #     print("[MongoDB] ⚠️ Không có kết nối DB. Bỏ qua việc đẩy dữ liệu.")
        #     return False

        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # ====== TÁCH EXAMS DOCUMENT ======
            exam_doc = dict(data)  # shallow copy
            sections = exam_doc.pop("sections", [])
            
            # Chuyển created_at ISO string thành datetime object cho MongoDB timestamp
            if exam_doc.get("created_at"):
                exam_doc["created_at"] = datetime.fromisoformat(exam_doc["created_at"])
            else:
                exam_doc["created_at"] = datetime.now(timezone.utc)

            exam_id = exam_doc.get("id", "unknown")

            # ====== TÁCH QUESTIONS DOCUMENTS ======
            question_docs = []
            for section in sections:
                section_type = section.get("type", "multiple_choice")
                for q in section.get("questions", []):
                    q_doc = dict(q)
                    q_doc["section_type"] = section_type  # Giữ lại thông tin section
                    # Serialize topic_tags enum values thành strings
                    if q_doc.get("topic_tags"):
                        q_doc["topic_tags"] = [
                            tag if isinstance(tag, str) else tag
                            for tag in q_doc["topic_tags"]
                        ]
                    question_docs.append(q_doc)

            # ====== LOG DỮ LIỆU (Testing mode) ======
            print(f"\n{'='*60}")
            print(f"[MongoDB] 📋 EXAM DOCUMENT (sẽ insert vào collection '{self.collection_exams}'):")
            print(f"    🔑 ID:             {exam_id}")
            print(f"    📚 Subject:        {exam_doc.get('subject')}")
            print(f"    📝 Exam Type:      {exam_doc.get('exam_type')}")
            print(f"    📅 Year:           {exam_doc.get('year')}")
            print(f"    🌐 Source:         {exam_doc.get('source')}")
            print(f"    📊 Total Q:        {exam_doc.get('total_questions')}")
            print(f"    ⏱️  Duration:       {exam_doc.get('duration')} phút")
            print(f"    🕐 Created At:     {exam_doc.get('created_at')}")
            print(f"    📦 Metadata:       {exam_doc.get('metadata')}")
            
            print(f"\n[MongoDB] 📋 QUESTIONS ({len(question_docs)} docs → collection '{self.collection_questions}'):")
            for i, qd in enumerate(question_docs[:5]):  # In tối đa 5 câu đầu
                print(f"    [{i+1}] id={qd.get('id', '?')[:16]}... | idx={qd.get('question_index')} | exam_id={qd.get('exam_id', '?')[:16]}... | tags={qd.get('topic_tags')}")
            if len(question_docs) > 5:
                print(f"    ... và {len(question_docs) - 5} câu hỏi khác.")
            print(f"{'='*60}\n")

            # ====== ACTUAL DB INSERT (commented out for testing) ======
            # # Insert exam document
            # self.exams_col.update_one(
            #     {"id": exam_id},
            #     {"$set": exam_doc},
            #     upsert=True
            # )
            # print(f"[MongoDB] 🚀 Đã upsert Exam '{exam_id}' vào '{self.collection_exams}'")
            #
            # # Insert questions (bulk)
            # if question_docs:
            #     from pymongo import UpdateOne
            #     ops = [
            #         UpdateOne({"id": qd["id"]}, {"$set": qd}, upsert=True)
            #         for qd in question_docs
            #     ]
            #     result = self.questions_col.bulk_write(ops)
            #     print(f"[MongoDB] 🚀 Đã upsert {result.upserted_count + result.modified_count} questions vào '{self.collection_questions}'")

            return True
            
        except Exception as e:
            print(f"[MongoDB] ❌ Lỗi khi khởi tạo insert: {e}")
            import traceback
            traceback.print_exc()
            return False
