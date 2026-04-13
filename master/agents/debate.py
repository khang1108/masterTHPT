# master/agents/debate.py
from typing import Union
from master.agents.common.message import (
    MessageRequest, MessageResponse, Intent, ExamQuestion,
)
from master.agents.teacher import TeacherAgent
from master.agents.verifier import VerifierAgent, VerifiedResult

import asyncio


class AgentPipeline:
    """Điều phối Teacher ↔ Verifier cho mọi intent."""

    def __init__(self):
        self.teacher  = TeacherAgent()
        self.verifier = VerifierAgent()

    async def setup(self):
        await asyncio.gather(self.teacher.setup(), self.verifier.setup())

    async def run(
        self,
        request: MessageRequest,
        thread_id: str = "default",
        max_round: int = 3,
    ) -> Union[MessageResponse, VerifiedResult, list[ExamQuestion]]:
        """
        Luồng chung cho mọi intent:
          1. Teacher draft
          2. Verifier verify → nếu disagree, Teacher debate → lặp lại
          3. Verifier finalize (hành động tuỳ intent):
               ASK_HINT / REVIEW_MISTAKE → MessageResponse
               PREPROCESS               → ghi DB, trả list[ExamQuestion]
               VIEW_ANALYSIS / EXAM_PRACTICE → VerifiedResult
        """
        # Bước 1: Teacher tạo draft
        state = await self.teacher.run_draft(request, max_round=max_round, thread_id=thread_id)

        # Bước 2–3: Vòng debate với Verifier
        for _ in range(max_round):
            verdict, result = await self.verifier.verify(state, thread_id=thread_id)

            if verdict == "agree":
                return result   # MessageResponse | VerifiedResult | list[ExamQuestion]

            # Verifier chưa đồng ý → Teacher debate lại
            state = await self.teacher.run_debate(result, thread_id=thread_id)

        # Hết max_round: ép finalize với state tốt nhất hiện có
        _, final = await self.verifier.verify(state, thread_id=f"{thread_id}-final")
        return final