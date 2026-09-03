"""Consolidate the 1,017 flat-color per-prop MICs into shared instances.

The 2026-08-13 routing pass created one MIC per (prop x GLB material) with a
flat BaseTint from the GLB baseColorFactor. 1,017 of those collapse to only 37
distinct (name|color) groups - the rest are byte-identical clones.

This script:
  1. Reads Saved/Audit/per_prop_routing.json (flat_color rows) -> group key (name|color).
  2. Creates ONE shared MI per group at
     /Game/EnvSandbox/Materials/Instances/Environment/FlatColors/MI_Flat_<Name>[_<n>]
     with BaseTint = the group color and TextureWeight = 0 (flat tint path).
  3. Re-points every Environment mesh slot currently referencing a per-prop flat
     MIC to the shared MI (slot-name based, like assign_mesh_prop_materials).
  4. (delete pass, --delete) after all slots are re-pointed: deletes per-prop MICs
     that are now zero-referencer, using AssetRegistry referencer proof.

Run in the UE editor (Monolith run_python): consolidate_flat_materials.main()
Writes: Saved/Audit/flat_mi_consolidation.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ENV = "/Game/EnvSandbox/Meshes/Environment"
FLAT_DIR = "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors"
PARENT_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
ROOT = Path(__file__).resolve().parents[2]
ROUTING = ROOT / "Saved" / "Audit" / "per_prop_routing.json"
OUT = ROOT / "Saved" / "Audit" / "flat_mi_consolidation.json"

MEL = unreal.MaterialEditingLibrary


def color_key(c):
    return tuple(round(float(x), 5) for x in c)


def build_groups():
    data = json.loads(ROUTING.read_text(encoding="utf-8"))
    groups = {}
    for row in data["rows"]:
        if row["mode"] != "flat_color":
            continue
        name = row["path"].rsplit("/", 1)[-1]
        key = (name, color_key(row["color"]))
        groups.setdefault(key, []).append(row["path"])
    return groups


def group_display_name(key):
    name = key[0]
    stem = "".join(c if (c.isalnum() or c == "_") else "_" for c in name)
    return stem or "Default"


def ensure_shared_mi(group_key, color, index):
    base = group_display_name(group_key)
    mi_name = base if index == 0 else f"{base}_{index}"
    path = f"{FLAT_DIR}/MI_Flat_{mi_name}"
    mi = unreal.load_asset(path)
    if mi is None:
        if not unreal.EditorAssetLibrary.does_directory_exist(FLAT_DIR):
            unreal.EditorAssetLibrary.make_directory(FLAT_DIR)
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = tools.create_asset(f"MI_Flat_{mi_name}", FLAT_DIR, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        return None, path
    parent = unreal.load_asset(PARENT_PATH)
    if parent is None:
        raise RuntimeError("master missing: " + PARENT_PATH)
    mi.set_editor_property("parent", parent)
    MEL.set_material_instance_vector_parameter_value(
        mi, "BaseTint", unreal.LinearColor(color[0], color[1], color[2], 1.0))
    MEL.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.0)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi, path


def repoint_meshes(shared_by_old_path):
    """Re-point every Environment mesh slot from per-prop flat MIC -> shared MI."""
    rows = []
    repointed = 0
    for prop_dir in sorted(Path(str(ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment")).iterdir()):
        if not prop_dir.is_dir():
            continue
        sm_dir = prop_dir / "StaticMeshes"
        if not sm_dir.exists():
            continue
        prop = prop_dir.name
        for sm in sorted(sm_dir.glob("*.uasset")):
            game = f"{ENV}/{prop}/StaticMeshes/{sm.stem}"
            mesh = unreal.load_asset(game)
            if mesh is None or mesh.get_class().get_name() != "StaticMesh":
                continue
            changed = []
            for i, s in enumerate(mesh.static_materials or []):
                cur = str(s.material_interface.get_path_name()) if s.material_interface else None
                if cur is None:
                    continue
                target = shared_by_old_path.get(cur.split(".")[0])
                if target is None:
                    continue
                shared = unreal.load_asset(target)
                if shared is None:
                    continue
                mesh.set_material(i, shared)
                repointed += 1
                changed.append({"slot": i, "name": str(s.material_slot_name) if s.material_slot_name else "",
                                "from": cur, "to": target})
            if changed:
                unreal.EditorAssetLibrary.save_loaded_asset(mesh)
                rows.append({"prop": prop, "mesh": sm.stem, "changes": changed})
    return rows, repointed


def referencers(path):
    """AssetRegistry referencers for a package path (asset-name stripped)."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    pkg = path.split(".")[0]
    opts = unreal.AssetRegistryDependencyOptions()
    opts.set_editor_property("include_soft_package_references", True)
    opts.set_editor_property("include_hard_package_references", True)
    return [str(d.asset_name) for d in reg.get_referencers(pkg, opts)]


def delete_pass(all_old_paths):
    """Delete per-prop flat MICs that have zero referencers."""
    deleted = []
    kept = []
    for old in sorted(all_old_paths):
        refs = referencers(old)
        if refs:
            kept.append({"path": old, "referencers": refs})
            continue
        if unreal.EditorAssetLibrary.delete_asset(old):
            deleted.append(old)
    return deleted, kept


def main():
    mode = "--delete" in sys.argv[1:]
    groups = build_groups()
    print(f"[flat_consol] groups: {len(groups)}  rows: {sum(len(v) for v in groups.values())}")

    shared = {}           # old per-prop MIC path -> shared MI path
    shared_meta = {}      # shared MI path -> group key (name|color)
    all_old = []
    name_counts = {}
    for idx, (key, paths) in enumerate(sorted(groups.items())):
        name, color = key
        n = name_counts.get(name, 0)
        name_counts[name] = n + 1
        mi, mi_path = ensure_shared_mi(key, color, n)
        if mi is None:
            print(f"[flat_consol] create failed: {key}")
            continue
        # variant numbering for duplicate names
        shared_meta[mi_path] = key
        for p in paths:
            all_old.append(p.split(".")[0])
            shared[p.split(".")[0]] = mi_path
        print(f"[flat_consol] {mi_path} <- {len(paths)} copies")

    rows, repointed = repoint_meshes(shared)
    print(f"[flat_consol] repointed slots: {repointed}  meshes touched: {len(rows)}")

    deleted = []
    kept = []
    if mode:
        deleted, kept = delete_pass(all_old)
        print(f"[flat_consol] deleted: {len(deleted)}  kept (still referenced): {len(kept)}")

    payload = {
        "generated": "2026-08-14",
        "delete_run": mode,
        "summary": {"groups": len(groups), "old_mics": len(all_old),
                    "repointed_slots": repointed, "meshes_touched": len(rows),
                    "deleted": len(deleted), "kept_referenced": len(kept)},
        "shared_mis": {k: {"group": f"{v[0]}|{v[1]}"} for k, v in shared_meta.items()},
        "repoints": rows,
        "deleted": deleted,
        "kept_referenced": kept,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[flat_consol] WROTE {OUT}")
    return payload


if __name__ == "__main__":
    main()
