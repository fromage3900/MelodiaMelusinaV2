"""Fix flat root-level Environment meshes that render master-noise textures.

The 2026-08-13 routing pass fixed meshes under <prop>/StaticMeshes/ but the
flat root-level meshes (<stem>.uasset directly in Environment/) were missed.
Their slots point at _Loose/MI_<stem> shells with TextureWeight=1.0 but NO
Albedo override -> they render the master's default noise texture.

This script, per flat root mesh:
  1. Reads each material slot's name (colormap / leafsDark / woodBirch / ...).
  2. If the stem has a sibling Textures/colormap.uasset -> route the shared
     colormap MI path (per-prop <stem>/Materials/colormap if it exists, else
     create one) with Albedo=colormap + TextureWeight=1.0.
  3. Else (flat-color pack): map slot name -> shared FlatColors MI
     (MI_Flat_<name>) created by the consolidation pass; assign directly.
  4. Assigns the routed MI to the slot, saves.

Run in the UE editor (Monolith run_python): fix_loose_mesh_materials.main()
Writes: Saved/Audit/loose_mesh_material_fix.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
FLAT_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors"
PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "loose_mesh_material_fix.json"

MEL = unreal.MaterialEditingLibrary


def flat_mi(name: str):
    """Shared flat MI for a slot name, or None."""
    cands = []
    for p in unreal.EditorAssetLibrary.list_assets(FLAT_DIR, recursive=False):
        leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
        if leaf == f"MI_Flat_{name}":
            cands.append(p)
        elif leaf.startswith(f"MI_Flat_{name}_") or leaf.startswith(f"MI_Flat_{name} "):
            cands.append(p)
    if len(cands) == 1:
        return cands[0]
    if len(cands) > 1:
        return cands[0]  # first variant
    return None


def colormap_for_stem(stem: str):
    """Per-prop colormap MIC path if it exists."""
    p = f"{ENV}/{stem}/Materials/colormap"
    if unreal.EditorAssetLibrary.does_asset_exist(p):
        return p
    return None


def ensure_loose_colormap(stem: str):
    """Create _Loose/MI_<stem> colormap-routed MI if missing."""
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
    tex = unreal.load_asset(f"{ENV}/{stem}/Textures/colormap")
    params = set()
    for fn in (MEL.get_texture_parameter_names, MEL.get_scalar_parameter_names):
        try:
            for p in (fn(parent) or []):
                params.add(str(p))
        except Exception:
            pass
    if tex is not None and "Albedo" in params:
        MEL.set_material_instance_texture_parameter_value(mi, "Albedo", tex)
    if "TextureWeight" in params:
        MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 1.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return path


def main():
    rows = []
    fixed = skipped = 0
    for p in unreal.EditorAssetLibrary.list_assets(ENV, recursive=False):
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            continue
        stem = p.rsplit("/", 1)[-1].split(".", 1)[0]
        if not stem or stem.startswith("_"):
            continue
        has_colormap = unreal.EditorAssetLibrary.does_asset_exist(f"{ENV}/{stem}/Textures/colormap")
        rec = {"mesh": p, "slots": []}
        changed = False
        for i, s in enumerate(a.static_materials or []):
            slot_name = str(s.material_slot_name) if s.material_slot_name else ""
            cur = s.material_interface
            cur_path = str(cur.get_path_name()) if cur else None
            if cur_path and "/_Loose/MI_" in cur_path:
                pass  # candidate
            elif cur_path and "FlatColors" in cur_path:
                continue  # already consolidated
            elif cur_path and cur_path.split(".")[0] != f"{ENV}/{stem}/Materials/colormap":
                # leave non-loose non-flat alone unless colormap-shaped
                if not (cur_path.endswith("colormap") or "/Materials/" in cur_path):
                    rec["slots"].append({"index": i, "name": slot_name, "status": "left"})
                    continue
            target = None
            if has_colormap and slot_name in ("colormap", ""):
                target = ensure_loose_colormap(stem)
            elif has_colormap and cur_path and "colormap" in cur_path:
                target = ensure_loose_colormap(stem)
            else:
                target = flat_mi(slot_name)
            if target is None:
                rec["slots"].append({"index": i, "name": slot_name,
                                     "status": "no_target", "mat": cur_path})
                skipped += 1
                continue
            tmi = unreal.load_asset(target)
            if tmi is None:
                rec["slots"].append({"index": i, "name": slot_name, "status": "load_failed"})
                skipped += 1
                continue
            if cur_path and cur_path.split(".")[0] == target.split(".")[0]:
                rec["slots"].append({"index": i, "name": slot_name, "status": "same"})
                continue
            a.set_material(i, tmi)
            changed = True
            fixed += 1
            rec["slots"].append({"index": i, "name": slot_name, "status": "routed",
                                 "from": cur_path, "to": target})
        if changed:
            unreal.EditorAssetLibrary.save_loaded_asset(a)
            rows.append(rec)
    payload = {
        "generated": "2026-08-14",
        "summary": {"slots_fixed": fixed, "slots_skipped": skipped, "meshes_touched": len(rows)},
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[loose_fix] fixed={fixed} skipped={skipped} meshes={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
