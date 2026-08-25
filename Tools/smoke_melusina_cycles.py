# -*- coding: utf-8 -*-
"""Solo Melusina Cycles smoke test - prove she can appear in pixels.

*** DO NOT RUN ON LIVE STAGE WITHOUT ARTIST CONSENT ***
  Honors Saved/Audit/MELUSINA_SHADER_AGENT_STOP.
  Mutates hide_render / world nodes for a throwaway plate - no stage save.
"""
from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
STOP = ROOT / "Saved" / "Audit" / "MELUSINA_SHADER_AGENT_STOP"
OUT = Path(r"G:\EnvironmentPortfolio\BS_GodFile\my-site-clean\generated\assets\character\melusina_cycles_smoke.png")


def log(m: str) -> None:
    print(f"[Smoke] {m}", flush=True)


def main() -> None:
    if STOP.is_file():
        log(f"ABORT: {STOP} present - smoke test blocked on lookdev freeze.")
        return
    # Hide everything
    for o in bpy.data.objects:
        if o.type in {"MESH", "CURVE", "LIGHT"}:
            o.hide_render = True

    # Show Melusina + hair + eyes only
    for o in bpy.data.objects:
        n = o.name
        if (
            n == "Melusina"
            or n.startswith("Hair Strand")
            or "Eyebrow" in n
            or "Eyelash" in n
            or "Iris" in n
            or "Cornea" in n
            or n.startswith("Retopo_")
            or n.startswith("Melusina_")
            or n in ("simply_coll", "Melusina_Skirt")
        ):
            o.hide_render = False
            o.hide_viewport = False
            o.hide_set(False)
            log(f"on {n}")

    for c in bpy.data.collections:
        c.hide_render = False

    # Simple world
    w = bpy.data.worlds.new("W_Smoke") if "W_Smoke" not in bpy.data.worlds else bpy.data.worlds["W_Smoke"]
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.2, 0.22, 0.3, 1)
    bg.inputs[1].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])

    # Sun light
    if "L_SmokeSun" not in bpy.data.objects:
        light_data = bpy.data.lights.new(name="L_SmokeSun", type="SUN")
        light_data.energy = 3.0
        light_obj = bpy.data.objects.new(name="L_SmokeSun", object_data=light_data)
        bpy.context.scene.collection.objects.link(light_obj)
    else:
        light_obj = bpy.data.objects["L_SmokeSun"]
    light_obj.hide_render = False
    light_obj.rotation_euler = (0.9, 0.2, 0.5)

    # Camera aimed at Melusina bounds
    mel = bpy.data.objects.get("Melusina")
    coords = [mel.matrix_world @ Vector(c) for c in mel.bound_box]
    mid = sum(coords, Vector()) / len(coords)
    cam = bpy.data.objects.get("Cam_Beauty") or bpy.data.objects.new("Cam_Smoke", bpy.data.cameras.new("Cam_Smoke"))
    if cam.name not in bpy.context.scene.collection.objects and cam.name not in [o.name for o in bpy.data.objects]:
        bpy.context.scene.collection.objects.link(cam)
    cam.location = mid + Vector((2.2, -3.5, 0.6))
    cam.rotation_euler = (mid - cam.location).to_track_quat("-Z", "Y").to_euler()
    if cam.data:
        cam.data.lens = 50
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 32
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT)
    log(f"mid={tuple(round(x,3) for x in mid)} cam={tuple(round(x,3) for x in cam.location)}")
    bpy.ops.render.render(write_still=True)
    log(f"wrote {OUT} ({OUT.stat().st_size if OUT.exists() else 0})")


if __name__ == "__main__":
    main()
