from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Awaitable, Callable, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage

from master.agents.common.llm_client import LLMClient
from master.agents.common.message import TaskRequest, TaskResponse
from master.logging.logger import Logger

import os

class BaseAgent(ABC):
    def __init__(
        self,
        agent_role: str,
    ):
        """Initialize the base agent.

        Args:
            name: The name of the agent.
            description: The description of the agent.
            system_prompt: The system prompt of the agent.
        """
        self._role = agent_role
        self._llm: Optional[BaseChatModel] = None
        self._tools: list = []
        self._trial: list[str] = []
        self.logger = Logger(f"agent.{agent_role}", service_prefix="Agent Service")

    @abstractmethod
    async def run(self, input: str) -> str:
        """Run the agent.

        Args:
            input: The input to the agent.
        """
        pass