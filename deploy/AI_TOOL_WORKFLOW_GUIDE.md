# AI Tool Workflow Guide - Multi-Agent Production Environment

## Overview
This guide documents the recommended replacement workflow for Cursor with unreliable local models. You now have multiple MCP-compatible options that can handle both Blender/Unreal automation and HTML website updates.

## Quick Start

### 1. Ensure Ollama is Running
```powershell
# Start Ollama service
ollama serve

# Verify with recommended model
ollama run qwen2.5-coder:14b
```

### 2. Choose Your AI Assistant

| Assistant | Config File | Best For | Offline |
|-----------|-------------|----------|---------|
| **Claude/Cursor** | `.cursor/mcp.json` | General purpose, full tool access | No |
| **OpenCode** | `.opencode.json` | Offline work, stable MCP | Yes |
| **Continue.dev** | `.continue/config.json` | VS Code integration | Yes |
| **Claude Code CLI** | `.claude.json` | Command line workflow | Yes |
| **Windsurf** | `.windsurf/mcp.json` | Experimental, promising | Yes |
| **JetBrains Rider** | `.rider/mcp.json` | UE C++ development | Yes |

## Configuration Files Created

### `.cursor/mcp.json` - Cursor MCP Config
- Ollama integration via ollama-mcp
- Filesystem server for project access
- Blender MCP adapter on port 9877
- Surreal Arch MCP adapter

### `.opencode.json` - OpenCode Config (Primary Alternative)
```bash
# Install (if not already)
npm install -g opencode

# Use with Ollama
opencode --model ollama:qwen2.5-coder:14b
```

### `.continue/config.json` - Continue.dev VS Code Extension
- Local Ollama provider
- Custom commands for website sync
- Slash commands for HTML editing

### `.claude.json` - Claude Code CLI
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Run with MCP
claude --mcp-config .claude.json
```

### `.windsurf/mcp.json` - Windsurf IDE
- Similar structure to Cursor config
- Windsurf-specific optimizations

## Available MCP Tools

### Blender Tools
- `blender_scene_info` - Get scene overview
- `blender_object_info` - Object details
- `blender_execute_code` - Arbitrary bpy code
- `blender_viewport_screenshot` - Capture renders
- `blender_shared_context` - Get context state

### Surreal Architecture Tools
- `surreal_list_genomes` - List 42 style genomes
- `surreal_status` - Active object properties
- `surreal_apply_genome` - Apply style genome
- `surreal_randomize_dna` - Random DNA values
- `surreal_spawn_graph` - Spawn greybox graphs
- `surreal_smoke_test` - Run test harness

## Website Workflow

### Editing HTML
Use any tool with filesystem access to edit:
- `my-site-clean/wix/index.html`
- `my-site-clean/wix/sakura-case-study.html`

### Sync to GitHub Pages
```bash
# Via router script
python deploy/ai_tool_router.py --sync-website

# Or via PowerShell
pwsh deploy/sync_site_to_github.ps1
```

## Troubleshooting

### "Provider Error" with Cursor
1. Ensure Ollama is running: `ollama serve`
2. Switch to OpenCode as alternative: `opencode`
3. Check tunnel if using remote Cursor: `pwsh deploy/start_cursor_ollama_tunnel.ps1`

### MCP Server Connection Issues
1. Verify Blender MCP addon is running on port 9877
2. Check Python path in configs matches your system
3. Run `python deploy/ai_tool_router.py --list-tools` to verify

### Your Installed Models
| Model | Size | Best For |
|-------|------|----------|
| `qwen2.5-coder:14b` | 9 GB | Web Development (recommended) |
| `deepseek-r1:14b` | 9 GB | Reasoning/Planning |
| `qwen2.5:7b` | 4.7 GB | General purpose, faster |
| `deepseek-r1:7b` | 4.7 GB | Lightweight reasoning |
| `gemma4:12b` | 7.6 GB | Alternative web dev |
| `llama3.1:8b` | 4.9 GB | General purpose |
| `qwen3.6:latest` | 23 GB | Large context (if available) |

### Model Recommendations
- **Web Development**: `qwen2.5-coder:14b` (your 9GB model)
- **Reasoning/Planning**: `deepseek-r1:14b` 

## Architecture Pattern

```
Your Request → AI Assistant (Claude/OpenCode/etc)
    ↓
MCP Protocol → Local Servers (Ollama + Adapters)
    ↓
  Tools: blender_mcp | surreal_arch_mcp | filesystem
    ↓
  Results → File Updates | Blender Actions | HTML Changes
