"""Render the five magical-surreal stones as a gem lineup, headless.

A gem material is judged by eye or not at all -- the numbers only prove it built.
This lays all five out at matched scale under the same key, plus a macro of one,
so the register can actually be compared.

Run: blender -b --factory-startup --python regalia_stone_sheet.py
"""

import bpy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(HERE)
import regalia_stone as RS  # noqa: E402

OUT = HERE


def bpy_extras_ndc(world_pt):
    """Project a world point to normalised device coords (-1..1) via the camera."""
    from bpy_extras.object_utils import world_to_camera_view
    scn = bpy.context.scene
    co = world_to_camera_view(scn, scn.camera, world_pt)
    return (co.x, co.y, co.z)


def main():
    scn = bpy.context.scene
    from math import radians, atan2, pi
    # --factory-startup STILL creates a 2 m Cube at the origin, dead centre in the
    # shot. Measured: it projected to ndc (0.5, 0.5) and was the "empty" grey frame.
    for junk in ("Cube",):
        ob = bpy.data.objects.get(junk)
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
    scn.render.engine = "BLENDER_EEVEE"
    scn.render.resolution_x = 1400
    scn.render.resolution_y = 620
    scn.render.film_transparent = False
    # AgX is Blender's default and it DESATURATES strong emission hard -- measured:
    # emission strength 3.0-4.6 with saturated cores rendered as pale pastel glass.
    # For a deliberately surreal palette the transform has to be Standard.
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.exposure = 0.0
    scn.view_settings.look = "None"
    try:
        scn.eevee.taa_render_samples = 96
    except Exception:
        pass

    # a dark stage so emission reads
    # build a FRESH world: the factory default is 0.05 grey, which renders as a
    # white field and hides the emission entirely.
    world = bpy.data.worlds.new("STAGE_DARK")
    scn.world = world
    world.use_nodes = True
    wnt = world.node_tree
    bgn = next((n for n in wnt.nodes if n.bl_idname == "ShaderNodeBackground"), None)
    if bgn is None:
        bgn = wnt.nodes.new("ShaderNodeBackground")
        wnt.links.new(bgn.outputs[0], next(n for n in wnt.nodes
                     if n.bl_idname == "ShaderNodeOutputWorld").inputs["Surface"])
    bgn.inputs[0].default_value = (0.012, 0.010, 0.028, 1.0)
    bgn.inputs[1].default_value = 1.0
    # no bloom to hide the rim glow
    try:
        scn.eevee.use_bloom = False
    except Exception:
        pass

    # five gems in a row, each faceted
    keys = list(RS.STONES.keys())
    gap = 0.13
    faceted = []
    for i, k in enumerate(keys):
        mat = RS.build_stone(k, "REGALIA_STONE_" + k.replace(" ", "_"))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.05,
                                             location=((i - 2) * gap, 0.0, 0.0))
        ob = bpy.context.active_object
        ob.name = "GEM_" + k.replace(" ", "_")
        # bevel the icosphere slightly so facets catch a highlight
        b = ob.modifiers.new("Bevel", "BEVEL")
        b.width = 0.004
        b.segments = 2
        ob.data.materials.append(mat)
        faceted.append(ob)

    # three-point rig, small and tight
    for nm, loc, energy, size, col in (
            ("K", (0.30, -0.45, 0.42), 26, 0.45, (1.0, 0.97, 0.92)),
            ("F", (-0.55, -0.35, 0.10), 8, 0.70, (0.80, 0.88, 1.0)),
            ("R", (0.10, 0.55, 0.30), 34, 0.30, (0.72, 0.62, 1.0))):
        ld = bpy.data.lights.new("L_" + nm, "AREA")
        ld.energy = energy
        ld.size = size
        ld.color = col
        lo = bpy.data.objects.new("L_" + nm, ld)
        scn.collection.objects.link(lo)
        lo.location = loc
        # lights aim at the origin; use a track constraint-free explicit approach
        lo.rotation_euler = (radians(90.0) - math.atan2(loc[2],
                            math.hypot(loc[0], loc[1])), 0.0,
                            math.atan2(-loc[0], -loc[1]) + math.pi / 2)

    cd = bpy.data.cameras.new("CAM")
    cd.lens = 40
    cd.clip_start = 0.01
    cam = bpy.data.objects.new("CAM", cd)
    scn.collection.objects.link(cam)
    cam.location = (0.0, -1.05, 0.05)
    # 82 deg: just above level, so facets catch the key light and the row still
    # reads as a row. 88 deg looked down on the gem tops and read as flat pentagons.
    cam.rotation_euler = (radians(82.0), 0.0, 0.0)
    scn.camera = cam

    # report what is actually in front of the camera before blaming the shader
    vl = bpy.context.view_layer
    inframe = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        st = {"name": ob.name, "hide_render": ob.hide_render,
              "visible": ob.visible_get(), "loc": [round(v, 3) for v in ob.location]}
        # project the world bbox centre into normalised device coords
        import mathutils
        pts = [ob.matrix_world @ mathutils.Vector(c) for c in ob.bound_box]
        ctr = sum(pts, mathutils.Vector()) / 8.0
        proj = vl.depsgraph and None
        co = bpy_extras_ndc(ctr)
        st["ndc"] = [round(x, 3) for x in co] if co else None
        inframe.append(st)
    for s in inframe:
        print("OBJ", s["name"], "hide", s["hide_render"], "vis", s["visible"],
              "loc", s["loc"], "ndc", s["ndc"])
    print("CAM loc", [round(v, 3) for v in cam.location],
          "rot", [round(v, 3) for v in cam.rotation_euler],
          "lens", cam.data.lens, "type", cam.data.type,
          "ortho_scale", cam.data.ortho_scale, "sensor_fit", cam.data.sensor_fit)
    print("SCENE camera is cam:", scn.camera is cam,
          "| res", scn.render.resolution_x, scn.render.resolution_y,
          "| pct", scn.render.resolution_percentage)

    scn.render.filepath = os.path.join(OUT, "stones_lineup.png")
    bpy.ops.render.render(write_still=True)
    print("SHOT stones_lineup", os.path.exists(scn.render.filepath))

    # macro of the default stone
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.hide_render = ob.name != "GEM_Void_Orchid"
    cam.location = (-0.26, -0.22, 0.03)
    cam.rotation_euler = (radians(80.0), 0.0, 0.0)
    scn.render.filepath = os.path.join(OUT, "stone_macro.png")
    bpy.ops.render.render(write_still=True)
    print("SHOT stone_macro", os.path.exists(scn.render.filepath))

    # --- verify the sheet against the pixels, not against an impression
    im = bpy.data.images.load(os.path.join(OUT, "stones_lineup.png"), check_existing=False)
    px = list(im.pixels)
    n = len(px) // 4
    R = [px[i * 4] for i in range(n)]
    G = [px[i * 4 + 1] for i in range(n)]
    B = [px[i * 4 + 2] for i in range(n)]
    lum = [0.2126 * R[i] + 0.7152 * G[i] + 0.0722 * B[i] for i in range(n)]
    W, H = 1400, 620
    # top 8% of rows is stage by construction (gems are centred, 44% of height)
    def band(r0, r1):
        acc = []
        for y in range(int(H * r0), int(H * r1)):
            for x in range(0, W, 7):
                i = (y * W + x) * 4
                acc.append((px[i], px[i + 1], px[i + 2]))
        return acc
    stage = band(0.00, 0.08)
    gems = band(0.42, 0.58)
    def mean3(a):
        return tuple(sum(c[k] for c in a) / len(a) for k in range(3))
    sm, gm = mean3(stage), mean3(gems)
    print("STAGE top-strip RGB   %.3f %.3f %.3f   (want < 0.30 = dark)" % sm)
    print("GEMS  mid-strip  RGB  %.3f %.3f %.3f   (want saturated vs stage)" % gm)
    print("GEM/STAGE contrast    %.2fx                  (want > 1.8)" % (
        (max(gm) / 1e-6) / max(max(sm), 1e-6)))
    corner = (R[0], G[0], B[0])
    # chroma spread across the frame, sampled on a grid
    picks = []
    step = max(1, n // 4000)
    for i in range(0, n, step):
        picks.append((R[i], G[i], B[i]))
    sat = []
    for r, g, b in picks:
        mx, mn = max(r, g, b), min(r, g, b)
        sat.append(0.0 if mx <= 0 else (mx - mn) / mx)
    print("PIX corner RGB      %.3f %.3f %.3f   (want < 0.10 = dark stage)" % corner)
    print("PIX mean luminance  %.3f              (want 0.05-0.45)" % (sum(lum) / n))
    print("PIX mean saturation %.3f              (want > 0.25 for vivid)" % (sum(sat) / len(sat)))
    print("PIX clipped frac    %.3f              (want < 0.02)" % (
        sum(1 for v in lum if v >= 0.995) / n))
    bpy.data.images.remove(im)
    print("STONE-SHEET-COMPLETE")


if __name__ == "__main__":
    main()
