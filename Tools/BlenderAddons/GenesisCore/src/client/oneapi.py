import json
import requests
from .openai import MCPClientOpenAI, logger


class MCPClientOneAPI(MCPClientOpenAI):
    @classmethod
    def info(cls):
        return {
            "name": "OneAPI",
            "description": "OneAPI",
            "version": "0.0.1",
        }

    @classmethod
    def default_config(cls):
        return {
            "base_url": "https://openai.justsong.cn",
            "api_key": "",
            "model": "Qwen/Qwen2.5-7B-Instruct",
        }

    def __init__(self, base_url="https://openai.justsong.cn", api_key="", model="", stream=True):
        super().__init__(base_url, api_key, model, stream)

    def response_raise_status(self, response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                json_data = response.json()
                if message := json_data.get("message"):
                    if message == "Function call is not supported for this model":
                        logger.error("此模型不支持工具调用")
                    raise Exception(message)
            except json.JSONDecodeError:
                ...
