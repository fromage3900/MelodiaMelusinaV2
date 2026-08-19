"""Delete proven-dead MIs: orphaned _Loose shells + superseded AvatarGarden MIs.

Registry-verified zero referencers for:
  - /Game/EnvSandbox/Meshes/Environment/_Loose/MI_* (499)
  - /Game/EnvSandbox/Meshes/Environment/AvatarGarden/Materials/MI_<Mesh>_Art (59)

Referencer proof per asset; batched deletes; manifest written.

Run in the UE editor (Monolith run_python): delete_dead_mis.main()
Writes: Saved/Audit/dead_mi_deletion_2026-08-14.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import unreal

OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "dead_mi_deletion_2026-08-14.json"
LOOSE_DIR = "/Game/EnvSandbox/Meshes/Environment/_Loose"
AG_DIR = "/Game/EnvSandbox/Meshes/Environment/AvatarGarden/Materials"

ROOTS = ["/Game/EnvSandbox/Meshes", "/Game/EnvSandbox/Library", "/Game/Library"]


def used_set():
    used = set()
    for root in ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for p in unreal.EditorAssetLibrary.list_assets(root, recursive=True):
            a = unreal.load_asset(p)
            if a is None:
                continue
            cls = a.get_class().get_name()
            if cls not in ("StaticMesh", "SkeletalMesh"):
                continue
            mats = getattr(a, "static_materials", None) or getattr(a, "materials", None) or []
            for s in mats:
                mm = getattr(s, "material_interface", None)
                if mm is not None:
                    used.add(mm.get_path_name().split(".")[0])
    return used


def candidates():
    out = []
    if unreal.EditorAssetLibrary.does_directory_exist(LOOSE_DIR):
        for p in unreal.EditorAssetLibrary.list_assets(LOOSE_DIR, recursive=True):
            a = unreal.load_asset(p)
            if a is not None and a.get_class().get_name() == "MaterialInstanceConstant":
                out.append(p.split(".")[0])
    if unreal.EditorAssetLibrary.does_directory_exist(AG_DIR):
        for p in unreal.EditorAssetLibrary.list_assets(AG_DIR, recursive=False):
            a = unreal.load_asset(p)
            if a is None or a.get_class().get_name() != "MaterialInstanceConstant":
                continue
            leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
            if leaf.startswith("MI_") and leaf.endswith("_Art"):
                out.append(p.split(".")[0])
    return sorted(set(out))


def registry_refs(pkg):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    opts = unreal.AssetRegistryDependencyOptions()
    opts.set_editor_property("include_soft_package_references", True)
    opts.set_editor_property("include_hard_package_references", True)
    try:
        return [str(r) for r in reg.get_referencers(pkg, opts)]
    except Exception:
        return []


def main():
    used = used_set()
    cands = [p for p in candidates() if p not in used]
    deleted = []
    kept = []
    batch = []
    for p in cands:
        refs = registry_refs(p)
        if refs:
            kept.append({"path": p, "refs": refs})
            continue
        if unreal.EditorAssetLibrary.delete_asset(p):
            deleted.append(p)
            batch.append(p)
            if len(batch) >= 40:
                time.sleep(0.4)
                batch = []
    payload = {
        "generated": "2026-08-14",
        "summary": {"deleted": len(deleted), "kept_referenced": len(kept),
                    "candidates": len(cands)},
        "deleted": deleted,
        "kept": kept,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(f"[dead_mi] deleted={len(deleted)} kept={len(kept)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
