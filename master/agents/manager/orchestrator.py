"""
Orchestrator của Manager Agent. Không cần LLM, chỉ dùng 
thuần LangGraph để gọi các nodes trong StateGraph.
"""
from __future__ import annotations

from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from master.agents.common.state import AgentState
from master.agents.manager.classify_intent import classify_intent, route_by_intent
from master.agents.common.message import Intent
from master.agents.teacher import TeacherAgent
from master.agents.verifier import VerifierAgent

# ===========================================
# NODEs
# ===========================================

def preprocess_node(state: AgentState) -> AgentState:
    """
    Node tiền xử lý. Chuẩn hóa các state đầu vào của các agent. 
    Set các default values nếu còn thiếu.

    Args:
        - state: AgentState, state của Agent
    Returns:
        - AgentState, state của Agent sau khi tiền xử lý.
    """
    return {
        **state,
        "round": state.get("round", 0),
        "max_round": state.get("max_round", 2),
        "phase": state.get("phase", "draft"),
        "debate_outputs": state.get("debate_outputs", []),
        "questions": state.get("questions", []),
        "student_answers": state.get("student_answers", []),
    }

def selection_questions_node(state: AgentState) -> AgentState:
    """
    Node chọn câu hỏi. Chọn câu hỏi từ câu hỏi đã làm.
    """
    #TODO: Hiện tại chỉ trả về đơn giản, sau này sẽ triển khai chung với Adaptive Agent
    #       lựa chọn các câu hỏi bằng BKT/IRT/KC + LLMs
    return {
        **state,
        "selected_questions": state.get("selected_questions", []),
    }

def teacher_node(state: AgentState) -> AgentState:
    """
    Node giảng viên. Giảng viên sẽ giảng các câu hỏi đã chọn.
    """
    teacher: TeacherAgent = TeacherAgent()

    debate_state = {
        "phase": "draft",
        "questions": state.get("selected_questions") or state.get("questions"),
        "student_answers": state.get("student_answers"),
        "round": state.get("round", 0),
        "max_round": state.get("max_round", 2),
    }

    result = teacher.graph.invoke(debate_state)

    return {
        **state,
        "solutions": result.get("solutions"),
        "debate_outputs": result.get("outputs", []),
        "phase": "verify",
    }

# ===========================================
# BUILD WORKFLOW GRAPHS
# ===========================================

def _build_tutoring_graph() -> StateGraph:
    """
    Xây dựng Tutoring Pipeline dùng để show hint / review mistake / explain / analysis theo câu.
    """

def _build_content_pipeline_graph() -> StateGraph:
    """
    Xây dựng StateGraph cho pipeline cào đề, làm sạch dữ liệu, tách câu hỏi và 
    sinh ra đáp án cho từng câu rồi lưu vô DB.
    """

    pass

def _build_adaptive_graph() -> StateGraph:
    """
    Xây dựng StateGraph cho pipeline thu thập và xây dựng LearnerProfile
    bằng các thuật toán BKT/IRT/KC + LLMs để có thể lựa chọn ra các câu hỏi phù
    hợp giúp người học nâng cao trình độ.
    """

    pass

def _build_solution_gen_graph() -> StateGraph:
    """
    Xây dựng StateGraph cho pipeline sinh lời giải cho các câu hỏi.
    """

    pass

def _build_analysis_graph() -> StateGraph:
    """
    Xây dựng StateGraph cho pipeline phân tích năng lực và tiến độ học tập của người học.
    """

    pass