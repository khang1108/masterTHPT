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
		- Đánh giá agree, confidence, correct_answer, reasoning, feedback, discrimination_a, difficulty_b.
		- reasoning phải ngắn gọn, đúng bản chất toán học, không lan man.
		- feedback phải viết bằng tiếng Việt, rõ ràng, có ích cho học sinh.
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
        - difficulty_a mặc định 1.0, difficulty_b mặc định 0.0.
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
		- confidence phải nằm trong khoảng [0, 1].
		- Không bỏ sót question_id nào trong batch.
		- Mỗi question_id chỉ có đúng một kết quả.

		BATCH_INPUT:
		{batch_input_json}
	"""
