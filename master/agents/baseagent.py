from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Awaitable, Callable

import os


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
    ):
        """Initialize the base agent.

        Args:
            name: The name of the agent.
            description: The description of the agent.
            system_prompt: The system prompt of the agent.
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt

    @abstractmethod
    async def run(self, input: str) -> str:
        """Run the agent.

        Args:
            input: The input to the agent.
        """
        pass