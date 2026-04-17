from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from master.agents.common.state import AgentState
from master.agents.common.message import MessageRequest, StudentAnswer, Intent
from master.agents.teacher.teacher import TeacherAgent
from master.agents.verifier.verifier import VerifierAgent
from master.agents.common.tools import ToolsRegistry

import asyncio
import uuid
import json

load_dotenv(override=True)

class Pipeline:
    def __init__(self):
        self.teacher = TeacherAgent()
        self.verifier = VerifierAgent()
        self.memory = MemorySaver()
        self.thread_id = str(uuid.uuid4())
        self.graph = None

    async def setup(self):
        await self.teacher.setup()
        await self.verifier.setup()
        await self.build_pipeline()

    async def build_pipeline(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("Tools", self.teacher.get_tool_node)
        graph_builder.add_node("Teacher", self.teacher.teacher)
        graph_builder.add_node("Verifier", self.verifier.verifier)

        # Teacher subgraph
        graph_builder.add_edge(START, "Teacher")
        graph_builder.add_conditional_edges(
            "Teacher", 
            self.teacher.teacher_router, 
            {"tools": "Tools", "verify": "Verifier", "END": END}    
        )
        graph_builder.add_edge("Tools", "Teacher")

        # Verifier subgraph
        graph_builder.add_conditional_edges(
            "Verifier", 
            self.verifier.verifier_router, 
            {"tools": "Tools", "teacher": "Teacher", "END": END}    
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, request):
        config = {"configurable": {"thread_id": self.thread_id}}

        state = AgentState(
            request=request,
            phase="draft",
            learner_profile=None,
            exam_id=None,
            questions=[],
            student_answers=[],
            round=0,
            max_round=3,
            is_agreed=[],
            confidence=[],
            reasoning="",
            teacher_feedback=[],
            verifier_feedback=[],
            grade_result=None,
            solutions=None,
            verified_solutions=None,
            selected_questions=None,
            profile_updates=None,
        )
        result = await self.graph.ainvoke(state, config=config)

        return result.get("response", [])

    async def cleanup(self):
        await ToolsRegistry.cleanup()


async def main():
    pipeline = Pipeline()
    await pipeline.setup()

    request = MessageRequest(
        intent=Intent.PREPROCESS.value,
        student_id="student_123",
        student_answers=[StudentAnswer(question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd', student_answer="B")],
        question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd',
        parser_output=[{
            "id": '07931d51-d61b-5a58-bb3b-351a8edccbcd',
            "type": 'multiple_choice',
            "content": 'Cho hình nón (N) có đường cao $SO = h$ và bán kính đáy bằng $r$, gọi M là điểm trên đoạn SO, đặt $OM = x,\\;0 < x < h$. Gọi (C) là thiết diện của mặt phẳng $(\\alpha)$ vuông góc với SO tại M, với hình nón (N). Tìm $x$ để thể tích khối nón đỉnh O đáy là (C) lớn nhất.',
            "options": [
                'A.$\\frac{h}{3}$',
                'B.$\\frac{h\\sqrt{2}}{2}.$',
                'C.$\\frac{h}{2}.$',
                'D.$\\frac{h\\sqrt{3}}{2}.$'
            ],
        }]
    )
    request = MessageRequest(
        intent=Intent.ASK_HINT.value,
        student_id="student_123",
        student_answers=[StudentAnswer(question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd', student_answer="B")],
        question_id='07931d51-d61b-5a58-bb3b-351a8edccbcd',
        parser_output=[{
            "id": '07931d51-d61b-5a58-bb3b-351a8edccbcd',
            "type": 'multiple_choice',
            "content": 'Cho hình nón (N) có đường cao $SO = h$ và bán kính đáy bằng $r$, gọi M là điểm trên đoạn SO, đặt $OM = x,\\;0 < x < h$. Gọi (C) là thiết diện của mặt phẳng $(\\alpha)$ vuông góc với SO tại M, với hình nón (N). Tìm $x$ để thể tích khối nón đỉnh O đáy là (C) lớn nhất.',
            "options": [
                'A.$\\frac{h}{3}$',
                'B.$\\frac{h\\sqrt{2}}{2}.$',
                'C.$\\frac{h}{2}.$',
                'D.$\\frac{h\\sqrt{3}}{2}.$'
            ],
        }]
    )

    result = await pipeline.run_superstep(request)
    try:
        print(json.dumps(result, ensure_ascii=True, default=str))
    except (BrokenPipeError, ValueError):
        pass
    finally:
        await pipeline.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
        