"""V7 base: final assembled Melusina House base staged live via addon builders.
Cells shell-only (Show Roof=False); roofs via monolith _build_curved_roof authority.
"""
import bpy, sys, math, mathutils

sys.path.insert(0, r"C:\Users\brenn\AppData\Roaming\Blender Foundation\Blender\5.2\scripts\addons")
import surreal_arch.melodia_gn  # registers all 268 builders
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
import importlib
sa = importlib.import_module("surreal_architecture_gen")

bpy.ops.wm.read_factory_settings(use_empty=True)
# register the monolith addon so surreal_arch_props exists (roofs need it)
try:
    bpy.ops.preferences.addon_enable(module="surreal_architecture_gen")
except Exception as e:
    print("ADDON_ENABLE_FAIL", e)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"

for name in ("MH_GN_OUTPUT", "MH_ROOFS", "MH_SETDRESS", "MH_LIGHTING", "MH_CAMS", "MH_EXPORT"):
    c = bpy.data.collections.new(name)
    sc.collection.children.link(c)
out_coll = bpy.data.collections["MH_GN_OUTPUT"]
roof_coll = bpy.data.collections["MH_ROOFS"]
dress = bpy.data.collections["MH_SETDRESS"]
built = {}

def build_and_place(bname, objname, loc, params=None, scale=None, coll=None):
    fn = GROUP_BUILDERS[bname]
    result = fn()
    tree = result[0] if isinstance(result, tuple) else result
    tree.name = objname + "_TREE"
    if params:
        for item in tree.interface.items_tree:
            if item.in_out == 'INPUT' and item.name in params and hasattr(item, 'default_value'):
                try:
                    item.default_value = params[item.name]
                except Exception as e:
                    print("PARAMFAIL", objname, item.name, e)
    ob = bpy.data.objects.new(objname, bpy.data.meshes.new(objname))
    (coll or out_coll).objects.link(ob)
    mod = ob.modifiers.new(objname, 'NODES')
    mod.node_group = tree
    ob.location = loc
    if scale:
        ob.scale = scale
    built[objname] = ob
    print("PLACED", objname)
    return ob

def add_roof(objname, cx, cy, z, w, d, rise, overhang=0.45, curve=0.25, coll=None):
    ob = bpy.data.objects.new(objname, bpy.data.meshes.new(objname))
    (coll or roof_coll).objects.link(ob)
    p = ob.surreal_arch_props
    p.roof_type = 'HIP'
    p.roof_span = w; p.roof_depth = d; p.roof_rise = rise
    p.roof_eave_overhang = overhang; p.roof_eave_curve = curve
    p.roof_segments = 24; p.roof_thickness = 0.08
    sa._build_curved_roof(ob, p)
    sa._add_roof_modifier_stack(ob, p)
    ob.name = f"SurrealRoof_HIP_{objname}"
    ob.location = (cx, cy, z)
    built[ob.name] = ob
    print("ROOF", ob.name)
    return ob

# ---- U-shaped massing (shell-only cells) ----
CELLS = [
    ("MH_Cell_Core",      (0.0, 0.0, 0.0),   {"Width": 7.0, "Depth": 5.5, "Height": 6.8, "Roof Rise": 2.6, "Show Roof": False, "Show Interior": True}),
    ("MH_Cell_LeftWing",  (-6.2, 0.6, 0.0),  {"Width": 4.8, "Depth": 4.2, "Height": 3.4, "Roof Rise": 1.4, "Show Roof": False, "Show Interior": True}),
    ("MH_Cell_Rear",      (1.8, -4.6, 0.0),  {"Width": 4.2, "Depth": 4.2, "Height": 4.6, "Roof Rise": 1.8, "Tower": True, "Show Roof": False, "Show Interior": True}),
]
for objname, loc, params in CELLS:
    build_and_place("MEL_city_house_cell", objname, loc, params)

# ---- Roofs via monolith authority ----
add_roof("Roof_Core",     0.0, 0.0, 6.8, 7.0, 5.5, 2.6)
add_roof("Roof_LeftWing", -6.2, 0.6, 3.4, 4.8, 4.2, 1.4)
add_roof("Roof_Rear",     1.8, -4.6, 4.6, 4.2, 4.2, 1.8)

# ---- Set dressing (musical identity) ----
build_and_place("MEL_music_baroque_organ", "MH_Organ", (8.2, 3.5, 0), None, None, dress)
build_and_place("MEL_mh_piano_walk", "MH_PianoWalk", (0, 7.5, 0), {"Key Count": 24, "Length": 8.0}, None, dress)
build_and_place("MEL_mh_sheet_rail", "MH_SheetRail", (-2.5, 7.2, 0), None, None, dress)
build_and_place("MEL_mh_lantern_row", "MH_Lanterns", (4.5, 6.5, 0), None, None, dress)
build_and_place("MEL_mh_tree_line", "MH_Trees", (-8.5, -4.0, 0), None, (0.9, 0.9, 0.9), dress)
build_and_place("MEL_allee_ribbon", "MH_Allee", (0, 11.0, 0), {"Length": 12.0, "Path Width": 2.4, "S-Curve": 1.2}, None, dress)

# ---- Cornice + pearl garland ----
build_and_place("MEL_mh_aaa_cornice", "MH_Cornice", (0, 0, 6.35),
                {"Ring Radius": 3.3, "Profile Radius": 0.07, "Band Rise": 0.12, "Band Spread": 0.05})
build_and_place("MEL_mh_aaa_lissajous_pearl", "MH_Pearls", (0, 2.9, 2.9),
                {"Freq X": 2.0, "Freq Y": 3.0, "Freq Z": 1.0, "Radius": 0.45, "Pearl Count": 80}, None, dress)

# ---- Palette materials (melusinashouseplan anchors) ----
def palette(name, rgb, rough=0.8, metal=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat

m_plaster = palette("M_MH_PearlPlaster_Pink", (0.968, 0.839, 0.906), rough=0.85)   # #F7D6E7
m_roof    = palette("M_MH_Roof_IridescentBlue", (0.431, 0.541, 0.686), rough=0.5)  # #6E8AAF
m_gold    = palette("M_MH_GoldBrass", (0.776, 0.631, 0.353), rough=0.35, metal=0.85)  # #C6A15A
for cellname in ("MH_Cell_Core", "MH_Cell_LeftWing", "MH_Cell_Rear"):
    ob = built[cellname]
    for i in range(len(ob.data.materials)):
        ob.data.materials[i] = m_plaster
for roofname, ob in built.items():
    if roofname.startswith("SurrealRoof"):
        ob.data.materials.clear()
        ob.data.materials.append(m_roof)
built["MH_Cornice"].data.materials.clear()
built["MH_Cornice"].data.materials.append(m_gold)

# ---- Ground ----
bpy.ops.mesh.primitive_circle_add(radius=14.0, vertices=96, fill_type='NGON', location=(0, 0, -0.04))
ground = bpy.context.active_object
ground.name = "MH_Ground"
ground.users_collection[0].objects.unlink(ground)
out_coll.objects.link(ground)
m = bpy.data.materials.new("MH6_StoneGround"); m.use_nodes = True
b = m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.42, 0.44, 0.48, 1)
b.inputs["Roughness"].default_value = 0.9
ground.data.materials.append(m)

# ---- World/lights/cam ----
w = bpy.data.worlds.new("W7"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.55, 0.75, 1.0)
sun = bpy.data.objects.new("SunKey", bpy.data.lights.new("SunKey", 'SUN'))
sun.data.energy = 4.0; sun.rotation_euler = (0.85, 0.15, 0.65)
bpy.data.collections["MH_LIGHTING"].objects.link(sun)
fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", 'AREA'))
fill.data.energy = 600; fill.data.size = 12; fill.location = (-8, -6, 7)
d2 = mathutils.Vector((0, 0, 2)) - fill.location
fill.rotation_euler = d2.to_track_quat('-Z', 'Y').to_euler()
bpy.data.collections["MH_LIGHTING"].objects.link(fill)
cam = bpy.data.objects.new("CAM_Hero", bpy.data.cameras.new("CAM_Hero"))
cam.location = (16.0, -15.0, 8.0)
d = mathutils.Vector((0, 0, 2.4)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 32
bpy.data.collections["MH_CAMS"].objects.link(cam)
sc.camera = cam

# ---- Eval + verify ----
def realize_tree(name):
    rt = bpy.data.node_groups.new(name, "GeometryNodeTree")
    rin = rt.nodes.new("NodeGroupInput"); rout = rt.nodes.new("NodeGroupOutput")
    rz = rt.nodes.new("GeometryNodeRealizeInstances")
    rt.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    rt.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    rt.links.new(rin.outputs[0], rz.inputs["Geometry"])
    rt.links.new(rz.outputs["Geometry"], rout.inputs[0])
    return rt

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
total = 0
fails = []
for name, ob in built.items():
    ev = ob.evaluated_get(dg)
    v = len(ev.data.vertices) if ev.data else 0
    if v == 0:
        # live-instance builder: count through a realize chain
        rz = ob.modifiers.new(name + "_rz", 'NODES')
        rz.node_group = realize_tree(name + "_rztree")
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        v = len(ev.data.vertices) if ev.data else 0
    total += v
    if v == 0:
        fails.append(name)
    print("EVAL", name, v)
print("TOTAL_VERTS", total)
print("EMPTY", fails)

# contact render
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1280; sc.render.resolution_y = 720
sc.render.filepath = r"C:\Users\brenn\melodiamelusinav2\Saved\Audit\melusinashouse\v7_base_hero.png"
bpy.ops.render.render(write_still=True)
print("RENDER_DONE")

bpy.ops.wm.save_as_mainfile(filepath=r"C:\Users\brenn\melodiamelusinav2\Saved\MelusinasHouse\MelusinasHouse_V7_Base.blend")
print("SAVED_OK")
