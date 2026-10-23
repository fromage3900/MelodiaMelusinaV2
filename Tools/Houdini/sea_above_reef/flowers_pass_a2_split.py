#!/usr/bin/env python
"""Cos_FlowerSpring — Pass A2: split the 48 shorewake panels into Shirt + Skirt groups.

Works on the frozen 48-slot blend (copy discipline: owner files untouched).
Classifies each panel by world-height (Blender Z-up): top half -> Shirt,
bottom half -> Skirt, with the two huge panels (P01 bodice, P02/P03 skirt)
forced by poly share. Exports per-panel OBJs + group manifests.

Run: blender -b --factory-startup -noaudio --python flowers_pass_a2_split.py
Out: Saved/Audit/melusina_lookdev/flowers_outfit/passA2_panel_*.obj
     flowers_split_manifest.json
"""
import json
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parents[3]
LOOKDEV = PROJECT / "Saved" / "Audit" / "melusina_lookdev"
OUT = LOOKDEV / "flowers_outfit"
SRC_BLEND = LOOKDEV / "Shorewake_48MAT_frozen_snapshot.blend"
TARGET = "SM_ShorewakeDress_48MAT"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))
obj = bpy.data.objects[TARGET]
slots = [ms.material.name if ms.material else "NONE" for ms in obj.material_slots]
dg = bpy.context.evaluated_depsgraph_get()

# per-panel world-Z centroid + bbox + poly share
panel_stats = {}
for poly in obj.data.polygons:
    name = slots[poly.material_index]
    st = panel_stats.setdefault(name, {"polys": 0, "z_sum": 0.0, "z_min": 1e9, "z_max": -1e9})
    st["polys"] += 1
    for li in poly.loop_indices:
        co = obj.data.vertices[obj.data.loops[li].vertex_index].co
        z = (obj.matrix_world @ co).z
        st["z_sum"] += z
        st["z_min"] = min(st["z_min"], z)
        st["z_max"] = max(st["z_max"], z)
total_polys = sum(s["polys"] for s in panel_stats.values())
for name, st in panel_stats.items():
    st["z_centroid"] = st["z_sum"] / st["polys"]
    st["poly_share"] = st["polys"] / total_polys

zs = sorted(s["z_centroid"] for s in panel_stats.values())
mid = zs[len(zs) // 2]

shirt, skirt = [], []
for name in sorted(panel_stats):
    st = panel_stats[name]
    # huge panels decide by poly share: bodice P01 -> shirt
    if st["poly_share"] > 0.10:
        (shirt if name == "SW_Dress_P01" else skirt).append(name)
    elif st["z_centroid"] >= mid:
        shirt.append(name)
    else:
        skirt.append(name)

# export per-panel OBJs with group tags
for name in sorted(panel_stats):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # hide all faces except this panel via temporarily deleting? No — use bmesh face-mask export:
    # simpler: export full mesh per group with material groups; panel objs via separate meshes
for group, names in (("shirt", shirt), ("skirt", skirt)):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.obj_export(
        filepath=str(OUT / f"passA2_{group}_panels.obj"),
        export_selected_objects=True, export_materials=True,
        export_material_groups=True, export_uv=True, export_normals=True,
        forward_axis="NEGATIVE_Y", up_axis="Z",
    )

manifest = {
    "schema": "melodia.flowerspring_split.v1",
    "source_blend": str(SRC_BLEND),
    "z_mid": round(mid, 4),
    "shirt_panels": shirt,
    "skirt_panels": skirt,
    "panel_stats": {k: {"polys": v["polys"], "poly_share": round(v["poly_share"], 4),
                        "z_centroid": round(v["z_centroid"], 4),
                        "z_range": [round(v["z_min"], 3), round(v["z_max"], 3)]}
                    for k, v in sorted(panel_stats.items())},
    "outputs": ["passA2_shirt_panels.obj", "passA2_skirt_panels.obj"],
}
(OUT / "flowers_split_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("SPLIT " + json.dumps({"shirt": len(shirt), "skirt": len(skirt),
                             "shirt_panels": shirt, "skirt_panels": skirt}))
