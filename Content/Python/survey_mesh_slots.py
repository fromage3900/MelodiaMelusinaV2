"""Survey mesh material slot assignments: which mesh slot0 MI vs prop's actual pack.

For each StaticMesh under EnvSandbox/Meshes/Environment/<prop>/StaticMeshes/:
  - slot0 material (usually a pack MI like MI_Env_<Pack>)
  - number of slots
  - which slots point at the prop's own Materials/ (correct) vs a pack MI

Writes Saved/Audit/mesh_slot_survey.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
ENV_DIR = ROOT / "Content" / "EnvSandbox" / "Meshes" / "Environment"
OUT = ROOT / "Saved" / "Audit" / "mesh_slot_survey.json"


def main() -> int:
    rows = []
    props = sorted(p for p in ENV_DIR.iterdir() if p.is_dir() and (p / "StaticMeshes").exists())
    for prop_dir in props:
        prop = prop_dir.name
        for sm in sorted((prop_dir / "StaticMeshes").glob("*.uasset")):
            game = "/Game/EnvSandbox/Meshes/Environment/" + prop + "/StaticMeshes/" + sm.stem
            mesh = unreal.load_asset(game)
            if not mesh or not isinstance(mesh, unreal.StaticMesh):
                continue
            slots = []
            for i, s in enumerate(mesh.static_materials or []):
                mi = s.material_interface
                slots.append({
                    "index": i,
                    "name": str(s.material_slot_name) if s.material_slot_name else "",
                    "material": str(mi.get_path_name()) if mi else None,
                })
            rows.append({
                "prop": prop,
                "mesh": sm.stem,
                "slots": slots,
                "n_slots": len(slots),
                "has_prop_material": any(
                    (s["material"] or "").startswith(f"/Game/EnvSandbox/Meshes/Environment/{prop}/Materials/")
                    for s in slots
                ),
            })

    from collections import Counter
    multi = [r for r in rows if r["n_slots"] > 1]
    report = {
        "generated": "2026-08-13",
        "meshes": rows,
        "meshes_total": len(rows),
        "meshes_multi_slot": len(multi),
        "meshes_with_prop_material": sum(1 for r in rows if r["has_prop_material"]),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"meshes: {len(rows)} | multi-slot: {len(multi)} | with prop material: {report['meshes_with_prop_material']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
