"""Route the correct pack texture set onto every Environment _Art mesh slot.

The 279 _Art static meshes (AvatarGarden / LunarYear / CrystalCrossroads packs)
were imported with per-mesh MIs (AvatarGarden/Materials/MI_<Mesh>_Art) that all
inherited the master's default noise textures. This script:

  1. Reads every _Art mesh's material slots (slot name -> current MI).
  2. Maps the slot name to the pack's real texture set (albedo/normal/metallic).
  3. Creates per-(mesh,slot) MIs when a mesh has multiple distinct atlases, and
     routes Albedo/NormalMap/MetallicMap + TextureWeight=1.0 (grounded against
     the master's live parameter list).
  4. Assigns the MI to the slot and saves.

Unmapped slots (no texture in any pack) are kept on the existing MI and logged.

Run in the UE editor (Monolith run_python): route_art_mesh_textures.main()
Writes: Saved/Audit/art_mesh_texture_routing.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
MI_DIR = f"{ENV}/AvatarGarden/Materials"
TEX_AG = "/Game/EnvSandbox/Textures/PackTextures/AvatarGarden"
TEX_LY = "/Game/EnvSandbox/Textures/PackTextures/LunarYear"
TEX_CC = "/Game/EnvSandbox/Textures/CrystalCrossroads"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "art_mesh_texture_routing.json"

MEL = unreal.MaterialEditingLibrary

# slot-name -> {"albedo": path_or_None, "normal": path_or_None, "metallic": path_or_None,
#               "roughness": float_or_None, "emissive": path_or_None}
# Names follow the imported texture assets verbatim (case-sensitive).


def _ag(name):
    return f"{TEX_AG}/{name}"


def _ly(name):
    return f"{TEX_LY}/{name}"


def _cc(name):
    return f"{TEX_CC}/{name}"


SLOT_MAP = {
    # ── AvatarGarden ──
    "Stand_Atlas": {"albedo": _ag("AvatarStand_Atlas_albedo"), "normal": _ag("AvatarStand_Atlas_normal"), "roughness": 0.75},
    "Bush": {"albedo": _ag("Bush_Atlas_01_albedo"), "normal": _ag("Bush_Atlas_01_normal"), "metallic": _ag("Bush_Atlas_01_metallic"), "roughness": 0.8},
    "Bush_Atlas_01": {"albedo": _ag("Bush_Atlas_01_albedo"), "normal": _ag("Bush_Atlas_01_normal"), "metallic": _ag("Bush_Atlas_01_metallic"), "roughness": 0.8},
    "GrassAtlas": {"albedo": _ag("GrassAtlas_albedo"), "normal": _ag("GrassAtlas_normal"), "metallic": _ag("GrassAtlas_metallic"), "roughness": 0.9},
    "Grass": {"albedo": _ag("GrassAtlas_albedo"), "normal": _ag("GrassAtlas_normal"), "metallic": _ag("GrassAtlas_metallic"), "roughness": 0.9},
    "SmallGrass_Mat": {"albedo": _ag("SmallGrass_albedo"), "roughness": 0.9},
    "GroundAtlas": {"albedo": _ag("GroundAtlas_albedo"), "normal": _ag("GroundAtlas_normal"), "metallic": _ag("GroundAtlas_metallic"), "roughness": 0.8},
    "Ground": {"albedo": _ag("Ground_albedo"), "normal": _ag("Ground_normal"), "metallic": _ag("Ground_metallic"), "roughness": 0.8},
    "GroundGrass": {"albedo": _ag("Ground_None_albedo"), "normal": _ag("Ground_normal"), "roughness": 0.85},
    "GroundRight": {"albedo": _ag("Ground_Right_albedo"), "roughness": 0.8},
    "Rock_Atlas": {"albedo": _ag("Rocks_Atlas_albedo"), "normal": _ag("Rocks_Atlas_normal"), "roughness": 0.6},
    "Stone": {"albedo": _ag("Stones_albedo"), "normal": _ag("Stones_normal"), "metallic": _ag("Stones_metallic"), "roughness": 0.6},
    "100AvatarsStone": {"albedo": _ag("100AvatarsStone_albedo"), "roughness": 0.65},
    "Avatar_Pedestals": {"albedo": _ag("Avatar_pedestals_albedo"), "normal": _ag("Avatar_pedestals_normal"), "roughness": 0.6},
    "Sand": {"albedo": _ag("Sand_albedo"), "normal": _ag("Sand_normal"), "metallic": _ag("Sand_metallic"), "roughness": 0.9},
    "Sand_Albedo": {"albedo": _ag("Sand_albedo"), "normal": _ag("Sand_normal"), "metallic": _ag("Sand_metallic"), "roughness": 0.9},
    "Trunk_Atlas": {"albedo": _ag("Trunk_Atlas_albedo"), "normal": _ag("Trunk_Atlas_normal"), "metallic": _ag("Trunk_Atlas_metallic"), "roughness": 0.85},
    "Wooden_Structures": {"albedo": _ag("Wooden_Structures_albedo"), "normal": _ag("Wooden_Structures_normal"), "metallic": _ag("Wooden_Structures_metallic"), "roughness": 0.75},
    "Wooden_Structures1": {"albedo": _ag("Wooden_Structures_albedo"), "normal": _ag("Wooden_Structures_normal"), "metallic": _ag("Wooden_Structures_metallic"), "roughness": 0.75},
    "Wooden_Structures2": {"albedo": _ag("Wooden_Structures_albedo"), "normal": _ag("Wooden_Structures_normal"), "metallic": _ag("Wooden_Structures_metallic"), "roughness": 0.75},
    "Wooden_Structures3": {"albedo": _ag("Wooden_Structures_albedo"), "normal": _ag("Wooden_Structures_normal"), "metallic": _ag("Wooden_Structures_metallic"), "roughness": 0.75},
    "Wood": {"albedo": _ag("Wooden_Structures_albedo"), "normal": _ag("Wooden_Structures_normal"), "roughness": 0.75},
    "Wood2": {"albedo": _ag("Wooden_Structures_albedo"), "normal": _ag("Wooden_Structures_normal"), "roughness": 0.75},
    "Leaves_Atlas_0": {"albedo": _ag("Leaves_Atlas_0_albedo"), "normal": _ag("Leaves_Atlas_0_normal"), "metallic": _ag("Leaves_Atlas_0_metallic"), "roughness": 0.8},
    "Leave_Atlas_0": {"albedo": _ag("Leaves_Atlas_0_albedo"), "normal": _ag("Leaves_Atlas_0_normal"), "roughness": 0.8},
    "Leaves_Atlas_02": {"albedo": _ag("Leaves_Atlas_02_albedo"), "normal": _ag("Leaves_Atlas_02_normal"), "metallic": _ag("Leaves_Atlas_02_metallic"), "roughness": 0.8},
    "Leaves_Atlas_03": {"albedo": _ag("Leaves_Atlas_03_albedo"), "normal": _ag("Leaves_Atlas_03_normal"), "metallic": _ag("Leaves_Atlas_03_metallic"), "roughness": 0.8},
    "Tree_Atlas_01": {"albedo": _ag("Tree_Artlas_01_albedo"), "normal": _ag("Tree_Artlas_01_normal"), "roughness": 0.85},
    "Tree_Atlas_02": {"albedo": _ag("Tree_Atlas_02_albedo"), "normal": _ag("Tree_Atlas_02_normal"), "metallic": _ag("Tree_Atlas_02_metallic"), "roughness": 0.85},
    "Tree_Atlas": {"albedo": _ag("Tree_Artlas_01_albedo"), "normal": _ag("Tree_Artlas_01_normal"), "roughness": 0.85},
    "PalmTree_Tree": {"albedo": _ag("Tree_Artlas_01_albedo"), "normal": _ag("Tree_Artlas_01_normal"), "roughness": 0.85},
    "Tree_Topper01": {"albedo": _ag("Tree_topper_1_albedo"), "normal": _ag("Tree_topper_1_normal"), "metallic": _ag("Tree_topper_1_metallic"), "roughness": 0.8},
    "Tree_Topper02": {"albedo": _ag("Tree_topper_2_albedo"), "normal": _ag("Tree_topper_2_normal"), "metallic": _ag("Tree_topper_2_metallic"), "roughness": 0.8},
    "Clouds_Atlas_01": {"albedo": _ag("Clouds_Atlas_albedo"), "roughness": 0.7},
    "ThatchRoof_01": {"albedo": _ag("ThatchRoof_albedo"), "roughness": 0.7},
    "ThatchRoof_02": {"albedo": _ag("ThatchRoof_albedo"), "roughness": 0.7},
    "ThatchRoof_03": {"albedo": _ag("ThatchRoof_albedo"), "roughness": 0.7},
    "Sunflare": {"albedo": _ag("Sunflare_albedo"), "roughness": 0.6, "emissive": None},
    "Stardust": {"albedo": _ag("Stardust_albedo"), "roughness": 0.5},
    "Galaxy": {"albedo": _ag("Galaxy_albedo"), "roughness": 0.4},
    "Water": {"albedo": _ag("Water_albedo"), "normal": _ag("Water_normal"), "metallic": _ag("Water_metallic"), "roughness": 0.25},
    "Foam": {"albedo": _ag("Foam_Albedo_Alpha"), "roughness": 0.3},
    "Poseidonia01": {"albedo": _ag("Poseidonia_01_albedo"), "roughness": 0.7},
    "Poseidonia02": {"albedo": _ag("Poseidonia_02_albedo"), "roughness": 0.7},
    "Portal01": {"albedo": _ag("Portal_albedo"), "roughness": 0.5},
    "Portal02": {"albedo": _ag("Portal_albedo"), "roughness": 0.5},
    "PortalThumbnail_Atlas": {"albedo": _ag("PortalThumbnail_albedo"), "roughness": 0.6},
    "Easel01": {"albedo": _ag("painting_easel_01_albedo"), "roughness": 0.7},
    "Paint_Easel_01": {"albedo": _ag("painting_easel_01_albedo"), "roughness": 0.7},
    "Paint_Easel_02": {"albedo": _ag("painting_easel_02_albedo"), "roughness": 0.7},
    "Paint_Easel_03": {"albedo": _ag("painting_easel_03_albedo"), "roughness": 0.7},
    "Palette": {"albedo": _ag("Palette_Albedo_Mat"), "roughness": 0.6},
    "Panel": {"albedo": _ag("Panel_Left_albedo"), "roughness": 0.7},
    "PlygonalMonolith": {"albedo": _ag("Polygona_Monolith_01_albedo"), "roughness": 0.6},
    "brush": {"albedo": _ag("Brush_albedo"), "roughness": 0.75},
    "Brush": {"albedo": _ag("Brush_albedo"), "roughness": 0.75},
    "Cylinder": {"albedo": _ag("StandCylinder_albedo"), "roughness": 0.7},
    "Beach01": {"albedo": _ag("Beach_albedo"), "roughness": 0.85},
    "SignWarning": {"albedo": _ag("Sign_Warning_albedo"), "roughness": 0.7},
    "WarningSignText": {"albedo": _ag("Sign_Warning_albedo"), "roughness": 0.7},
    "Text": {"albedo": _ag("Signs_Names_albedo"), "roughness": 0.7},
    "Text_signs": {"albedo": _ag("Signs_Names_albedo"), "roughness": 0.7},
    "Domo": {"albedo": _ag("Domo_albedo"), "metallic": _ag("Domo_metallic"), "roughness": 0.4},
    "Flower": {"albedo": _ag("Leaves_Atlas_03_albedo"), "roughness": 0.85},
    "Metal": {"albedo": _ag("Domo_metallic"), "roughness": 0.3},
    "Red_Button": {"albedo": _ag("100AvatarsStone_albedo"), "roughness": 0.5},
    # ── LunarYear ──
    "Trim01": {"albedo": _ly("Trim_01_Albedo"), "roughness": 0.55},
    "Trim02": {"albedo": _ly("Trim_02_Albedo"), "roughness": 0.55},
    "Trim03": {"albedo": _ly("Trim_03_Albedo"), "roughness": 0.55},
    "Trim04": {"albedo": _ly("Trim_04_Albedo"), "roughness": 0.55},
    "AlphaTrim01": {"albedo": _ly("Alpha_Trim_01_Albedo"), "roughness": 0.55},
    "LunarYearBricks": {"albedo": _ly("LunarYear_FloorBricks_2D_View"), "roughness": 0.7},
    "LunarYearFloorgrass": {"albedo": _ly("LunarYear_Floorgrass_2D_View"), "roughness": 0.9},
    "Wearables": {"albedo": _ly("Wearables_Permanent_Collections"), "roughness": 0.6},
    "DragonBody": {"albedo": _ly("Dragon_Body_Albedo"), "emissive": _ly("Dragon_Body_Emissive"), "roughness": 0.5},
    "DragonHead": {"albedo": _ly("Dragon_Head_Albedo"), "emissive": _ly("Dragon_Head_Emissive"), "roughness": 0.5},
    "LOWP_Dragon": {"albedo": _ly("LOWP_Dragon_Albedo"), "normal": _ly("LOWP_Dragon_Normal"), "metallic": _ly("LOWP_Dragon_Metallic"), "emissive": _ly("LOWP_Dragon_Emissive"), "roughness": 0.5},
    "Light": {"albedo": _ly("ligth_albedo"), "emissive": _ly("ligth_albedo"), "roughness": 0.4},
    "Collab": {"albedo": _ly("Collab_02"), "roughness": 0.7},
    "Poster": {"albedo": _ly("Poster_Albedo"), "roughness": 0.7},
    "Metafactory": {"albedo": _ly("Metafactory_Showcase_Albedo"), "roughness": 0.6},
    "fireworks": {"albedo": _ly("fireworks"), "emissive": _ly("fireworks_emisivo"), "roughness": 0.3},
    # ── CrystalCrossroads (Paradise rooms) ──
    "Atlas_01_Mat": {"albedo": _cc("T_Atlas_01_Albedo"), "roughness": 0.7},
    "Atlas_01_Trans_Mat": {"albedo": _cc("T_Atlas_01_Trans"), "roughness": 0.3},
    "Seam_Sand_Mat": {"albedo": _cc("T_Seam_Sand_Albedo"), "roughness": 0.85},
    "Seam_Floor_Mat": {"albedo": _cc("T_Seam_Floor_Albedo"), "roughness": 0.7},
    "Outliner_Mat": {"albedo": _cc("T_Seam_Shadows_01"), "roughness": 0.5},
    "Shadows_Mat": {"albedo": _cc("T_Seam_Shadows_01"), "roughness": 0.5},
}

# Slots with no pack texture: give a flat tint instead of the master's noise default.
FLAT_TINT = {
    "Atlas": (0.85, 0.82, 0.78),
    "PoapLetter": (0.80, 0.72, 0.55),
    "FX": (0.95, 0.95, 0.95),
    "BosonGreen": (0.32, 0.58, 0.36),
    "Dialogue_Bubble_Mat": (1.0, 1.0, 1.0),
    "Emisive": (1.0, 1.0, 1.0),
    "Emisive_Fruit": (0.85, 0.30, 0.30),
    "Sun": (0.95, 0.80, 0.30),
}

MASTER_PARAM_CACHE = {}


def _parent_params(mi):
    parent = mi.get_editor_property("parent")
    if parent is None:
        return set()
    key = parent.get_path_name()
    if key not in MASTER_PARAM_CACHE:
        names = set()
        for p in (MEL.get_scalar_parameter_names(parent) or []):
            names.add(str(p))
        for p in (MEL.get_vector_parameter_names(parent) or []):
            names.add(str(p))
        for p in (MEL.get_texture_parameter_names(parent) or []):
            names.add(str(p))
        MASTER_PARAM_CACHE[key] = names
    return MASTER_PARAM_CACHE[key]


def _sanitize(slot):
    out = "".join(c if (c.isalnum() or c == "_") else "_" for c in slot)
    return out


def _ensure_mi(path, parent):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(path.split("/")[-1], "/".join(path.split("/")[:-1]), unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    mi.set_editor_property("parent", parent)
    return mi


def _route(mi, spec, dry):
    params = _parent_params(mi)
    changed = []
    tex = spec.get("albedo")
    if tex:
        asset = unreal.load_asset(tex)
        if asset is not None and "Albedo" in params:
            if not dry:
                MEL.set_material_instance_texture_parameter_value(mi, "Albedo", asset)
            changed.append("Albedo")
    nrm = spec.get("normal")
    if nrm:
        asset = unreal.load_asset(nrm)
        if asset is not None and "NormalMap" in params:
            if not dry:
                MEL.set_material_instance_texture_parameter_value(mi, "NormalMap", asset)
            changed.append("NormalMap")
    met = spec.get("metallic")
    if met:
        asset = unreal.load_asset(met)
        if asset is not None and "MetallicMap" in params:
            if not dry:
                MEL.set_material_instance_texture_parameter_value(mi, "MetallicMap", asset)
            changed.append("MetallicMap")
    rough = spec.get("roughness")
    if rough is not None and "Roughness" in params:
        if not dry:
            MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", float(rough))
        changed.append("Roughness")
    if "TextureWeight" in params:
        if not dry:
            MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
        changed.append("TextureWeight")
    return changed


def main(dry: bool = False):
    survey = OUT.parent / "avatar_garden_slots_survey.json"
    rows = json.loads(survey.read_text(encoding="utf-8")) if survey.exists() else None
    results = []
    matched = unmatched = 0
    used_slots = set()
    if rows is None:
        meshes = [
            p for p in unreal.EditorAssetLibrary.list_assets(ENV, recursive=False)
            if p.endswith("_Art")
        ]
    else:
        meshes = [m["mesh"].split(".")[0] for m in rows["meshes"]]
    for path in meshes:
        mesh = unreal.load_asset(path)
        if mesh is None or mesh.get_class().get_name() != "StaticMesh":
            continue
        slots = list(mesh.static_materials)
        rec = {"mesh": path, "slots": []}
        per_slot_used = {}
        for i, s in enumerate(slots):
            slot_name = str(s.material_slot_name) if s.material_slot_name else ""
            spec = SLOT_MAP.get(slot_name)
            flat = FLAT_TINT.get(slot_name) if spec is None else None
            if spec is None and flat is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "unmapped"})
                unmatched += 1
                continue
            matched += 1
            used_slots.add(slot_name)
            stem = path.rsplit("/", 1)[-1]
            if len(slots) == 1:
                mi_path = f"{MI_DIR}/MI_{stem}"
            else:
                mi_path = f"{MI_DIR}/MI_{stem}_{_sanitize(slot_name)}"
            if dry:
                rec["slots"].append({"index": i, "name": slot_name, "status": "would_route" if spec else "would_flat",
                                     "target": mi_path})
                continue
            parent = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
            mi = _ensure_mi(mi_path, parent)
            if mi is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "mi_create_failed"})
                continue
            if spec is not None:
                changed = _route(mi, spec, dry=False)
            else:
                changed = ["BaseTint", "TextureWeight=0"]
                if "BaseTint" in _parent_params(mi):
                    MEL.set_material_instance_vector_parameter_value(
                        mi, "BaseTint", unreal.LinearColor(flat[0], flat[1], flat[2], 1.0))
                if "TextureWeight" in _parent_params(mi):
                    MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.0)
            unreal.EditorAssetLibrary.save_loaded_asset(mi)
            mesh.set_material(i, mi)
            rec["slots"].append({"index": i, "name": slot_name, "status": "routed" if spec else "flat",
                                 "target": mi_path, "params": changed})
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        results.append(rec)
    payload = {
        "generated": "2026-08-14",
        "dry": dry,
        "summary": {"meshes": len(results), "slots_matched": matched, "slots_unmatched": unmatched,
                    "used_slots": sorted(used_slots)},
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[art_route] matched={matched} unmatched={unmatched} meshes={len(results)} dry={dry}")
    return payload


if __name__ == "__main__":
    main(dry="--dry-run" in __import__("sys").argv)
