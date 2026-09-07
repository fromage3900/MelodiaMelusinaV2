# -*- coding: utf-8 -*-
"""p06 — editorial drape: XPBD cloth veil settle -> shape key, with authored fallback.

Timeboxed: try node-cloth settle headless 60 frames; if the solver API fails
or the veil explodes (max vertex delta sanity), fall back to an authored
catenary drape shape key. Either way: `Drape_Editorial` key + plate.
"""
import bpy, json, math, os
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p06] {m}", flush=True)
report = {"phase": "p06", "path": None}

# veil mesh: strip hanging from scroll socket
old = bpy.data.objects.get("ME_WaveViolin_Veil")
if old: bpy.data.objects.remove(old, do_unlink=True)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=14, y_subdivisions=24, size=1)
veil = bpy.context.active_object; veil.name = "ME_WaveViolin_Veil"
veil.scale = (0.075, 0.16, 1)
bpy.ops.object.transform_apply(scale=True)
for c in list(veil.users_collection): c.objects.unlink(veil)
bpy.data.collections["ME_WaveViolin_Ornament"].objects.link(veil)
skel = []
# move to hang from scroll: top edge at socket
top = min(v.co.y for v in veil.data.vertices)
for v in veil.data.vertices:
    v.co.z += -0.60 + (top - v.co.y) * 1.0   # hang down in -Z from y top
    v.co.y -= 0.03
    v.co.x *= 1.0
skel_top = [i for i, v in enumerate(veil.data.vertices) if abs(v.co.z - max(u.co.z for u in veil.data.vertices)) < 1e-4]
vg = veil.vertex_groups.new(name="ME_Pin")
vg.add(skel_top, 1.0, 'REPLACE')
veil.data.materials.append(bpy.data.materials["ME_MAT_Violin_RibbonTwilight"])

ok_xpbd = False
try:
    # try the 5.2 node-cloth path: Cloth Dynamics + XPBD solver in a GN modifier
    ng = bpy.data.node_groups.new("ME_Violin_ClothSettle", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n_in = ng.nodes.new("NodeGroupInput"); n_out = ng.nodes.new("NodeGroupOutput")
    cd = None
    for nt_id in ("GeometryNodeClothDynamics", "GeometryNodeCloth"):
        try:
            cd = ng.nodes.new(nt_id); break
        except Exception:
            continue
    if cd is None:
        raise RuntimeError("no cloth node in this build")
    # wire minimally; pin group attribute name
    for inp in cd.inputs:
        if "Pin" in inp.name and "Group" in inp.name:
            cd.inputs[inp.name].default_value = "ME_Pin"
    ng.links.new(n_in.outputs["Geometry"], cd.inputs["Geometry"])
    # step through frames by setting scene frame + depsgraph eval
    md = veil.modifiers.new("ME_XPBD", "NODES"); md.node_group = ng
    scn = bpy.context.scene
    settle_max = 0.0
    base = [v.co.copy() for v in veil.data.vertices]
    for f in range(1, 61):
        scn.frame_set(f)
        ev = veil.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        try:
            dv = max((me.vertices[i].co - base[i]).length for i in range(len(base)))
            settle_max = max(settle_max, dv)
        except Exception:
            raise RuntimeError("vert mismatch")
        ev.to_mesh_clear()
        if f == 40:
            final = [me.vertices[i].co.copy() for i in range(len(base))]
    if settle_max > 0.6:
        raise RuntimeError(f"veil exploded: max delta {settle_max:.2f}")
    # bake to shape key
    veil.modifiers.remove(md)
    scn.frame_set(1)
    if not veil.data.shape_keys:
        veil.shape_key_add(name="Basis", from_mix=False)
    sk = veil.data.shape_keys.new_key("Drape_Editorial") if hasattr(veil.data.shape_keys,'new_key') else None
    if sk is None:
        sk = veil.shape_key_add(name="Drape_Editorial", from_mix=False)
    for i, co in enumerate(final):
        sk.data[i].co = co
    report["path"] = "xpbd_settled"
    report["settle_max_delta"] = round(settle_max, 3)
    ok_xpbd = True
except Exception as exc:
    log(f"xpbd lane failed: {exc} -> authored fallback")
    # authored catenary drape fallback
    if veil.modifiers.get("ME_XPBD"): veil.modifiers.remove(veil.modifiers["ME_XPBD"])
    bpy.context.scene.frame_set(1)
    zs = [v.co.z for v in veil.data.vertices]
    zmax = max(zs)
    if not veil.data.shape_keys:
        veil.shape_key_add(name="Basis", from_mix=False)
    if "Drape_Editorial" not in [k.name for k in veil.data.shape_keys.key_blocks]:
        sk = veil.shape_key_add(name="Drape_Editorial", from_mix=False)
    else:
        sk = veil.data.shape_keys.key_blocks["Drape_Editorial"]
    for i, v in enumerate(veil.data.vertices):
        t = (zmax - v.co.z) / max(zmax - min(zs), 1e-6)   # 0 top -> 1 bottom
        sway = math.sin(t * math.pi * 1.3 + v.co.x * 9) * 0.022 * t
        puff = math.sin(t * math.pi) * 0.018
        co = v.co + Vector((sway, -puff, 0))
        sk.data[i].co = co
    report["path"] = "authored_fallback"
    report["reason"] = str(exc)[:200]

bpy.context.scene.frame_set(1)
# poster composition: slight low hero
cam = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
cam.location = Vector((0.5, -1.75, 0.18))
d = Vector((0, 0, 0.05)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 60
scn = bpy.context.scene
scn.render.filepath = os.path.join(OUT, "p06_poster.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_mainfile()
report["ok"] = True
json.dump(report, open(os.path.join(OUT, "p06_report.json"), "w"), indent=1)
log(f"done via {report['path']}")
