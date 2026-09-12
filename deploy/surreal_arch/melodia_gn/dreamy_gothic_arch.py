"""MEL_dreamy_gothic_arch — slim lancet arch with gold tracery inlay.

A slimmer, more ornate re-imagining of the existing Gothic portal arch
(MEL_gothic_arch in euro_kit.py / build_gothic_portal in gothic_kit.py).

Produces a pointed lancet arch (two circular arcs meeting at a sharp apex)
with a thin gold tracery inlay tracing the outer perimeter, placed slightly
proud so it reads as a filigreed wire.

Builder path (GN tree builders), NOT the greybox kit path.
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_bool_param, register_builder,
)


# ──────────────────────────────────────────────────────────────────────
# Low-level helpers
# ──────────────────────────────────────────────────────────────────────

def _lancet_arch_path(tree, width, height, radius=None, x=0, y=0, label="lancet"):
    """Build the full pointed lancet arch outline as a single joined curve.

    Two circular arcs (GeometryNodeCurveArc) meet at a sharp apex; a MeshLine
    closes the base.  All three pieces are converted to curves and joined.

    radius — circle radius.  If None, defaults to width/2 so the arcs are
             tangent at the apex (sharp point).  A larger radius produces a
             blunter Gothic peak; a smaller one makes a sharper lancet.
    """
    half_W = width * 0.5
    if radius is None:
        # Tangent-at-apex: R = half_W → arcs meet at exactly (0, height)
        radius = half_W
    # peak angle measured from horizontal at each arc center
    cos_peak = (radius - half_W) / max(radius, 0.001)
    peak_angle = math.acos(min(1.0, max(-1.0, cos_peak)))
    # Vertical offset of arc center from base
    cy = math.sqrt(max(0.0, radius * radius - half_W * half_W))
    base_y = height - cy  # base of the arch opening sits at y=0

    res = 48

    # ── Right arc: from bottom-right to apex ──
    right_arc = safe_node(tree, "GeometryNodeCurveArc", (x, y + 150))
    if right_arc is None:
        return None
    try:
        right_arc.mode = "RADIUS"
        right_arc.inputs["Resolution"].default_value = res
        right_arc.inputs["Radius"].default_value = radius
        right_arc.inputs["Start Angle"].default_value = math.pi - peak_angle
        right_arc.inputs["Sweep Angle"].default_value = peak_angle
    except Exception:
        pass
    color_node(right_arc, label)

    right_t = safe_node(tree, "GeometryNodeTransform", (x + 250, y + 150))
    if right_t is None:
        return None
    # Arc center: right side, at height `cy` above base
    right_t.inputs["Translation"].default_value = (half_W - radius + half_W, 0, base_y)
    right_t.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    link_sockets(tree, right_arc.outputs["Curve"], right_t.inputs["Geometry"])
    color_node(right_t, label)

    # ── Left arc: from apex to bottom-left ──
    left_arc = safe_node(tree, "GeometryNodeCurveArc", (x, y - 150))
    try:
        left_arc.mode = "RADIUS"
        left_arc.inputs["Resolution"].default_value = res
        left_arc.inputs["Radius"].default_value = radius
        left_arc.inputs["Start Angle"].default_value = math.pi * 0.5 + peak_angle
        left_arc.inputs["Sweep Angle"].default_value = peak_angle
    except Exception:
        pass
    color_node(left_arc, label)

    left_t = safe_node(tree, "GeometryNodeTransform", (x + 250, y - 150))
    if left_t is None:
        return None
    # Mirror the right arc: negative X offset
    left_t.inputs["Translation"].default_value = (-(half_W - radius + half_W), 0, base_y)
    left_t.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    link_sockets(tree, left_arc.outputs["Curve"], left_t.inputs["Geometry"])
    color_node(left_arc, label)
    color_node(left_t, label)

    # ── Base line: bottom-left → bottom-right (closes the arch opening) ──
    base_line = safe_node(tree, "GeometryNodeMeshLine", (x, y - 350))
    if base_line is not None:
        base_line.mode = "END_POINTS"
        base_line.inputs["Count"].default_value = 2
        try:
            base_line.inputs["Start Location"].default_value = (-half_W, 0, 0)
            base_line.inputs["End Location"].default_value = (half_W, 0, 0)
        except Exception:
            pass
        color_node(base_line, label)
        to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (x + 200, y - 350))
        if to_curve is not None:
            link_sockets(tree, base_line.outputs["Mesh"],
                         to_curve.inputs.get("Mesh") or to_curve.inputs[0])
            color_node(to_curve, label)
            base_curve = to_curve.outputs.get("Curve") or to_curve.outputs.get("Geometry")
        else:
            base_curve = None
    else:
        base_curve = None

    # ── Join all three curve pieces ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (x + 500, y))
    color_node(join, label)
    link_sockets(tree, right_t.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, left_t.outputs["Geometry"], join.inputs["Geometry"])
    if base_curve is not None:
        link_sockets(tree, base_curve, join.inputs["Geometry"])

    return join.outputs["Geometry"]


def _sweep_profile(tree, curve_sock, radius, x=0, y=0, label="arch", res=16):
    """Sweep a circular profile along a curve to produce a solid mesh.

    Returns the Mesh output socket.
    """
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x - 200, y))
    if profile is None:
        profile = safe_node(tree, "GeometryNodeMeshCircle", (x - 200, y))
    try:
        profile.inputs["Resolution"].default_value = res
        profile.inputs["Radius"].default_value = radius
    except Exception:
        pass
    color_node(profile, label)

    c2m = safe_node(tree, "GeometryNodeCurveToMesh", (x, y))
    if c2m is None:
        return None
    link_sockets(tree, curve_sock, c2m.inputs.get("Curve") or c2m.inputs[0])
    prof_in = c2m.inputs.get("Profile Curve") or c2m.inputs.get("Profile")
    if prof_in is not None:
        link_sockets(tree, profile.outputs.get("Curve") or profile.outputs[0], prof_in)
    try:
        c2m.inputs["Fill Caps"].default_value = True
    except Exception:
        pass
    color_node(c2m, label)
    return c2m.outputs.get("Mesh") or c2m.outputs.get("Geometry")


def _make_math(tree, op, a, b=None, loc=(0, 0)):
    """Create a ShaderNodeMath with operation and inputs preset. Returns the node."""
    m = safe_node(tree, "ShaderNodeMath", loc)
    if m is not None:
        m.operation = op
        if a is not None:
            try:
                m.inputs[0].default_value = a
            except Exception:
                pass
        if b is not None:
            try:
                m.inputs[1].default_value = b
            except Exception:
                pass
    color_node(m, "math")
    return m


def _make_combine_xyz(tree, x=None, y=None, z=None, loc=(0, 0)):
    """Create a ShaderNodeCombineXYZ with optional inputs preset."""
    c = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if c is not None:
        if x is not None:
            c.inputs["X"].default_value = x
        if y is not None:
            c.inputs["Y"].default_value = y
        if z is not None:
            c.inputs["Z"].default_value = z
    color_node(c, "math")
    return c


# ──────────────────────────────────────────────────────────────────────
# BUILDER
# ──────────────────────────────────────────────────────────────────────

def build_dreamy_gothic_arch(group_name="MEL_dreamy_gothic_arch"):
    """Slim lancet arch with gold tracery inlay along the perimeter.

    Parameters:
      Arch Width      — span of the arch opening (default 1.2 m)
      Arch Height     — tip-to-base height (default 2.4 m)
      Arch Thickness  — wall/limb thickness (default 0.25 m)
      Tracery Depth   — width of the gold inlay strip (default 0.08 m)
      Gold Inlay      — toggle the gold tracery perimeter (default True)
      Gold Offset     — how far gold sits proud outward (default 0.005 m)

    The arch is a pointed lancet (two circular arcs meeting at a sharp apex),
    swept with a circular profile. The gold tracery is a second swept profile
    along the outer perimeter, slightly proud, tracing the silhouette like a
    filigreed wire.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Arch Width", 1.2, 0.1, 10.0,
                    "Span of the lancet arch")
    add_float_param(tree, "Arch Height", 2.4, 0.2, 20.0,
                    "Height from base to apex")
    add_float_param(tree, "Arch Thickness", 0.25, 0.05, 1.0,
                    "Wall/limb thickness")
    add_float_param(tree, "Tracery Depth", 0.08, 0.01, 0.5,
                    "Width of the gold inlay strip")
    add_bool_param(tree, "Gold Inlay", True,
                   "Toggle gold tracery perimeter inlay")
    add_float_param(tree, "Gold Offset", 0.005, 0.0, 0.05,
                    "How far gold sits proud of stone surface")

    # ── 1. Main arch path (lancet: two circle arcs + base line) ──
    arch_path = _lancet_arch_path(
        tree, width=1.0, height=1.0, x=bx, y=by, label="lancet"
    )

    # ── 2. Scale arch path to actual dimensions ──
    scale_arch = safe_node(tree, "GeometryNodeTransform", (bx + 400, by))
    if scale_arch is not None and arch_path is not None:
        link_sockets(tree, arch_path, scale_arch.inputs["Geometry"])
        # Scale: X = Arch Width, Z = Arch Height, Y = 0 (2D in XZ plane)
        scale_combine = _make_combine_xyz(tree, x=None, y=0.0, z=None, loc=(bx + 200, by))
        if scale_combine is not None:
            link_sockets(tree, gin.outputs["Arch Width"], scale_combine.inputs["X"])
            link_sockets(tree, gin.outputs["Arch Height"], scale_combine.inputs["Z"])
            link_sockets(tree, scale_combine.outputs["Vector"], scale_arch.inputs["Scale"])
            color_node(scale_combine, "math")
        color_node(scale_arch, "lancet")
        arch_path = scale_arch.outputs["Geometry"]

    # ── 3. Sweep main arch solid (profile radius = Arch Thickness / 2) ──
    half_thick = _make_math(tree, "MULTIPLY", None, 0.5, loc=(bx + 100, by - 200))
    if half_thick is not None:
        link_sockets(tree, gin.outputs["Arch Thickness"], half_thick.inputs[0])
        color_node(half_thick, "math")

    arch_mesh = _sweep_profile(
        tree, arch_path,
        radius=0.01,  # will be scaled below
        x=bx + 700, y=by,
        label="arch",
    )

    # Scale the swept arch mesh: X = Arch Thickness * 0.5, Z = Arch Thickness * 0.5
    if arch_mesh is not None and half_thick is not None:
        scale_mesh = safe_node(tree, "GeometryNodeTransform", (bx + 900, by))
        link_sockets(tree, arch_mesh, scale_mesh.inputs["Geometry"])
        th_combine = _make_combine_xyz(tree, x=None, y=0.0, z=None, loc=(bx + 750, by))
        if th_combine is not None:
            link_sockets(tree, half_thick.outputs["Value"], th_combine.inputs["X"])
            link_sockets(tree, half_thick.outputs["Value"], th_combine.inputs["Z"])
            link_sockets(tree, th_combine.outputs["Vector"], scale_mesh.inputs["Scale"])
            color_node(th_combine, "math")
        color_node(scale_mesh, "arch")
        arch_mesh = scale_mesh.outputs["Geometry"]

    # ── 4. Gold tracery inlay ──
    # Build a second, slightly larger arch path for the gold wire.
    # We scale the normalized path by Arch Width + 2*Gold Offset, Arch Height + Gold Offset,
    # so the gold traces the outer silhouette.
    gold_geom = None
    has_gold = gin.outputs.get("Gold Inlay")

    if has_gold is not None:
        # Gold path (independent copy of the lancet path)
        gold_path = _lancet_arch_path(
            tree, width=1.0, height=1.0, x=bx, y=by + 300, label="tracery"
        )

        if gold_path is not None:
            gold_scale = safe_node(tree, "GeometryNodeTransform", (bx + 400, by + 300))
            link_sockets(tree, gold_path, gold_scale.inputs["Geometry"])

            # Gold width = Arch Width + 2 * Gold Offset (wider to sit proud)
            gold_w = _make_math(tree, "MULTIPLY", None, 2.0, loc=(bx + 100, by + 300))
            if gold_w is not None:
                link_sockets(tree, gin.outputs["Gold Offset"], gold_w.inputs[0])
                color_node(gold_w, "math")

            gold_width = _make_math(tree, "ADD", None, None, loc=(bx + 250, by + 300))
            if gold_width is not None:
                link_sockets(tree, gin.outputs["Arch Width"], gold_width.inputs[0])
                if gold_w is not None:
                    link_sockets(tree, gold_w.outputs["Value"], gold_width.inputs[1])
                color_node(gold_width, "math")

            # Gold height = Arch Height + 2 * Gold Offset
            gold_h2 = _make_math(tree, "MULTIPLY", None, 2.0, loc=(bx + 100, by + 350))
            if gold_h2 is not None:
                link_sockets(tree, gin.outputs["Gold Offset"], gold_h2.inputs[0])
                color_node(gold_h2, "math")

            gold_height = _make_math(tree, "ADD", None, None, loc=(bx + 250, by + 350))
            if gold_height is not None:
                link_sockets(tree, gin.outputs["Arch Height"], gold_height.inputs[0])
                if gold_h2 is not None:
                    link_sockets(tree, gold_h2.outputs["Value"], gold_height.inputs[1])
                color_node(gold_height, "math")

            g_combine = _make_combine_xyz(tree, x=None, y=0.0, z=None, loc=(bx + 400, by + 300))
            if g_combine is not None and gold_width is not None and gold_height is not None:
                link_sockets(tree, gold_width.outputs["Value"], g_combine.inputs["X"])
                link_sockets(tree, gold_height.outputs["Value"], g_combine.inputs["Z"])
                link_sockets(tree, g_combine.outputs["Vector"], gold_scale.inputs["Scale"])
                color_node(g_combine, "math")
            color_node(gold_scale, "tracery")

            gold_path_scaled = gold_scale.outputs["Geometry"]

            # Sweep gold profile: radius = Tracery Depth / 2
            gold_half_depth = _make_math(tree, "MULTIPLY", None, 0.5, loc=(bx + 100, by + 500))
            if gold_half_depth is not None:
                link_sockets(tree, gin.outputs["Tracery Depth"], gold_half_depth.inputs[0])
                color_node(gold_half_depth, "math")

            gold_mesh = _sweep_profile(
                tree, gold_path_scaled,
                radius=0.01,  # will be scaled below
                x=bx + 700, y=by + 300,
                label="tracery",
            )

            # Scale gold mesh: profile radius = Tracery Depth / 2
            if gold_mesh is not None and gold_half_depth is not None:
                gold_scale_mesh = safe_node(tree, "GeometryNodeTransform", (bx + 900, by + 300))
                link_sockets(tree, gold_mesh, gold_scale_mesh.inputs["Geometry"])
                gd_combine = _make_combine_xyz(tree, x=None, y=0.0, z=None, loc=(bx + 750, by + 300))
                if gd_combine is not None:
                    link_sockets(tree, gold_half_depth.outputs["Value"], gd_combine.inputs["X"])
                    link_sockets(tree, gold_half_depth.outputs["Value"], gd_combine.inputs["Z"])
                    link_sockets(tree, gd_combine.outputs["Vector"], gold_scale_mesh.inputs["Scale"])
                    color_node(gd_combine, "math")
                color_node(gold_scale_mesh, "tracery")
                gold_mesh = gold_scale_mesh.outputs["Geometry"]

            # Switch to toggle gold on/off
            if gold_mesh is not None:
                gold_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 1200, by + 300))
                try:
                    gold_switch.input_type = "GEOMETRY"
                except Exception:
                    pass
                link_sockets(tree, has_gold, gold_switch.inputs["Switch"])
                gold_true = gold_switch.inputs.get("True") or gold_switch.inputs.get("TRUE")
                link_sockets(tree, gold_mesh, gold_true)
                gold_geom = gold_switch.outputs.get("Output") or gold_switch.outputs.get("Geometry")
                color_node(gold_switch, "instance")

    # ── 5. Join main arch + gold tracery ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1500, by))
    color_node(join, "output")
    link_sockets(tree, arch_mesh, join.inputs["Geometry"])
    if gold_geom is not None:
        link_sockets(tree, gold_geom, join.inputs["Geometry"])

    # ── 6. Smooth ──
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1700, by))
    if shade is not None:
        shade.inputs["Shade Smooth"].default_value = True
        link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
        color_node(shade, "output")
        final_geo = shade.outputs["Geometry"]
    else:
        final_geo = join.outputs["Geometry"]

    link_sockets(tree, final_geo, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arch Profile", "nodes": ("arc", "curve", "lancet", "transform", "scale", "join"), "role": "curve"},
        {"title": "Gold Tracery", "nodes": ("gold", "tracery", "switch"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# ──────────────────────────────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────────────────────────────

register_builder(
    "MEL_dreamy_gothic_arch", build_dreamy_gothic_arch,
    "Dreamy Gothic Arch",
    "Slim lancet arch with gold tracery inlay along the perimeter.",
    category="ornament",
)
