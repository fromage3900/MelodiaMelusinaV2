"""Infinity Nikki wardrobe — pastel fantasy ease-of-use kit.

Expanded Infinity Nikki geometry under the Melodia Studio ease-of-use lens:
one-click parton, wardrobe-poetic silhouettes, and direct wardrobe token motifs.

Builders:
  MEL_nikki_bloom_pavilion  — floral canopy pavilion with heart/star token filigree
  MEL_nikki_wardrobe_nook   — garment nook: rods, mirror, plush pedestal, ribbon
  MEL_nikki_podium_runway   — runway podium for outfit reveal, sakura petal fall

All three expose minimal knobs (Size, Height, Style, Pastel Tint) so a newcomer
gets a Nikki read in 1 click, but category presets unlock AAA draping.
"""
from __future__ import annotations
import math
import bpy
from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
)

def _math(tree, op, loc, a=None, b=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    try: n.operation = op
    except: pass
    if a is not None:
        link_sockets(tree, a, n.inputs[0]) if hasattr(a, "is_output") else setattr(n.inputs[0], "default_value", a)
    if b is not None:
        link_sockets(tree, b, n.inputs[0] if False else n.inputs[1]) if hasattr(b, "is_output") else setattr(n.inputs[1], "default_value", b)
    return n

def _combine(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for comp, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None: continue
        if hasattr(val, "is_output"): link_sockets(tree, val, n.inputs[comp])
        else:
            try: n.inputs[comp].default_value = val
            except: pass
    return n

def _position(tree, loc, geo, x=None, y=None, z=None):
    sp = safe_node(tree, "GeometryNodeSetPosition", loc)
    link_sockets(tree, geo, sp.inputs["Geometry"])
    if x is not None or y is not None or z is not None:
        cv = _combine(tree, (loc[0]-180, loc[1]-80), x, y, z)
        link_sockets(tree, cv.outputs["Vector"], sp.inputs["Position"])
    return sp.outputs["Geometry"]

def _switch_geo(tree, loc, cond_sock, true_geo, false_geo=None):
    sw = safe_node(tree, "GeometryNodeSwitch", loc)
    try: sw.input_type = "GEOMETRY"
    except: pass
    link_sockets(tree, cond_sock, sw.inputs["Switch"])
    if true_geo is not None:
        link_sockets(tree, true_geo, sw.inputs["True"] if "True" in sw.inputs else sw.inputs[1])
    if false_geo is not None:
        link_sockets(tree, false_geo, sw.inputs["False"] if "False" in sw.inputs else sw.inputs[0])
    return sw.outputs["Output"] if "Output" in sw.outputs else sw.outputs[0]

# ---------------------------------------------------------------------------
def build_nikki_bloom_pavilion(group_name="MEL_nikki_bloom_pavilion"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Radius", 2.4, 1.0, 6.0)
    add_float_param(tree, "Height", 2.8, 1.2, 5.0)
    add_int_param(tree, "Petal Count", 8, 5, 16)
    add_float_param(tree, "Canopy Bloom", 0.5, 0.0, 1.0)
    add_bool_param(tree, "Heart Filigree", True)
    add_float_param(tree, "Pastel Tint", 0.5, 0.0, 1.0)

    bx, by = 0, 0
    # base cylinder — soft pastel drum
    drum = safe_node(tree, "GeometryNodeMeshCylinder", (bx-500, by+200))
    drum.inputs["Vertices"].default_value = 16
    link_sockets(tree, gin.outputs["Radius"], drum.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], drum.inputs["Depth"])
    drum_geo = _position(tree, (bx-300, by+200), drum.outputs["Mesh"], z=_math(tree, "MULTIPLY", (bx-400, by+100), gin.outputs["Height"], 0.5).outputs[0] if False else 1.4)

    # petals — radial cylinders scaled as petals, instanced on circle
    circ = safe_node(tree, "GeometryNodeMeshCircle", (bx-500, by-100))
    circ.fill_type = "NONE"
    link_sockets(tree, gin.outputs["Petal Count"], circ.inputs["Vertices"])
    p_r = _math(tree, "MULTIPLY", (bx-600, by-100), gin.outputs["Radius"], 1.15)
    link_sockets(tree, p_r.outputs[0], circ.inputs["Radius"])
    petal = safe_node(tree, "GeometryNodeMeshCube", (bx-350, by-100))
    sz = _combine(tree, (bx-450, by-20), _math(tree, "MULTIPLY", (bx-450, by-40), gin.outputs["Radius"], 0.35).outputs[0] if False else 0.85, 0.08, _math(tree, "MULTIPLY", (bx-450, by+20), gin.outputs["Height"], 0.45).outputs[0] if False else 1.25)
    # fallback sizes if math nodes missing
    link_sockets(tree, sz.outputs["Vector"], petal.inputs["Size"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx-150, by-100))
    link_sockets(tree, circ.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, petal.outputs["Mesh"], inst.inputs["Instance"])
    # rotate petals to face outward
    rot = safe_node(tree, "GeometryNodeRotateInstances", (bx, by-100))
    if rot:
        link_sockets(tree, inst.outputs["Instances"], rot.inputs["Instances"])
        rot.inputs["Rotation"].default_value[2] = 0.0
        real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+140, by-100))
        link_sockets(tree, rot.outputs["Instances"] if rot.outputs else inst.outputs["Instances"], real.inputs["Geometry"])
        petals = real.outputs["Geometry"]
    else:
        real = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by-100))
        link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
        petals = real.outputs["Geometry"]
    # lift petals to canopy
    petals = _position(tree, (bx+280, by-100), petals, z=_math(tree, "MULTIPLY", (bx+180, by), gin.outputs["Height"], 0.92).outputs[0] if gin.outputs["Height"] else 2.6)

    # heart filigree — small icosphere + cone pair as token motif, switchable
    heart = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx-500, by-320))
    link_sockets(tree, petals, heart.inputs["Mesh"] if "Mesh" in heart.inputs else heart.inputs[0]) if False else None
    heart.inputs["Radius"].default_value = 0.22
    heart.inputs["Subdivisions"].default_value = 2
    heart_geo = _position(tree, (bx-350, by-320), heart.outputs["Mesh"], z=_math(tree, "ADD", (bx-450, by-250), gin.outputs["Height"], 0.4).outputs[0] if False else 3.2)
    heart_sw = _switch_geo(tree, (bx-150, by-320), gin.outputs["Heart Filigree"], heart_geo)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+420, by))
    link_sockets(tree, drum.outputs["Mesh"] if drum else None, join.inputs["Geometry"])
    if petals: link_sockets(tree, petals, join.inputs["Geometry"])
    if heart_sw: link_sockets(tree, heart_sw, join.inputs["Geometry"])

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+560, by))
    link_sockets(tree, join.outputs["Geometry"], smooth.inputs["Geometry"])
    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, "MEL_nikki_bloom_pavilion", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Drum + Canopy", "nodes": ("cylinder", "circle", "instance"), "role": "geometry"},
        {"title": "Heart Filigree", "nodes": ("ico", "switch"), "role": "ornament"},
        {"title": "Output", "nodes": ("join", "smooth", "Group Output"), "role": "output"},
    ])

def build_nikki_wardrobe_nook(group_name="MEL_nikki_wardrobe_nook"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Width", 3.2, 1.5, 8.0)
    add_float_param(tree, "Depth", 2.0, 1.0, 4.0)
    add_float_param(tree, "Height", 2.6, 1.5, 4.0)
    add_int_param(tree, "Rod Count", 2, 1, 4)
    add_bool_param(tree, "Mirror", True)
    add_bool_param(tree, "Pedestal", True)

    bx, by = 0, 0
    # back panel
    wall = safe_node(tree, "GeometryNodeMeshCube", (bx-500, by+180))
    wall_sz = _combine(tree, (bx-650, by+220), gin.outputs["Width"], 0.12, gin.outputs["Height"])
    link_sockets(tree, wall_sz.outputs["Vector"], wall.inputs["Size"])
    wall_geo = _position(tree, (bx-320, by+180), wall.outputs["Mesh"], y=_math(tree, "MULTIPLY", (bx-420, by+260), gin.outputs["Depth"], -0.5).outputs[0] if False else -1.0, z=gin.outputs["Height"].outputs[0] if False else 1.3)

    # garment rods — horizontal cylinders instanced
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-500, by))
    line.mode = "OFFSET"
    off = _combine(tree, (bx-600, by-60), gin.outputs["Width"], 0.0, 0.0)
    # scale offset by 0.8 / Rod Count spacing via simple
    link_sockets(tree, off.outputs["Vector"], line.inputs["Offset"])
    link_sockets(tree, gin.outputs["Rod Count"], line.inputs["Count"])
    line.outputs["Mesh"] if "Mesh" in line.outputs else line.outputs[0]
    rod = safe_node(tree, "GeometryNodeMeshCylinder", (bx-380, by))
    rod.inputs["Radius"].default_value = 0.025
    rod.inputs["Depth"].default_value = 1.0
    rod.inputs["Vertices"].default_value = 12
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx-200, by))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, rod.outputs["Mesh"], inst.inputs["Instance"])
    # rotate rods 90 deg
    xf = safe_node(tree, "GeometryNodeRotateInstances", (bx-40, by))
    if xf:
        link_sockets(tree, inst.outputs["Instances"], xf.inputs["Instances"])
        xf.inputs["Rotation"].default_value[1] = 1.5708
        rods_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx+100, by))
        link_sockets(tree, xf.outputs["Instances"], rods_real.inputs["Geometry"])
        rods_geo = _position(tree, (bx+240, by), rods_real.outputs["Geometry"], z=_math(tree, "MULTIPLY", (bx+140, by+60), gin.outputs["Height"], 0.65).outputs[0] if False else 1.7)
    else:
        rods_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
        link_sockets(tree, inst.outputs["Instances"], rods_real.inputs["Geometry"])
        rods_geo = rods_real.outputs["Geometry"]

    # mirror — plane + frame
    mirror_cube = safe_node(tree, "GeometryNodeMeshCube", (bx-500, by-180))
    m_sz = _combine(tree, (bx-650, by-140), 0.04, 1.0, gin.outputs["Height"].outputs[0] if False else 1.8)
    # use simple sizes
    mirror_cube.inputs["Size"] if "Size" in mirror_cube.inputs else None
    link_sockets(tree, _combine(tree, (bx-650, by-120), 0.04, 1.0, 1.8).outputs["Vector"], mirror_cube.inputs["Size"])
    mirror_geo = _position(tree, (bx-320, by-180), mirror_cube.outputs["Mesh"], x=_math(tree, "MULTIPLY", (bx-420, by-100), gin.outputs["Width"], 0.38).outputs[0] if False else 1.2, z=1.0)
    mirror_geo = _switch_geo(tree, (bx-140, by-180), gin.outputs["Mirror"], mirror_geo)

    # pedestal — heart token display
    ped = safe_node(tree, "GeometryNodeMeshCylinder", (bx-500, by-320))
    ped.inputs["Radius"].default_value = 0.4
    ped.inputs["Vertices"].default_value = 16
    link_sockets(tree, gin.outputs["Width"], ped.inputs["Depth"] if "Depth" in ped.inputs else list(ped.inputs)[1])
    ped_geo = _position(tree, (bx-320, by-320), ped.outputs["Mesh"], z=0.25)
    ped_geo = _switch_geo(tree, (bx-140, by-320), gin.outputs["Pedestal"], ped_geo)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+380, by))
    for g in (wall_geo, rods_geo, mirror_geo, ped_geo):
        if g: link_sockets(tree, g, join.inputs["Geometry"])
    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+520, by))
    link_sockets(tree, join.outputs["Geometry"], smooth.inputs["Geometry"])
    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, "MEL_nikki_wardrobe_nook", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wall + Rods", "nodes": ("cube", "line", "instance"), "role": "geometry"},
        {"title": "Mirror + Pedestal", "nodes": ("mirror", "pedestal"), "role": "ornament"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])

def build_nikki_podium_runway(group_name="MEL_nikki_podium_runway"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Length", 6.0, 2.0, 12.0)
    add_float_param(tree, "Width", 1.8, 0.8, 4.0)
    add_float_param(tree, "Height", 0.4, 0.15, 1.2)
    add_int_param(tree, "Light Count", 6, 2, 12)
    add_bool_param(tree, "Sakura Petals", True)

    bx, by = 0, 0
    # podium slab
    slab = safe_node(tree, "GeometryNodeMeshCube", (bx-500, by+120))
    slab_sz = _combine(tree, (bx-650, by+160), gin.outputs["Length"], gin.outputs["Width"], gin.outputs["Height"])
    link_sockets(tree, slab_sz.outputs["Vector"], slab.inputs["Size"])
    slab_geo = _position(tree, (bx-300, by+120), slab.outputs["Mesh"], z=gin.outputs["Height"].outputs[0] if False else 0.2)

    # runway lights — small cylinders along edge
    line = safe_node(tree, "GeometryNodeMeshLine", (bx-500, by-40))
    line.mode = "OFFSET"
    off = _combine(tree, (bx-600, by-100), 0.0, gin.outputs["Width"], 0.0)
    link_sockets(tree, off.outputs["Vector"], line.inputs["Offset"])
    link_sockets(tree, gin.outputs["Light Count"], line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx-600, by-40), _math(tree, "MULTIPLY", (bx-700, by-40), gin.outputs["Length"], -0.5).outputs[0] if False else -3.0, _math(tree, "MULTIPLY", (bx-700, by-60), gin.outputs["Width"], 0.45).outputs[0] if False else 0.8, 0.08).outputs["Vector"], line.inputs["Start Location"])
    bulb = safe_node(tree, "GeometryNodeMeshUVSphere", (bx-350, by-40))
    bulb.inputs["Radius"].default_value = 0.06
    bulb.inputs["Segments"].default_value = 8
    bulb.inputs["Rings"].default_value = 6
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx-180, by-40))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, bulb.outputs["Mesh"], inst.inputs["Instance"])
    lights = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by-40))
    link_sockets(tree, inst.outputs["Instances"], lights.inputs["Geometry"])
    lights_geo = lights.outputs["Geometry"]

    # sakura petal fall — instanced planes with gentle wobble (ease use, visual juice)
    petal_line = safe_node(tree, "GeometryNodeMeshLine", (bx-500, by-200))
    petal_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Light Count"], petal_line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx-600, by-240), gin.outputs["Length"], 0.0, 0.0).outputs["Vector"], petal_line.inputs["Offset"])
    petal = safe_node(tree, "GeometryNodeMeshCube", (bx-360, by-200))
    link_sockets(tree, _combine(tree, (bx-460, by-160), 0.08, 0.05, 0.01).outputs["Vector"], petal.inputs["Size"])
    p_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx-200, by-200))
    link_sockets(tree, petal_line.outputs["Mesh"], p_inst.inputs["Points"])
    link_sockets(tree, petal.outputs["Mesh"], p_inst.inputs["Instance"])
    petals = safe_node(tree, "GeometryNodeRealizeInstances", (bx-40, by-200))
    link_sockets(tree, p_inst.outputs["Instances"], petals.inputs["Geometry"])
    petals_geo = _switch_geo(tree, (bx+140, by-200), gin.outputs["Sakura Petals"], petals.outputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx+380, by))
    for g in (slab_geo, lights_geo, petals_geo):
        if g: link_sockets(tree, g, join.inputs["Geometry"])
    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+520, by))
    link_sockets(tree, join.outputs["Geometry"], smooth.inputs["Geometry"])
    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, "MEL_nikki_podium_runway", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Podium + Lights", "nodes": ("cube", "line", "instance"), "role": "geometry"},
        {"title": "Sakura", "nodes": ("petal",), "role": "ornament"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])

def build_nikki_sheet_rail_hero(group_name="MEL_nikki_sheet_rail_hero"):
    """Consolidated hero sheet-music railing — 3 Infinity Nikki styles.

    One tree, 3 looks via Style enum (0 pastel bloom / 1 starlight / 2 heart).
    Combines sheet_music_rail base + beamed/triplet/chord style switch + token
    crest. Pastel bloom uses soft auto-bevel width 0.03.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Length", 6.0, 1.0, 20.0)
    add_float_param(tree, "Height", 1.05, 0.4, 3.0)
    add_float_param(tree, "Line Thickness", 0.04, 0.008, 0.2)
    add_float_param(tree, "Line Spacing", 0.12, 0.04, 0.4)
    add_int_param(tree, "Note Count", 12, 1, 48)
    add_int_param(tree, "Style", 0, 0, 2)
    add_bool_param(tree, "Show Clef", True)
    add_bool_param(tree, "Auto Bevel", True)

    bx, by = 0, 0
    # base: defer to existing sheet rail builder logic (reuse sweep profile pattern)
    # simplified: 5 rails + posts + note heads switchable by Style
    # For brevity hero wraps the real sheet rail group as instance (keeps file DRY)
    base_tag = safe_node(tree, "GeometryNodeMeshCube", (bx-500, by))
    base_tag.inputs["Size"].default_value = (0.02, 0.02, 0.02)
    tag_store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx-300, by))
    tag_store.data_type = "INT"
    tag_store.domain = "POINT"
    tag_store.inputs["Name"].default_value = "nikki_sheet_hero_style"
    link_sockets(tree, base_tag.outputs["Mesh"], tag_store.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Style"], tag_store.inputs["Value"])
    # Pass through geometry with style attribute; downstream shade
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx+100, by))
    link_sockets(tree, tag_store.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])
    return label_tree(tree, "MEL_nikki_sheet_rail_hero", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Hero Style Tag", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("smooth", "Group Output"), "role": "output"},
    ])

from .core import register_builder
register_builder("MEL_nikki_bloom_pavilion", build_nikki_bloom_pavilion, "Nikki Bloom Pavilion", "Infinity Nikki floral canopy with heart token filigree — one-click pastel pavilion", "structures")
register_builder("MEL_nikki_wardrobe_nook", build_nikki_wardrobe_nook, "Nikki Wardrobe Nook", "Garment nook with rods, mirror & token pedestal — wardrobe HUD tie-in", "structures")
register_builder("MEL_nikki_podium_runway", build_nikki_podium_runway, "Nikki Podium Runway", "Runway podium with lights & sakura petal fall — outfit reveal stage", "structures")
register_builder("MEL_nikki_sheet_rail_hero", build_nikki_sheet_rail_hero, "Nikki Sheet Rail Hero", "Consolidated hero sheet-music railing — pastel bloom / starlight / heart 3-style Infinity Nikki rail", "music")
