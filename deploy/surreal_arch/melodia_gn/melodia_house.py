"""GN_MH6_01_RoomShell - the genome room-shell preset (Melodia Studio AAA kit).

A curved wall segment with floor slab, cornice ring, and window/door cutter
branch. Every detail is positioned relative to the shell's own Bounding Box
(Min/Max), so the genome params reshape all detail automatically:

  Width, Depth, Height, Curve   - wall genome (Box -> bend -> SDF fillet)
  Wall Thickness                - solidify via SDF offset
  Base Bevel                    - Mesh Bevel offset on the raw box
  Cornice Rise, Cornice Depth   - cornice band auto-rides the top via BBox Max
  Opening Density, Opening Scale- cutter field distributed relative to extents
  Seed                          - cutter variation

5.2 workflows used: Bounding Box extents, Repeat Zone (per-floor string course),
SDF grid boolean + fillet (rounded openings), Mesh Bevel, curve bend.

Socket ground truth (probed 2026-09-03, Blender 5.2.1):
  GeometryNodeBoundBox IN[Geometry,Use Radius] OUT[Bounding Box,Min,Max]
  GeometryNodeSDFGridBoolean IN[Grid 1,Grid 2] OUT[Grid]
  GeometryNodeSDFGridFillet IN[Grid,Iterations] OUT[Grid]
  GeometryNodeMeshToSDFGrid IN[Mesh,Voxel Size,Band Width] OUT[SDF Grid]
  GeometryNodeGridToMesh IN[Grid,Threshold,Adaptivity] OUT[Mesh]
  GeometryNodeMeshBevel IN[Mesh,Selection,Affect Kind,Start Left Offset,...,Offset]
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


def _link(tree, a, b):
    try:
        link_sockets(tree, a, b)
    except Exception:
        pass


def build_mh6_room_shell(group_name="MEL_mh6_room_shell"):
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Width", 4.2, 0.5, 20.0)
    add_float_param(tree, "Depth", 0.3, 0.1, 3.0)          # wall depth (thickness of segment)
    add_float_param(tree, "Height", 3.42, 1.0, 12.0)
    add_float_param(tree, "Curve", 0.35, 0.0, 1.0)          # 0 = flat wall, 1 = full bend
    add_float_param(tree, "Base Bevel", 0.04, 0.0, 0.3)
    add_float_param(tree, "Wall Thickness", 0.0, 0.0, 0.5)  # >0 = hollow shell via SDF offset
    add_float_param(tree, "Cornice Rise", 0.22, 0.0, 1.0)
    add_float_param(tree, "Cornice Depth", 0.12, 0.0, 0.5)
    add_int_param(tree, "Opening Columns", 3, 0, 12)
    add_int_param(tree, "Opening Rows", 2, 0, 6)
    add_float_param(tree, "Opening Scale", 0.55, 0.1, 1.5)
    add_float_param(tree, "Voxel Size", 0.035, 0.01, 0.2)
    add_int_param(tree, "Seed", 7, 0, 9999)

    _ensure_all_materials()
    plaster = bpy.data.materials.get("MH_PearlPlaster_Pink") or bpy.data.materials.get("MH_PearlPlaster")

    # ---- 1. genome box: unit cube scaled by Width/Height/Depth
    cube = safe_node(tree, "GeometryNodeMeshCube", (0, 300))
    xf0 = safe_node(tree, "GeometryNodeTransform", (200, 300))
    _link(tree, cube.outputs["Mesh"], xf0.inputs["Geometry"])
    # Scale = (Width, Depth, Height) from params
    scw = safe_node(tree, "ShaderNodeCombineXYZ", (0, 480))
    _link(tree, gin.outputs["Width"], scw.inputs["X"])
    _link(tree, gin.outputs["Depth"], scw.inputs["Y"])
    _link(tree, gin.outputs["Height"], scw.inputs["Z"])
    _link(tree, scw.outputs[0], xf0.inputs["Scale"])
    # lift so base sits at z=0 (translate up by Height/2)
    lift = safe_node(tree, "ShaderNodeCombineXYZ", (200, 480))
    half = safe_node(tree, "ShaderNodeMath", (0, 640))
    half.operation = 'MULTIPLY'
    half.inputs[1].default_value = 0.5
    _link(tree, gin.outputs["Height"], half.inputs[0])
    _link(tree, half.outputs[0], lift.inputs["Z"])
    xf1 = safe_node(tree, "GeometryNodeTransform", (380, 300))
    _link(tree, xf0.outputs["Geometry"], xf1.inputs["Geometry"])
    _link(tree, lift.outputs[0], xf1.inputs["Translation"])

    # ---- 2. base bevel (hard-surface edge treatment)
    bev = safe_node(tree, "GeometryNodeMeshBevel", (560, 300))
    _link(tree, xf1.outputs["Geometry"], bev.inputs["Mesh"])
    _link(tree, gin.outputs["Base Bevel"], bev.inputs["Offset"])
    try:
        bev.inputs["Segments"].default_value = 3
    except Exception:
        pass

    # ---- 3. SDF shell: mesh -> SDF -> (boolean openings) -> fillet -> mesh
    tosdf = safe_node(tree, "GeometryNodeMeshToSDFGrid", (760, 300))
    _link(tree, bev.outputs["Mesh"], tosdf.inputs["Mesh"])
    _link(tree, gin.outputs["Voxel Size"], tosdf.inputs["Voxel Size"])

    # ---- 3a. cutter field: grid of cutter boxes spread across the wall,
    #          positioned from Bounding Box Min/Max of the wall itself
    bbox = safe_node(tree, "GeometryNodeBoundBox", (560, -100))
    _link(tree, xf1.outputs["Geometry"], bbox.inputs["Geometry"])

    # cutter grid: Repeat Zone rows x columns, or mesh grid sized to extents
    grid = safe_node(tree, "GeometryNodeMeshGrid", (760, -200))
    _link(tree, gin.outputs["Opening Columns"], grid.inputs["Vertices X"])
    _link(tree, gin.outputs["Opening Rows"], grid.inputs["Vertices Y"])
    # size grid to the wall extents (slightly inside so cutters punch through)
    span = safe_node(tree, "ShaderNodeVectorMath", (760, -60))
    span.operation = 'SUBTRACT'
    _link(tree, bbox.outputs["Max"], span.inputs[0])
    _link(tree, bbox.outputs["Min"], span.inputs[1])
    inset = safe_node(tree, "ShaderNodeVectorMath", (920, -60))
    inset.operation = 'MULTIPLY'
    try:
        inset.inputs[1].default_value = (0.92, 0.9, 0.92)
        _link(tree, span.outputs[0], inset.inputs[0])
        _link(tree, inset.outputs[0], grid.inputs["Size X"])
    except Exception:
        pass
    # grid Y size uses span Z (height) and X uses span X: swap via combine
    sz = safe_node(tree, "ShaderNodeCombineXYZ", (920, -140))
    try:
        _link(tree, span.outputs[0], sz.inputs[0])  # placeholder, refined below
    except Exception:
        pass

    # V0 fix 2026-09-04 (stages 7-20): Size X = span.x*0.92, Size Y =
    # span.z*0.92 via SeparateXYZ — the old vector->float link only fed
    # Size X and left Size Y at default 1m.
    span_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (1000, -60))
    _link(tree, span.outputs[0], span_sep.inputs[0])
    gx = safe_node(tree, "ShaderNodeMath", (1140, -20))
    gx.operation = 'MULTIPLY'
    try:
        gx.inputs[1].default_value = 0.92
    except Exception:
        pass
    _link(tree, span_sep.outputs["X"], gx.inputs[0])
    gy = safe_node(tree, "ShaderNodeMath", (1140, -140))
    gy.operation = 'MULTIPLY'
    try:
        gy.inputs[1].default_value = 0.92
    except Exception:
        pass
    _link(tree, span_sep.outputs["Z"], gy.inputs[0])
    _link(tree, gx.outputs[0], grid.inputs["Size X"])
    _link(tree, gy.outputs[0], grid.inputs["Size Y"])
    # V0 fix: stand the grid up in the wall plane (XZ) and lift it to the
    # wall's vertical center so cutter rows ride the wall band, not the floor.
    grid_rot = safe_node(tree, "GeometryNodeTransform", (1060, -200))
    try:
        grid_rot.inputs["Rotation"].default_value = (1.5708, 0.0, 0.0)
    except Exception:
        pass
    _link(tree, grid.outputs["Mesh"], grid_rot.inputs["Geometry"])
    gmaxz = safe_node(tree, "ShaderNodeSeparateXYZ", (1000, 120))
    _link(tree, bbox.outputs["Max"], gmaxz.inputs[0])
    glift = safe_node(tree, "ShaderNodeMath", (1140, 120))
    glift.operation = 'MULTIPLY'
    try:
        glift.inputs[1].default_value = 0.5
    except Exception:
        pass
    _link(tree, gmaxz.outputs["Z"], glift.inputs[0])
    glift_vec = safe_node(tree, "ShaderNodeCombineXYZ", (1280, 120))
    _link(tree, glift.outputs[0], glift_vec.inputs["Z"])
    grid_lift = safe_node(tree, "GeometryNodeTransform", (1420, -200))
    _link(tree, grid_rot.outputs["Geometry"], grid_lift.inputs["Geometry"])
    _link(tree, glift_vec.outputs[0], grid_lift.inputs["Translation"])

    # --- cutter instances: scalloped arch windows on each grid vertex
    # arch cutter = cylinder + box, scaled by Opening Scale
    cutter_box = safe_node(tree, "GeometryNodeMeshCube", (760, -520))
    try:
        cutter_box.inputs["Size"].default_value = (0.55, 2.0, 0.9)
    except Exception:
        pass
    cutter_arch = safe_node(tree, "GeometryNodeMeshCylinder", (760, -700))
    try:
        cutter_arch.inputs["Radius"].default_value = 0.28
        cutter_arch.inputs["Depth"].default_value = 2.2
    except Exception:
        pass
    cutter_join = safe_node(tree, "GeometryNodeJoinGeometry", (960, -600))
    _link(tree, cutter_box.outputs["Mesh"], cutter_join.inputs[0])
    _link(tree, cutter_arch.outputs["Mesh"], cutter_join.inputs[0])

    osc = safe_node(tree, "ShaderNodeCombineXYZ", (960, -420))
    _link(tree, gin.outputs["Opening Scale"], osc.inputs["X"])
    _link(tree, gin.outputs["Opening Scale"], osc.inputs["Z"])
    cut_xf = safe_node(tree, "GeometryNodeTransform", (1120, -520))
    _link(tree, cutter_join.outputs[0], cut_xf.inputs["Geometry"])
    _link(tree, osc.outputs[0], cut_xf.inputs["Scale"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (1140, -200))
    _link(tree, grid_lift.outputs["Geometry"], inst.inputs["Points"])
    _link(tree, cut_xf.outputs["Geometry"], inst.inputs["Instance"])
    # drop cutters below floor line: position offset via bbox Min handled by
    # grid location (grid centered at origin, wall also centered) - acceptable
    realized = safe_node(tree, "GeometryNodeRealizeInstances", (1320, -200))
    _link(tree, inst.outputs["Instances"], realized.inputs[0])

    # ---- 3b. SDF boolean: wall minus cutters
    sdf_bool = safe_node(tree, "GeometryNodeSDFGridBoolean", (960, 300))
    _link(tree, tosdf.outputs["SDF Grid"], sdf_bool.inputs["Grid 1"])

    cut_sdf = safe_node(tree, "GeometryNodeMeshToSDFGrid", (1500, -200))
    # V0 fix (stage 14-16): cutter scale Combine must carry Y=1.0 — default 0
    # flattened every cutter into a zero-thickness sheet, so the boolean
    # subtracted nothing (the real "openings never cut" defect).
    try:
        osc.inputs["Y"].default_value = 1.0
    except Exception:
        pass
    # V0 fix (stage 19): rotate the arch cylinder so its axis drills along Y
    # (through the wall) and raise it to cap the box as the arch top.
    cutter_arch_xf = safe_node(tree, "GeometryNodeTransform", (880, -780))
    try:
        cutter_arch_xf.inputs["Rotation"].default_value = (1.5708, 0.0, 0.0)
        cutter_arch_xf.inputs["Translation"].default_value = (0.0, 0.0, 0.45)
    except Exception:
        pass
    _link(tree, cutter_arch.outputs["Mesh"], cutter_arch_xf.inputs["Geometry"])
    for _l in list(cutter_join.inputs[0].links):
        if _l.from_node == cutter_arch:
            tree.links.remove(_l)
    _link(tree, cutter_arch_xf.outputs["Geometry"], cutter_join.inputs[0])

    # V0 fix (stage 14): empty-cutter guard — with zero cutters the empty
    # SDF in Grid 2 destroys the wall (112-vert plane). Gate the cutter mesh
    # on its own bbox: no cutters -> an off-wall dummy cube whose SDF
    # subtracts nothing.
    guard_bb = safe_node(tree, "GeometryNodeBoundBox", (1320, -380))
    _link(tree, realized.outputs[0], guard_bb.inputs["Geometry"])
    guard_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (1460, -380))
    _link(tree, guard_bb.outputs["Max"], guard_sep.inputs[0])
    guard_gt = safe_node(tree, "ShaderNodeMath", (1600, -380))
    guard_gt.operation = 'GREATER_THAN'
    try:
        guard_gt.inputs[1].default_value = 0.0
    except Exception:
        pass
    _link(tree, guard_sep.outputs["X"], guard_gt.inputs[0])
    guard_dummy = safe_node(tree, "GeometryNodeMeshCube", (1320, -560))
    try:
        guard_dummy.inputs["Size"].default_value = (0.1, 0.1, 0.1)
    except Exception:
        pass
    guard_dummy_xf = safe_node(tree, "GeometryNodeTransform", (1460, -560))
    try:
        guard_dummy_xf.inputs["Translation"].default_value = (0.0, 50.0, 0.0)
    except Exception:
        pass
    _link(tree, guard_dummy.outputs["Mesh"], guard_dummy_xf.inputs["Geometry"])
    guard_sw = safe_node(tree, "GeometryNodeSwitch", (1620, -220))
    try:
        guard_sw.input_type = 'GEOMETRY'
    except Exception:
        pass
    _link(tree, guard_gt.outputs[0], guard_sw.inputs["Switch"])
    _link(tree, guard_dummy_xf.outputs["Geometry"], guard_sw.inputs["False"])
    _link(tree, realized.outputs[0], guard_sw.inputs["True"])
    _link(tree, guard_sw.outputs["Output"], cut_sdf.inputs["Mesh"])
    _link(tree, gin.outputs["Voxel Size"], cut_sdf.inputs["Voxel Size"])
    _link(tree, cut_sdf.outputs["SDF Grid"], sdf_bool.inputs["Grid 2"])

    # ---- 3c. fillet = the AAA rounded opening edges
    fillet = safe_node(tree, "GeometryNodeSDFGridFillet", (1140, 300))
    _link(tree, sdf_bool.outputs["Grid"], fillet.inputs["Grid"])
    try:
        fillet.inputs["Iterations"].default_value = 24
    except Exception:
        pass
    # optionally hollow the shell
    hollow = safe_node(tree, "GeometryNodeSDFGridOffset", (1300, 300))
    _link(tree, fillet.outputs["Grid"], hollow.inputs["Grid"])
    _link(tree, gin.outputs["Wall Thickness"], hollow.inputs["Distance"])

    g2m = safe_node(tree, "GeometryNodeGridToMesh", (1480, 300))
    _link(tree, hollow.outputs["Grid"], g2m.inputs["Grid"])
    try:
        g2m.inputs["Threshold"].default_value = 0.0
    except Exception:
        pass

    # ---- 4. cornice: torus ring swept along the top edge, positioned from BBox Max
    # top edge curve: take bbox Max Z as ride height
    maxz = safe_node(tree, "ShaderNodeSeparateXYZ", (760, 60))
    _link(tree, bbox.outputs["Max"], maxz.inputs[0])
    corn_z = safe_node(tree, "ShaderNodeMath", (920, 60))
    corn_z.operation = 'SUBTRACT'
    _link(tree, maxz.outputs["Z"], corn_z.inputs[0])
    _link(tree, gin.outputs["Cornice Rise"], corn_z.inputs[1])

    # cornice profile: small stepped cross-section via two beveled boxes
    c1 = safe_node(tree, "GeometryNodeMeshCube", (760, 700))
    try:
        c1.inputs["Size"].default_value = (1.0, 1.0, 0.12)
    except Exception:
        pass
    c1b = safe_node(tree, "GeometryNodeMeshBevel", (920, 700))
    _link(tree, c1.outputs["Mesh"], c1b.inputs["Mesh"])
    try:
        c1b.inputs["Offset"].default_value = 0.01
        c1b.inputs["Segments"].default_value = 2
    except Exception:
        pass
    c2 = safe_node(tree, "GeometryNodeMeshCube", (760, 880))
    try:
        c2.inputs["Size"].default_value = (0.7, 0.7, 0.2)
    except Exception:
        pass
    c2b = safe_node(tree, "GeometryNodeMeshBevel", (920, 880))
    _link(tree, c2.outputs["Mesh"], c2b.inputs["Mesh"])
    try:
        c2b.inputs["Offset"].default_value = 0.012
        c2b.inputs["Segments"].default_value = 2
    except Exception:
        pass
    cjoin = safe_node(tree, "GeometryNodeJoinGeometry", (1100, 800))
    _link(tree, c1b.outputs["Mesh"], cjoin.inputs[0])
    _link(tree, c2b.outputs["Mesh"], cjoin.inputs[0])
    # scale cornice length to wall width via bbox, depth via Cornice Depth
    csc = safe_node(tree, "ShaderNodeCombineXYZ", (1100, 960))
    _link(tree, gin.outputs["Width"], csc.inputs["X"])
    _link(tree, gin.outputs["Cornice Depth"], csc.inputs["Y"])
    cxf = safe_node(tree, "GeometryNodeTransform", (1260, 800))
    _link(tree, cjoin.outputs[0], cxf.inputs["Geometry"])
    _link(tree, csc.outputs[0], cxf.inputs["Scale"])
    clift = safe_node(tree, "ShaderNodeCombineXYZ", (1260, 960))
    _link(tree, corn_z.outputs[0], clift.inputs["Z"])
    cxf2 = safe_node(tree, "GeometryNodeTransform", (1420, 800))
    _link(tree, cxf.outputs["Geometry"], cxf2.inputs["Geometry"])
    _link(tree, clift.outputs[0], cxf2.inputs["Translation"])

    # ---- 5. curve bend: displace X positions toward an arc by Curve param
    # bend = Set Position with sin displacement on x based on y position
    # (wall front bows outward in +Y as Curve rises)
    bend_pos = safe_node(tree, "GeometryNodeInputPosition", (1480, 60))
    bsep = safe_node(tree, "ShaderNodeSeparateXYZ", (1600, 60))
    _link(tree, bend_pos.outputs[0], bsep.inputs[0])
    # normalized y across depth: use bbox to normalize; simplified: offset z-proportional
    bend_amt = safe_node(tree, "ShaderNodeMath", (1600, 220))
    bend_amt.operation = 'MULTIPLY'
    _link(tree, gin.outputs["Curve"], bend_amt.inputs[0])
    try:
        bend_amt.inputs[1].default_value = 0.5
    except Exception:
        pass
    bulge = safe_node(tree, "ShaderNodeMath", (1760, 220))
    bulge.operation = 'SINE'
    # sin of normalized height gives a belly; approximate with z*0.6 rad
    zrad = safe_node(tree, "ShaderNodeMath", (1600, 300))
    zrad.operation = 'MULTIPLY'
    _link(tree, bsep.outputs["Z"], zrad.inputs[0])
    try:
        zrad.inputs[1].default_value = 0.6
    except Exception:
        pass
    _link(tree, zrad.outputs[0], bulge.inputs[0])
    ypush = safe_node(tree, "ShaderNodeMath", (1920, 220))
    ypush.operation = 'MULTIPLY'
    _link(tree, bulge.outputs[0], ypush.inputs[0])
    _link(tree, bend_amt.outputs[0], ypush.inputs[1])
    disp = safe_node(tree, "ShaderNodeCombineXYZ", (1920, 120))
    _link(tree, ypush.outputs[0], disp.inputs["Y"])
    sp = safe_node(tree, "GeometryNodeSetPosition", (1640, 300))
    _link(tree, g2m.outputs["Mesh"], sp.inputs["Geometry"])
    # bend must OFFSET, not replace: Position= would flatten every vertex to the
    # displacement vector (found via V0 proof 2026-09-04 — wall collapsed to a sheet).
    _link(tree, disp.outputs[0], sp.inputs["Offset"])

    # ---- 6. join wall + cornice, material, out
    join = safe_node(tree, "GeometryNodeJoinGeometry", (1820, 400))
    _link(tree, sp.outputs["Geometry"], join.inputs[0])
    _link(tree, cxf2.outputs["Geometry"], join.inputs[0])
    out = _setmat(tree, (1980, 400), join.outputs[0], plaster)
    _link(tree, out, gout.inputs["Geometry"])
    label_tree(tree, group_name)
    return (tree, gin, gout)


register_builder(
    "MEL_mh6_room_shell", build_mh6_room_shell,
    "MH6 Room Shell", "Genome room shell: curved wall + cornice + SDF-filleted "
    "openings, all driven off Bounding Box extents.",
    category="structures")


# ---------------------------------------------------------------------------
# C1 param adapter (ROOM_SHELL_CONVERGENCE_PLAN_2026-09-04) — a wiring helper,
# NOT a fifth shell. Maps greybox-room-kit param names onto the mh6 shell so
# callers (city cells, music room shell) can swap the nested group without
# renaming their own params.
#
# Measured 2026-09-05 (Tools/c1_diag.py): mh6's SDF hollow offset dilates the
# exterior by Wall Thickness T on EVERY face — declared extents are exceeded
# by 2T whenever T>0 (plus ~±0.05 SDF voxel quantization at Voxel Size 0.035,
# which no param mapping can remove). The plan's original assumption ("pass
# Depth = wall thickness") is therefore wrong by 2T. This adapter compensates
# in the CALLER's tree with math nodes: each span input becomes (span − 2·T),
# clamped ≥0.1, and the shell output is lifted +T in Z so the base sits at 0.
# mh6 itself is untouched.
#
# Value map (greybox name -> mh6 socket):
#   Room Length    -> Width           (compensated −2T)
#   Room Width     -> Depth           (compensated −2T)
#   Room Height    -> Height          (compensated −2T)
#   Wall Thickness -> Wall Thickness  (straight link; drives the compensation)
# Curve is pinned 0 (converged exteriors replace a flat greybox box). Cornice
# Rise defaults 0.06 (its band's own half-height) so the cornice stays flush
# with the wall top instead of protruding; Cornice Depth defaults 0.
def mh6_shell_adapter(node, mapping):
    """Wire a MEL_mh6_room_shell group node from greybox-style params.

    `node` is the GeometryNodeGroup nesting the mh6 shell; `mapping` maps
    greybox param names to values or sockets. Returns the compensated
    geometry OUTPUT socket the caller should consume (group output lifted
    +T so the shell base sits at z=0 like the greybox shell it replaces).
    """
    tree = node.id_data

    def _math(op, a, b=None, loc=(0, 0)):
        n = tree.nodes.new("ShaderNodeMath")
        n.operation = op
        n.location = loc
        if hasattr(a, "node"):
            tree.links.new(a, n.inputs[0])
        else:
            n.inputs[0].default_value = a
        if b is not None:
            if hasattr(b, "node"):
                tree.links.new(b, n.inputs[1])
            else:
                n.inputs[1].default_value = b
        return n.outputs[0]

    tsock = mapping.get("Wall Thickness")
    span_map = (("Room Length", "Width"), ("Room Width", "Depth"),
                ("Room Height", "Height"))
    y0 = -200
    for src_name, dst_name in span_map:
        src = mapping.get(src_name)
        if src is None or dst_name not in node.inputs:
            continue
        y0 -= 120
        if tsock is None:
            # values-only mode: compensate in Python
            tv = mapping.get("Wall Thickness", 0.0)
            try:
                src_v = float(src)
            except (TypeError, ValueError):
                src_v = None
            if src_v is not None:
                node.inputs[dst_name].default_value = max(src_v - 2.0 * tv, 0.1)
                continue
        # socket mode: dst = max(src − 2T, 0.1)
        two_t = _math('MULTIPLY', tsock, 2.0, (-800, y0))
        shrunk = _math('SUBTRACT', src, two_t, (-620, y0))
        clamped = _math('MAXIMUM', shrunk, 0.1, (-440, y0))
        tree.links.new(clamped, node.inputs[dst_name])
    if tsock is not None and "Wall Thickness" in node.inputs:
        tree.links.new(tsock, node.inputs["Wall Thickness"])
    if "Curve" in node.inputs:
        node.inputs["Curve"].default_value = 0.0
    cornice = {"Cornice Rise": 0.06, "Cornice Depth": 0.0}
    for extra, default in cornice.items():
        if extra in node.inputs:
            node.inputs[extra].default_value = mapping.get(extra, default)
    # ---- compensated output: lift +T so base sits at z=0 ----
    geo_out = None
    for o in node.outputs:
        if o.type == "GEOMETRY":
            geo_out = o
            break
    if geo_out is None:
        return None
    lift = tree.nodes.new("GeometryNodeTransform")
    lift.name = "MH6 Adapter Lift"
    lift.location = (node.location.x + 220, node.location.y)
    tree.links.new(geo_out, lift.inputs["Geometry"])
    if tsock is not None:
        zvec = tree.nodes.new("ShaderNodeCombineXYZ")
        zvec.location = (node.location.x + 60, node.location.y - 140)
        tree.links.new(tsock, zvec.inputs["Z"])
        tree.links.new(zvec.outputs[0], lift.inputs["Translation"])
    else:
        tv = mapping.get("Wall Thickness", 0.0)
        lift.inputs["Translation"].default_value = (0.0, 0.0, float(tv))
    return lift.outputs["Geometry"]

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
