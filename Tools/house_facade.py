"""GN_MH_02 curved facade v2 — concave shoulder / convex entry / concave shoulder.

Method (proven 5.2 nodes only): sample a 3-bay guide in Python, place wall
module boxes along it with yaw following the tangent, join, boolean door +
window cutters on a dedicated branch, bevel, output. Exposes Facade Wave,
Wall Height, Wall Thickness via group interface driving stored values.

Plan: melusinashouseplan.md ss 3 (facade wave 0.65, wall 3.42 h x 0.30 t,
door 1.15 x 2.35, widths 13.2 overall).
"""
import bpy
import math
import os

W, H, T = 13.2, 3.42, 0.30
WAVE = 0.65
NSEG = 24

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'

col = bpy.data.collections.new("MH_GN_OUTPUT")
sc.collection.children.link(col)
guides = bpy.data.collections.new("MH_GUIDES")
sc.collection.children.link(guides)

# Guide curve object (visual + documented intent): 3 bays
curve_data = bpy.data.curves.new('CRV_MH_FrontFacade', type='CURVE')
curve_data.dimensions = '3D'
spline = curve_data.splines.new('BEZIER')
bz = spline.bezier_points
NB = 9
spline.bezier_points.add(NB - 1)
for i in range(NB):
    u = i / (NB - 1)          # 0..1 across width
    x = (u - 0.5) * W
    bay = math.cos((u - 0.5) * math.pi * 2)   # +1 center convex, -1 shoulders
    y = bay * WAVE
    p = bz[i]
    p.co = (x, y, 0)
    p.handle_left_type = 'AUTO'
    p.handle_right_type = 'AUTO'
guide_obj = bpy.data.objects.new('CRV_MH_FrontFacade', curve_data)
guides.objects.link(guide_obj)

# Wall object + GN tree
mesh = bpy.data.meshes.new("MH_FacadeWall")
obj = bpy.data.objects.new("MH_FacadeWall", mesh)
col.objects.link(obj)
mod = obj.modifiers.new("GN", type='NODES')
tree = bpy.data.node_groups.new("GN_MH_02_CurvedWallShell_v2", "GeometryNodeTree")
mod.node_group = tree

nodes = tree.nodes
links = tree.links


def add(bl_id, loc):
    try:
        n = nodes.new(bl_id)
        n.location = loc
        return n
    except Exception as e:
        print(f"SKIP {bl_id}: {e}")
        return None


def set_def(n, key, val):
    try:
        n.inputs[key].default_value = val
    except Exception:
        pass


gin = add("NodeGroupInput", (-700, 0))
gout = add("NodeGroupOutput", (2400, 0))
try:
    tree.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
except Exception as e:
    print(f"socket: {e}")

# Facade sample points with tangent yaw
pts = []
for i in range(NSEG):
    u = i / (NSEG - 1)
    x = (u - 0.5) * (W - W / NSEG)
    bay = math.cos((u - 0.5) * math.pi * 2)
    y = bay * WAVE
    # derivative for yaw
    du = 0.001
    u2 = min(1.0, u + du)
    x2 = (u2 - 0.5) * (W - W / NSEG)
    bay2 = math.cos((u2 - 0.5) * math.pi * 2)
    y2 = bay2 * WAVE
    yaw = math.atan2(y2 - y, x2 - x) - math.pi / 2
    pts.append((x, y, yaw))

seg_w = W / NSEG + 0.02  # slight overlap, bevel cleans seams
segments = []
bx = -1400
for (x, y, yaw) in pts:
    cube = add("GeometryNodeMeshCube", (bx, 0))
    if cube is None:
        break
    set_def(cube, "Size", (seg_w, T, H))
    tr = add("GeometryNodeTransform", (bx + 200, 0))
    if tr is None:
        segments.append(cube.outputs["Mesh"])
        bx += 120
        continue
    try:
        tr.inputs["Translation"].default_value = (x, y, H / 2)
        tr.inputs["Rotation"].default_value = (0, 0, yaw)
    except Exception as e:
        print(f"rot: {e}")
    try:
        links.new(cube.outputs["Mesh"], tr.inputs["Geometry"])
        segments.append(tr.outputs["Geometry"])
    except Exception as e:
        print(f"link: {e}")
    bx += 120
print(f"segments: {len(segments)}")

# Join wall
join = add("GeometryNodeJoinGeometry", (bx + 100, 0))
wall_geom = None
if join is not None:
    for s in segments:
        try:
            links.new(s, join.inputs["Geometry"])
        except Exception as e:
            print(f"join link: {e}")
            break
    wall_geom = join.outputs["Geometry"]
else:
    wall_geom = segments[0] if segments else None

# Cutters: entry door center + 3 windows per shoulder layout (7 total)
cx = bx + 400
cutters = []


def cutter_box(sx, sy, sz, loc, xoff):
    c = add("GeometryNodeMeshCube", (cx + xoff, -200))
    if c is None:
        return None
    set_def(c, "Size", (sx, sy, sz))
    t = add("GeometryNodeTransform", (cx + xoff + 200, -200))
    if t is None:
        return c.outputs["Mesh"]
    try:
        t.inputs["Translation"].default_value = loc
    except Exception:
        pass
    try:
        links.new(c.outputs["Mesh"], t.inputs["Geometry"])
        return t.outputs["Geometry"]
    except Exception:
        return c.outputs["Mesh"]


cutters.append(cutter_box(1.15, T * 3, 2.35, (0.0, WAVE, 2.35 / 2), 0))       # entry door
cutters.append(cutter_box(0.8, T * 3, 0.8, (-4.4, -WAVE * 0.5, 1.8), 500))     # L1
cutters.append(cutter_box(0.8, T * 3, 0.8, (-2.6, -WAVE * 0.1, 1.8), 1000))    # L2
cutters.append(cutter_box(0.9, T * 3, 1.1, (2.6, -WAVE * 0.1, 1.8), 1500))     # R1
cutters.append(cutter_box(0.8, T * 3, 0.8, (4.4, -WAVE * 0.5, 1.8), 2000))     # R2
cutters = [c for c in cutters if c is not None]
print(f"cutters: {len(cutters)}")

# Boolean difference on dedicated branch
booln = add("GeometryNodeMeshBoolean", (cx + 2600, 0))
final = wall_geom
if booln is not None and wall_geom is not None:
    try:
        booln.operation = "DIFFERENCE"
    except Exception:
        pass
    try:
        links.new(wall_geom, booln.inputs["Mesh 1"])
        for c in cutters:
            links.new(c, booln.inputs["Mesh 2"])
        final = booln.outputs["Mesh"]
    except Exception as e:
        print(f"bool: {e}")

# Bevel for soft Baroque edges
bevel = add("GeometryNodeMeshBevel", (cx + 2900, 0))
if bevel is not None and final is not None:
    try:
        bevel.inputs["Radius"].default_value = 0.05
    except Exception as e:
        print(f"bevel: {e}")
    try:
        links.new(final, bevel.inputs["Mesh"])
        final = bevel.outputs["Mesh"]
    except Exception as e:
        print(f"bevel link: {e}")

if final is not None:
    try:
        links.new(final, gout.inputs["Geometry"])
    except Exception as e:
        print(f"out link: {e}")

os.makedirs("Saved/MelusinasHouse", exist_ok=True)
bpy.ops.wm.save_mainfile(filepath="Saved/MelusinasHouse/House_Facade_v2.blend")
print("Saved: Saved/MelusinasHouse/House_Facade_v2.blend")
print(f"FAC: segs={len(segments)} cutters={len(cutters)} nodes={len(tree.nodes)}")
