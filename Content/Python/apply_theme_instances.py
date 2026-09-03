"""Apply surreal baroque + zen themed instances; refresh master Japanese ornament maps.

Editor:
  py Content/Python/apply_theme_instances.py

Headless:
  python Content/Python/apply_theme_instances.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "theme_instances.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _resolve_texture_keys(spec: dict, alphas) -> dict[str, list[str]]:
    wires: dict[str, list[str]] = {}
    tex_keys = spec.get("textures") or {}
    if not tex_keys or not alphas:
        return wires
    sparkle = getattr(alphas, "SPARKLE_MASKS", {})
    fairy = getattr(alphas, "FAIRY_GLYPH_MASKS", {})
    motif = getattr(alphas, "MOTIF_MASKS", {})
    jro = getattr(alphas, "JAPANESE_ORNAMENT_MASKS", {})
    for pname, key in tex_keys.items():
        if pname == "SparkleMask" and key in sparkle:
            wires[pname] = [sparkle[key]] if isinstance(sparkle[key], str) else list(sparkle[key])
        elif pname == "FairyGlyphMask":
            if key in jro:
                wires[pname] = list(jro[key])
            elif key in fairy:
                wires[pname] = list(fairy[key])
        elif pname == "MotifMask":
            if key in jro:
                wires[pname] = list(jro[key])
            elif key in motif:
                wires[pname] = list(motif[key])
    return wires


def build_theme_instances() -> list[dict]:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as tex_catalog
    from theme_instances import MASTER, THEME_INSTANCES

    try:
        import portfolio_alpha_paths as alphas
    except ImportError:
        alphas = None

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing master: {MASTER}")

    mat = unreal.load_asset(MASTER)
    master_wired = tex_catalog.apply_master_defaults(mat, MASTER_PATH, force=True)
    violations = tex_catalog.scan_master_texture_violations(mat)
    lib.save_package(mat)

    profile_names = sorted({spec.get("profile", "TP_Default") for spec in THEME_INSTANCES})
    profiles = lib.create_toon_profiles(profile_names)
    results: list[dict] = []

    for spec in THEME_INSTANCES:
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
        if alphas:
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
            "folder": folder,
            "textures": wired_textures,
            "status": "created_or_updated",
        })

    return results, master_wired, violations


def _run_in_ue() -> int:
    import unreal

    unreal.log("=== APPLY THEME INSTANCES (Baroque + Zen) ===")
    instances, master_wired, violations = build_theme_instances()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER_PATH,
        "master_wired": master_wired,
        "violations_after": violations,
        "theme_count": len(instances),
        "instances": instances,
        "texture_pack": "/Game/Textures/70_Japanese_Ornament_Alphas_vfxMed",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[ThemeInstances] {len(instances)} themes -> {REPORT}")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    print(f"THEME_INSTANCES_OK count={len(instances)} clean={not violations.get('banned') and not violations.get('unwired')}")
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: UE not found at {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / "theme_instances.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/apply_theme_instances.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
