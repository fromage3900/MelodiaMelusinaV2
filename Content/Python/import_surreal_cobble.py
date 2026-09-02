# -*- coding: utf-8 -*-
"""Import the surreal cobble Copernicus PBR maps and build ShadowDream MIs live.

Runs in the Unreal Editor Python context (via Tools/ue_run_python.py).
Matches the materialize_glitter_polished.py contract: gate every param on the
parent's parameter names, batch-set, save per MI.

Target master: M_Master_Toon_Universal (toon spine). Cloth cutout would need
M_Master_Toon_Universal_Alpha, but the gilded cloth here is OPAQUE inlay, so
Universal is correct.

Run:
  python Tools/ue_run_python.py --file Content/Python/import_surreal_cobble.py
  python Tools/ue_run_python.py --file Content/Python/import_surreal_cobble.py --dry
"""
from __future__ import annotations
import sys, argparse
from pathlib import Path
import unreal

DRY = "--dry" in sys.argv

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "surreal_cobble_import_2026-08-30.json"
MEL = unreal.MaterialEditingLibrary

MAP_DIR = "/Game/EnvSandbox/Textures/SurrealCobble"
DEST = "/Game/EnvSandbox/Materials/Instances/Tilable/SurrealCobble"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

# Soft dream palette (per material orchestration plan)
SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)   # #8AA0D6
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)   # #E8A0BF

# Variants baked by copernicus_surreal_cobble.py
VARIANTS = ["AshenGilded", "MoonlitCobble", "EmberAsh"]

MAP_SUFFIXES = {
    "BaseColor": "BaseColor",
    "Normal": "Normal",
    "Roughness": "Roughness",
    "Metallic": "Metallic",
    "Height": "Height",
    "Iridescence": "Iridescence",
    "MovingPearlMask": "MovingPearlMask",
    "ORM": "ORM",
}

# Texture param name on M_Master_Toon_Universal for each map
TEX_PARAM = {
    "BaseColor": "BaseColor",
    "Normal": "Normal",
    "Roughness": "RoughnessMap",
    "Metallic": "MetallicMap",
    "Height": "HeightMap",
    "Iridescence": "IridescenceMap",
    "MovingPearlMask": "PearlMask",   # best-guess param; gated below
    "ORM": "ORM",
}


def ensure_tex(stem: str, suffix: str):
    p = f"{MAP_DIR}/T_SurrealCobble_{stem}_{suffix}"
    return unreal.load_asset(p)


def ensure_mi(name: str):
    path = f"{DEST}/{name}"
    mi = unreal.load_asset(path)
    if mi is not None:
        return mi
    if not unreal.EditorAssetLibrary.does_directory_exist(DEST):
        unreal.EditorAssetLibrary.make_directory(DEST)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    parent = unreal.load_asset(PARENT)
    mi.set_editor_property("parent", parent)
    return mi


def apply(mi, stem: str):
    parent = mi.get_editor_property("parent")
    s_params = set(str(p) for p in (MEL.get_scalar_parameter_names(parent) or []))
    v_params = set(str(p) for p in (MEL.get_vector_parameter_names(parent) or []))
    t_params = set(str(p) for p in (MEL.get_texture_parameter_names(parent) or []))

    for src, param in TEX_PARAM.items():
        if param not in t_params:
            continue
        tex = ensure_tex(stem, MAP_SUFFIXES[src])
        if tex is not None:
            MEL.set_material_instance_texture_parameter_value(mi, param, tex)

    # ShadowDream soft blue/pink (the signature dream grade)
    if "bShadowDream_Active" in s_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "bShadowDream_Active", 1.0)
    if "ShadowDreamStrength" in s_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "ShadowDreamStrength", 0.6)
    if "ShadowDreamTint" in v_params:
        MEL.set_material_instance_vector_parameter_value(mi, "ShadowDreamTint", SOFT_BLUE)
    if "ShadowFlowerColor" in v_params:
        MEL.set_material_instance_vector_parameter_value(mi, "ShadowFlowerColor", SOFT_PINK)
    if "BaseTint" in v_params:
        MEL.set_material_instance_vector_parameter_value(mi, "BaseTint", unreal.LinearColor(0.82, 0.80, 0.88, 1.0))

    unreal.EditorAssetLibrary.save_loaded_asset(mi)


def main():
    results = []
    if DRY:
        print("[SurrealCobble] DRY RUN")
    for stem in VARIANTS:
        name = f"MI_Tilable_SurrealCobble_{stem}_R060_Tile4"
        if DRY:
            present = {s: (ensure_tex(stem, MAP_SUFFIXES[s]) is not None) for s in MAP_SUFFIXES}
            results.append({"mi": f"{DEST}/{name}", "stem": stem, "textures_present": present})
            continue
        mi = ensure_mi(name)
        if mi is None:
            results.append({"mi": name, "status": "failed_create"})
            continue
        apply(mi, stem)
        results.append({"mi": f"{DEST}/{name}", "status": "ok", "stem": stem})
        unreal.log(f"[SurrealCobble] {name} -> {PARENT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(__import__("json").dumps(results, indent=2), encoding="utf-8")
    print(f"[SurrealCobble] wrote {OUT}")
    print(__import__("json").dumps(results, indent=2))


if __name__ == "__main__":
    main()
