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
    _tools: list[BaseTool] | None = None
    _tool_node: ToolNode | None = None
    _browser = None
    _playwright = None
    _mongo_client = AsyncIOMotorClient(MONGO_URI)

    # ── Setup ──────────────────────────────────────────────────────────────────

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

        # Trích xuất và lưu riêng data questions ra file JSON để debug
        if collection_name == "questions":
            import json
            import os
            debug_file = "preprocess_output.json"
            
            existing_docs = []
            if os.path.exists(debug_file):
                try:
                    with open(debug_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            existing_docs = json.loads(content)
                except Exception:
                    pass
                    
            for doc in documents:
                # Loại bỏ objectid do mongo tự sinh
                doc_copy = {k: v for k, v in doc.items() if k != "_id"}
                existing_docs.append(doc_copy)
                
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(existing_docs, f, ensure_ascii=False, indent=2)


    def get_tool_node(self) -> ToolNode:
        return self._tool_node


    # ── Cleanup ────────────────────────────────────────────────────────────────

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