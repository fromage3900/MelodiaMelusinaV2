"""Render the Shorewake dress with each panel colored by garment material group.

Opens the frozen-snapshot blend (48 slots), reads garment_layers_manifest.json,
assigns each slot a flat color by its material group, and renders several views
(front, three-quarter, back) in Eevee so the silhouette-merge labeling is
visually verifiable. Writes PNGs + a manifest. Non-destructive.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy

BLEND = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/"
             r"Shorewake_48MAT_frozen_snapshot.blend")
MANIFEST = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/"
                r"night_pkg_2026-08-31/garment_layers_manifest.json")
OUT_DIR = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/silhouette_out")


def palette(n):
    hsv = [(i * 360.0 / n) % 360 for i in range(n)]
    for h in hsv:
        # hsv->rgb (Blender 0..1 linear-ish)
        hx = h / 360.0
        c = 0.85
        x = c * (1 - abs((hx * 6) % 2 - 1))
        m = 0.08
        if hx < 1 / 6: rgb = (c, x, m)
        elif hx < 2 / 6: rgb = (x, c, m)
        elif hx < 3 / 6: rgb = (m, c, x)
        elif hx < 4 / 6: rgb = (m, x, c)
        elif hx < 5 / 6: rgb = (x, m, c)
        else: rgb = (c, m, x)
        yield tuple(v + m for v in rgb) + (1.0,)


def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = data["material_groups"]
    panel_to_group = {}
    for r in data["panels"]:
        panel_to_group[r["panel"]] = r["material_group"]

    group_names = sorted(groups.keys())
    colors = dict(zip(group_names, palette(len(group_names))))

    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 1100

    obj = bpy.data.objects.get("SM_ShorewakeDress_48MAT")
    if obj is None:
        raise RuntimeError("mesh not found")
    # replace each slot's material with a flat group color
    for slot in range(len(obj.data.materials)):
        slotmat = obj.data.materials[slot]
        if not slotmat or not slotmat.name.startswith("SW_Dress"):
            continue
        grp = panel_to_group.get(slotmat.name, "M_Skirt_Full")
        col = colors[grp]
        mat = bpy.data.materials.new(f"GRP_{grp}")
        mat.use_nodes = True
        base = mat.node_tree.nodes["Principled BSDF"]
        base.inputs["Base Color"].default_value = col
        base.inputs["Roughness"].default_value = 1.0
        obj.data.materials[slot] = mat

    # hide everything else; camera setup
    for o in bpy.data.objects:
        if o is not obj:
            o.hide_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if "Cam" not in bpy.data.cameras:
        cam = bpy.data.cameras.new("Cam")
        cam_obj = bpy.data.objects.new("Cam", cam)
        bpy.context.collection.objects.link(cam_obj)
    else:
        cam_obj = bpy.data.objects["Cam"]
    scene.camera = cam_obj
    cam_obj.data.type = "PERSP"
    cam_obj.data.lens = 45

    # fit camera to rail/target distances using bbox
    from mathutils import Vector
    lo = obj.matrix_world @ Vector(obj.bound_box[0])
    hi = obj.matrix_world @ Vector(obj.bound_box[6])
    center = Vector(((lo[i] + hi[i]) / 2 for i in range(3)))
    diag = ((hi[0]-lo[0])**2 + (hi[1]-lo[1])**2 + (hi[2]-lo[2])**2) ** 0.5
    dist = diag * 1.7

    up = Vector((0, 0, 1))
    target = center.copy()
    views = {
        "FRONT": (math.radians(0.0), math.radians(0.0)),
        "THREE_QUARTER": (math.radians(25.0), math.radians(35.0)),
        "BACK": (math.radians(15.0), math.radians(180.0)),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for vname, (pitch, yaw) in views.items():
        # orbit: spherical around target
        cp = math.cos(pitch); sp = math.sin(pitch)
        cy = math.cos(yaw); sy = math.sin(yaw)
        offset = Vector((dist * cp * sy, -dist * cp * cy, dist * sp))
        cam_obj.location = target + offset
        direction = (target - cam_obj.location).normalized()
        # rotation such that -Z points along direction, Y up
        rot = direction.to_track_quat("-Z", "Y")
        cam_obj.rotation_euler = rot.to_euler()
        scene.render.filepath = str(OUT_DIR / f"GARMENT_MERGE_{vname}.png")
        bpy.ops.render.render(write_still=True)
        outputs[vname] = f"GARMENT_MERGE_{vname}.png"
        print(f"[gm] {vname} rendered")

    legend = {"groups": group_names, "colors": {g: list(colors[g]) for g in group_names}}
    (OUT_DIR / "garment_merge_manifest.json").write_text(
        json.dumps({**legend, "outputs": outputs}, indent=2), encoding="utf-8")
    print("[gm] done ->", OUT_DIR)


if __name__ == "__main__":
    main()