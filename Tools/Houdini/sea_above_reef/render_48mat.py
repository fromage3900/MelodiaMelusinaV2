"""Visual proof for the 48-slot dress: each material slot gets a distinct pastel,
then a 3/4 render. Opens Shorewake_48MAT.blend, renders, does not overwrite it.
Run:  blender -b --factory-startup -noaudio --python render_48mat.py
"""
import colorsys
from pathlib import Path

import bpy

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BLEND = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/Shorewake_48MAT.blend"
OUT = PROJECT_ROOT / "Saved/Audit/sea_above/renders/skiff/SHOREWAKE_48MAT_SLOTS.png"

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene
# 5.2 compositing lives in a node GROUP (scene.node_tree is gone in 5.2):
# the USD import left a graph that renders uniform white over everything
comp_group = getattr(scene, "compositor_node_group", None)
if comp_group:
    print(f"[48mat-qa] compositor group '{comp_group.name}' nodes: "
          f"{[n.type for n in comp_group.nodes]}")
    for n in list(comp_group.nodes):
        comp_group.nodes.remove(n)
    scene.compositor_node_group = None
elif hasattr(scene, "node_tree") and scene.node_tree:
    print(f"[48mat-qa] legacy comp nodes: {[n.type for n in scene.node_tree.nodes]}")
    for n in list(scene.node_tree.nodes):
        scene.node_tree.nodes.remove(n)
# the USD import leaves stray root objects (e.g. 'melusinashorewake', 'Looks') -
# a full white duplicate of the dress sits in front of the slotted mesh otherwise
strays = [o for o in bpy.data.objects
          if o.name != "SM_ShorewakeDress_48MAT" and o.type in ("MESH", "EMPTY")]
stray_names = [o.name for o in strays]      # capture BEFORE removal
for o in strays:
    bpy.data.objects.remove(o, do_unlink=True)
print(f"[48mat-qa] removed {len(strays)} stray objects: {stray_names[:6]}")
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.render.resolution_x = 900
scene.render.resolution_y = 1200

dress = bpy.data.objects.get("SM_ShorewakeDress_48MAT")
assert dress, "slotted dress object not found"

hues = [i / 48.0 for i in range(48)]
# KEY: recolor through the OBJECT's material slots. The USD import links
# materials to the OBJECT, so mesh-datablock recolors are invisible to renders
print(f"[48mat-qa] slot links: "
      f"{[s.link for s in dress.material_slots][:5]} "
      f"(object-linked slots override mesh datablocks)")
for slot_idx, slot in enumerate(dress.material_slots):
    mat = slot.material
    if mat is None:
        continue
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    # USDZ-imported materials don't use a node literally named "Principled BSDF"
    # (the silent-skip bug) - rebuild the graph deterministically instead
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    h = hues[slot_idx % 48]
    c = colorsys.hsv_to_rgb(h, 0.70, 0.85)
    bsdf.inputs["Base Color"].default_value = (*c, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Metallic"].default_value = 0.0
# render-time evidence: what do the first 3 materials actually contain?
for mi in range(3):
    m = dress.data.materials[mi]
    types = [n.type for n in m.node_tree.nodes] if m.use_nodes else "NO_NODES"
    pb = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) \
        if m.use_nodes else None
    bc = list(pb.inputs["Base Color"].default_value) if pb else None
    em = round(pb.inputs["Emission Strength"].default_value, 2) if pb and \
        "Emission Strength" in pb.inputs else "n/a"
    mt = round(pb.inputs["Metallic"].default_value, 2) if pb and \
        "Metallic" in pb.inputs else "n/a"
    print(f"[48mat-qa] slot{mi}: {m.name} nodes={types} base={bc} "
          f"metallic={mt} emission={em}")

bpy.ops.object.select_all(action="DESELECT")
dress.select_set(True)
bpy.context.view_layer.objects.active = dress
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode="OBJECT")

# camera: high 3/4 over the flat layout
lo = Vector((1e9,) * 3) if False else None
from mathutils import Vector
lo = Vector((1e9,) * 3)
hi = Vector((-1e9,) * 3)
for c in dress.bound_box:
    w = dress.matrix_world @ Vector(c)
    lo = Vector(map(min, lo, w))
    hi = Vector(map(max, hi, w))
center = (lo + hi) / 2.0
diag = max((hi - lo).length, 1.0)
data = bpy.data.cameras.new("QA")
data.lens = 50
data.clip_end = 1e7
cam = bpy.data.objects.new("QA", data)
cam.location = center + Vector((0.35, -0.85, 1.15)).normalized() * diag * 0.9
bpy.context.collection.objects.link(cam)
tgt = bpy.data.objects.new("QA_T", None)
tgt.location = center
bpy.context.collection.objects.link(tgt)
cc = cam.constraints.new("TRACK_TO")
cc.target = tgt
scene.camera = cam

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.05, 0.055, 0.07, 1.0)
scene.view_settings.exposure = -1.0        # first pass blew out to white
try:
    scene.view_settings.view_transform = "Standard"   # AgX desaturates the pastels
except Exception:
    pass
for lname, loc, col, e in (("K", (2, -3, 4), (1.0, 0.9, 0.75), 3000.0),
                           ("F", (-3, -1.5, 1.5), (0.5, 0.85, 0.9), 1500.0),
                           ("R", (1, 2.5, 2), (0.75, 0.88, 1.0), 1800.0)):
    ld = bpy.data.lights.new(lname, "AREA")
    ld.energy = e
    ld.color = col
    ld.size = diag * 0.5
    lo2 = bpy.data.objects.new(lname, ld)
    lo2.location = center + Vector(loc).normalized() * diag * 0.8
    bpy.context.collection.objects.link(lo2)

scene.render.filepath = str(OUT)
# DECISIVE STATE DUMP before rendering
print("[dbg] scene:", scene.name, "| use_nodes(compo):", scene.use_nodes,
      "| view:", scene.view_settings.view_transform,
      "| exposure:", scene.view_settings.exposure)
print("[dbg] dress: holdout=", getattr(dress, "is_holdout", "n/a"),
      "visible_camera=", getattr(dress, "visible_camera", "n/a"),
      "mats:", len(dress.data.materials), "slots:", len(dress.material_slots))
print("[dbg] world bg:", list(bg.inputs[0].default_value),
      "strength:", round(float(bg.inputs[1].default_value), 3))
print("[dbg] mesh objects in scene:",
      [o.name for o in bpy.data.objects if o.type == "MESH"])
mat0 = dress.data.materials[0]
if mat0 and mat0.use_nodes:
    for n in mat0.node_tree.nodes:
        insp = {}
        for i in n.inputs:
            try:
                dv = i.default_value
                insp[i.name] = list(dv) if hasattr(dv, "__len__") else round(float(dv), 3)
            except Exception:
                insp[i.name] = "?"
        print(f"[dbg] mat0 node {n.type}: {insp}")
bpy.ops.render.render(write_still=True)
print(f"[48mat-qa] render -> {OUT.name} ({len(dress.data.materials)} colored slots)")
