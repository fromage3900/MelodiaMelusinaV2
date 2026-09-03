"""Route the GothicCastle PBR set onto the 41 Cathedral static meshes.

All 41 SM_Cathedral_* meshes share slot 'Material_0' and were mass-assigned
MI_Env_MedievalBuilder (KayKit albedo - wrong pack). This script creates two
dedicated Cathedral MIs (stone masonry + rock cliff) from the imported
GothicCastle stone_wall / rock_cliff PBR sets, then assigns by mesh-name
heuristic (cliff/rock pieces -> rock; everything else -> stone).

Run in the UE editor (Monolith run_python): route_cathedral_materials.main()
Writes: Saved/Audit/cathedral_routing.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

CAT = "/Game/EnvSandbox/Meshes/Cathedral"
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/Cathedral"
TEX = "/Game/EnvSandbox/Textures/PackTextures/GothicCastle"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "cathedral_routing.json"

MEL = unreal.MaterialEditingLibrary

ROCK_TOKENS = ("cliff", "rock", "boulder", "crag")


def _tex(name):
    return f"{TEX}/{name}"


STONE_SPEC = {
    "Albedo": _tex("Stone_Wall_vdbhdju_1K_BaseColor"),
    "NormalMap": _tex("Stone_Wall_vdbhdju_1K_Normal"),
    "MetallicMap": None,
    "Roughness": 0.85,
    "UVScale": 2.0,
}

ROCK_SPEC = {
    "Albedo": _tex("Rock_Cliff_uhrochkg_1K_BaseColor"),
    "NormalMap": _tex("Rock_Cliff_uhrochkg_1K_Normal"),
    "MetallicMap": None,
    "Roughness": 0.9,
    "UVScale": 1.5,
}


def ensure_mi(name):
    path = f"{MI_DIR}/{name}"
    mi = unreal.load_asset(path)
    if mi is None:
        if not unreal.EditorAssetLibrary.does_directory_exist(MI_DIR):
            unreal.EditorAssetLibrary.make_directory(MI_DIR)
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(name, MI_DIR, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    parent = unreal.load_asset(PARENT)
    mi.set_editor_property("parent", parent)
    return mi


def apply_spec(mi, spec):
    parent = mi.get_editor_property("parent")
    params = set()
    for p in (MEL.get_texture_parameter_names(parent) or []):
        params.add(str(p))
    for p in (MEL.get_scalar_parameter_names(parent) or []):
        params.add(str(p))
    for name, tex_path in (("Albedo", spec["Albedo"]), ("NormalMap", spec["NormalMap"])):
        if tex_path and name in params:
            t = unreal.load_asset(tex_path)
            if t is not None:
                MEL.set_material_instance_texture_parameter_value(mi, name, t)
    if "Roughness" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", spec["Roughness"])
    if "UVScale" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "UVScale", spec["UVScale"])
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)


def main():
    stone = ensure_mi("MI_Cathedral_Stone")
    rock = ensure_mi("MI_Cathedral_Rock")
    if stone is None or rock is None:
        raise RuntimeError("MI create failed")
    apply_spec(stone, STONE_SPEC)
    apply_spec(rock, ROCK_SPEC)

    l = unreal.EditorAssetLibrary.list_assets(CAT, recursive=True)
    rows = []
    stone_n = rock_n = 0
    for p in l:
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            continue
        name = p.rsplit("/", 1)[-1]
        target = rock if any(t in name.lower() for t in ROCK_TOKENS) else stone
        a.set_material(0, target)
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        rows.append({"mesh": p, "assigned": target.get_path_name()})
        if target == rock:
            rock_n += 1
        else:
            stone_n += 1
    payload = {
        "generated": "2026-08-14",
        "summary": {"meshes": len(rows), "stone": stone_n, "rock": rock_n,
                    "stone_mi": stone.get_path_name(), "rock_mi": rock.get_path_name()},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[cathedral] stone={stone_n} rock={rock_n} total={len(rows)}")
    return payload


if __name__ == "__main__":
    main()
