"""Final loose-mesh material sweep (Library props, colliders, helpers).

Remaining bad meshes: flat root meshes whose _Loose/MI_<stem> shells have
TextureWeight=1.0 but no Albedo (they render master-noise). Fix rules:
  1. Library props (SM_* / MeshBlend names): point at the Library's real
     MI_M_<Name> instance when one exists.
  2. Colliders / helper meshes (*collider, *_BS, Retopo*, Cube_BS, Group,
     __ignore_, weight*, wheel*): flat tint (BaseTint grey-white, TW=0) so they
     render clean instead of noise; they are collision/helper geometry.
  3. AnimeFoliage (anime_grass_blade, anime_tree_stylized): flat tint
     (the pack is unlit colored cards; no per-mesh colormap exists).

Run in the UE editor (Monolith run_python): fix_loose_mesh_materials2.main()
Writes: Saved/Audit/loose_mesh_material_fix2.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
LIB = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
FLAT_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "loose_mesh_material_fix2.json"

MEL = unreal.MaterialEditingLibrary

LIB_MI_CACHE = None


def lib_mi_for(stem: str):
    """Find MI_M_<stem> in the Magicians Library (cached scan)."""
    global LIB_MI_CACHE
    if LIB_MI_CACHE is None:
        LIB_MI_CACHE = {}
        if unreal.EditorAssetLibrary.does_directory_exist(LIB):
            for p in unreal.EditorAssetLibrary.list_assets(LIB, recursive=True):
                a = unreal.load_asset(p)
                if a is None or a.get_class().get_name() != "MaterialInstanceConstant":
                    continue
                leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
                LIB_MI_CACHE[leaf] = p
    for cand in (f"MI_M_{stem}", f"MI_M_{stem.replace('_', '')}", stem):
        if cand in LIB_MI_CACHE:
            return LIB_MI_CACHE[cand]
    # fuzzy: strip SM_ prefix
    if stem.startswith("SM_"):
        return LIB_MI_CACHE.get("MI_M_" + stem[3:])
    return None


def flat_mi(name: str):
    if not unreal.EditorAssetLibrary.does_directory_exist(FLAT_DIR):
        return None
    for p in unreal.EditorAssetLibrary.list_assets(FLAT_DIR, recursive=False):
        leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
        if leaf == f"MI_Flat_{name}":
            return p
    return None


def ensure_flat_tint(stem: str, color=(0.78, 0.78, 0.75)):
    """Create/refresh a flat-tint _Loose MI for a helper mesh."""
    path = f"{ENV}/_Loose/MI_{stem}"
    mi = unreal.load_asset(path)
    if mi is None:
        if not unreal.EditorAssetLibrary.does_directory_exist(f"{ENV}/_Loose"):
            unreal.EditorAssetLibrary.make_directory(f"{ENV}/_Loose")
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(f"MI_{stem}", f"{ENV}/_Loose",
                                unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None
    parent = unreal.load_asset(PARENT)
    mi.set_editor_property("parent", parent)
    params = set()
    for fn in (MEL.get_vector_parameter_names, MEL.get_scalar_parameter_names):
        try:
            for p in (fn(parent) or []):
                params.add(str(p))
        except Exception:
            pass
    if "BaseTint" in params:
        MEL.set_material_instance_vector_parameter_value(
            mi, "BaseTint", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return path


def is_helper(stem: str) -> bool:
    n = stem.lower()
    return ("collider" in n or n.endswith("_bs") or "retopo" in n
            or n in ("group", "group_1", "__ignore_", "body-mesh", "head-mesh")
            or n.startswith("weight") or n.startswith("wheel")
            or n.startswith("cable") or n.startswith("cube") or n.startswith("cylinder")
            or n.startswith("ram") or n.startswith("catapult") or n == "arm"
            or n.startswith("anime_"))


def main():
    rows = []
    fixed = 0
    for p in unreal.EditorAssetLibrary.list_assets(ENV, recursive=False):
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            continue
        stem = p.rsplit("/", 1)[-1].split(".", 1)[0]
        if not stem or stem.startswith("_") or "/_Loose/" in p:
            continue
        rec = {"mesh": p, "slots": []}
        changed = False
        for i, s in enumerate(a.static_materials or []):
            cur = s.material_interface
            cur_path = str(cur.get_path_name()) if cur else None
            if cur_path is None or "/_Loose/" not in cur_path:
                continue  # only loose shells
            # check current MI: has albedo? if already resolved skip
            mi_cur = cur
            alb = None
            try:
                alb = MEL.get_material_instance_texture_parameter_value(mi_cur, "Albedo")
            except Exception:
                pass
            if alb is not None and "sbs_-_" not in alb.get_path_name():
                rec["slots"].append({"index": i, "status": "already_textured"})
                continue
            target = None
            if stem.startswith("SM_"):
                target = lib_mi_for(stem)
            if target is None and is_helper(stem):
                target = ensure_flat_tint(stem)
            if target is None:
                # last resort: try library by slot name
                slot_name = str(s.material_slot_name) if s.material_slot_name else ""
                target = lib_mi_for(slot_name)
            if target is None:
                rec["slots"].append({"index": i, "name": str(s.material_slot_name) if s.material_slot_name else "",
                                     "status": "no_target", "mat": cur_path})
                continue
            tmi = unreal.load_asset(target)
            if tmi is None:
                rec["slots"].append({"index": i, "status": "load_failed", "target": target})
                continue
            a.set_material(i, tmi)
            changed = True
            fixed += 1
            rec["slots"].append({"index": i, "name": str(s.material_slot_name) if s.material_slot_name else "",
                                 "status": "routed", "from": cur_path, "to": target})
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
    unreal.log(f"[loose_fix2] fixed={fixed} meshes={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
