#!/usr/bin/env python
"""Slotted bake-mesh export for the Shorewake dress.

Opens the verified 48-slot blend (Shorewake_48MAT_frozen_snapshot.blend),
audits per-slot UV bboxes, cross-checks UV compatibility against the
consolidated bake-source blend, then exports:

  bake/night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.obj  (48 usemtl)
  bake/night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.fbx  (48 slots)
  bake/night_pkg_2026-08-31/slotted_export_manifest.json
  bake/night_pkg_2026-08-31/face_uv_data.npz                        (ID rasterizer input)

Run: blender -b --factory-startup -noaudio --python shorewake_bake_slotted_export.py
"""
import bpy
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
LOOKDEV = PROJECT / "Saved" / "Audit" / "melusina_lookdev"
BAKE = LOOKDEV / "bake"
PKG = BAKE / "night_pkg_2026-08-31"
SRC_BLEND = LOOKDEV / "Shorewake_48MAT_frozen_snapshot.blend"
CONSOLIDATED = LOOKDEV / "Shorewake_48MAT_consolidated.blend"
TARGET = "SM_ShorewakeDress_48MAT"

PKG.mkdir(parents=True, exist_ok=True)


def audit(obj):
    slots = [ms.material.name if ms.material else "NONE" for ms in obj.material_slots]
    uv = obj.data.uv_layers[0]
    per = {}
    for poly in obj.data.polygons:
        name = slots[poly.material_index]
        rec = per.setdefault(name, {"polys": 0, "u": [1e9, -1e9], "v": [1e9, -1e9]})
        rec["polys"] += 1
        for li in poly.loop_indices:
            u, v = uv.data[li].uv
            rec["u"][0] = min(rec["u"][0], u); rec["u"][1] = max(rec["u"][1], u)
            rec["v"][0] = min(rec["v"][0], v); rec["v"][1] = max(rec["v"][1], v)
    return slots, per


# --- 1. audit consolidated (bake source) -------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(CONSOLIDATED))
cons_obj = bpy.data.objects[TARGET]
cons_slots, cons_per = audit(cons_obj)
cons_polys = len(cons_obj.data.polygons)

# --- 2. open frozen 48-slot blend, audit, export ------------------------------
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))
obj = bpy.data.objects[TARGET]
slots, per = audit(obj)
polys = len(obj.data.polygons)
verts = len(obj.data.vertices)

uv_overlap_count = 0
pairs = list(per.items())
for i in range(len(pairs)):
    for j in range(i + 1, len(pairs)):
        a, b = pairs[i][1], pairs[j][1]
        if (a["u"][0] < b["u"][1] and b["u"][0] < a["u"][1]
                and a["v"][0] < b["v"][1] and b["v"][0] < a["v"][1]):
            uv_overlap_count += 1

# UV compatibility vs consolidated on shared panel names
compat = []
for name in sorted(set(per) & set(cons_per)):
    a, b = per[name], cons_per[name]
    du = max(abs(a["u"][0] - b["u"][0]), abs(a["u"][1] - b["u"][1]))
    dv = max(abs(a["v"][0] - b["v"][0]), abs(a["v"][1] - b["v"][1]))
    compat.append({"panel": name, "du": round(du, 5), "dv": round(dv, 5),
                   "polys_48": a["polys"], "polys_cons": b["polys"]})
max_du = max(c["du"] for c in compat) if compat else None
max_dv = max(c["dv"] for c in compat) if compat else None

# --- 3. dump face/uv arrays for the numpy ID rasterizer -----------------------
import numpy as np
uv = obj.data.uv_layers[0]
loop_uv = np.empty(len(uv.data) * 2, dtype=np.float32)
uv.data.foreach_get("uv", loop_uv)
loop_uv = loop_uv.reshape(-1, 2)
loop_tot = np.empty(len(obj.data.polygons), dtype=np.int32)
obj.data.polygons.foreach_get("loop_total", loop_tot)
mat_idx = np.empty(len(obj.data.polygons), dtype=np.int32)
obj.data.polygons.foreach_get("material_index", mat_idx)
np.savez_compressed(PKG / "face_uv_data.npz",
                    loop_uv=loop_uv, loop_total=loop_tot,
                    material_index=mat_idx, slot_names=json.dumps(slots))

# --- 4. export OBJ (with materials) + FBX ------------------------------------
obj_base = str(PKG / "SM_ShorewakeDress_48MAT_v2_slotted")
bpy.ops.wm.obj_export(
    filepath=obj_base + ".obj",
    export_selected_objects=False, export_materials=True,
    export_material_groups=True, export_smooth_groups=True,
    export_uv=True, export_normals=True, export_colors=True,
    forward_axis="NEGATIVE_Y", up_axis="Z",
)
bpy.ops.export_scene.fbx(
    filepath=obj_base + ".fbx",
    use_selection=False, mesh_smooth_type="FACE",
    add_leaf_bones=False, bake_anim=False, path_mode="ABSOLUTE",
    axis_forward="-Y", axis_up="Z",
)

# --- 5. manifest ---------------------------------------------------------------
manifest = {
    "schema": "melodia.shorewake_slotted_export.v1",
    "source_blend": str(SRC_BLEND),
    "slot_count": len(slots),
    "empty_slots": sum(1 for s in slots if s == "NONE"),
    "unique_materials": len(set(slots)),
    "slots": slots,
    "polys": polys,
    "verts": verts,
    "uv_overlap_count": uv_overlap_count,
    "uv_in_0_1": all(r["u"][1] <= 1.001 and r["v"][1] <= 1.001 and r["u"][0] >= -0.001
                     and r["v"][0] >= -0.001 for r in per.values()),
    "uv_compat_vs_bake_source": {
        "bake_source": str(CONSOLIDATED),
        "bake_source_polys": cons_polys,
        "bake_source_slots": len(cons_slots),
        "shared_panels_checked": len(compat),
        "max_du": max_du, "max_dv": max_dv,
        "detail": compat,
        "note": "consolidated bake source has +{} polys vs 48-slot blend; "
                "existing UV-projected bakes remain valid iff UV bboxes match "
                "on shared panels".format(cons_polys - polys),
    },
    "per_slot": per,
    "outputs": {
        "obj": obj_base + ".obj", "fbx": obj_base + ".fbx",
        "face_uv_npz": str(PKG / "face_uv_data.npz"),
    },
    "color_attrs": [c.name for c in obj.data.color_attributes],
}
(PKG / "slotted_export_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("EXPORT_SUMMARY " + json.dumps({
    "slot_count": len(slots), "polys": polys, "verts": verts,
    "uv_overlap_count": uv_overlap_count, "max_du": max_du, "max_dv": max_dv,
}))
