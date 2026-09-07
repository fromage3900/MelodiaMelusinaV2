# -*- coding: utf-8 -*-
"""ME_WaveViolin 'Night Reel' — p00 stage bootstrap (headless, idempotent).

Creates the base .blend: collections, socket empties, EEVEE settings,
3-band toon dusk world, 3-light rig, cameras. Saves to lane folder.
Never touches the GUI Blender session.
"""
import bpy, json, math, os, sys
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
os.makedirs(OUT, exist_ok=True)

def log(m): print(f"[vr-p00] {m}", flush=True)

# fresh scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# collections
names = ["ME_WaveViolin_Assemblies","ME_WaveViolin_Strings","ME_WaveViolin_Ornament",
         "ME_WaveViolin_Transformation","ME_WaveViolin_Presentation","Export"]
root = bpy.context.scene.collection
for n in names:
    c = bpy.data.collections.get(n) or bpy.data.collections.new(n)
    if c.name not in [ch.name for ch in root.children]:
        root.children.link(c)

# sockets (placement anchors; transform rig will parent to these later)
socket_pos = {
    "SOCKET_Scroll_Pommel": (0, 0, 0.62),
    "SOCKET_Bridge_Hub":    (0, -0.02, 0.05),
    "SOCKET_Tail_Deploy":   (0, 0, -0.48),
    "SOCKET_Waist_L":       (-0.11, -0.02, -0.05),
    "SOCKET_Waist_R":       (0.11, -0.02, -0.05),
    "SOCKET_FHole_L":       (-0.055, -0.028, -0.02),
    "SOCKET_FHole_R":       (0.055, -0.028, -0.02),
}
for n, p in socket_pos.items():
    if bpy.data.objects.get(n): continue
    e = bpy.data.objects.new(n, None)
    e.empty_display_type = 'SPHERE'; e.empty_display_size = 0.02
    e.location = p
    bpy.data.collections["ME_WaveViolin_Transformation"].objects.link(e)

# master control empty (drivers will key off this in p03)
mc = bpy.data.objects.get("ME_WaveViolin_Control")
if not mc:
    mc = bpy.data.objects.new("ME_WaveViolin_Control", None)
    mc.empty_display_type = 'ARROWS'; mc.empty_display_size = 0.12
    bpy.data.collections["ME_WaveViolin_Transformation"].objects.link(mc)

# render settings (Rev05 conventions)
scn = bpy.context.scene
try: scn.render.engine = "BLENDER_EEVEE_NEXT"
except Exception: scn.render.engine = "BLENDER_EEVEE"
scn.render.resolution_x = 1400; scn.render.resolution_y = 1400
scn.render.image_settings.file_format = "PNG"
if hasattr(scn, "eevee") and hasattr(scn.eevee, "taa_render_samples"):
    scn.eevee.taa_render_samples = 64
scn.eevee.use_raytracing = True if hasattr(scn.eevee, "use_raytracing") else False

# toon dusk world (3 hard bands, lesson from Day 2)
w = bpy.data.worlds.get("ME_World_CelDuskNight") or bpy.data.worlds.new("ME_World_CelDuskNight")
scn.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld")
bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 0.5
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.interpolation = "CONSTANT"
els = ramp.color_ramp.elements
els[0].position = 0.0;  els[0].color = (0.98, 0.72, 0.80, 1)
els[1].position = 0.40; els[1].color = (0.55, 0.45, 0.75, 1)
e = els.new(0.72); e.color = (0.18, 0.22, 0.44, 1)
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.15; mr.inputs["From Max"].default_value = 0.85
nt.links.new(tc.outputs["Window"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# light rig (WaveHarp presentation values, tightened per Day-2 review)
lights = {
    "ME_WaveViolin_Light_Key":  (("AREA", 650, 0.6),  (1.4, -1.8, 1.55)),
    "ME_WaveViolin_Light_Fill": (("AREA", 260, 1.0),  (-1.2, -1.0, 0.72)),
    "ME_WaveViolin_Light_Rim":  (("AREA", 800, 0.9),  (0.6, 0.7, 1.45)),
}
for n, ((t, en, sz), loc) in lights.items():
    if bpy.data.objects.get(n): continue
    ld = bpy.data.lights.new(n, t); ld.energy = en; ld.size = sz
    ob = bpy.data.objects.new(n, ld); ob.location = loc
    bpy.data.collections["ME_WaveViolin_Presentation"].objects.link(ob)
    # aim at origin
    d = -Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ground + cameras
gr = bpy.data.objects.get("ME_WaveViolin_Ground")
if not gr:
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, -0.72))
    gr = bpy.context.active_object; gr.name = "ME_WaveViolin_Ground"
    gm = bpy.data.materials.new("ME_MAT_Violin_Ground"); gm.use_nodes = True
    gp = gm.node_tree.nodes["Principled BSDF"]
    gp.inputs["Base Color"].default_value = (0.16, 0.13, 0.20, 1)
    gp.inputs["Roughness"].default_value = 0.95
    gr.data.materials.append(gm)
    for c in list(gr.users_collection): c.objects.unlink(gr)
    bpy.data.collections["ME_WaveViolin_Presentation"].objects.link(gr)

for cn, loc in {
    "ME_WaveViolin_Cam_Presentation": (0.44, -2.03, 0.1),
}.items():
    if not bpy.data.objects.get(cn):
        cd = bpy.data.cameras.new(cn); cd.lens = 55
        ob = bpy.data.objects.new(cn, cd); ob.location = loc
        d = Vector((0, 0, 0.02)) - Vector(loc)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        bpy.data.collections["ME_WaveViolin_Presentation"].objects.link(ob)
        scn.camera = ob

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
rep = {"phase": "p00", "ok": True, "blend": BLEND, "collections": names,
       "sockets": list(socket_pos), "res": [scn.render.resolution_x, scn.render.resolution_y]}
with open(os.path.join(OUT, "p00_report.json"), "w") as f: json.dump(rep, f, indent=1)
log("saved " + BLEND)
