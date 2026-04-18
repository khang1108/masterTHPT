from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from master.logging.logger import Logger

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
        self.logger = Logger(agent_role)
        self.system_prompt : str = None

    def build_messages(self, content: str | BaseMessage) -> list[BaseMessage]:
        messages: list[BaseMessage] = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt.strip()))
        if isinstance(content, BaseMessage):
            messages.append(content)
        else:
            messages.append(HumanMessage(content=content))
        return messages

    async def execute_step(
        self,
        state: dict[str, Any],
        *,
        step: Any | None = None,
    ) -> dict[str, Any]:
        """Optional structured execution contract for manager-orchestrated steps.

        Legacy agents can continue using their existing entrypoints. The newer
        manager/planner layer may call this method when an agent supports a
        request-level execution step contract.
        """

        raise NotImplementedError(
            f"{type(self).__name__} does not implement structured step execution"
        )

    @abstractmethod
    async def run(self, input: str) -> str:
        """Run the agent.

        Args:
            input: The input to the agent.
        """
        pass
