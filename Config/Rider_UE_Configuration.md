# JetBrains Rider Unreal Engine Development Setup

## Project Overview
- **Project**: BS_GodFile
- **Engine Version**: Unreal Engine 5.8
- **Module**: BS_GodFile (Runtime module)
- **Key Plugins**: UnrealMCP, ModelContextProtocol, PCG toolkit

## MCP Configuration for Rider

### Step 1: Install MCP Client Plugin
1. Open Rider → File → Settings → Plugins
2. Search for "MCP Client" in JetBrains Marketplace
3. Install the MCP Client plugin
4. Restart Rider

### Step 2: Import MCP Configuration
1. In Rider: File → Settings → Tools → MCP
2. Click "Import from file"
3. Select `.rider/mcp.json` from project root

This file mirrors the root `.mcp.json` (used by VS Code / Cline), so Rider and VS Code share the exact same tool set:
`monolith`, `it-is-unreal`, `figma`, `ueblueprintmcp` (off by default), `ollama`, `deepseek-v4` (OpenRouter), `kimi-k3` (TokenRouter).

> **API keys live only in `.rider/mcp.json` / `.mcp.json` / `.opencode.json`**, all listed in `.gitignore`. Do not commit them.

### Step 3: Configure Unreal Engine Plugin Support
The project has these MCP-related plugins already enabled:
- **UnrealMCP** - Core MCP integration
- **ModelContextProtocol** - Base MCP support
- **MCPClientToolset** - Client tools

### Step 4: Available MCP Tools
Once configured, you'll have access to:

| Server | Tools | Purpose |
|--------|-------|---------|
| ollama | chat, embeddings | Local LLM inference |
| hermes | search, docs | Web/docs search for UE/Blender |
| blender-mcp | scene_info, execute_code | Blender automation |
| surreal-arch-mcp | list_genomes, apply_genome | Procedural architecture |
| git-mcp | commit, push, status | Git operations |
| filesystem | read, write, list | File operations |

## Model Recommendations for UE Development

### In Rider with MCP:
- **For C++ debugging**: `deepseek-r1:14b` (strong reasoning)
- **For Python scripts**: `qwen2.5-coder:14b` (code focus)
- **For architecture questions**: `qwen3.6:latest` (large context)

### Quick Commands:
```bash
# Test model in terminal
ollama run deepseek-r1:14b "Explain UE5 PCG graph architecture for procedural rocks"
```

## Project Architecture Quick Reference

### Source Structure:
- `Source/BS_GodFile/BS_GodFile.Build.cs` - Module rules
- `Source/BS_GodFile/` - C++ source files

### Content Structure:
- `Content/Python/` - Python automation (25+ scripts)
- `Content/EnvSandbox/PCG/` - PCG graphs
- `Content/Melodia/` - Melodia game subsystem
- `deploy/*.py` - MCP adapters and orchestration

### Key Python API Points:
- `pcg_graph_builder.py` - Builds PCG graphs programmatically
- `surreal_arch_mcp_adapter.py` - Architecture generator tools
- `blender_mcp_adapter.py` - Blender automation bridge
- `mcp_git.py` - Git operations via MCP
