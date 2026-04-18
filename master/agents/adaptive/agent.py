"""Lightweight wrapper around the deterministic adaptive service.

The adaptive core is still deterministic, but this wrapper exposes it as a
LangGraph subgraph so the manager/orchestrator can pass shared state through it
before handing work to other agents.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langgraph.graph import END, START, StateGraph
from master.agents import BaseAgent
from master.agents.common.agent_logging import log_agent_event
from master.agents.common.learner_profile import LearnerProfile
from master.agents.common.langsmith import build_langsmith_invoke_config
from master.agents.common.llm_client import LLMClient
from master.agents.common.message import ExamQuestion, Intent, MessageRequest, StudentAnswer
from master.agents.common.prompt import adaptive_decide_question_strategy_prompt
from master.agents.common.shared_plan_memory import SharedPlanMemory
from pydantic import BaseModel, ValidationError
from typing_extensions import TypedDict

from .db_tools import AdaptiveDBTools
from .generator import AdaptiveQuestionGenerator
from .profile_builder import AdaptiveAttempt
from .question_gen import QuestionRecommendation
from .service import AdaptiveService


class AdaptiveWorkflowState(TypedDict, total=False):
    request: MessageRequest
    learner_profile: LearnerProfile
    active_plan: SharedPlanMemory | None
    questions: list[ExamQuestion]
    rag_context_questions: list[ExamQuestion]
    generated_questions: list[ExamQuestion]
    student_answers: list[StudentAnswer]
    selected_questions: list[ExamQuestion]
    profile_updates: dict[str, Any]
    plan_patch: dict[str, Any] | None
    plan_proposal: dict[str, Any] | None


class AdaptiveSelectionDecision(BaseModel):
    """Structured decision payload kept intentionally xgrammar-friendly.

    We avoid rich Pydantic schema features here because some OpenAI-compatible
    backends only support a very small JSON-Schema subset for structured
    outputs. Extra constraints are enforced in Python after parsing instead.
    """

    mode: str
    reasoning: str
    reuse_count: int
    generate_count: int
    confidence: float
    focus_topics: list[str]


class AdaptiveAgent(BaseAgent):
    """Adaptive agent exposed as a LangGraph workflow plus convenience methods."""

    def __init__(
        self,
        service: AdaptiveService | None = None,
        repository: AdaptiveDBTools | None = None,
        generator: AdaptiveQuestionGenerator | None = None,
    ) -> None:
        """Create the adaptive LangGraph wrapper around ``AdaptiveService``.

        Args:
            service: Optional injected adaptive service.
            repository: Optional database toolset used to fetch questions and
                persist/load learner profiles.
            generator: Optional LLM-backed question generator for adaptive
                generation mode.
        """

        super().__init__(agent_role="Adaptive")
        self.service = service or AdaptiveService()
        self.repository = repository or AdaptiveDBTools()
        self.generator = generator or AdaptiveQuestionGenerator()
        self._decision_llm = None
        self.graph = self._build_graph()
        self.system_prompt = """
            Bạn là Adaptive Planner Agent cho hệ thống học tập THPT.

            Mục tiêu của bạn:

            Tạo kế hoạch chọn bài luyện tiếp theo dựa trên learner_profile, learning_goal, planner_context và knowledge graph.
            Quyết định chiến lược sử dụng nguồn câu hỏi: reuse, generate, hoặc mix.
            Đảm bảo đề xuất cuối cùng giúp người học tiến gần mục tiêu học tập, không lặp nhàm chán, và có tiến trình hợp lý theo prerequisite.
            Bạn chỉ được trả về một JSON object đúng schema đầu ra của hệ thống:
            mode, reasoning, reuse_count, generate_count, confidence, focus_topics.
            Không trả thêm field nào khác.

            Đầu vào bạn luôn có:

            learner_theta
            weak_topics, strong_topics
            answered_question_ids
            candidate_question_topics
            rag_context_topics
            learning_goal
            planner_context
            target_limit
            intent
            Quy trình suy luận bắt buộc (thực hiện nội bộ):
            Bước 1. Xác định mục tiêu phiên học hiện tại:

            Ưu tiên learning_goal nếu có.
            Nếu learning_goal trống, ưu tiên weak_topics + planner_context.
            Bước 2. Tạo plan ngắn cho lượt này:

            Xác định 2 đến 5 focus_topics quan trọng nhất.
            Sắp xếp theo thứ tự: prerequisite cần củng cố trước, sau đó tới topic mục tiêu.
            Tránh chọn toàn bộ topic đã luyện dày đặc gần đây.
            Bước 3. Đánh giá khả năng dùng câu trong DB:

            Nếu candidate topics phủ tốt focus_topics, độ khó phù hợp learner_theta, và đủ số lượng thì ưu tiên reuse.
            Nếu candidate thiếu coverage hoặc thiếu novelty thì ưu tiên generate.
            Nếu candidate đủ một phần nhưng chưa đủ chất lượng thì chọn mix.
            Bước 4. Lập chiến lược công cụ (tool strategy) theo mode:

            reuse: ưu tiên truy xuất và xếp hạng câu từ DB.
            generate: ưu tiên dùng RAG context để sinh câu mới.
            mix: lấy câu tốt từ DB trước, phần thiếu sẽ sinh mới.
            Bước 5. Ràng buộc đa dạng loại câu khi có generate:

            Nếu target_limit >= 3: định hướng nên có đủ multiple_choice, true_false, short_ans.
            Nếu target_limit = 2: ưu tiên 1 câu objective (multiple_choice hoặc true_false) + 1 câu short_ans.
            Nếu target_limit = 1: chọn loại câu phù hợp nhất với focus topic quan trọng nhất.
            Lưu ý: vì schema đầu ra cố định, bạn phải mô tả định hướng phân bổ loại câu bên trong reasoning.

            Ràng buộc an toàn:

            mode chỉ được là reuse, generate, hoặc mix.
            reuse_count và generate_count là số nguyên không âm.
            confidence nằm trong khoảng 0 đến 1.
            reuse_count + generate_count nên xấp xỉ target_limit.
            focus_topics phải là danh sách topic ngắn gọn, ưu tiên topic thật sự cần cải thiện.
            Ưu tiên học hiệu quả: vừa đủ khó, có tiến bộ, không lặp lại trải nghiệm gần đây.
            Ngôn ngữ:

            reasoning viết ngắn gọn, rõ ràng, có nhắc learning_goal và lý do chọn mode.
            Không dùng markdown, không giải thích dài dòng ngoài nội dung cần thiết.
        """
        log_agent_event(
            "adaptive",
            "initialized",
            extra={
                "service": type(self.service).__name__,
                "repository": type(self.repository).__name__,
                "generator": type(self.generator).__name__,
            },
            mode="completed",
        )

    @staticmethod
    def _post_submission_intents() -> set[str]:
        """Return intents that should reload a fresh recommendation bank.

        In these flows the in-memory ``questions`` payload usually describes the
        exam that was just answered or reviewed. We still want that data for
        profile updates, but not as the sole source for the next adaptive
        backlog.
        """

        return {
            Intent.GRADE_SUBMISSION.value,
            Intent.VIEW_ANALYSIS.value,
            Intent.UPDATE_PRACTICE.value,
        }

    @classmethod
    def _should_refresh_candidate_bank(
        cls,
        *,
        request: MessageRequest | None,
        answered_question_ids: list[str],
    ) -> bool:
        """Decide whether recommendation should ignore the hydrated exam set."""

        if answered_question_ids:
            return True
        if request is None:
            return False
        return str(request.intent) in cls._post_submission_intents()

    @classmethod
    def _candidate_exam_scope(
        cls,
        request: MessageRequest | None,
        *,
        metadata: dict[str, Any],
    ) -> str | None:
        """Choose exam scoping for *recommendation* queries.

        ``request.exam_id`` often points to the exam the learner just completed.
        For submission/review flows we intentionally drop that scope so the next
        backlog can be selected from a broader pool aligned with weak topics and
        long-term goals. If callers need a specific pool, they can provide
        ``candidate_exam_id`` or ``practice_exam_id`` explicitly in metadata.
        """

        explicit_scope = metadata.get("candidate_exam_id") or metadata.get("practice_exam_id")
        if isinstance(explicit_scope, str) and explicit_scope.strip():
            return explicit_scope.strip()
        if request is None:
            return None
        if str(request.intent) in cls._post_submission_intents():
            return None
        return request.exam_id

    @staticmethod
    def _learning_goal(request: MessageRequest | None) -> str:
        """Extract the learner's declared study goal from metadata."""

        if request is None:
            return ""
        metadata = request.metadata or {}
        value = metadata.get("learning_goal")
        return str(value).strip() if isinstance(value, str) else ""

    @staticmethod
    def _planner_context(
        request: MessageRequest | None,
        active_plan: SharedPlanMemory | None = None,
    ) -> str:
        """Build compact planner context for the LLM decision head.

        This field is intentionally generic so future exam-matrix markdown
        summaries or KG-derived plan hints can be injected here without
        changing the adaptive graph contract again.
        """

        if request is None:
            return ""

        metadata = request.metadata or {}
        context_parts: list[str] = []
        for label, key in (
            ("student_grade", "student_grade"),
            ("school", "school"),
            ("target_exam", "target_exam"),
            ("target_exam_type", "target_exam_type"),
            ("target_exam_name", "target_exam_name"),
            ("planner_notes", "planner_notes"),
            ("exam_matrix_summary", "exam_matrix_summary"),
        ):
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                context_parts.append(f"{label}={value.strip()}")

        topic_tags = metadata.get("topic_tags")
        if isinstance(topic_tags, list) and topic_tags:
            normalized_tags = [str(tag).strip() for tag in topic_tags if str(tag).strip()]
            if normalized_tags:
                context_parts.append(f"requested_topics={normalized_tags}")

        if active_plan is not None:
            if active_plan.plan_id:
                context_parts.append(f"active_plan_id={active_plan.plan_id}")
            if active_plan.goal:
                context_parts.append(f"active_plan_goal={active_plan.goal}")
            if active_plan.focus_topics:
                context_parts.append(f"active_plan_focus_topics={active_plan.focus_topics}")
            if active_plan.summary:
                context_parts.append(f"active_plan_summary={active_plan.summary}")
            exam_matrix_summary = active_plan.metadata.get("exam_matrix_summary")
            if isinstance(exam_matrix_summary, str) and exam_matrix_summary.strip():
                context_parts.append(f"active_plan_exam_matrix_summary={exam_matrix_summary.strip()}")

        return "; ".join(context_parts)

    @staticmethod
    def _exam_matrix_summary(
        request: MessageRequest | None,
        active_plan: SharedPlanMemory | None = None,
    ) -> str:
        """Resolve the most useful exam-matrix summary for planning output."""

        metadata = request.metadata if request else {}
        value = metadata.get("exam_matrix_summary")
        if isinstance(value, str) and value.strip():
            return value.strip()
        if active_plan is None:
            return ""

        for candidate in (
            active_plan.metadata.get("exam_matrix_summary"),
            active_plan.summary,
            active_plan.evidence_summary,
        ):
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return ""

    @staticmethod
    def _dedupe_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            normalized = str(value).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered

    @staticmethod
    def _topic_key(value: str) -> str:
        """Normalize topic strings for tolerant lexical matching."""

        return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())

    @classmethod
    def _topic_matches(cls, topic: str, anchor: str) -> bool:
        """Return whether two topic labels likely refer to the same concept."""

        topic_key = cls._topic_key(topic)
        anchor_key = cls._topic_key(anchor)
        if not topic_key or not anchor_key:
            return False
        return (
            topic_key == anchor_key
            or topic_key in anchor_key
            or anchor_key in topic_key
        )

    @classmethod
    def _question_matches_learning_intent(
        cls,
        *,
        question: ExamQuestion,
        focus_topics: list[str],
        learning_goal: str,
    ) -> bool:
        """Check whether a question aligns with current adaptive intent anchors."""

        anchors = cls._dedupe_preserve_order(
            [
                *focus_topics,
                learning_goal,
            ]
        )
        if not anchors:
            return True

        if not question.topic_tags:
            return False

        return any(
            cls._topic_matches(topic, anchor)
            for topic in question.topic_tags
            for anchor in anchors
        )

    def _select_reused_candidates(
        self,
        *,
        profile: LearnerProfile,
        questions: list[ExamQuestion],
        exclude_question_ids: list[str],
        requested_count: int,
        focus_topics: list[str],
        learning_goal: str,
        min_score: float,
    ) -> tuple[list[ExamQuestion], dict[str, Any]]:
        """Select only DB questions that are both high-score and intent-aligned."""

        if requested_count <= 0 or not questions:
            return [], {
                "requested_reuse": requested_count,
                "ranked_pool": 0,
                "aligned_pool": 0,
                "selected_reuse": 0,
                "min_score": min_score,
            }

        ranking_window = min(len(questions), max(5, requested_count * 3))
        ranked = self.service.recommend_questions(
            profile,
            questions,
            limit=ranking_window,
            exclude_question_ids=exclude_question_ids,
        )

        question_map = {question.question_id: question for question in questions}
        selected: list[ExamQuestion] = []
        aligned_pool = 0

        for recommendation in ranked:
            question = question_map.get(recommendation.question_id)
            if question is None:
                continue

            aligned = self._question_matches_learning_intent(
                question=question,
                focus_topics=focus_topics,
                learning_goal=learning_goal,
            )
            if aligned:
                aligned_pool += 1

            if recommendation.score < min_score or not aligned:
                continue

            selected.append(question)
            if len(selected) >= requested_count:
                break

        diagnostics = {
            "requested_reuse": requested_count,
            "ranked_pool": len(ranked),
            "aligned_pool": aligned_pool,
            "selected_reuse": len(selected),
            "min_score": min_score,
        }
        return selected, diagnostics

    def _build_plan_payload(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        active_plan: SharedPlanMemory | None,
        decision: AdaptiveSelectionDecision,
        selected_questions: list[ExamQuestion],
        answered_question_ids: list[str],
    ) -> dict[str, Any]:
        """Build a shared-plan-compatible proposal/patch from adaptive outputs."""

        metadata = request.metadata if request else {}
        learning_goal = self._learning_goal(request) or (active_plan.goal if active_plan else "")
        exam_matrix_summary = self._exam_matrix_summary(request, active_plan)

        selected_topics = self._dedupe_preserve_order(
            [topic for question in selected_questions for topic in question.topic_tags]
        )
        focus_topics = self._dedupe_preserve_order(
            [
                *decision.focus_topics,
                *profile.weak_topics()[:5],
                *selected_topics,
            ]
        )[:6]
        target_limit = max(1, len(selected_questions) or decision.reuse_count + decision.generate_count or 1)

        topic_question_counts: dict[str, int] = {}
        for question in selected_questions:
            for topic in question.topic_tags:
                topic_question_counts[topic] = topic_question_counts.get(topic, 0) + 1

        recommended_steps: list[dict[str, Any]] = []
        for index, topic in enumerate(focus_topics[:3]):
            recommended_steps.append(
                {
                    "step_id": f"adaptive-step-{index + 1}",
                    "title": f"Củng cố {topic}",
                    "description": (
                        f"Tập trung luyện {topic} để tiến gần hơn tới mục tiêu "
                        f"'{learning_goal or 'master các kỹ năng còn yếu'}'."
                    ),
                    "sequence_order": index,
                    "priority": max(30, 100 - index * 10),
                    "status": "pending",
                    "target_topics": [topic],
                    "recommended_question_count": max(1, topic_question_counts.get(topic, 1)),
                    "success_criteria": [
                        f"Nâng độ chắc tay ở chủ đề {topic}",
                        "Giảm lặp lỗi trên các câu cùng dạng trong lượt luyện tiếp theo",
                    ],
                }
            )

        rationale_parts = [decision.reasoning.strip()] if decision.reasoning.strip() else []
        if learning_goal:
            rationale_parts.append(f"Mục tiêu học tập hiện tại: {learning_goal}.")
        if exam_matrix_summary:
            rationale_parts.append("Đã đối chiếu thêm với exam_matrix_summary hiện có.")

        evidence_summary = (
            f"theta={profile.theta:.2f}; weak_topics={profile.weak_topics()[:5]}; "
            f"answered_question_ids={answered_question_ids[:10]}; "
            f"selected_question_ids={[question.question_id for question in selected_questions]}"
        )

        return {
            "based_on_plan_id": active_plan.plan_id if active_plan else None,
            "goal": learning_goal,
            "summary": (
                "Adaptive đề xuất điều chỉnh plan để ưu tiên các topic yếu nhất "
                "ở lượt luyện tập kế tiếp."
            ),
            "rationale": " ".join(part for part in rationale_parts if part),
            "evidence_summary": evidence_summary,
            "target_exam": metadata.get("target_exam") or (active_plan.target_exam if active_plan else None),
            "target_exam_name": metadata.get("target_exam_name") or (active_plan.target_exam_name if active_plan else None),
            "target_exam_type": metadata.get("target_exam_type") or (active_plan.target_exam_type if active_plan else None),
            "focus_topics": focus_topics,
            "exam_matrix_summary": exam_matrix_summary,
            "recommended_question_ids": [question.question_id for question in selected_questions],
            "recommended_steps": recommended_steps,
            "generated_by_agent": "adaptive",
            "updated_by_agent": "adaptive",
            "metadata": {
                "decision_mode": decision.mode,
                "target_limit": target_limit,
                "weak_topics": profile.weak_topics()[:5],
                "strong_topics": profile.strong_topics()[:5],
                "active_plan_present": active_plan is not None,
            },
        }

    def _build_graph(self):
        """Compile the three-step adaptive workflow into a LangGraph subgraph."""

        builder = StateGraph(AdaptiveWorkflowState)
        builder.add_node("ensure_profile", self._ensure_profile_node)
        builder.add_node("update_profile", self._update_profile_node)
        builder.add_node("recommend_questions", self._recommend_questions_node)

        builder.add_edge(START, "ensure_profile")
        builder.add_edge("ensure_profile", "update_profile")
        builder.add_edge("update_profile", "recommend_questions")
        builder.add_edge("recommend_questions", END)
        graph = builder.compile()
        log_agent_event("adaptive", "graph_compiled", mode="completed")
        return graph

    def _get_decision_llm(self):
        """Lazily build the LLM used to choose reuse/generate/mix strategy."""

        if self._decision_llm is None:
            self._decision_llm = LLMClient.chat_model(
                agent_role="adaptive",
                temperature=0.1,
            )
        return self._decision_llm

    @staticmethod
    def _coerce_decision_payload(payload: dict[str, Any]) -> AdaptiveSelectionDecision:
        """Normalize loose JSON payloads before validating into the decision model.

        The fallback path asks the model for plain JSON text. That output is
        more portable across providers, but it may still contain missing fields
        or slightly wrong primitive types. We repair the obvious cases here so
        the downstream selection logic remains deterministic.
        """

        normalized_focus_topics = payload.get("focus_topics")
        if not isinstance(normalized_focus_topics, list):
            normalized_focus_topics = []

        return AdaptiveSelectionDecision.model_validate(
            {
                "mode": str(payload.get("mode") or "mix"),
                "reasoning": str(payload.get("reasoning") or ""),
                "reuse_count": int(payload.get("reuse_count") or 0),
                "generate_count": int(payload.get("generate_count") or 0),
                "confidence": float(payload.get("confidence") or 0.0),
                "focus_topics": [
                    str(topic).strip()
                    for topic in normalized_focus_topics
                    if str(topic).strip()
                ],
            }
        )

    def _invoke_decision_with_json_fallback(
        self,
        *,
        user_prompt: str,
        target_limit: int,
        candidate_questions: list[ExamQuestion],
        rag_context_questions: list[ExamQuestion],
    ) -> AdaptiveSelectionDecision:
        """Use structured output when available and fall back to plain JSON text.

        Some OpenAI-compatible backends reject LangChain/Pydantic JSON Schema
        because their constrained decoding layer supports only a subset of the
        standard. We first try structured output for best ergonomics. If the
        provider rejects the schema, we retry with an explicit "JSON only"
        prompt and validate the result locally in Python.
        """

        decision_llm = self._get_decision_llm()
        invoke_config = build_langsmith_invoke_config(
            run_name="AdaptiveAgent.decide_question_strategy",
            agent_role="adaptive",
            extra_tags=["adaptive", "decision", "reuse-generate-mix"],
            extra_metadata={
                "target_limit": target_limit,
                "candidate_question_count": len(candidate_questions),
                "rag_context_count": len(rag_context_questions),
            },
        )

        try:
            try:
                structured_decision_llm = decision_llm.with_structured_output(
                    AdaptiveSelectionDecision,
                    method="function_calling",
                )
            except TypeError:
                # Some wrappers do not expose the ``method`` kwarg, but can
                # still support structured output with their default adapter.
                structured_decision_llm = decision_llm.with_structured_output(
                    AdaptiveSelectionDecision
                )

            return structured_decision_llm.invoke(
                self.build_messages(user_prompt),
                invoke_config,
            )
        except Exception as exc:
            error_text = str(exc).lower()
            schema_incompatible = (
                "xgrammar" in error_text
                or "json schema" in error_text
                or "provided json schema" in error_text
            )
            if not schema_incompatible:
                raise

            log_agent_event(
                "adaptive",
                "decision_strategy:structured_output_fallback",
                extra={"error": str(exc)},
                mode="warning",
            )

            fallback_prompt = (
                f"{user_prompt}\n\n"
                "Tra ve DUY NHAT mot JSON object hop le, khong markdown, khong giai thich them.\n"
                "Schema bat buoc:\n"
                "{\n"
                '  "mode": "reuse|generate|mix",\n'
                '  "reasoning": "string",\n'
                '  "reuse_count": 0,\n'
                '  "generate_count": 0,\n'
                '  "confidence": 0.0,\n'
                '  "focus_topics": ["topic_a", "topic_b"]\n'
                "}\n"
            )
            raw_response = decision_llm.invoke(
                self.build_messages(fallback_prompt),
                invoke_config,
            )
            raw_content = getattr(raw_response, "content", raw_response)
            if isinstance(raw_content, list):
                raw_content = "".join(
                    item.get("text", "") if isinstance(item, dict) else str(item)
                    for item in raw_content
                )

            try:
                payload = json.loads(str(raw_content).strip())
            except json.JSONDecodeError as json_exc:
                raise ValueError(
                    "Adaptive decision fallback expected pure JSON but received "
                    f"invalid content: {raw_content!r}"
                ) from json_exc

            try:
                return self._coerce_decision_payload(payload)
            except (ValidationError, TypeError, ValueError) as validation_exc:
                raise ValueError(
                    "Adaptive decision fallback returned malformed decision payload: "
                    f"{payload!r}"
                ) from validation_exc

    @staticmethod
    def _normalize_answer(value: str | None) -> str:
        """Normalize an answer string for lightweight exact-match comparison."""

        return (value or "").strip().upper().replace(" ", "")

    def _is_answer_correct(
        self,
        student_answer: str | None,
        correct_answer: str | None,
    ) -> bool:
        """Apply a lightweight correctness check for adaptive-profile updates."""

        return self._normalize_answer(student_answer) == self._normalize_answer(
            correct_answer
        )

    async def _ensure_profile_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Ensure the workflow state always carries a learner profile.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch that either preserves the injected profile or creates
            a new one from request identifiers.
        """

        profile = state.get("learner_profile")
        request = state.get("request")
        log_agent_event(
            "adaptive",
            "ensure_profile:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        if profile is not None:
            log_agent_event(
                "adaptive",
                "ensure_profile:existing_profile",
                state=state,
                request=request,
                mode="progress",
            )
            return {"learner_profile": profile}

        request = state.get("request")
        student_id = "anonymous"
        if request is not None:
            student_id = request.student_id or request.user_id or student_id

        loaded_profile = None
        if student_id != "anonymous":
            # Keep all Mongo access on the orchestrator's existing event loop.
            # The repository uses Motor, so bouncing through a helper thread and
            # `asyncio.run()` would risk running DB operations on a different
            # loop than the one that created the async client.
            loaded_profile = await self.load_learner_profile(student_id)
        if loaded_profile is not None:
            log_agent_event(
                "adaptive",
                "ensure_profile:loaded_profile",
                request=request,
                extra={"student_id": student_id},
                mode="completed",
            )
            return {"learner_profile": loaded_profile}

        created_profile = self.service.create_profile(student_id)
        if student_id != "anonymous":
            await self.save_learner_profile(created_profile)
        log_agent_event(
            "adaptive",
            "ensure_profile:created_profile",
            request=request,
            extra={"student_id": student_id},
            mode="completed",
        )
        return {"learner_profile": created_profile}

    async def _update_profile_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Transform graded answers into attempts and replay them into the profile.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch containing the updated learner profile and a compact
            audit summary of what changed.
        """

        profile = state.get("learner_profile")
        request = state.get("request")
        log_agent_event(
            "adaptive",
            "update_profile:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        questions = [ExamQuestion.model_validate(question) for question in state.get("questions", [])]
        answers = [StudentAnswer.model_validate(answer) for answer in state.get("student_answers", [])]
        question_map = {question.question_id: question for question in questions}
        non_empty_answer_count = sum(1 for answer in answers if answer.normalized_answer())

        attempts: list[AdaptiveAttempt] = []
        for answer in answers:
            question = question_map.get(answer.question_id)
            if question is None or not answer.normalized_answer():
                continue
            attempts.append(
                AdaptiveAttempt.from_question(
                    question,
                    is_correct=self._is_answer_correct(
                        answer.normalized_answer(),
                        question.correct_answer,
                    ),
                )
            )

        if not attempts or profile is None:
            no_update_result = {
                "profile_updates": {
                    "attempts_processed": 0,
                    "weak_topics": profile.weak_topics() if profile else [],
                    "strong_topics": profile.strong_topics() if profile else [],
                }
            }
            log_agent_event(
                "adaptive",
                "update_profile:no_attempts",
                state=state,
                request=request,
                extra={
                    "attempts": len(attempts),
                    "answers": len(answers),
                    "non_empty_answers": non_empty_answer_count,
                    "questions": len(questions),
                    "mapped_questions": len(question_map),
                },
                mode="warning",
            )
            return no_update_result

        updated_profile, summaries = self.service.update_profile_from_attempts(
            profile,
            attempts,
        )
        # Persist asynchronously on the same loop used by the manager graph.
        # This avoids the old sync bridge that could create a second event loop
        # and make the shared Motor client behave unpredictably.
        await self.save_learner_profile(updated_profile)
        update_result = {
            "learner_profile": updated_profile,
            "profile_updates": {
                "attempts_processed": len(attempts),
                "updates": summaries,
                "weak_topics": updated_profile.weak_topics(),
                "strong_topics": updated_profile.strong_topics(),
            },
        }
        log_agent_event(
            "adaptive",
            "update_profile:done",
            request=request,
            extra={
                "attempts": len(attempts),
                "summary_count": len(summaries),
                "weak_topics": len(updated_profile.weak_topics()),
                "strong_topics": len(updated_profile.strong_topics()),
            },
            mode="completed",
        )
        return update_result

    async def _recommend_questions_node(self, state: AdaptiveWorkflowState) -> dict[str, Any]:
        """Score the current question bank and select the next adaptive items.

        Args:
            state: Current adaptive workflow state.

        Returns:
            A state patch containing the selected next questions.
        """

        profile = state.get("learner_profile")
        active_plan = state.get("active_plan")
        request = state.get("request")
        log_agent_event(
            "adaptive",
            "recommend_questions:start",
            state=state,
            request=request,
            mode="agent_node",
        )
        answers = [StudentAnswer.model_validate(answer) for answer in state.get("student_answers", [])]
        answered_question_ids = [answer.question_id for answer in answers if answer.question_id]
        questions = [ExamQuestion.model_validate(question) for question in state.get("questions", [])]
        existing_profile_updates = (
            dict(state.get("profile_updates"))
            if isinstance(state.get("profile_updates"), dict)
            else {}
        )

        if profile is None:
            log_agent_event(
                "adaptive",
                "recommend_questions:missing_profile",
                state=state,
                request=request,
                mode="warning",
            )
            return {"selected_questions": []}

        if not questions:
            # Fresh practice flows may arrive without any candidate bank in
            # memory, so we lazily load one from Mongo.
            questions = await self.load_questions(
                request=request,
                profile=profile,
                exclude_question_ids=answered_question_ids,
            )
        elif self._should_refresh_candidate_bank(
            request=request,
            answered_question_ids=answered_question_ids,
        ):
            # The hydrated ``questions`` list is often the just-finished exam.
            # Keep that set for BKT/IRT/CAT profile updates, but do not trap
            # recommendation inside it. Reload a broader candidate pool here so
            # the next backlog can track the learner's goal instead of replaying
            # the same exam corpus.
            questions = await self.load_questions(
                request=request,
                profile=profile,
                exclude_question_ids=answered_question_ids,
            )

        # RAG context is always loaded from Mongo, so this node must await it
        # directly instead of relying on any sync wrapper around async IO.
        rag_context_questions = await self.load_rag_context_questions(
            request=request,
            profile=profile,
            exclude_question_ids=answered_question_ids,
        )
        decision = self.decide_question_strategy(
            request=request,
            profile=profile,
            active_plan=active_plan,
            candidate_questions=questions,
            rag_context_questions=rag_context_questions,
            answered_question_ids=answered_question_ids,
        )

        metadata = request.metadata if request else {}
        requested_total = max(
            1,
            min(
                5,
                max(decision.reuse_count, 0) + max(decision.generate_count, 0),
            ),
        )
        reuse_target = 0
        if decision.mode == "reuse":
            reuse_target = max(1, decision.reuse_count or requested_total)
        elif decision.mode == "mix":
            reuse_target = max(1, decision.reuse_count)

        try:
            db_fit_min_score = float(metadata.get("db_fit_min_score", 0.50))
        except (TypeError, ValueError):
            db_fit_min_score = 0.50
        db_fit_min_score = max(0.0, min(1.0, db_fit_min_score))

        selected_reused: list[ExamQuestion] = []
        reuse_fit = {
            "requested_reuse": reuse_target,
            "ranked_pool": 0,
            "aligned_pool": 0,
            "selected_reuse": 0,
            "min_score": db_fit_min_score,
        }
        if questions and reuse_target > 0:
            selected_reused, reuse_fit = self._select_reused_candidates(
                profile=profile,
                questions=questions,
                exclude_question_ids=answered_question_ids,
                requested_count=min(reuse_target, len(questions)),
                focus_topics=decision.focus_topics,
                learning_goal=self._learning_goal(request),
                min_score=db_fit_min_score,
            )

        base_generation_target = (
            max(decision.generate_count, 0)
            if decision.mode in {"generate", "mix"}
            else 0
        )
        generation_target = max(
            base_generation_target,
            requested_total - len(selected_reused),
        )

        generated_questions: list[ExamQuestion] = []
        if rag_context_questions and generation_target > 0:
            generated_questions = self.generate_questions_from_context(
                request=request,
                profile=profile,
                rag_context_questions=rag_context_questions,
                limit_override=generation_target,
            )

        persisted_generated_count = 0
        if generated_questions:
            upsert_generated = getattr(self.repository, "upsert_generated_questions", None)
            if callable(upsert_generated):
                try:
                    persisted_generated_count = await upsert_generated(
                        generated_questions,
                        user_id=request.user_id if request else None,
                        plan_id=active_plan.plan_id if active_plan else None,
                    )
                except RuntimeError:
                    log_agent_event(
                        "adaptive",
                        "persist_generated_questions_failed",
                        request=request,
                        extra={"generated": len(generated_questions)},
                        mode="warning",
                    )

        selected_questions = self.merge_question_sources(
            reused_questions=selected_reused,
            generated_questions=generated_questions,
            target_limit=requested_total,
        )
        plan_payload = self._build_plan_payload(
            request=request,
            profile=profile,
            active_plan=active_plan,
            decision=decision,
            selected_questions=selected_questions,
            answered_question_ids=answered_question_ids,
        )
        plan_patch = plan_payload if active_plan is not None else None
        plan_proposal = plan_payload if active_plan is None else None
        trace = {
            "decision": decision.model_dump(mode="json"),
            "inputs": {
                "answered_question_ids": answered_question_ids,
                "candidate_question_count": len(questions),
                "rag_context_count": len(rag_context_questions),
                "weak_topics": profile.weak_topics(),
                "strong_topics": profile.strong_topics(),
                "theta": profile.theta,
                "active_plan_id": active_plan.plan_id if active_plan else None,
            },
            "outputs": {
                "reused_question_ids": [question.question_id for question in selected_reused],
                "generated_question_ids": [question.question_id for question in generated_questions],
                "selected_question_ids": [question.question_id for question in selected_questions],
                "reuse_fit": reuse_fit,
                "base_generation_target": base_generation_target,
                "final_generation_target": generation_target,
                "generated_persisted_count": persisted_generated_count,
                "plan_patch_generated": plan_patch is not None,
                "plan_proposal_generated": plan_proposal is not None,
            },
        }
        result = {
            "questions": questions,
            "active_plan": active_plan,
            "rag_context_questions": rag_context_questions,
            "generated_questions": generated_questions,
            "selected_questions": selected_questions,
            "plan_patch": plan_patch,
            "plan_proposal": plan_proposal,
            "profile_updates": {
                **existing_profile_updates,
                "adaptive_trace": trace,
            },
        }
        log_agent_event(
            "adaptive",
            "recommend_questions:selected",
            request=request,
            extra={
                "candidate_questions": len(questions),
                "rag_context_questions": len(rag_context_questions),
                "decision_mode": decision.mode,
                "reuse_count": len(selected_reused),
                "generated_count": len(generated_questions),
                "selected_questions": len(selected_questions),
            },
            mode="completed",
        )
        return result

    async def run(self, state: AdaptiveWorkflowState) -> AdaptiveWorkflowState:
        """Invoke the adaptive workflow without leaving the current event loop.

        The manager graph already runs via `ainvoke(...)`, so the adaptive
        subgraph should stay async from top to bottom. This keeps every Motor
        operation on one loop and removes the need for unsafe sync bridges.
        """

        log_agent_event(
            "adaptive",
            "run:start",
            state=state,
            request=state.get("request"),
            mode="agent_node",
        )
        final_state = await self.graph.ainvoke(
            state,
            config=build_langsmith_invoke_config(
                run_name="AdaptiveAgent.run",
                agent_role="adaptive",
                extra_tags=["adaptive", "question-selection"],
            ),
        )
        log_agent_event(
            "adaptive",
            "run:done",
            state=final_state,
            request=final_state.get("request"),
            mode="completed",
        )
        return final_state

    async def load_learner_profile(self, student_id: str) -> LearnerProfile | None:
        """Load the persisted learner profile from the adaptive profile store.

        This helper intentionally remains async because the repository is backed
        by Motor. Calling it synchronously from a helper thread would re-create
        the exact cross-event-loop problem we are trying to remove.
        """

        try:
            profile = await self.repository.get_learner_profile(student_id)
            log_agent_event(
                "adaptive",
                "load_learner_profile",
                extra={"student_id": student_id, "found": profile is not None},
                mode="progress",
            )
            return profile
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "load_learner_profile_failed",
                extra={"student_id": student_id},
                mode="warning",
            )
            return None

    async def save_learner_profile(self, profile: LearnerProfile) -> None:
        """Persist the latest learner profile snapshot to the adaptive profile store.

        The write is awaited directly so the shared Motor client stays on the
        same event loop as the manager/adaptive graphs.
        """

        try:
            await self.repository.upsert_learner_profile(profile)
            log_agent_event(
                "adaptive",
                "save_learner_profile",
                extra={"student_id": profile.student_id},
                mode="progress",
            )
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "save_learner_profile_failed",
                extra={"student_id": profile.student_id},
                mode="warning",
            )
            return None

    async def load_questions(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        exclude_question_ids: list[str] | None = None,
    ) -> list[ExamQuestion]:
        """Fetch candidate questions from MongoDB for adaptive selection.

        The loader supports a few progressively stronger filters:

        1. ``request.exam_id`` or explicit ``metadata.question_ids``
        2. ``metadata.topic_tags``
        3. weak topics derived from the current learner profile

        This method is async for the same reason as profile load/save: question
        retrieval talks to Mongo through Motor and should stay on one loop.
        """

        metadata = request.metadata if request else {}
        requested_question_ids = metadata.get("question_ids") or []
        requested_topic_tags = metadata.get("topic_tags") or profile.weak_topics()
        requested_limit = metadata.get("question_limit") or metadata.get("limit") or 100
        scoped_exam_id = self._candidate_exam_scope(request, metadata=metadata)

        if not isinstance(requested_question_ids, list):
            requested_question_ids = []
        if not isinstance(requested_topic_tags, list):
            requested_topic_tags = []

        try:
            limit = max(1, int(requested_limit))
        except (TypeError, ValueError):
            limit = 100

        try:
            questions = await self.repository.get_questions(
                exam_id=scoped_exam_id,
                question_ids=requested_question_ids,
                topic_tags=requested_topic_tags,
                exclude_question_ids=exclude_question_ids or [],
                limit=limit,
            )
            log_agent_event(
                "adaptive",
                "load_questions",
                request=request,
                extra={
                    "question_ids": len(requested_question_ids),
                    "topic_tags": len(requested_topic_tags),
                    "exclude_question_ids": len(exclude_question_ids or []),
                    "limit": limit,
                    "result": len(questions),
                },
                mode="progress",
            )
            return questions
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "load_questions_failed",
                request=request,
                extra={"limit": limit},
                mode="warning",
            )
            return []

    async def load_rag_context_questions(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        exclude_question_ids: list[str] | None = None,
    ) -> list[ExamQuestion]:
        """Always retrieve DB-backed question context for adaptive generation.

        Keeping this helper async makes the DB boundary explicit: the adaptive
        workflow awaits Mongo first, then runs deterministic selection / LLM
        decision logic on the resulting in-memory objects.
        """

        metadata = request.metadata if request else {}
        requested_question_ids = metadata.get("rag_question_ids") or metadata.get("question_ids") or []
        requested_topic_tags = metadata.get("rag_topic_tags") or metadata.get("topic_tags") or profile.weak_topics()
        requested_limit = metadata.get("rag_context_limit") or 8
        scoped_exam_id = self._candidate_exam_scope(request, metadata=metadata)

        if not isinstance(requested_question_ids, list):
            requested_question_ids = []
        if not isinstance(requested_topic_tags, list):
            requested_topic_tags = []

        try:
            limit = max(1, int(requested_limit))
        except (TypeError, ValueError):
            limit = 8

        try:
            questions = await self.repository.get_rag_question_context(
                exam_id=scoped_exam_id,
                question_ids=requested_question_ids,
                topic_tags=requested_topic_tags,
                exclude_question_ids=exclude_question_ids or [],
                limit=limit,
            )
            log_agent_event(
                "adaptive",
                "load_rag_context_questions",
                request=request,
                extra={
                    "question_ids": len(requested_question_ids),
                    "topic_tags": len(requested_topic_tags),
                    "exclude_question_ids": len(exclude_question_ids or []),
                    "limit": limit,
                    "result": len(questions),
                },
                mode="progress",
            )
            return questions
        except RuntimeError:
            log_agent_event(
                "adaptive",
                "load_rag_context_questions_failed",
                request=request,
                extra={"limit": limit},
                mode="warning",
            )
            return []

    def generate_questions_from_context(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        rag_context_questions: list[ExamQuestion],
        limit_override: int | None = None,
    ) -> list[ExamQuestion]:
        """Generate new practice questions from mandatory DB-retrieved context."""

        metadata = request.metadata if request else {}
        requested_limit = limit_override or metadata.get("generation_limit") or metadata.get("question_limit") or 3
        try:
            limit = max(1, int(requested_limit))
        except (TypeError, ValueError):
            limit = 3

        generated = self.generator.generate_questions(
            request=request,
            profile=profile,
            context_questions=rag_context_questions,
            limit=limit,
        )
        log_agent_event(
            "adaptive",
            "generate_questions_from_context",
            request=request,
            extra={
                "context_questions": len(rag_context_questions),
                "limit": limit,
                "generated": len(generated),
            },
            mode="completed",
        )
        return generated

    def decide_question_strategy(
        self,
        *,
        request: MessageRequest | None,
        profile: LearnerProfile,
        active_plan: SharedPlanMemory | None,
        candidate_questions: list[ExamQuestion],
        rag_context_questions: list[ExamQuestion],
        answered_question_ids: list[str],
    ) -> AdaptiveSelectionDecision:
        """Nhờ LLM quyết định nên reuse, generate hay mix."""

        metadata = request.metadata if request else {}
        forced_mode = str(metadata.get("adaptive_mode") or "").strip().lower()
        requested_limit = metadata.get("generation_limit") or metadata.get("question_limit") or 3
        try:
            total_target = max(1, min(5, int(requested_limit)))
        except (TypeError, ValueError):
            total_target = 3

        if forced_mode in {"reuse", "generate", "mix"}:
            if forced_mode == "reuse":
                return AdaptiveSelectionDecision(
                    mode="reuse",
                    reasoning="Mode bị ép từ metadata nên adaptive dùng lại câu cũ.",
                    reuse_count=total_target,
                    generate_count=0,
                    confidence=1.0,
                    focus_topics=profile.weak_topics()[:3],
                )
            if forced_mode == "generate":
                return AdaptiveSelectionDecision(
                    mode="generate",
                    reasoning="Mode bị ép từ metadata nên adaptive sinh câu mới từ RAG context.",
                    reuse_count=0,
                    generate_count=total_target,
                    confidence=1.0,
                    focus_topics=profile.weak_topics()[:3],
                )
            return AdaptiveSelectionDecision(
                mode="mix",
                reasoning="Mode bị ép từ metadata nên adaptive kết hợp câu cũ và câu mới.",
                reuse_count=max(1, total_target // 2),
                generate_count=max(1, total_target - (total_target // 2)),
                confidence=1.0,
                focus_topics=profile.weak_topics()[:3],
            )

        if not candidate_questions and not rag_context_questions:
            return AdaptiveSelectionDecision(
                mode="reuse",
                reasoning="Không có candidate questions và cũng không có RAG context.",
                reuse_count=0,
                generate_count=0,
                confidence=0.0,
                focus_topics=[],
            )
        if not candidate_questions:
            return AdaptiveSelectionDecision(
                mode="generate",
                reasoning="Không còn câu cũ phù hợp nên chỉ có thể sinh câu mới.",
                reuse_count=0,
                generate_count=total_target,
                confidence=0.95,
                focus_topics=profile.weak_topics()[:3],
            )
        if not rag_context_questions:
            return AdaptiveSelectionDecision(
                mode="reuse",
                reasoning="Không có RAG context nên chỉ có thể dùng lại câu hiện có.",
                reuse_count=total_target,
                generate_count=0,
                confidence=0.95,
                focus_topics=profile.weak_topics()[:3],
            )

        user_prompt = adaptive_decide_question_strategy_prompt(
            target_limit=total_target,
            intent=str(request.intent) if request else "UNKNOWN",
            learner_theta=profile.theta,
            weak_topics=profile.weak_topics(),
            strong_topics=profile.strong_topics(),
            answered_question_ids=answered_question_ids,
            candidate_question_topics=[question.topic_tags for question in candidate_questions[:12]],
            rag_context_topics=[question.topic_tags for question in rag_context_questions[:12]],
            learning_goal=self._learning_goal(request),
            planner_context=self._planner_context(request, active_plan),
            user_request=(request.content if request else "") or (request.student_message if request else "") or "",
        )
        # Keep provider-native structured output when possible, but gracefully
        # degrade to plain JSON text for backends with limited schema support.
        decision = self._invoke_decision_with_json_fallback(
            user_prompt=user_prompt,
            target_limit=total_target,
            candidate_questions=candidate_questions,
            rag_context_questions=rag_context_questions,
        )

        mode = str(decision.mode or "mix").strip().lower()
        if mode not in {"reuse", "generate", "mix"}:
            mode = "mix"
        decision.mode = mode
        if mode == "reuse":
            decision.reuse_count = max(1, min(total_target, decision.reuse_count or total_target))
            decision.generate_count = 0
        elif mode == "generate":
            decision.reuse_count = 0
            decision.generate_count = max(1, min(total_target, decision.generate_count or total_target))
        else:
            decision.reuse_count = max(1, min(total_target - 1 if total_target > 1 else 1, decision.reuse_count or (total_target // 2 or 1)))
            decision.generate_count = max(1, min(total_target, decision.generate_count or (total_target - decision.reuse_count)))
            while decision.reuse_count + decision.generate_count > total_target:
                if decision.generate_count > decision.reuse_count and decision.generate_count > 1:
                    decision.generate_count -= 1
                elif decision.reuse_count > 1:
                    decision.reuse_count -= 1
                else:
                    break
        return decision

    @staticmethod
    def merge_question_sources(
        *,
        reused_questions: list[ExamQuestion],
        generated_questions: list[ExamQuestion],
        target_limit: int,
    ) -> list[ExamQuestion]:
        """Gộp hai nguồn câu hỏi và loại trùng theo question_id."""

        merged: list[ExamQuestion] = []
        seen: set[str] = set()
        for question in [*reused_questions, *generated_questions]:
            if question.question_id in seen:
                continue
            seen.add(question.question_id)
            merged.append(question)
            if len(merged) >= target_limit:
                break
        return merged

    def update_profile(
        self,
        profile: LearnerProfile,
        attempt: AdaptiveAttempt,
    ) -> tuple[LearnerProfile, dict]:
        """Delegate one attempt update to the underlying adaptive service."""

        return self.service.update_profile(profile, attempt)

    def recommend_questions(
        self,
        profile: LearnerProfile,
        questions: list[ExamQuestion],
        *,
        limit: int = 5,
    ) -> list[QuestionRecommendation]:
        """Delegate question ranking to the underlying adaptive service."""

        return self.service.recommend_questions(profile, questions, limit=limit)
