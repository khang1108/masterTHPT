# master/agents/common/tools_registry.py

from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_experimental.tools import PythonREPLTool
from langchain_core.tools import BaseTool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from playwright.async_api import async_playwright
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import json
import uuid
import os

load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI")


class CounterEvidenceDecision(BaseModel):
    found_counter_evidence: bool = Field(default=False, description="True only if there is concrete math-based counter-evidence already found without tools.")
    counter_evidence: str = Field(default="", description="Concrete counter-evidence. Prefer one line per question_id.")

class ToolsRegistry:
    # ── Class-level cache (dùng chung toàn bộ agent instances) ────────────────
    _tools: list[BaseTool] | None = None
    _browser = None
    _playwright = None
    _mongo_client = AsyncIOMotorClient(MONGO_URI)

    # ── Setup ──────────────────────────────────────────────────────────────────

    async def setup_tools(self, llm):
        if ToolsRegistry._tools is None:
            await self._init_tools()

        self._tools          = ToolsRegistry._tools
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

        ToolsRegistry._tools      = all_tools
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

    def _stringify_message_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("text"):
                        parts.append(str(item["text"]))
                    else:
                        parts.append(json.dumps(item, ensure_ascii=False, default=str))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part).strip()

        if content is None:
            return ""

        try:
            return json.dumps(content, ensure_ascii=False, default=str)
        except TypeError:
            return str(content)


    def _strip_code_fence(self, text: str) -> str:
        normalized = str(text or "").strip()
        if normalized.startswith("```"):
            normalized = normalized.split("\n", 1)[-1]
        if normalized.endswith("```"):
            normalized = normalized.rsplit("```", 1)[0]
        return normalized.strip()

    async def _execute_tool_calls(
        self,
        tool_calls: list[dict],
        messages_key: str,
    ) -> list[ToolMessage]:
        if not tool_calls:
            return []

        tool_map = {
            getattr(tool, "name", type(tool).__name__): tool
            for tool in (self._tools or [])
        }
        tool_names = [tc.get("name", "unknown_tool") for tc in tool_calls]
        self.logger.tools_node(f"{messages_key} start: {len(tool_calls)} tool call(s) {tool_names}")

        tool_messages: list[ToolMessage] = []
        for tool_call in tool_calls:
            name = tool_call.get("name", "unknown_tool")
            call_id = tool_call.get("id", f"{messages_key}_{uuid.uuid4().hex[:8]}")
            args = tool_call.get("args", {})
            tool = tool_map.get(name)

            if tool is None:
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool `{name}` not found.",
                        name=name,
                        tool_call_id=call_id,
                        status="error",
                    )
                )
                continue

            try:
                result = await tool.ainvoke(args)
                tool_messages.append(
                    ToolMessage(
                        content=self._stringify_message_content(result),
                        name=name,
                        tool_call_id=call_id,
                        status="success",
                    )
                )
            except Exception as error:
                tool_messages.append(
                    ToolMessage(
                        content=f"Tool `{name}` failed: {error}",
                        name=name,
                        tool_call_id=call_id,
                        status="error",
                    )
                )

        completed_names = [tm.name for tm in tool_messages]
        self.logger.tools_node(f"{messages_key} completed: {len(tool_messages)} tool message(s) {completed_names}")
        return tool_messages

    async def _run_python_research_fallback(self, prompt: str, messages_key: str) -> tuple[str, bool]:
        code_prompt = (
            "Hãy viết MỘT đoạn Python ngắn để kiểm tra hoặc tính thử cho yêu cầu research dưới đây. "
            "Ưu tiên dùng sympy nếu phù hợp. Chỉ trả về code Python hợp lệ, không markdown, không giải thích.\n\n"
            f"RESEARCH_REQUEST:\n{prompt}"
        )
        code_response = await self._llm.ainvoke(self.build_messages(code_prompt))
        python_code = self._strip_code_fence(
            self._stringify_message_content(getattr(code_response, "content", code_response))
        )
        if not python_code:
            python_code = "print('No automatic python check generated.')"

        tool_messages = await self._execute_tool_calls(
            [
                {
                    "name": "Python_REPL",
                    "args": {"query": python_code},
                    "id": f"{messages_key}_python_{uuid.uuid4().hex[:8]}",
                }
            ],
            messages_key=messages_key,
        )

        summary_messages: list[BaseMessage] = list(self.build_messages(prompt))
        summary_messages.append(AIMessage(content="Tôi đã dùng Python_REPL để kiểm tra thêm."))
        summary_messages.extend(tool_messages)
        summary_messages.append(
            HumanMessage(
                content=(
                    "Tóm tắt ngắn gọn các bằng chứng vừa kiểm tra được. "
                    "Mỗi dòng theo dạng `question_id=... | tool=Python_REPL | evidence=...`. "
                    "Nếu code lỗi thì nêu rõ lỗi đó."
                )
            )
        )
        summary_response = await self._llm.ainvoke(summary_messages)
        summary_content = self._stringify_message_content(
            getattr(summary_response, "content", summary_response)
        )
        return summary_content, True

    async def run_tool_research(self, prompt: str, messages_key: str, require_tool: bool = False, max_steps: int = 4) -> tuple[str, bool]:
        if not getattr(self, "_llm_with_tools", None):
            raise RuntimeError("LLM with tools has not been initialized. Call setup_tools() first.")

        messages: list[BaseMessage] = list(self.build_messages(prompt))
        used_tools = False

        for _ in range(max_steps):
            response = await self._llm_with_tools.ainvoke(messages)
            messages.append(response)

            tool_calls = getattr(response, "tool_calls", None) or []
            if tool_calls:
                used_tools = True
                tool_messages = await self._execute_tool_calls(tool_calls, messages_key)
                messages.extend(tool_messages)
                continue

            content = self._stringify_message_content(getattr(response, "content", response))
            if require_tool and not used_tools:
                return await self._run_python_research_fallback(prompt, messages_key)

            return content, used_tools

        final_response = await self._llm.ainvoke(messages)
        final_content = self._stringify_message_content(
            getattr(final_response, "content", final_response)
        )
        if require_tool and not used_tools:
            self.logger.warning(f"{messages_key} research finished without any tool call after {max_steps} step(s)")
        return final_content, used_tools

    async def run_counter_evidence_then_tool(self, counter_prompt: str, tool_prompt: str, messages_key: str, max_steps: int = 4) -> tuple[str, bool, str]:
        if not getattr(self, "_llm", None):
            raise RuntimeError("LLM has not been initialized. Call setup_tools() first.")

        try:
            research_llm = self._llm.with_structured_output(CounterEvidenceDecision)
            decision: CounterEvidenceDecision = await research_llm.ainvoke(self.build_messages(counter_prompt))
            counter_evidence = (decision.counter_evidence or "").strip()
            if decision.found_counter_evidence and counter_evidence:
                self.logger.agent_node(f"{messages_key} research: found counter evidence without tools")
                return counter_evidence, False, "counter evidence"

            self.logger.agent_node(f"{messages_key} research: no counter evidence found, fallback to tools")
        except Exception as error:
            self.logger.warning(f"{messages_key} counter evidence step failed, fallback to tools: {error}")
    
        tool_evidence, used_tools = await self.run_tool_research(tool_prompt, messages_key=messages_key, require_tool=True, max_steps=max_steps)
        return tool_evidence, used_tools, "tool"


    # ── Cleanup ────────────────────────────────────────────────────────────────

    @classmethod
    async def cleanup(cls):
        """Đóng browser và playwright. Gọi trong GradingPipeline.run() finally."""
        browser = cls._browser
        playwright = cls._playwright

        cls._tools = None
        cls._browser = None
        cls._playwright = None

        if browser:
            try:
                await browser.close()
            except Exception:
                pass

        if playwright:
            try:
                await playwright.stop()
            except Exception:
                pass
