from master.agents.common.message import Intent
from master.agents.common.state import AgentState

def classify_intent(state: AgentState) -> AgentState:
    """
    Bộ phân loại Intent. Cho các Intent được định nghĩa bên trong.
    
    Args:
        - state: AgentState, state của Agent
    """

    request = state["request"]
    metadata = request.metadata or {}

    if metadata.get("intent"):
        state["intent"] = Intent(metadata["intent"])
    else:
        # Keyword-based fallback
        text = request.content.lower()
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
        Intent.PREPROCESS: "preprocess_router",
        Intent.VIEW_ANALYSIS: "build_analysis",
    }
    return routes.get(state["intent"], "clarification_loop")