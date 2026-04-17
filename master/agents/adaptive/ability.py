"""Dùng để cập nhật hồ sơ học tập của học sinh dựa trên phản hồi mới nhất về câu hỏi đã trả lời.

Module này sở hữu khả năng học tập tổng thể của người học được khởi tạo bằng các 
adaptive stack. Để đánh giá khả năng học thì sẽ dựa trên công thức Item Response Theory (IRT).

P(correct | theta, difficulty_b, discrimination_a) = 1 / (1 + exp(-a * (theta - b)))

Trong đó:
    - theta: khả năng học tập của học sinh.
    - difficulty_b: độ khó của câu hỏi.
    - discrimination_a: độ phân biệt của câu hỏi, tức là mức độ nhạy cảm của câu hỏi đối với sự khác biệt về khả năng học tập.

Mục tiêu thiết kế là thực tế:
    - Ước lượng learner mạnh đến mức nào trên một thang đo nhỏ.
    - Ước lượng khả năng learner có thể giải quyết một bài toán có độ khó cho trước.
    - Cập nhật khả năng học tập của learner sau khi có một phản hồi được chấm điểm.
"""

from __future__ import annotations
from pydantic import BaseModel
import math

from master.agents.adaptive.bkt import _clamp_probability as _clamp

class AbilityParameters(BaseModel):
    """Hyperparameters được dùng để điều chỉnh khả năng học tập và độ khó được cập nhật theo thời gian.

    Attributes:
        student_k: Step size for the learner ability update (learning_rate cho biến theta)
        question_k: Step size for the item difficulty update.
        default_discrimination: Default steepness of the logistic curve. Higher
            values make the same theta-difficulty gap feel more decisive.
        min_theta: Lower bound for learner ability.
        max_theta: Upper bound for learner ability.
        min_difficulty: Lower bound for item difficulty.
        max_difficulty: Upper bound for item difficulty.
    """

    student_k: float = 0.35
    question_k: float = 0.15
    #TODO: Tune this default discrimination value based on real data. The ideal value
    default_discrimination: float = 6.0
    min_theta: float = -1.0
    max_theta: float = 1.0
    min_difficulty: float = 0.0
    max_difficulty: float = 1.0


class AbilityUpdateResult(BaseModel):
    """Cấu trúc kết quả trả về sau mỗi lần cập nhật.

    Attributes:
        theta: Updated learner ability after observing the response.
        difficulty: Updated item difficulty..
        expected_correct_probability: Model-estimated success probability before
            observing the latest outcome.
        residual: ``observed - expected``. Positive means the learner did
            better than expected; negative means worse than expected.
    """

    theta: float
    difficulty: float
    expected_correct_probability: float
    residual: float


def _estimate_correct_answer(
    theta: float,
    difficulty: float,
    discrimination: float = 1.0,
) -> float:
    """Ước lượng ``P(correct)`` bằng cách dùng đường cong logistic item-response. Hàm này được dùng để trả lời câu hỏi khi 
    student có khả năng theta thì xác suất trả lời

    The intuition is straightforward:
    - if ``theta`` is much larger than ``difficulty``, probability approaches 1
    - if ``theta`` is much smaller than ``difficulty``, probability approaches 0
    - when they are equal, probability is 0.5

    We also allow a discrimination parameter ``a``:
    - larger ``a`` means the curve is steeper
    - smaller ``a`` means the transition from easy to hard is softer
    """

    # Đảm bảo giá trị của discrimination không quá nhỏ.
    # Nếu discrimination quá nhỏ, đường cong sẽ trở nên quá phẳng, làm mất đi khả năng phân biệt giữa các mức độ khả năng khác nhau của người học. 
    # Việc đặt một giá trị tối thiểu giúp duy trì tính nhạy cảm của mô hình đối với sự khác biệt về khả năng học tập.
    a = max(0.2, discrimination)

    # P(correct) = 1 / (1 + exp(-a * (theta - difficulty)))
    delta = _clamp(a * (theta - difficulty), -12.0, 12.0)
    return 1.0 / (1.0 + math.exp(-delta))


def expected_correct_probability(
    theta: float,
    difficulty: float,
    discrimination: float = 1.0,
) -> float:
    """Public wrapper for the lightweight IRT success-probability estimate.

    Args:
        theta: Current learner ability estimate.
        difficulty: Question difficulty on the same latent scale.
        discrimination: Steepness of the logistic item curve.

    Returns:
        Estimated probability that the learner answers correctly.
    """

    return _estimate_correct_answer(
        theta=theta,
        difficulty=difficulty,
        discrimination=discrimination,
    )


def update_theta(
    theta: float,
    difficulty: float,
    is_correct: bool,
    params: AbilityParameters | None = None,
    discrimination: float | None = None,
) -> AbilityUpdateResult:
    """Thực hiện cập nhật khả năng học tập của người học.

    The update follows a simple residual-based rule:
    1. estimate how likely the learner was to succeed
    2. compare that estimate with the actual outcome
    3. move ability up/down in proportion to the surprise

    Examples:
    - expected 0.30, observed correct => positive residual => theta increases
    - expected 0.90, observed wrong   => negative residual => theta decreases

    Item difficulty updates are supported but disabled by default because the
    current MVP does not persist item updates yet. That makes the function safe
    to adopt immediately without introducing hidden state drift elsewhere.
    """

    tuned = params or AbilityParameters()
    a = (
        discrimination
        if discrimination is not None
        else tuned.default_discrimination
    )
    expected = _estimate_correct_answer(
        theta=theta,
        difficulty=difficulty,
        discrimination=a,
    )
    observed = 1.0 if is_correct else 0.0
    residual = observed - expected

    # Theta always updates because the student response is new information
    # about the learner.
    next_theta = _clamp(
        theta + tuned.student_k * residual,
        tuned.min_theta,
        tuned.max_theta,
    )

    return AbilityUpdateResult(
        theta=next_theta,
        difficulty=difficulty,
        expected_correct_probability=expected,
        residual=residual,
    )


# Compatibility aliases: the wider adaptive package still thinks in "IRT"
# naming, even though this module is intentionally a lightweight global ability
# engine rather than a full-blown offline IRT calibration system.
IRTParameters = AbilityParameters
IRTUpdateResult = AbilityUpdateResult
update_theta_and_difficulty = update_theta
