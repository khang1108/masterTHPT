"""Shared tool registry and ReAct loop helpers for agent modules."""

from __future__ import annotations

import asyncio
import os
from typing import Type

from dotenv import load_dotenv
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_experimental.tools import PythonREPLTool
from langgraph.prebuilt import ToolNode
from motor.motor_asyncio import AsyncIOMotorClient
from playwright.async_api import async_playwright
from pydantic import BaseModel

from .langsmith import build_langsmith_invoke_config

load_dotenv(override=True)
MONGO_URI = os.getenv("MONGO_URI")


class ToolsRegistry:
    """Mixin that centralizes shared tools, Mongo helpers, and the ReAct loop.

    Tool instances are cached at class level so multiple agents can share the
    same browser and utility tool setup without repeatedly re-initializing them.
    """

    _shared_tools: list[BaseTool] | None = None
    _shared_tool_map: dict[str, BaseTool] | None = None
    _shared_tool_node: ToolNode | None = None
    _shared_browser = None
    _shared_playwright = None
    _mongo_client = AsyncIOMotorClient(MONGO_URI)
    _tools_init_lock = asyncio.Lock()

    def _log_tools(self, message: str) -> None:
        """Log tool-related lifecycle events through the agent logger when available."""

        if hasattr(self, "logger") and hasattr(self.logger, "tools_node"):
            self.logger.tools_node(message)
        else:
            print(f"[INFO] [tools] {message}")

    async def setup_tools(self, llm) -> None:
        """Attach the shared toolset to the current agent and bind it to an LLM.

        Args:
            llm: Base LLM before tool binding.
        """

        self._log_tools("setup_tools started")
        await self.ensure_shared_tools_initialized()
        self._attach_shared_tools_to_agent(llm)
        self._log_tools(f"setup_tools completed; total tools={len(self._tools)}")

    async def ensure_shared_tools_initialized(self) -> None:
        """Initialize the shared tool cache exactly once per process."""

        if ToolsRegistry._shared_tools is not None:
            self._log_tools("tool cache hit; reusing shared tools")
            return

        async with ToolsRegistry._tools_init_lock:
            if ToolsRegistry._shared_tools is None:
                self._log_tools("tool cache miss; initializing shared tools")
                await self._init_tools()
            else:
                self._log_tools("tool cache hit after lock; reusing shared tools")

    def _attach_shared_tools_to_agent(self, llm) -> None:
        """Attach the shared tool cache to the current agent instance."""

        if ToolsRegistry._shared_tools is None:
            raise RuntimeError("Shared tools chưa được khởi tạo")

        self._tools = ToolsRegistry._shared_tools
        self._tool_map = ToolsRegistry._shared_tool_map
        self._tool_node = ToolsRegistry._shared_tool_node
        self.browser = ToolsRegistry._shared_browser
        self.playwright = ToolsRegistry._shared_playwright
        self._llm = llm
        self._llm_with_tools = llm.bind_tools(self._tools)

    async def _init_tools(self) -> None:
        """Initialize browser tools, file tools, and the Python REPL once."""

        self._log_tools("initializing Playwright browser and toolkits")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        browser_tools = PlayWrightBrowserToolkit.from_browser(
            async_browser=browser
        ).get_tools()
        file_tools = FileManagementToolkit().get_tools()
        repl_tool = PythonREPLTool()
        all_tools = browser_tools + file_tools + [repl_tool]
        tool_node = ToolNode(all_tools)

        ToolsRegistry._shared_tools = all_tools
        ToolsRegistry._shared_tool_map = {tool.name: tool for tool in all_tools}
        ToolsRegistry._shared_tool_node = tool_node
        ToolsRegistry._shared_browser = browser
        ToolsRegistry._shared_playwright = playwright
        self._log_tools("shared tools initialized")

    async def get_data(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
        length: int = 10,
    ) -> list:
        """Fetch documents from MongoDB using a simple query helper."""

        collection = ToolsRegistry._mongo_client[database_name][collection_name]
        return await collection.find(query).to_list(length=length)

    async def insert_data(
        self,
        database_name: str,
        collection_name: str,
        documents: list[dict],
    ) -> None:
        """Insert one or more documents into MongoDB."""

        if not documents:
            return
        collection = ToolsRegistry._mongo_client[database_name][collection_name]
        await collection.insert_many(documents)

    def get_tool_node(self) -> ToolNode:
        """Return the shared ``ToolNode`` used by LangGraph workflows."""

        return self._tool_node

    async def _execute_tool_calls(self, tool_calls: list) -> list[ToolMessage]:
        """Execute all requested tool calls concurrently and return tool messages."""

        async def _call_one(tool_call) -> ToolMessage:
            self._log_tools(f"tool call start: {tool_call.get('name')}")
            tool = self._tool_map.get(tool_call["name"])
            if tool is None:
                content = f"Tool '{tool_call['name']}' không tồn tại"
            else:
                try:
                    content = str(await tool.ainvoke(tool_call["args"]))
                except Exception as exc:  # pragma: no cover - defensive logging path
                    content = f"Tool error: {exc}"
            self._log_tools(f"tool call end: {tool_call.get('name')}")
            return ToolMessage(content=content, tool_call_id=tool_call["id"])

        return await asyncio.gather(*[_call_one(tool_call) for tool_call in tool_calls])

    async def _run_with_tools(
        self,
        prompt: str,
        output_schema: Type[BaseModel],
        max_tool_rounds: int = 5,
    ) -> BaseModel:
        """Run a lightweight ReAct loop and extract structured output at the end.

        Args:
            prompt: User/task prompt passed to the tool-aware LLM.
            output_schema: Pydantic schema used for the final structured parse.
            max_tool_rounds: Maximum number of tool-using reasoning rounds.

        Returns:
            A parsed instance of ``output_schema``.
        """

        messages = [HumanMessage(content=prompt)]
        self._log_tools(
            f"_run_with_tools start; max_tool_rounds={max_tool_rounds}, prompt_len={len(prompt)}"
        )
        role_name = getattr(self, "_role", self.__class__.__name__).strip().lower()

        for round_idx in range(max_tool_rounds):
            response: AIMessage = await asyncio.to_thread(
                self._llm_with_tools.invoke,
                messages,
                build_langsmith_invoke_config(
                    run_name=f"{self.__class__.__name__}.tool_call_round",
                    agent_role=role_name,
                    extra_tags=["react-loop", "tool-aware"],
                    extra_metadata={"tool_round": round_idx + 1},
                ),
            )
            messages.append(response)

            self._log_tools(
                f"tool round {round_idx + 1}/{max_tool_rounds}; tool_calls={len(response.tool_calls or [])}"
            )

            if not response.tool_calls:
                break

            tool_messages = await self._execute_tool_calls(response.tool_calls)
            messages.extend(tool_messages)

        result = await asyncio.to_thread(
            self._llm.with_structured_output(output_schema).invoke,
            messages,
            build_langsmith_invoke_config(
                run_name=f"{self.__class__.__name__}.structured_output",
                agent_role=role_name,
                extra_tags=["structured-output"],
                extra_metadata={
                    "output_schema": output_schema.__name__,
                    "message_count": len(messages),
                },
            ),
        )
        self._log_tools("_run_with_tools completed")
        return result

    @classmethod
    async def cleanup(cls) -> None:
        """Close shared browser resources and reset the shared tool cache."""

        if cls._shared_browser:
            await cls._shared_browser.close()
        if cls._shared_playwright:
            await cls._shared_playwright.stop()
        cls._shared_tools = None
        cls._shared_tool_map = None
        cls._shared_tool_node = None
        cls._shared_browser = None
        cls._shared_playwright = None
