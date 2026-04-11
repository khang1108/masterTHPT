from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_experimental.tools import PythonREPLTool

class ToolRegistry:
    def __init__(self):
        pass

    async def playwright_tools(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        return toolkit.get_tools(), browser, playwright

    async def get_file_tools(self):
        toolkit = FileManagementToolkit()
        return toolkit.get_tools()

    async def get_python_repl_tool(self):
        return PythonREPLTool()

    async def get_all_tools(self):
        browser_tools, browser, playwright = await self.playwright_tools()
        file_tools = await self.get_file_tools()
        python_repl_tool = await self.get_python_repl_tool()
        all_tools = browser_tools + file_tools + [python_repl_tool]

        return all_tools, browser, playwright


async def get_all_tools():
    """Build the full tool set (used by teacher / verifier when running as a script)."""
    return await ToolRegistry().get_all_tools()
