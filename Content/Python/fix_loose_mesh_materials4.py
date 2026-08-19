"""Fix the final 18 mesh-referenced noise-rendering MIs (2026-08-14 round 4).

Cases (verified by direct slot inspection):
  - Room16A_Floor_Tiles slot 'Seam_Floor_Mat' -> T_Seam_Floor_Albedo (CC)
  - Room16B_Floor_Tiles_Shadows slot 'Seam_Floor_Mat' -> T_Seam_Floor_Albedo
  - Room08A_Floor_Shadows slot 'Atlas_01_Trans_Mat' -> T_Atlas_01_Trans (CC)
  - Room16A_FLoor_Shadows slot 'Atlas_01_Trans_Mat' -> T_Atlas_01_Trans
  - Room16A_Floor_Tiles slot 'Atlas_01_Mat' already routed (Atlas_01_Mat MI)
  - __ignore_ slot 'Water' -> flat tint
  - Cable_BS / Cube_BS / Cylinder_BS (helper meshes elsewhere) -> flat tint
  - Palette01_Art / RiverFoam01_Art / WaterfallFoam01_Art -> flat tint
  - SM_Desk2 / SM_Wick / SM_Outside_Wall (mirror leftovers) -> EnvSandbox MI_M_*
  - Zen_LanternWarm / Baroque_GildedFiligree / Escher_ImpossibleTile:
    authored fractional TW (0.55 / TW=None) - intentional lookdev; leave as-is
    (only normalize TW None on Escher if the master requires it).

Run in the UE editor (Monolith run_python): fix_loose_mesh_materials4.main()
Writes: Saved/Audit/loose_mesh_material_fix4.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
CC = "/Game/EnvSandbox/Textures/CrystalCrossroads"
MIRROR = "/Game/Library/Migrated/MagiciansLibrary"
AUTH = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "loose_mesh_material_fix4.json"

MEL = unreal.MaterialEditingLibrary

# mesh stem -> {slot_name: tex_path or ('flat',)}
SLOT_TEX = {
    "Room16A_Floor_Tiles": {
        "Seam_Floor_Mat": f"{CC}/T_Seam_Floor_Albedo",
    },
    "Room16B_Floor_Tiles_Shadows": {
        "Seam_Floor_Mat": f"{CC}/T_Seam_Floor_Albedo",
    },
    "Room08A_Floor_Shadows": {
        "Atlas_01_Trans_Mat": f"{CC}/T_Atlas_01_Trans",
    },
    "Room16A_FLoor_Shadows": {
        "Atlas_01_Trans_Mat": f"{CC}/T_Atlas_01_Trans",
    },
    "Room08A_Floor_Sand": {
        "Seam_Sand_Mat": f"{CC}/T_Seam_Sand_Albedo",
    },
    "Room16B_Floor_Sand": {
        "Seam_Sand_Mat": f"{CC}/T_Seam_Sand_Albedo",
    },
}

AG = "/Game/EnvSandbox/Textures/PackTextures/AvatarGarden"

FLAT_STEMS = ("__ignore_",)

# AvatarGarden single-slot MIs with known pack textures
AG_SLOT_TEX = {
    "Palette01_Art": {"Palette": f"{AG}/Palette_Albedo_Mat"},
    "RiverFoam01_Art": {"Foam": f"{AG}/Foam_Albedo_Alpha"},
    "WaterfallFoam01_Art": {"Foam": f"{AG}/Foam_Albedo_Alpha"},
}


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


def set_tex(mi, tex_path):
    params = params_of(mi)
    t = unreal.load_asset(tex_path)
    if t is not None and "Albedo" in params:
        MEL.set_material_instance_texture_parameter_value(mi, "Albedo", t)
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return True


def set_flat(mi):
    params = params_of(mi)
    if "BaseTint" in params:
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseTint", unreal.LinearColor(0.82, 0.80, 0.78, 1.0))
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
        rec = {"mesh": p, "slots": []}
        changed = False
        for i, s in enumerate(a.static_materials or []):
            cur = s.material_interface
            cur_path = str(cur.get_path_name()) if cur else None
            if cur_path is None:
                continue
            is_loose = "/_Loose/" in cur_path
            is_ag = "/AvatarGarden/Materials/" in cur_path
            if not (is_loose or is_ag):
                continue
            slot_name = str(s.material_slot_name) if s.material_slot_name else ""
            alb = None
            try:
                alb = MEL.get_material_instance_texture_parameter_value(cur, "Albedo")
            except Exception:
                pass
            if alb is not None and "sbs_-_" not in alb.get_path_name():
                continue
            routes = SLOT_TEX.get(stem) or AG_SLOT_TEX.get(stem)
            tex_path = routes.get(slot_name) if routes else None
            if tex_path is None and stem in FLAT_STEMS:
                tex_path = "flat"
            if tex_path is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "no_route",
                                     "mat": cur_path})
                continue
            mi = unreal.load_asset(cur_path)
            if mi is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "load_failed"})
                continue
            ok = set_tex(mi, tex_path) if tex_path != "flat" else set_flat(mi)
            if ok:
                fixed += 1
                changed = True
                rec["slots"].append({"index": i, "name": slot_name, "status": "routed",
                                     "to": tex_path or "flat"})
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
    unreal.log(f"[loose_fix4] fixed={fixed} meshes={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
