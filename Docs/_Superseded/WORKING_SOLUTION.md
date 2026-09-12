# Working Solution: Multi-Agent Orchestration Workflow

## Problem Summary
- Cursor: "Provider Error" - connection issues
- OpenCode: Shows "disconnected" - doesn't natively support Ollama
- Claude Code: Forgets context between messages
- Devin: Installed at `C:\Users\froma\AppData\Local\Programs\Devin\Devin.exe`

## Solution: Self-Contained Orchestrator

### 1. Direct Python Scripts (Most Reliable)
```bash
# Run the orchestrator - captures renders, updates website, deploys
python deploy/orchestrator.py --orchestrate

# Or step by step:
python deploy/orchestrator.py --blender-renders  # Check Blender MCP
python deploy/orchestrator.py --update-web        # Update website
python deploy/orchestrator.py --deploy             # Git push
```

### 2. MCP Tools Available (via ollama-mcp bridge)
Your MCP adapters provide these tools:
- `blender_scene_info` - Scene status
- `blender_execute_code` - Run bpy code
- `blender_viewport_screenshot` - Capture renders
- `surreal_list_genomes` - List style genomes
- `surreal_apply_genome` - Apply architectural styles
- `git_status` - Check git
- `git_add_commit_push` - Auto commit

### 3. Working Commands Right Now

```bash
# Check all MCP tools
python deploy/ai_tool_router.py --list-tools

# Check tool status
powershell -File deploy\ai_tool_quickstart.ps1 -Action status

# Sync website to GitHub
python deploy/ai_tool_router.py --sync-website

# Or run orchestration
python deploy/orchestrator.py --orchestrate
```

### 4. For Devin (Alternative)
Launch Devin and configure MCP with: `C:\EnvironmentPortfolio\BS_GodFile\.devin\mcp.json`

### 5. For Reliable AI Work

**Best approach given your issues:**
1. Use the provided Python scripts directly
2. Run them from terminal/PowerShell
3. MCP tools are always available through the adapters
4. No context loss, no disconnections

### 6. Next Steps to Fix Tools

```bash
# For OpenCode - install ollama plugin
opencode plugin ollama  # May need npm install -g @opencode/plugin-ollama

# For Claude Code - try with explicit config
claude --mcp-config .claude.json --model deepseek-r1:14b
```

## Quick Reference

| Goal | Command |
|------|---------|
| Orchestrate full workflow | `python deploy/orchestrator.py --orchestrate` |
| Check Blender connection | `python deploy/orchestrator.py --blender-renders` |
| Sync website | `python deploy/ai_tool_router.py --sync-website` |
| List all tools | `python deploy/ai_tool_router.py --list-tools` |
| Status check | `powershell deploy\ai_tool_quickstart.ps1` |

## Models Ranked for Your Work

| Model | Size | Best For |
|-------|------|----------|
| **deepseek-r1:14b** | 9GB | Critical thinking, planning |
| **qwen3.6:latest** | 23GB | Complex codebases |
| **gemma4:12b** | 7.6GB | Creative solutions |
| **qwen2.5-coder:14b** | 9GB | Web development |
