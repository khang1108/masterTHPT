from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from master.agents.common.state import AgentState
from master.agents.common.message import MessageRequest, StudentAnswer, Intent
from master.agents.parser.parser import ParserAgent
from master.agents.teacher.teacher import TeacherAgent
from master.agents.verifier.verifier import VerifierAgent
from master.agents.common.tools import ToolsRegistry

import asyncio
import uuid
import json

load_dotenv(override=True)

class Pipeline:
    def __init__(self):
        self.parser = ParserAgent()
        self.teacher = TeacherAgent()
        self.verifier = VerifierAgent()
        self.memory = MemorySaver()
        self.thread_id = str(uuid.uuid4())
        self.graph = None

    async def setup(self):
        await self.parser.setup()
        await self.teacher.setup()
        await self.verifier.setup()
        await self.build_pipeline()

    async def build_pipeline(self):
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("Parser", self.parser.parser)
        graph_builder.add_node("Teacher", self.teacher.teacher)
        graph_builder.add_node("Verifier", self.verifier.verifier)

        # Teacher subgraph
        graph_builder.add_conditional_edges(
            START, 
            self.parser.parser_router, 
            {"parser": "Parser", "teacher": "Teacher"}
        )
        graph_builder.add_edge("Parser", "Teacher")

        graph_builder.add_conditional_edges(
            "Teacher", 
            self.teacher.teacher_router, 
            {"verify": "Verifier", "END": END}
        )

        # Verifier subgraph
        graph_builder.add_conditional_edges(
            "Verifier", 
            self.verifier.verifier_router, 
            {"teacher": "Teacher", "END": END}
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, request):
        config = {"configurable": {"thread_id": self.thread_id}}
        
        # Clean up existing debug output
        import os
        if request.intent == Intent.PREPROCESS.value and os.path.exists("preprocess_output.json"):
            os.remove("preprocess_output.json")

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

        return result

    async def cleanup(self):
        await ToolsRegistry.cleanup()


async def main():
    pipeline = Pipeline()
    await pipeline.setup()
    
    request = MessageRequest(
		intent=Intent.PREPROCESS.value,
        student_id="69df0e1d0e91c4f3d1d6353f",
		question_id="07931d51-d61b-5a58-bb3b-351a8edccbcd",
        # file_path="c:\\Users\\abcsd\\Downloads\\Đề cuối kỳ 2 Toán 10 năm 2024 - 2025 trường THPT Lê Hồng Phong - Đắk Lắk - TOANMATH.com.pdf"
        # file_path="c:\\Users\\abcsd\\Downloads\\Đề cuối kỳ 2 Toán 11 năm 2024 - 2025 trường THPT Lê Hồng Phong - Đắk Lắk - TOANMATH.com.pdf"
        # file_path="c:\\Users\\abcsd\\Downloads\\Đề cuối kỳ 2 Toán 12 năm 2024 - 2025 trường THPT Lê Hồng Phong - Đắk Lắk - TOANMATH.com.pdf"
        # file_path="c:\\Users\\abcsd\\Downloads\\Đề kiểm tra cuối học kì 2 Toán 12 năm 2025 – 2026 sở GD&ĐT Bắc Ninh.pdf"
        file_path="c:\\Users\\abcsd\\Downloads\\de-khao-sat-chat-luong-toan-12-dot-2-nam-2025-2026-so-gddt-phu-tho.pdf"
        # file_path="c:\\Users\\abcsd\\Downloads\\de-thi-thu-tot-nghiep-thpt-2026-mon-toan-lan-2-so-gddt-son-la (1).pdf"
        # file_path="c:\\Users\\abcsd\\Downloads\\de-khao-sat-chat-luong-toan-12-dot-2-nam-2025-2026-so-gddt-phu-tho.pdf"
    )

    try:
        result = await pipeline.run_superstep(request)
        # print(json.dumps(result, ensure_ascii=True, default=str))
    except (BrokenPipeError, ValueError):
        pass
    finally:
        await pipeline.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
        
