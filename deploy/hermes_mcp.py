#!/usr/bin/env python
"""Hermes MCP Server - Documentation, Git Health, and Blessings/Burdens tools.

Provides MCP tools for:
- Git health checks
- Blessings/burdens verification
- Creating new blessings/burdens
- Generating documentation reports

Usage:
    python hermes_mcp.py <command> [args]
    
Commands:
    verify        - Run verification pass
    blessings     - List current blessings
    add-blessing  - Add a new blessing/burden pair (requires JSON input)
    git-status    - Get git repository status
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "Saved" / "Audit"
MODS_PATH = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_RoomMods.json"

# Valid effect types for blessings
VALID_EFFECT_TYPES = {
    "starting_mana", "max_sp", "element_unlock", "passive",
    "perfect_window_bonus", "combo_persistence"
}

# Required fields for room modifiers
REQUIRED_MOD_FIELDS = {"blessing_id", "display_name", "description", "token_cost", "curse"}

TOOLS = {
    "hermes_verify": {
        "description": "Run Hermes verification for blessings and git health",
        "parameters": {}
    },
    "hermes_list_blessings": {
        "description": "List all current blessings/burdens",
        "parameters": {}
    },
    "hermes_add_blessing": {
        "description": "Add a new blessing/burden pair to room modifiers",
        "parameters": {
            "mod_id": {"type": "string", "description": "Unique modifier ID"},
            "blessing_data": {"type": "object", "description": "Blessing data JSON"}
        }
    },
    "hermes_git_status": {
        "description": "Get git repository health status",
        "parameters": {}
    }
}

def git_health_check():
    """Check git repository health."""
    result = {"status": "ok", "issues": []}
    
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=ROOT
        )
        lines = status.stdout.strip().split("\n") if status.stdout.strip() else []
        untracked = [l for l in lines if l.startswith("??")]
        modified = [l for l in lines if l and not l.startswith("??")]
        
        if untracked:
            result["issues"].append(f"{len(untracked)} untracked files")
        if modified:
            result["issues"].append(f"{len(modified)} modified files")
            
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        result["branch"] = branch.stdout.strip()
        
        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%H %s"],
            capture_output=True, text=True, cwd=ROOT
        )
        result["last_commit"] = log_result.stdout.strip()
        
    except Exception as e:
        result["status"] = "error"
        result["issues"].append(str(e))
    
    return result

def blessings_health_check():
    """Verify blessings and burdens integrity."""
    result = {"status": "ok", "blessings_count": 0, "burdens_count": 0}
    
    if not MODS_PATH.exists():
        return {"status": "missing", "message": "DT_MelodySlime_RoomMods.json not found"}
    
    data = json.loads(MODS_PATH.read_text(encoding="utf-8"))
    rows = data.get("Rows", {})
    
    valid_count = 0
    for mod_id, mod_data in rows.items():
        missing = REQUIRED_MOD_FIELDS - set(mod_data.keys())
        if not missing:
            valid_count += 1
            result["burdens_count"] += 1
    
    result["blessings_count"] = valid_count
    return result

def list_blessings():
    """List all blessings/burdens."""
    if not MODS_PATH.exists():
        return {"status": "missing", "blessings": []}
    
    data = json.loads(MODS_PATH.read_text(encoding="utf-8"))
    rows = data.get("Rows", {})
    
    return {
        "status": "ok",
        "count": len(rows),
        "blessings": [
            {
                "id": mod_id,
                "blessing_id": mod_data.get("blessing_id", ""),
                "display_name": mod_data.get("display_name", ""),
                "effect_type": mod_data.get("effect_type", "passive"),
                "curse": mod_data.get("curse", "")
            }
            for mod_id, mod_data in rows.items()
        ]
    }

def add_blessing(mod_id: str, blessing_data: dict):
    """Add a new blessing/burden pair."""
    if not MODS_PATH.exists():
        return {"status": "error", "message": "Room modifiers file not found"}
    
    data = json.loads(MODS_PATH.read_text(encoding="utf-8"))
    rows = data.get("Rows", {})
    
    if mod_id in rows:
        return {"status": "exists", "message": f"{mod_id} already exists"}
    
    # Validate required fields
    missing = REQUIRED_MOD_FIELDS - set(blessing_data.keys())
    if missing:
        return {"status": "error", "message": f"Missing required fields: {missing}"}
    
    # Validate effect_type
    effect_type = blessing_data.get("effect_type", "")
    if effect_type and effect_type not in VALID_EFFECT_TYPES:
        return {"status": "error", "message": f"Invalid effect_type: {effect_type}"}
    
    # Add the blessing
    rows[mod_id] = blessing_data
    data["Rows"] = rows
    MODS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    return {"status": "created", "mod_id": mod_id}

def run_verify():
    """Run full verification pass."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    
    git_result = git_health_check()
    blessings_result = blessings_health_check()
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "git": git_result,
        "blessings": blessings_result
    }
    
    report_path = AUDIT_DIR / "hermes_health.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    
    return report

def main():
    if len(sys.argv) < 2:
        print("Usage: hermes_mcp.py <command>")
        print("Commands:", list(TOOLS.keys()))
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "verify":
        result = run_verify()
    elif cmd == "blessings":
        result = list_blessings()
    elif cmd == "git-status":
        result = git_health_check()
    elif cmd == "add-blessing":
        if len(sys.argv) < 4:
            print("Usage: hermes_mcp.py add-blessing <mod_id> <blessing_data_json>")
            sys.exit(1)
        mod_id = sys.argv[2]
        blessing_data = json.loads(sys.argv[3])
        result = add_blessing(mod_id, blessing_data)
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()