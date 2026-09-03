"""Create usable material instances for the two Kenney texture packs.

- RetroTexturesFantasy (117 albedo textures): one MI per texture at
  /Game/EnvSandbox/Materials/Instances/Environment/RetroTextures/
  with Albedo routed, TextureWeight=1.0, roughness by name type.
- PatternPackExtra (84 patterns): one MI per pattern at
  /Game/EnvSandbox/Materials/Instances/Environment/PatternsExtra/

Run in the UE editor (Monolith run_python): materialize_kenney_textures.main()
Writes: Saved/Audit/kenney_texture_mis.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

TEX_RTF = "/Game/EnvSandbox/Textures/PackTextures/RetroTexturesFantasy"
TEX_PPE = "/Game/EnvSandbox/Textures/PackTextures/PatternPackExtra"
MI_RTF = "/Game/EnvSandbox/Materials/Instances/Environment/RetroTextures"
MI_PPE = "/Game/EnvSandbox/Materials/Instances/Environment/PatternsExtra"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "kenney_texture_mis.json"

MEL = unreal.MaterialEditingLibrary

ROUGHNESS_HINTS = {
    "door_metal": 0.4, "metal": 0.4, "stone": 0.65, "brick": 0.8, "rock": 0.8,
    "wood": 0.72, "timber": 0.72, "floor_ground": 0.9, "dirt": 0.88, "grass": 0.9,
    "sand": 0.9, "water": 0.15, "roof": 0.65, "thatch": 0.8, "window": 0.2,
    "glass": 0.08, "pattern": 0.7, "wall": 0.7, "clay": 0.6, "tiles": 0.6,
}


def roughness_for(name: str) -> float | None:
    n = name.lower()
    for token, val in ROUGHNESS_HINTS.items():
        if token in n:
            return val
    return 0.7


def ensure_mi(name: str, mi_dir: str):
    path = f"{mi_dir}/{name}"
    mi = unreal.load_asset(path)
    if mi is None:
        if not unreal.EditorAssetLibrary.does_directory_exist(mi_dir):
            unreal.EditorAssetLibrary.make_directory(mi_dir)
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(name, mi_dir, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    parent = unreal.load_asset(PARENT)
    mi.set_editor_property("parent", parent)
    return mi


def route(mi, tex_path: str, rough: float | None):
    parent = mi.get_editor_property("parent")
    params = set()
    for p in (MEL.get_texture_parameter_names(parent) or []):
        params.add(str(p))
    for p in (MEL.get_scalar_parameter_names(parent) or []):
        params.add(str(p))
    tex = unreal.load_asset(tex_path)
    if tex is not None and "Albedo" in params:
        MEL.set_material_instance_texture_parameter_value(mi, "Albedo", tex)
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    if rough is not None and "Roughness" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", float(rough))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)


def main():
    results = []
    for tex_dir, mi_dir, pack in ((TEX_RTF, MI_RTF, "RetroTexturesFantasy"),
                                  (TEX_PPE, MI_PPE, "PatternPackExtra")):
        if not unreal.EditorAssetLibrary.does_directory_exist(tex_dir):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(tex_dir, recursive=False):
            name = p.rsplit("/", 1)[-1].split(".", 1)[0]
            mi = ensure_mi(f"MI_{name}", mi_dir)
            if mi is None:
                results.append({"name": name, "status": "failed"})
                continue
            route(mi, p, roughness_for(name))
            results.append({"name": name, "status": "ok", "pack": pack})
    payload = {
        "generated": "2026-08-14",
        "summary": {"created": len([r for r in results if r["status"] == "ok"]),
                    "failed": len([r for r in results if r["status"] == "failed"])},
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[tex_mis] {payload['summary']}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
