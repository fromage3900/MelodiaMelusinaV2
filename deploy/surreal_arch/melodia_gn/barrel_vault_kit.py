"""Barrel vault ceiling GN group builder.

A semicircular (barrel) vault ceiling spanning between two walls. Uses
GeometryNodeCurveArc (Blender 5.2 native) for the arc, and a MeshGrid→MeshToCurve
profile for the cross-section.

Uses only Blender 5.x-native node ids via ``safe_node`` so legacy/remap
handling is automatic.
"""
from __future__ import annotations

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder, apply_universal_music_pass,
)


def build_barrel_vault_ceiling(group_name="MEL_barrel_vault_ceiling"):
    """Barrel vault ceiling panel spanning between two walls.

    Uses GeometryNodeCurveArc for the semicircular profile, swept with
    a Grid→CurveToMesh profile via CurveToMesh.

    Inputs:
      Geometry      — incoming (pass-through)
      Vault Radius  — 4 m  (radius of the barrel arc)
      Vault Length  — 6 m  (length of the vault along its axis)
      Vault Thick   — 0.3 m (profile thickness for solidification)
      Invert        — False (flip arc direction)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ── Parameters ──
    vr = add_float_param(tree, "Vault Radius", 4.0, 0.1, 50.0)
    vl = add_float_param(tree, "Vault Length", 6.0, 0.1, 100.0)
    vt = add_float_param(tree, "Vault Thickness", 0.3, 0.01, 5.0)
    inv = add_bool_param(tree, "Invert", False)

    # ── 1. Arc curve via GeometryNodeCurveArc (5.2 native) ──
    arc = safe_node(tree, "GeometryNodeCurveArc", (bx - 200, by + 200))
    color_node(arc, "curve")
    if arc is not None:
        try:
            arc.mode = "RADIUS"
        except Exception:
            pass
        link_sockets(tree, vr, arc.inputs.get("Radius", arc.inputs.get("Radius")))
        try:
            arc.inputs["Resolution"].default_value = 64
        except Exception:
            pass
        # Semicircle = π radians. The 5.2 socket is "Sweep Angle" — writing
        # "Arc Angle" raised KeyError inside try/except and silently left the
        # node's 315° default (5.4978 rad), so the vault wrapped past a
        # semicircle. Probe, don't assume.
        for _name in ("Sweep Angle", "Arc Angle"):
            _s = arc.inputs.get(_name)
            if _s is not None:
                try:
                    _s.default_value = 3.14159265359
                except Exception:
                    pass
                break

    # ── 2. Profile: Grid → MeshToCurve ──
    # Width = thickness (Z direction), Height = length (Y direction)
    profile_grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by - 100))
    color_node(profile_grid, "geometry")
    if profile_grid is not None:
        try:
            link_sockets(tree, vt, profile_grid.inputs.get("Size X", profile_grid.inputs[0]))
            link_sockets(tree, vl, profile_grid.inputs.get("Size Y", profile_grid.inputs[1]))
            profile_grid.inputs.get("Vertices X", profile_grid.inputs[2]).default_value = 2
            profile_grid.inputs.get("Vertices Y", profile_grid.inputs[3]).default_value = 2
        except Exception:
            pass

    # Convert mesh to curve for sweeping
    profile_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 200, by - 100))
    color_node(profile_curve, "curve")
    link_sockets(tree, profile_grid.outputs.get("Mesh", profile_grid.outputs[0]), profile_curve.inputs.get("Mesh", profile_curve.inputs[0]))

    # Transform profile: rotate 90° on X so it's vertical for the sweep
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

    # ── 4. Invert handling ──
    # sign = 1 - 2*invert → 1 when False, -1 when True
    sign_mul = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 300))
    sign_mul.operation = "MULTIPLY"
    link_sockets(tree, inv, sign_mul.inputs[0])
    sign_mul.inputs[1].default_value = 2.0
    color_node(sign_mul, "math")

    sign_sub = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 300))
    sign_sub.operation = "SUBTRACT"
    sign_sub.inputs[0].default_value = 1.0
    link_sockets(tree, sign_mul.outputs["Value"], sign_sub.inputs[1])
    color_node(sign_sub, "math")

    # Scale Z by sign (flip arc vertically)
    inv_tx = safe_node(tree, "GeometryNodeTransform", (bx + 500, by))
    color_node(inv_tx, "geometry")
    link_sockets(tree, sweep.outputs.get("Mesh", sweep.outputs.get("Geometry")), inv_tx.inputs.get("Geometry"))
    try:
        link_float_to_vector(tree, sign_sub.outputs["Value"], inv_tx, "Scale", defaults=(1.0, 1.0, 1.0), component=2)
    except Exception:
        pass

    # ── 5. Extrude for thickness ──
    # The vault is a swept OPEN surface, so it has no volume of its own: the
    # extrude IS the thickness. Offset is the (linked) thickness field, so
    # Offset Scale must stay 1.0 — a 0.0 default multiplied the field to zero,
    # leaving every side face coincident (1016 zero-area faces, z extent 0.0;
    # probe 2026-10-02). Both name variants probed: the 5.2 socket is
    # "Offset Scale".
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx + 700, by))
    color_node(extrude, "geometry")
    link_sockets(tree, inv_tx.outputs.get("Geometry", inv_tx.outputs.get("Mesh")), extrude.inputs.get("Mesh", extrude.inputs[0]))
    link_sockets(tree, vt, extrude.inputs.get("Offset", extrude.inputs[2]))
    _os = extrude.inputs.get("Offset Scale")
    if _os is not None:
        try:
            _os.default_value = 1.0
        except Exception:
            pass

    # ── 6. Join with incoming geometry ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 900, by))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), join.inputs.get("Geometry"))
    link_sockets(tree, extrude.outputs.get("Mesh", extrude.outputs.get("Geometry")), join.inputs.get("Geometry"))

    # ── 7. Shade smooth ──
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1100, by))
    color_node(shade, "geometry")
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, join.outputs.get("Geometry"), shade.inputs.get("Geometry"))

    # Apply universal music pass
    music_geo = apply_universal_music_pass(tree, gin, shade.outputs.get("Geometry"), (bx + 1300, by))
    link_sockets(tree, music_geo, gout.inputs.get("Geometry"))

    # ── Color nodes ──
    color_node(arc, "curve")
    color_node(profile_grid, "geometry")
    color_node(profile_curve, "curve")
    color_node(profile_tx, "geometry")
    color_node(sweep, "geometry")
    color_node(inv_tx, "geometry")
    color_node(extrude, "geometry")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_barrel_vault_ceiling", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arc", "nodes": ("arc",), "role": "curve"},
        {"title": "Profile", "nodes": ("profile_grid", "profile_curve", "profile_tx"), "role": "geometry"},
        {"title": "Sweep & Extrude", "nodes": ("sweep", "inv_tx", "extrude"), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ── Registry ──
register_builder(
    "MEL_barrel_vault_ceiling", build_barrel_vault_ceiling,
    "Barrel Vault Ceiling",
    "Curved barrel-vault ceiling panel spanning between two walls, with "
    "editable length, radius, thickness, and segment count.",
    category="structures",
)
