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
    # ── Class-level cache (dùng chung toàn bộ agent instances) ────────────────
    _tools: list[BaseTool] | None = None
    _tool_node: ToolNode | None = None
    _browser = None
    _playwright = None
    _mongo_client = AsyncIOMotorClient(MONGO_URI)

    def _log_tools(self, message: str) -> None:
        """Log tool-related lifecycle events through the agent logger when available."""

    async def setup_tools(self, llm):
        if ToolsRegistry._tools is None:
            await self._init_tools()

        self._tools          = ToolsRegistry._tools
        self._tool_node      = ToolsRegistry._tool_node
        self.browser         = ToolsRegistry._browser
        self.playwright      = ToolsRegistry._playwright
        self._llm            = llm
        self._llm_with_tools = llm.bind_tools(self._tools)
        self.logger.info(f"setup_tools completed; total tools={len(self._tools)}")

    async def _init_tools(self):
        self.logger.info("initializing Playwright browser and toolkits")
        playwright    = await async_playwright().start()
        browser       = await playwright.chromium.launch(headless=True)
        browser_tools = PlayWrightBrowserToolkit.from_browser(async_browser=browser).get_tools()
        file_tools    = FileManagementToolkit().get_tools()
        repl_tool     = PythonREPLTool()
        all_tools     = browser_tools + file_tools + [repl_tool]

        tool_node = ToolNode(all_tools)

        ToolsRegistry._tools      = all_tools
        ToolsRegistry._tool_node  = tool_node
        ToolsRegistry._browser    = browser
        ToolsRegistry._playwright = playwright

    # ── MongoDB ────────────────────────────────────────────────────────────────

    async def get_data(self, database_name: str, collection_name: str, query: dict, limit: int = 10) -> list:
        collection = ToolsRegistry._mongo_client[database_name][collection_name]
        return await collection.find(query).to_list(length=limit)

    async def insert_data(self, database_name: str, collection_name: str, documents: list[dict]):
        if not documents:
            return
        collection = ToolsRegistry._mongo_client[database_name][collection_name]
        await collection.insert_many(documents)


    def get_tool_node(self) -> ToolNode:
        return self._tool_node


    @classmethod
    async def cleanup(cls):
        """Đóng browser và playwright. Gọi trong GradingPipeline.run() finally."""
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()
        cls._tools      = None
        cls._tool_node  = None
        cls._browser    = None
        cls._playwright = None
