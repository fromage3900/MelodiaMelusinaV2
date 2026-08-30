"""Materialize SeaAbove Reef textures into ShadowDream MIs (Universal, soft blue/pink).

Today's batch: ~50 textures under /Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures
  T_SeaAbove_*, T_Jelly_*, T_Leviathan_*, T_Organ_*, T_DressShorewake_*
Creates MIs at /Game/EnvSandbox/Materials/Instances/SeaAbove/Reef/
Parent: /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal
ShadowDream: Strength 0.7, Tint soft blue #8AA0D6, Flower soft pink #E8A0BF

Run in editor (Monolith): materialize_seaabove_reef_shadowdream.main()
Writes: Saved/Audit/seaabove_reef_shadowdream_mis.json
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

TEX_ROOT = "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures"
MI_ROOT = "/Game/EnvSandbox/Materials/Instances/SeaAbove/Reef"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "seaabove_reef_shadowdream_mis.json"

MEL = unreal.MaterialEditingLibrary

# Soft palette — ShadowDream
SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)   # #8BA0D6
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)   # #E8A0BF
SHADOW_DREAM_STRENGTH = 0.70
SHADOW_FLOWER_STRENGTH = 0.45
SHADOW_FLOWER_SCALE = 1.0

ROUGHNESS_HINTS = {
    "albedo": 0.75, "basecolor": 0.75, "base_color": 0.75,
    "normal": 0.75, "roughness": 0.75, "opacity": 0.75,
    "emissive": 0.75, "mask": 0.75, "lut": 0.75,
    "wetrock": 0.35, "sand": 0.85, "coral": 0.65, "bone": 0.55,
    "jelly": 0.25, "irid": 0.30, "biolum": 0.20, "caustics": 0.35,
    "shell": 0.45, "kelp": 0.80, "foam": 0.90,
}

def roughness_for(name: str) -> float:
    n = name.lower()
    for k, v in ROUGHNESS_HINTS.items():
        if k in n:
            return v
    return 0.70

def ensure_mi(name: str, mi_dir: str):
    path = f"{mi_dir}/{name}"
    mi = unreal.load_asset(path)
    if mi is not None:
        return mi
    if not unreal.EditorAssetLibrary.does_directory_exist(mi_dir):
        unreal.EditorAssetLibrary.make_directory(mi_dir)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(name, mi_dir, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    parent = unreal.load_asset(PARENT)
    if parent is None:
        unreal.log_error(f"[SeaAbove] Parent not found: {PARENT}")
        return None
    mi.set_editor_property("parent", parent)
    return mi

def route(mi, tex_path: str, tex_name: str):
    parent = mi.get_editor_property("parent")
    tex_params = set(str(p) for p in (MEL.get_texture_parameter_names(parent) or []))
    scalar_params = set(str(p) for p in (MEL.get_scalar_parameter_names(parent) or []))
    vector_params = set(str(p) for p in (MEL.get_vector_parameter_names(parent) or []))
    tex = unreal.load_asset(tex_path)
    # Route albedo/basecolor textures to Albedo
    if tex is not None and "Albedo" in tex_params:
        # Only route basecolor/albedo/mask textures as albedo; LUTs and normals skip
        low = tex_name.lower()
        if any(k in low for k in ["basecolor", "base_color", "albedo", "mask", "atlas", "shimmer"]):
            MEL.set_material_instance_texture_parameter_value(mi, "Albedo", tex)
        elif "normal" in low and "Normal" in tex_params:
            MEL.set_material_instance_texture_parameter_value(mi, "Normal", tex)
    if "TextureWeight" in scalar_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    rough = roughness_for(tex_name)
    if "Roughness" in scalar_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", float(rough))
    # ShadowDream — soft blue / soft pink
    if "ShadowDreamStrength" in scalar_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "ShadowDreamStrength", float(SHADOW_DREAM_STRENGTH))
    if "ShadowDreamTint" in vector_params:
        MEL.set_material_instance_vector_parameter_value(mi, "ShadowDreamTint", SOFT_BLUE)
    if "ShadowFlowerColor" in vector_params:
        MEL.set_material_instance_vector_parameter_value(mi, "ShadowFlowerColor", SOFT_PINK)
    if "ShadowFlowerStrength" in scalar_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "ShadowFlowerStrength", float(SHADOW_FLOWER_STRENGTH))
    if "ShadowFlowerScale" in scalar_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "ShadowFlowerScale", float(SHADOW_FLOWER_SCALE))
    unreal.EditorAssetLibrary.save_loaded_asset(mi)

def main():
    results = []
    if not unreal.EditorAssetLibrary.does_directory_exist(TEX_ROOT):
        unreal.log_error(f"[SeaAbove] Tex root missing: {TEX_ROOT}")
        return results
    assets = unreal.EditorAssetLibrary.list_assets(TEX_ROOT, recursive=False)
    unreal.log(f"[SeaAbove] Found {len(assets)} textures at {TEX_ROOT}")
    for p in sorted(assets):
        name = p.rsplit("/", 1)[-1].split(".", 1)[0]
        mi_name = f"MI_{name.replace('T_','')}_ShadowDream"
        mi = ensure_mi(mi_name, MI_ROOT)
        if mi is None:
            results.append({"name": name, "mi": mi_name, "status": "failed_create"})
            continue
        route(mi, p, name)
        results.append({"name": name, "mi": f"{MI_ROOT}/{mi_name}", "status": "ok", "shadowdream": True})
        unreal.log(f"[SeaAbove] {name} -> {mi_name} (R={roughness_for(name):.2f}, SD blue/pink)")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"[SeaAbove] Wrote {OUT} ({len(results)} entries)")
    return results

if __name__ == "__main__":
    main()
