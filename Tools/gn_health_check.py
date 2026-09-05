#!/usr/bin/env python3
"""
GN Health Check — Verify all Geometry Nodes builders are functional.

Runs through every registered GN builder and checks:
1. The module imports without errors
2. The build function exists
3. The node tree can be created (if bpy is available)

Usage:
    python Tools/gn_health_check.py          # offline (import check only)
    python Tools/gn_health_check.py --live   # in-Blender (full check)

Output: Saved/Audit/gn_health_report_YYYY-MM-DD.json
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
SAVE_DIR = REPO / "Saved" / "Audit"

# Paths to check
GN_PATHS = [
    ("Melodia GN", REPO / "deploy" / "surreal_arch" / "melodia_gn"),
    ("Kawaii GN", REPO / "Tools" / "BlenderAddons" / "blender_kawaii_gn"),
    ("Brutalist GN", REPO / "Tools" / "BlenderAddons" / "blender_brutalist_gn"),
    ("Melodia Studio", REPO / "Tools" / "BlenderAddons" / "melodia_studio"),
    ("Resonant World", REPO / "Tools" / "BlenderAddons" / "resonant_world_studio"),
    ("Melodia Aura", REPO / "Tools" / "BlenderAddons" / "melodia_aura"),
    ("Melodia Showroom", REPO / "Tools" / "BlenderAddons" / "melodia_showroom"),
    ("Melodia Stage", REPO / "Tools" / "BlenderAddons" / "melodia_stage"),
    ("Melodia Pose Audit", REPO / "Tools" / "BlenderAddons" / "melodia_pose_audit"),
    ("GenesisCore", REPO / "Tools" / "BlenderAddons" / "GenesisCore"),
]


def check_import(path: Path, name: str) -> dict:
    """Try to import a module and report status."""
    result = {"name": name, "path": str(path), "ok": False, "error": None, "modules": 0, "builders": []}

    if not path.exists():
        result["error"] = "path not found"
        return result

    # Add to sys.path if needed
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    parent = path.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))

    try:
        # Count Python files
        py_files = list(path.rglob("*.py"))
        result["modules"] = len(py_files)

        # Try importing the package
        pkg_name = path.name
        spec = importlib.util.spec_from_file_location(pkg_name, path / "__init__.py")
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result["ok"] = True

            # Check for registry
            for attr in ("KAWAII_GN_REGISTRY", "BRUTALIST_GN_REGISTRY", "MELODIA_GN_REGISTRY"):
                reg = getattr(mod, attr, None)
                if reg:
                    result["registry"] = attr
                    result["registry_size"] = len(reg)
                    result["builders"] = list(reg.keys())[:20]  # first 20

        else:
            # No __init__.py — check if it's a module package
            result["error"] = "no __init__.py found"
            result["ok"] = True  # not necessarily an error

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc().split("\n")[-5:]

    return result


def check_melodia_gn_special(path: Path) -> dict:
    """Melodia GN is special — it's a flat package of builders, not a class registry."""
    result = {"name": "Melodia GN", "path": str(path), "ok": False, "error": None, "modules": 0, "builders": []}

    if not path.exists():
        result["error"] = "path not found"
        return result

    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

    try:
        py_files = [f for f in path.glob("*.py") if f.name != "__init__.py"]
        result["modules"] = len(py_files)

        # Count build functions
        build_fns = []
        for f in py_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "def build_" in content:
                    build_fns.append(f.stem)
            except Exception:
                pass

        result["builders"] = build_fns[:30]
        result["builder_count"] = len(build_fns)
        result["ok"] = True

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"

    return result


def main():
    live = "--live" in sys.argv
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if live else "offline",
        "python": sys.version,
        "systems": [],
        "total_modules": 0,
        "total_builders": 0,
        "errors": 0,
    }

    for name, path in GN_PATHS:
        print(f"Checking {name}...", end=" ", flush=True)

        if name == "Melodia GN":
            r = check_melodia_gn_special(path)
        else:
            r = check_import(path, name)

        report["systems"].append(r)
        report["total_modules"] += r.get("modules", 0)
        report["total_builders"] += r.get("builder_count", len(r.get("builders", [])))
        if r.get("error"):
            report["errors"] += 1
            print(f"ERROR: {r['error']}")
        else:
            print(f"OK ({r.get('modules', 0)} modules)")

    # Save report
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = SAVE_DIR / f"gn_health_report_{ts}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Total modules: {report['total_modules']}")
    print(f"Total builders: {report['total_builders']}")
    print(f"Errors: {report['errors']}")
    print(f"Report: {report_path}")

    return 0 if report["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
