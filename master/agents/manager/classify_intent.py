from master.agents.common.message import Intent
from master.agents.common.state import AgentState


def _coerce_intent(value) -> Intent | None:
    """Convert enum or string-like values into a normalized Intent."""

    if value is None:
        return None
    if isinstance(value, Intent):
        return value

    raw = str(value).strip()
    if not raw:
        return None

    for candidate in (raw, raw.split(".")[-1]):
        try:
            return Intent(candidate)
        except ValueError:
            continue
    return None

def classify_intent(state: AgentState) -> AgentState:
    """
    Bộ phân loại Intent. Cho các Intent được định nghĩa bên trong.
    
    Args:
        - state: AgentState, state của Agent
    """

    request = state["request"]
    metadata = request.metadata or {}

    explicit_intent = _coerce_intent(request.intent) or _coerce_intent(
        metadata.get("intent")
    )

    if explicit_intent:
        state["intent"] = explicit_intent
        return state

    if metadata.get("intent"):
        coerced = _coerce_intent(metadata["intent"])
        if coerced is not None:
            state["intent"] = coerced
            return state

    if request.content:
        text = request.content.lower()
    else:
        text = ""

    if any(kw in text for kw in ["chấm bài", "đáp án", "lời giải"]):
        state["intent"] = Intent.EXAM_PRACTICE
    elif any(kw in text for kw in ["lỗi", "lỗi sai", "phân tích lỗi"]):
        state["intent"] = Intent.REVIEW_MISTAKE
    elif any(kw in text for kw in ["tiền xử lý", "lấy đáp án"]):
        state["intent"] = Intent.PREPROCESS
    elif any(kw in text for kw in ["gợi ý", "hint", "trợ giúp", "help me", "hướng dẫn", "giải thích"]):
        state["intent"] = Intent.ASK_HINT
    elif any(kw in text for kw in ["phân tích", "năng lực", "analysis", "profile", "thống kê", "dashboard", "tiến độ"]):
        state["intent"] = Intent.VIEW_ANALYSIS
    else:
        state["intent"] = Intent.UNKNOWN
    
    return state

def route_by_intent(state: AgentState) -> str:
    """
    Route the request to the appropriate agent.
    Args:
        - state: AgentState, state của Agent
    """
    routes = {
        Intent.ASK_HINT: "teacher_hint",
        Intent.REVIEW_MISTAKE: "build_review",
        Intent.EXAM_PRACTICE: "exam_practice_router",
        Intent.GRADE_SUBMISSION: "exam_practice_router",
        Intent.UPDATE_PRACTICE: "exam_practice_router",
        Intent.PREPROCESS: "preprocess_router",
        Intent.VIEW_ANALYSIS: "build_analysis",
    }
    return routes.get(state["intent"], "clarification_loop")
