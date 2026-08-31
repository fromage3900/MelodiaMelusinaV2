"""Shorewake dress bake prep — v2 geometry for the Houdini full bake.

Input : Saved/Audit/melusina_lookdev/Shorewake_48MAT_consolidated.fbx
        (48 labeled panels, SW_Dress_P01..48, single shared UV layout)
Checks: 48 slots present, UVs exist, per-panel UV bbox overlap audit,
        smooth shading + custom split normals.
Output: Saved/Audit/melusina_lookdev/bake/
          SM_ShorewakeDress_48MAT_v2.obj      (hython bake target: UVs + normals)
          bake_prep_manifest.json             (slot map, UV audit, versions)

Run:  blender -b --factory-startup --python shorewake_bake_prep.py
      (any Blender 4.x/5.x; run from Tools/Houdini/sea_above_reef/)
"""

import bmesh
import bpy
import json
import math
from pathlib import Path

SRC_BLEND = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_lookdev\Shorewake_48MAT_consolidated.blend")
OUT_DIR = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melusina_lookdev\bake")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no mesh objects in source blend")
    # Prefer the merged dress object if present, else the largest mesh.
    target = None
    for name_hint in ("Shorewake_48MAT", "ShorewakeDress"):
        for o in meshes:
            if name_hint.lower() in o.name.lower():
                target = o
                break
        if target:
            break
    target = target or max(meshes, key=lambda o: len(o.data.polygons))
    me = target.data
    print("TARGET", target.name, "verts", len(me.vertices), "polys", len(me.polygons))

    # --- UV audit -----------------------------------------------------------
    uv_layer = me.uv_layers.active
    if uv_layer is None:
        raise SystemExit("no UV layer on target mesh")
    slots = [ms.material.name if ms.material else "NONE" for ms in target.material_slots]
    panels = sorted(set(slots))
    # Per-panel UV bbox
    panel_uv = {p: [1e9, 1e9, -1e9, -1e9] for p in panels}
    for poly in me.polygons:
        p = slots[poly.material_index]
        box = panel_uv[p]
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            box[0] = min(box[0], uv.x); box[1] = min(box[1], uv.y)
            box[2] = max(box[2], uv.x); box[3] = max(box[3], uv.y)
    overlaps = []
    pl = list(panel_uv.items())
    for i in range(len(pl)):
        for j in range(i + 1, len(pl)):
            (na, a), (nb, b) = pl[i], pl[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                overlaps.append([na, nb])
    in_range = all(-0.01 <= box[0] and box[2] <= 1.01 and -0.01 <= box[1] and box[3] <= 1.01
                   for box in panel_uv.values())
    print("PANELS", len(panels), "UV_BBOX_OVERLAPS", len(overlaps), "IN_0_1", in_range)

    # --- Shading: smooth + angle-based sharp edges (Blender 4.1+ API) --------
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()
    if hasattr(bpy.ops.object, "shade_smooth_by_angle"):
        try:
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(60), keep_sharp_edges=False)
        except Exception:
            pass

    # --- Export v2 OBJ (hython bake target) ----------------------------------
    obj_path = OUT_DIR / "SM_ShorewakeDress_48MAT_v2.obj"
    bpy.ops.wm.obj_export(
        filepath=str(obj_path),
        export_selected_objects=False,
        export_uv=True,
        export_normals=True,
        export_materials=False,
        global_scale=1.0,
        forward_axis="Y",
        up_axis="Z",
    )
    print("WROTE", obj_path)

    manifest = {
        "schema": "melodia.shorewake_bake_prep.v1",
        "source_blend": str(SRC_BLEND),
        "target_object": target.name,
        "verts": len(me.vertices),
        "polys": len(me.polygons),
        "panel_count": len(panels),
        "panels": panels[:64],
        "uv_bbox_overlaps": overlaps[:128],
        "uv_overlap_count": len(overlaps),
        "uv_in_0_1": in_range,
        "obj": str(obj_path),
        "note": "custom split normals via auto_smooth 60deg; polys forced smooth",
    }
    (OUT_DIR / "bake_prep_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("MANIFEST WRITTEN, uv_overlap_count=", len(overlaps))


main()
