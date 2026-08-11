"""Apply curated starter MI_Show_* instances: params, alpha masks, compositing textures.

Does NOT delete legacy MI_Universal_* — run archive_unused_instances.py separately.

Editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_starter_instances.py"

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_starter_instances.py" ^
    -unattended -nullrhi
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "starter_instances.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _resolve_texture_keys(spec: dict, alphas) -> dict[str, list[str]]:
    """Map short keys in spec['textures'] to catalog path lists."""
    wires: dict[str, list[str]] = {}
    tex_keys = spec.get("textures") or {}
    if not tex_keys or not alphas:
        return wires
    sparkle = getattr(alphas, "SPARKLE_MASKS", {})
    fairy = getattr(alphas, "FAIRY_GLYPH_MASKS", {})
    motif = getattr(alphas, "MOTIF_MASKS", {})
    for pname, key in tex_keys.items():
        if pname == "SparkleMask" and key in sparkle:
            wires[pname] = [sparkle[key]] if isinstance(sparkle[key], str) else list(sparkle[key])
        elif pname == "StarMap" and key in sparkle:
            wires[pname] = [sparkle[key]] if isinstance(sparkle[key], str) else list(sparkle[key])
        elif pname == "FairyGlyphMask" and key in fairy:
            wires[pname] = list(fairy[key])
        elif pname == "MotifMask" and key in motif:
            wires[pname] = list(motif[key])
    return wires


def build_starter_instances() -> list[dict]:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as tex_catalog
    from starter_instances import MASTER, SHOWCASE_DIR, STARTER_INSTANCES

    try:
        import portfolio_alpha_paths as alphas
    except ImportError:
        alphas = None

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing master: {MASTER} — run setup_master_universal.py first")

    if alphas:
        alphas.ensure_alpha_imports()

    profile_names = sorted({spec.get("profile", "TP_Default") for spec in STARTER_INSTANCES})
    profiles = lib.create_toon_profiles(profile_names)
    lib.ensure_directory(SHOWCASE_DIR)
    results: list[dict] = []

    for spec in STARTER_INSTANCES:
        name = spec["name"]
        inst = lib.create_material_instance(name, SHOWCASE_DIR, MASTER)
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
        if alphas:
            texture_wires.update(alphas.INSTANCE_TEXTURE_WIRES.get(name, {}))
        texture_wires.update(_resolve_texture_keys(spec, alphas))
        for pname, candidates in texture_wires.items():
            path = lib.set_instance_texture(inst, pname, candidates)
            if path:
                wired_textures[pname] = path
        extra = tex_catalog.apply_instance_texture_defaults(inst, name, wired_textures)
        wired_textures.update(extra)
        lib.save_package(inst)
        results.append({
            "instance": name,
            "purpose": spec.get("purpose", ""),
            "folder": SHOWCASE_DIR,
            "textures": wired_textures,
            "status": "created_or_updated",
        })

    return results


def _run_in_ue() -> int:
    import unreal

    unreal.log("=== APPLY STARTER INSTANCES ===")
    instances = build_starter_instances()
    import portfolio_texture_catalog as catalog

    texture_pass = catalog.refresh_starter_instance_textures()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "starter_count": len(instances),
        "instances": instances,
        "texture_refresh": texture_pass,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[StarterInstances] {len(instances)} starters -> {REPORT}")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: UE not found at {UE_CMD}")
        print("Run in-editor: py Content/Python/apply_starter_instances.py")
        return 1
    subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/portfolio_texture_catalog.py")], check=False)
    log = PROJECT_ROOT / "Saved" / "Logs" / "starter_instances.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/apply_starter_instances.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        "-nullrhi",
        f"-log={log}",
    ]
    print(f"Starter instances -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
