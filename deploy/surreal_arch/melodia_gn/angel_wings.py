"""Angel feather wing builders — parametric, mathematical, ARP-rig-attachable.

Sibling to reaver_wings.py in the wing family, different aria: where Reaver
reads horror-feminine (Lissajous spar + membrane + wound bake), the angel read
is LAYERED FEATHER. Two builders:

  MEL_angel_wing_feather_row - one wing: a cosine-rise arm arc
      P(t) = (Side*Span*t, 0, Rise*(1 - cos(pi*t/2))),  t in [0,1]
    stations resampled along it, each carrying a flat blade hung down -Z with
    a quadratic droop bow. Per-station size follows a power law
      S(t) = SizeMin + (1 - SizeMin) * t^TaperPower
    (primaries long outboard, coverts short inboard) and the row fans out by
    FanAngle * t around local Y. Side (-1/+1) mirrors the whole wing.

  MEL_angel_wing_pair        - both wings from one tree: two feather-row group
    nodes (Side -1 / +1) joined on a Root Height / Root Back offset. Built for
    the reaver carrier pattern: zero-vert host + NODES modifier + bone parent
    at the wing root (spine_03.x on character_rig).

Doctrine: variants are presets/dials, never tree copies. Blade width is
uniform in v1 (ribbon-family edge extrude) with a per-point feather_t
attribute for shader-side taper/shimmer; geometric taper is a v2 dial if the
look asks for it. Self-contained: only .core imports.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    add_float_param, add_int_param,
    color_node, label_tree, link_sockets, link_float_to_vector,
    new_geometry_tree, register_builder, safe_node, set_resample_count, sock,
)


def _g(node, *names):
    """Output socket via core.sock, first-output fallback (skirt_decor idiom)."""
    if node is None:
        return None
    try:
        s = sock(node, *names, outputs=True)
        if s is not None:
            return s
    except Exception:
        pass
    try:
        return node.outputs[0] if node.outputs else None
    except Exception:
        return None


def _i(node, *names):
    if node is None:
        return None
    try:
        return sock(node, *names)
    except Exception:
        return None


def _math(tree, loc, op, a=None, b=None, const=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n is None:
        return None
    n.operation = op
    for slot, val in ((0, a), (1, const if const is not None else b)):
        target = n.inputs[slot]
        if val is None:
            continue
        if hasattr(val, "is_linked"):
            link_sockets(tree, val, target)
        else:
            try:
                target.default_value = val
            except Exception:
                pass
    color_node(n, "math")
    return n


def _out(tree, loc, op, a=None, b=None, const=None):
    n = _math(tree, loc, op, a, b, const)
    return _g(n, "Value")


def _combine(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is None:
        return None
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        s = n.inputs[name]
        if val is None:
            try:
                s.default_value = 0.0
            except Exception:
                pass
        elif hasattr(val, "is_linked"):
            link_sockets(tree, val, s)
        else:
            try:
                s.default_value = val
            except Exception:
                pass
    color_node(n, "math")
    return _g(n, "Vector")


def build_angel_wing_feather_row(group_name="MEL_angel_wing_feather_row"):
    """One angel wing: cosine-rise arm arc with a power-law feather row."""
    tree, gin, gout = new_geometry_tree(group_name)

    count = add_int_param(tree, "Feather Count", 14, 2, 48)
    span = add_float_param(tree, "Span", 0.85, 0.3, 2.5)
    rise = add_float_param(tree, "Rise", 0.45, 0.0, 1.2)
    length = add_float_param(tree, "Blade Length", 0.42, 0.05, 0.9)
    width = add_float_param(tree, "Blade Width", 0.028, 0.005, 0.08)
    droop = add_float_param(tree, "Droop", 0.16, 0.0, 0.5)
    fan = add_float_param(tree, "Fan Angle", 0.5, 0.0, 1.05)
    taper = add_float_param(tree, "Taper Power", 1.6, 0.5, 3.0)
    size_min = add_float_param(tree, "Size Min", 0.35, 0.2, 1.0)
    segments = add_int_param(tree, "Segments", 16, 6, 48)
    side = add_int_param(tree, "Side", 1, -1, 1)

    # --- arm arc: mesh line -> cosine-rise set position -> curve -> resample
    line = safe_node(tree, "GeometryNodeMeshLine", (-1600, 0))
    line.mode = "OFFSET"
    link_sockets(tree, segments, _i(line, "Count"))
    segs_m1 = _math(tree, (-1800, 140), "SUBTRACT", a=segments, const=1)
    step = _out(tree, (-1960, 140), "DIVIDE", const=1.0, a=_g(segs_m1, "Value"))
    link_float_to_vector(tree, step, line, "Offset", component=0,
                         defaults=(1.0, 0.0, 0.0))

    idx = safe_node(tree, "GeometryNodeInputIndex", (-1800, -160))
    color_node(idx, "attribute")
    t = _out(tree, (-1640, -160), "DIVIDE", a=_g(idx, "Index"),
             b=_g(segs_m1, "Value"))

    # P(t) = (Side*Span*t, 0, Rise*(1 - cos(pi*t/2)))  -- SUBTRACT is (1 - cos)
    half = _out(tree, (-1480, -160), "MULTIPLY", const=0.5, a=t)
    arc_x = _out(tree, (-1320, -60), "MULTIPLY",
                 a=_out(tree, (-1480, -40), "MULTIPLY", a=side, b=span), b=t)
    arc_z = _out(tree, (-1320, -220), "MULTIPLY", a=rise,
                 b=_out(tree, (-1480, -280), "SUBTRACT", a=1.0,
                        b=_out(tree, (-1640, -300), "COSINE",
                               a=_out(tree, (-1800, -300), "MULTIPLY",
                                      const=math.pi, a=half))))

    setpos = safe_node(tree, "GeometryNodeSetPosition", (-1140, 0))
    link_sockets(tree, _g(line, "Mesh"), _i(setpos, "Geometry", "Mesh"))
    link_sockets(tree, _combine(tree, (-1320, 60), x=arc_x, z=arc_z),
                 _i(setpos, "Position"))

    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (-960, 0))
    link_sockets(tree, _g(setpos, "Geometry", "Mesh"),
                 _i(to_curve, "Mesh", "Geometry"))
    resample = safe_node(tree, "GeometryNodeResampleCurve", (-800, 0))
    set_resample_count(resample, count)
    link_sockets(tree, _g(to_curve, "Curve", "Geometry"),
                 _i(resample, "Curve", "Geometry"))
    arc_curve = _g(resample, "Curve", "Geometry")

    # per-station parameter: f = Index / (Feather Count - 1) on the points
    # domain (Instance Rotation/Scale evaluate against the points geometry)
    count_m1 = _math(tree, (-960, -300), "SUBTRACT", a=count, const=1)
    f = _out(tree, (-800, -220), "DIVIDE",
             a=_g(_math(tree, (-960, -220), "ADD", a=_g(idx, "Index")), "Value"),
             b=_g(count_m1, "Value"))

    # --- feather blade template: anchor at origin, hangs -Z, droop bows -X
    blade = safe_node(tree, "GeometryNodeMeshLine", (-1600, 420))
    blade.mode = "OFFSET"
    link_sockets(tree, segments, _i(blade, "Count"))
    b_step = _out(tree, (-1960, 560), "MULTIPLY", const=-1.0,
                  a=_out(tree, (-1800, 560), "DIVIDE",
                         a=length, b=_g(segs_m1, "Value")))
    link_float_to_vector(tree, b_step, blade, "Offset", component=2,
                         defaults=(0.0, 0.0, 1.0))
    b_idx = safe_node(tree, "GeometryNodeInputIndex", (-1800, 300))
    color_node(b_idx, "attribute")
    bt = _out(tree, (-1640, 300), "DIVIDE", a=_g(b_idx, "Index"),
              b=_g(segs_m1, "Value"))
    # quadratic droop toward -X (toward the body once hung on the +X wing)
    b_x = _out(tree, (-1480, 240), "MULTIPLY",
               a=_out(tree, (-1800, 660), "MULTIPLY", const=-1.0, a=droop),
               b=_out(tree, (-1640, 240), "MULTIPLY", a=bt, b=bt))
    b_pos = safe_node(tree, "GeometryNodeInputPosition", (-1800, 420))
    b_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1640, 420))
    link_sockets(tree, _g(b_pos, "Position"), b_sep.inputs["Vector"])
    b_setpos = safe_node(tree, "GeometryNodeSetPosition", (-1320, 420))
    link_sockets(tree, _g(blade, "Mesh"), _i(b_setpos, "Geometry", "Mesh"))
    link_sockets(tree, _combine(tree, (-1480, 360), x=b_x,
                                z=_g(b_sep, "Z")), _i(b_setpos, "Position"))

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (-1140, 420))
    extrude.mode = "EDGES"
    link_sockets(tree, _g(b_setpos, "Geometry", "Mesh"), _i(extrude, "Mesh"))
    link_float_to_vector(tree, width, extrude, "Offset Scale", component=0,
                         defaults=(1.0, 0.0, 0.0))
    color_node(extrude, "geometry")

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (-960, 420))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, _g(extrude, "Mesh", "Geometry"),
                 _i(shade, "Mesh", "Geometry"))

    store_t = safe_node(tree, "GeometryNodeStoreNamedAttribute", (-800, 420))
    store_t.data_type = "FLOAT"
    store_t.domain = "POINT"
    link_sockets(tree, _g(shade, "Mesh", "Geometry"),
                 _i(store_t, "Geometry", "Mesh"))
    _i(store_t, "Name").default_value = "feather_t"
    link_sockets(tree, bt, _i(store_t, "Value"))
    blade_geo = _g(store_t, "Geometry", "Mesh")

    # --- per-station: fan rotation + power-law scale S = SizeMin + (1-SizeMin)*f^p
    fan_ang = _out(tree, (-620, -220), "MULTIPLY",
                   a=_out(tree, (-800, -220), "MULTIPLY",
                          a=_out(tree, (-960, -280), "MULTIPLY", const=-1.0, a=side),
                          b=fan), b=f)
    rot = _combine(tree, (-460, -160), y=fan_ang)

    fpow = _math(tree, (-800, -380), "POWER", a=f, b=taper)
    grow = _out(tree, (-620, -380), "MULTIPLY",
                a=_out(tree, (-800, -440), "SUBTRACT", const=1.0, a=size_min),
                b=_g(fpow, "Value"))
    scale_f = _out(tree, (-460, -380), "ADD", a=size_min, b=grow)
    scale_v = _combine(tree, (-300, -300), x=scale_f, y=scale_f, z=scale_f)

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (-140, 0))
    color_node(inst, "instance")
    link_sockets(tree, arc_curve, _i(inst, "Points"))
    link_sockets(tree, blade_geo, _i(inst, "Instance"))
    link_sockets(tree, scale_v, _i(inst, "Scale"))
    link_sockets(tree, rot, _i(inst, "Rotation"))

    realized = safe_node(tree, "GeometryNodeRealizeInstances", (40, 0))
    color_node(realized, "geometry")
    link_sockets(tree, _g(inst, "Instances"), _i(realized, "Geometry"))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (220, 0))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), sock(join, "Geometry"))
    link_sockets(tree, _g(realized, "Geometry"), sock(join, "Geometry"))
    link_sockets(tree, _g(join, "Geometry"), gout.inputs.get("Geometry"))

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arm Arc", "nodes": ("line", "setpos", "to_curve", "resample"), "role": "curve"},
        {"title": "Feather Blade", "nodes": ("blade", "b_setpos", "extrude", "store_t"), "role": "geometry"},
        {"title": "Feather Row", "nodes": ("inst", "realized"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])
    return tree, gin, gout


def build_angel_wing_pair(group_name="MEL_angel_wing_pair"):
    """Both wings from one tree: Side -1 and Side +1 rows joined at the root.

    Carrier pattern: zero-vert host + NODES modifier, host bone-parented to
    spine_03.x. Root Height lifts the wings off the bone line; Root Back
    pushes them behind the spine (negative Y = toward her back).
    """
    tree, gin, gout = new_geometry_tree(group_name)

    root_h = add_float_param(tree, "Root Height", 0.12, -0.3, 0.6)
    root_b = add_float_param(tree, "Root Back", -0.06, -0.3, 0.3)

    row_group_name = "MEL_angel_wing_feather_row"
    if row_group_name not in bpy.data.node_groups:
        build_angel_wing_feather_row(row_group_name)

    frame_nodes = []
    wings = []
    for i, sd in enumerate((1, -1)):
        gn = safe_node(tree, "GeometryNodeGroup", (-600, i * 320))
        if gn is not None:
            gn.node_tree = bpy.data.node_groups.get(row_group_name)
            try:
                gn.inputs["Side"].default_value = sd
            except Exception:
                pass
        tr = safe_node(tree, "GeometryNodeTransform", (-380, i * 320))
        color_node(tr, "geometry")
        link_sockets(tree, _g(gn, "Geometry"), _i(tr, "Geometry"))
        link_sockets(tree, _combine(tree, (-560, i * 320 - 180),
                                    y=root_b, z=root_h),
                     _i(tr, "Translation"))
        frame_nodes.extend(n for n in (gn, tr) if n is not None)
        wings.append(_g(tr, "Geometry"))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (-140, 160))
    color_node(join, "geometry")
    link_sockets(tree, gin.outputs.get("Geometry"), sock(join, "Geometry"))
    for w in wings:
        link_sockets(tree, w, sock(join, "Geometry"))
    link_sockets(tree, _g(join, "Geometry"), gout.inputs.get("Geometry"))

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wings L/R", "nodes": tuple(n.name for n in frame_nodes), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])
    return tree, gin, gout


try:
    from .core import register_builder as _rb  # noqa: F401

    register_builder(
        "MEL_angel_wing_feather_row", build_angel_wing_feather_row,
        "Angel Wing Feather Row",
        "One parametric angel wing: cosine-rise arm arc, power-law feather "
        "row, fan rotation, droop bow; Side mirrors L/R",
        category="decor",
    )
    register_builder(
        "MEL_angel_wing_pair", build_angel_wing_pair,
        "Angel Wing Pair",
        "Both angel wings from one tree (Side -1/+1 rows joined) with root "
        "offset dials; carrier = zero-vert host bone-parented to spine_03.x",
        category="decor",
    )
    print("[angel_wings] registered MEL_angel_wing_feather_row + MEL_angel_wing_pair")
except ImportError:
    print("[angel_wings] standalone mode (no core registry)")


if __name__ == "__main__":
    build_angel_wing_feather_row()
    build_angel_wing_pair()
