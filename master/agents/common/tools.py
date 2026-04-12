# master/agents/common/agent_mixin.py

from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Type
import asyncio
import os

load_dotenv(override=True)
MONGO_URI = os.getenv("MONGO_URI")

class ToolRegistry:
    # ── Shared across all agents (class-level cache) ───────────────────────────
    _shared_tools: list[BaseTool] | None = None
    _shared_tool_map: dict[str, BaseTool] | None = None
    _shared_browser = None
    _shared_playwright = None
    _mongo_client = AsyncIOMotorClient(MONGO_URI)

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup_tools(self, llm):
        """Gọi trong setup() của agent. llm là base LLM chưa bind tools."""
        if ToolRegistry._shared_tools is None:
            await self._init_tools()

        self._tools          = ToolRegistry._shared_tools
        self._tool_map       = ToolRegistry._shared_tool_map
        self.browser         = ToolRegistry._shared_browser
        self.playwright      = ToolRegistry._shared_playwright
        self._llm            = llm
        self._llm_with_tools = llm.bind_tools(self._tools)

    async def _init_tools(self):
        playwright      = await async_playwright().start()
        browser         = await playwright.chromium.launch(headless=False)
        browser_tools   = PlayWrightBrowserToolkit.from_browser(async_browser=browser).get_tools()
        file_tools      = FileManagementToolkit().get_tools()
        repl_tool       = PythonREPLTool()
        all_tools       = browser_tools + file_tools + [repl_tool]

        ToolRegistry._shared_tools      = all_tools
        ToolRegistry._shared_tool_map   = {t.name: t for t in all_tools}
        ToolRegistry._shared_browser    = browser
        ToolRegistry._shared_playwright = playwright

    # ── MongoDB ────────────────────────────────────────────────────────────────

    async def get_data(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
        length: int = 10,
    ):
        collection = ToolRegistry._mongo_client[database_name][collection_name]
        return await collection.find(query).to_list(length=length)

    # ── ReAct loop ─────────────────────────────────────────────────────────────

    async def _execute_tool_calls(self, tool_calls: list) -> list[ToolMessage]:
        async def _call_one(tc) -> ToolMessage:
            tool = self._tool_map.get(tc["name"])
            if tool is None:
                content = f"Tool '{tc['name']}' không tồn tại"
            else:
                try:
                    content = str(await tool.ainvoke(tc["args"]))
                except Exception as e:
                    content = f"Tool error: {e}"
            return ToolMessage(content=content, tool_call_id=tc["id"])

        return await asyncio.gather(*[_call_one(tc) for tc in tool_calls])

    async def _run_with_tools(
        self,
        prompt: str,
        output_schema: Type[BaseModel],
        max_tool_rounds: int = 5,
    ) -> BaseModel:
        messages = [HumanMessage(content=prompt)]

        for _ in range(max_tool_rounds):
            response: AIMessage = await asyncio.to_thread(
                self._llm_with_tools.invoke, messages
            )
            messages.append(response)

            if not response.tool_calls:
                break

            tool_messages = await self._execute_tool_calls(response.tool_calls)
            messages.extend(tool_messages)

        return await asyncio.to_thread(
            self._llm.with_structured_output(output_schema).invoke,
            messages,
        )

    # ── Cleanup ────────────────────────────────────────────────────────────────

    @classmethod
    async def cleanup(cls):
        if cls._shared_browser:
            await cls._shared_browser.close()
        if cls._shared_playwright:
            await cls._shared_playwright.stop()
        cls._shared_tools      = None
        cls._shared_tool_map   = None
        cls._shared_browser    = None
        cls._shared_playwright = None

tools = ToolRegistry()