"""Apply healthy PBR texture defaults to the landscape master and its instances.

Run inside the UE editor Python interpreter:

    import apply_healthy_landscape_defaults as ld
    ld.main()

Or from the content-browser exec field:

    py Content/Python/apply_healthy_landscape_defaults.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib
import portfolio_texture_catalog as tex_catalog


MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
INSTANCE_FOLDER = "/Game/EnvSandbox/Materials/Instances/Landscape"
TRIPLANAR_FOLDER = "/Game/EnvSandbox/Materials/Instances/Landscape/Triplanar"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "healthy_landscape_defaults.json"

LANDSCAPE_INSTANCES: list[dict] = [
    {"name": "MI_Landscape_CliffGrass", "scalars": {"TriplanarBlend": 1.0, "TriplanarSlopeStart": 0.3, "TriplanarSlopeEnd": 0.75}},
    {"name": "MI_Landscape_Meadow", "scalars": {"TriplanarBlend": 0.35, "TriplanarSlopeStart": 0.45, "TriplanarSlopeEnd": 0.82}},
    {"name": "MI_Landscape_SnowAlpine", "scalars": {"TriplanarBlend": 0.85, "TriplanarSlopeStart": 0.25, "TriplanarSlopeEnd": 0.68}},
    {"name": "MI_Landscape_SakuraGarden", "scalars": {"TriplanarBlend": 0.2, "TriplanarSlopeStart": 0.5, "TriplanarSlopeEnd": 0.85}},
    {"name": "MI_Landscape_ForestFloor", "scalars": {"TriplanarBlend": 0.55, "TriplanarSlopeStart": 0.38, "TriplanarSlopeEnd": 0.78}},
    {"name": "MI_Landscape_CoastalCliff", "scalars": {"TriplanarBlend": 0.9, "TriplanarSlopeStart": 0.22, "TriplanarSlopeEnd": 0.65}},
    {"name": "MI_Landscape_PondBank", "scalars": {"TriplanarBlend": 0.45, "TriplanarSlopeStart": 0.35, "TriplanarSlopeEnd": 0.72}},
    {"name": "MI_Landscape_DesertArid", "scalars": {"TriplanarBlend": 0.7, "TriplanarSlopeStart": 0.3, "TriplanarSlopeEnd": 0.7}},
    {"name": "MI_Landscape_VolcanicRock", "scalars": {"TriplanarBlend": 1.0, "TriplanarSlopeStart": 0.15, "TriplanarSlopeEnd": 0.55}},
    {"name": "MI_Landscape_UrbanCobble", "scalars": {"TriplanarBlend": 0.5, "TriplanarSlopeStart": 0.4, "TriplanarSlopeEnd": 0.8}},
    {"name": "MI_Landscape_WetlandMud", "scalars": {"TriplanarBlend": 0.4, "TriplanarSlopeStart": 0.35, "TriplanarSlopeEnd": 0.72}},
]

TRIPLANAR_INSTANCES: list[dict] = [
    {"name": "MI_Landscape_Triplanar_StoneWarm", "switches": {"bTriplanarPro_Active": True}, "scalars": {"TriplanarPro_BlendStrength": 1.0, "TriplanarPro_Tiling": 320.0, "TriplanarPro_SlopeStart": 0.3, "TriplanarPro_SlopeEnd": 0.75}},
    {"name": "MI_Landscape_Triplanar_DesertSand", "switches": {"bTriplanarPro_Active": True}, "scalars": {"TriplanarPro_BlendStrength": 0.85, "TriplanarPro_Tiling": 180.0, "TriplanarPro_SlopeStart": 0.28, "TriplanarPro_SlopeEnd": 0.68}},
    {"name": "MI_Landscape_Triplanar_SnowCrust", "switches": {"bTriplanarPro_Active": True}, "scalars": {"TriplanarPro_BlendStrength": 0.95, "TriplanarPro_Tiling": 400.0, "TriplanarPro_SlopeStart": 0.2, "TriplanarPro_SlopeEnd": 0.6}},
    {"name": "MI_Landscape_Triplanar_VolcanicAsh", "switches": {"bTriplanarPro_Active": True}, "scalars": {"TriplanarPro_BlendStrength": 1.0, "TriplanarPro_Tiling": 260.0, "TriplanarPro_SlopeStart": 0.12, "TriplanarPro_SlopeEnd": 0.55}},
]


def _apply_texture_defaults_to_master(master) -> dict[str, str]:
    """Set the master's texture parameter default objects to healthy PBR maps."""
    wired: dict[str, str] = {}
    for expr, owner in lib.iter_texture_parameter_expressions(master):
        pname = lib._param_name(expr)
        if not pname:
            continue
        candidates = tex_catalog.LANDSCAPE_TEXTURE_DEFAULTS.get(pname)
        if not candidates:
            continue
        path = lib.set_expression_texture(expr, candidates)
        if path:
            wired[pname] = path
            if owner and owner != master:
                owner.modify()
    master.modify()
    return wired


def _create_or_update_instance(spec: dict, folder: str, parent: str) -> dict:
    name = spec["name"]
    inst = lib.create_material_instance(name, folder, parent)

    for pname, rgba in spec.get("vectors", {}).items():
        lib.set_instance_vector(inst, pname, rgba)
    for pname, value in spec.get("scalars", {}).items():
        # Static switch parameters use 0/1 float values from instances
        lib.set_instance_scalar(inst, pname, float(value))
    for pname, value in spec.get("switches", {}).items():
        lib.set_instance_static_switch(inst, pname, bool(value))

    wired: dict[str, str] = {}
    for pname, candidates in tex_catalog.LANDSCAPE_TEXTURE_DEFAULTS.items():
        path = lib.set_instance_texture(inst, pname, candidates)
        if path:
            wired[pname] = path

    lib.save_package(inst)
    return {"instance": name, "folder": folder, "textures": wired, "status": "created_or_updated"}


def main() -> dict:
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        raise RuntimeError(f"Missing landscape master: {MASTER_PATH}")

    master = unreal.load_asset(MASTER_PATH)
    lib.ensure_directory(INSTANCE_FOLDER)
    lib.ensure_directory(TRIPLANAR_FOLDER)

    master_textures = _apply_texture_defaults_to_master(master)
    lib.save_package(master)

    results: list[dict] = []
    for spec in LANDSCAPE_INSTANCES:
        results.append(_create_or_update_instance(spec, INSTANCE_FOLDER, MASTER_PATH))
    for spec in TRIPLANAR_INSTANCES:
        results.append(_create_or_update_instance(spec, TRIPLANAR_FOLDER, MASTER_PATH))

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER_PATH,
        "master_texture_defaults": master_textures,
        "instances": results,
        "instance_count": len(results),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[HealthyLandscapeDefaults] wrote {REPORT}")
    return report


if __name__ == "__main__":
    main()
