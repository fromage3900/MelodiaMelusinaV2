"""Survey Magician's Library meshes (EnvSandbox + Library migrated copies)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved" / "Audit" / "magicians_survey.json"
LIB_ROOTS = [
    "/Game/EnvSandbox/Library/Migrated/MagiciansLibrary",
    "/Game/Library/Migrated/MagiciansLibrary",
]


def main() -> int:
    rows = []
    for root in LIB_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            if "/StaticMeshes/" in path or not path.rsplit("/", 1)[-1].startswith("SM_"):
                continue
            m = unreal.load_asset(path)
            if not m or not isinstance(m, unreal.StaticMesh):
                continue
            slots = []
            for i, s in enumerate(m.static_materials or []):
                mi = s.material_interface
                slots.append({"i": i, "name": str(s.material_slot_name), "mat": str(mi.get_path_name()) if mi else "NONE"})
            rows.append({"path": path, "slots": slots})

    from collections import Counter
    fallback = Counter()
    for r in rows:
        for s in r["slots"]:
            if "MI_Universal" in (s["mat"] or "") or "ImportedPacks/MI_Env" in (s["mat"] or ""):
                fallback[s["mat"].split(".")[0].rsplit("/", 1)[-1]] += 1

    report = {
        "generated": "2026-08-13",
        "meshes": rows,
        "mesh_count": len(rows),
        "fallback_slots": dict(fallback),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Magician meshes: {len(rows)}")
    print("fallback slot usage:", dict(fallback))
    return 0


if __name__ == "__main__":
    sys.exit(main())
