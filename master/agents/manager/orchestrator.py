"""Orchestrator trung tâm cho luồng MVP hiện tại.

Luồng nghiệp vụ đang dùng:

- ``PREPROCESS``:
  parser tách đề từ PDF/image -> teacher/verifier sinh đáp án chuẩn.
- ``ASK_HINT``:
  user bấm nút Hint ở một câu -> teacher trả về gợi ý ngắn.
- ``REVIEW_MISTAKE``:
  user bấm Explain ở một câu -> teacher/verifier giải thích lỗi sai hoặc lời giải.
- ``VIEW_ANALYSIS`` / ``EXAM_PRACTICE`` / ``UPDATE_PRACTICE``:
  adaptive cập nhật hồ sơ học sinh, quyết định nên dùng câu cũ hay sinh câu mới,
  rồi trả về danh sách câu hỏi gợi ý tiếp theo.

Trong MVP này, nhánh adaptive không tiếp tục gọi teacher/verifier để giải trước
các câu được gợi ý. Orchestrator chỉ dừng ở bước chọn/sinh câu hỏi phù hợp.
"""

from __future__ import annotations

import inspect
from typing import Any

from langgraph.graph import END, START, StateGraph

from master.agents.common.agent_logging import log_agent_event
from master.agents.adaptive import AdaptiveAgent, AdaptiveDBTools
from master.agents.common.execution_plan import (
    ExecutionAgent,
    ExecutionPlan,
    ReplanSignal,
    StepResult,
    StepStatus,
)
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.message import (
    ExamQuestion,
    Intent,
    MessageRequest,
    MessageResponse,
    StudentAnswer,
)
from master.agents.common.state import AgentState
from master.agents.manager.classify_intent import classify_intent
from master.agents.manager.request_planner import RequestPlannerAgent


def preprocess_node(state: AgentState) -> AgentState:
    """Chuẩn hóa state đầu vào trước khi bắt đầu route theo intent."""

    request = state.get("request")
    log_agent_event(
        "manager",
        "preprocess:start",
        state=state,
        request=request,
        mode="agent_node",
    )
    agent_trail = list(state.get("agent_trail") or [])
    if "manager" not in agent_trail:
        agent_trail.append("manager")

    exam_id = state.get("exam_id")
    if request is not None and not exam_id:
        exam_id = request.exam_id

    normalized_state = {
        **state,
        "exam_id": exam_id,
        "round": state.get("round", 0),
        "max_round": state.get("max_round", 2),
        "phase": state.get("phase", "draft"),
        "debate_outputs": state.get("debate_outputs", []),
        "questions": state.get("questions", []),
        "student_answers": state.get("student_answers", []),
        "parser_output": state.get("parser_output")
        or (request.parser_output if request is not None else []),
        "selected_questions": state.get("selected_questions", []),
        "profile_updates": state.get("profile_updates", {}),
        "execution_plan": state.get("execution_plan"),
        "step_results": state.get("step_results", []),
        "planner_summary": state.get("planner_summary"),
        "tool_trace": state.get("tool_trace", []),
        "allowed_tools": state.get("allowed_tools", []),
        "needs_replan": bool(state.get("needs_replan", False)),
        "replan_count": int(state.get("replan_count", 0) or 0),
        "agent_trail": agent_trail,
    }
    log_agent_event(
        "manager",
        "preprocess:done",
        state=normalized_state,
        request=request,
        mode="progress",
    )
    return normalized_state


async def _run_teacher_verifier_solution_pipeline(
    *,
    request: MessageRequest,
    learner_profile,
    exam_id: str | None,
    questions: list[ExamQuestion],
    student_answers: list[StudentAnswer],
    max_rounds: int,
    confidence_threshold: float,
    thread_id: str,
) -> AgentState:
    """Nhánh dự phòng cho tương lai: teacher/verifier giải sẵn câu hỏi mới.

    MVP hiện tại chưa dùng nhánh này trong graph chính, nhưng vẫn giữ lại để sau
    này có thể bật chế độ "pre-compute lời giải" cho bộ câu hỏi adaptive.
    """

    log_agent_event(
        "manager",
        "solution_pipeline:invoke",
        request=request,
        extra={
            "selected_questions": len(questions),
            "student_answers": len(student_answers),
            "max_rounds": max_rounds,
            "confidence_threshold": confidence_threshold,
            "thread_id": thread_id,
        },
        mode="agent_node",
    )
    from master.agents.server import (
        _get_teacher_agent,
        _get_verifier_agent,
        build_pipeline_graph,
    )

    teacher = await _get_teacher_agent()
    verifier = await _get_verifier_agent()
    pipeline_graph = build_pipeline_graph(teacher, verifier)

    solution_state = AgentState(
        request=request,
        learner_profile=learner_profile,
        exam_id=exam_id,
        questions=questions,
        student_answers=student_answers,
        debate_outputs=[],
        _verdicts=[],
        round=0,
        max_round=max_rounds,
        _teacher_confidence_threshold=confidence_threshold,
        _thread_id=thread_id,
    )

    final_state = await pipeline_graph.ainvoke(
        solution_state,
        config=build_langsmith_invoke_config(
            run_name="ManagerOrchestrator.solution_pipeline",
            agent_role="manager",
            thread_id=thread_id,
            extra_tags=["manager", "solution-pipeline", "teacher", "verifier"],
            extra_metadata={
                "exam_id": exam_id,
                "selected_question_count": len(questions),
            },
        ),
    )
    log_agent_event(
        "manager",
        "solution_pipeline:completed",
        state=final_state,
        request=request,
        extra={"selected_questions": len(questions)},
        mode="completed",
    )
    return final_state


class ManagerOrchestrator:
    """Điều phối parser, teacher, verifier và adaptive trong một graph."""

    def __init__(
        self,
        *,
        repository: AdaptiveDBTools | None = None,
        adaptive_agent: AdaptiveAgent | None = None,
        request_planner: RequestPlannerAgent | None = None,
    ) -> None:
        self.repository = repository or AdaptiveDBTools()
        self.adaptive_agent = adaptive_agent or AdaptiveAgent(repository=self.repository)
        self.request_planner = request_planner or RequestPlannerAgent()
        # Chỉ setup Parser khi execution plan thật sự cần tới.
        # Cách này giữ thay đổi nhỏ, không làm manager khởi động nặng hơn.
        self._parser_agent = None
        self.graph = self._build_graph()
        log_agent_event(
            "manager",
            "initialized",
            extra={
                "repository": type(self.repository).__name__,
                "adaptive_agent": type(self.adaptive_agent).__name__,
                "request_planner": type(self.request_planner).__name__,
            },
            mode="completed",
        )

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        """Await values only when the callee returned an awaitable."""

        if inspect.isawaitable(value):
            return await value
        return value

    async def _get_parser_agent(self):
        """Khởi tạo muộn ParserAgent để step parser chạy độc lập trong manager."""

        if self._parser_agent is None:
            from master.agents.parser.parser import ParserAgent

            self._parser_agent = ParserAgent()
            await self._parser_agent.setup()
        return self._parser_agent

    @staticmethod
    def _append_agent_trail(state: AgentState, *agents: str) -> list[str]:
        """Thêm tên agent vào trail theo đúng thứ tự đã chạy, không lặp."""

        trail = list(state.get("agent_trail") or [])
        for agent in agents:
            if agent and agent not in trail:
                trail.append(agent)
        return trail

    @staticmethod
    def _normalize_history_student_answers(raw_answers: Any) -> list[StudentAnswer]:
        """Chuẩn hóa dữ liệu bài làm từ history về cùng schema ``StudentAnswer``."""

        if raw_answers is None:
            return []

        if isinstance(raw_answers, dict):
            normalized: list[StudentAnswer] = []
            for question_id, value in raw_answers.items():
                if not question_id:
                    continue
                if isinstance(value, dict):
                    payload = {"question_id": question_id, **value}
                else:
                    payload = {"question_id": question_id, "student_answer": value}
                normalized.append(StudentAnswer.model_validate(payload))
            return normalized

        if isinstance(raw_answers, list):
            normalized = []
            for item in raw_answers:
                if isinstance(item, dict):
                    normalized.append(StudentAnswer.model_validate(item))
            return normalized

        return []

    @staticmethod
    def _extract_review_student_answer(request: MessageRequest | None) -> str | None:
        """Lấy đáp án học sinh từ payload Explain/review-mistake kiểu cũ."""

        if request is None:
            return None

        extra_answer = getattr(request, "student_ans", None)
        if extra_answer is None:
            extra_answer = request.metadata.get("student_ans") if request.metadata else None
        if extra_answer is None:
            return None
        return str(extra_answer)

    @staticmethod
    def _extract_file_path(request: MessageRequest | None) -> str | None:
        """Tìm đường dẫn file đầu tiên mà parser có thể xử lý."""

        # MVP hiện tại cho phép backend truyền file qua metadata hoặc file_urls.
        # Orchestrator chỉ cần tìm ra một path hợp lệ để chuyển cho parser.

        if request is None:
            return None

        metadata = request.metadata or {}
        for key in ("file_path", "parser_file_path", "local_file_path"):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for item in request.file_urls:
            if isinstance(item, str) and item.strip():
                return item.strip()

        return None

    @staticmethod
    def _normalize_execution_plan(value: Any) -> ExecutionPlan | None:
        """Coerce loose plan payloads into the canonical execution-plan model."""

        if value is None:
            return None
        if isinstance(value, ExecutionPlan):
            return value
        if isinstance(value, dict):
            return ExecutionPlan.model_validate(value)
        return None

    @staticmethod
    def _normalize_step_results(value: Any) -> list[StepResult]:
        """Coerce optional result payloads into ``StepResult`` objects."""

        if not isinstance(value, list):
            return []
        normalized: list[StepResult] = []
        for item in value:
            if isinstance(item, StepResult):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(StepResult.model_validate(item))
        return normalized

    @staticmethod
    def _step_summary(step_output: dict[str, Any]) -> str:
        """Create a compact, chain-of-thought-safe step summary for logs/debug."""

        if step_output.get("feedback"):
            return str(step_output["feedback"]).strip()
        if step_output.get("selected_question_count") is not None:
            return f"selected_questions={step_output['selected_question_count']}"
        if step_output.get("response_type"):
            return str(step_output["response_type"])
        return "Step completed."

    def _build_step_result(
        self,
        *,
        step_id: str,
        agent: ExecutionAgent,
        step_output: dict[str, Any],
        tool_calls_used: list[str],
        replan_signal: ReplanSignal | None = None,
        status: StepStatus = StepStatus.COMPLETED,
    ) -> StepResult:
        """Create a normalized step-result record for observability/debug."""

        return StepResult(
            step_id=step_id,
            agent=agent,
            step_status=status,
            summary=self._step_summary(step_output),
            step_output=step_output,
            tool_calls_used=list(tool_calls_used),
            replan_signal=replan_signal,
        )

    @staticmethod
    def _remaining_plan_steps(plan: ExecutionPlan | None) -> int:
        """Return the number of steps left from the current execution index."""

        if plan is None:
            return 0
        return max(0, len(plan.steps) - int(plan.current_step_index or 0))

    async def _hydrate_backend_context_node(self, state: AgentState) -> AgentState:
        """Nạp thêm dữ liệu từ Mongo nếu backend chỉ gửi ID.

        Mục tiêu của bước này:
        - bổ sung ``student_answers`` từ history nếu request chưa có
        - bổ sung ``questions`` từ question_id / exam_id để các agent sau dùng
        - hợp nhất lại request thành một payload đầy đủ hơn cho các node sau
        """

        request = state.get("request")
        if request is None:
            return state
        
        log_agent_event(
            "manager",
            "hydrate:start",
            state=state,
            request=request,
            mode="agent_node",
        )

        resolved_student_id = request.student_id or request.user_id
        resolved_exam_id = state.get("exam_id") or request.exam_id
        metadata = dict(request.metadata or {})
        active_plan = state.get("active_plan")

        history_record = state.get("history_record")

        raw_student_answers = state.get("student_answers") or request.student_answers
        legacy_student_answers = getattr(request, "student_ans", None)
        if not raw_student_answers and isinstance(legacy_student_answers, list):
            raw_student_answers = legacy_student_answers

        student_answers: list[StudentAnswer] = []
        for ans in (raw_student_answers or []):
            payload = ans
            if isinstance(ans, dict) and "_id" in ans:
                # Ép kiểu ObjectId sang str trước khi đưa cho Pydantic.
                payload = {**ans, "_id": str(ans["_id"])}
            student_answers.append(StudentAnswer.model_validate(payload))

        questions_from_state = []
        for q in (state.get("questions") or []):
            if isinstance(q, dict):
                # Ép kiểu ObjectId sang str trước khi đưa cho Pydantic
                if "_id" in q: q["_id"] = str(q["_id"])
                if "user_id" in q: q["user_id"] = str(q["user_id"])
            questions_from_state.append(ExamQuestion.model_validate(q))
        questions = questions_from_state

        if not student_answers:
            review_student_answer = self._extract_review_student_answer(request)
            if request.question_id and review_student_answer:
                student_answers = [
                    StudentAnswer(
                        question_id=request.question_id,
                        student_answer=review_student_answer,
                    )
                ]

        if history_record is None and not student_answers and resolved_student_id:
            history_id = metadata.get("history_id")
            try:
                if history_id:
                    history_record = await self.repository.get_history_by_id(str(history_id))
                if history_record is None:
                    history_record = await self.repository.get_latest_history(
                        user_id=resolved_student_id,
                        exam_id=resolved_exam_id,
                    )
            except RuntimeError:
                log_agent_event(
                    "manager",
                    "hydrate:history_lookup_failed",
                    request=request,
                    extra={"history_id": history_id, "exam_id": resolved_exam_id},
                    mode="warning",
                )
                history_record = None

        if history_record and not student_answers:
            student_answers = self._normalize_history_student_answers(
                history_record.get("student_ans")
            )
            raw_history_id = history_record.get("_id")
            if raw_history_id is not None:
                metadata.setdefault("history_id", str(raw_history_id))

        student_lookup_identity = request.user_id or resolved_student_id
        student_record = None
        if student_lookup_identity:
            try:
                student_record = await self.repository.get_student_profile(student_lookup_identity)
            except RuntimeError:
                log_agent_event(
                    "manager",
                    "hydrate:student_lookup_failed",
                    request=request,
                    extra={"student_lookup_identity": student_lookup_identity},
                    mode="warning",
                )
                student_record = None

        learner_profile = state.get("learner_profile")
        if learner_profile is None and student_lookup_identity:
            try:
                # Adaptive phụ thuộc trực tiếp vào learner_profile.
                # Nếu bỏ sót field này trong hydrate thì nhánh adaptive sẽ coi như
                # chưa có hồ sơ học sinh và trả về ``selected_questions=[]``.
                learner_profile = await self.repository.get_learner_profile(student_lookup_identity)
            except RuntimeError:
                log_agent_event(
                    "manager",
                    "hydrate:learner_profile_lookup_failed",
                    request=request,
                    extra={"student_lookup_identity": student_lookup_identity},
                    mode="warning",
                )
                learner_profile = None

        if student_record is not None:
            learning_goal = student_record.get("learning_goal")
            if isinstance(learning_goal, str) and learning_goal.strip():
                metadata.setdefault("learning_goal", learning_goal.strip())

            student_grade = student_record.get("grade")
            if student_grade is not None:
                metadata.setdefault("student_grade", str(student_grade))

            school = student_record.get("school")
            if isinstance(school, str) and school.strip():
                metadata.setdefault("school", school.strip())

        plan_lookup_user_id = request.user_id or resolved_student_id
        """Sinh plan lookup user id tương tự như student lookup id để tăng khả năng tìm được plan phù hợp với người dùng, 
        dù backend có thể chỉ gửi student_id hoặc user_id."""
        if active_plan is None and plan_lookup_user_id:
            try:
                active_plan = await self.repository.get_active_shared_plan(plan_lookup_user_id)
            except RuntimeError:
                log_agent_event(
                    "manager",
                    "hydrate:active_plan_lookup_failed",
                    request=request,
                    extra={"plan_lookup_user_id": plan_lookup_user_id},
                    mode="warning",
                )
                active_plan = None

        if active_plan is not None:
            if active_plan.goal:
                metadata.setdefault("learning_goal", active_plan.goal)
            if active_plan.target_exam:
                metadata.setdefault("target_exam", active_plan.target_exam)
            if active_plan.target_exam_name:
                metadata.setdefault("target_exam_name", active_plan.target_exam_name)
            if active_plan.target_exam_type:
                metadata.setdefault("target_exam_type", active_plan.target_exam_type)

            exam_matrix_summary = active_plan.metadata.get("exam_matrix_summary")
            if isinstance(exam_matrix_summary, str) and exam_matrix_summary.strip():
                metadata.setdefault("exam_matrix_summary", exam_matrix_summary.strip())
            elif active_plan.summary:
                metadata.setdefault("exam_matrix_summary", active_plan.summary)

        if not questions:
            question_ids: list[str] = []
            if request.question_id:
                question_ids.append(request.question_id)
            question_ids.extend(
                answer.question_id for answer in student_answers if answer.question_id
            )

            deduped_question_ids: list[str] = []
            seen_question_ids: set[str] = set()
            for question_id in question_ids:
                if not question_id or question_id in seen_question_ids:
                    continue
                seen_question_ids.add(question_id)
                deduped_question_ids.append(question_id)

            try:
                if deduped_question_ids:
                    questions = await self.repository.get_questions(
                        question_ids=deduped_question_ids,
                        limit=max(len(deduped_question_ids), 1),
                    )

                if not questions and resolved_exam_id:
                    requested_limit = metadata.get("question_limit") or metadata.get("limit") or 100
                    try:
                        limit = max(1, int(requested_limit))
                    except (TypeError, ValueError):
                        limit = 100
                    questions = await self.repository.get_questions(
                        exam_id=resolved_exam_id,
                        limit=limit,
                    )
            except RuntimeError:
                log_agent_event(
                    "manager",
                    "hydrate:question_lookup_failed",
                    request=request,
                    extra={
                        "exam_id": resolved_exam_id,
                        "question_ids": len(deduped_question_ids),
                    },
                    mode="warning",
                )
                questions = []

        normalized_request = request.model_copy(
            update={
                "student_id": resolved_student_id,
                "exam_id": resolved_exam_id,
                "metadata": metadata,
                "student_answers": student_answers or request.student_answers,
            }
        )

        hydrated_state = {
            **state,
            "request": normalized_request,
            "exam_id": resolved_exam_id,
            "learner_profile": learner_profile,
            "student_answers": student_answers,
            "questions": questions,
            "history_record": history_record,
            "active_plan": active_plan,
        }
        log_agent_event(
            "manager",
            "hydrate:done",
            state=hydrated_state,
            request=normalized_request,
            extra={
                "history_found": history_record is not None,
                "resolved_student_id": resolved_student_id,
                "has_learner_profile": learner_profile is not None,
                "has_active_plan": active_plan is not None,
            },
            mode="progress",
        )
        return hydrated_state

    async def _grading_node(self, state: AgentState) -> AgentState:
        """Xử lý nhóm intent dùng parser/teacher/verifier.

        Nhóm này bao gồm:
        - ``PREPROCESS``: trích xuất đề + sinh answer key
        - ``ASK_HINT``: gợi ý cho một câu
        - ``REVIEW_MISTAKE``: giải thích/lời giải cho một câu
        """

        request = state.get("request")
        if request is None:
            return state
        log_agent_event(
            "manager",
            "grading:start",
            state=state,
            request=request,
            mode="agent_node",
        )

        # ``run_superstep`` là wrapper async của pipeline cũ trong ``server.py``.
        # Orchestrator vẫn tái sử dụng nó để giảm số chỗ phải thay đổi trong MVP.
        from master.agents.server import run_superstep

        metadata = request.metadata or {}
        try:
            max_rounds = max(1, int(metadata.get("max_rounds", state.get("max_round", 2))))
        except (TypeError, ValueError):
            max_rounds = 2

        try:
            confidence_threshold = float(
                metadata.get("confidence_threshold", state.get("_teacher_confidence_threshold", 0.9))
            )
        except (TypeError, ValueError):
            confidence_threshold = 0.9

        file_path = self._extract_file_path(request)
        parser_batch_size = metadata.get("parser_batch_size")

        if file_path and not (request.student_answers or state.get("student_answers")):
            # Trường hợp parser: backend mới gửi file/path, chưa có bài làm.
            pipeline_result = await run_superstep(
                request
            )
            agent_trail = self._append_agent_trail(state, "parser", "teacher", "verifier")
            grading_mode = "parser_pipeline"
        else:
            # Trường hợp Hint / Explain: request đã đủ context hoặc đã hydrate xong.
            normalized_request = request.model_copy(
                update={"student_answers": state.get("student_answers") or request.student_answers}
            )
            pipeline_result = await run_superstep(
                request=normalized_request,
            )
            if state.get("intent") == Intent.ASK_HINT:
                agent_trail = self._append_agent_trail(state, "teacher")
            else:
                agent_trail = self._append_agent_trail(state, "teacher", "verifier")
            grading_mode = "direct_pipeline"

        response = (
            pipeline_result.get("response")
            if isinstance(pipeline_result, dict)
            else pipeline_result
        )
        teacher_feedback = (
            pipeline_result.get("teacher_feedback", [])
            if isinstance(pipeline_result, dict)
            else state.get("teacher_feedback", [])
        )
        verifier_feedback = (
            pipeline_result.get("verifier_feedback", [])
            if isinstance(pipeline_result, dict)
            else state.get("verifier_feedback", [])
        )
        debate_outputs = (
            pipeline_result.get("debate_outputs", [])
            if isinstance(pipeline_result, dict)
            else state.get("debate_outputs", [])
        )

        graded_state = {
            **state,
            "request": pipeline_result.get("request", request)
            if isinstance(pipeline_result, dict)
            else request,
            "response": response,
            "parser_output": (
                pipeline_result.get("request").parser_output
                if isinstance(pipeline_result, dict)
                and pipeline_result.get("request") is not None
                and hasattr(pipeline_result.get("request"), "parser_output")
                else state.get("parser_output")
            ),
            "teacher_feedback": teacher_feedback,
            "verifier_feedback": verifier_feedback,
            "debate_outputs": debate_outputs,
            "agent_trail": agent_trail,
        }
        log_agent_event(
            "manager",
            "grading:done",
            state=graded_state,
            request=request,
            extra={
                "grading_mode": grading_mode,
                "confidence_threshold": confidence_threshold,
                "max_rounds": max_rounds,
            },
            mode="completed",
        )
        return graded_state

    async def _parser_node(self, state: AgentState) -> AgentState:
        """Chạy Parser như một step độc lập trước khi vào pipeline chấm cũ.

        Mục tiêu của bước nối tối thiểu:
        - manager thực sự gọi Parser ở step ``parser-1``
        - lưu ``parser_output`` vào state/request
        - step kế tiếp vẫn có thể tái sử dụng pipeline Teacher/Verifier hiện tại
        """

        request = state.get("request")
        if request is None:
            return state

        log_agent_event(
            "manager",
            "parser:start",
            state=state,
            request=request,
            mode="agent_node",
        )

        file_path = self._extract_file_path(request)
        if not file_path:
            log_agent_event(
                "manager",
                "parser:skip_no_file",
                state=state,
                request=request,
                mode="progress",
            )
            return state

        parser_request = request.model_copy(update={"file_path": file_path})
        parser_agent = await self._get_parser_agent()
        parser_state = await self._maybe_await(
            parser_agent.parser(
                AgentState(
                    request=parser_request,
                    parser_output=state.get("parser_output"),
                )
            )
        )

        parsed_request = parser_state.get("request") if isinstance(parser_state, dict) else None
        if parsed_request is None:
            log_agent_event(
                "manager",
                "parser:missing_request",
                state=state,
                request=parser_request,
                mode="progress",
            )
            return state

        next_state = {
            **state,
            "request": parsed_request,
            "exam_id": parsed_request.exam_id or state.get("exam_id"),
            "parser_output": parsed_request.parser_output or [],
            "agent_trail": self._append_agent_trail(state, "parser"),
        }
        log_agent_event(
            "manager",
            "parser:done",
            state=next_state,
            request=parsed_request,
            extra={
                "parsed_question_count": len(parsed_request.parser_output or []),
                "exam_id": parsed_request.exam_id,
            },
            mode="completed",
        )
        return next_state

    async def _adaptive_node(self, state: AgentState) -> AgentState:
        """Chạy adaptive để cập nhật hồ sơ và gợi ý bài tiếp theo.

        Adaptive trong MVP hiện tại có thể:
        - cập nhật learner profile từ lịch sử làm bài
        - quyết định nên chọn câu hỏi cũ hay sinh câu hỏi mới
        - trả về ``selected_questions`` phù hợp để frontend/backend dùng tiếp

        Node này phải là async vì AdaptiveAgent hiện chạy bằng ``ainvoke`` và
        gọi thẳng repository Motor. Giữ toàn bộ nhánh adaptive trên cùng event
        loop với manager sẽ tránh lỗi lệch loop khi save/load learner profile.
        """

        request = state.get("request")
        if request is None:
            return state
        log_agent_event(
            "manager",
            "adaptive:start",
            state=state,
            request=request,
            mode="agent_node",
        )

        metadata = dict(request.metadata or {})
        intent = state.get("intent")

        if intent in {
            Intent.UPDATE_PRACTICE,
            Intent.EXAM_PRACTICE,
            Intent.GRADE_SUBMISSION,
            Intent.VIEW_ANALYSIS,
        }:
            metadata.setdefault("generate_questions", True)
            metadata.setdefault("generation_limit", 3)
            metadata.setdefault("rag_context_limit", 8)
            metadata.setdefault("adaptive_mode", "llm_decide")

        normalized_request = request.model_copy(update={"metadata": metadata})
        adaptive_state = await self._maybe_await(
            self.adaptive_agent.run(
            {
                "request": normalized_request,
                "learner_profile": state.get("learner_profile"),
                "active_plan": state.get("active_plan"),
                "questions": state.get("questions", []),
                "student_answers": state.get("student_answers", []),
                "selected_questions": state.get("selected_questions", []),
                "profile_updates": state.get("profile_updates", {}),
                "planner_summary": state.get("planner_summary"),
                "allowed_tools": state.get("allowed_tools", []),
            }
        )
        )
        adaptive_result = {
            **state,
            "request": normalized_request,
            "learner_profile": adaptive_state.get("learner_profile"),
            "active_plan": adaptive_state.get("active_plan", state.get("active_plan")),
            "selected_questions": adaptive_state.get("selected_questions", []),
            "profile_updates": adaptive_state.get("profile_updates", {}),
            "plan_patch": adaptive_state.get("plan_patch"),
            "plan_proposal": adaptive_state.get("plan_proposal"),
            "agent_trail": self._append_agent_trail(state, "adaptive"),
        }
        log_agent_event(
            "manager",
            "adaptive:done",
            state=adaptive_result,
            request=normalized_request,
            extra={
                "generate_questions": metadata.get("generate_questions"),
            },
            mode="completed",
        )
        return adaptive_result

    async def _request_planner_node(self, state: AgentState) -> AgentState:
        """Build or rebuild a short-lived execution plan for the current request."""

        request = state.get("request")
        log_agent_event(
            "manager",
            "request_planner:start",
            state=state,
            request=request,
            mode="agent_node",
        )

        planner_patch = await self.request_planner.execute_step(state)
        execution_plan = self._normalize_execution_plan(planner_patch.get("execution_plan"))
        planner_summary = str(planner_patch.get("planner_summary") or "").strip() or None
        current_step = execution_plan.current_step() if execution_plan is not None else None
        prior_replan_count = int(state.get("replan_count", 0) or 0)
        if state.get("needs_replan"):
            prior_replan_count += 1
        planned_state = {
            **state,
            "execution_plan": execution_plan,
            "planner_summary": planner_summary,
            "allowed_tools": list(current_step.allowed_tools) if current_step is not None else [],
            "needs_replan": False,
            "replan_count": prior_replan_count,
        }
        log_agent_event(
            "manager",
            "request_planner:done",
            state=planned_state,
            request=request,
            extra={
                "has_execution_plan": execution_plan is not None,
                "planned_steps": len(execution_plan.steps) if execution_plan else 0,
                "current_step_index": execution_plan.current_step_index if execution_plan else None,
            },
            mode="completed",
        )
        return planned_state

    async def _specialist_execution_node(self, state: AgentState) -> AgentState:
        """Execute the current planned specialist step while reusing legacy nodes."""

        request = state.get("request")
        execution_plan = self._normalize_execution_plan(state.get("execution_plan"))
        current_step = execution_plan.current_step() if execution_plan is not None else None
        if request is None or execution_plan is None or current_step is None:
            return state

        log_agent_event(
            "manager",
            "specialist_execution:start",
            state=state,
            request=request,
            extra={
                "step_id": current_step.step_id,
                "agent": current_step.agent.value,
                "current_step_index": execution_plan.current_step_index,
            },
            mode="agent_node",
        )

        base_state = {
            **state,
            "allowed_tools": list(current_step.allowed_tools),
        }
        step_results = self._normalize_step_results(state.get("step_results"))
        tool_trace = list(state.get("tool_trace") or [])
        replan_signal: ReplanSignal | None = None

        if current_step.agent == ExecutionAgent.ADAPTIVE:
            specialist_state = await self._adaptive_node(base_state)
            execution_plan.current_step_index += 1
            step_output = {
                "selected_question_count": len(specialist_state.get("selected_questions") or []),
                "profile_update_keys": sorted(
                    self._ensure_dict(specialist_state.get("profile_updates")).keys()
                ),
                "response_type": execution_plan.final_response_mode.value,
            }
            step_results.append(
                self._build_step_result(
                    step_id=current_step.step_id,
                    agent=current_step.agent,
                    step_output=step_output,
                    tool_calls_used=current_step.allowed_tools,
                )
            )
            tool_trace.append(
                {
                    "step_id": current_step.step_id,
                    "agent": current_step.agent.value,
                    "allowed_tools": list(current_step.allowed_tools),
                }
            )
            next_state = {
                **specialist_state,
                "execution_plan": execution_plan,
                "step_results": step_results,
                "tool_trace": tool_trace,
                "needs_replan": False,
                "allowed_tools": list(execution_plan.current_step().allowed_tools)
                if execution_plan.current_step()
                else [],
            }
        elif current_step.agent == ExecutionAgent.PARSER:
            # Parser được tách thành step riêng.
            # Sau bước này, Teacher/Verifier vẫn chạy qua pipeline cũ nhưng sẽ
            # dùng lại ``request.parser_output`` nên không parse lại file nữa.
            specialist_state = await self._parser_node(base_state)
            execution_plan.current_step_index += 1
            step_output = {
                "parsed_question_count": len(specialist_state.get("parser_output") or []),
                "exam_id": specialist_state.get("exam_id"),
                "response_type": execution_plan.final_response_mode.value,
            }
            step_results.append(
                self._build_step_result(
                    step_id=current_step.step_id,
                    agent=current_step.agent,
                    step_output=step_output,
                    tool_calls_used=current_step.allowed_tools,
                )
            )
            tool_trace.append(
                {
                    "step_id": current_step.step_id,
                    "agent": current_step.agent.value,
                    "allowed_tools": list(current_step.allowed_tools),
                }
            )
            next_state = {
                **specialist_state,
                "execution_plan": execution_plan,
                "step_results": step_results,
                "tool_trace": tool_trace,
                "needs_replan": False,
                "allowed_tools": list(execution_plan.current_step().allowed_tools)
                if execution_plan.current_step()
                else [],
            }
        else:
            specialist_state = await self._grading_node(base_state)
            pipeline_agents: list[str] = list(current_step.metadata.get("pipeline_agents") or [])
            contiguous_steps = execution_plan.steps[execution_plan.current_step_index :]
            grading_steps = [
                step
                for step in contiguous_steps
                if step.agent.value in {"parser", "teacher", "verifier"}
            ]
            step_output = {
                "feedback": self._stringify_feedback_entry(
                    (specialist_state.get("teacher_feedback") or [None])[-1]
                )
                or self._stringify_feedback_entry(
                    (specialist_state.get("verifier_feedback") or [None])[-1]
                ),
                "response_type": execution_plan.final_response_mode.value,
                "pipeline_agents": pipeline_agents or [step.agent.value for step in grading_steps],
            }
            for step in grading_steps:
                step_results.append(
                    self._build_step_result(
                        step_id=step.step_id,
                        agent=step.agent,
                        step_output=step_output,
                        tool_calls_used=step.allowed_tools,
                    )
                )
                tool_trace.append(
                    {
                        "step_id": step.step_id,
                        "agent": step.agent.value,
                        "allowed_tools": list(step.allowed_tools),
                    }
                )
            execution_plan.current_step_index += len(grading_steps)
            next_state = {
                **specialist_state,
                "execution_plan": execution_plan,
                "step_results": step_results,
                "tool_trace": tool_trace,
                "needs_replan": bool(replan_signal and replan_signal.requested),
                "allowed_tools": list(execution_plan.current_step().allowed_tools)
                if execution_plan.current_step()
                else [],
            }

        log_agent_event(
            "manager",
            "specialist_execution:done",
            state=next_state,
            request=request,
            extra={
                "step_id": current_step.step_id,
                "agent": current_step.agent.value,
                "remaining_steps": self._remaining_plan_steps(execution_plan),
                "needs_replan": next_state.get("needs_replan"),
            },
            mode="completed",
        )
        return next_state

    @staticmethod
    def _build_solution_student_answers(
        questions: list[ExamQuestion] | list[dict[str, Any]],
    ) -> list[StudentAnswer]:
        """Tạo answer rỗng để teacher/verifier có thể "giải hộ" bộ câu hỏi mới.

        Hàm này chỉ phục vụ cho nhánh solution-pipeline dự phòng, chưa dùng trong
        luồng MVP hiện tại.
        """

        placeholders: list[StudentAnswer] = []
        for question in questions:
            normalized = ExamQuestion.model_validate(question)
            placeholders.append(
                StudentAnswer(
                    question_id=normalized.question_id,
                    student_answer="",
                )
            )
        return placeholders

    async def _solution_pipeline_node(self, state: AgentState) -> AgentState:
        """Nhánh dự phòng: cho teacher/verifier giải trước bộ câu adaptive.

        MVP hiện tại chưa route vào node này; giữ lại để mở rộng sau.
        """

        request = state.get("request")
        selected_questions = [
            ExamQuestion.model_validate(question)
            for question in (state.get("selected_questions") or [])
        ]
        if request is None or not selected_questions:
            return state
        log_agent_event(
            "manager",
            "solution_pipeline:start",
            state=state,
            request=request,
            extra={"selected_questions": len(selected_questions)},
            mode="agent_node",
        )

        metadata = request.metadata or {}
        try:
            max_rounds = max(1, int(metadata.get("max_rounds", state.get("max_round", 2))))
        except (TypeError, ValueError):
            max_rounds = 2

        try:
            confidence_threshold = float(
                metadata.get(
                    "confidence_threshold",
                    state.get("_teacher_confidence_threshold", 0.9),
                )
            )
        except (TypeError, ValueError):
            confidence_threshold = 0.9

        solution_student_answers = self._build_solution_student_answers(selected_questions)
        solution_request = request.model_copy(update={"student_answers": solution_student_answers})
        effective_thread_id = (
            state.get("_thread_id")
            or f"manager-solution-{request.user_id or request.student_id or 'anonymous'}"
        )
        final_solution_state = await _run_teacher_verifier_solution_pipeline(
            request=solution_request,
            learner_profile=state.get("learner_profile"),
            exam_id=state.get("exam_id") or solution_request.exam_id,
            questions=selected_questions,
            student_answers=solution_student_answers,
            max_rounds=max_rounds,
            confidence_threshold=confidence_threshold,
            thread_id=effective_thread_id,
        )

        next_state = {
            **state,
            "response": final_solution_state.get("response") or state.get("response"),
            "debate_outputs": final_solution_state.get("debate_outputs", []),
            "agent_trail": self._append_agent_trail(state, "teacher", "verifier"),
        }
        log_agent_event(
            "manager",
            "solution_pipeline:done",
            state=next_state,
            request=request,
            extra={"selected_questions": len(selected_questions)},
            mode="completed",
        )
        return next_state

    @staticmethod
    def _default_feedback(
        intent: Intent | str | None,
        *,
        selected_count: int,
        attempts_processed: int,
    ) -> str:
        """Sinh feedback mặc định nếu một nhánh chưa tạo phản hồi riêng."""

        if intent == Intent.EXAM_PRACTICE:
            return f"Adaptive đã chuẩn bị {selected_count} câu hỏi luyện tập tiếp theo."
        if intent == Intent.GRADE_SUBMISSION:
            return (
                f"Adaptive đã gợi ý {selected_count} câu luyện tập tiếp theo sau khi chấm bài."
                if selected_count
                else "Adaptive đã chấm bài và cập nhật hồ sơ học tập."
            )
        if intent == Intent.UPDATE_PRACTICE:
            return f"Adaptive đã cập nhật danh sách luyện tập với {selected_count} câu hỏi."
        if intent == Intent.VIEW_ANALYSIS:
            return (
                "Adaptive đã phân tích lịch sử làm bài và cập nhật hồ sơ học tập."
                if attempts_processed
                else "Adaptive đã tải hồ sơ học tập hiện tại."
            )
        if intent == Intent.ASK_HINT:
            return "Đã tạo gợi ý cho câu hỏi hiện tại."
        if intent == Intent.REVIEW_MISTAKE:
            return "Đã tạo phần giải thích cho câu trả lời hiện tại."
        return "Manager đã điều phối xong workflow của các agent."

    @staticmethod
    def _ensure_dict(value: Any) -> dict[str, Any]:
        """Normalize optional state payloads that are expected to be mappings."""

        return value if isinstance(value, dict) else {}

    @staticmethod
    def _ensure_list(value: Any) -> list[Any]:
        """Normalize optional state payloads that are expected to be lists."""

        return value if isinstance(value, list) else []

    @staticmethod
    def _stringify_feedback_entry(entry: Any) -> str:
        """Convert pipeline feedback entries into a plain string for API output."""

        if entry is None:
            return ""
        if isinstance(entry, str):
            return entry.strip()
        if isinstance(entry, list):
            flattened = [
                ManagerOrchestrator._stringify_feedback_entry(item)
                for item in entry
            ]
            return "\n".join(item for item in flattened if item)
        content = getattr(entry, "content", None)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item.strip())
                elif isinstance(item, dict):
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        text_parts.append(text_value.strip())
            return "\n".join(part for part in text_parts if part)
        if hasattr(entry, "feedback"):
            feedback = getattr(entry, "feedback", None)
            if isinstance(feedback, str):
                return feedback.strip()
        if isinstance(entry, dict):
            for key in ("feedback", "content", "text"):
                value = entry.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return str(entry).strip()

    async def _finalize_response_node(self, state: AgentState) -> AgentState:
        """Đóng gói state cuối cùng thành ``MessageResponse`` cho API trả ra."""

        request = state.get("request")
        log_agent_event(
            "manager",
            "finalize:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        response = state.get("response")
        profile_updates = self._ensure_dict(state.get("profile_updates"))
        selected_questions = self._ensure_list(state.get("selected_questions"))
        teacher_feedback_entries = self._ensure_list(state.get("teacher_feedback"))
        attempts_processed = int(profile_updates.get("attempts_processed") or 0)

        if isinstance(response, dict):
            payload = dict(response)
        elif response is not None and hasattr(response, "model_dump"):
            payload = response.model_dump(mode="json")
        else:
            payload = {}
        payload.setdefault("student_id", request.student_id if request else None)
        payload.setdefault("user_id", request.user_id if request else None)
        payload.setdefault("exam_id", state.get("exam_id") or (request.exam_id if request else None))
        payload.setdefault("question_id", request.question_id if request else None)
        fallback_feedback = self._default_feedback(
            state.get("intent"),
            selected_count=len(selected_questions),
            attempts_processed=attempts_processed,
        )
        teacher_feedback = ""
        if teacher_feedback_entries:
            teacher_feedback = self._stringify_feedback_entry(teacher_feedback_entries[-1])
        payload.setdefault(
            "feedback",
            teacher_feedback or fallback_feedback,
        )

        payload["selected_questions"] = [
            question.model_dump(mode="json", by_alias=True)
            if hasattr(question, "model_dump")
            else question
            for question in selected_questions
        ]
        payload["profile_updates"] = profile_updates
        payload["agent_trail"] = list(state.get("agent_trail") or ["manager"])
        if state.get("planner_summary"):
            payload["planner_summary"] = state.get("planner_summary")
        step_results = self._normalize_step_results(state.get("step_results"))
        if step_results:
            payload["step_results"] = [
                step_result.model_dump(mode="json")
                for step_result in step_results
            ]
        tool_trace = self._ensure_list(state.get("tool_trace"))
        if tool_trace:
            payload["tool_trace"] = tool_trace
        if isinstance(state.get("plan_patch"), dict):
            payload["plan_patch"] = state.get("plan_patch")
        if isinstance(state.get("plan_proposal"), dict):
            payload["plan_proposal"] = state.get("plan_proposal")

        learner_profile = state.get("learner_profile")
        if learner_profile is not None:
            payload["learner_profile"] = learner_profile.model_dump(mode="json")

        finalized = MessageResponse.model_validate(payload)
        finalized_state = {**state, "response": finalized}
        log_agent_event(
            "manager",
            "finalize:done",
            state=finalized_state,
            request=request,
            extra={"feedback_len": len(finalized.feedback or "")},
            mode="completed",
        )
        return finalized_state

    @staticmethod
    def _route_after_hydrate(state: AgentState) -> str:
        """Chọn nhánh xử lý chính sau khi đã hydrate xong context.

        Workflow mới luôn đi qua request planner cho các intent đã biết để
        manager có execution plan ngắn hạn trước khi dispatch specialist.
        """

        intent = state.get("intent")
        route = "finalize"
        if intent in {
            Intent.ASK_HINT,
            Intent.PREPROCESS,
            Intent.REVIEW_MISTAKE,
            Intent.EXAM_PRACTICE,
            Intent.GRADE_SUBMISSION,
            Intent.VIEW_ANALYSIS,
            Intent.UPDATE_PRACTICE,
        }:
            route = "request_planner"
        log_agent_event(
            "manager",
            "route_after_hydrate",
            state=state,
            extra={"route": route},
            mode="progress",
        )
        return route

    @staticmethod
    def _route_after_request_planner(state: AgentState) -> str:
        """Route after planning depending on whether a valid execution plan exists."""

        execution_plan = state.get("execution_plan")
        route = "specialist_execution" if execution_plan is not None else "finalize"
        log_agent_event(
            "manager",
            "route_after_request_planner",
            state=state,
            extra={"route": route},
            mode="progress",
        )
        return route

    @staticmethod
    def _route_after_specialist_execution(state: AgentState) -> str:
        """Handle the lightweight replan loop, then finalize when work is done."""

        route = "finalize"
        execution_plan = state.get("execution_plan")
        if isinstance(execution_plan, dict):
            execution_plan = ExecutionPlan.model_validate(execution_plan)
        needs_replan = bool(state.get("needs_replan"))
        replan_count = int(state.get("replan_count", 0) or 0)
        if needs_replan and replan_count < 1:
            route = "request_planner"
        elif isinstance(execution_plan, ExecutionPlan) and execution_plan.has_remaining_steps():
            route = "specialist_execution"
        log_agent_event(
            "manager",
            "route_after_specialist_execution",
            state=state,
            extra={
                "route": route,
                "needs_replan": needs_replan,
                "replan_count": replan_count,
            },
            mode="progress",
        )
        return route

    def _build_graph(self):
        """Dựng graph điều phối chính cho AI service.

        Cấu trúc mới:
        START -> preprocess -> classify_intent -> hydrate_backend_context
              -> request_planner -> specialist_execution -> (replan tối đa 1 lần)
              -> finalize -> END
        """

        builder = StateGraph(AgentState)
        builder.add_node("preprocess", preprocess_node)
        builder.add_node("classify_intent", classify_intent)
        builder.add_node("hydrate_backend_context", self._hydrate_backend_context_node)
        builder.add_node("request_planner", self._request_planner_node)
        builder.add_node("specialist_execution", self._specialist_execution_node)
        builder.add_node("finalize", self._finalize_response_node)

        builder.add_edge(START, "preprocess")
        builder.add_edge("preprocess", "classify_intent")
        builder.add_edge("classify_intent", "hydrate_backend_context")
        builder.add_conditional_edges(
            "hydrate_backend_context",
            self._route_after_hydrate,
            {
                "request_planner": "request_planner",
                "finalize": "finalize",
            },
        )
        builder.add_conditional_edges(
            "request_planner",
            self._route_after_request_planner,
            {
                "specialist_execution": "specialist_execution",
                "finalize": "finalize",
            },
        )
        builder.add_conditional_edges(
            "specialist_execution",
            self._route_after_specialist_execution,
            {
                "request_planner": "request_planner",
                "specialist_execution": "specialist_execution",
                "finalize": "finalize",
            },
        )
        builder.add_edge("finalize", END)
        graph = builder.compile()
        log_agent_event("manager", "graph_compiled", mode="completed")
        return graph

    async def run(self, state: AgentState) -> AgentState:
        """Chạy manager graph trên state đã được caller khởi tạo."""

        log_agent_event(
            "manager",
            "run:start",
            state=state,
            request=state.get("request"),
            mode="agent_node",
        )
        final_state = await self.graph.ainvoke(
            state,
            config=build_langsmith_invoke_config(
                run_name="ManagerOrchestrator.run",
                agent_role="manager",
                thread_id=state.get("_thread_id"),
                extra_tags=["manager", "orchestrator"],
                extra_metadata={"exam_id": state.get("exam_id")},
            ),
        )
        log_agent_event(
            "manager",
            "run:done",
            state=final_state,
            request=final_state.get("request"),
            mode="completed",
        )
        return final_state

    async def run_request(
        self,
        request: MessageRequest,
        *,
        exam_id: str | None = None,
        thread_id: str | None = None,
        max_round: int = 2,
    ) -> MessageResponse:
        """Wrapper public: nhận ``MessageRequest`` và trả ``MessageResponse``."""

        log_agent_event(
            "manager",
            "run_request:start",
            request=request,
            extra={"thread_id": thread_id, "max_round": max_round},
            mode="agent_node",
        )
        final_state = await self.run(
            {
                "request": request,
                "exam_id": exam_id or request.exam_id,
                "max_round": max_round,
                "student_answers": request.student_answers or [],
                "_thread_id": thread_id or f"manager-{request.user_id or request.student_id or 'anonymous'}",
            }
        )
        response = final_state.get("response")
        if response is None:
            log_agent_event(
                "manager",
                "run_request:fallback_response",
                state=final_state,
                request=request,
                mode="warning",
            )
            return MessageResponse(
                student_id=request.student_id,
                user_id=request.user_id,
                exam_id=exam_id or request.exam_id,
                feedback="Manager workflow completed without a concrete response.",
            )
        log_agent_event(
            "manager",
            "run_request:done",
            state=final_state,
            request=request,
            mode="completed",
        )
        return response


# def _build_tutoring_graph() -> StateGraph:
#     """Wrapper tương thích ngược cho các import cũ."""

#     return ManagerOrchestrator().graph


# def _build_content_pipeline_graph() -> StateGraph:
#     """Wrapper tương thích ngược cho các import cũ."""

#     return ManagerOrchestrator().graph


# def _build_adaptive_graph() -> StateGraph:
#     """Wrapper tương thích ngược cho các import cũ."""

#     return ManagerOrchestrator().graph


# def _build_solution_gen_graph() -> StateGraph:
#     """Wrapper tương thích ngược cho các import cũ."""

#     return ManagerOrchestrator().graph


# def _build_analysis_graph() -> StateGraph:
#     """Wrapper tương thích ngược cho các import cũ."""

#     return ManagerOrchestrator().graph


async def run_manager_orchestrator(
    request: MessageRequest,
    *,
    exam_id: str | None = None,
    thread_id: str | None = None,
    max_round: int = 2,
) -> MessageResponse:
    """Điểm vào async công khai để AI service gọi orchestrator."""

    log_agent_event(
        "manager",
        "entrypoint:start",
        request=request,
        extra={"thread_id": thread_id, "max_round": max_round},
        mode="agent_node",
    )
    orchestrator = ManagerOrchestrator()
    response = await orchestrator.run_request(
        request,
        exam_id=exam_id,
        thread_id=thread_id,
        max_round=max_round,
    )
    log_agent_event(
        "manager",
        "entrypoint:done",
        request=request,
        extra={"has_feedback": bool(response.feedback)},
        mode="completed",
    )
    return response
