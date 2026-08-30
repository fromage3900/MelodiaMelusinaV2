"""Glitter polished — create/tune MIs from glitter masters with roughness spread + tileable textures.

Masters:
  - M_Glitter_Enhanced_Master (GlitterColor/Size, UVScale, Roughness)
  - M_Glitter_UltimateSparkling (SparkleColor/Intensity)
  - M_Glitter_WorldAligned (world-aligned tiling)
  - M_Glitter_VolumetricInk_Master

Sources: Atlantis PBR tilables at /Game/EnvSandbox/Textures/Atlantis (KB3D_ATL_*)
Dest: /Game/EnvSandbox/Materials/Instances/Glitter/Polished

Roughness spread: Stone 0.85, Brick 0.78, Beige 0.72, Blue stone 0.65, Marble 0.32, Gold 0.28, Ivy 0.92
Tile: UVScale 4/6/8 per variant

Run: materialize_glitter_polished.main(dry_run=False)
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "glitter_polished_2026-08-30.json"
MEL = unreal.MaterialEditingLibrary

MASTERS = {
    "enhanced": "/Game/EnvSandbox/Materials/Masters/M_Glitter_Enhanced_Master",
    "ultimate": "/Game/EnvSandbox/Materials/Masters/M_Glitter_UltimateSparkling",
    "world": "/Game/EnvSandbox/Materials/Masters/M_Glitter_WorldAligned",
    "ink": "/Game/EnvSandbox/Materials/Masters/M_Glitter_VolumetricInk_Master",
}
DEST = "/Game/EnvSandbox/Materials/Instances/Glitter/Polished"
TEX_ATL = "/Game/EnvSandbox/Textures/Atlantis"

# Soft palette
SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)

# Plan: (mi_suffix, master_key, tex_base, roughness, glitterSize/UVScale, sparkle)
PLAN = [
    # Enhanced — stone/brick tilables, roughness spread + tile
    ("Atlantis_BrickStoneCleanBlueA_Tile4_R065", "enhanced", "KB3D_ATL_BrickStoneCleanBlueA", 0.65, {"GlitterSize": 0.9, "UVScale": 4.0}),
    ("Atlantis_BrickStoneCleanBlueB_Tile6_R068", "enhanced", "KB3D_ATL_BrickStoneCleanBlueB", 0.68, {"GlitterSize": 1.1, "UVScale": 6.0}),
    ("Atlantis_BrickStoneCleanBlueC_Tile8_R070", "enhanced", "KB3D_ATL_BrickStoneCleanBlueC", 0.70, {"GlitterSize": 1.3, "UVScale": 8.0}),
    ("Atlantis_BrickStoneCleanBeigeA_Tile6_R072", "enhanced", "KB3D_ATL_BrickStoneCleanBeigeA", 0.72, {"GlitterSize": 1.0, "UVScale": 6.0}),
    ("Atlantis_BrickStoneCleanA_Tile4_R078", "enhanced", "KB3D_ATL_BrickStoneCleanA", 0.78, {"GlitterSize": 0.85, "UVScale": 4.0}),
    # Ultimate — high sparkle, blue/pink
    ("Halo_Ultimate_Blue_R032", "ultimate", "KB3D_ATL_StoneCleanTrimA", 0.32, {"SparkleIntensity": 3.5, "SparkleColor": SOFT_BLUE}),
    ("Pile_Ultimate_Pink_R028", "ultimate", "KB3D_ATL_GoldWornA", 0.28, {"SparkleIntensity": 4.5, "SparkleColor": SOFT_PINK}),
    ("Stage_Ultimate_BluePink_R035", "ultimate", "KB3D_ATL_BrickStoneCleanA", 0.35, {"SparkleIntensity": 2.8, "SparkleColor": SOFT_BLUE}),
    ("Crown_Ultimate_Gold_R028", "ultimate", "KB3D_ATL_GoldWornA", 0.28, {"SparkleIntensity": 5.0, "SparkleColor": SOFT_PINK}),
    ("Ember_Ultimate_Warm_R045", "ultimate", "KB3D_ATL_BrickStoneCleanBeigeA", 0.45, {"SparkleIntensity": 3.0, "SparkleColor": SOFT_PINK}),
    # WorldAligned — large arch, world UV
    ("Floor_WorldAligned_Tile2_R085", "world", "KB3D_ATL_StoneCleanTrimB", 0.85, {"UVScale": 2.0, "Tiling": 2.0}),
    ("Vault_WorldAligned_Tile4_R080", "world", "KB3D_ATL_BrickStoneCleanTrimB", 0.80, {"UVScale": 4.0, "Tiling": 4.0}),
    ("Buttress_WorldAligned_Tile6_R082", "world", "KB3D_ATL_StoneCleanTrimC", 0.82, {"UVScale": 6.0, "Tiling": 6.0}),
    ("Column_WorldAligned_Tile4_R078", "world", "KB3D_ATL_StoneCleanTrimD", 0.78, {"UVScale": 4.0, "Tiling": 4.0}),
    ("Ivy_WorldAligned_Tile8_R092", "world", "KB3D_ATL_BrickStoneCleanA", 0.92, {"UVScale": 8.0, "Tiling": 8.0}),
]

def ensure_mi(name: str, parent_path: str):
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
    parent = unreal.load_asset(parent_path)
    mi.set_editor_property("parent", parent)
    return mi

def apply_params(mi, tex_base: str, roughness: float, extras: dict):
    parent = mi.get_editor_property("parent")
    s_params = set(str(p) for p in (MEL.get_scalar_parameter_names(parent) or []))
    v_params = set(str(p) for p in (MEL.get_vector_parameter_names(parent) or []))
    t_params = set(str(p) for p in (MEL.get_texture_parameter_names(parent) or []))
    # Route PBR tilables
    for suffix, param in [("basecolor", "BaseColor"), ("normal", "Normal"), ("roughness", "RoughnessMap"), ("metallic", "MetallicMap"), ("height", "HeightMap"), ("orm", "ORM")]:
        tex_path = f"{TEX_ATL}/{tex_base}_{suffix}"
        tex = unreal.load_asset(tex_path)
        if tex is not None and param in t_params:
            MEL.set_material_instance_texture_parameter_value(mi, param, tex)
        elif tex is not None and "Albedo" in t_params and suffix == "basecolor":
            MEL.set_material_instance_texture_parameter_value(mi, "Albedo", tex)
    if "Roughness" in s_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", float(roughness))
    if "TextureWeight" in s_params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    for k, v in extras.items():
        if k in s_params and isinstance(v, (int, float)):
            MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
        elif k in v_params and isinstance(v, unreal.LinearColor):
            MEL.set_material_instance_vector_parameter_value(mi, k, v)
        elif k in s_params and isinstance(v, unreal.LinearColor):
            pass
    unreal.EditorAssetLibrary.save_loaded_asset(mi)

def main(dry_run: bool = False):
    results = []
    for suffix, master_key, tex_base, rough, extras in PLAN:
        name = f"MI_Glitter_{suffix}"
        parent = MASTERS[master_key]
        if unreal.load_asset(parent) is None:
            results.append({"mi": name, "status": "parent_missing", "parent": parent})
            continue
        if dry_run:
            results.append({"mi": f"{DEST}/{name}", "status": "dry", "parent": parent, "tex": tex_base, "rough": rough, "extras": str(extras)})
            continue
        mi = ensure_mi(name, parent)
        if mi is None:
            results.append({"mi": name, "status": "failed_create"})
            continue
        apply_params(mi, tex_base, rough, extras)
        results.append({"mi": f"{DEST}/{name}", "status": "ok", "parent": parent, "tex": tex_base, "rough": rough})
        unreal.log(f"[Glitter] {name} -> {parent} R={rough} {extras}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"[Glitter] Wrote {OUT} ({len(results)} entries, dry_run={dry_run})")
    return results
