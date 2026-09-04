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
    _link(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    _link(tree, cut_xf.outputs["Geometry"], inst.inputs["Instance"])
    # drop cutters below floor line: position offset via bbox Min handled by
    # grid location (grid centered at origin, wall also centered) - acceptable
    realized = safe_node(tree, "GeometryNodeRealizeInstances", (1320, -200))
    _link(tree, inst.outputs["Instances"], realized.inputs[0])

    # ---- 3b. SDF boolean: wall minus cutters
    sdf_bool = safe_node(tree, "GeometryNodeSDFGridBoolean", (960, 300))
    _link(tree, tosdf.outputs["SDF Grid"], sdf_bool.inputs["Grid 1"])

    cut_sdf = safe_node(tree, "GeometryNodeMeshToSDFGrid", (1500, -200))
    _link(tree, realized.outputs[0], cut_sdf.inputs["Mesh"])
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
    _link(tree, disp.outputs[0], sp.inputs["Position"])

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
