import requests
from .base import logger
from .openai import MCPClientOpenAI


class MCPClientDeepSeek(MCPClientOpenAI):
    @classmethod
    def info(cls):
        return {
            "name": "DeepSeek",
            "description": "A client that uses DeepSeek for the rendering.",
            "version": "0.0.1",
        }

    @classmethod
    def default_config(cls):
        return {
            "base_url": "https://api.deepseek.com",
            "api_key": "",
            "model": "deepseek-chat",
        }

    def __init__(self, base_url="https://api.deepseek.com", api_key="", model="", stream=True):
        super().__init__(base_url, api_key, model, stream)
