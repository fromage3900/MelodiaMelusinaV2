"""
Fallback and type definitions for MCP types.

Allows ue_blueprint_mcp to operate seamlessly whether the official mcp
package is installed or when running in a minimal/embedded Python environment.
"""

from __future__ import annotations

try:
    from mcp.types import Tool, TextContent
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    from dataclasses import dataclass, field
    from typing import Any, Callable, Dict, List, Optional

    @dataclass
    class Tool:
        name: str
        description: str
        inputSchema: Dict[str, Any] = field(default_factory=dict)


    @dataclass
    class TextContent:
        type: str = "text"
        text: str = ""


    class Server:
        def __init__(self, name: str):
            self.name = name
            self._list_tools_handler: Optional[Callable] = None
            self._call_tool_handler: Optional[Callable] = None

        def list_tools(self):
            def decorator(func: Callable):
                self._list_tools_handler = func
                return func
            return decorator


        def call_tool(self):
            def decorator(func: Callable):
                self._call_tool_handler = func
                return func
            return decorator

        async def list_tools_impl(self) -> List[Tool]:
            if self._list_tools_handler:
                return await self._list_tools_handler()
            return []


        async def call_tool_impl(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if self._call_tool_handler:
                return await self._call_tool_handler(name, arguments)
            return [TextContent(type="text", text='{"success": false, "error": "No handler registered"}')]


        def create_initialization_options(self) -> Dict[str, Any]:
            return {}


        async def run(self, read_stream: Any, write_stream: Any, initialization_options: Any = None):
            pass


    class _StdioServerContext:
        async def __aenter__(self):
            return (None, None)


        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass


    def stdio_server():
        return _StdioServerContext()

__all__ = ["Tool", "TextContent", "Server", "stdio_server"]
