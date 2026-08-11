import requests

from .openai import MCPClientOpenAI, logger


class MCPClientClaude(MCPClientOpenAI):
    @classmethod
    def info(cls):
        return {
            "name": "Claude",
            "description": "Claude is a powerful language model that can be used to generate text.",
            "version": "0.0.1",
        }

    @classmethod
    def default_config(cls):
        return {
            "base_url": "https://api.anthropic.com",
            "api_key": "",
            "model": "claude-3-5-haiku-20241022",
        }

    def __init__(self, base_url="https://api.anthropic.com", api_key="", model="", stream=True):
        super().__init__(base_url, api_key, model, stream)

    def get_chat_url(self):
        return f"{self.base_url}/v1/chat/completions"

    def fetch_models_ex(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key,
        }

        model_url = f"{self.base_url}/v1/models"
        if not self.api_key:
            logger.error("API密钥不能为空")
            return []
        try:
            response = requests.get(model_url, headers=headers)
            json_data = response.json()
            error = json_data.get("error", {})
            if error:
                raise Exception(error.get("message", "Unknown error"))

            models = response.json().get("data", [])
            self.models = [model["id"] for model in models]
        except Exception as e:
            logger.error(f"获取模型列表失败, 请检查大模型服务商, API密钥及base url是否正确: {e}")
        return self.models
