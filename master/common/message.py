from pydantic import BaseModel

class GradeResult(BaseModel):
    """
    Điểm được chấm từ phía /app gửi về (điểm, câu đúng, câu sai)
    Args:
        exam_id: ID của bài thi
        student_id: ID của học sinh
        session_id: ID của phiên học
        total_questions: Tổng số câu hỏi
        total_correct: Tổng số câu đúng
        total_score: Tổng điểm
    """
    exam_id: str
    student_id: str
    session_id: str
    total_questions: int
    total_correct: int
    total_score: float

class Solution(BaseModel):
    """
    Lời giải cho một câu hỏi
    Args:
        question_id: ID của câu hỏi
        solution: Lời giải cho câu hỏi
    """
    question_id: str
    solution: str