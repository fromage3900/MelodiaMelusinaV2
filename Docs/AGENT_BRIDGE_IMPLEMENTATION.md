# Agent Bridge Implementation - Universal Environment Platform

## Overview

The Agent Bridge system provides a **single unified MCP entry point** for all 5 specialized agents (Geometry, Material, Placement, Integration, QA), plus a blessing evolution engine for the roguelike game system.

## What Was Created

### 1. `deploy/agent_bridge_mcp.py` - Universal MCP Bridge
A single MCP server that routes natural language intents to the appropriate agent:
- `delegate_to_agent` - Route intent to any agent by type (geometry/material/placement/integration/audit/blessing)
- `get_agent_status` - Get real-time status of all agents
- `get_agent_memory` - Query shared agent memory/context
- `run_blessing_evolution` - Generate new blessings via Ollama
- `ue_editor_command` - Prepare commands for UE editor execution

### 2. `Content/Python/agent_status_panel.py` - UE In-Editor Panel
UE Python module that shows agent status in the editor:
- Logs agent status to Output Log window
- Adds "Agent Bridge Status" menu entry under LiveLink
- Shows icons and readiness for each agent (🏛️🎨📍🔗🛡️)

### 3. `deploy/blessing_evolution_daemon.py` - AI-Generated Blessings
Daemon that processes blessing evolution requests via Ollama:
- Watches `Saved/AgentMemory/blessing_evolution_queue.json`
- Generates new blessing/curse pairs matching existing patterns
- Logs results to `blessing_evolution_log.json`

### 4. `deploy/start_agent_bridge.ps1` - Startup Script
PowerShell script to check and start the agent bridge system.

## Updated MCP Configurations

All MCP configs now include the agent-bridge server:
- `.opencode.json` (project config)
- `.cursor/mcp.json`
- `.devin/mcp.json`
- `.windsurf/mcp.json`
- `.rider/mcp.json`
- `c:/Users/froma/.config/opencode/opencode.jsonc` (user config)

## Usage Examples

### Natural Language Agent Calls
```
# Instead of knowing specific tool names:
delegate_to_agent("geometry", "apply_genome", {"genome_id": "ZEN_SHRINE_AXIS"})

# Get all agent status:
get_agent_status()

# Generate new blessings:
run_blessing_evolution(target_count=5, element_focus="Forte")
```

### In Unreal Editor
1. Open UE Editor
2. Go to LiveLink > Agent Bridge Status
3. Check Output Log for: 🏛️ Geometry, 🎨 Material, 📍 Placement, 🔗 Integration, 🛡️ QA

## Architecture

```
                    ┌───────────────────────────────┐
                    │    Agent Bridge MCP Server    │
                    │  Single entry point for all   │
                    └───────────────┬───────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Intent Parser  │     │  Memory Logger  │     │ Blessing Queue  │
│  (natural lang) │     │  (delegation)   │     │  (Ollama gen)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Existing MCP Adapters                        │
│  blender_mcp  |  surreal_arch_mcp  |  git_mcp  |  hermes        │
└─────────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Test in UE**: Launch Unreal Editor and verify Agent Bridge Status menu works
2. **Connect Ollama**: Ensure Ollama is running with `qwen2.5-coder:14b` model
3. **Evolve Blessings**: Use `run_blessing_evolution` to generate new content
4. **Expand Memory**: Add more shared context entries to AgentMemory

## File Locations

| Component | Path |
|-----------|------|
| MCP Bridge | `deploy/agent_bridge_mcp.py` |
| UE Panel | `Content/Python/agent_status_panel.py` |
| Blessing Daemon | `deploy/blessing_evolution_daemon.py` |
| Startup Script | `deploy/start_agent_bridge.ps1` |
| Evolution Queue | `Saved/AgentMemory/blessing_evolution_queue.json` |
| Delegation Log | `Saved/AgentMemory/delegation_log.json` |

---

*Created via Agent Bridge Expansion - 2026-07-20*