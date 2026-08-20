"""Read-only inventory/preflight for the v22 Melusina Blender stage.

This script deliberately never saves the stage and never applies a remap. It
records the real armature modifier targets, vertex groups, shape-key counts,
and candidate wardrobe objects before the destructive-looking export lane is
allowed to run.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="Saved/Audit/melusina_v2_stage_preflight.json")
    parser.add_argument("--fast", action="store_true", help="Skip expensive dependency/shape-key probes while inventorying the stage")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])


def object_row(obj: bpy.types.Object, fast: bool = False) -> dict:
    modifiers = [m for m in obj.modifiers if m.type == "ARMATURE"]
    arm_targets = [m.object.name if m.object else None for m in modifiers]
    groups = [g.name for g in obj.vertex_groups]
    shape_keys = obj.data.shape_keys.key_blocks if not fast and obj.data and obj.data.shape_keys else []
    return {
        "name": obj.name,
        "collection_names": [c.name for c in obj.users_collection],
        "vertices": len(obj.data.vertices) if obj.data else 0,
        "armature_modifiers": len(modifiers),
        "armature_targets": arm_targets,
        "find_armature": None if fast else (obj.find_armature().name if obj.find_armature() else None),
        "vertex_group_count": len(groups),
        "vertex_group_sample": groups[:24],
        "shape_key_count": len(shape_keys),
    }


def main() -> int:
    ns = args()
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    rig = next((obj for obj in rigs if obj.name == "character_rig"), None)
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.data]
    candidate_meshes = [
        object_row(obj, ns.fast)
        for obj in meshes
        if any(token in obj.name.lower() for token in ("melusina", "wardrobe", "shirt", "skirt", "boot", "accessory"))
    ]
    collections = [
        {
            "name": coll.name,
            "object_count": len(coll.objects),
            "mesh_names": [obj.name for obj in coll.objects if obj.type == "MESH"][:100],
        }
        for coll in bpy.data.collections
        if any(token in coll.name.lower() for token in ("melusina", "wardrobe", "outfit", "v2"))
    ]
    bone_names = [bone.name for bone in rig.data.bones] if rig else []
    report = {
        "schema": "melodia.melusina_v2_stage_preflight.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": bpy.data.filepath,
        "read_only": True,
        "armatures": [obj.name for obj in rigs],
        "character_rig": {
            "found": bool(rig),
            "bone_count": len(bone_names),
            "bone_sample": bone_names[:48],
            "dotted_count": sum("." in name for name in bone_names),
        },
        "candidate_collections": collections,
        "candidate_mesh_count": len(candidate_meshes),
        "candidate_meshes": candidate_meshes,
        "ok": bool(rig) and bool(candidate_meshes),
        "promotion_allowed": False,
        "fast_mode": ns.fast,
        "note": "Inventory only. A separate bind/remap/export pass must prove the 465-bone contract.",
    }
    report_path = Path(ns.report)
    if not report_path.is_absolute():
        report_path = Path(__file__).resolve().parents[1] / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Report: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
