import bpy
import requests
import json
from copy import deepcopy
from .openai import MCPClientOpenAI, logger


class MCPClientLocalOllama(MCPClientOpenAI):
    @classmethod
    def info(cls):
        return {
            "name": "LocalOllama",
            "description": "Local Ollama client",
            "version": "1.0.0",
        }

    @classmethod
    def default_config(cls):
        return {
            "base_url": "http://localhost:11434",
            "api_key": "",
            "model": "llama3.2:3b",
        }

    def __init__(self, base_url="http://localhost:11434", api_key="ollama", model="", stream=True):
        super().__init__(base_url, api_key=api_key, model=model, stream=stream)

    def response_raise_status(self, response: requests.Response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                json_data = response.json()
                error = json_data.get("error", "")
                if message := error.get("message", ""):
                    if "does not support tools" in message:
                        logger.error("当前模型不支持工具调用, 请更换模型")
                    raise Exception(message)
                print(json_data)
            except json.JSONDecodeError:
                raise
