from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from typing import Optional

import uuid
import re

class Type(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_ans"

class QuestionOutput(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_index: int = Field(description="Số thứ tự câu hỏi trong đề, bắt đầu từ 1")
    type: Type = Field(description="Loại câu hỏi, là 1 trong 3 loại sau 'multiple_choice' hoặc 'true_false' hoặc 'short_ans'")
    content: str = Field(description="Nội dung câu hỏi, có thể bao gồm cả text và LaTeX, bỏ phần đầu như 'Câu 1: ' hoặc '1.'")
    options: Optional[list[str]] = Field(default=None, description="Danh sách lựa chọn nếu là câu hỏi trắc nghiệm, để trống nếu là câu hỏi tự luận")
    has_image: bool = Field(description="Câu hỏi có chứa hình ảnh hay không")
    image_url: Optional[str] = Field(default=None, description="URL của hình ảnh nếu có")
    generated: bool = Field(default=False, description="True nếu câu hỏi được tạo ra bởi LLM, False nếu được trích xuất trực tiếp từ đề thi. Nếu generated = True thì các trường có thể không chính xác và chỉ mang tính tham khảo.")


    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("content must not be empty")
        return content

    @field_validator("options")
    @classmethod
    def validate_options_items(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return None

        normalized_options = [str(option).strip() for option in value if str(option).strip()]
        return normalized_options or None

    @model_validator(mode="after")
    def validate_question_rules(self) -> "QuestionOutput":
        if self.type == Type.MULTIPLE_CHOICE:
            if not self.options or len(self.options) != 4:
                raise ValueError("multiple_choice must have exactly 4 options")

            expected_prefixes = ("A.", "B.", "C.", "D.")
            all_correct = all(option.startswith(prefix) for option, prefix in zip(self.options, expected_prefixes))

            if not all_correct:
                # Normalize: strip existing wrong prefixes and add correct ones
                normalized = []
                for option, prefix in zip(self.options, expected_prefixes):
                    text = option.strip()
                    if not text:
                        continue

                    # Remove existing prefix patterns like "a.", "a)", "A)", "1.", etc.
                    text = re.sub(r"^[A-Da-d1-4][.\)]\s*", "", text).strip()
                    normalized.append(f"{prefix} {text}")
                self.options = normalized

        elif self.type == Type.TRUE_FALSE:
            if not self.options:
                raise ValueError("true_false must have options")

            expected_prefixes = list("abcd")[:len(self.options)]
            normalized = []
            for option, letter in zip(self.options, expected_prefixes):
                text = option.strip()
                if re.match(r"^[a-d][.\)]", text):
                    normalized.append(text)
                else:
                    # Remove wrong prefix and add correct one
                    text = re.sub(r"^[A-Da-d1-4][.\)]\s*", "", text).strip()
                    normalized.append(f"{letter}) {text}")
            self.options = normalized

        elif self.type == Type.SHORT_ANSWER:
            if self.options is not None:
                raise ValueError("short_ans must have options = []")

        return self

class MetadataOutput(BaseModel):
    subject: Optional[str] = None
    exam_type: Optional[str] = None
    year: Optional[int] = None
    grade: Optional[int] = None
    source: Optional[str] = None
    total_questions: Optional[int] = None
    duration: Optional[int] = None    

class QuestionReviewOutput(BaseModel):
    question_marker: Optional[str] = None
    type: Type
    content: str
    options: list[str] = Field(default_factory=list)
    has_image: bool = False
    image_url: Optional[str] = None


class PageReviewOutput(BaseModel):
    metadata: MetadataOutput = Field(default_factory=MetadataOutput)
    questions: list[QuestionReviewOutput] = Field(default_factory=list)