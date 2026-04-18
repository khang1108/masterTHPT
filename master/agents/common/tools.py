"""Shared tool registry and DB helpers for agent modules."""

from __future__ import annotations

import asyncio
import re
import unicodedata
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
from master.agents.adaptive.graph import AdaptiveGraph

from .agent_logging import log_agent_event
from .langsmith import build_langsmith_invoke_config

load_dotenv(override=True)

__all__ = ["MongoDBTools", "ToolsRegistry"]


def _normalize_topic_text(value: str | None) -> str:
    """Chuẩn hóa text để so khớp bảo thủ với nhãn trong knowledge graph."""

    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    uppercase = without_accents.upper()
    return re.sub(r"[^A-Z0-9]+", " ", uppercase).strip()


class TraceKnowledgeGraphTopicsInput(BaseModel):
    """Input schema cho tool truy vết KG để gắn nhãn câu hỏi."""

    question_text: str
    options: list[str] = []
    candidate_topics: list[str] = []
    limit: int = 5


class KnowledgeGraphTopicResolver:
    """Bộ truy vết KG dùng chung cho Teacher/Verifier khi gắn nhãn câu hỏi.

    Cách làm được giữ theo hướng bảo thủ:
    - ưu tiên canonicalize các topic mà model đã đoán ra
    - sau đó mới dò lexical match từ nội dung câu hỏi và đáp án
    - chỉ trả về một số lượng nhỏ topic_tags để tránh gắn nhãn quá rộng
    """

    def __init__(self) -> None:
        self.graph = AdaptiveGraph()

    def trace(
        self,
        *,
        question_text: str,
        options: list[str] | None = None,
        candidate_topics: list[str] | None = None,
        limit: int = 5,
    ) -> list[str]:
        options = options or []
        candidate_topics = candidate_topics or []
        limit = max(1, limit)

        ranked: dict[str, int] = {}

        # Ưu tiên các topic do model đề xuất, nhưng luôn canonicalize về KG id.
        for topic in candidate_topics:
            resolved = self.graph.resolve_topic(topic)
            if resolved:
                ranked[resolved] = ranked.get(resolved, 0) + 10

        haystack = _normalize_topic_text(
            " \n ".join(
                [
                    question_text or "",
                    *options,
                ]
            )
        )
        haystack_tokens = set(haystack.split())

        for node_id, node in self.graph.knowledge_graph.kc_metadata.items():
            label_tokens = set(_normalize_topic_text(node.label).split())
            if not label_tokens:
                continue

            overlap = len(haystack_tokens & label_tokens)
            if overlap == 0:
                continue

            score = overlap
            label_normalized = _normalize_topic_text(node.label)
            if label_normalized and label_normalized in haystack:
                score += 5

            if node.grade is not None:
                score += 1

            ranked[node_id] = ranked.get(node_id, 0) + score

        return [
            topic_id
            for topic_id, _ in sorted(
                ranked.items(),
                key=lambda item: (-item[1], item[0]),
            )[:limit]
        ]


_shared_kg_topic_resolver: KnowledgeGraphTopicResolver | None = None


def _get_shared_kg_topic_resolver() -> KnowledgeGraphTopicResolver:
    """Khởi tạo lười bộ resolver để toàn bộ agent dùng chung một KG instance."""

    global _shared_kg_topic_resolver
    if _shared_kg_topic_resolver is None:
        _shared_kg_topic_resolver = KnowledgeGraphTopicResolver()
    return _shared_kg_topic_resolver


class KnowledgeGraphTraceTool(BaseTool):
    """Tool cho phép agent truy vết KG và canonicalize topic_tags."""

    name: str = "trace_knowledge_graph_topics"
    description: str = (
        "Dùng để dò knowledge graph, canonicalize và gợi ý topic_tags cho câu hỏi "
        "dựa trên nội dung câu hỏi, đáp án, và các topic ứng viên."
    )
    args_schema: type[BaseModel] = TraceKnowledgeGraphTopicsInput

    def _run(
        self,
        question_text: str,
        options: list[str] | None = None,
        candidate_topics: list[str] | None = None,
        limit: int = 5,
    ) -> list[str]:
        resolver = _get_shared_kg_topic_resolver()
        return resolver.trace(
            question_text=question_text,
            options=options,
            candidate_topics=candidate_topics,
            limit=limit,
        )


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
        kg_trace_tool = KnowledgeGraphTraceTool()
        all_tools     = browser_tools + file_tools + [repl_tool, kg_trace_tool]

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

    def trace_question_topics(
        self,
        *,
        question_text: str,
        options: list[str] | None = None,
        candidate_topics: list[str] | None = None,
        limit: int = 5,
    ) -> list[str]:
        """API dùng trực tiếp trong code cho Teacher/Verifier khi preprocess lần đầu.

        Dù tool đã được bind cho LLM, bước gắn nhãn câu hỏi lần đầu vẫn nên có một
        lối gọi trực tiếp để bảo đảm dữ liệu topic_tags luôn được canonicalize và
        lưu vào DB ngay cả khi model không chủ động gọi tool.
        """

        resolver = _get_shared_kg_topic_resolver()
        return resolver.trace(
            question_text=question_text,
            options=options,
            candidate_topics=candidate_topics,
            limit=limit,
        )


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
