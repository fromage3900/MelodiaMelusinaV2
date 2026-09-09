# -*- coding: utf-8 -*-
"""p05 — ribbons on scroll/tail sockets + bead chain along waist.

Lessons folded from WaveHarp Day 2:
- ribbons fall with gravity + flutter, never skyward
- hue node is a ROTATION (0.5 identity) — use direct color, no hue trick
- Base Color may be linked in hybrid mats — check before writing defaults
- cloth read: metallic 0, roughness ~0.7, modest sheen
"""
import bpy, json, math, os
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p05] {m}", flush=True)

# --- twilight cloth mat (standalone simple graph; cel group optional) ---
mr = bpy.data.materials.get("ME_MAT_Violin_RibbonTwilight")
if not mr:
    mr = bpy.data.materials["ME_MAT_Violin_AmberNight"].copy()
    mr.name = "ME_MAT_Violin_RibbonTwilight"
pr = next(n for n in mr.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
bc = pr.inputs["Base Color"]
if bc.is_linked:
    for l in list(bc.links): mr.node_tree.links.remove(l)
bc.default_value = (0.24, 0.08, 0.34, 1)          # deep twilight violet, direct
pr.inputs["Metallic"].default_value = 0.0
pr.inputs["Roughness"].default_value = 0.80
sw = pr.inputs.get("Sheen Weight") or pr.inputs.get("Sheen")
if sw: sw.default_value = 0.5
ei = pr.inputs.get("Emission Strength")
if ei and not ei.is_linked: ei.default_value = 0.0

def ribbon(name, socket, length, width, side, phase, flutter):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    sk = bpy.data.objects[socket]
    o = sk.matrix_world.translation.copy()
    cu = bpy.data.curves.new(name + "_curve", "CURVE")
    cu.dimensions = "3D"; cu.twist_mode = "Z_UP"; cu.extrude = width; cu.resolution_u = 24
    sp = cu.splines.new("BEZIER"); N = 7; sp.bezier_points.add(N-1)
    for i, bp in enumerate(sp.bezier_points):
        t = i/(N-1)
        fall = -length*t
        arc = side * length * 0.5 * (t**1.6)
        back = -length * 0.16 * (t**1.2)
        wave = math.sin(t*math.pi*2 + phase) * flutter * t
        bp.co = o + Vector((arc + wave, back, fall))
        bp.handle_left_type = bp.handle_right_type = "AUTO"
        bp.radius = 1.0 - 0.8*(t**2)
    ob = bpy.data.objects.new(name, cu)
    bpy.data.collections["ME_WaveViolin_Ornament"].objects.link(ob)
    ob.parent = sk; ob.matrix_parent_inverse = sk.matrix_world.inverted()
    sol = ob.modifiers.new("ME_Ribbon_Thickness", "SOLIDIFY"); sol.thickness = 0.0016
    ob.data.materials.append(mr)
    return ob.name

made = [
    ribbon("ME_WaveViolin_Ribbon_Scroll", "SOCKET_Scroll_Pommel", 0.34, 0.014, -1, 0.0, 0.024),
    ribbon("ME_WaveViolin_Ribbon_Tail",   "SOCKET_Tail_Deploy",   0.26, 0.011,  1, 2.1, 0.018),
]

# --- bead chain along waist: GN instance-on-curve over a catenary ---
old = bpy.data.objects.get("ME_WaveViolin_BeadChain")
if old: bpy.data.objects.remove(old, do_unlink=True)
cu = bpy.data.curves.new("ME_WaveViolin_BeadChain_curve", "CURVE")
cu.dimensions = "3D"; cu.resolution_u = 24
sp = cu.splines.new("BEZIER"); N = 9; sp.bezier_points.add(N-1)
for i, bp in enumerate(sp.bezier_points):
    t = i/(N-1)
    x = -0.13 + 0.26*t
    z = -0.05 - math.sin(t*math.pi)*0.05
    bp.co = Vector((x, -0.045, z))
    bp.handle_left_type = bp.handle_right_type = "AUTO"
chain = bpy.data.objects.new("ME_WaveViolin_BeadChain", cu)
bpy.data.collections["ME_WaveViolin_Ornament"].objects.link(chain)

bead_me = bpy.data.meshes.new("ME_WaveViolin_Bead")
import bmesh
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0075)
bm.to_mesh(bead_me); bm.free()
bead = bpy.data.objects.new("ME_WaveViolin_BeadProto", bead_me)
bead.hide_render = True; bead.hide_viewport = True
bpy.context.scene.collection.objects.link(bead)
# gem mat: may have been purged from the saved file if it had no users (Blender GC)
gem = bpy.data.materials.get("ME_MAT_Violin_DuskGem")
if gem is None:
    src = bpy.data.materials.get("ME_MAT_Violin_AmberNight")
    gem = src.copy(); gem.name = "ME_MAT_Violin_DuskGem"
    gp = next(n for n in gem.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    gp.inputs["Base Color"].default_value = (0.35, 0.16, 0.55, 1)
    gp.inputs["Roughness"].default_value = 0.12
    gp.inputs["Metallic"].default_value = 0.0
    ec = gp.inputs.get("Emission Color"); ei = gp.inputs.get("Emission Strength")
    if ec: ec.default_value = (0.5, 0.2, 0.8, 1)
    if ei: ei.default_value = 0.8
bead.data.materials.append(gem)

ng = bpy.data.node_groups.get("ME_Violin_BeadScatter")
if ng: bpy.data.node_groups.remove(ng)
ng = bpy.data.node_groups.new("ME_Violin_BeadScatter", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gin = ng.nodes.new("GeometryNodeObjectInfo"); gin.inputs[0].default_value = bead; gin.transform_space = 'ORIGINAL'
pts = ng.nodes.new("GeometryNodeCurveToPoints"); pts.mode = 'COUNT'; pts.inputs["Count"].default_value = 14
iop = ng.nodes.new("GeometryNodeInstanceOnPoints")
real = ng.nodes.new("GeometryNodeRealizeInstances")
gout = ng.nodes.new("NodeGroupOutput")
n_in = ng.nodes.new("NodeGroupInput")
ng.links.new(n_in.outputs["Geometry"], pts.inputs["Curve"])
ng.links.new(pts.outputs["Points"], iop.inputs["Points"])
ng.links.new(gin.outputs["Geometry"], iop.inputs["Instance"])
ng.links.new(iop.outputs["Instances"], real.inputs["Geometry"])
ng.links.new(real.outputs["Geometry"], gout.inputs["Geometry"])
md = chain.modifiers.new("ME_BeadScatter", "NODES"); md.node_group = ng

scn = bpy.context.scene
scn.render.filepath = os.path.join(OUT, "p05_hero.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_mainfile()
json.dump({"phase":"p05","ok":True,"ribbons":made,"beads":14,"plate":scn.render.filepath},
          open(os.path.join(OUT,"p05_report.json"),"w"), indent=1)
log("done")
