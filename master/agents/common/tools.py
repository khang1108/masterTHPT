# master/agents/common/tools_registry.py

from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Type
from dotenv import load_dotenv
import asyncio
import os

load_dotenv(override=True)
MONGO_URI = os.getenv("MONGO_URI")

class ToolsRegistry:
    # ── Class-level cache (dùng chung toàn bộ agent instances) ────────────────
    _shared_tools: list[BaseTool] | None = None
    _shared_tool_map: dict[str, BaseTool] | None = None
    _shared_tool_node: ToolNode | None = None
    _shared_browser = None
    _shared_playwright = None
    _mongo_client = AsyncIOMotorClient(MONGO_URI)
    _tools_init_lock = asyncio.Lock()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _log_tools(self, message: str):
        if hasattr(self, "logger") and hasattr(self.logger, "tools_node"):
            self.logger.tools_node(message)
        else:
            print(f"[INFO] [tools] {message}")

    async def setup_tools(self, llm):
        """
        Gọi trong setup() của agent.
        llm: base LLM chưa bind tools (LLMClient.chat_model()).
        """
        self._log_tools("setup_tools started")
        await self.ensure_shared_tools_initialized()
        self._attach_shared_tools_to_agent(llm)
        self._log_tools(f"setup_tools completed; total tools={len(self._tools)}")

    async def ensure_shared_tools_initialized(self):
        """Khởi tạo shared tools đúng một lần cho toàn bộ process."""
        if ToolsRegistry._shared_tools is not None:
            self._log_tools("tool cache hit; reusing shared tools")
            return

        async with ToolsRegistry._tools_init_lock:
            if ToolsRegistry._shared_tools is None:
                self._log_tools("tool cache miss; initializing shared tools")
                await self._init_tools()
            else:
                self._log_tools("tool cache hit after lock; reusing shared tools")

    def _attach_shared_tools_to_agent(self, llm):
        """Gắn shared tools đã cache vào agent hiện tại và bind vào LLM."""
        if ToolsRegistry._shared_tools is None:
            raise RuntimeError("Shared tools chưa được khởi tạo")

        self._tools = ToolsRegistry._shared_tools
        self._tool_map = ToolsRegistry._shared_tool_map
        self._tool_node = ToolsRegistry._shared_tool_node
        self.browser = ToolsRegistry._shared_browser
        self.playwright = ToolsRegistry._shared_playwright
        self._llm = llm
        self._llm_with_tools = llm.bind_tools(self._tools)

    async def _init_tools(self):
        """Khởi tạo tất cả tools một lần duy nhất."""
        self._log_tools("initializing Playwright browser and toolkits")
        playwright    = await async_playwright().start()
        browser       = await playwright.chromium.launch(headless=True)
        browser_tools = PlayWrightBrowserToolkit.from_browser(
            async_browser=browser
        ).get_tools()
        file_tools    = FileManagementToolkit().get_tools()
        repl_tool     = PythonREPLTool()
        all_tools     = browser_tools + file_tools + [repl_tool]

        # Tạo ToolNode cho LangSmith tracking
        tool_node = ToolNode(all_tools)

        ToolsRegistry._shared_tools      = all_tools
        ToolsRegistry._shared_tool_map   = {t.name: t for t in all_tools}
        ToolsRegistry._shared_tool_node  = tool_node
        ToolsRegistry._shared_browser    = browser
        ToolsRegistry._shared_playwright = playwright
        self._log_tools(f"shared tools initialized")

    # ── MongoDB ────────────────────────────────────────────────────────────────

    async def get_data(
        self,
        database_name: str,
        collection_name: str,
        query: dict,
        length: int = 10,
    ) -> list:
        collection = ToolsRegistry._mongo_client[database_name][collection_name]
        return await collection.find(query).to_list(length=length)

    async def insert_data(
        self,
        database_name: str,
        collection_name: str,
        documents: list[dict],
    ):
        """Insert nhiều document vào MongoDB."""
        if not documents:
            return
        collection = ToolsRegistry._mongo_client[database_name][collection_name]
        await collection.insert_many(documents)

    # ── ReAct loop ─────────────────────────────────────────────────────────────

    def get_tool_node(self) -> ToolNode:
        """
        Trả về ToolNode đã khởi tạo cho việc add vào LangGraph.
        ToolNode này sẽ tự động gọi tools và LangSmith sẽ track được.
        
        Cách sử dụng:
          builder.add_node("tools", agent.get_tool_node())
        """
        return self._tool_node

    async def _execute_tool_calls(self, tool_calls: list) -> list[ToolMessage]:
        """Thực thi tất cả tool calls song song."""
        async def _call_one(tc) -> ToolMessage:
            self._log_tools(f"tool call start: {tc.get('name')}")
            tool = self._tool_map.get(tc["name"])
            if tool is None:
                content = f"Tool '{tc['name']}' không tồn tại"
            else:
                try:
                    content = str(await tool.ainvoke(tc["args"]))
                except Exception as e:
                    content = f"Tool error: {e}"
            self._log_tools(f"tool call end: {tc.get('name')}")
            return ToolMessage(content=content, tool_call_id=tc["id"])

        return await asyncio.gather(*[_call_one(tc) for tc in tool_calls])

    async def _run_with_tools(
        self,
        prompt: str,
        output_schema: Type[BaseModel],
        max_tool_rounds: int = 5,
    ) -> BaseModel:
        """
        ReAct loop:
          1. LLM (có tools) suy luận, gọi tools nếu cần
          2. Lặp cho đến khi không còn tool call hoặc hết max_tool_rounds
          3. Dùng toàn bộ message history để extract structured output
        """
        messages = [HumanMessage(content=prompt)]
        self._log_tools(
            f"_run_with_tools start; max_tool_rounds={max_tool_rounds}, prompt_len={len(prompt)}"
        )

        for round_idx in range(max_tool_rounds):
            response: AIMessage = await asyncio.to_thread(
                self._llm_with_tools.invoke, messages
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
        )
        self._log_tools("_run_with_tools completed")
        return result

    # ── Cleanup ────────────────────────────────────────────────────────────────

    @classmethod
    async def cleanup(cls):
        """Đóng browser và playwright. Gọi trong GradingPipeline.run() finally."""
        if cls._shared_browser:
            await cls._shared_browser.close()
        if cls._shared_playwright:
            await cls._shared_playwright.stop()
        cls._shared_tools      = None
        cls._shared_tool_map   = None
        cls._shared_tool_node  = None
        cls._shared_browser    = None
        cls._shared_playwright = None