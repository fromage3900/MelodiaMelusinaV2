# Additional MCP Servers: Hermes Integration

## Hermes MCP - ✅ ADDED
Hermes provides:
- **Web search capabilities** via Brave Search API (optional)
- **Documentation lookup** (ReadTheDocs, MDN, Unreal docs)
- **GitHub integration** - search repos, issues, PRs
- Essential for research and finding Unreal/Blender documentation

**Config:** Already configured in `.rider/mcp.json` and can be added to other MCP configs

```json
{
  "mcpServers": {
    "hermes": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-hermes"]
    }
  }
}
```

## JetBrains Rider MCP Integration

Rider supports MCP through the "MCP Client" plugin. Configuration:

1. Install the **MCP Client** plugin from JetBrains Marketplace
2. Use `.rider/mcp.json` config (created)
3. In Rider: Settings → Tools → MCP → Import from file

## Usage with OpenCode Desktop

All MCP servers work with OpenCode. Point to your config:

```bash
# Use project config
opencode --config .opencode.json --model ollama:qwen2.5-coder:14b

# Or use Rider config
opencode --config .rider/mcp.json
```

## Model Recommendations by Task

| Task | Model | Command |
|------|-------|---------|
| Complex Reasoning | deepseek-r1:14b | `opencode --model ollama:deepseek-r1:14b` |
| Web Development | qwen2.5-coder:14b | `opencode --model ollama:qwen2.5-coder:14b` |
| Large Context | qwen3.6:latest | `opencode --model ollama:qwen3.6:latest` |
| Code Completion | codellama:7b | `opencode --model ollama:codellama:7b` |
