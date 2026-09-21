"""Skirt decor kit - hem-hanging charm runs in the Nikki decor language.

The Nikki decor family (nikki_decor.py) owns guide-driven runs for architecture:
bead strings, star pendants and wall drops along eaves and walls. A garment hem is
the same device at jewellery scale, with two differences that matter:

* the guide is a CLOSED ring (the hem line), so the run wraps instead of swagging;
* the ornaments HANG below the guide, so the read is a fringe of charms, not a
  string of beads lying on a line.

Builders:
  MEL_skirt_hem_charm      - the pearl-drop template. Built so its attachment point
                             (top of the link ring) sits at local z = 0 and the body
                             hangs below, which is what makes ``Hang`` on the row
                             mean "clearance between guide and charm".
  MEL_skirt_hem_dangl_row  - N stations resampled along a guide ring, one charm per
                             station, per-station scale with deterministic jitter,
                             dropped by Hang, strung on an optional cord.

Idiom is copied from the proven family (nikki_decor.py):
* guides are NodeSocketObject params with an in-graph curve fallback, never
  hard-coded Object Info pointers;
* Set Material runs on the ornament branch BEFORE the join with host geometry;
* every parameter is a real interface socket wired into the graph - node-side
  defaults standing in for an unwired param are the silent-no-op defect.
"""

from __future__ import annotations

import bpy

from .core import (
    add_bool_param, add_float_param, add_int_param,
    color_node, label_tree, link_sockets, make_group_input,
    new_geometry_tree, register_builder, safe_node, sock,
)

GOLD_MATERIAL_NAME = "MH_MAT_Ornament_Gold"


# --------------------------------------------------------------------------
# shared helpers (same shapes as nikki_decor.py)
# --------------------------------------------------------------------------

def _gold():
    return bpy.data.materials.get(GOLD_MATERIAL_NAME)


def _is_sock(value):
    return value is not None and hasattr(value, "is_linked")


def V(node):
    """Value socket of a Math node (or None)."""
    if node is None:
        return None
    try:
        return node.outputs["Value"]
    except Exception:
        return node.outputs[0] if node.outputs else None


def _feed(tree, value, target):
    """Link a socket into `target`, or write it as a default value."""
    if target is None or value is None:
        return
    try:
        if _is_sock(value):
            link_sockets(tree, value, target)
        elif isinstance(value, (int, float, bool, tuple, list)):
            target.default_value = value
    except Exception:
        pass


def _isock(node, *names):
    """Input socket resolved through core.sock (name variants + fallback)."""
    if node is None:
        return None
    try:
        s = sock(node, *names)
        if s is not None:
            return s
    except Exception:
        pass
    return None


def _gsock(node, *names):
    """Output socket resolved through core.sock, then first-socket fallback."""
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


def _frames(*specs):
    out = []
    for spec in specs:
        title, role = spec[0], spec[1]
        nodes = spec[2:]
        out.append({"title": title, "role": role,
                    "nodes": tuple(n.name for n in nodes if n is not None)})
    return out


def _mk(tree, loc, operation, const=None, a=None, b=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n is None:
        return None
    n.operation = operation
    slot1 = const if const is not None else b
    for i, val in enumerate((a, slot1)):
        _feed(tree, val, n.inputs[i])
    color_node(n, "math")
    return n


def _out(tree, loc, operation, const=None, a=None, b=None):
    """Math node's Value socket, for read-only uses."""
    return V(_mk(tree, loc, operation, const, a, b))


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
        else:
            _feed(tree, val, s)
    color_node(n, "math")
    return n.outputs["Vector"]


def _transform(tree, loc, geom, translation=None, rotation=None, scale=None):
    n = safe_node(tree, "GeometryNodeTransform", loc)
    if n is None:
        return None
    link_sockets(tree, geom, n.inputs["Geometry"])
    _feed(tree, translation, n.inputs["Translation"])
    _feed(tree, rotation, n.inputs["Rotation"])
    _feed(tree, scale, n.inputs["Scale"])
    color_node(n, "geometry")
    return _gsock(n, "Geometry")


def _set_position(tree, loc, geom, offset=None, position=None):
    n = safe_node(tree, "GeometryNodeSetPosition", loc)
    if n is None:
        return None
    link_sockets(tree, geom, n.inputs["Geometry"])
    _feed(tree, position, n.inputs["Position"])
    _feed(tree, offset, n.inputs["Offset"])
    color_node(n, "geometry")
    return _gsock(n, "Geometry")


def _join(tree, loc, geoms):
    n = safe_node(tree, "GeometryNodeJoinGeometry", loc)
    if n is None:
        return None
    for g in geoms:
        if g is None:
            continue
        try:
            link_sockets(tree, g, n.inputs["Geometry"])
        except Exception:
            pass
    color_node(n, "geometry")
    return _gsock(n, "Geometry")


def _shade(tree, loc, geom, smooth=True):
    n = safe_node(tree, "GeometryNodeSetShadeSmooth", loc)
    if n is None:
        return geom
    link_sockets(tree, geom, n.inputs["Mesh"])
    _feed(tree, smooth, n.inputs["Shade Smooth"])
    color_node(n, "geometry")
    return _gsock(n, "Mesh")


def _set_material(tree, loc, geom, material_sock=None):
    n = safe_node(tree, "GeometryNodeSetMaterial", loc)
    if n is None:
        return geom
    link_sockets(tree, geom, n.inputs["Geometry"])
    if material_sock is not None:
        link_sockets(tree, material_sock, n.inputs["Material"])
    color_node(n, "material")
    return _gsock(n, "Geometry")


def _material_param(tree, name="Material"):
    return make_group_input(tree, "NodeSocketMaterial", name, default=_gold())


def _guide_param(tree, name="Guide"):
    return make_group_input(tree, "NodeSocketObject", name, default=None)


def _guide_params(tree):
    """Guide object param + in-graph curve fallback (family convention)."""
    obj = _guide_param(tree, "Guide")
    curve = None
    try:
        curve = make_group_input(tree, "NodeSocketGeometry", "Guide Curve")
    except Exception:
        pass
    use_curve = add_bool_param(tree, "Guide From Curve", False)
    return obj, curve, use_curve


def _guide_geometry(tree, loc, guide_sock, curve_sock=None, use_curve_sock=None):
    """Guide object -> geometry in the HOST's local space (RELATIVE is load-bearing)."""
    n = safe_node(tree, "GeometryNodeObjectInfo", loc)
    if n is None:
        return None
    try:
        n.transform_space = "RELATIVE"
    except Exception:
        pass
    if guide_sock is not None:
        link_sockets(tree, guide_sock, n.inputs["Object"])
    color_node(n, "curve")
    if curve_sock is None or use_curve_sock is None:
        return _gsock(n, "Geometry")
    sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 180, loc[1] - 160))
    if sw is None:
        return _gsock(n, "Geometry")
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, _gsock(n, "Geometry"), sw.inputs["False"])
    link_sockets(tree, curve_sock, sw.inputs["True"])
    link_sockets(tree, use_curve_sock, sw.inputs["Switch"])
    return _gsock(sw, "Output")


def _ensure_group_node(tree, group_name, builder, loc):
    if group_name not in bpy.data.node_groups and builder is not None:
        try:
            builder(group_name)
        except Exception:
            return None
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node is not None:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def _resample(tree, loc, curve_sock, count_sock):
    n = safe_node(tree, "GeometryNodeResampleCurve", loc)
    if n is None:
        return curve_sock
    try:
        n.mode = "COUNT"
    except Exception:
        pass
    link_sockets(tree, curve_sock, n.inputs["Curve"])
    link_sockets(tree, count_sock, n.inputs["Count"])
    color_node(n, "curve")
    return _gsock(n, "Curve")


def _sweep_circle(tree, loc, curve_sock, radius_sock, resolution=8):
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1] - 240))
    color_node(profile, "curve")
    if profile is not None:
        _feed(tree, int(resolution), _isock(profile, "Resolution"))
        link_sockets(tree, radius_sock, _isock(profile, "Radius"))
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", loc)
    if sweep is None:
        return None
    link_sockets(tree, curve_sock, sweep.inputs["Curve"])
    if profile is not None:
        link_sockets(tree, _gsock(profile, "Curve"), sweep.inputs["Profile Curve"])
    color_node(sweep, "geometry")
    return _gsock(sweep, "Mesh")


def _geometry_switch(tree, loc, condition_sock, when_true, when_false=None):
    n = safe_node(tree, "GeometryNodeSwitch", loc)
    if n is None:
        return None
    try:
        n.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, condition_sock, n.inputs["Switch"])
    _feed(tree, when_true, n.inputs["True"])
    _feed(tree, when_false, n.inputs["False"])
    color_node(n, "geometry")
    return _gsock(n, "Output")


def _finish(tree, gin, gout, ornament_sock, material_sock, loc=(1180, 0)):
    """Set material on the ornament branch, then join it onto the host geometry."""
    orn = _set_material(tree, loc, ornament_sock, material_sock=material_sock)
    merged = _join(tree, (loc[0] + 180, 0), [gin.outputs["Geometry"], orn])
    link_sockets(tree, merged, gout.inputs["Geometry"])
    return merged


# --------------------------------------------------------------------------
# 1. MEL_skirt_hem_charm - the pearl-drop template
# --------------------------------------------------------------------------

def build_skirt_hem_charm(group_name="MEL_skirt_hem_charm"):
    """Pearl-drop charm: pearl + cap + link ring.

    Origin is the ATTACHMENT POINT: the top of the link ring sits at local z = 0 and
    the body hangs below, so an instance placed on a hem guide at Hang = 0 touches
    the guide and any Hang value reads as clearance.

    Params:
        Pearl Radius: pearl sphere radius (drives the whole charm's mass)
        Cap Height:   cone cap height
        Link Radius:  hanging link ring radius
    """
    tree, gin, gout = new_geometry_tree(group_name)
    r = add_float_param(tree, "Pearl Radius", 0.011, 0.002, 0.05)
    cap = add_float_param(tree, "Cap Height", 0.006, 0.001, 0.03)
    link = add_float_param(tree, "Link Radius", 0.0045, 0.001, 0.02)
    mat = _material_param(tree)

    # ---- pearl ----------------------------------------------------------
    pearl = safe_node(tree, "GeometryNodeMeshUVSphere", (-640, 240))
    _feed(tree, 16, _isock(pearl, "Segments"))
    _feed(tree, 12, _isock(pearl, "Rings"))
    _feed(tree, r, _isock(pearl, "Radius"))
    pearl_g = _shade(tree, (-440, 240), _gsock(pearl, "Mesh"), smooth=True)

    # ---- cap cone above the pearl ---------------------------------------
    cone = safe_node(tree, "GeometryNodeMeshCone", (-640, -40))
    _feed(tree, 12, _isock(cone, "Vertices"))
    _feed(tree, _out(tree, (-840, -40), "MULTIPLY", 0.42, a=r), _isock(cone, "Radius 1"))
    _feed(tree, 0.0, _isock(cone, "Radius 2"))
    _feed(tree, cap, _isock(cone, "Depth"))
    z_cap = _out(tree, (-840, -200), "ADD", a=r,
                 b=_out(tree, (-1000, -200), "MULTIPLY", 0.5, a=cap))
    cone_g = _transform(tree, (-440, -40), _gsock(cone, "Mesh"),
                        translation=_combine(tree, (-620, -200), z=z_cap))

    # ---- link ring, standing in XZ --------------------------------------
    torus = safe_node(tree, "GeometryNodeMeshTorus", (-640, -340))
    _feed(tree, 10, _isock(torus, "Major Segments"))
    _feed(tree, 6, _isock(torus, "Minor Segments"))
    _feed(tree, link, _isock(torus, "Major Radius"))
    _feed(tree, 0.0016, _isock(torus, "Minor Radius"))
    z_link = _out(tree, (-840, -500), "ADD",
                  a=_out(tree, (-1000, -500), "ADD", a=r, b=cap),
                  b=link)
    rot90x = _combine(tree, (-1000, -620), x=1.5708)
    link_g = _transform(tree, (-440, -340), _gsock(torus, "Mesh"),
                        translation=_combine(tree, (-620, -500), z=z_link),
                        rotation=rot90x)

    # ---- shift so the attachment point sits at local z = 0 --------------
    shift = _out(tree, (-260, -760), "MULTIPLY", -1.0,
                 a=_out(tree, (-420, -760), "ADD",
                        a=_out(tree, (-580, -760), "ADD", a=r, b=cap),
                        b=_out(tree, (-580, -880), "MULTIPLY", 2.0, a=link)))
    joined = _join(tree, (-60, 0), [pearl_g, cone_g, link_g])
    body = _transform(tree, (120, 0), joined,
                      translation=_combine(tree, (-60, -760), z=shift))
    orn = _set_material(tree, (300, 0), body, material_sock=mat)
    link_sockets(tree, orn, gout.inputs["Geometry"])

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Pearl, Cap, Link", "geometry", pearl, cone, torus),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 2. MEL_skirt_hem_dangl_row - charms hanging from a guide ring
# --------------------------------------------------------------------------

def build_skirt_hem_dangl_row(group_name="MEL_skirt_hem_dangl_row"):
    """A fringe of charms hanging from a guide ring - the skirt-hem decor run.

    Guide = a closed curve drawn around the hem (the authoring handle, or the
    in-graph ``Guide Curve`` geometry). Stations are resampled along it; each
    station carries one MEL_skirt_hem_charm, scaled by Charm Scale with
    deterministic jitter, dropped by Hang, strung on an optional cord.

    Params:
        Station Count: charms around the ring (12 = one per chromatic step)
        Charm Scale:   instance scale (1.0 = template size)
        Hang:          extra drop below the guide (m)
        Jitter:        per-station scale variation (deterministic, seeded by Index)
        Cord Radius:   the cord the charms hang from
        Show Cord:     draw the cord ring
    """
    tree, gin, gout = new_geometry_tree(group_name)
    guide, guide_curve, use_curve = _guide_params(tree)
    stations = add_int_param(tree, "Station Count", 12, 1, 200)
    charm_scale = add_float_param(tree, "Charm Scale", 1.0, 0.05, 4.0)
    hang = add_float_param(tree, "Hang", 0.0, 0.0, 0.5)
    jitter = add_float_param(tree, "Jitter", 0.18, 0.0, 1.0)
    cord_r = add_float_param(tree, "Cord Radius", 0.0018, 0.0005, 0.02)
    show_cord = add_bool_param(tree, "Show Cord", True)
    mat = _material_param(tree)

    guide_geom = _guide_geometry(tree, (-1460, 0), guide, guide_curve, use_curve)
    points = _resample(tree, (-1260, 120), guide_geom, stations)
    hung = _set_position(tree, (-1040, 120), points,
                         offset=_combine(tree, (-1200, -120),
                                         z=_out(tree, (-1360, -120), "MULTIPLY", -1.0, a=hang)))

    # deterministic jitter: 1 + Jitter * sin(Index * 12.9898)   [bead-string idiom]
    idx = safe_node(tree, "GeometryNodeInputIndex", (-1200, -420))
    color_node(idx, "attribute")
    phase = _mk(tree, (-1040, -420), "MULTIPLY", 12.9898, a=_gsock(idx, "Index"))
    wave = _mk(tree, (-880, -420), "SINE", a=V(phase))
    jmul = _mk(tree, (-720, -420), "MULTIPLY", a=V(wave), b=jitter)
    jf = _mk(tree, (-560, -420), "ADD", 1.0, a=V(jmul))
    size_f = _mk(tree, (-400, -300), "MULTIPLY", a=charm_scale, b=V(jf))
    size_v = _combine(tree, (-240, -300), x=V(size_f), y=V(size_f), z=V(size_f))

    charm_grp = _ensure_group_node(tree, "MEL_skirt_hem_charm", build_skirt_hem_charm, (-240, 320))
    charms = safe_node(tree, "GeometryNodeInstanceOnPoints", (60, 120))
    color_node(charms, "instance")
    if charms is not None:
        link_sockets(tree, hung, charms.inputs["Points"])
        link_sockets(tree, _gsock(charm_grp, "Geometry"), charms.inputs["Instance"])
        link_sockets(tree, size_v, charms.inputs["Scale"])

    realized = safe_node(tree, "GeometryNodeRealizeInstances", (240, 120))
    color_node(realized, "geometry")
    link_sockets(tree, _gsock(charms, "Instances"), realized.inputs["Geometry"])

    cord = _sweep_circle(tree, (-1040, -340), guide_geom, cord_r)
    cord_used = _geometry_switch(tree, (-840, -340), show_cord, cord)

    orn = _join(tree, (420, 0), [cord_used, _gsock(realized, "Geometry")])
    _finish(tree, gin, gout, orn, mat, (600, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Guide + Cord", "curve", guide_geom, cord, cord_used),
        ("Charm Row", "instance", points, hung, charm_grp, charms, realized),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# addon registration
# --------------------------------------------------------------------------

try:
    from .core import register_builder  # noqa: E402

    register_builder(
        "MEL_skirt_hem_charm", build_skirt_hem_charm,
        "Skirt Hem Charm",
        "Pearl-drop charm hanging from its attachment point; the hem row's unit ornament",
        category="decor",
    )
    register_builder(
        "MEL_skirt_hem_dangl_row", build_skirt_hem_dangl_row,
        "Skirt Hem Dangl Row",
        "Charms hanging from a guide ring: stations resampled along the hem, scale jitter, optional cord",
        category="decor",
    )
    print("[skirt_decor] registered MEL_skirt_hem_charm + MEL_skirt_hem_dangl_row")
except ImportError:
    print("[skirt_decor] standalone mode (no core registry)")


if __name__ == "__main__":
    build_skirt_hem_charm()
    build_skirt_hem_dangl_row()
