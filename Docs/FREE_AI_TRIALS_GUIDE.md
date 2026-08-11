# Free AI Trials & Integrations Guide

## 🤖 Available Free AI Platforms

These platforms offer free tiers that integrate well with the Agent Bridge MCP system:

### 1. Ollama (Already Configured)
- **Free**: 100% Local, no subscription required
- **Models**: qwen2.5-coder, deepseek-r1, llama3.1, gemma2, phi3
- **Setup**: Already running on your machine (port 11434)
- **Integration**: Direct HTTP API compatible with agent_bridge_mcp

### 2. Together.ai
- **Free Tier**: $25 credit for new signups
- **Models**: Llama 3.1, Qwen, DeepSeek, Mistral
- **API Endpoint**: `https://api.together.ai/v1/chat/completions`
- **Integration**: Works via OpenRouter or direct API

### 3. Groq
- **Free Tier**: 14,400 requests/day (fast Llama/Qwen models)
- **Models**: Llama 3.1 70B, Qwen 2.5, Mixtral
- **API Endpoint**: `https://api.groq.com/openai/v1/chat/completions`
- **Speed**: Extremely fast (100+ tokens/sec)

### 4. OpenRouter
- **Free Tier**: $10 credit for new users
- **Models**: All major models in one API
- **Setup**: Single API key for all providers
- **Integration**: Universal endpoint for agent_bridge_mcp

### 5. DeepSeek
- **Free Tier**: Free tier available, signup required
- **Models**: DeepSeek Chat, DeepSeek Coder
- **API Endpoint**: `https://api.deepseek.com/v1/chat/completions`
- **Strength**: Excellent reasoning for agent workflows

### 6. Fireworks.ai
- **Free Tier**: $1 credit to start
- **Models**: Llama, Qwen, Gemma, Moondream
- **API Endpoint**: `https://api.fireworks.ai/inference/v1/chat/completions`

### 7. Cohere
- **Free Tier**: 1M tokens free
- **Models**: Command R+, Command Light
- **API Endpoint**: `https://api.cohere.ai/v1/chat`

## 🔧 Integration Setup

### Option A: OpenRouter (Recommended)
Simplest integration - one endpoint for all models:

```json
// Add to your MCP config (e.g., .opencode.json)
{
  "openrouter": {
    "enabled": true,
    "type": "local",
    "command": ["python", "PATH_TO_YOUR_OPENROUTER_MCP_SERVER"]
  }
}
```

Or use the OpenAI-compatible endpoint with curl:
```python
# In agent_bridge_mcp.py - you can add model selection via OpenRouter
# Just set OPENROUTER_API_KEY env var
```

### Option B: Direct Provider
Add each provider's endpoint to `agent_bridge_mcp.py`:

```python
# Example: Add to PROBABLE_AI_ENDPOINTS in agent_bridge_mcp.py
PROVIDER_ENDPOINTS = {
    "together": "https://api.together.ai/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
}
```

## 🚀 Quick Start Commands

Once you get an API key, test it with:

```bash
# Test Together.ai
curl -X POST https://api.together.ai/v1/chat/completions \
  -H "Authorization: Bearer $TOGETHER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-coder-32b", "messages": [{"role": "user", "content": "Say hello!"}]}'

# Test Groq
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-70b-versatile", "messages": [{"role": "user", "content": "Say hello!"}]}'

# Test OpenRouter
curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen-2.5-coder-32b", "messages": [{"role": "user", "content": "Say hello!"}]}'
```

## 💡 Model Recommendations

For the Agent Bridge system, these models work well:

| Model | Best For | Notes |
|-------|----------|-------|
| qwen2.5-coder-14b/32b | Code generation, blessings | Already configured |
| deepseek-coder | Reasoning, architecture | Great for complex prompt parsing |
| llama-3.1-70b | General purpose, creative | High quality outputs |
| gemma-2-9b | Fast responses | Good for status checks |

## 🛠️ Agent Bridge Model Selection

You can override models when calling the bridge:

```python
# In your MCP client, add model parameter:
delegate_to_agent(
    intent="blessing", 
    action="evolve", 
    payload={"target_count": 5},
    model="deepseek/deepseek-coder"  # Override default
)
```

## 🔗 Adding New Providers

To integrate a new AI provider into the bridge:

1. Sign up at the provider's website
2. Get your API key
3. Add endpoint to `agent_bridge_mcp.py`
4. Test with `echo {"id":1,"method":"tools/call","params":{"name":"get_agent_status"}} | python deploy/agent_bridge_mcp.py`
5. Done! All MCP clients now have access

## 📱 MCP-Ready Providers

| Provider | MCP Server Available | Notes |
|----------|---------------------|-------|
| Ollama | ✅ Built-in | Local only |
| OpenRouter | ✅ openrouter-mcp | Universal API |
| Groq | ✅ groq-mcp | Fast inference |
| Together | ✅ together-mcp | Multiple models |
| Anthropic | ✅ claude-mcp | If you have credits |
| OpenAI | ✅ openai-mcp | If you have credits |

---

*Use this guide to expand your agent ecosystem!*