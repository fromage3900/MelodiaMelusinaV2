"""Render the 48 Shorewake dress panels as isolated silhouettes -> contact sheet.

Opens the frozen-snapshot blend (has all 48 material slots intact), isolates
each panel by material index, renders it flat-color against black in Eevee
(fast, orthographic front view), assembles an 8x6 grid contact sheet, and
writes a manifest mapping panel name -> PNG.

No destructive edits to the source blend: works on a temp copy, deletes
everything after render. Deterministic.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Vector

BLEND = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/"
             r"Shorewake_48MAT_frozen_snapshot.blend")
OUT_DIR = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/silhouette_out")
SEED_HASH = "20260902"
# grid
COLS, ROWS = 8, 6
CELL = 280
MARGIN = 80
SHEET_W = COLS * CELL + MARGIN * 2
SHEET_H = ROWS * CELL + MARGIN * 2


def isolate_panel_copy(name: str) -> bpy.types.Object:
    """Duplicate the slotted mesh, delete all faces except one material."""
    src = bpy.data.objects["SM_ShorewakeDress_48MAT"]
    idx = None
    for slot in range(len(src.data.materials)):
        if src.data.materials[slot] and src.data.materials[slot].name == name:
            idx = slot
            break
    if idx is None:
        raise RuntimeError(f"slot {name} not found")
    me = src.data
    obj = src.copy()
    obj.data = me.copy()
    bpy.context.collection.objects.link(obj)
    # build face set to keep
    keep = [p.index for p in me.polygons if p.material_index == idx]
    if not keep:
        raise RuntimeError(f"{name}: no faces on slot")
    keep_set = set(keep)
    # remove verts not referenced after face deletion (leave to Blender's cleanup)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bpy.context.edit_object.data
    import bmesh
    bm2 = bmesh.from_edit_mesh(bm)
    for f in bm2.faces:
        f.select = f.index in keep_set
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.update()
    return obj


def flat_mat(name: str, color):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    base = m.node_tree.nodes["Principled BSDF"]
    base.inputs["Base Color"].default_value = color
    base.inputs["Roughness"].default_value = 1.0
    m.diffuse_color = color
    return m


def setup_scene():
    # Ensure a clean scene with camera + sun
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    if "SilCam" not in bpy.data.cameras:
        cam = bpy.data.cameras.new("SilCam")
        cam.lens = 85
        cam_obj = bpy.data.objects.new("SilCam", cam)
        bpy.context.collection.objects.link(cam_obj)
    else:
        cam_obj = bpy.data.objects["SilCam"]
    cam_obj.rotation_euler = (1.5708, 0.0, 0.0)  # front view looking down -Z? adjust
    scene.camera = cam_obj


def render_panel(obj: bpy.types.Object, out_png: Path, cell: int):
    # ortho camera fitted to the object's bbox
    scene = bpy.context.scene
    cam = scene.camera
    cam.data.type = "ORTHO"
    lo = obj.matrix_world @ Vector(obj.bound_box[0])
    hi = obj.matrix_world @ Vector(obj.bound_box[6])
    size = hi - lo
    cam.data.ortho_scale = max(size[0], size[1]) * 1.25
    cx = (lo.x + hi.x) / 2.0
    cy = (lo.y + hi.y) / 2.0
    z_front = hi.z + max(size[0], size[1]) * 2.0
    cam.location = ((cx, cy, z_front))
    cam.rotation_euler = (0.0, 0.0, 0.0)
    cam.data.lens = 35
    scene.render.resolution_x = cell
    scene.render.resolution_y = cell
    # only our object visible
    for o in bpy.data.objects:
        o.hide_set(True)
    obj.hide_set(False)
    scene.render.filepath = str(out_png)
    bpy.ops.render.render(write_still=True)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    src = bpy.data.objects.get("SM_ShorewakeDress_48MAT")
    if src is None:
        raise RuntimeError("mesh SM_ShorewakeDress_48MAT not found in blend")
    # collect slot names
    slot_names = []
    for slot in range(len(src.data.materials)):
        m = src.data.materials[slot]
        if m is not None and m.name.startswith("SW_Dress"):
            slot_names.append(m.name)
    slot_names.sort(key=lambda n: int("".join(ch for ch in n if ch.isdigit())))
    print(f"[sil] {len(slot_names)} slots: {slot_names[0]}..{slot_names[-1]}")

    setup_scene()
    # hide source so it doesn't render
    src.hide_set(True)

    manifests = []
    for i, name in enumerate(slot_names):
        obj = isolate_panel_copy(name)
        png = f"panel_{i+1:02d}_{name}.png"
        vcount = len(obj.data.vertices)
        pcount = len(obj.data.polygons)
        render_panel(obj, OUT_DIR / png, CELL)
        manifests.append({"slot": i, "panel": name, "png": png,
                          "verts": vcount, "polys": pcount})
        # remove the isolated copy
        bpy.data.objects.remove(obj, do_unlink=True)
        print(f"[sil] {name} -> {png} ({vcount} v)")

    # assemble contact sheet with PIL (blender ships it)
    from PIL import Image, ImageDraw
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(sheet)
    for i, rec in enumerate(manifests):
        r, c = divmod(i, COLS)
        x0 = MARGIN + c * CELL
        y0 = MARGIN + r * CELL
        img = Image.open(OUT_DIR / rec["png"]).resize((CELL, CELL))
        sheet.alpha_composite(img, (x0, y0))
        draw.text((x0 + 6, y0 + 6), rec["panel"], fill=(255, 255, 255))
    sheet_p = OUT_DIR / "SILHOUETTE_GRID_48.png"
    sheet.convert("RGB").save(sheet_p)
    print(f"[sil] contact sheet -> {sheet_p}")

    manifest = {
        "schema": "melodia.shorewake_silhouette_render.v1",
        "seed_hash": SEED_HASH,
        "source_blend": str(BLEND),
        "panel_count": len(manifests),
        "grid": {"cols": COLS, "rows": ROWS, "cell": CELL},
        "panels": manifests,
        "sheet": str(sheet_p),
    }
    (OUT_DIR / "silhouette_render_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()