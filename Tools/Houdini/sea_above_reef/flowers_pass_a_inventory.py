#!/usr/bin/env python
"""Pass A — inventory of the owner's melodiamelusinaflowers.usdz (copied, never modified).

Dumps: object census (meshes/armatures/empties), material slots, per-mesh poly/vert
counts, world-space bounds, UV presence. Exports all meshes as world-space OBJ for
the Houdini silhouette passes, plus a per-panel OBJ split for the slot pass.

Run: blender -b --factory-startup -noaudio --python flowers_pass_a_inventory.py
Out: Saved/Audit/melusina_lookdev/flowers_outfit/
     passA_inventory.json, passA_all_meshes.obj, passA_panel_*.obj
"""
import json
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parents[3]
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"
SRC = OUT / "melodiamelusinaflowers_copy.usdz"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_homefile(use_factory_startup=True)
bpy.ops.wm.usd_import(filepath=str(SRC))

objects = []
for ob in bpy.data.objects:
    rec = {"name": ob.name, "type": ob.type}
    if ob.type == "MESH":
        rec.update({
            "polys": len(ob.data.polygons),
            "verts": len(ob.data.vertices),
            "materials": [ms.material.name if ms.material else "NONE"
                          for ms in ob.material_slots],
            "uv_layers": [u.name for u in ob.data.uv_layers],
            "color_attrs": [c.name for c in ob.data.color_attributes],
            "shape_keys": len(ob.data.shape_keys.key_blocks) if ob.data.shape_keys else 0,
            "world_bounds": [round(v, 3) for v in
                             [c for corner in ob.bound_box for c in corner]],
            "parent": ob.parent.name if ob.parent else None,
        })
    objects.append(rec)

meshes = [o for o in objects if o["type"] == "MESH"]
manifest = {
    "schema": "melodia.flowers_pass_a.v1",
    "source": str(SRC),
    "source_sha256": "82585879F01F531B3D95BAD2C377C71F7364AEB7D9EFCED40FCED45EF5BBA8CF",
    "object_count": len(objects),
    "mesh_count": len(meshes),
    "armatures": [o["name"] for o in objects if o["type"] == "ARMATURE"],
    "total_polys": sum(m["polys"] for m in meshes),
    "total_verts": sum(m["verts"] for m in meshes),
    "objects": objects,
}

# world-space combined OBJ (Y-up like shorewake passes)
bpy.ops.object.select_all(action="DESELECT")
for ob in bpy.data.objects:
    if ob.type == "MESH":
        ob.select_set(True)
bpy.context.view_layer.objects.active = (
    bpy.data.objects[[o["name"] for o in meshes][0]] if meshes else None)
bpy.ops.wm.obj_export(
    filepath=str(OUT / "passA_all_meshes.obj"),
    export_selected_objects=True, export_materials=True,
    export_material_groups=True, export_uv=True, export_normals=True,
    forward_axis="NEGATIVE_Y", up_axis="Z",
)

# per-mesh OBJs (panel split basis)
for o in meshes:
    ob = bpy.data.objects[o["name"]]
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    safe = o["name"].replace(" ", "_").replace("/", "_")
    bpy.ops.wm.obj_export(
        filepath=str(OUT / f"passA_panel_{safe}.obj"),
        export_selected_objects=True, export_materials=True,
        export_material_groups=True, export_uv=True, export_normals=True,
        forward_axis="NEGATIVE_Y", up_axis="Z",
    )

(OUT / "passA_inventory.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("PASS_A " + json.dumps({
    "meshes": len(meshes),
    "total_polys": manifest["total_polys"],
    "materials": sorted({mm for m in meshes for mm in m["materials"]})[:60],
    "mesh_names": [m["name"] for m in meshes][:60],
}))
