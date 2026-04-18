"""Shared tool registry and DB helpers for agent modules.

The registry now supports role-scoped tool bundles so the manager/planner can
inject a narrower capability surface into each specialist agent.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from dotenv import load_dotenv
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_core.tools import BaseTool
from langchain_experimental.tools import PythonREPLTool
from langgraph.prebuilt import ToolNode
from playwright.async_api import async_playwright
from pydantic import BaseModel

from master.common.tools import MongoDBTools
from master.agents.adaptive.graph import AdaptiveGraph

from .agent_logging import log_agent_event
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

    # Class-level caches are shared across every agent instance so scoped
    # bundles can be reused without repeatedly booting Playwright.
    _tool_bundles: dict[str, list[BaseTool]] | None = None
    _tool_nodes: dict[str, ToolNode | None] | None = None
    _tool_name_bundles: dict[str, list[str]] | None = None
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

    @classmethod
    def tool_bundle_names(cls) -> list[str]:
        """Return the known tool-bundle names used for capability scoping."""

        return ["default", "teacher", "verifier", "parser", "adaptive"]

    @classmethod
    def get_tool_names_for_role(cls, role: str) -> list[str]:
        """Expose normalized tool names for planner/debug/test use.

        The method works even before any agent instance has called
        ``setup_tools(...)`` so unit tests can assert scoping policy without
        paying Playwright startup cost.
        """

        canonical_role = (role or "default").strip().lower()
        if canonical_role == "adaptive":
            return []
        if canonical_role == "parser":
            return [
                "copy_file",
                "file_delete",
                "file_search",
                "list_directory",
                "move_file",
                "read_file",
                "write_file",
            ]
        if canonical_role in {"teacher", "verifier"}:
            return [
                "python_repl",
                "trace_knowledge_graph_topics",
            ]
        return [
            "click_element",
            "copy_file",
            "current_webpage",
            "extract_hyperlinks",
            "extract_text",
            "file_delete",
            "file_search",
            "get_elements",
            "list_directory",
            "move_file",
            "navigate_back",
            "navigate_browser",
            "previous_webpage",
            "python_repl",
            "read_file",
            "trace_knowledge_graph_topics",
            "write_file",
        ]

    async def setup_tools(self, llm, *, bundle: str = "default"):
        selected_bundle = (bundle or "default").strip().lower()
        if ToolsRegistry._tool_bundles is None:
            self._log_tools("setup_tools:init_scoped_toolkit")
            await self._init_tools()
        else:
            self._log_tools("setup_tools:reuse_scoped_toolkit")

        available_bundles = ToolsRegistry._tool_bundles or {}
        available_nodes = ToolsRegistry._tool_nodes or {}
        tool_names = ToolsRegistry._tool_name_bundles or {}

        if selected_bundle not in available_bundles:
            selected_bundle = "default"

        self._tool_bundle = selected_bundle
        self._tools = list(available_bundles.get(selected_bundle, []))
        self._tool_node = available_nodes.get(selected_bundle)
        self._tool_names = list(tool_names.get(selected_bundle, []))
        self.browser = ToolsRegistry._browser
        self.playwright = ToolsRegistry._playwright
        self._llm = llm
        self._llm_with_tools = llm.bind_tools(self._tools) if self._tools else llm
        self._log_tools(
            f"setup_tools:done bundle={selected_bundle} total_tools={len(self._tools)}"
        )

    async def _init_tools(self):
        self._log_tools("init_tools:start")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        browser_tools = PlayWrightBrowserToolkit.from_browser(async_browser=browser).get_tools()
        file_tools = FileManagementToolkit().get_tools()
        repl_tool = PythonREPLTool()
        kg_trace_tool = KnowledgeGraphTraceTool()
        all_tools = browser_tools + file_tools + [repl_tool, kg_trace_tool]

        bundle_map: dict[str, list[BaseTool]] = {
            "default": all_tools,
            "teacher": [repl_tool, kg_trace_tool],
            "verifier": [repl_tool, kg_trace_tool],
            "parser": file_tools,
            # Adaptive currently uses repository methods directly rather than
            # LangChain tools, so the scoped bundle intentionally stays empty.
            "adaptive": [],
        }
        node_map: dict[str, ToolNode | None] = {
            name: (ToolNode(tools) if tools else None)
            for name, tools in bundle_map.items()
        }
        tool_name_map = {
            name: [tool.name for tool in tools]
            for name, tools in bundle_map.items()
        }

        ToolsRegistry._tool_bundles = bundle_map
        ToolsRegistry._tool_nodes = node_map
        ToolsRegistry._tool_name_bundles = tool_name_map
        ToolsRegistry._tools = bundle_map["default"]
        ToolsRegistry._tool_node = node_map["default"]
        ToolsRegistry._browser = browser
        ToolsRegistry._playwright = playwright
        self._log_tools(
            "init_tools:done "
            f"browser_tools={len(browser_tools)} file_tools={len(file_tools)} "
            f"default_tools={len(all_tools)} teacher_tools={len(bundle_map['teacher'])} "
            f"verifier_tools={len(bundle_map['verifier'])} parser_tools={len(bundle_map['parser'])}"
        )

    def get_tool_node(self, bundle: str | None = None) -> ToolNode | None:
        """Return the current bundle tool node or another scoped bundle node."""

        selected_bundle = (
            (bundle or getattr(self, "_tool_bundle", "default")).strip().lower()
        )
        if ToolsRegistry._tool_nodes and selected_bundle in ToolsRegistry._tool_nodes:
            return ToolsRegistry._tool_nodes[selected_bundle]
        return self._tool_node

    def get_tools_for_role(self, role: str | None = None) -> list[BaseTool]:
        """Return actual tool instances for a given scoped role."""

        if not ToolsRegistry._tool_bundles:
            return list(self._tools or [])
        selected_role = (role or getattr(self, "_tool_bundle", "default")).strip().lower()
        return list(ToolsRegistry._tool_bundles.get(selected_role, []))

    def get_tool_names(self, role: str | None = None) -> list[str]:
        """Return scoped tool names for planner/debug code paths."""

        if ToolsRegistry._tool_name_bundles:
            selected_role = (role or getattr(self, "_tool_bundle", "default")).strip().lower()
            return list(ToolsRegistry._tool_name_bundles.get(selected_role, []))
        return self.get_tool_names_for_role(role or "default")

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
        cls._tool_bundles = None
        cls._tool_nodes = None
        cls._tool_name_bundles = None
        cls._tools      = None
        cls._tool_node  = None
        cls._browser    = None
        cls._playwright = None
        log_agent_event("tools", "cleanup:done", mode="completed")
