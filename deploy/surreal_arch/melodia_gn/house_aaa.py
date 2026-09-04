"""AAA hard-surface house kit - Blender 5.2 flagship GN workflows.

Four builders targeting the Melusina house overhaul, written against the
probed 5.2 node set:

- MEL_mh_aaa_cornice      CurvePrimitiveCircle sweeps (bed mould / corona /
                  fillet stack) + Mesh Bevel hard-surface articulation
- MEL_mh_aaa_dentil       Repeat Zone dentil row (index-socket wiring),
                  graceful fallback to Instance on Points
- MEL_mh_aaa_scallop_uv   UV-space shingle projection: grid -> Sample UV
                  Surface (Value=Position) -> Set Position -> 5-variant
                  scallop family picked per point
- MEL_mh_aaa_lissajous_pearl  Lissajous curve from sine math nodes ->
                  MeshToCurve -> CurveToPoints pearl string

All builders return (tree, gin, gout) and register via register_builder.

5.2 socket ground truth (probed 2026-09-03):
  GeometryNodeCurvePrimitiveCircle IN[Resolution,Point1..3,Radius] OUT[Curve,Center]
  GeometryNodeSampleUVSurface IN[Mesh,Value,UV Map,Sample UV] OUT[Value,Is Valid]
  GeometryNodeMeshLine IN[Count,Resolution,Start Location,Offset] OUT[Mesh]
  GeometryNodeRepeatInput IN[Iterations,geometry] OUT[Iteration,geometry]
  GeometryNodeMeshGrid OUT[Mesh,UV Map]
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder,
)
from .house_dress import _ensure_material, _ensure_all_materials


def _bevel(tree, loc, geom_sock, width=0.01, segments=2):
    n = safe_node(tree, "GeometryNodeMeshBevel", loc)
    if n is None:
        return geom_sock
    try:
        n.inputs["Width"].default_value = width
        n.inputs["Segments"].default_value = segments
    except Exception:
        pass
    link_sockets(tree, geom_sock, n.inputs["Mesh"])
    return n.outputs[0]


def _setmat(tree, loc, geometry, material):
    if geometry is None or material is None:
        return geometry
    sm = safe_node(tree, "GeometryNodeSetMaterial", loc)
    try:
        sm.inputs["Material"].default_value = material
    except Exception:
        pass
    link_sockets(tree, geometry, sm.inputs[0])
    return sm.outputs[0]


def _xf(tree, loc, geom_sock, scale=None, translation=None):
    n = safe_node(tree, "GeometryNodeTransform", loc)
    if scale is not None:
        try:
            n.inputs["Scale"].default_value = scale
        except Exception:
            pass
    if translation is not None:
        try:
            n.inputs["Translation"].default_value = translation
        except Exception:
            pass
    link_sockets(tree, geom_sock, n.inputs["Geometry"])
    return n.outputs[0]


def _param_v3(tree, loc, sock, axis):
    """Broadcast a float param socket into one axis of a Combine XYZ."""
    comb = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    try:
        link_sockets(tree, sock, comb.inputs[axis])
    except Exception:
        pass
    return comb.outputs[0]


# ---------------------------------------------------------------------------
# 1. Cornice ring: three concentric torus-band sweeps at stacked heights
# ---------------------------------------------------------------------------

def build_mh_aaa_cornice(group_name="MEL_mh_aaa_cornice"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Ring Radius", 6.0, 0.5, 40.0)
    add_float_param(tree, "Profile Radius", 0.09, 0.02, 0.5)
    add_float_param(tree, "Band Rise", 0.14, 0.0, 1.0)
    add_float_param(tree, "Band Spread", 0.06, 0.0, 1.0)

    _ensure_all_materials()
    gold = bpy.data.materials.get("MH_GoldBrass")
    plaster = bpy.data.materials.get("MH_PearlPlaster")

    # profile circle (shared, small)
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-200, 0))
    try:
        prof.inputs["Resolution"].default_value = 12
        link_sockets(tree, gin.outputs["Profile Radius"], prof.inputs["Radius"])
    except Exception:
        pass
    prof_sock = prof.outputs["Curve"]

    parts = []
    # three bands: fillet (top, gold, widest), corona (mid, plaster), bed (base)
    for i, (zmul, rmul, mat) in enumerate([
        (2.0, 1.15, gold),
        (1.0, 1.35, plaster),
        (0.0, 1.0, plaster),
    ]):
        ring = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (0, i * 220))
        try:
            ring.inputs["Resolution"].default_value = 96
        except Exception:
            pass
        # radius = Ring Radius + rmul*Band Spread
        base = safe_node(tree, "ShaderNodeMath", (0, i * 220 - 120))
        try:
            base.operation = 'MULTIPLY'
            base.inputs[1].default_value = rmul
            link_sockets(tree, gin.outputs["Band Spread"], base.inputs[0])
            addn = safe_node(tree, "ShaderNodeMath", (140, i * 220 - 120))
            addn.operation = 'ADD'
            link_sockets(tree, base.outputs[0], addn.inputs[0])
            link_sockets(tree, gin.outputs["Ring Radius"], addn.inputs[1])
            link_sockets(tree, addn.outputs[0], ring.inputs["Radius"])
        except Exception:
            pass
        c2m = safe_node(tree, "GeometryNodeCurveToMesh", (200, i * 220))
        link_sockets(tree, ring.outputs["Curve"], c2m.inputs["Curve"])
        link_sockets(tree, prof_sock, c2m.inputs["Profile Curve"])
        beveled = _bevel(tree, (360, i * 220), c2m.outputs["Mesh"], 0.012, 2)
        # lift each band: z = zmul * Band Rise
        lift = safe_node(tree, "ShaderNodeCombineXYZ", (360, i * 220 - 140))
        try:
            m2 = safe_node(tree, "ShaderNodeMath", (200, i * 220 - 200))
            m2.operation = 'MULTIPLY'
            m2.inputs[1].default_value = zmul
            link_sockets(tree, gin.outputs["Band Rise"], m2.inputs[0])
            link_sockets(tree, m2.outputs[0], lift.inputs["Z"])
        except Exception:
            pass
        xfn = safe_node(tree, "GeometryNodeTransform", (520, i * 220))
        link_sockets(tree, beveled, xfn.inputs["Geometry"])
        try:
            link_sockets(tree, lift.outputs[0], xfn.inputs["Translation"])
        except Exception:
            pass
        parts.append(xfn.outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (760, 220))
    for p in parts:
        link_sockets(tree, p, join.inputs[0])
    out = _setmat(tree, (900, 220), join.outputs[0], gold)
    link_sockets(tree, out, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


# ---------------------------------------------------------------------------
# 2. Dentil row via Repeat Zone (index sockets), Instance-on-Points fallback
# ---------------------------------------------------------------------------

def build_mh_aaa_dentil(group_name="MEL_mh_aaa_dentil"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Count", 24, 2, 200)
    add_float_param(tree, "Spacing", 0.22, 0.05, 2.0)
    add_float_param(tree, "Block Size", 0.12, 0.02, 1.0)

    _ensure_all_materials()
    plaster = bpy.data.materials.get("MH_PearlPlaster")

    cube = safe_node(tree, "GeometryNodeMeshCube", (0, 0))
    try:
        cube.inputs["Size"].default_value = (1.0, 0.6, 0.45)
        link_sockets(tree, gin.outputs["Block Size"], cube.inputs["Size"])
    except Exception:
        pass
    # uniform-ish block: broadcast float size via vector scale on transform
    block = _bevel(tree, (200, 0), cube.outputs["Mesh"], 0.012, 2)
    block = _xf(tree, (320, 0), block, scale=(0.6, 0.35, 0.45))

    result = None
    try:
        rin = tree.nodes.new("GeometryNodeRepeatInput")
        rout = tree.nodes.new("GeometryNodeRepeatOutput")
        rin.location = (460, 0)
        rout.location = (900, 0)
        rin.pair_with_output(rout)
        # input side: [Iterations, geometry]; output side: [Iteration, geometry]
        link_sockets(tree, block, rin.inputs[1])
        try:
            link_sockets(tree, gin.outputs["Count"], rin.inputs[0])
        except Exception:
            pass
        # body: offset geometry by iteration * spacing along X
        idx = safe_node(tree, "GeometryNodeInputIndex", (560, 160))
        mul = safe_node(tree, "ShaderNodeMath", (620, 160))
        try:
            mul.operation = 'MULTIPLY'
            link_sockets(tree, rin.outputs[0], mul.inputs[0])
            link_sockets(tree, gin.outputs["Spacing"], mul.inputs[1])
            off = safe_node(tree, "ShaderNodeCombineXYZ", (700, 160))
            link_sockets(tree, mul.outputs[0], off.inputs["X"])
            xfn = safe_node(tree, "GeometryNodeTransform", (760, 60))
            link_sockets(tree, rin.outputs[1], xfn.inputs["Geometry"])
            link_sockets(tree, off.outputs[0], xfn.inputs["Translation"])
            link_sockets(tree, xfn.outputs[0], rout.inputs["Item_0"])
        except Exception:
            pass
        result = rout.outputs["Item_0"]
    except Exception:
        result = None

    if result is None:
        # fallback: mesh line + instance on points
        line = safe_node(tree, "GeometryNodeMeshLine", (460, -240))
        try:
            link_sockets(tree, gin.outputs["Count"], line.inputs["Count"])
            sp = safe_node(tree, "ShaderNodeCombineXYZ", (620, -300))
            link_sockets(tree, gin.outputs["Spacing"], sp.inputs["X"])
            link_sockets(tree, sp.outputs[0], line.inputs["Offset"])
        except Exception:
            pass
        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (700, -240))
        link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
        link_sockets(tree, block, inst.inputs["Instance"])
        result = inst.outputs["Instances"]

    out = _setmat(tree, (1050, 0), result, plaster)
    link_sockets(tree, out, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


# ---------------------------------------------------------------------------
# 3. UV-projected scallop shingles
# ---------------------------------------------------------------------------

def build_mh_aaa_scallop_uv(group_name="MEL_mh_aaa_scallop_uv"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Roof Radius", 5.0, 1.0, 30.0)
    add_float_param(tree, "Roof Squash", 0.45, 0.1, 2.0)
    add_int_param(tree, "Rows", 18, 2, 80)
    add_int_param(tree, "Cols", 30, 2, 120)
    add_float_param(tree, "Shingle Scale", 0.32, 0.05, 2.0)

    _ensure_all_materials()
    names = ["MH_RoofIridescentBlue", "MH_FlowerLavender", "MH_AquaGlass",
             "MH_FlowerPink", "MH_RoofIridescentBlue"]
    roof_mats = [bpy.data.materials.get(n) for n in names]
    fallback = bpy.data.materials.get("MH_RoofIridescentBlue")
    roof_mats = [m or fallback for m in roof_mats]

    # --- roof target: squashed sphere, radius param via transform
    sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (0, 300))
    try:
        sphere.inputs["Segments"].default_value = 64
        sphere.inputs["Rings"].default_value = 32
    except Exception:
        pass
    rr = _param_v3(tree, (0, 480), gin.outputs["Roof Radius"], "X")
    sq = _param_v3(tree, (0, 560), gin.outputs["Roof Squash"], "Z")
    merge = safe_node(tree, "ShaderNodeMix", (200, 520))
    try:
        merge.data_type = 'VECTOR'
        merge.blend_type = 'REPLACE'
        merge.inputs[0].default_value = 1.0
        link_sockets(tree, rr, merge.inputs[5])   # A vector
        link_sockets(tree, sq, merge.inputs[6])   # B vector
    except Exception:
        pass
    scale_v = merge.outputs[2] if merge else rr
    roof = _xf(tree, (220, 300), sphere.outputs["Mesh"])
    try:
        xfn = roof.node
        link_sockets(tree, scale_v, xfn.inputs["Scale"])
    except Exception:
        pass

    # --- UV grid: default 2x2 size -> map XY to 0..1
    grid = safe_node(tree, "GeometryNodeMeshGrid", (0, -100))
    try:
        grid.inputs["Size X"].default_value = 2.0
        grid.inputs["Size Y"].default_value = 2.0
        link_sockets(tree, gin.outputs["Cols"], grid.inputs["Vertices X"])
        link_sockets(tree, gin.outputs["Rows"], grid.inputs["Vertices Y"])
    except Exception:
        pass
    pos = safe_node(tree, "GeometryNodeInputPosition", (220, -160))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (300, -160))
    link_sockets(tree, pos.outputs[0], sep.inputs[0])
    mr_x = safe_node(tree, "ShaderNodeMapRange", (400, -100))
    mr_y = safe_node(tree, "ShaderNodeMapRange", (400, -260))
    try:
        mr_x.inputs["From Min"].default_value = -1.0
        mr_x.inputs["From Max"].default_value = 1.0
        mr_y.inputs["From Min"].default_value = -1.0
        mr_y.inputs["From Max"].default_value = 1.0
        link_sockets(tree, sep.outputs["X"], mr_x.inputs["Value"])
        link_sockets(tree, sep.outputs["Y"], mr_y.inputs["Value"])
    except Exception:
        pass
    uv = safe_node(tree, "ShaderNodeCombineXYZ", (560, -160))
    try:
        link_sockets(tree, mr_x.outputs["Result"], uv.inputs["X"])
        link_sockets(tree, mr_y.outputs["Result"], uv.inputs["Y"])
    except Exception:
        pass

    # --- sample roof position at UV (Value = Position)
    pos_in = safe_node(tree, "GeometryNodeInputPosition", (700, 220))
    sample = safe_node(tree, "GeometryNodeSampleUVSurface", (760, 60))
    link_sockets(tree, roof, sample.inputs["Mesh"])
    try:
        link_sockets(tree, pos_in.outputs[0], sample.inputs["Value"])
        link_sockets(tree, uv.outputs[0], sample.inputs["Sample UV"])
    except Exception:
        pass

    sp = safe_node(tree, "GeometryNodeSetPosition", (960, 0))
    link_sockets(tree, grid.outputs["Mesh"], sp.inputs["Geometry"])
    try:
        link_sockets(tree, sample.outputs["Value"], sp.inputs["Position"])
    except Exception:
        pass

    # --- 5-variant scallop family, picked per point
    variants = []
    scales = [(0.16, 0.12, 0.05), (0.15, 0.13, 0.055), (0.17, 0.11, 0.045),
              (0.14, 0.14, 0.06), (0.16, 0.12, 0.05)]
    for i in range(5):
        s = safe_node(tree, "GeometryNodeMeshUVSphere", (0, -600 - i * 180))
        try:
            s.inputs["Segments"].default_value = 16
            s.inputs["Rings"].default_value = 8
        except Exception:
            pass
        v = _xf(tree, (220, -600 - i * 180), s.outputs["Mesh"], scale=scales[i])
        variants.append(v)
    geo_inst = safe_node(tree, "GeometryNodeGeometryToInstance", (560, -500))
    for v in variants:
        try:
            link_sockets(tree, v, geo_inst.inputs[0])
        except Exception:
            pass

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (1160, -200))
    link_sockets(tree, sp.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, geo_inst.outputs[0], inst.inputs["Instance"])
    try:
        inst.inputs["Pick Instance"].default_value = True
        ss = _param_v3(tree, (1000, -380), gin.outputs["Shingle Scale"], "X")
        link_sockets(tree, ss, inst.inputs["Scale"])
    except Exception:
        pass

    out = _setmat(tree, (1340, -200), inst.outputs["Instances"], roof_mats[0])
    link_sockets(tree, out, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


# ---------------------------------------------------------------------------
# 4. Lissajous pearl string
# ---------------------------------------------------------------------------

def build_mh_aaa_lissajous_pearl(group_name="MEL_mh_aaa_lissajous_pearl"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Freq X", 2.0, 1.0, 9.0)
    add_float_param(tree, "Freq Y", 3.0, 1.0, 9.0)
    add_float_param(tree, "Freq Z", 1.0, 1.0, 9.0)
    add_float_param(tree, "Radius", 0.6, 0.05, 5.0)
    add_int_param(tree, "Pearl Count", 60, 8, 400)
    add_float_param(tree, "Pearl Size", 0.035, 0.005, 0.5)

    _ensure_all_materials()
    gold = bpy.data.materials.get("MH_GoldBrass")

    line = safe_node(tree, "GeometryNodeMeshLine", (0, 0))
    try:
        line.inputs["Count"].default_value = 128
    except Exception:
        pass
    idx = safe_node(tree, "GeometryNodeInputIndex", (200, 160))
    div = safe_node(tree, "ShaderNodeMath", (260, 160))
    try:
        div.operation = 'DIVIDE'
        link_sockets(tree, idx.outputs[0], div.inputs[0])
        div.inputs[1].default_value = (2.0 * math.pi / 128.0)
    except Exception:
        pass
    sins = []
    for k, (loc_y, freq_param) in enumerate([(260, "Freq X"), (120, "Freq Y"), (-20, "Freq Z")]):
        mul = safe_node(tree, "ShaderNodeMath", (340, loc_y))
        sin = safe_node(tree, "ShaderNodeMath", (480, loc_y))
        try:
            mul.operation = 'MULTIPLY'
            sin.operation = 'SINE'
            link_sockets(tree, div.outputs[0], mul.inputs[0])
            link_sockets(tree, gin.outputs[freq_param], mul.inputs[1])
            link_sockets(tree, mul.outputs[0], sin.inputs[0])
        except Exception:
            pass
        sins.append(sin)
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (620, 120))
    try:
        link_sockets(tree, sins[0].outputs[0], comb.inputs["X"])
        link_sockets(tree, sins[1].outputs[0], comb.inputs["Y"])
        link_sockets(tree, sins[2].outputs[0], comb.inputs["Z"])
    except Exception:
        pass
    scale = safe_node(tree, "ShaderNodeVectorMath", (760, 120))
    try:
        scale.operation = 'SCALE'
        link_sockets(tree, comb.outputs[0], scale.inputs[0])
        link_sockets(tree, gin.outputs["Radius"], scale.inputs["Scale"])
    except Exception:
        pass
    sp = safe_node(tree, "GeometryNodeSetPosition", (900, 0))
    link_sockets(tree, line.outputs["Mesh"], sp.inputs["Geometry"])
    try:
        link_sockets(tree, scale.outputs[0], sp.inputs["Position"])
    except Exception:
        pass
    # mesh -> curve -> resample -> points
    m2c = safe_node(tree, "GeometryNodeMeshToCurve", (1040, 0))
    link_sockets(tree, sp.outputs["Geometry"], m2c.inputs["Mesh"])
    resamp = safe_node(tree, "GeometryNodeResampleCurve", (1180, 0))
    try:
        link_sockets(tree, m2c.outputs["Curve"], resamp.inputs["Curve"])
        link_sockets(tree, gin.outputs["Pearl Count"], resamp.inputs["Count"])
    except Exception:
        pass
    pts = safe_node(tree, "GeometryNodeCurveToPoints", (1320, 0))
    try:
        link_sockets(tree, resamp.outputs["Curve"], pts.inputs["Curve"])
    except Exception:
        pass
    pearl = safe_node(tree, "GeometryNodeMeshUVSphere", (1320, -260))
    try:
        pearl.inputs["Segments"].default_value = 12
        pearl.inputs["Rings"].default_value = 8
    except Exception:
        pass
    ps = _param_v3(tree, (1320, -420), gin.outputs["Pearl Size"], "X")
    pearl_xf = safe_node(tree, "GeometryNodeTransform", (1460, -260))
    link_sockets(tree, pearl.outputs["Mesh"], pearl_xf.inputs["Geometry"])
    try:
        link_sockets(tree, ps, pearl_xf.inputs["Scale"])
    except Exception:
        pass
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (1500, 0))
    try:
        link_sockets(tree, pts.outputs["Points"], inst.inputs["Points"])
    except Exception:
        link_sockets(tree, sp.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, pearl_xf.outputs[0], inst.inputs["Instance"])

    out = _setmat(tree, (1660, 0), inst.outputs["Instances"], gold)
    link_sockets(tree, out, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


def _register_all():
    register_builder(
        "MEL_mh_aaa_cornice", build_mh_aaa_cornice,
        "MH AAA Cornice", "Stepped cornice/string-course ring, swept + beveled.",
        category="structures")
    register_builder(
        "MEL_mh_aaa_dentil", build_mh_aaa_dentil,
        "MH AAA Dentil Row", "Repeat Zone dentil blocks under a cornice.",
        category="structures")
    register_builder(
        "MEL_mh_aaa_scallop_uv", build_mh_aaa_scallop_uv,
        "MH AAA Scallop UV", "UV-projected scallop shingles via Sample UV Surface.",
        category="set_dressing")
    register_builder(
        "MEL_mh_aaa_lissajous_pearl", build_mh_aaa_lissajous_pearl,
        "MH AAA Lissajous Pearl", "Lissajous pearl string driven by sine math; music-reactive.",
        category="ornament")


_register_all()
