"""Point /Game/Library mirror meshes at the EnvSandbox Library's real MIs.

The /Game/Library/Migrated/MagiciansLibrary/ tree is a mirror copy whose meshes
reference local _Loose/MI_SM_* shells (TextureWeight=1.0, no Albedo -> noise).
The authoritative materials live in the EnvSandbox copy
(/Game/EnvSandbox/Library/Migrated/MagiciansLibrary/<Prop>/MI_M_<Name>).

This script re-points every /Game/Library/Migrated/MagiciansLibrary mesh slot
from a _Loose/MI_SM_* shell to the matching EnvSandbox MI_M_<Name>.

Run in the UE editor (Monolith run_python): fix_library_mirror_materials.main()
Writes: Saved/Audit/library_mirror_material_fix.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

MIRROR = "/Game/Library/Migrated/MagiciansLibrary"
AUTH = "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary"
OUT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "library_mirror_material_fix.json"


def auth_mi_cache():
    cache = {}
    if unreal.EditorAssetLibrary.does_directory_exist(AUTH):
        for p in unreal.EditorAssetLibrary.list_assets(AUTH, recursive=True):
            a = unreal.load_asset(p)
            if a is None or a.get_class().get_name() != "MaterialInstanceConstant":
                continue
            leaf = p.rsplit("/", 1)[-1].split(".", 1)[0]
            cache[leaf] = p
    return cache


def main():
    cache = auth_mi_cache()
    rows = []
    fixed = 0
    for p in unreal.EditorAssetLibrary.list_assets(MIRROR, recursive=True):
        a = unreal.load_asset(p)
        if a is None or a.get_class().get_name() != "StaticMesh":
            continue
        changed = False
        rec = {"mesh": p, "slots": []}
        for i, s in enumerate(a.static_materials or []):
            cur = s.material_interface
            cur_path = str(cur.get_path_name()) if cur else None
            if cur_path is None or "/_Loose/" not in cur_path:
                continue
            # the mirror mesh's own name determines the MI_M_ target
            stem = p.rsplit("/", 1)[-1].split(".", 1)[0]
            target = None
            for cand in (f"MI_M_{stem}", f"MI_M_{stem.replace('_', '')}"):
                if cand in cache:
                    target = cache[cand]
                    break
            if target is None and stem.startswith("SM_"):
                target = cache.get("MI_M_" + stem[3:])
            if target is None:
                rec["slots"].append({"index": i, "name": str(s.material_slot_name) if s.material_slot_name else "",
                                     "status": "no_target", "mat": cur_path})
                continue
            tmi = unreal.load_asset(target)
            if tmi is None:
                rec["slots"].append({"index": i, "status": "load_failed"})
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
    unreal.log(f"[mirror_fix] fixed={fixed} meshes={len(rows)}")
    print(json.dumps(payload["summary"]))
    return payload


if __name__ == "__main__":
    main()
