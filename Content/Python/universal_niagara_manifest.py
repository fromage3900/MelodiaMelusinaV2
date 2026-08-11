"""Disk-only manifest and readiness report for the universal Niagara portfolio kit.

This script does not import Unreal or modify assets. It parses
setup_niagara_library.py and compares the authored system specs against the
latest Niagara build report.

Run:
  python Content/Python/universal_niagara_manifest.py
"""
from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT_ROOT / "Content" / "Python" / "setup_niagara_library.py"
BUILD_REPORT = PROJECT_ROOT / "Saved" / "Audit" / "niagara_library_build.json"
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "VFX"
MANIFEST_PATH = OUT_DIR / "universal_niagara_manifest.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _eval(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_eval(item, env) for item in node.elts)
    if isinstance(node, ast.List):
        return [_eval(item, env) for item in node.elts]
    if isinstance(node, ast.Name):
        return env.get(node.id, node.id)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                parts.append(str(part.value))
            elif isinstance(part, ast.FormattedValue):
                parts.append(str(_eval(part.value, env)))
        return "".join(parts)
    raise ValueError(f"unsupported ast node: {type(node).__name__}")


def _env(tree: ast.Module) -> dict[str, Any]:
    env: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        env[target.id] = _eval(node.value, env)
                    except Exception:
                        pass
    return env


def _systems(tree: ast.Module, env: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    assign = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SYSTEMS"
        ),
        None,
    )
    if not isinstance(assign, ast.AnnAssign) or not isinstance(assign.value, ast.Tuple):
        return entries

    for item in assign.value.elts:
        if not isinstance(item, ast.Call):
            continue
        args = [_eval(arg, env) for arg in item.args]
        kwargs = {kw.arg: _eval(kw.value, env) for kw in item.keywords if kw.arg}
        name = str(args[0]) if args else "UNKNOWN"
        folder = str(args[1]) if len(args) > 1 else ""
        template = str(args[2]) if len(args) > 2 else kwargs.get("template_emitter")
        family = "Universal" if "/Universal" in folder else folder.rsplit("/", 1)[-1]
        entries.append(
            {
                "system_name": name,
                "asset_path": f"{folder}/{name}.{name}",
                "vfx_family": family,
                "template": template or kwargs.get("atmospheric_preset"),
                "theme": kwargs.get("theme", ""),
                "paired_materials": list(kwargs.get("paired_materials", ())),
                "user_params": list(kwargs.get("user_params", ())),
                "portfolio_role": _portfolio_role(name, str(kwargs.get("theme", ""))),
            }
        )
    return entries


def _portfolio_role(name: str, theme: str) -> str:
    text = f"{name} {theme}".lower()
    if "water" in text or "rain" in text:
        return "water_and_weather"
    if "dust" in text or "mist" in text or "wisp" in text:
        return "atmosphere_depth"
    if "fire" in text or "sparkle" in text or "constellation" in text:
        return "magical_readability"
    if "leaf" in text or "petal" in text:
        return "wind_motion"
    if "trail" in text or "burst" in text:
        return "cinematic_accent"
    return "ambient_support"


def _latest_status() -> dict[str, str]:
    if not BUILD_REPORT.is_file():
        return {}
    try:
        report = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
    except Exception:
        return {}
    statuses: dict[str, str] = {}
    for item in report.get("built", []):
        if isinstance(item, dict) and item.get("name"):
            statuses[str(item["name"])] = str(item.get("status") or "unknown")
    for item in report.get("errors", []):
        if isinstance(item, dict) and item.get("name"):
            statuses[str(item["name"])] = "error"
    return statuses


def build_manifest() -> dict[str, Any]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8-sig"), filename=str(SOURCE))
    env = _env(tree)
    systems = _systems(tree, env)
    statuses = _latest_status()
    for system in systems:
        build_status = statuses.get(system["system_name"], "planned")
        system["build_status"] = build_status
        system["readiness"] = "needs_editor_build" if build_status == "planned" else "needs_pie_tune"
        if build_status in {"existing", "created"}:
            system["readiness"] = "structural_ready_visual_tuning_required"
        if build_status == "error":
            system["readiness"] = "blocked"

    counts: dict[str, int] = {}
    readiness: dict[str, int] = {}
    for system in systems:
        counts[system["vfx_family"]] = counts.get(system["vfx_family"], 0) + 1
        readiness[system["readiness"]] = readiness.get(system["readiness"], 0) + 1

    return {
        "generated_at": _now(),
        "generated_by": "universal_niagara_manifest.py",
        "ok": True,
        "source": SOURCE.as_posix(),
        "latest_build_report": BUILD_REPORT.as_posix() if BUILD_REPORT.is_file() else None,
        "counts": {"systems": len(systems), "families": counts, "readiness": readiness},
        "systems": systems,
        "acceptance_gates": [
            "No Niagara compile errors in editor output log.",
            "Each universal system has a stable thumbnail or 5-10 second reel clip.",
            "Spawn bounds are visible enough for portfolio review but not noisy.",
            "User parameters are named consistently for Sequencer or Blueprint control.",
            "VFX supports material/look-dev without hiding material surface quality.",
        ],
    }


def main() -> int:
    manifest = build_manifest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        "UNIVERSAL_NIAGARA_MANIFEST "
        f"systems={manifest['counts']['systems']} "
        f"families={manifest['counts']['families']} -> {MANIFEST_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

