import re
import asyncio

from functools import update_wrapper
from typing import Callable
from threading import Thread

from mcp.server.fastmcp import FastMCP
from .executor import BlenderExecutor
from ..logger import getLogger

logger = getLogger("BlenderMCPServer")


class MakeTool:
    def __init__(self, func):
        self.executor = BlenderExecutor.get()
        update_wrapper(self, func)
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.executor.send_function_call(self.func, kwargs)


class BlenderMCPServer(FastMCP):
    def __init__(self, *args, **settings):
        super().__init__(*args, **settings)
        self.make_tool = MakeTool

    def add_tool(self, *arg, **kwargs):
        res = super().add_tool(*arg, **kwargs)
        # self.list_tools 是异步方法
        tool = asyncio.run(self.list_tools())[-1]
        try:
            properties = tool.inputSchema["properties"]
            description = tool.description
            for name, info in properties.items():
                # - name: description.....\n
                find_description = re.search(f"- {name}: (.*)\n", description)
                if not find_description:
                    continue
                info["description"] = find_description.group(1)
                logger.debug(f"添加描述 - {name}: {info['description']}")
                # 从description中获取属性描述
        except Exception as e:
            logger.warning(f"Build property description failed: {e}")
        return res


class Server:
    host: str = "localhost"
    port: int = 45677
    server: "BlenderMCPServer" = None
    tools: dict[Callable, None] = {}
    make_tool = MakeTool
    tool_wraper: None

    @classmethod
    def init(cls):
        cls.server = BlenderMCPServer(name="BlenderMCPServer", host=cls.host, port=cls.port)
        cls.tool_wraper = cls.server.tool()

    @classmethod
    def register_tool(cls, tool: Callable) -> None:
        if tool in cls.tools:
            return
        t = cls.make_tool(tool)
        cls.tools[tool] = t
        cls.tool_wraper(t)

    @classmethod
    def register_tools(cls, tools: list[Callable]) -> None:
        for tool in tools:
            cls.register_tool(tool)

    @classmethod
    def unregister_tool(cls, tool: Callable) -> None:
        if tool not in cls.tools:
            return
        try:
            t = cls.tools.pop(tool, None)
            cls.server._tool_manager._tools.pop(t.__name__)
        except Exception as e:
            logger.warning(f"Unregister tool failed: {e}")

    @classmethod
    def unregister_tools(cls, tools: list[Callable]) -> None:
        for tool in tools:
            cls.unregister_tool(tool)

    @classmethod
    def main(cls):
        if not cls.server:
            cls.init()
        logger.info("创世核心正在运转...")
        cls.server.run(transport="sse")

    @classmethod
    def run(cls):
        """Run the MCP server"""
        job = Thread(target=cls.main, daemon=True)
        job.start()


def register():
    Server.init()
    Server.run()


def unregister():
    pass
