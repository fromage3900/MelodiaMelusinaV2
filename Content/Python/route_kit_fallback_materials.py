"""Route the 38 kit-folder fallback slots to proper instances (2026-08-14).

Cases (owner-approved):
  - OrnamentMusical (7): assign each slot its local M_Musical* MI by slot name.
  - Ornament (15): create MI_Ornament_GoldTrim (Universal parent, gold stylized)
    and assign all.
  - Celestial (6 on MI_Universal_IridescentShell) + MathStructures (2 on
    IridescentShell): create MI_Celestial_Space (deep-space tint, iridescence,
    sparkle, dream ramp) and assign.
  - WPTerrains (4 on MI_Universal_Default): assign shared MI_Flat_stone
    (flat tint - placeholder terrain, no source art).

Leaves intentional lookdev as-is: Celestial rock isles on SurrealRocks
MI_Material, Math Lissajous/Trefoil on Baroque MI_Baroque_GildedFiligree.

Run in the UE editor (Monolith run_python): route_kit_fallback_materials.main()
Writes: Saved/Audit/kit_fallback_routing.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
INST_DIR = "/Game/EnvSandbox/Materials/Instances/Environment"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "kit_fallback_routing.json"

MEL = unreal.MaterialEditingLibrary

MUSICAL_FOLDER = "/Game/EnvSandbox/Meshes/OrnamentMusical"
ORN_FOLDER = "/Game/EnvSandbox/Meshes/Ornament"
CEL_FOLDER = "/Game/EnvSandbox/Meshes/Celestial"
MATH_FOLDER = "/Game/EnvSandbox/Meshes/MathStructures"
WP_FOLDER = "/Game/EnvSandbox/Meshes/WPTerrains"

IRIDESCENT = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Universal_IridescentShell"
DEFAULT_MI = "/Game/EnvSandbox/Materials/Instances/Environment/MI_Universal_Default"


def params_of(mi):
    parent = mi.get_editor_property("parent")
    out = set()
    for fn in (MEL.get_texture_parameter_names, MEL.get_scalar_parameter_names,
               MEL.get_vector_parameter_names, MEL.get_static_switch_parameter_names):
        try:
            for p in (fn(parent) or []):
                out.add(str(p))
        except Exception:
            pass
    return out


def ensure_mi(name, specs):
    path = f"{INST_DIR}/{name}"
    mi = unreal.load_asset(path)
    if mi is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(name, INST_DIR, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    mi.set_editor_property("parent", unreal.load_asset(PARENT))
    params = params_of(mi)
    for pname, pval in specs.items():
        try:
            if pname in params:
                if isinstance(pval, tuple):
                    MEL.set_material_instance_vector_parameter_value(
                        mi, pname, unreal.LinearColor(pval[0], pval[1], pval[2], 1.0))
                else:
                    MEL.set_material_instance_scalar_parameter_value(mi, pname, float(pval))
        except Exception:
            pass
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return path


def assign_meshes(folder, mat_path_by_slot=None, mat_path=None, skip_other=True,
                  only_from=None):
    """Assign material to meshes in a folder. only_from: only touch slots whose
    current material path contains this marker. Returns rows."""
    rows = []
    if not unreal.EditorAssetLibrary.does_directory_exist(folder):
        return rows
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=True):
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            continue
        rec = {"mesh": p, "slots": []}
        changed = False
        for i, s in enumerate(a.static_materials or []):
            cur = s.material_interface
            cur_path = str(cur.get_path_name()) if cur else None
            slot_name = str(s.material_slot_name) if s.material_slot_name else ""
            if only_from is not None and (cur_path is None or only_from not in cur_path):
                continue
            target = None
            if mat_path_by_slot is not None:
                target = mat_path_by_slot.get(slot_name)
                if target is None and skip_other:
                    rec["slots"].append({"index": i, "name": slot_name, "status": "no_target",
                                         "mat": cur_path})
                    continue
            if target is None and mat_path is not None:
                target = mat_path
            if target is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "no_target",
                                     "mat": cur_path})
                continue
            tmi = unreal.load_asset(target)
            if tmi is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "load_failed"})
                continue
            if cur_path and cur_path.split(".")[0] == target.split(".")[0]:
                rec["slots"].append({"index": i, "name": slot_name, "status": "same"})
                continue
            a.set_material(i, tmi)
            changed = True
            rec["slots"].append({"index": i, "name": slot_name, "status": "routed",
                                 "from": cur_path, "to": target})
        if changed:
            unreal.EditorAssetLibrary.save_loaded_asset(a)
            rows.append(rec)
    return rows


def main():
    rows = []

    # 1. OrnamentMusical: slot name -> local MI
    musical_mis = {}
    for p in unreal.EditorAssetLibrary.list_assets(MUSICAL_FOLDER, recursive=True):
        leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
        a = unreal.load_asset(p)
        if a is None:
            continue
        if a.get_class().get_name() == "MaterialInstanceConstant":
            musical_mis[leaf] = p
        elif a.get_class().get_name() == "Material":
            musical_mis[leaf] = p  # masters are fine as slot targets too
    rows += assign_meshes(MUSICAL_FOLDER, mat_path_by_slot=musical_mis, skip_other=False)

    # 2. Ornament -> gold trim instance
    gold = ensure_mi("MI_Ornament_GoldTrim", {
        "BaseTint": (0.92, 0.75, 0.42),
        "TextureWeight": 0.0,
        "Roughness": 0.35,
        "Metallic": 0.65,
        "RimIntensity": 0.25,
        "ShadowDreamStrength": 0.3,
        "RampStrength": 0.3,
        "GildingStrength": 0.8,
    })
    if gold:
        rows += assign_meshes(ORN_FOLDER, mat_path=gold)

    # 3. Celestial + Math on iridescent shell -> celestial space instance
    cel = ensure_mi("MI_Celestial_Space", {
        "BaseTint": (0.42, 0.38, 0.62),
        "TextureWeight": 0.0,
        "Roughness": 0.4,
        "Metallic": 0.0,
        "Iridescence": 0.8,
        "SparkleIntensity": 0.4,
        "CelestialStarIntensity": 0.5,
        "ShadowDreamStrength": 0.3,
        "RampStrength": 0.3,
    })
    if cel:
        for folder in (CEL_FOLDER, MATH_FOLDER):
            rows += assign_meshes(folder, mat_path=cel, only_from=IRIDESCENT)

    # 4. WPTerrains on MI_Universal_Default -> flat stone tint
    stone = "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors/MI_Flat_stone"
    if unreal.EditorAssetLibrary.does_asset_exist(stone):
        rows += assign_meshes(WP_FOLDER, mat_path=stone, only_from=DEFAULT_MI)

    payload = {
        "generated": "2026-08-14",
        "summary": {"rows": len(rows)},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[kit_route] meshes={len(rows)}")
    print(json.dumps({"meshes": len(rows)}))
    return payload


if __name__ == "__main__":
    main()
