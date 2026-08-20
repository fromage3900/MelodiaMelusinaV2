# -*- coding: utf-8 -*-
"""Cathedral kit — headless capability audit of reusable melodia_gn builders.

Usage (inside project root):
  blender 5.2 --factory-startup -b -P Tools/cathedral_gn_audit.py

Read-only: builds each registered GN node group once, evaluates it on a throwaway
object, records tri/vert/dimension/param surface, writes
Saved/Audit/cathedral_builder_capabilities.json. No project assets touched.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import bpy

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEPLOY = os.path.join(ROOT, "deploy")  # parent of the surreal_arch package
OUT = os.path.join(ROOT, "Saved", "Audit", "cathedral_builder_capabilities.json")

if DEPLOY not in sys.path:
    sys.path.insert(0, DEPLOY)

TARGETS = [
    # nave structure
    "MEL_math_gothic_cathedral",
    "MEL_castle_wall_segment",
    "MEL_castle_gothic_window",
    "MEL_castle_buttress",
    "MEL_castle_curtain_wall",
    "MEL_castle_crenellation",
    "MEL_castle_tower",
    "MEL_castle_keep",
    "MEL_castle_gatehouse",
    "MEL_castle_spiral_stairs",
    "MEL_castle_assembler",
    "MEL_recursive_castle_spire",
    "MEL_endless_escher_bridge",
    "MEL_column",
    "MEL_baluster",
    "MEL_post",
    "MEL_rail",
    "MEL_star_finial",
    "MEL_arch",
    "MEL_gazebo",
    "MEL_portico",
    "MEL_greybox_room_kit",
    # musical notation
    "MEL_music_note_head",
    "MEL_music_treble_clef",
    "MEL_music_staff",
    "MEL_music_sheet_rail",
    "MEL_music_phrase",
    "MEL_harmonic_orb",
    # ornament
    "MEL_ornament_radial",
    "MEL_ornament_frame",
    "MEL_ornament_panel",
    "MEL_decorative_rosette",
    "MEL_filigree_spiral",
    # hero centerpiece
    "MEL_sky_observatory",
    # array / compose primitives
    "MEL_linear_array",
    "MEL_grid_array",
    "MEL_radial_array",
    "MEL_circular_array",
    "MEL_instance_on_spline",
]


def log(msg: str) -> None:
    print(f"[cathedral-audit] {msg}", flush=True)


def input_surface(tree) -> list[dict]:
    out = []
    for item in tree.interface.items_tree:
        if item.item_type != "SOCKET" or item.in_out != "INPUT":
            continue
        rec = {"name": item.name}
        try:
            dv = getattr(item, "default_value", None)
            if hasattr(dv, "to_list"):
                dv = list(dv.to_list())
            elif hasattr(dv, "__iter__") and not isinstance(dv, (str, bytes)):
                dv = list(dv)
            rec["default"] = dv
        except Exception:
            pass
        out.append(rec)
    return out


def evaluate_one(name: str, builder, tree) -> dict:
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.modifiers.clear()
    mod = obj.modifiers.new("MelodiaGN", "NODES")
    mod.node_group = tree
    result = {"name": name, "built": True, "params": input_surface(tree)}
    try:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        mesh = ev.to_mesh()
        verts = len(mesh.vertices)
        polys = len(mesh.polygons)
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        result["verts"] = verts
        result["tris"] = polys
        result["dims"] = (
            round(max(xs) - min(xs), 3) if xs else 0.0,
            round(max(ys) - min(ys), 3) if ys else 0.0,
            round(max(zs) - min(zs), 3) if zs else 0.0,
        )
        ev.to_mesh_clear()
    except Exception as exc:
        result["eval_error"] = str(exc)
    bpy.data.objects.remove(obj, do_unlink=True)
    return result


def main() -> int:
    from surreal_arch import melodia_gn  # package import; registers every builder
    from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA

    log(f"registry has {len(GROUP_BUILDERS)} builders")
    results = []
    for name in TARGETS:
        if name not in GROUP_BUILDERS:
            results.append({"name": name, "built": False, "reason": "not_registered"})
            log(f"MISSING {name}")
            continue
        builder = GROUP_BUILDERS[name]
        try:
            tree = builder(name) if name not in bpy.data.node_groups else bpy.data.node_groups[name]
        except Exception as exc:
            results.append({"name": name, "built": False, "reason": f"build_error: {exc}"})
            log(f"FAIL build {name}: {exc}")
            continue
        rec = evaluate_one(name, builder, tree)
        meta = GROUP_METADATA.get(name, {})
        rec["label"] = meta.get("label", "")
        rec["category"] = meta.get("category", "")
        results.append(rec)
        log(f"OK {name} verts={rec.get('verts')} tris={rec.get('tris')} dims={rec.get('dims')}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checked": len(TARGETS),
        "built": sum(1 for r in results if r.get("built")),
        "eval_ok": sum(1 for r in results if r.get("tris", 0) > 0),
        "zero_face": [r["name"] for r in results if r.get("tris") == 0],
        "results": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")
    log(f"written {OUT}")
    return 0 if summary["eval_ok"] == len(TARGETS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
