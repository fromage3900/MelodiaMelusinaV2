# Model Recommendations for Critical Thinking & Coding

## 🚀 Cloud Models — Primary (Best Reasoning, via MCP/API)

Configured in `.mcp.json` (works in **both VS Code and Rider**):

| Model | Provider | Endpoint | Key Env | Best For |
|-------|----------|----------|---------|----------|
| **DeepSeek V4** | OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` | Primary reasoning, planning, architecture. Free tier + cheap paid plan. |
| **Kimi K3** | TokenRouter | `https://tokenrouter.ai/beta/v1` | TokenRouter key | Large-context coding, web dev, document analysis |

**MCP server names (registered in `.mcp.json`):** `deepseek-v4` and `kimi-k3`
- **VS Code (Cline):** auto-picks up `.mcp.json` on session restart.
- **Rider:** Settings → Tools → MCP → Import from `.mcp.json`.

### DeepSeek V4 via OpenRouter (openai-compatible)
```bash
# Test with curl
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek/deepseek-v4","messages":[{"role":"user","content":"Explain UE5 PCG"}]}'
```

### Kimi K3 via TokenRouter (openai-compatible)
```bash
curl https://tokenrouter.ai/beta/v1/chat/completions \
  -H "Authorization: Bearer $TOKENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"moonshotai/kimi-k3","messages":[{"role":"user","content":"Explain UE5 PCG"}]}'
```

### DeepSeek V4 via Official API (Paid, no rate limits)
If OpenRouter free tier is too tight, use the official DeepSeek API instead — very cheap (~$0.28/M input tokens):
```json
"OPENAI_BASE_URL": "https://api.deepseek.com",
"OPENAI_MODEL": "deepseek-chat"
```

---

## 📁 Offline / Local Models (Fallback — Ollama)

### Your Installed Models Ranked for Complex Reasoning

| Model | Size | Strengths | Best For |
|-------|------|-----------|----------|
| **qwen3.6:latest** | 23 GB | Largest context, advanced reasoning | Most complex problems, long codebases |
| **deepseek-r1:14b** | 9 GB | Reasoning-specialized, strong logic | Critical thinking, planning, architecture |
| **gemma4:12b** | 7.6 GB | Latest Google model, good reasoning | Complex analysis, creative solutions |
| **deepseek-coder:6.7b** | 3.8 GB | Code-focused reasoning | Technical problem solving |
| **qwen2.5-coder:14b** | 9 GB | Excellent for web dev | Web development (project default) |
| **qwen2.5:7b** | 4.7 GB | General purpose, faster | General purpose |
| **deepseek-r1:7b** | 4.7 GB | Lightweight reasoning | Lighter reasoning tasks |
| **llama3.1:8b** | 4.9 GB | General purpose | Fallback general use |
| **codellama:7b** | 3.8 GB | Code completion | Code completion tasks |
| **nomic-embed-text** | 274 MB | Embeddings | Vector search/embeddings |

## Recommendations for Different Tasks

### Hard Problems / Fable-style Reasoning
```bash
# Primary choice - deepseek-r1:14b
opencode --model ollama:deepseek-r1:14b
# or
claude --model deepseek-r1:14b --mcp-config .claude.json
```

### Complex Codebases / Long Context
```bash
# If you have enough VRAM (qwen3.6 at 23GB)
opencode --model ollama:qwen3.6:latest
```

### Web Development / Medium Complexity
```bash
# Your qwen2.5-coder:14b is excellent
opencode --model ollama:qwen2.5-coder:14b
```

## Quick Test Commands

```bash
# Test reasoning with a prompt
ollama run deepseek-r1:14b "Explain the architecture pattern of a surreal procedural generator in 3 steps"

# Test with OpenCode
opencode --model ollama:deepseek-r1:14b --prompt "What's the best approach for multi-agent Blender/Unreal automation?"
```

## Model Switching in OpenCode

You can change models on-the-fly in OpenCode with `/model ollama:MODEL_NAME`