"""Final targeted fix for remaining loose meshes (67 MIs).

Covers the specific stems the generic sweeps couldn't route:
  - Room*_Floor_* (CrystalCrossroads): Seam_Sand_Mat/Seam_Floor_Mat/Atlas_01_Mat/
    Shadows_Mat slots -> T_Seam_Sand_Albedo / T_Seam_Floor_Albedo / T_Atlas_01_Albedo
    / T_Seam_Shadows_01 (CrystalCrossroads pack textures).
  - LeavePalmTree02_01 (AvatarGarden): Leaves_Atlas_03 -> Leaves_Atlas_03_albedo.
  - arrow / colormap slots with no sibling colormap: flat tint (no source).
  - Instruments (cello/violin/contrabass/Cable_BS/...) and helper meshes
    (__ignore_, Cube_BS, Cylinder_BS, weight*, wheel*, StylizedCrossProp_FBX):
    flat tint via MI_Flat_ wood/metal/glass defaults or a neutral tint.
  - AvatarGarden single-slot leftovers (Palette01_Art, RiverFoam01_Art,
    WaterfallFoam01_Art): flat tint (no source map exists for these slots).
  - Curated Zen/Baroque/Escher MIs (Zen_LanternWarm, Baroque_GildedFiligree,
    Escher_ImpossibleTile): leave as authored (fractional TW is intentional);
    only fix TW=None case -> 1.0.

Run in the UE editor (Monolith run_python): fix_loose_mesh_materials3.main()
Writes: Saved/Audit/loose_mesh_material_fix3.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
CC = "/Game/EnvSandbox/Textures/CrystalCrossroads"
AG = "/Game/EnvSandbox/Textures/PackTextures/AvatarGarden"
FLAT_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "loose_mesh_material_fix3.json"

MEL = unreal.MaterialEditingLibrary

# stem -> list of (slot_name, target_texture_path or flat-tint color or FLAT_MI name)
SLOT_ROUTES = {
    "Room08A_Floor_Sand": [("Seam_Sand_Mat", f"{CC}/T_Seam_Sand_Albedo")],
    "Room08A_Floor_Shadows": [("Shadows_Mat", f"{CC}/T_Seam_Shadows_01")],
    "Room16A_FLoor_Shadows": [("Shadows_Mat", f"{CC}/T_Seam_Shadows_01")],
    "Room16A_Floor_Tiles": [("Atlas_01_Mat", f"{CC}/T_Atlas_01_Albedo")],
    "Room16B_Floor_Sand": [("Seam_Sand_Mat", f"{CC}/T_Seam_Sand_Albedo")],
    "Room16B_Floor_Tiles_Shadows": [("Atlas_01_Mat", f"{CC}/T_Atlas_01_Albedo"),
                                    ("Shadows_Mat", f"{CC}/T_Seam_Shadows_01")],
    "LeavePalmTree02_01": [("Leaves_Atlas_03", f"{AG}/Leaves_Atlas_03_albedo")],
}

FLAT_HELPERS = (
    "__ignore_", "arrow", "cello", "contrabass", "violin", "Cable_BS",
    "Cube_BS", "Cylinder_BS", "StylizedCrossProp_FBX", "weight", "weight_1",
    "wheel_1", "wheel_2", "wheel_3", "wheel_4", "wheel_5",
    "Palette01_Art", "RiverFoam01_Art", "WaterfallFoam01_Art", "catapult",
    "catapult_1", "ram", "body-mesh", "head-mesh",
)


def params_of(mi):
    parent = mi.get_editor_property("parent")
    out = set()
    for fn in (MEL.get_texture_parameter_names, MEL.get_scalar_parameter_names,
               MEL.get_vector_parameter_names):
        try:
            for p in (fn(parent) or []):
                out.add(str(p))
        except Exception:
            pass
    return out


def route_texture(mi, tex_path):
    params = params_of(mi)
    t = unreal.load_asset(tex_path)
    if t is not None and "Albedo" in params:
        MEL.set_material_instance_texture_parameter_value(mi, "Albedo", t)
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return True


def route_flat(mi, name=None, color=None):
    params = params_of(mi)
    if color and "BaseTint" in params:
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseTint", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return True


def main():
    rows = []
    fixed = 0
    for p in unreal.EditorAssetLibrary.list_assets(ENV, recursive=False):
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            continue
        stem = p.rsplit("/", 1)[-1].split(".", 1)[0]
        if not stem or stem.startswith("_"):
            continue
        rec = {"mesh": p, "slots": []}
        changed = False
        routes = SLOT_ROUTES.get(stem)
        is_helper = stem in FLAT_HELPERS
        for i, s in enumerate(a.static_materials or []):
            cur = s.material_interface
            cur_path = str(cur.get_path_name()) if cur else None
            if cur_path is None or "/_Loose/" not in cur_path:
                continue
            slot_name = str(s.material_slot_name) if s.material_slot_name else ""
            # check current albedo state
            alb = None
            try:
                alb = MEL.get_material_instance_texture_parameter_value(cur, "Albedo")
            except Exception:
                pass
            if alb is not None and "sbs_-_" not in alb.get_path_name():
                rec["slots"].append({"index": i, "name": slot_name, "status": "already_textured"})
                continue
            target = None
            if routes:
                for slot_route, tex_path in routes:
                    if slot_route == slot_name or slot_name == "":
                        target = ("tex", tex_path)
                        break
            if target is None and is_helper:
                target = ("flat", None)
            if target is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "no_route",
                                     "mat": cur_path})
                continue
            mi = unreal.load_asset(cur_path)
            if mi is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "load_failed"})
                continue
            if target[0] == "tex":
                ok = route_texture(mi, target[1])
            else:
                ok = route_flat(mi)
            if ok:
                fixed += 1
                changed = True
                rec["slots"].append({"index": i, "name": slot_name, "status": "routed",
                                     "to": target[1] if target[0] == "tex" else "flat"})
        if changed:
            unreal.EditorAssetLibrary.save_loaded_asset(a)
            rows.append(rec)
    payload = {
        "generated": "2026-08-14",
        "summary": {"slots_fixed": fixed, "meshes_touched": len(rows)},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[loose_fix3] fixed={fixed} meshes={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
