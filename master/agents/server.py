from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from master.agents.common.agent_logging import log_agent_event
from master.agents.parser.parser import ParserAgent
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
        log_agent_event(
            "pipeline",
            "initialized",
            extra={"thread_id": self.thread_id},
            mode="completed",
        )

    async def setup(self):
        log_agent_event("pipeline", "setup:start", extra={"thread_id": self.thread_id}, mode="agent_node")
        await self.parser.setup()
        await self.teacher.setup()
        await self.verifier.setup()
        await self.build_pipeline()
        log_agent_event("pipeline", "setup:done", extra={"thread_id": self.thread_id}, mode="completed")

    async def build_pipeline(self):
        log_agent_event("pipeline", "build_pipeline:start", extra={"thread_id": self.thread_id}, mode="agent_node")
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
        log_agent_event("pipeline", "build_pipeline:done", extra={"thread_id": self.thread_id}, mode="completed")

    async def run_superstep(self, request):
        log_agent_event("pipeline", "run_superstep:start", request=request, extra={"thread_id": self.thread_id}, mode="agent_node")
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
        log_agent_event("pipeline", "cleanup:start", extra={"thread_id": self.thread_id}, mode="agent_node")
        await ToolsRegistry.cleanup()
        log_agent_event("pipeline", "cleanup:done", extra={"thread_id": self.thread_id}, mode="completed")


async def run_superstep(request):
    """Wrapper async mức module để orchestrator gọi pipeline cũ dễ hơn."""

    pipeline = Pipeline()
    await pipeline.setup()

    try:
        return await pipeline.run_superstep(request)
    finally:
        await pipeline.cleanup()
