import json
import bpy
import base64
import requests
import re
from copy import deepcopy
from pathlib import Path

from .base import MCPClientBase, logger


class MCPClientOpenAI(MCPClientBase):
    @classmethod
    def info(cls):
        return {
            "name": "OpenAI Compatible",
            "description": "A client that uses OpenAI for the rendering.",
            "version": "0.0.1",
        }

    @classmethod
    def default_config(cls):
        return {
            "base_url": "https://api.openai.com",
            "api_key": "",
            "model": "gpt-4o-mini",
        }

    def __init__(self, base_url="https://api.openai.com", api_key="", model="", stream=True):
        super().__init__(base_url, api_key, model, stream)

    def get_chat_url(self):
        return f"{self.base_url}/v1/chat/completions"

    def fetch_models_ex(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        model_url = f"{self.base_url}/v1/models"
        try:
            response = requests.get(model_url, headers=headers)
            models = response.json().get("data", [])
            self.models = [model["id"] for model in models]
        except Exception:
            logger.error("获取模型列表失败, 请检查大模型服务商, API密钥及base url是否正确")
        return self.models

    async def prepare_tools(self):
        response = await self.session.list_tools()
        tools = []
        for tool in response.tools:
            tool_info = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    # "parameters": {
                    #     "type": "object",
                    #     "properties": {
                    #         "city": {
                    #             "type": "string",
                    #             "description": "The name of the city",
                    #         },
                    #     },
                    #     "required": ["city"],
                    # },
                },
            }
            parameters = deepcopy(tool.inputSchema)
            tool_info["function"]["parameters"] = parameters
            # region 简化函数描述
            description = tool.description
            description = description.replace("Args:", "")
            for name, info in parameters.get("properties", {}).items():
                find_description = re.search(f"- {name}: (.*)\n", description)
                if not find_description:
                    continue
                description = description.replace(find_description.group(0), "")
            description = description.replace("\n", "").strip()
            while "  " in description:
                description = description.replace("  ", " ")
            # endregion 简化函数描述
            tool_info["function"]["description"] = description
            tools.append(tool_info)
        return tools

    def response_raise_status(self, response: requests.Response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                json_data = response.json()
                error = json_data.get("error", {})
                if message := error.get("message"):
                    if "tools is not supported" in message:
                        logger.error("此模型不支持工具调用")
                    # for deepseek
                    if "does not support Function Calling" in message:
                        logger.error("此模型不支持工具调用")
                    raise Exception(message)
                print(json_data)
            except json.JSONDecodeError:
                ...

    async def process_query(self, query: str) -> list:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "messages": self.messages,
            "tools": None,
            "stream": self.stream,
        }
        if not self.use_history:
            self.clear_messages()
        # messages.append({"role": "system", "content": self.system_prompt()})
        user_content = [{"type": "text", "text": query}]
        while not self.image_queue.empty():
            image_path = Path(self.image_queue.get())
            base64_image = base64.b64encode(image_path.read_bytes()).decode()
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                },
            }
            user_content.append(image_content)

        self.push_message({"role": "user", "content": user_content})
        data["tools"] = await self.prepare_tools()
        with requests.Session() as session:
            session.headers.update(headers)
            session.stream = self.stream
            while not self.should_skip():
                last_call_index = -1
                self.tool_calls.clear()
                response = session.post(self.get_chat_url(), json=data)
                self.response_raise_status(response)
                response.encoding = "utf-8"
                # print("---------------------------------------START---------------------------------------")

                for line in response.iter_lines():
                    if not line:
                        continue
                    if self.should_skip():
                        break
                    # print("原始数据:", line)
                    if not (json_data := self.parse_line(line)):
                        # print("无法解析原始数据:", line)
                        continue
                    choice = json_data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason", "")
                    if finish_reason in {"stop", "tool_calls"}:
                        continue
                    if json_data.get("type", "") == "ping":
                        # for claude openai compatible
                        continue
                    if error := self.parse_error(json_data):
                        logger.error(error)
                        break
                    if not delta:
                        logger.warning(f"delta数据缺失: {line}")
                        continue
                    # print("delta原始数据:", delta)
                    # ---------------------------1.文本输出---------------------------
                    # 原始数据 {"choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}}]}
                    if (content := delta.get("content")) or (content := delta.get("reasoning_content")):
                        self.push_stream_message({"role": "streaming", "content": content})
                        print(content, end="", flush=True)

                    # ---------------------------2.工具调用---------------------------
                    # 原始数据 {"choices": [{"index": 0, "delta": {"role": "assistant", "tool_calls": [{"index": 0, "id": "XXX", "type": "function", "function": {"name": "get_scene_info", "arguments": ""}}]}}]}
                    if not (tool_call := delta.get("tool_calls", [{}])[0]):
                        continue
                    index = tool_call["index"]
                    fn_name = tool_call.get("function", {}).get("name", "")
                    # 工具调用的第一条数据
                    if fn_name and index not in self.tool_calls:
                        last_call_index = index
                        self.tool_calls[index] = tool_call
                        print(f"\n选择工具: {fn_name} 参数: ", end="", flush=True)
                    # 过滤无效的tool_call(小模型生成的多余arguments)
                    if index not in self.tool_calls:
                        continue
                    # 流式输出拼接arguments
                    if arguments := tool_call.get("function", {}).get("arguments", ""):
                        self.tool_calls[index]["function"]["arguments"] += arguments
                        print(arguments, end="", flush=True)
                    # 每轮只允许一个工具调用( 当存在连续调用时, 每当tryjson 成功时就调用)
                    if self.ensure_tool_call(index):
                        await self.call_tool(index)
                # print("----------------------------------------END-----------------------------------------")
                if self.should_skip():
                    break
                if last_call_index == -1:
                    break
                # 保证执行最后一个工具调用
                for index in list(self.tool_calls):
                    # 最后强制调用一次, 如果有报错信息会写入messages
                    await self.call_tool(index)
        return ""
