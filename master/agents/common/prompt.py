from typing import Iterable


def parser_ocr_instruction() -> str:
	return (
		"Bạn là OCR engine. Hãy đọc toàn bộ văn bản trong ảnh và trả về duy nhất nội dung văn bản "
		"đã OCR theo thứ tự đọc từ trên xuống dưới, trái sang phải. "
		"Không giải thích, không thêm nhận xét, không bổ sung nội dung ngoài ảnh. "
		"Giữ nguyên tiếng Việt có dấu và xuống dòng hợp lý."
	)


def teacher_draft_mode_instruction(solve_mode: bool) -> str:
	if solve_mode:
		return "Chế độ PREPROCESS: không có đáp án học sinh, hãy tự giải từng câu rồi kết luận."
	return "Chế độ REVIEW: chấm đáp án học sinh cho từng câu."


def teacher_batch_draft_prompt(mode_instruction: str, batch_input_json: str) -> str:
	return (
		"Bạn là giáo viên chấm nháp theo batch.\n"
		"Nhiệm vụ: xử lý toàn bộ câu trong BATCH_INPUT.\n"
		f"{mode_instruction}\n\n"
		"Yêu cầu output:\n"
		"- Trả về đúng schema DraftBatchResult.\n"
		"- results phải đủ tất cả question_id và mỗi id đúng 1 kết quả.\n"
		"- confidence trong [0,1].\n"
		"- reasoning ngắn gọn (<= 80 từ/câu).\n\n"
		"Ràng buộc ngôn ngữ (bắt buộc):\n"
		"- Toàn bộ nội dung text trong output (reasoning, feedback) PHẢI bằng tiếng Việt.\n"
		"- Không dùng tiếng Anh, trừ ký hiệu toán học hoặc tên riêng bắt buộc.\n"
		"- Dù đề bài có tiếng Anh, vẫn diễn giải và phản hồi bằng tiếng Việt.\n\n"
		"BATCH_INPUT:\n"
		f"{batch_input_json}"
	)


def teacher_batch_debate_prompt(batch_input_json: str) -> str:
	return (
		"Bạn là giáo viên tranh luận theo batch với Verifier.\n"
		"Nhiệm vụ: cập nhật kết luận cho toàn bộ câu trong BATCH_INPUT.\n\n"
		"Yêu cầu output:\n"
		"- Trả về đúng schema DebateBatchResult.\n"
		"- results phải đủ tất cả question_id và mỗi id đúng 1 kết quả.\n"
		"- teacher_rebuttal và final_feedback ngắn gọn.\n\n"
		"Ràng buộc ngôn ngữ (bắt buộc):\n"
		"- Toàn bộ nội dung text trong output (teacher_rebuttal, final_feedback) PHẢI bằng tiếng Việt.\n"
		"- Không dùng tiếng Anh, trừ ký hiệu toán học hoặc tên riêng bắt buộc.\n"
		"- Dù đề bài có tiếng Anh, vẫn diễn giải và phản hồi bằng tiếng Việt.\n\n"
		"BATCH_INPUT:\n"
		f"{batch_input_json}"
	)


def teacher_hint_prompt(
	question: object,
	student_answer: str | None,
	student_message: str | None,
) -> str:
	return f"""Bạn là giáo viên hỗ trợ học sinh.
        Nhiệm vụ: đưa ra gợi ý ngắn gọn để học sinh tự giải, KHÔNG tiết lộ đáp án trực tiếp.
        Nếu thông tin chưa đủ, hãy hỏi lại tối đa 1 câu để làm rõ.
        Bắt buộc: phản hồi hoàn toàn bằng tiếng Việt tự nhiên, không dùng tiếng Anh.

        Câu hỏi: {question}
        Câu trả lời hiện tại của học sinh: {student_answer}
        Tin nhắn học sinh: {student_message}

        Trả về JSON với trường feedback là nội dung gợi ý thân thiện, rõ ràng, tối đa 5 câu.
        """


def teacher_preprocess_prompt(image_bucket_url: str, parser_output: str) -> str:
	return f"""Bạn là bộ chuẩn hóa dữ liệu đề thi.

        Nhiệm vụ:
        - Đọc OCR text bên dưới và trích xuất dữ liệu theo đúng schema exam/questions.
        - Trả về đúng cấu trúc JSON của model Pydantic (exam + questions).
        - Mỗi question phải có id duy nhất dạng UUID string.
        - Nếu OCR không rõ đáp án đúng thì để correct_answer = null.
		- Nếu OCR_TEXT có dòng IMAGE_URL theo trang thì ưu tiên dùng URL đó cho các câu hỏi thuộc trang tương ứng.
		- Nếu câu hỏi có hình nhưng không tìm được IMAGE_URL theo trang thì has_image=true và image_url dùng link này: {image_bucket_url}.
        - Nếu không có hình thì has_image=false và image_url=null.
        - topic_tags dùng danh sách rỗng nếu chưa suy ra được.
        - difficulty_a mặc định 1.0, difficulty_b mặc định 0.0.
        - exam.id ưu tiên dùng exam_id đã có (nếu có), nếu không thì tự tạo UUID.
        - exam.questions phải là danh sách id của toàn bộ questions theo thứ tự question_index.
        - Các trường văn bản (subject, content, content_latex nếu có mô tả chữ, metadata mô tả) ưu tiên tiếng Việt; không tự dịch sai nghĩa.
        - Quy ước tên topic_tags: Dùng format subject.grade.chapter_code.topic_code (ví dụ: math.12.ch2.integrals).
        OCR_TEXT:
        {parser_output}
        """


def verifier_mode_instruction(solve_mode: bool) -> str:
	if solve_mode:
		return "Chế độ PREPROCESS: không có đáp án học sinh, hãy phản biện lời giải của teacher."
	return "Chế độ REVIEW: phản biện bài làm học sinh và chấm nháp của teacher."


def verifier_batch_prompt(mode_instruction: str, batch_input_json: str) -> str:
	return f"""Bạn là Verifier.
        Nhiệm vụ: kiểm tra batch theo hướng dẫn sau: {mode_instruction}

        Yêu cầu output:
        - Trả về đúng schema VerifierBatchVerdict.
        - verdicts phải chứa đúng tất cả question_id bên dưới (mỗi id đúng 1 verdict).
        - reasoning ngắn gọn (<= 60 từ mỗi câu).
        - feedback tối đa 2 ý ngắn mỗi câu.
        - confidence trong [0,1].

        Ràng buộc ngôn ngữ (bắt buộc):
        - Toàn bộ nội dung text trong output (reasoning, feedback) PHẢI bằng tiếng Việt.
        - Không dùng tiếng Anh, trừ ký hiệu toán học hoặc tên riêng bắt buộc.
        - Dù đề bài có tiếng Anh, vẫn diễn giải và phản hồi bằng tiếng Việt.

        BATCH_INPUT:
        {batch_input_json}
        """


def verifier_summary_prompt(lines: Iterable[str]) -> str:
	return (
		"Dựa trên kết quả chấm và phân tích dưới đây, hãy viết một đoạn nhận xét ngắn gọn cho học sinh.\n"
		"Bắt buộc: phản hồi hoàn toàn bằng tiếng Việt, không dùng tiếng Anh.\n\n"
		+ "\n".join(lines)
	)
