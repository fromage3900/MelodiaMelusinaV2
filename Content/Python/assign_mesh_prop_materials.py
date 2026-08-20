"""Assign the correct per-prop material to every mesh slot.

For each StaticMesh under EnvSandbox/Meshes/Environment/<prop>/StaticMeshes/:
  for each material slot with name <slotname>:
    if <prop>/Materials/<slotname>.uasset exists -> assign it (correct per-prop map/color)
    elif exactly one material in <prop>/Materials -> assign that
    else keep as-is (report).

This replaces the mass-assigned shared pack MIs (MI_Env_*) on mesh slots with the
prop's own materials, which now carry the correct GLB colormap / flat color.

Writes Saved/Audit/mesh_material_assign.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment"
OUT = ROOT / "Saved" / "Audit" / "mesh_material_assign.json"


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    rows = []
    assigned = skipped = missing = 0

    props = sorted(p for p in ENV_DIR.iterdir() if p.is_dir() and (p / "StaticMeshes").exists())
    for prop_dir in props:
        prop = prop_dir.name
        mats_dir = prop_dir / "Materials"
        prop_mats = {p.stem: p for p in mats_dir.glob("*.uasset")} if mats_dir.exists() else {}
        for sm in sorted((prop_dir / "StaticMeshes").glob("*.uasset")):
            game = "/Game/EnvSandbox/Meshes/Environment/" + prop + "/StaticMeshes/" + sm.stem
            mesh = unreal.load_asset(game)
            if not mesh or not isinstance(mesh, unreal.StaticMesh):
                continue
            changed = []
            static_mats = list(mesh.static_materials or [])
            for i, s in enumerate(static_mats):
                slot_name = str(s.material_slot_name) if s.material_slot_name else ""
                current = str(s.material_interface.get_path_name()) if s.material_interface else None
                # current already a prop material? skip
                if current and current.startswith(f"/Game/EnvSandbox/Meshes/Environment/{prop}/Materials/"):
                    continue
                target = prop_mats.get(slot_name) or (prop_mats.get(sm.stem) if len(prop_mats) == 1 else None)
                if target is None and len(prop_mats) == 1:
                    target = next(iter(prop_mats.values()))
                if target is None:
                    missing += 1
                    changed.append({"slot": i, "name": slot_name, "status": "no_prop_material"})
                    continue
                game_mat = "/Game/EnvSandbox/Meshes/Environment/" + prop + "/Materials/" + target.stem
                mat = unreal.load_asset(game_mat)
                if not mat:
                    missing += 1
                    changed.append({"slot": i, "name": slot_name, "status": "load_failed"})
                    continue
                if not dry:
                    mesh.set_material(i, mat)
                    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
                assigned += 1
                changed.append({"slot": i, "name": slot_name, "from": current, "to": game_mat, "status": "assigned"})
            if changed:
                rows.append({"prop": prop, "mesh": sm.stem, "changes": changed})

    report = {
        "generated": "2026-08-13",
        "dry_run": dry,
        "rows": rows,
        "summary": {"meshes_touched": len(rows), "slots_assigned": assigned, "slots_missing": missing, "slots_skipped": skipped},
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"meshes touched: {len(rows)} | slots assigned: {assigned} | missing: {missing}")
    return 0


if __name__ == "__main__":
    time.sleep(5)
    sys.exit(main())
