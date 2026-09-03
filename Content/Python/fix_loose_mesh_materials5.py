"""Fix the last mesh-referenced noise MIs (2026-08-14 round 5).

Cases:
  - Room16B_Floor_Tiles_Shadows slot 'Atlas_01_Trans_Mat' -> T_Atlas_01_Trans
  - /Game/Library mirror SM_Desk2 -> EnvSandbox MI_M_Desk_2
  - /Game/Library mirror SM_Wick -> EnvSandbox Zen MI_Zen_LanternWarm
  - /Game/Library mirror SM_Outside_Wall -> flat tint (no source anywhere)
  - /Game/EnvSandbox SM_Outside_Wall (own _Loose shell) -> flat tint
Run in the UE editor (Monolith run_python): fix_loose_mesh_materials5.main()
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
CC = "/Game/EnvSandbox/Textures/CrystalCrossroads"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "loose_mesh_material_fix5.json"

MEL = unreal.MaterialEditingLibrary

EXPLICIT = {
    ("Room16B_Floor_Tiles_Shadows", "Atlas_01_Trans_Mat"): ("tex", f"{CC}/T_Atlas_01_Trans"),
    ("Room16B_Floor_Tiles_Shadows", "Seam_Floor_Mat"): ("tex", f"{CC}/T_Seam_Floor_Albedo"),
    ("Room16B_Floor_Tiles_Shadows", "Atlas_01_Mat"): ("tex", f"{CC}/T_Atlas_01_Albedo"),
    ("SM_Desk2", "WorldGridMaterial"): ("mi", "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/Desk2/MI_M_Desk_2"),
    ("SM_Wick", "WorldGridMaterial"): ("mi", "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_LanternWarm"),
    ("SM_Outside_Wall", "WorldGridMaterial"): ("flat", None),
    ("SM_Desk_Drawer", "WorldGridMaterial"): ("mi", "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/DeskDrawer/MI_M_Desk_Drawer"),
    ("SM_Drawer_Box002", "WorldGridMaterial"): ("mi", "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/Drawer/MI_M_Drawer_Box002"),
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


def set_flat(mi):
    params = params_of(mi)
    if "BaseTint" in params:
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseTint", unreal.LinearColor(0.75, 0.73, 0.70, 1.0))
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)


def main():
    rows = []
    fixed = 0
    roots = ["/Game/EnvSandbox/Meshes/Environment",
             "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
             "/Game/Library/Migrated/MagiciansLibrary"]
    seen = set()
    for root in roots:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            if p in seen:
                continue
            seen.add(p)
            a = unreal.load_asset(p)
            if a is None or a.get_class().get_name() != "StaticMesh":
                continue
            stem = p.rsplit("/", 1)[-1].split(".", 1)[0]
            rec = {"mesh": p, "slots": []}
            changed = False
            for i, s in enumerate(a.static_materials or []):
                cur = s.material_interface
                cur_path = str(cur.get_path_name()) if cur else None
                if cur_path is None or "/_Loose/" not in cur_path:
                    continue
                slot_name = str(s.material_slot_name) if s.material_slot_name else ""
                route = EXPLICIT.get((stem, slot_name))
                if route is None:
                    rec["slots"].append({"index": i, "name": slot_name, "status": "no_route",
                                         "mat": cur_path})
                    continue
                kind, val = route
                if kind == "mi":
                    tmi = unreal.load_asset(val)
                    if tmi is None:
                        rec["slots"].append({"index": i, "name": slot_name, "status": "mi_missing"})
                        continue
                    a.set_material(i, tmi)
                    rec["slots"].append({"index": i, "name": slot_name, "status": "routed", "to": val})
                elif kind == "tex":
                    mi = unreal.load_asset(cur_path)
                    set_tex(mi, val)
                    rec["slots"].append({"index": i, "name": slot_name, "status": "routed", "to": val})
                else:
                    mi = unreal.load_asset(cur_path)
                    set_flat(mi)
                    rec["slots"].append({"index": i, "name": slot_name, "status": "flattened"})
                fixed += 1
                changed = True
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
    unreal.log(f"[loose_fix5] fixed={fixed} meshes={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
