"""Shared tool registry and DB helpers for agent modules."""

from __future__ import annotations

import asyncio
from typing import Type

from dotenv import load_dotenv
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_experimental.tools import PythonREPLTool
from langgraph.prebuilt import ToolNode
from playwright.async_api import async_playwright
from pydantic import BaseModel

from master.common.tools import MongoDBTools

from .agent_logging import log_agent_event
from .langsmith import build_langsmith_invoke_config

load_dotenv(override=True)

__all__ = ["MongoDBTools", "ToolsRegistry"]


class ToolsRegistry(MongoDBTools):
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
    def _log_tools(self, message: str) -> None:
        """Log tool-related lifecycle events through the agent logger when available."""

        role = getattr(self, "_role", type(self).__name__.lower())
        log_agent_event("tools", message, extra={"owner": role}, mode="tools_node")

    def _on_mongo_event(self, message: str) -> None:
        """Bridge shared MongoDB helpers into the agent logging layer."""

        self._log_tools(message)

    async def setup_tools(self, llm):
        if ToolsRegistry._tools is None:
            self._log_tools("setup_tools:init_shared_toolkit")
            await self._init_tools()
        else:
            self._log_tools("setup_tools:reuse_shared_toolkit")

        self._tools          = ToolsRegistry._tools
        self._tool_node      = ToolsRegistry._tool_node
        self.browser         = ToolsRegistry._browser
        self.playwright      = ToolsRegistry._playwright
        self._llm            = llm
        self._llm_with_tools = llm.bind_tools(self._tools)
        self._log_tools(f"setup_tools:done total_tools={len(self._tools)}")

    async def _init_tools(self):
        self._log_tools("init_tools:start")
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
        self._log_tools(
            f"init_tools:done browser_tools={len(browser_tools)} file_tools={len(file_tools)} total_tools={len(all_tools)}"
        )

    def get_tool_node(self) -> ToolNode:
        return self._tool_node


    @classmethod
    async def cleanup(cls):
        """Đóng browser và playwright. Gọi trong GradingPipeline.run() finally."""
        log_agent_event(
            "tools",
            "cleanup:start",
            extra={
                "has_browser": cls._browser is not None,
                "has_playwright": cls._playwright is not None,
            },
            mode="tools_node",
        )
        if cls._browser:
            await cls._browser.close()
        if cls._playwright:
            await cls._playwright.stop()
        cls._tools      = None
        cls._tool_node  = None
        cls._browser    = None
        cls._playwright = None
        log_agent_event("tools", "cleanup:done", mode="completed")
