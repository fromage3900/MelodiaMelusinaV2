"""Nap-time portfolio prep — instance-only materials, mesh renames, WP recreate.

  python Content/Python/run_nap_prep.py
  python Content/Python/run_nap_prep.py --skip-wp
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
AUDIT = PROJECT_ROOT / "Saved" / "Audit"
LOG_DIR = PROJECT_ROOT / "Saved" / "Logs"
REPORT = AUDIT / "nap_prep.json"


def _py(script: str, *args: str) -> tuple[int, str]:
    log = LOG_DIR / f"nap_prep_{script.replace('.py', '')}.log"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(PYTHON / script), *args]
    print(f">>> {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    log.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return proc.returncode, str(log)


def main() -> int:
    skip_wp = "--skip-wp" in sys.argv
    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "policy": "instances_only_materials",
        "steps": [],
    }
    rc = 0

    # Refuse rather than terminate an editor that may belong to another lane.
    probe = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "$p=Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue; if ($p) { $p | Select-Object Id,ProcessName; exit 2 }"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        print("Refusing nap prep while an Unreal editor process is active.")
        if probe.stdout:
            print(probe.stdout.strip())
        return 2

    filesystem_steps = [
        ("audit_static_mesh_inventory", "audit_static_mesh_inventory.py"),
        ("restore_portfolio_textures", "restore_portfolio_textures.py"),
        ("audit_material_library_baseline", "audit_material_library.py"),
        ("material_instance_audit_baseline", "material_instance_audit.py"),
    ]
    for label, script in filesystem_steps:
        code, log_path = _py(script)
        report["steps"].append({"step": label, "exit_code": code, "log": log_path})
        if code != 0:
            rc = 1

    ue_steps = [
        ("rename_static_meshes", "rename_static_meshes.py"),
        ("sync_portfolio_instances_only", "sync_portfolio_instances_only.py"),
        ("refresh_instance_textures", "portfolio_texture_catalog.py", "--refresh-instances"),
    ]
    if not skip_wp:
        ue_steps.append(("wp_recreate", "run_wp_pillar_levels_cmd.py", "--all", "--recreate-wp"))

    for entry in ue_steps:
        label, script, *args = entry
        code, log_path = _py(script, *args)
        report["steps"].append({"step": label, "exit_code": code, "log": log_path})
        if code != 0:
            rc = 1
            if label == "wp_recreate":
                print("WARNING: WP recreate failed — stopping before post-audits")
                break

    post_steps = [
        ("audit_static_mesh_inventory_post", "audit_static_mesh_inventory.py"),
        ("material_instance_audit_post", "material_instance_audit.py"),
        ("audit_material_library_post", "audit_material_library.py"),
    ]
    for label, script in post_steps:
        code, log_path = _py(script)
        report["steps"].append({"step": label, "exit_code": code, "log": log_path})

    report["exit_code"] = rc
    AUDIT.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Nap prep complete rc={rc} -> {REPORT}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
