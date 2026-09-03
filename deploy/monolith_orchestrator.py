#!/usr/bin/env python
"""Monolithic Orchestrator - Unified agent system controller.

This brings together all 5 agents into a single coordinated system that:
- Monitors agent health in real-time
- Routes work between agents efficiently
- Handles cross-agent dependencies
- Provides unified API for MCP and UI clients

Usage:
    python monolith_orchestrator.py [--once] [--daemon]
"""
from __future__ import annotations

import json
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENT_MEMORY_DIR = PROJECT_ROOT / "Saved" / "AgentMemory"

# Agent definitions
AGENTS = {
    "geometry": {
        "name": "Geometry Agent",
        "owner": "PGA",
        "primary": "deploy/surreal_architecture_gen.py",
        "mcp": "blender-mcp",
        "loop_stop": "deploy/SURREAL_ARCH_LOOP_STOP",
        "status_file": "Saved/AgentMemory/geometry_status.json",
    },
    "material": {
        "name": "Material Agent",
        "owner": "MPA",
        "primary": "Content/Python/setup_master_universal.py",
        "mcp": "surreal-arch-mcp",
        "loop_stop": "deploy/MATERIAL_AAA_LOOP.pid",
        "status_file": "Saved/AgentMemory/material_status.json",
    },
    "placement": {
        "name": "Placement Agent",
        "owner": "PPA",
        "primary": "Content/Python/setup_pcg_universal.py",
        "mcp": "surreal-arch-mcp",
        "loop_stop": "deploy/SDF_FACTORY_LOOP.pid",
        "status_file": "Saved/AgentMemory/placement_status.json",
    },
    "integration": {
        "name": "Integration Agent",
        "owner": "WIA",
        "primary": "Content/Python/import_world_manifest.py",
        "mcp": "blender-mcp",
        "loop_stop": "deploy/SURREAL_WORLD_LOOP_STOP",
        "status_file": "Saved/AgentMemory/integration_status.json",
    },
    "qa": {
        "name": "QA Agent",
        "owner": "SQA",
        "primary": "deploy/run_verify.ps1",
        "mcp": "filesystem",
        "loop_stop": None,  # QA doesn't use loop stop
        "status_file": "Saved/AgentMemory/qa_status.json",
    }
}


def get_agent_health(agent_key: str) -> dict:
    """Get health status for a specific agent."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return {"status": "unknown", "error": "agent not found"}
    
    loop_stop_path = PROJECT_ROOT / agent["loop_stop"] if agent.get("loop_stop") else None
    status_file = PROJECT_ROOT / agent["status_file"]
    
    # Check loop stop
    is_running = True
    if loop_stop_path and loop_stop_path.exists():
        is_running = False
    
    # Check status file
    if status_file.exists():
        try:
            status_data = json.loads(status_file.read_text())
        except Exception:
            status_data = {}
    else:
        status_data = {}
    
    return {
        "name": agent["name"],
        "owner": agent["owner"],
        "status": "running" if is_running else "stopped",
        "health": status_data.get("health", "unknown"),
        "last_check": datetime.now().isoformat(),
    }


def get_all_agents_health() -> dict:
    """Get health status for all agents."""
    return {key: get_agent_health(key) for key in AGENTS}


def route_workflow(workflow_type: str, payload: dict) -> dict:
    """Route work to appropriate agents based on workflow type."""
    routing = {
        "build_environment": {
            "sequence": ["geometry", "material", "placement", "integration"],
            "description": "Build complete environment from genome",
        },
        "evolve_content": {
            "sequence": ["qa"],
            "description": "Run blessing evolution via QA agent",
        },
        "audit_system": {
            "sequence": ["qa"],
            "description": "Run system health audit",
        },
        "render_portfolio": {
            "sequence": ["geometry", "material", "placement", "integration"],
            "description": "Capture renders and build portfolio",
        }
    }
    
    workflow = routing.get(workflow_type)
    if not workflow:
        return {"error": "Unknown workflow type", "type": workflow_type}
    
    # Log workflow start
    workflow_log = {
        "timestamp": datetime.now().isoformat(),
        "workflow": workflow_type,
        "agents_involved": workflow["sequence"],
        "payload": payload,
    }
    
    log_file = AGENT_MEMORY_DIR / "workflow_log.json"
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except Exception:
            pass
    logs.append(workflow_log)
    log_file.write_text(json.dumps(logs[-50:], indent=2))
    
    return {
        "workflow": workflow_type,
        "description": workflow["description"],
        "agents": workflow["sequence"],
        "status": "routed",
    }


def monolith_tick() -> dict:
    """Single tick of the monolith - check all agents and route work."""
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    health = get_all_agents_health()
    
    # Check for pending work
    next_actions = []
    
    # Check for blessing evolution queue
    blessing_queue = AGENT_MEMORY_DIR / "blessing_evolution_queue.json"
    if blessing_queue.exists():
        try:
            queue = json.loads(blessing_queue.read_text())
            if queue:
                next_actions.append({
                    "type": "blessing_evolution",
                    "priority": "high",
                    "count": len(queue),
                })
        except Exception:
            pass
    
    # Check for prompt queue
    prompt_queue = AGENT_MEMORY_DIR / "prompt_queue.json"
    if prompt_queue.exists():
        try:
            queue = json.loads(prompt_queue.read_text())
            if queue:
                next_actions.append({
                    "type": "natural_language_prompt",
                    "priority": "medium",
                    "count": len(queue),
                })
        except Exception:
            pass
    
    # Save monolith state
    state = {
        "timestamp": datetime.now().isoformat(),
        "agents": health,
        "next_actions": next_actions,
        "monolith_version": "1.0",
    }
    
    state_file = AGENT_MEMORY_DIR / "monolith_state.json"
    state_file.write_text(json.dumps(state, indent=2))
    
    return state


def run_blessing_evolution(target_count: int = 5, element_focus: str = None) -> dict:
    """Run blessing evolution via monolith."""
    from blessing_evolution_daemon import process_evolution_request
    
    request = {"target_count": target_count}
    if element_focus:
        request["element_focus"] = element_focus
    
    return process_evolution_request(request)


def main():
    """Run monolith orchestrator."""
    AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    if "--daemon" in sys.argv:
        print("[Monolith] Starting daemon mode...")
        while True:
            state = monolith_tick()
            print("[Monolith] State saved: {} agents checked".format(len(state["agents"])))
            time.sleep(30)  # Check every 30 seconds
    
    elif "--once" in sys.argv:
        state = monolith_tick()
        print(json.dumps(state, indent=2))
    
    else:
        # Interactive mode
        print("Monolith Orchestrator Commands:")
        print("  --once      Run single check")
        print("  --daemon    Run continuous monitoring")
        print("  --workflow <type>  Route workflow")
        print("\nAvailable workflows:", list(route_workflow("", {})).keys() if False else "build_environment, evolve_content, audit_system, render_portfolio")


if __name__ == "__main__":
    if "--workflow" in sys.argv:
        idx = sys.argv.index("--workflow")
        if idx + 1 < len(sys.argv):
            workflow_type = sys.argv[idx + 1]
            payload = {}
            print(json.dumps(route_workflow(workflow_type, payload), indent=2))
    else:
        main()