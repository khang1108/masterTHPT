# master/pipeline/grading_pipeline.py
from master.agents.common.message import MessageRequest
from master.agents.teacher import TeacherAgent
from master.agents.verifier import VerifierAgent, VerifiedResult

import asyncio


class GradingPipeline:
    def __init__(self):
        self.teacher  = TeacherAgent()
        self.verifier = VerifierAgent()

    async def setup(self):
        # Khởi tạo song song để tiết kiệm thời gian
        await asyncio.gather(
            self.teacher.setup(),
            self.verifier.setup(),
        )

    async def run(
        self,
        request: MessageRequest,
        thread_id: str = "default",
        max_round: int = 3,
    ) -> VerifiedResult:
        
        # ── Vòng 1: Teacher chấm nháp ─────────────────────────────────────────
        debate_state = await self.teacher.run_draft(
            request,
            max_round=max_round,
            thread_id=thread_id,
        )

        # ── Vòng lặp: Verifier kiểm tra, Teacher tranh luận ───────────────────
        for round_num in range(max_round):
            verdict, result = await self.verifier.verify(
                debate_state,
                thread_id=thread_id,
            )

            # Verifier đồng ý toàn bộ → xong
            if verdict == "agree":
                return result  # VerifiedResult

            # Verifier chưa đồng ý → Teacher debate lại với feedback mới
            # result lúc này là DebateState đã có verifier_feedback
            debate_state = await self.teacher.run_debate(
                result,
                thread_id=thread_id,
            )

        # ── Hết max_round: ép Verifier finalize với kết quả tốt nhất hiện có ──
        _, final = await self.verifier.verify(
            debate_state,
            thread_id=f"{thread_id}-force-final",
        )

        # Nếu vẫn disagree sau force → wrap thủ công để không crash downstream
        if not isinstance(final, VerifiedResult):
            final = _build_fallback_result(debate_state)

        return final


def _build_fallback_result(debate_state) -> VerifiedResult:
    """Fallback khi hết round mà Verifier vẫn không agree."""
    from master.agents.verifier import VerifiedResult, VerifiedQuestion

    questions = []
    for o in debate_state["outputs"]:
        sa     = o.student_ans
        draft  = o.draft_result
        debate = o.debate_result
        questions.append(VerifiedQuestion(
            exam_id         = debate_state.get("exam_id", ""),
            question_id     = sa.question_id,
            final_score     = (debate.final_score if debate else draft.score if draft else 0.0),
            is_correct      = (draft.is_correct if draft else False),
            reasoning_chain = (
                ([f"[Draft] {draft.reasoning}"]   if draft  else []) +
                ([f"[Debate] {debate.teacher_rebuttal}"] if debate else [])
            ),
            consensus_note  = "Hết max_round, dùng kết quả cuối của Teacher",
        ))

    return VerifiedResult(
        exam_id         = debate_state.get("exam_id", ""),
        student_id      = debate_state.get("student_id"),
        session_id      = debate_state.get("session_id"),
        questions       = questions,
        total_questions = len(questions),
        total_correct   = sum(1 for q in questions if q.is_correct),
        total_score     = sum(q.final_score or 0.0 for q in questions),
    )


# ── Entry point từ NestJS ──────────────────────────────────────────────────────

async def main():
    pipeline = GradingPipeline()
    await pipeline.setup()

    request = MessageRequest(
        intent="VIEW_ANALYSIS",
        user_message="Chấm bài thi",
        metadata={
            "exam_id":         "bed1f84d-...",
            "student_id":      "student-001",
            "session_id":      "session-abc",
            "total_questions": 2,
            "exam_sections":   [],
            "student_answers": [...],
        },
    )

    result: VerifiedResult = await pipeline.run(
        request,
        thread_id="exam-session-001",
        max_round=3,
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())