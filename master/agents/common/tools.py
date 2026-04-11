from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_experimental.tools import PythonREPLTool

class ToolRegistry:
    def __init__(self):
        pass
    async def playwright_tools():
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
        return toolkit.get_tools(), browser, playwright

    async def get_file_tools():
        toolkit = FileManagementToolkit()
        return toolkit.get_tools()

    async def get_python_repl_tool():
        return PythonREPLTool()

    async def get_all_tools():
        browser_tools, browser, playwright = await playwright_tools()
        file_tools = await get_file_tools()
        python_repl_tool = await get_python_repl_tool()
        all_tools = browser_tools + file_tools + [python_repl_tool]
        
        return all_tools, browser, playwright
