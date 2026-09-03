"""Minimal direct-lookup probe for the v22 stage.

Avoids enumerating Blender's full datablock, which can block on the large WIP
scene.  It is read-only and never saves the source stage.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


def main() -> int:
    report_path = Path("Saved/Audit/melusina_v2_stage_direct_probe.json")
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]
        if "--report" in args:
            report_path = Path(args[args.index("--report") + 1])

    rig = bpy.data.objects.get("character_rig")
    body = bpy.data.objects.get("Melusina.001")
    if body is None:
        for name in ("Melusina", "Melusina_V2", "Melusina.002"):
            body = bpy.data.objects.get(name)
            if body is not None:
                break

    def mesh_row(obj):
        if obj is None or obj.type != "MESH":
            return None
        modifiers = [m for m in obj.modifiers if m.type == "ARMATURE"]
        return {
            "name": obj.name,
            "vertices": len(obj.data.vertices) if obj.data else 0,
            "armature_targets": [m.object.name if m.object else None for m in modifiers],
            "vertex_group_count": len(obj.vertex_groups),
            "vertex_group_sample": [g.name for g in obj.vertex_groups[:32]],
            "shape_key_count": len(obj.data.shape_keys.key_blocks) if obj.data and obj.data.shape_keys else 0,
            "collections": [c.name for c in obj.users_collection],
        }

    collection_rows = []
    for collection_name in (
        "Asset_melusina",
        "Wardrobe_Base",
        "Wardrobe_Accessories",
        "Review_Queue",
        "Wardrobe_V2",
    ):
        collection = bpy.data.collections.get(collection_name)
        if collection is None:
            continue
        meshes = [mesh_row(obj) for obj in collection.objects if obj.type == "MESH"]
        collection_rows.append({"name": collection_name, "mesh_count": len(meshes), "meshes": meshes})

    report = {
        "schema": "melodia.melusina_v2_stage_direct_probe.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": bpy.data.filepath,
        "read_only": True,
        "rig": {
            "found": rig is not None,
            "name": rig.name if rig else None,
            "bone_count": len(rig.data.bones) if rig else 0,
            "bone_sample": [b.name for b in rig.data.bones[:48]] if rig else [],
            "dotted_count": sum("." in b.name for b in rig.data.bones) if rig else 0,
        },
        "body": mesh_row(body),
        "collections": collection_rows,
        "promotion_allowed": False,
    }
    if not report_path.is_absolute():
        report_path = Path(__file__).resolve().parents[1] / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["rig"]["found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
