"""LangGraph-based manager orchestrator for cross-agent coordination.

This graph acts as the "brainstem" between backend events and the specialized
agents:

- hydrate missing backend context from MongoDB
- route by intent
- delegate grading/preprocess/hint flows to parser/teacher/verifier
- delegate personalization and next-question generation to adaptive
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from master.agents.adaptive import AdaptiveAgent, AdaptiveDBTools
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


def preprocess_node(state: AgentState) -> AgentState:
    """Normalize shared manager state before any routing happens."""

    request = state.get("request")
    agent_trail = list(state.get("agent_trail") or [])
    if "manager" not in agent_trail:
        agent_trail.append("manager")

    exam_id = state.get("exam_id")
    if request is not None and not exam_id:
        exam_id = request.exam_id

    return {
        **state,
        "exam_id": exam_id,
        "round": state.get("round", 0),
        "max_round": state.get("max_round", 2),
        "phase": state.get("phase", "draft"),
        "debate_outputs": state.get("debate_outputs", []),
        "questions": state.get("questions", []),
        "student_answers": state.get("student_answers", []),
        "selected_questions": state.get("selected_questions", []),
        "profile_updates": state.get("profile_updates", {}),
        "agent_trail": agent_trail,
    }


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
    """Run teacher/verifier over manager-selected questions via the shared graph."""

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

    return await pipeline_graph.ainvoke(
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


class ManagerOrchestrator:
    """Coordinate parser, teacher, verifier, and adaptive from one graph."""

    def __init__(
        self,
        *,
        repository: AdaptiveDBTools | None = None,
        adaptive_agent: AdaptiveAgent | None = None,
    ) -> None:
        self.repository = repository or AdaptiveDBTools()
        self.adaptive_agent = adaptive_agent or AdaptiveAgent(repository=self.repository)
        self.graph = self._build_graph()

    @staticmethod
    def _append_agent_trail(state: AgentState, *agents: str) -> list[str]:
        """Append agent names once while preserving the observed execution order."""

        trail = list(state.get("agent_trail") or [])
        for agent in agents:
            if agent and agent not in trail:
                trail.append(agent)
        return trail

    @staticmethod
    def _normalize_history_student_answers(raw_answers: Any) -> list[StudentAnswer]:
        """Accept several history payload shapes and normalize them."""

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
        """Pull the legacy review-mistake answer field from extra attributes."""

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
        """Resolve the first parser-compatible file path from the request."""

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

    async def _hydrate_backend_context_node(self, state: AgentState) -> AgentState:
        """Load histories/questions from Mongo when backend only sent IDs."""

        request = state.get("request")
        if request is None:
            return state

        resolved_student_id = request.student_id or request.user_id
        resolved_exam_id = state.get("exam_id") or request.exam_id
        metadata = dict(request.metadata or {})

        history_record = state.get("history_record")
        student_answers = [
            StudentAnswer.model_validate(answer)
            for answer in (state.get("student_answers") or request.student_answers or [])
        ]
        questions = [
            ExamQuestion.model_validate(question)
            for question in (state.get("questions") or [])
        ]

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
                history_record = None

        if history_record and not student_answers:
            student_answers = self._normalize_history_student_answers(
                history_record.get("student_ans")
            )
            raw_history_id = history_record.get("_id")
            if raw_history_id is not None:
                metadata.setdefault("history_id", str(raw_history_id))

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
                elif resolved_exam_id:
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
                questions = []

        normalized_request = request.model_copy(
            update={
                "student_id": resolved_student_id,
                "exam_id": resolved_exam_id,
                "metadata": metadata,
                "student_answers": student_answers or request.student_answers,
            }
        )

        return {
            **state,
            "request": normalized_request,
            "exam_id": resolved_exam_id,
            "student_answers": student_answers,
            "questions": questions,
            "history_record": history_record,
        }

    async def _grading_node(self, state: AgentState) -> AgentState:
        """Delegate grading-style flows to parser/teacher/verifier."""

        request = state.get("request")
        if request is None:
            return state

        from master.agents.server import run_grading_pipeline

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
            response = await run_grading_pipeline(
                request=None,
                exam_id=state.get("exam_id"),
                max_rounds=max_rounds,
                confidence_threshold=confidence_threshold,
                thread_id=state.get("_thread_id"),
                file_path=file_path,
                student_id=request.student_id or request.user_id,
                parser_batch_size=parser_batch_size,
            )
            agent_trail = self._append_agent_trail(state, "parser", "teacher", "verifier")
        else:
            normalized_request = request.model_copy(
                update={"student_answers": state.get("student_answers") or request.student_answers}
            )
            response = await run_grading_pipeline(
                request=normalized_request,
                exam_id=state.get("exam_id") or normalized_request.exam_id,
                max_rounds=max_rounds,
                confidence_threshold=confidence_threshold,
                thread_id=state.get("_thread_id"),
            )
            if state.get("intent") == Intent.ASK_HINT:
                agent_trail = self._append_agent_trail(state, "teacher")
            else:
                agent_trail = self._append_agent_trail(state, "teacher", "verifier")

        return {
            **state,
            "response": response,
            "agent_trail": agent_trail,
        }

    def _adaptive_node(self, state: AgentState) -> AgentState:
        """Run adaptive update/selection/generation on the hydrated context."""

        request = state.get("request")
        if request is None:
            return state

        metadata = dict(request.metadata or {})
        intent = state.get("intent")

        if intent in {
            Intent.GRADE_SUBMISSION,
            Intent.UPDATE_PRACTICE,
            Intent.EXAM_PRACTICE,
            Intent.VIEW_ANALYSIS,
        }:
            metadata.setdefault("generate_questions", True)
            metadata.setdefault("generation_limit", 3)
            metadata.setdefault("rag_context_limit", 8)

        normalized_request = request.model_copy(update={"metadata": metadata})
        adaptive_state = self.adaptive_agent.run(
            {
                "request": normalized_request,
                "learner_profile": state.get("learner_profile"),
                "questions": state.get("questions", []),
                "student_answers": state.get("student_answers", []),
                "selected_questions": state.get("selected_questions", []),
                "profile_updates": state.get("profile_updates", {}),
            }
        )
        return {
            **state,
            "request": normalized_request,
            "learner_profile": adaptive_state.get("learner_profile"),
            "selected_questions": adaptive_state.get("selected_questions", []),
            "profile_updates": adaptive_state.get("profile_updates", {}),
            "agent_trail": self._append_agent_trail(state, "adaptive"),
        }

    @staticmethod
    def _build_solution_student_answers(
        questions: list[ExamQuestion] | list[dict[str, Any]],
    ) -> list[StudentAnswer]:
        """Create blank answers so teacher/verifier can solve selected questions."""

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
        """Let teacher and verifier autonomously solve and validate next questions."""

        request = state.get("request")
        selected_questions = [
            ExamQuestion.model_validate(question)
            for question in (state.get("selected_questions") or [])
        ]
        if request is None or not selected_questions:
            return state

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

        return {
            **state,
            "response": final_solution_state.get("response") or state.get("response"),
            "debate_outputs": final_solution_state.get("debate_outputs", []),
            "agent_trail": self._append_agent_trail(state, "teacher", "verifier"),
        }

    @staticmethod
    def _default_feedback(
        intent: Intent | str | None,
        *,
        selected_count: int,
        attempts_processed: int,
    ) -> str:
        """Produce a concise fallback feedback for non-grading routes."""

        if intent == Intent.EXAM_PRACTICE:
            return f"Adaptive đã chuẩn bị {selected_count} câu hỏi luyện tập tiếp theo."
        if intent == Intent.UPDATE_PRACTICE:
            return f"Adaptive đã cập nhật danh sách luyện tập với {selected_count} câu hỏi."
        if intent == Intent.VIEW_ANALYSIS:
            return (
                "Adaptive đã phân tích lịch sử làm bài và cập nhật hồ sơ học tập."
                if attempts_processed
                else "Adaptive đã tải hồ sơ học tập hiện tại."
            )
        return "Manager đã điều phối xong workflow của các agent."

    async def _finalize_response_node(self, state: AgentState) -> AgentState:
        """Merge intermediate state into one API-friendly response object."""

        request = state.get("request")
        response = state.get("response")
        profile_updates = state.get("profile_updates") or {}
        selected_questions = state.get("selected_questions") or []
        attempts_processed = int(profile_updates.get("attempts_processed") or 0)

        payload = response.model_dump(mode="json") if response is not None else {}
        payload.setdefault("student_id", request.student_id if request else None)
        payload.setdefault("user_id", request.user_id if request else None)
        payload.setdefault("exam_id", state.get("exam_id") or (request.exam_id if request else None))
        payload.setdefault("question_id", request.question_id if request else None)
        payload.setdefault(
            "feedback",
            self._default_feedback(
                state.get("intent"),
                selected_count=len(selected_questions),
                attempts_processed=attempts_processed,
            ),
        )

        payload["selected_questions"] = [
            question.model_dump(mode="json", by_alias=True)
            if hasattr(question, "model_dump")
            else question
            for question in selected_questions
        ]
        payload["profile_updates"] = profile_updates
        payload["agent_trail"] = list(state.get("agent_trail") or ["manager"])

        learner_profile = state.get("learner_profile")
        if learner_profile is not None:
            payload["learner_profile"] = learner_profile.model_dump(mode="json")

        finalized = MessageResponse.model_validate(payload)
        return {**state, "response": finalized}

    @staticmethod
    def _route_after_hydrate(state: AgentState) -> str:
        """Choose the next specialized workflow after backend hydration."""

        intent = state.get("intent")
        if intent in {Intent.ASK_HINT, Intent.PREPROCESS, Intent.GRADE_SUBMISSION, Intent.REVIEW_MISTAKE}:
            return "grading"
        if intent in {Intent.EXAM_PRACTICE, Intent.VIEW_ANALYSIS, Intent.UPDATE_PRACTICE}:
            return "adaptive"
        return "finalize"

    @staticmethod
    def _route_after_grading(state: AgentState) -> str:
        """Grade submission flows continue into adaptive; others can finalize."""

        if state.get("intent") == Intent.GRADE_SUBMISSION:
            return "adaptive"
        return "finalize"

    @staticmethod
    def _route_after_adaptive(state: AgentState) -> str:
        """Run teacher/verifier on the selected questions when practice continues."""

        intent = state.get("intent")
        selected_questions = state.get("selected_questions") or []
        if not selected_questions:
            return "finalize"

        if intent in {
            Intent.EXAM_PRACTICE,
            Intent.UPDATE_PRACTICE,
            Intent.VIEW_ANALYSIS,
            Intent.GRADE_SUBMISSION,
        }:
            return "solution_pipeline"
        return "finalize"

    def _build_graph(self):
        """Compile the manager graph used by the AI service entrypoint."""

        builder = StateGraph(AgentState)
        builder.add_node("preprocess", preprocess_node)
        builder.add_node("classify_intent", classify_intent)
        builder.add_node("hydrate_backend_context", self._hydrate_backend_context_node)
        builder.add_node("grading", self._grading_node)
        builder.add_node("adaptive", self._adaptive_node)
        builder.add_node("solution_pipeline", self._solution_pipeline_node)
        builder.add_node("finalize", self._finalize_response_node)

        builder.add_edge(START, "preprocess")
        builder.add_edge("preprocess", "classify_intent")
        builder.add_edge("classify_intent", "hydrate_backend_context")
        builder.add_conditional_edges(
            "hydrate_backend_context",
            self._route_after_hydrate,
            {
                "grading": "grading",
                "adaptive": "adaptive",
                "finalize": "finalize",
            },
        )
        builder.add_conditional_edges(
            "grading",
            self._route_after_grading,
            {
                "adaptive": "adaptive",
                "finalize": "finalize",
            },
        )
        builder.add_conditional_edges(
            "adaptive",
            self._route_after_adaptive,
            {
                "solution_pipeline": "solution_pipeline",
                "finalize": "finalize",
            },
        )
        builder.add_edge("solution_pipeline", "finalize")
        builder.add_edge("finalize", END)
        return builder.compile()

    async def run(self, state: AgentState) -> AgentState:
        """Run the manager graph over an already-built agent state."""

        return await self.graph.ainvoke(
            state,
            config=build_langsmith_invoke_config(
                run_name="ManagerOrchestrator.run",
                agent_role="manager",
                thread_id=state.get("_thread_id"),
                extra_tags=["manager", "orchestrator"],
                extra_metadata={"exam_id": state.get("exam_id")},
            ),
        )

    async def run_request(
        self,
        request: MessageRequest,
        *,
        exam_id: str | None = None,
        thread_id: str | None = None,
        max_round: int = 2,
    ) -> MessageResponse:
        """Convenience wrapper for the public request -> response flow."""

        final_state = await self.run(
            {
                "request": request,
                "exam_id": exam_id or request.exam_id,
                "max_round": max_round,
                "_thread_id": thread_id or f"manager-{request.user_id or request.student_id or 'anonymous'}",
            }
        )
        response = final_state.get("response")
        if response is None:
            return MessageResponse(
                student_id=request.student_id,
                user_id=request.user_id,
                exam_id=exam_id or request.exam_id,
                feedback="Manager workflow completed without a concrete response.",
            )
        return response


def _build_tutoring_graph() -> StateGraph:
    """Backward-compatible wrapper for older imports."""

    return ManagerOrchestrator().graph


def _build_content_pipeline_graph() -> StateGraph:
    """Backward-compatible wrapper for older imports."""

    return ManagerOrchestrator().graph


def _build_adaptive_graph() -> StateGraph:
    """Backward-compatible wrapper for older imports."""

    return ManagerOrchestrator().graph


def _build_solution_gen_graph() -> StateGraph:
    """Backward-compatible wrapper for older imports."""

    return ManagerOrchestrator().graph


def _build_analysis_graph() -> StateGraph:
    """Backward-compatible wrapper for older imports."""

    return ManagerOrchestrator().graph


async def run_manager_orchestrator(
    request: MessageRequest,
    *,
    exam_id: str | None = None,
    thread_id: str | None = None,
    max_round: int = 2,
) -> MessageResponse:
    """Public async entrypoint used by the agent service layer."""

    orchestrator = ManagerOrchestrator()
    return await orchestrator.run_request(
        request,
        exam_id=exam_id,
        thread_id=thread_id,
        max_round=max_round,
    )
