"""MEL_curved_wall — adjustable arc wall segment for dreamy stylized architecture.

A single curved wall panel that can span any angle (30-180 degrees) and radius.
Uses GeometryNodeCurveArc (5.2 native) for the wall outline, then
GeometryNodeCurveToMesh to sweep a profile.

Builder:
  MEL_curved_wall — arc wall with editable radius, angle, height, thickness
"""
from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder,
)


def build_curved_wall(group_name="MEL_legacy_curved_wall"):
    """Curved wall segment: an arc of a circle, built as a mesh.

    Uses GeometryNodeCurveArc for the wall outline, then CurveToMesh
    with a profile to create the solid wall.

    Inputs:
      Geometry     — incoming (pass-through)
      Radius       — 4 m  (arc radius; larger = gentler curve)
      Arc Angle    — 90   (degrees, 10-180)
      Wall Height  — 3.5 m
      Wall Thick   — 0.35 m (wall depth, measured from arc center)
      Segments     — 32   (arc resolution)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ── Parameters ──
    r = add_float_param(tree, "Radius", 4.0, 0.1, 50.0)
    angle_deg = add_float_param(tree, "Arc Angle", 90.0, 1.0, 180.0)
    h = add_float_param(tree, "Wall Height", 3.5, 0.1, 20.0)
    t = add_float_param(tree, "Wall Thickness", 0.35, 0.01, 5.0)
    segs = add_int_param(tree, "Segments", 32, 4, 256)

    # ── 1. Arc curve (GeometryNodeCurveArc in 5.2) ──
    arc = safe_node(tree, "GeometryNodeCurveArc", (bx - 200, by + 200))
    color_node(arc, "curve")
    if arc is not None:
        try:
            arc.mode = "RADIUS"
        except Exception:
            pass
        link_sockets(tree, r, arc.inputs.get("Radius", arc.inputs.get("Radius")))
        try:
            arc.inputs["Resolution"].default_value = 64
        except Exception:
            pass
        # Set arc angle in radians (90 degrees = π/2)
        # Arc Angle is in radians
        rad_conv = safe_node(tree, "ShaderNodeMath", (bx - 300, by + 100))
        rad_conv.operation = "RADIANS"
        link_sockets(tree, angle_deg, rad_conv.inputs[0])
        link_sockets(tree, rad_conv.outputs["Value"], arc.inputs.get("Arc Angle", arc.inputs[2] if len(arc.inputs) > 2 else None))

    # ── 2. Profile: a Quad curve made from a MeshGrid → MeshToCurve ──
    # The profile is a rectangle of Width = Wall Thickness, Height = Wall Height
    # Since GeometryNodeCurvePrimitiveRectangle doesn't exist in 5.2, we
    # build a quad from a MeshGrid (2x2 verts), convert to curve.
    profile_mesh = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by - 100))
    color_node(profile_mesh, "geometry")
    if profile_mesh is not None:
        try:
            link_sockets(tree, t, profile_mesh.inputs.get("Size X", profile_mesh.inputs[0]))
            link_sockets(tree, h, profile_mesh.inputs.get("Size Y", profile_mesh.inputs[1]))
            profile_mesh.inputs.get("Vertices X", profile_mesh.inputs[2]).default_value = 2
            profile_mesh.inputs.get("Vertices Y", profile_mesh.inputs[3]).default_value = 2
        except Exception:
            pass

    # Convert mesh to curve for sweeping
    profile_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 200, by - 100))
    color_node(profile_curve, "curve")
    link_sockets(tree, profile_mesh.outputs.get("Mesh", profile_mesh.outputs[0]), profile_curve.inputs.get("Mesh", profile_curve.inputs[0]))

    # Transform profile to face correct direction
    profile_tx = safe_node(tree, "GeometryNodeTransform", (bx, by - 100))
    link_sockets(tree, profile_curve.outputs.get("Curve", profile_curve.outputs[0]), profile_tx.inputs.get("Geometry", profile_tx.inputs[0]))
    try:
        profile_tx.inputs["Rotation"].default_value = (1.5708, 0, 0)
    except Exception:
        pass

    # ── 3. Sweep: CurveToMesh (arc × profile) ──
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 200, by))
    color_node(sweep, "geometry")
    link_sockets(tree, arc.outputs.get("Curve", arc.outputs[0]), sweep.inputs.get("Curve", sweep.inputs[0]))
    link_sockets(tree, profile_tx.outputs.get("Geometry", profile_tx.outputs.get("Curve")), sweep.inputs.get("Profile Curve", sweep.inputs.get("Profile")))
    try:
        sweep.inputs["Fill Caps"].default_value = True
    except Exception:
        pass

    # ── 4. Join with incoming ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), join.inputs.get("Geometry"))
    link_sockets(tree, sweep.outputs.get("Mesh", sweep.outputs.get("Geometry")), join.inputs.get("Geometry"))

    # ── 5. Set shade smooth ──
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 700, by))
    color_node(shade, "geometry")
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, join.outputs.get("Geometry"), shade.inputs.get("Geometry"))

    link_sockets(tree, shade.outputs.get("Geometry"), gout.inputs.get("Geometry"))

    return label_tree(tree, "MEL_legacy_curved_wall", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arc", "nodes": ("arc", "rad_conv"), "role": "curve"},
        {"title": "Profile", "nodes": ("profile_mesh", "profile_curve", "profile_tx"), "role": "geometry"},
        {"title": "Sweep & Join", "nodes": ("sweep", "join", "shade", "Group Output"), "role": "output"},
    ])


# ── Registry ──
register_builder(
    "MEL_legacy_curved_wall", build_curved_wall,
    "Curved Wall",
    "Adjustable arc wall segment for dreamy stylized interiors. "
    "Edit radius, arc angle, height, thickness, and segment count.",
    category="structures",
)
