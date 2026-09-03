"""Convert Cathedral + Atlantis architecture meshes to Toon Universal pipeline.

Replaces imported KB3D_ATL_* / legacy material slots with instances of
  /Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal
using soft ShadowDream palette (blue #8AA0D6 / pink #E8A0BF) where appropriate,
and sensible roughness/metallic per slot type (stone 0.85, brick 0.80, gold 0.35 metallic).

Targets:
  /Game/EnvSandbox/Meshes/Cathedral/*  (92 meshes)
  /Game/EnvSandbox/Meshes/Atlantis/*  (~200+ meshes)

Creates per-slot MIs at:
  /Game/EnvSandbox/Materials/Instances/Architecture/Cathedral/
  /Game/EnvSandbox/Materials/Instances/Architecture/Atlantis/

Then reassigns mesh material slots via StaticMesh.set_material().

Run in editor (Monolith): convert_arch_to_toon.main(dry_run=True) first, then dry_run=False
Writes: Saved/Audit/arch_toon_conversion.json
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MI_ROOT_CATH = "/Game/EnvSandbox/Materials/Instances/Architecture/Cathedral"
MI_ROOT_ATL = "/Game/EnvSandbox/Materials/Instances/Architecture/Atlantis"
MESH_ROOTS = ["/Game/EnvSandbox/Meshes/Cathedral", "/Game/EnvSandbox/Meshes/Atlantis"]
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "arch_toon_conversion.json"

MEL = unreal.MaterialEditingLibrary

SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)

# slot name -> (roughness, metallic, tint_override)
SLOT_PRESETS = {
    "stone":   (0.85, 0.0, None),
    "brick":   (0.80, 0.0, None),
    "trim":    (0.70, 0.0, None),
    "gold":    (0.35, 0.85, None),
    "worn":    (0.60, 0.15, None),
    "marble":  (0.25, 0.0, SOFT_BLUE),
    "glass":   (0.08, 0.0, SOFT_BLUE),
    "rose":    (0.55, 0.0, SOFT_PINK),
    "default": (0.70, 0.0, None),
}

def preset_for(slot: str):
    s = slot.lower()
    for k, v in SLOT_PRESETS.items():
        if k in s:
            return v
    return SLOT_PRESETS["default"]

def ensure_mi(slot_name: str, mi_dir: str):
    mi_name = f"MI_Arch_{slot_name}"
    path = f"{mi_dir}/{mi_name}"
    mi = unreal.load_asset(path)
    if mi is not None:
        return mi, path
    if not unreal.EditorAssetLibrary.does_directory_exist(mi_dir):
        unreal.EditorAssetLibrary.make_directory(mi_dir)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(mi_name, mi_dir, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None, path
    parent = unreal.load_asset(PARENT)
    mi.set_editor_property("parent", parent)
    rough, metal, tint = preset_for(slot_name)
    parent_obj = mi.get_editor_property("parent")
    scalars = set(str(p) for p in (MEL.get_scalar_parameter_names(parent_obj) or []))
    vectors = set(str(p) for p in (MEL.get_vector_parameter_names(parent_obj) or []))
    if "Roughness" in scalars:
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", float(rough))
    if "Metallic" in scalars:
        MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", float(metal))
    if "TextureWeight" in scalars:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.85)
    if "ShadowDreamStrength" in scalars:
        MEL.set_material_instance_scalar_parameter_value(mi, "ShadowDreamStrength", 0.55)
    if "ShadowDreamTint" in vectors:
        MEL.set_material_instance_vector_parameter_value(mi, "ShadowDreamTint", tint if tint is not None else SOFT_BLUE)
    if "ShadowFlowerColor" in vectors:
        MEL.set_material_instance_vector_parameter_value(mi, "ShadowFlowerColor", SOFT_PINK)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi, path

def convert_mesh(mesh_path: str, mi_dir: str, dry_run: bool):
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        return {"mesh": mesh_path, "status": "not_found"}
    mats = mesh.get_editor_property("static_materials") or []
    changes = []
    for idx, sm in enumerate(mats):
        slot = str(sm.get_editor_property("material_slot_name") or f"Slot{idx}")
        imported = str(sm.get_editor_property("imported_material_slot_name") or slot)
        key = imported or slot
        # skip if already toon
        cur = sm.get_editor_property("material_interface")
        cur_path = cur.get_path_name() if cur else ""
        if "M_Master_Toon_Universal" in cur_path or "MI_Arch_" in cur_path:
            changes.append({"slot": slot, "action": "already_toon", "path": cur_path})
            continue
        mi, mi_path = ensure_mi(key.replace(" ", "_").replace(".", "_"), mi_dir)
        if mi is None:
            changes.append({"slot": slot, "action": "mi_failed", "key": key})
            continue
        if not dry_run:
            mesh.set_material(idx, mi)
        changes.append({"slot": slot, "key": key, "action": "dry" if dry_run else "assigned", "mi": mi_path})
    if not dry_run and changes:
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return {"mesh": mesh_path, "status": "ok", "changes": changes}

def main(dry_run: bool = True):
    results = []
    all_meshes = []
    for root in MESH_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            unreal.log_warning(f"[ArchToon] Missing root: {root}")
            continue
        all_meshes.extend(unreal.EditorAssetLibrary.list_assets(root, recursive=True))
    # filter to StaticMesh only (exclude materials/textures that may be under same root)
    mesh_paths = [p for p in all_meshes if p.startswith("/Game/EnvSandbox/Meshes/Cathedral") or p.startswith("/Game/EnvSandbox/Meshes/Atlantis")]
    unreal.log(f"[ArchToon] Found {len(mesh_paths)} meshes (dry_run={dry_run})")
    for mp in sorted(mesh_paths):
        mi_dir = MI_ROOT_CATH if "/Cathedral" in mp else MI_ROOT_ATL
        r = convert_mesh(mp, mi_dir, dry_run)
        results.append(r)
        if r["status"] == "ok" and r.get("changes"):
            unreal.log(f"[ArchToon] {mp} -> {len(r['changes'])} slots")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    unreal.log(f"[ArchToon] Wrote {OUT}")
    return results
