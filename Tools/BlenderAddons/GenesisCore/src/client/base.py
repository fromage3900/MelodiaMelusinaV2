import json
import bpy
import math
import random
import queue
import asyncio
import requests
from threading import Thread
from copy import deepcopy
from dataclasses import dataclass
from typing import Union, Literal
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from ..timer import Timer
from ..logger import getLogger
from ..utils import BTextWriter

logger = getLogger("  BlenderClient")


@dataclass
class ContentEmpty:
    rtype: Literal["empty"]
    text: str
    tool_calls: list
    error: str


@dataclass
class ContentText:
    rtype: Literal["text"]
    text: str


@dataclass
class ContentTool:
    rtype: Literal["tool"]
    tool_calls: list
    arguments: str


ContentType = Union[ContentEmpty, ContentText, ContentTool]


class ResponseParser:
    @staticmethod
    def parse_response(response: str) -> ContentType:
        try:
            data = json.loads(response)
            return data
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None


class MCPClientBase:
    client_pools: dict[object, "MCPClientBase"] = {}
    __clients__: dict[str, "MCPClientBase"] = {}

    def __init__(self, base_url="https://api.deepseek.com", api_key="", model="", stream=True):
        self._base_url = ""
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.stream = stream
        self.session: ClientSession = None
        self.messages = []
        self.tool_calls: dict[str, dict] = {}
        self.should_clear_messages = False
        self.command_processing = False
        self.use_history = False
        self.models = []
        self.exit_stack = AsyncExitStack()
        self.should_stop = False
        self.skip_current_command = False
        self.command_queue = queue.Queue()
        self.image_queue = queue.Queue()
        self.is_running = False
        self.push_instance(self)
        # self.response_parser = ResponseParser()
        # s = self.response_parser.parse_response("S")
        self.reset_config()
        self.clear_messages()

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, value):
        self._base_url = value[:-1] if value.endswith("/") else value

    def push_stream_message(self, message):
        BTextWriter.get().push(deepcopy(message))

    def push_message(self, message):
        BTextWriter.get().push(deepcopy(message))
        self.messages.append(message)

    def clear_messages(self):
        self.messages.clear()
        BTextWriter.get().clear()

    def update(self):
        if self.should_clear_messages:
            self.clear_messages()
            self.should_clear_messages = False
        Timer.put(self.reset_config)

    def reset_config(self):
        from ..preference import get_pref

        pref = get_pref()
        self.base_url = pref.base_url
        self.api_key = pref.api_key
        self.model = pref.model
        self.use_history = pref.use_history_message

    def get_chat_url(self):
        return ""

    def fetch_models(self, force=False) -> list:
        if self.models and not force:
            return self.models
        logger.info("正在获取模型列表...")
        self.models = sorted(self.fetch_models_ex())
        return self.models

    def fetch_models_ex(self):
        return []

    @classmethod
    def info(cls):
        return {
            "name": "MCPClientBase",
            "description": "A base class for MCP clients",
            "version": "0.1.0",
        }

    @classmethod
    def get(cls):
        return cls.client_pools.get(cls, None)

    @classmethod
    def push_instance(cls, self):
        cls.client_pools[cls] = self

    @classmethod
    def pop_instance(cls):
        return cls.client_pools.pop(cls, None)

    @classmethod
    def get_all_clients(cls):
        clients = []
        for c in cls.__subclasses__():
            clients.append(c)
            clients += c.get_all_clients()
        return clients

    @classmethod
    def get_enum_items(cls):
        return [(c.__name__, c.info()["name"], c.info()["description"]) for c in cls.get_all_clients()]

    @classmethod
    def default_config(cls):
        return {}

    @classmethod
    def get_client_by_name(cls, name: str) -> "MCPClientBase":
        if name not in cls.__clients__:
            for c in cls.get_all_clients():
                cls.__clients__[c.__name__] = c
        return cls.__clients__[name]

    @classmethod
    def stop_client(cls):
        if not (instance := cls.pop_instance()):
            return
        instance.should_stop = True

    @classmethod
    def try_start_client(cls):
        instance = cls.get()
        if not instance or instance.should_stop:
            cls.push_instance(cls())
        instance = cls.get()
        if instance.is_running:
            instance.reset_config()
            return
        instance.is_running = True

        def run_client():
            asyncio.run(instance.main())
            logger.info(f"客户端 {cls.__name__} 结束运行!")

        job = Thread(target=run_client, daemon=True)
        job.start()

    @classmethod
    def draw(cls, layout: bpy.types.UILayout):
        from ..preference import get_pref

        pref = get_pref()
        layout.prop(pref, "api_key")
        layout.prop(pref, "base_url")
        layout.prop(pref, "model")

    def should_skip(self):
        return self.skip_current_command or self.should_stop

    def system_prompt(self):
        prompt_cn = """
        你擅长对用户的问题进行分析, 并选择合适的工具来解决用户的问题. 
        逐步思考, 每个思考步骤只保留最少的草稿, 最终选择合适的工具来解决问题.
        注意: 仅能选择提供的可用工具
        """
        prompt_en = """
        You are good at analyzing user questions and choosing the appropriate tools to solve user problems.
        Think step by step, but keep only a minimum draft for each thinking step, and finally choose the appropriate tool to solve the problem.
        Note: Only use the tools you have been provided with.
        """
        # prompt_en_path = Path(__file__).parent / "prompt_en.txt"
        # prompt_en = prompt_en_path.read_text(encoding="utf-8")
        return prompt_en.strip()

    async def connect_to_server(self):
        """连接到MCP服务器"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        stdio_transport = await self.exit_stack.enter_async_context(sse_client(url="http://localhost:45677/sse", headers=headers))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

    def parse_line(self, line: str) -> dict:
        if not line:
            return {}
        line = line.decode("utf-8").replace("data:", "").strip()
        # print("收到消息:", line)
        if line.endswith(("[DONE]", "PROCESSING")):
            return {}
        if line.endswith("[ERROR]"):
            print(line)
            return {}
        try:
            return json.loads(line)
        except Exception:
            if "PROCESSING" in line:
                return {}
            print("Json解析错误", line)
        return {}

    def parse_error(self, error: dict):
        return error.get("error", {}).get("message", "")

    def response_raise_status(self, response):
        pass

    def parse_arguments(self, arguments: str):
        arguments = arguments.strip()
        # 基本的json格式校验
        if not arguments.startswith("{") or not arguments.endswith("}"):
            raise json.JSONDecodeError("参数格式错误", arguments, 0)
        try:
            try:
                return eval(arguments, {"math": math, "random": random})
            except Exception:
                pass
            return json.loads(arguments)
        except Exception as e:
            logger.info(f"\n错误参数: {arguments}\n")
            raise e

    def ensure_tool_call(self, index: int):
        tool_call = self.tool_calls[index]
        func = tool_call.get("function", {})
        try:
            arguments = func.get("arguments", "").strip()
            self.parse_arguments(arguments)
        except Exception:
            return False
        return True

    async def call_tool(self, index: int):
        """调用工具"""
        tool_call = self.tool_calls[index]
        func = tool_call.get("function", {})
        fn_name = func.get("name")
        arguments = func.get("arguments", "").strip() or "{}"
        print()  # 每次调用工具时，打印一个空行，方便查看日志
        logger.info(f"尝试工具: {fn_name} 参数: {arguments}")
        results = await self.call_tool_ex(fn_name, arguments)
        self.tool_calls.pop(index)
        self.push_message({"role": "assistant", "content": "", "tool_calls": [tool_call]})
        for rtype, result in results:
            final_result = f"Selected tool: {fn_name}\nResult: {result}"
            tool_call_result = {"role": "tool", "content": final_result, "tool_call_id": tool_call["id"], "name": fn_name}
            self.push_message(tool_call_result)

    async def call_tool_ex(self, fn_name: str, arguments: str | dict) -> tuple[str, str]:
        try:
            arguments = self.parse_arguments(arguments)
        except Exception as e:
            logger.info(f"参数解析错误:\n{arguments}\n{e}")
            return [("error", f"Argument parsing error: {e}")]
        res = await self.session.call_tool(fn_name, arguments)
        results = []
        for res_content in res.content:
            result = ""
            rtype = res_content.type
            if rtype == "text":
                result = res_content.text
            elif rtype == "image":
                result = res_content.data
            elif rtype == "resource":
                result = res_content.resource
            if isinstance(result, str) and result.startswith("Error"):
                rtype = "error"
                logger.error(result)
            results.append((rtype, result))
        return results

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        return ""

    async def main(self):
        try:
            logger.info("尝试连接到创世核心...")
            await self.connect_to_server()
            logger.info("创世核心已连接!")
            while True:
                try:
                    self.command_processing = False
                    self.update()
                    if self.should_stop:
                        break
                    try:
                        query = self.command_queue.get_nowait()
                    except queue.Empty:
                        await asyncio.sleep(0.2)
                        continue
                    logger.info(f"当前命令: {query}")
                    self.skip_current_command = False
                    self.command_processing = True
                    response = await self.process_query(query)
                    print()
                    if self.skip_current_command:
                        logger.info(f"跳过命令: {query}")
                        continue
                    logger.info(f"处理完成: {query}")
                    # client.session.call_tool
                    # print(response)
                except requests.exceptions.HTTPError as e:
                    logger.warning(f"HTTP错误(请检查api_key, 模型使用情况或额度): {e}")
                except Exception:
                    import traceback

                    traceback.print_exc()
        except Exception as e:
            logger.error(f"连接失败: {e}")
            logger.error("请尝试改变网络环境(开关代理等)")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """清理资源"""
        self.command_processing = False
        await self.exit_stack.aclose()
