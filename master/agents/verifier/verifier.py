from typing import Annotated, List, Any, Optional, Dict
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tools import get_all_tools
from master.agents import BaseAgent
from master.agents.teacher import State

class VerifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Verifier Agent",
            description="Chuyên gia Đánh giá / Giám khảo AI giàu kinh nghiệm, có khả năng đánh giá chính xác và công bằng các câu trả lời của Teacher Agent dựa trên tiêu chí đã được xác định.",
            system_prompt="Bạn là một Chuyên gia Đánh giá / Giám khảo AI giàu kinh nghiệm. Nhiệm vụ chính của bạn là đánh giá chính xác và công bằng các câu trả lời của Teacher Agent dựa trên tiêu chí đã được xác định."
        )

        self.verifier_llm_with_tools = None
        self.verifier_llm_with_output = None
        self.tools = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await get_all_tools()
        verifier_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
        self.verifier_llm_with_tools = verifier_llm.bind_tools(self.tools)

        await self.build_graph()