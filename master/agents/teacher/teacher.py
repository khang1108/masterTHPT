from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from 
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage
from master.agents import BaseAgent
from master.agents.common import ExamData
from master.agents.common import ToolRegistry
from master.agents.common import LLMClient

class TeacherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_role="teacher",
        )
        self.llm_with_tools = None
        self.llm_with_output = None
        self.tools = None
        self.browser = None
        self.playwright = None
        self.memory = MemorySaver()
    
    async def setup(self):
        self.logger.info("Setting up the teacher agent...")
        self._tools = await ToolRegistry.get_all_tools()
        self._llm = await LLMClient.chat_model()
        self.llm_with_tools = self._llm.bind_tools(self._tools)
        

