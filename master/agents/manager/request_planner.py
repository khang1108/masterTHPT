"""Central request planner for manager-level orchestration.

The planner is intentionally deterministic in this first iteration. It turns a
hydrated request + context into a compact ``ExecutionPlan`` that the manager
can execute while still reusing legacy specialist pipelines underneath.
"""

from __future__ import annotations

from typing import Any

from master.agents import BaseAgent
from master.agents.common.execution_plan import (
    ExecutionAgent,
    ExecutionPlan,
    ExecutionStep,
    FinalResponseMode,
)
from master.agents.common.message import Intent
from master.agents.common.state import AgentState
from master.agents.common.tools import ToolsRegistry


class RequestPlannerAgent(BaseAgent):
    """Build a short-lived execution plan for one inbound request."""

    def __init__(self) -> None:
        super().__init__(agent_role="RequestPlanner")
        self.system_prompt = (
            "You are the central orchestration planner. Build compact, explicit "
            "execution plans and never expose chain-of-thought."
        )

    @staticmethod
    def _normalize_intent(intent: Intent | str | None) -> Intent:
        """Coerce raw intent values into the normalized enum."""

        if isinstance(intent, Intent):
            return intent
        try:
            return Intent(str(intent))
        except ValueError:
            return Intent.UNKNOWN

    @staticmethod
    def _request_has_file_context(state: AgentState) -> bool:
        """Detect whether the current request likely needs parser involvement."""

        request = state.get("request")
        if request is None:
            return False
        metadata = request.metadata or {}
        if any(metadata.get(key) for key in ("file_path", "parser_file_path", "local_file_path")):
            return True
        return bool(request.file_urls)

    @staticmethod
    def _build_goal(intent: Intent, state: AgentState) -> str:
        """Produce a compact goal statement for logs and specialist context."""

        request = state.get("request")
        active_plan = state.get("active_plan")
        if intent == Intent.ASK_HINT:
            return "Tạo gợi ý vừa đủ để học sinh tự làm tiếp."
        if intent == Intent.REVIEW_MISTAKE:
            return "Phân tích lỗi sai và đưa cách sửa đúng, có kiểm tra lại."
        if intent == Intent.PREPROCESS:
            return "Trích xuất đề và xây answer key đáng tin cậy."
        if intent in {
            Intent.EXAM_PRACTICE,
            Intent.GRADE_SUBMISSION,
            Intent.UPDATE_PRACTICE,
            Intent.VIEW_ANALYSIS,
        }:
            if active_plan is not None and active_plan.goal:
                return f"Điều phối adaptive theo active plan: {active_plan.goal}"
            if request and isinstance(request.metadata.get("learning_goal"), str):
                return str(request.metadata["learning_goal"]).strip() or "Điều phối adaptive."
            return "Điều phối adaptive để cập nhật hồ sơ và chọn lượt luyện tiếp theo."
        return "Điều phối request theo workflow phù hợp nhất."

    def _build_steps(self, intent: Intent, state: AgentState) -> tuple[list[ExecutionStep], bool, FinalResponseMode]:
        """Translate a normalized intent into ordered execution steps."""

        has_file_context = self._request_has_file_context(state)
        if intent == Intent.PREPROCESS and has_file_context:
            return (
                [
                    ExecutionStep(
                        step_id="parser-1",
                        agent=ExecutionAgent.PARSER,
                        objective="Trích xuất đề từ file đầu vào thành parser_output ổn định.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("parser"),
                        metadata={"dispatch": "grading_pipeline", "pipeline_agents": ["parser", "teacher", "verifier"]},
                    ),
                    ExecutionStep(
                        step_id="teacher-1",
                        agent=ExecutionAgent.TEACHER,
                        objective="Sinh đáp án chuẩn và đánh giá sơ bộ cho từng câu hỏi đã parse.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("teacher"),
                        metadata={"dispatch": "grading_pipeline", "pipeline_agents": ["teacher", "verifier"]},
                    ),
                    ExecutionStep(
                        step_id="verifier-1",
                        agent=ExecutionAgent.VERIFIER,
                        objective="Kiểm tra lại answer key và feedback preprocess trước khi trả kết quả.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("verifier"),
                        stop_on_complete=True,
                        metadata={"dispatch": "grading_pipeline", "pipeline_agents": ["verifier"]},
                    ),
                ],
                True,
                FinalResponseMode.PREPROCESS_RESULT,
            )
        if intent == Intent.ASK_HINT:
            return (
                [
                    ExecutionStep(
                        step_id="teacher-1",
                        agent=ExecutionAgent.TEACHER,
                        objective="Đưa gợi ý theo tầng, không giải toàn bộ bài toán.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("teacher"),
                        stop_on_complete=True,
                        metadata={"dispatch": "grading_pipeline", "pipeline_agents": ["teacher"]},
                    )
                ],
                False,
                FinalResponseMode.HINT,
            )
        if intent == Intent.REVIEW_MISTAKE:
            return (
                [
                    ExecutionStep(
                        step_id="teacher-1",
                        agent=ExecutionAgent.TEACHER,
                        objective="Phân tích lỗi sai và dựng lời giải/sửa lỗi ban đầu.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("teacher"),
                        metadata={"dispatch": "grading_pipeline", "pipeline_agents": ["teacher", "verifier"]},
                    ),
                    ExecutionStep(
                        step_id="verifier-1",
                        agent=ExecutionAgent.VERIFIER,
                        objective="Kiểm tra lại phân tích lỗi sai và kết luận cuối.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("verifier"),
                        stop_on_complete=True,
                        metadata={"dispatch": "grading_pipeline", "pipeline_agents": ["verifier"]},
                    ),
                ],
                True,
                FinalResponseMode.REVIEW,
            )
        if intent in {
            Intent.EXAM_PRACTICE,
            Intent.GRADE_SUBMISSION,
            Intent.UPDATE_PRACTICE,
            Intent.VIEW_ANALYSIS,
        }:
            return (
                [
                    ExecutionStep(
                        step_id="adaptive-1",
                        agent=ExecutionAgent.ADAPTIVE,
                        objective="Cập nhật learner profile và chọn bộ câu hỏi phù hợp cho lượt tiếp theo.",
                        allowed_tools=ToolsRegistry.get_tool_names_for_role("adaptive"),
                        stop_on_complete=True,
                        metadata={"dispatch": "adaptive"},
                    )
                ],
                False,
                FinalResponseMode.ADAPTIVE_RECOMMENDATION,
            )
        return ([], False, FinalResponseMode.FALLBACK)

    def build_plan(self, state: AgentState) -> tuple[ExecutionPlan | None, str]:
        """Build an execution plan plus a compact planner summary."""

        intent = self._normalize_intent(state.get("intent"))
        goal = self._build_goal(intent, state)
        steps, requires_verification, final_response_mode = self._build_steps(intent, state)
        if not steps:
            return None, "Planner không tìm được workflow phù hợp, sẽ trả fallback response."

        planner_summary = (
            f"Planner chọn workflow {intent.value} với {len(steps)} bước; "
            f"final_response_mode={final_response_mode.value}; "
            f"requires_verification={requires_verification}."
        )
        plan = ExecutionPlan(
            intent=intent.value,
            goal=goal,
            steps=steps,
            current_step_index=0,
            requires_verification=requires_verification,
            final_response_mode=final_response_mode,
            metadata={
                "planner": "request_planner",
                "step_agents": [step.agent.value for step in steps],
                "has_file_context": self._request_has_file_context(state),
            },
        )
        return plan, planner_summary

    async def run(self, input: str) -> str:
        """Legacy string entrypoint kept only to satisfy the base contract."""

        return str(input)

    async def execute_step(
        self,
        state: dict[str, Any],
        *,
        step: Any | None = None,
    ) -> dict[str, Any]:
        """Expose the structured planner contract expected by the manager."""

        plan, planner_summary = self.build_plan(state)
        return {
            "execution_plan": plan,
            "planner_summary": planner_summary,
        }
