#!/usr/bin/env python
"""Hermes Daemon - Documentation, Git Health, and Blessings/Burdens Verification.

This daemon:
1. Generates documentation from project state
2. Monitors git health (status, untracked files, divergence)
3. Verifies room modifiers blessings/curses pairs
4. Creates new blessings/burdens with proper validation
5. Sends out status updates via log files

Stop: deploy/HERMES_DAEMON_STOP
"""
from __future__ import annotations
import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "Saved" / "Audit"
STOP_FILE = ROOT / "deploy" / "HERMES_DAEMON_STOP"
LOG_FILE = ROOT / "deploy" / "hermes_daemon.log"

# Valid effect types for blessings
VALID_EFFECT_TYPES = {
    "starting_mana", "max_sp", "element_unlock", "passive",
    "perfect_window_bonus", "combo_persistence"
}

# Required fields for room modifiers
REQUIRED_MOD_FIELDS = {"blessing_id", "display_name", "description", "token_cost", "curse"}

def log(message: str):
    """Write timestamped log entry."""
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line, flush=True)
    LOG_FILE.open("a", encoding="utf-8").write(line + "\n")

def git_health_check() -> dict:
    """Check git repository health."""
    result = {"status": "ok", "issues": []}
    
    try:
        # Get git status
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
            
        # Check branch status
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        result["branch"] = branch.stdout.strip()
        
        # Check last commit
        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%H %s"],
            capture_output=True, text=True, cwd=ROOT
        )
        result["last_commit"] = log_result.stdout.strip()
        
    except Exception as e:
        result["status"] = "error"
        result["issues"].append(str(e))
    
    return result

def blessings_health_check() -> dict:
    """Verify blessings and burdens (room modifiers) integrity."""
    result = {"status": "ok", "issues": [], "blessings_count": 0, "burdens_count": 0}
    
    # Check DT_MelodySlime_RoomMods.json
    mods_path = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_RoomMods.json"
    if not mods_path.exists():
        result["issues"].append("DT_MelodySlime_RoomMods.json not found")
        result["status"] = "missing"
        return result
    
    try:
        data = json.loads(mods_path.read_text(encoding="utf-8"))
        rows = data.get("Rows", {})
        
        valid_count = 0
        burden_count = 0
        
        for mod_id, mod_data in rows.items():
            # Check blessing structure
            blessing_issues = []
            
            # Verify required fields
            missing = REQUIRED_MOD_FIELDS - set(mod_data.keys())
            if missing:
                result["issues"].append(f"{mod_id}: missing fields {missing}")
                continue  # Skip rest if missing required fields
            
            # Verify curse field exists (blessing is represented by display_name)
            if "curse" not in mod_data:
                result["issues"].append(f"{mod_id}: missing curse field for blessing pair")
                continue
            
            burden_count += 1
            
            # Verify effect_type is valid
            effect_type = mod_data.get("effect_type", "")
            if effect_type and effect_type not in VALID_EFFECT_TYPES:
                blessing_issues.append(f"unknown effect_type: {effect_type}")
                result["issues"].append(f"{mod_id}: {blessing_issues}")
            
            if not blessing_issues:
                valid_count += 1
        
        result["blessings_count"] = valid_count
        result["burdens_count"] = burden_count
        
        if result["issues"]:
            result["status"] = "warning"
            
    except Exception as e:
        result["issues"].append(f"JSON parse error: {e}")
        result["status"] = "error"
    
    return result

def generate_documentation() -> dict:
    """Generate documentation report."""
    result = {"files_written": 0}
    
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate blessings report
    blessings_report = {
        "generated_at": datetime.now().isoformat(),
        "blessings_file": "Content/Melodia/DataStuctures/DT_MelodySlime_RoomMods.json",
    }
    
    mods_path = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_RoomMods.json"
    if mods_path.exists():
        data = json.loads(mods_path.read_text(encoding="utf-8"))
        rows = data.get("Rows", {})
        
        blessings_report["total_modifiers"] = len(rows)
        blessings_report["burdens_pairs"] = [
            {
                "id": mod_id,
                "blessing": mod_data.get("display_name", ""),
                "curse": mod_data.get("curse", "")
            }
            for mod_id, mod_data in rows.items()
        ]
    
    # Write report
    report_path = AUDIT_DIR / "HERMES_BLESSINGS_REPORT.json"
    report_path.write_text(json.dumps(blessings_report, indent=2), encoding="utf-8")
    result["files_written"] += 1
    
    return result

def create_blessing_burden(mod_id: str, blessing_data: dict) -> dict:
    """Create a new blessing/burden pair in the room modifiers JSON."""
    mods_path = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_RoomMods.json"
    
    if not mods_path.exists():
        return {"status": "error", "message": "Room modifiers file not found"}
    
    try:
        data = json.loads(mods_path.read_text(encoding="utf-8"))
        rows = data.get("Rows", {})
        
        # Check if already exists
        if mod_id in rows:
            return {"status": "exists", "message": f"{mod_id} already exists"}
        
        # Validate required fields
        missing = REQUIRED_MOD_FIELDS - set(blessing_data.keys())
        if missing:
            return {"status": "error", "message": f"Missing fields: {missing}"}
        
        # Add to rows
        rows[mod_id] = blessing_data
        data["Rows"] = rows
        
        # Write back
        mods_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
        return {"status": "created", "mod_id": mod_id}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_pass():
    """Execute one verification pass."""
    log("Running Hermes verification pass...")
    
    # Git health
    git_result = git_health_check()
    log(f"Git health: {git_result['status']} - {', '.join(git_result.get('issues', [])) or 'clean'}")
    
    # Blessings health
    blessings_result = blessings_health_check()
    log(f"Blessings health: {blessings_result['status']} - {blessings_result['blessings_count']} valid pairs, "
        f"{blessings_result['burdens_count']} burden pairs")
    
    if blessings_result["issues"]:
        for issue in blessings_result["issues"][:5]:  # Limit output
            log(f"  Issue: {issue}")
    
    # Generate documentation
    doc_result = generate_documentation()
    log(f"Documentation: {doc_result['files_written']} files written")
    
    # Write health report
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "git": git_result,
        "blessings": blessings_result,
        "documentation": doc_result
    }
    
    report_path = AUDIT_DIR / "hermes_health.json"
    report_path.write_text(json.dumps(health_report, indent=2), encoding="utf-8")

def main():
    """Main daemon loop, or a single pass with --run-once."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run one verification pass and exit (no daemon loop)",
    )
    args = parser.parse_args()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    if args.run_once:
        log("Hermes run-once pass")
        run_pass()
        log("Run-once complete")
        return

    log("Hermes daemon started")

    last_census = None
    while not STOP_FILE.exists():
        # Run verification
        run_pass()
        log("Pass complete, sleeping 60s...")
        
        # Sleep in small increments to check stop file
        for _ in range(60):
            if STOP_FILE.exists():
                break
            time.sleep(1)
    
    log("Hermes daemon stopped")

if __name__ == "__main__":
    main()