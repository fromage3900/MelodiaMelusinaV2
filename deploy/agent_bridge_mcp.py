#!/usr/bin/env python
"""Universal Agent MCP Bridge - Single entry point for all 5 agents.

Provides natural language intent routing to specialized agents:
- Geometry Agent (Blender surreal_arch)
- Material Agent (UE Substrate Toon)
- Placement Agent (UE PCG systems)
- World Integration Agent (Live Link, imports)
- QA Sentinel Agent (health, audits, blessings)

Usage:
    python agent_bridge_mcp.py  # Runs as MCP server on stdio
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_MEMORY_DIR = PROJECT_ROOT / "Saved" / "AgentMemory"

TOOLS = [
    {
        "name": "delegate_to_agent",
        "description": "Route natural language intent to appropriate agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "What type of work: 'geometry', 'material', 'placement', 'integration', 'audit', or 'blessing'",
                },
                "action": {
                    "type": "string",
                    "description": "Specific action to perform",
                },
                "payload": {
                    "type": "object",
                    "description": "Additional parameters for the action",
                },
                "model": {
                    "type": "string",
                    "description": "Optional: Override model (e.g., 'qwen2.5-coder:14b', 'deepseek-r1:14b')",
                },
            },
            "required": ["intent", "action"],
        },
    },
    {
        "name": "get_agent_status",
        "description": "Get status of all agents or specific agent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Optional: Specific agent (geometry, material, placement, integration, qa)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_agent_memory",
        "description": "Query shared agent memory/context",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in agent memory",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "run_blessing_evolution",
        "description": "Evolve game blessings based on gameplay patterns",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_count": {
                    "type": "integer",
                    "description": "How many new blessings to generate",
                    "default": 5,
                },
                "element_focus": {
                    "type": "string",
                    "description": "Optional: Focus on specific element (Forte, Tide, Gale, etc.)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "ue_editor_command",
        "description": "Send command to Unreal Editor via Live Link",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "UE Python command to execute",
                },
                "wait_for_result": {
                    "type": "boolean",
                    "description": "Wait for result (requires UE Live Link ready)",
                },
            },
            "required": ["command"],
        },
    },
]


def route_intent(intent: str, action: str, payload: dict | None = None) -> dict:
    """Route intent to appropriate agent subsystem."""
    payload = payload or {}
    
    # Log the delegation
    log_delegation(intent, action, payload)
    
    if intent == "geometry":
        return handle_geometry(action, payload)
    elif intent == "material":
        return handle_material(action, payload)
    elif intent == "placement":
        return handle_placement(action, payload)
    elif intent == "integration":
        return handle_integration(action, payload)
    elif intent == "audit":
        return handle_audit(action, payload)
    elif intent == "blessing":
        return handle_blessing(action, payload)
    else:
        return {
            "status": "error",
            "message": f"Unknown intent: {intent}. Use: geometry, material, placement, integration, audit, blessing",
            "suggestion": f"Try rephrasing '{action}' with a clearer intent",
        }


def log_delegation(intent: str, action: str, payload: dict) -> None:
    """Log delegation to agent memory."""
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    log_file = AGENT_MEMORY_DIR / "delegation_log.json"
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "intent": intent,
        "action": action,
        "payload": payload,
    }
    
    # Append to log
    if log_file.exists():
        logs = json.loads(log_file.read_text())
    else:
        logs = []
    
    logs.append(entry)
    log_file.write_text(json.dumps(logs[-100:], indent=2))  # Keep last 100 entries


def handle_geometry(action: str, payload: dict) -> dict:
    """Geometry Agent: surreal_arch style genomes."""
    # Import and use surreal_arch_mcp_adapter logic
    if action == "list_genomes":
        return {"status": "delegate", "target": "surreal_list_genomes"}
    elif action == "apply_genome":
        genome_id = payload.get("genome_id", "ZEN_SHRINE_AXIS")
        return {"status": "delegate", "target": "surreal_apply_genome", "params": {"genome_id": genome_id}}
    elif action == "spawn_graph":
        genome_id = payload.get("genome_id", "ZEN_SHRINE_AXIS")
        return {"status": "delegate", "target": "surreal_spawn_graph", "params": {"genome_id": genome_id}}
    elif action == "randomize_dna":
        return {"status": "delegate", "target": "surreal_randomize_dna", "params": {"seed": payload.get("seed")}}
    else:
        return {"status": "error", "message": f"Unknown geometry action: {action}"}


def handle_material(action: str, payload: dict) -> dict:
    """Material Agent: UE material/master operations."""
    # Material workflow - check for relevant scripts
    if action == "build_universal":
        return {"status": "delegate", "target": "ue_execute", "script": "setup_master_universal.py"}
    elif action == "list_masters":
        masters_dir = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials"
        return {"status": "info", "masters_found": len(list(masters_dir.glob("**/*.uasset"))) if masters_dir.exists() else 0}
    elif action == "apply_toon_preset":
        profile = payload.get("profile", "TP_Default")
        return {"status": "delegate", "target": "ue_execute", "script": f"apply_toon_profile_{profile}.py"}
    else:
        return {"status": "error", "message": f"Unknown material action: {action}"}


def handle_placement(action: str, payload: dict) -> dict:
    """Placement Agent: PCG graph operations."""
    if action == "build_sakura":
        return {"status": "delegate", "target": "ue_execute", "script": "setup_pcg_sakura.py"}
    elif action == "build_zen":
        return {"status": "delegate", "target": "ue_execute", "script": "build_pcg_zen_shrine.py"}
    elif action == "build_universal":
        return {"status": "delegate", "target": "ue_execute", "script": "setup_pcg_universal.py"}
    elif action == "status":
        return check_pcg_status()
    else:
        return {"status": "error", "message": f"Unknown placement action: {action}"}


def check_pcg_status() -> dict:
    """Check PCG graph status."""
    pcg_dir = PROJECT_ROOT / "Content" / "EnvSandbox" / "PCG"
    graphs = list(pcg_dir.glob("**/*.uasset")) if pcg_dir.exists() else []
    return {
        "status": "ok",
        "graph_count": len(graphs),
        "graphs": [str(g.relative_to(PROJECT_ROOT)) for g in graphs[:10]],
    }


def handle_integration(action: str, payload: dict) -> dict:
    """World Integration Agent: Live Link, imports, coordination."""
    if action == "live_link_status":
        return check_livelink_status()
    elif action == "import_manifest":
        manifest_path = payload.get("manifest_path", "")
        return {"status": "delegate", "target": "ue_execute", "script": "import_world_manifest.py", "params": {"path": manifest_path}}
    elif action == "sync_blender":
        return {"status": "delegate", "target": "blender_scene_info"}
    else:
        return {"status": "error", "message": f"Unknown integration action: {action}"}


def check_livelink_status() -> dict:
    """Check Live Link connection status."""
    # Look for recent connection markers
    log_file = PROJECT_ROOT / "Saved" / "Logs" / "livelink.log"
    if log_file.exists():
        return {"status": "configured", "log_exists": True}
    return {"status": "configured", "log_exists": False, "note": "Start via UE LiveLink menu"}


def handle_audit(action: str, payload: dict) -> dict:
    """QA Sentinel Agent: Health checks, verification."""
    if action == "run_health":
        return {"status": "delegate", "target": "hermes_verify"}
    elif action == "blessings_health":
        return {"status": "delegate", "target": "hermes_list_blessings"}
    elif action == "git_status":
        return {"status": "delegate", "target": "git_status"}
    else:
        return {"status": "error", "message": f"Unknown audit action: {action}"}


def handle_blessing(action: str, payload: dict) -> dict:
    """Generate/evolve roguelike blessings."""
    if action == "evolve":
        target_count = payload.get("target_count", 5)
        element_focus = payload.get("element_focus")
        return {
            "status": "delegate",
            "target": "ollama_generate_blessings",
            "params": {"target_count": target_count, "element_focus": element_focus},
        }
    elif action == "list":
        # Return current blessings from roguelike.py
        blessings_file = PROJECT_ROOT / "Content" / "Python" / "gmm" / "game" / "roguelike.py"
        if blessings_file.exists():
            return {"status": "info", "source": str(blessings_file)}
        return {"status": "missing", "message": "Blessings source not found"}
    else:
        return {"status": "error", "message": f"Unknown blessing action: {action}"}


def get_agent_status(agent_name: str | None = None) -> dict:
    """Get status of all agents or specific agent."""
    # Check for loop stop files and health markers
    loop_files = {
        "geometry": PROJECT_ROOT / "deploy" / "SURREAL_ARCH_LOOP_STOP",
        "material": PROJECT_ROOT / "deploy" / "MATERIAL_AAA_LOOP.pid",
        "placement": PROJECT_ROOT / "deploy" / "SDF_FACTORY_LOOP.pid",
        "integration": PROJECT_ROOT / "deploy" / "SURREAL_WORLD_LOOP_STOP",
        "qa": PROJECT_ROOT / "deploy" / "SURREAL_ARCH_LOOP_STOP",
    }
    
    all_agents = ["geometry", "material", "placement", "integration", "qa"]
    
    if agent_name:
        all_agents = [agent_name] if agent_name in all_agents else []
    
    status_map = {}
    for agent in all_agents:
        loop_stop = loop_files.get(agent)
        if loop_stop and loop_stop.exists():
            status_map[agent] = {"status": "stopped", "loop_stop_file": str(loop_stop.name)}
        else:
            status_map[agent] = {"status": "ready"}
    
    # Check audit health
    audit_health = PROJECT_ROOT / "Saved" / "Audit" / "hermes_health.json"
    if audit_health.exists():
        try:
            health = json.loads(audit_health.read_text())
            status_map["qa"]["health"] = health.get("blessings", {}).get("blessings_count", 0)
        except Exception:
            pass
    
    return {
        "timestamp": datetime.now().isoformat(),
        "agents": status_map,
        "project_root": str(PROJECT_ROOT),
    }


def get_agent_memory(query: str, category: str | None = None) -> dict:
    """Query shared agent memory."""
    memory_file = AGENT_MEMORY_DIR / "shared_context.json"
    results = []
    
    if memory_file.exists():
        try:
            memory = json.loads(memory_file.read_text())
            # Simple text search through memory
            for entry in memory.get("entries", []):
                if query.lower() in json.dumps(entry).lower():
                    if category is None or category.lower() in entry.get("category", "").lower():
                        results.append(entry)
        except Exception:
            pass
    
    return {
        "query": query,
        "category": category,
        "results": results[:20],  # Limit results
        "total_found": len(results),
    }


def run_blessing_evolution(target_count: int = 5, element_focus: str | None = None) -> dict:
    """Generate new blessings based on existing patterns."""
    # Load existing blessings to find patterns
    blessings_file = PROJECT_ROOT / "Content" / "Python" / "gmm" / "game" / "roguelike.py"
    
    evolution_context = {
        "target_count": target_count,
        "element_focus": element_focus,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Store evolution request for daemon to pick up
    evolution_file = AGENT_MEMORY_DIR / "blessing_evolution_queue.json"
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    queue = []
    if evolution_file.exists():
        try:
            queue = json.loads(evolution_file.read_text())
        except Exception:
            pass
    
    queue.append(evolution_context)
    evolution_file.write_text(json.dumps(queue, indent=2))
    
    return {
        "status": "queued",
        "message": f"Blessing evolution request queued for {target_count} blessings",
        "element_focus": element_focus or "all",
    }


def ue_editor_command(command: str, wait_for_result: bool = False) -> dict:
    """Prepare UE editor command for execution."""
    return {
        "status": "prepared",
        "command": command,
        "wait_for_result": wait_for_result,
        "note": "Execute this Python in UE Editor via init_unreal.py or LiveLink",
    }


def main():
    """Main MCP stdio loop."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        rid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})
        
        if method == "initialize":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "agent-bridge-mcp", "version": "1.0.0"},
                },
            }) + "\n")
            sys.stdout.flush()
        
        elif method == "tools/list":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"tools": TOOLS},
            }) + "\n")
            sys.stdout.flush()
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            
            if tool_name == "delegate_to_agent":
                result = route_intent(
                    args.get("intent", ""),
                    args.get("action", ""),
                    args.get("payload"),
                )
            elif tool_name == "get_agent_status":
                result = get_agent_status(args.get("agent_name"))
            elif tool_name == "get_agent_memory":
                result = get_agent_memory(args.get("query", ""), args.get("category"))
            elif tool_name == "run_blessing_evolution":
                result = run_blessing_evolution(
                    args.get("target_count", 5),
                    args.get("element_focus"),
                )
            elif tool_name == "ue_editor_command":
                result = ue_editor_command(
                    args.get("command", ""),
                    args.get("wait_for_result", False),
                )
            else:
                result = {"status": "error", "message": f"Unknown tool: {tool_name}"}
            
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }) + "\n")
            sys.stdout.flush()
        
        elif method == "notifications/initialized":
            pass
        
        else:
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()