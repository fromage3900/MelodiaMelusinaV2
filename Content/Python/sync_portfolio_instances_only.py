"""Refresh portfolio material instances only — never modifies core masters (M_*/MF_*).

Headless:
  python Content/Python/sync_portfolio_instances_only.py

Editor:
  py Content/Python/sync_portfolio_instances_only.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "sync_portfolio_instances_only.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _build_instances_from_specs(specs: list[dict], resolve_keys_fn=None) -> list[dict]:
    """Create/update MI_* from specs without touching the parent master graph."""
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as tex_catalog

    try:
        import portfolio_alpha_paths as alphas
    except ImportError:
        alphas = None

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing master (read-only): {MASTER}")

    profile_names = sorted({spec.get("profile", "TP_Default") for spec in specs})
    profiles = lib.create_toon_profiles(profile_names)
    results: list[dict] = []

    for spec in specs:
        name = spec["name"]
        folder = spec["folder"]
        lib.ensure_directory(folder)
        inst = lib.create_material_instance(name, folder, MASTER)
        profile = profiles.get(spec.get("profile", "TP_Default"))
        if profile:
            lib.set_instance_toon_profile(inst, profile)
        for pname, rgba in spec.get("vectors", {}).items():
            lib.set_instance_vector(inst, pname, rgba)
        for pname, value in spec.get("scalars", {}).items():
            lib.set_instance_scalar(inst, pname, value)
        for pname, value in spec.get("switches", {}).items():
            lib.set_instance_static_switch(inst, pname, bool(value))

        wired_textures: dict[str, str] = {}
        texture_wires: dict[str, list[str]] = {}
        if alphas and resolve_keys_fn:
            texture_wires.update(resolve_keys_fn(spec, alphas))
        for pname, candidates in texture_wires.items():
            path = lib.set_instance_texture(inst, pname, candidates)
            if path:
                wired_textures[pname] = path
        extra = tex_catalog.apply_instance_texture_defaults(inst, name, wired_textures)
        wired_textures.update(extra)
        lib.save_package(inst)
        results.append({
            "instance": name,
            "folder": folder,
            "textures": wired_textures,
            "status": "created_or_updated",
        })
    return results


def run_sync() -> dict:
    import unreal
    from apply_starter_instances import build_starter_instances
    from apply_theme_instances import _resolve_texture_keys
    from theme_instances import BAROQUE_INSTANCES
    from zen_instances import ZEN_INSTANCES

    results: list[dict] = []
    ok = True

    def step(name: str, fn) -> None:
        nonlocal ok
        try:
            out = fn()
            results.append({"step": name, "ok": True, "detail": out})
            unreal.log(f"[InstancesOnly] {name} OK")
        except Exception as exc:
            ok = False
            results.append({"step": name, "ok": False, "error": str(exc)})
            unreal.log_error(f"[InstancesOnly] {name} failed: {exc}")

    step("starters", lambda: {"count": len(build_starter_instances())})
    step("sakura", lambda: __import__("setup_sakura_instances").build() or {"status": "ok"})
    step("baroque", lambda: {"count": len(_build_instances_from_specs(BAROQUE_INSTANCES, _resolve_texture_keys))})
    step("zen", lambda: {"count": len(_build_instances_from_specs(ZEN_INSTANCES, _resolve_texture_keys))})
    step("trimsheet", lambda: {"count": len(__import__("setup_trimsheet_instances").build())})
    step("nikki_hero_reparent", lambda: __import__("reparent_nikki_hero_instances").reparent_instances())

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "policy": "instances_only_no_master_edits",
        "steps": results,
        "all_ok": ok and all(r["ok"] for r in results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return report


def main() -> int:
    if _in_ue():
        report = run_sync()
        print(json.dumps({"all_ok": report["all_ok"], "report": str(REPORT)}, indent=2))
        return 0 if report["all_ok"] else 1
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / "sync_portfolio_instances_only.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/sync_portfolio_instances_only.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        "-nullrhi",
        "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    print(f"Instance-only sync -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
