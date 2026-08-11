from .openai import MCPClientOpenAI


class MCPClientOpenRouter(MCPClientOpenAI):
    @classmethod
    def info(cls):
        return {
            "name": "OpenRouter",
            "description": "OpenRouter API",
            "version": "0.0.1",
        }

    @classmethod
    def default_config(cls):
        return {
            "base_url": "https://openrouter.ai/api",
            "api_key": "",
            "model": "anthropic/claude-3.5-haiku",
        }

    def __init__(self, base_url="https://openrouter.ai/api", api_key="", model="", stream=True):
        super().__init__(base_url, api_key, model, stream)
