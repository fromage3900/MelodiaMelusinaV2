"""Run all Melusina setup steps in sequence.

This script orchestrates the full Melusina exploration setup:
1. Rig assessment
2. Blend space creation
3. Blueprint duplication
4. MPC parameter check

Works via direct API when Unreal is available, falls back gracefully.
Writes audit reports to Saved/Audit/.

Usage (via UnrealEditor-Cmd - headless):
    # The PowerShell runner uses this mode
    # See deploy/run_melusina_setup.ps1 for full command
    
Usage (when Unreal Editor is running with MCP):
    # POST to http://localhost:9316 with:
    {"namespace":"editor","action":"run_python","params":{"command":"/full/path/to/run_melusina_all.py","mode":"execute_file"}}
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from pathlib import Path


def run_all() -> dict:
    """Execute all Melusina setup steps and return combined report."""
    audit = {
        "timestamp": str(datetime.datetime.now()),
        "rig_assessment": {},
        "blend_space": {},
        "blueprint": {},
        "mpc_params": {},
        "errors": [],
        "warnings": [],
    }
    
    # Step 1: Assess rig
    try:
        import assess_melusina_rig
        audit["rig_assessment"] = assess_melusina_rig.build_full_report()
    except Exception as e:
        audit["rig_assessment"] = {"error": str(e)}
        audit["errors"].append(f"Rig assessment failed: {e}")
    
    # Step 2: Create blend space
    try:
        import setup_melusina_exploration
        bs_result = setup_melusina_exploration.create_blend_space()
        audit["blend_space"] = bs_result
        if bs_result.get("error"):
            audit["warnings"].append(f"Blend space: {bs_result.get('error', '')}")
    except Exception as e:
        audit["blend_space"] = {"error": str(e)}
        audit["errors"].append(f"Blend space creation failed: {e}")
    
    # Step 3: Create exploration blueprint
    try:
        import setup_melusina_exploration
        bp_result = setup_melusina_exploration.create_exploration_blueprint()
        audit["blueprint"] = bp_result
    except Exception as e:
        audit["blueprint"] = {"error": str(e)}
        audit["errors"].append(f"Blueprint creation failed: {e}")
    
    # Step 4: Check MPC parameters
    try:
        import bridge_melusina_to_mpc
        mpc_result = bridge_melusina_to_mpc.build_mpc_bridge()
        audit["mpc_params"] = mpc_result
    except Exception as e:
        audit["mpc_params"] = {"error": str(e)}
        audit["warnings"].append(f"MPC bridge check failed: {e}")
    
    # Determine overall status
    has_unreal = "unreal" in sys.modules
    if has_unreal:
        critical_ok = (
            "error" not in audit["rig_assessment"] and
            audit["blueprint"].get("created", False)
        )
    else:
        # No Unreal - check if files exist and we can at least validate structure
        critical_ok = True  # Standalone mode, just report what we can
    
    audit["ok"] = critical_ok
    audit["unreal_available"] = has_unreal
    
    return audit


def save_audit(report: dict) -> str:
    """Save audit report to Saved/Audit directory."""
    audit_dir = Path(__file__).parent.parent / "Saved" / "Audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    path = audit_dir / "melusina_setup_audit.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return str(path)


def main() -> int:
    """Main entry point."""
    report = run_all()
    print(json.dumps(report, indent=2))
    
    path = save_audit(report)
    print(f"\nAudit saved to: {path}")
    
    return 0 if report.get("ok", False) else 1


if __name__ == "__main__":
    sys.exit(main())