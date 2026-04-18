from typing import Iterable

def parser_ocr_instruction() -> str:
	return (
		"""
		Hãy đọc ảnh đề thi này và trích xuất toàn bộ nội dung nhìn thấy thành JSON theo đúng schema hệ thống.

		Yêu cầu:
		- Trích xuất metadata nếu nhìn thấy rõ.
		- Trích xuất đầy đủ các câu hỏi theo đúng thứ tự xuất hiện trong ảnh.
		- Giữ nguyên tiếng Việt gốc, công thức toán học, và ký hiệu xuất hiện trong đề.
		- Với câu trắc nghiệm, giữ nguyên nhãn A., B., C., D. ở đầu từng đáp án trong options.
		- Nếu câu không có đáp án lựa chọn thì options = [].
		- Nếu một thông tin không nhìn rõ thì không suy diễn thêm.
		"""
	)


def teacher_preprocess_prompt(batch_input_json: str) -> str:
    return f"""
		Hãy phân tích toàn bộ các câu hỏi trong BATCH_INPUT và trả về kết quả chấm cho từng question_id.

		Yêu cầu cho mỗi kết quả:
		- Xác định đáp án đúng nếu có thể.
		- Đánh giá agree, confidence, correct_answer, reasoning, feedback, discrimination_a, difficulty_b, topic_tags.
		- reasoning phải ngắn gọn, đúng bản chất toán học, không lan man.
		- feedback phải viết bằng tiếng Việt, rõ ràng, có ích cho học sinh.
		- topic_tags là danh sách ngắn các chủ đề/kỹ năng toán học liên quan nhất tới câu hỏi.
		- confidence phải nằm trong khoảng [0, 1].
		- discrimination_a và difficulty_b phải nằm trong khoảng [0, 1].
		- Không bỏ sót question_id nào trong batch.
		- Mỗi question_id chỉ có đúng một kết quả.

		BATCH_INPUT:
		{batch_input_json}
	"""

def teacher_hint_prompt(question, student_answer: str | None, student_message: str | None,) -> str:
	return f"""Hãy tạo một feedback dạng hint cho học sinh dựa trên thông tin dưới đây.

        Mục tiêu:
        - Chỉ đưa gợi ý vừa đủ để học sinh tự làm tiếp.
        - Không tiết lộ trọn vẹn đáp án nếu chưa thật sự cần thiết.
        - Ưu tiên gợi ý theo hướng tư duy, phương pháp, hoặc bước tiếp theo.
        - Viết hoàn toàn bằng tiếng Việt tự nhiên, ngắn gọn, dễ hiểu.
        - BẮT BUỘC tạo đúng 3 mức gợi ý trong field feedback theo format:
          Hint 1: ...
          Hint 2: ...
          Hint 3: ...
        - Hint 1 phải là gợi ý định hướng.
        - Hint 2 phải là gợi ý phương pháp hoặc công thức nên dùng.
        - Hint 3 phải là bước làm tiếp theo, nhưng vẫn chưa được lộ toàn bộ lời giải.
        - Không gộp cả ba hint thành một đoạn duy nhất không có nhãn.

        Thông tin bài toán:
        {question}

        Câu trả lời hiện tại của học sinh:
        {student_answer}

        Tin nhắn học sinh:
        {student_message}
	"""

def teacher_review_mistake_prompt(content: str, student_answer: str | None, student_message: str | None,) -> str:
	return f"""Hãy phân tích bài làm của học sinh và tạo kết quả review cho đúng schema hệ thống.

		Yêu cầu nội dung:
		- Xác định học sinh đúng hay sai.
		- Nếu sai, chỉ ra bước sai hoặc ý sai quan trọng nhất.
		- Giải thích ngắn gọn vì sao sai.
		- Nêu cách sửa đúng hoặc hướng làm đúng.
		- reasoning phải súc tích, đúng trọng tâm.
		- feedback phải là lời giải thích rõ ràng, dễ hiểu, viết bằng tiếng Việt tự nhiên.

		Câu hỏi:
		{content}

		Câu trả lời hiện tại của học sinh:
		{student_answer}

		Tin nhắn học sinh:
		{student_message}
	"""

def teacher_parse_prompt(image_bucket_url: str, parser_output: str) -> str:
	return f"""Hãy chuẩn hóa OCR_TEXT dưới đây thành JSON theo đúng schema exam/questions của hệ thống.

        Yêu cầu:
        - Giữ nguyên nội dung gốc nếu OCR đã đủ rõ; chỉ chuẩn hóa cấu trúc dữ liệu.
        - Mỗi question phải có id duy nhất dạng UUID string.
        - exam.questions phải là danh sách id của toàn bộ câu hỏi theo đúng question_index.
        - Nếu không xác định được correct_answer thì để null.
		- Nếu OCR_TEXT có IMAGE_URL theo trang thì ưu tiên gắn image_url đó cho các câu hỏi thuộc trang tương ứng.
		- Nếu câu hỏi có hình nhưng không tìm thấy IMAGE_URL theo trang thì đặt has_image=true và image_url={image_bucket_url}.
        - Nếu không có hình thì has_image=false và image_url=null.
        - topic_tags dùng danh sách rỗng nếu chưa xác định được.
        - discrimination_a mặc định 1.0, difficulty_b mặc định 0.0.
        - exam.id ưu tiên dùng exam_id sẵn có; nếu không có thì tự tạo UUID.
        - Các trường văn bản phải giữ tiếng Việt tự nhiên, không dịch sang ngôn ngữ khác.
        - Không bịa thêm câu hỏi, đáp án, hoặc metadata không có trong OCR_TEXT.

        OCR_TEXT:
        {parser_output}
	"""


def verifier_prompt(batch_input_json: str) -> str:
	return f"""
		Hãy kiểm tra lại đánh giá của Teacher cho toàn bộ các câu hỏi trong BATCH_INPUT và trả về kết quả cuối cùng theo đúng schema hệ thống.

		Yêu cầu:
		- Xác nhận hoặc phản biện kết luận của Teacher cho từng question_id.
		- agree = true nếu bạn đồng ý với đánh giá của Teacher; false nếu không đồng ý hoặc thấy chưa đủ chắc chắn.
		- reasoning phải ngắn gọn, nêu rõ điểm đúng hoặc sai trong đánh giá của Teacher.
		- feedback phải là phiên bản cuối cùng, rõ ràng, có thể gửi trực tiếp cho học sinh.
		- topic_tags là danh sách ngắn các chủ đề/kỹ năng toán học liên quan nhất tới câu hỏi.
		- confidence phải nằm trong khoảng [0, 1].
		- Không bỏ sót question_id nào trong batch.
		- Mỗi question_id chỉ có đúng một kết quả.

		BATCH_INPUT:
		{batch_input_json}
	"""


def adaptive_decide_question_strategy_prompt(
	target_limit: int,
	intent: str,
	learner_theta: float,
	weak_topics: list[str],
	strong_topics: list[str],
	answered_question_ids: list[str],
	candidate_question_topics: list[list[str]],
	rag_context_topics: list[list[str]],
	learning_goal: str,
	planner_context: str,
	user_request: str,
) -> str:
	return f"""
		Hãy quyết định chiến lược adaptive phù hợp nhất cho lượt ra câu tiếp theo.

		Bối cảnh nhiệm vụ:
		- intent = {intent}
		- learning_goal = {learning_goal}
		- planner_context = {planner_context}

		Dữ liệu hiện tại:
		- target_limit = {target_limit}
		- learner_theta = {learner_theta}
		- weak_topics = {weak_topics}
		- strong_topics = {strong_topics}
		- answered_question_ids = {answered_question_ids}
		- candidate_question_count = {len(candidate_question_topics)}
		- candidate_question_topics = {candidate_question_topics}
		- rag_context_count = {len(rag_context_topics)}
		- rag_context_topics = {rag_context_topics}
		- user_request = {user_request}

		Nguyên tắc quyết định:
		- Hồ sơ học sinh đã được cập nhật riêng bằng lịch sử bài vừa nộp.
		- Ở bước này bạn đang chọn chiến lược để tạo backlog luyện tập tiếp theo.
		- Ưu tiên bám mục tiêu dài hạn của học sinh và các chủ đề cần master.
		- Không xem bộ câu vừa làm xong là nguồn duy nhất cho lượt luyện tập tiếp theo.
		- Nếu ngân hàng hiện có chưa đủ phủ mục tiêu học tập, hãy ưu tiên generate hoặc mix.
	"""


def adaptive_generate_questions_prompt(
    *,
    limit: int,
    learner_profile_json: str,
    target_topics_json: str,
    learner_request: str,
    rag_context_json: str,
) -> str:
    return f"""
		Hãy sinh {limit} câu hỏi mới cho học sinh.

		Dữ liệu đầu vào:
		- LearnerProfile: {learner_profile_json}
		- Target topics ưu tiên: {target_topics_json}
		- Yêu cầu bổ sung của học sinh: {learner_request or "Không có"}

		RAG context từ database (chỉ dùng để tham khảo phong cách, độ khó, và phạm vi kiến thức):
		{rag_context_json}

		Yêu cầu:
		- Ưu tiên các chủ đề học sinh còn yếu và các target topics.
		- Độ khó phù hợp với năng lực hiện tại của học sinh.
		- Câu hỏi phải mới, không sao chép hoặc biến đổi nhẹ từ context.
		- Chỉ trả về output đúng schema đã được quy định.
		"""
