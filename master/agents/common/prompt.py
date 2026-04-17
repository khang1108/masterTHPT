from typing import Iterable

def parser_ocr_instruction() -> str:
	return (
		"""
	        Bạn là một hệ thống OCR trích xuất đề thi tiếng Việt.

	        Nhiệm vụ:
	        - Đọc ảnh đề thi và trích xuất thành JSON.
	        - Chỉ trả về JSON hợp lệ.
	        - Không trả lời giải thích, không markdown, không code fence.

	        Schema bắt buộc:
	        {
	          "metadata": {
				"subject": "mã môn học (vd: math, physics, chemistry...)",
				"exam_type": "loại kỳ thi (vd: Cuối kì 1, Giữa kì 2...)",
				"year": "Sử dụng định dạng NumberInt('YYYY')",
				"grade": "Sử dụng định dạng NumberInt('số lớp')",
				"source": "Tên trường hoặc nguồn đề",
				"duration": "Sử dụng định dạng NumberInt('thời gian làm bài')",
	          },
	          "questions": [
	            {
	              "type": "",
	              "content": "nội dung câu hỏi, có thể bao gồm cả công thức LaTeX",
	              "options": []
	            }
	          ]
	        }

	        Rules:
	        - Chỉ trích xuất từ nội dung có trong ảnh.
	        - Giữ nguyên tiếng Việt gốc, không dịch.
	        - Giữ nguyên công thức LaTeX theo dạng $$...$$ nếu có.
	        - Escape dấu backslash trong LaTeX (\\frac, \\sqrt, ...).
	        - Giữ đúng thứ tự đáp án trong options.
	        - Nếu câu không có đáp án lựa chọn thì options = [].
	        - Nếu không xác định được một trường trong metadata thì để chuỗi rỗng "".
	        - Không bịa thêm câu hỏi hoặc nội dung không có trong ảnh.

	        Quan trọng:
	        - Không sao chép ví dụ schema vào output như dữ liệu thực.
			- Trong options, BẮT BUỘC các ký tự A., B., C., D phải ở đầu không được khác, sau đó sẽ kèm text của đáp án câu đó.
	        - Output chứa bất kỳ văn bản ngoài JSON đều bị xem là sai.
			
			Dữ liệu mẫu cho Metadata:
            - subject: 'math'
            - exam_type: 'Cuối kì 1'
        """
	)


def teacher_preprocess_prompt(batch_input_json: str) -> str:
    return f"""
		Bạn là Trợ lý Giáo viên chuyên chấm bài theo lô (batch).
		NHIỆM VỤ: Phân tích và đánh giá toàn bộ câu hỏi trong BATCH_INPUT.

		YÊU CẦU ĐẦU RA:
		1. Đầy đủ: Trả về kết quả cho mọi 'question_id', không bỏ sót.
		2. Định mức: Mỗi 'question_id' đi kèm chính xác 1 kết quả chấm.
		3. Chỉ số: 'confidence' nằm trong khoảng [0, 1].
		4. Diễn giải: 'reasoning' phải súc tích, đi thẳng vào vấn đề.

		RÀNG BUỘC NGÔN NGỮ (BẮT BUỘC):
		- Sử dụng TIẾNG VIỆT cho toàn bộ nội dung (reasoning, feedback).

		BATCH_INPUT:
		{batch_input_json}
	"""

def teacher_hint_prompt(question: object, student_answer: str | None, student_message: str | None,) -> str:
	return f"""Bạn là giáo viên hỗ trợ học sinh.
        Nhiệm vụ: đưa ra gợi ý ngắn gọn để học sinh tự giải, KHÔNG tiết lộ đáp án trực tiếp.
        Nếu thông tin chưa đủ, hãy hỏi lại tối đa 1 câu để làm rõ.
        Bắt buộc: phản hồi hoàn toàn bằng tiếng Việt tự nhiên, không dùng tiếng Anh.

        Câu hỏi: {question}
        Câu trả lời hiện tại của học sinh: {student_answer}
        Tin nhắn học sinh: {student_message}

        Trả về feedback cho học sinh
	"""

def teacher_review_mistake_prompt(question: object, student_answer: str | None, student_message: str | None,) -> str:
	return f"""Bạn là giáo viên chuyên phản biện bài làm của học sinh.
		Nhiệm vụ: Phân tích và chỉ ra sai sót trong câu trả lời của học sinh, giúp họ hiểu lỗi và cách cải thiện.
		Bắt buộc: phản hồi hoàn toàn bằng tiếng Việt tự nhiên, không dùng tiếng Anh.

		Câu hỏi: {question}
		Câu trả lời hiện tại của học sinh: {student_answer}
		Tin nhắn học sinh: {student_message}

		Trả về với trường feedback là phân tích chi tiết về sai sót, giải thích rõ ràng và gợi ý cách cải thiện.
	"""

def teacher_parse_prompt(image_bucket_url: str, parser_output: str) -> str:
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


def verifier_prompt(batch_input_json: str) -> str:
	return f"""
		Bạn là Trợ lý Giáo viên chuyên chấm bài theo lô (batch).
		NHIỆM VỤ: Phân tích và đánh giá toàn bộ câu hỏi trong BATCH_INPUT.

		Dưới đây là danh sách các question_id cần chấm cũng như câu trả lời của học sinh cho từng câu hỏi đó. 
		Hãy đưa ra đánh giá cho từng câu trả lời dựa trên các tiêu chí sau:
		1. Đúng hay Sai: Xác định xem câu trả lời của học sinh có đúng hay không.
		2. Mức độ tự tin: Đánh giá mức độ tự tin của bạn về đánh giá đúng/sai, với điểm số từ 0 đến 1.
		3. Lý do: Cung cấp một giải thích ngắn gọn về lý do tại sao bạn đánh giá câu trả lời đó là đúng hay sai.
		BATCH_INPUT:
		{batch_input_json}
	"""