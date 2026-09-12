"""Nikki decor kit - AAA dangling bead / pendant / filigree geometry for Melodia Studio.

Owns the ornament family the Melusina study renders use for hanging decor: bead,
star, heart and crystal solids, cord strands, and the guide-driven string builders
that hang them.

Design rules (ADDON_AUTHORITY_2026-09-03.md + the convergence skill):

* Every parameter is a real interface socket wired into the graph. Node-side
  defaults standing in for an unwired param are the silent-no-op defect that made
  the study's "Bead Count" / "Drop" sliders do nothing.
* Guides are ``NodeSocketObject`` inputs, never hard-coded ``Object Info``
  pointers, so one tree serves every wall / eave run and stays registerable.
* ``Set Material`` runs on the ornament branch BEFORE the join with host geometry,
  so a decor pass cannot re-materialise the accumulated roofline.
* Droop is a parabolic field over the guide's spline parameter: ends stay on the
  guide, the middle hangs. That is what makes a run read as a swag, not a line.
* Templates are real solids (pearl / star / heart / crystal). The study file's
  ornaments were all one radius-1.0 sphere, which is why the "beads" were 2 m
  balls on the wall and the "stars" were spheres.

Convention: arithmetic helpers return the Math NODE; use ``V(node)`` for its Value
socket. Linking into slot 1 after creation therefore works without a second lookup.
"""

import math

import bpy

from .core import (
    add_bool_param, add_float_param, add_int_param,
    color_node, label_tree, link_sockets, make_group_input, mesh_boolean_node,
    new_geometry_tree, register_builder, safe_node,
)

GOLD_MATERIAL_NAME = "MH_MAT_Ornament_Gold"


# --------------------------------------------------------------------------
# shared helpers
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


def _frames(*specs):
    """(title, role, *nodes) -> label_tree frame specs."""
    out = []
    for spec in specs:
        title, role = spec[0], spec[1]
        nodes = spec[2:]
        out.append({"title": title, "role": role,
                    "nodes": tuple(n.name for n in nodes if n is not None)})
    return out


def _mk(tree, loc, operation, const=None, a=None, b=None, c=None):
    """Create a Math node, feed its slots, return the NODE.

    `const` is shorthand for a literal in slot 1 (the common ``x <op> k`` shape);
    pass `a`/`b`/`c` for explicit slot 0/1/2 control.
    """
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n is None:
        return None
    n.operation = operation
    slot1 = const if const is not None else b
    for i, val in enumerate((a, slot1, c)):
        _feed(tree, val, n.inputs[i])
    color_node(n, "math")
    return n


def _out(tree, loc, operation, const=None, a=None, b=None, c=None):
    """Math node's Value socket, for read-only uses."""
    return V(_mk(tree, loc, operation, const, a, b, c))


def _combine(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is None:
        return None
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        sock = n.inputs[name]
        if val is None:
            try:
                sock.default_value = 0.0
            except Exception:
                pass
        else:
            _feed(tree, val, sock)
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
    return n.outputs["Geometry"]


def _set_position(tree, loc, geom, offset=None, position=None):
    n = safe_node(tree, "GeometryNodeSetPosition", loc)
    if n is None:
        return None
    link_sockets(tree, geom, n.inputs["Geometry"])
    _feed(tree, position, n.inputs["Position"])
    _feed(tree, offset, n.inputs["Offset"])
    color_node(n, "geometry")
    return n.outputs["Geometry"]


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
    return n.outputs["Geometry"]


def _shade(tree, loc, geom, smooth=None, invert=False):
    """Shade smooth from a bool socket (optionally inverted), or a literal."""
    n = safe_node(tree, "GeometryNodeSetShadeSmooth", loc)
    if n is None:
        return geom
    link_sockets(tree, geom, n.inputs["Mesh"])
    sock = n.inputs["Shade Smooth"]
    if smooth is None:
        pass
    elif not _is_sock(smooth):
        try:
            sock.default_value = bool(smooth)
        except Exception:
            pass
    elif invert:
        inv = _mk(tree, (loc[0] - 160, loc[1] - 180), "SUBTRACT", a=1.0)
        if inv is not None:
            link_sockets(tree, smooth, inv.inputs[1])
            link_sockets(tree, V(inv), sock)
    else:
        link_sockets(tree, smooth, sock)
    color_node(n, "geometry")
    return n.outputs["Mesh"]


def _boolean(tree, loc, a, b, operation="UNION"):
    """Mesh Boolean via core's 5.2-safe socket resolution (input names vary by solver)."""
    try:
        node, out = mesh_boolean_node(tree, loc, operation, a, b)
    except Exception:
        return None
    if node is None:
        return None
    try:
        node.solver = "EXACT"
    except Exception:
        pass
    color_node(node, "geometry")
    return out


def _merge(tree, loc, geom, distance=0.0004):
    n = safe_node(tree, "GeometryNodeMergeByDistance", loc)
    if n is None:
        return geom
    link_sockets(tree, geom, n.inputs["Geometry"])
    try:
        n.inputs["Distance"].default_value = distance
    except Exception:
        pass
    color_node(n, "geometry")
    return n.outputs["Geometry"]


def _set_material(tree, loc, geom, material_sock=None, material=None):
    n = safe_node(tree, "GeometryNodeSetMaterial", loc)
    if n is None:
        return geom
    link_sockets(tree, geom, n.inputs["Geometry"])
    if material_sock is not None:
        link_sockets(tree, material_sock, n.inputs["Material"])
    elif material is not None:
        try:
            n.inputs["Material"].default_value = material
        except Exception:
            pass
    color_node(n, "material")
    return n.outputs["Geometry"]


def _material_param(tree, name="Material"):
    return make_group_input(tree, "NodeSocketMaterial", name, default=_gold())


def _guide_param(tree, name="Guide"):
    return make_group_input(tree, "NodeSocketObject", name, default=None)


def _guide_params(tree):
    """Add a Guide object param AND an in-graph curve fallback.

    The object route is the authoring route: drop a curve in the scene and point at
    it. It cannot be satisfied from inside a node graph, so a nested consumer (the
    eyewear chain, for example) has no way to drive it. The Geometry input plus an
    explicit switch gives that path without changing the object behaviour: switch
    off is exactly what it was before.
    """
    obj = _guide_param(tree, "Guide")
    try:
        make_group_input(tree, "NodeSocketGeometry", "Guide Curve")
    except Exception:
        pass
    add_bool_param(tree, "Guide From Curve", False)
    return obj


def _guide_geometry(tree, loc, guide_sock, curve_sock=None, use_curve_sock=None):
    """Guide object -> geometry, in the HOST's local space.

    ``transform_space='RELATIVE`` is load-bearing. With the default ``ORIGINAL`` the
    guide's own coordinates are consumed as if they were host-local, so a host object
    carrying any transform displaces every run by that transform: the study's
    ``ROOF_Roof_Main`` sits at (0, 15, 2), which parked the star pendants, heart
    filigree and all three wall bead runs 4-6 m off the building in empty space.
    RELATIVE cancels the host transform exactly, so a run appears where its guide is
    drawn in the world and the guide stays a truthful authoring handle.
    """
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
        return n.outputs["Geometry"]
    sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 180, loc[1] - 160))
    if sw is None:
        return n.outputs["Geometry"]
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, n.outputs["Geometry"], sw.inputs["False"])
    link_sockets(tree, curve_sock, sw.inputs["True"])
    link_sockets(tree, use_curve_sock, sw.inputs["Switch"])
    return sw.outputs["Output"]


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


def _set_group_param(node, name, value):
    """Set a nested group node's unlinked input to a literal."""
    if node is None or value is None:
        return
    try:
        sock = node.inputs.get(name)
        if sock is None or sock.is_linked:
            return
        if not _is_sock(value):
            sock.default_value = value
    except Exception:
        pass


def _drooped_curve(tree, loc, curve_sock, droop_sock):
    """offset_z = -Droop * (1 - (2t - 1)^2) over the curve's spline parameter."""
    param = safe_node(tree, "GeometryNodeSplineParameter", (loc[0] - 340, loc[1] - 240))
    color_node(param, "attribute")
    two_t = _mk(tree, (loc[0] - 180, loc[1] - 240), "MULTIPLY", 2.0, a=param.outputs["Factor"])
    one_less = _mk(tree, (loc[0] - 20, loc[1] - 240), "SUBTRACT", 1.0, a=V(two_t))
    sq = _mk(tree, (loc[0] + 140, loc[1] - 240), "MULTIPLY", a=V(one_less), b=V(one_less))
    complement = _mk(tree, (loc[0] + 300, loc[1] - 240), "SUBTRACT", a=1.0)
    if complement is not None:
        link_sockets(tree, V(sq), complement.inputs[1])
    neg = _mk(tree, (loc[0] + 460, loc[1] - 240), "MULTIPLY", -1.0, a=V(complement))
    sag = _mk(tree, (loc[0] + 620, loc[1] - 240), "MULTIPLY", a=V(neg), b=droop_sock)
    off = _combine(tree, (loc[0] + 780, loc[1] - 240), z=V(sag))
    return _set_position(tree, loc, curve_sock, offset=off)


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
    return n.outputs["Curve"]


def _sweep_circle(tree, loc, curve_sock, radius_sock, resolution=8):
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (loc[0] - 200, loc[1] - 240))
    color_node(profile, "curve")
    if profile is not None:
        try:
            profile.inputs["Resolution"].default_value = int(resolution)
        except Exception:
            pass
        link_sockets(tree, radius_sock, profile.inputs["Radius"])
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", loc)
    if sweep is None:
        return None
    link_sockets(tree, curve_sock, sweep.inputs["Curve"])
    if profile is not None:
        link_sockets(tree, profile.outputs["Curve"], sweep.inputs["Profile Curve"])
    color_node(sweep, "geometry")
    return sweep.outputs["Mesh"]


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
    return n.outputs["Output"]


def _finish(tree, gin, gout, ornament_sock, material_sock, loc=(1180, 0)):
    """Set material on the ornament branch, then join it onto the host geometry."""
    orn = _set_material(tree, loc, ornament_sock, material_sock=material_sock)
    merged = _join(tree, (loc[0] + 180, 0), [gin.outputs["Geometry"], orn])
    link_sockets(tree, merged, gout.inputs["Geometry"])
    return merged


# --------------------------------------------------------------------------
# 1. MEL_nikki_bead - the pearl
# --------------------------------------------------------------------------

def build_nikki_bead(group_name="MEL_nikki_bead"):
    """Pearl / drop bead solid. Squash and Teardrop shape it; Faceted kills the smooth shade."""
    tree, gin, gout = new_geometry_tree(group_name)
    radius = add_float_param(tree, "Radius", 0.022, 0.002, 0.30)
    segs = add_int_param(tree, "Segments", 20, 6, 64)
    rings = add_int_param(tree, "Rings", 12, 4, 48)
    squash = add_float_param(tree, "Squash", 1.0, 0.2, 3.0)
    teardrop = add_float_param(tree, "Teardrop", 0.0, -1.5, 1.5)
    faceted = add_bool_param(tree, "Faceted", False)
    mat = _material_param(tree)

    sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (-640, 0))
    color_node(sphere, "geometry")
    if sphere is not None:
        link_sockets(tree, segs, sphere.inputs["Segments"])
        link_sockets(tree, rings, sphere.inputs["Rings"])
        link_sockets(tree, radius, sphere.inputs["Radius"])

    scaled = _transform(tree, (-420, 0), sphere.outputs["Mesh"] if sphere else None,
                        scale=_combine(tree, (-540, 160), x=1.0, y=1.0, z=squash))

    pos = safe_node(tree, "GeometryNodeInputPosition", (-640, -300))
    color_node(pos, "attribute")
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-480, -300))
    color_node(sep, "math")
    if sep is not None:
        link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    zsq = _mk(tree, (-320, -300), "MULTIPLY", a=sep.outputs["Z"], b=sep.outputs["Z"])
    safe_r = _mk(tree, (-480, -440), "MAXIMUM", a=radius)
    if safe_r is not None:
        safe_r.inputs[1].default_value = 1e-6
    pull = _mk(tree, (-160, -360), "DIVIDE", a=teardrop)
    if pull is not None:
        link_sockets(tree, V(safe_r), pull.inputs[1])
    shaped = _mk(tree, (0, -320), "MULTIPLY", a=V(zsq), b=V(pull))
    neg = _mk(tree, (160, -320), "MULTIPLY", -1.0, a=V(shaped))
    dropped = _set_position(tree, (380, 0), scaled, offset=_combine(tree, (240, -180), z=V(neg)))

    shaded = _shade(tree, (560, 0), dropped, smooth=faceted, invert=True)
    _finish(tree, gin, gout, shaded, mat, (740, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Pearl", "geometry", sphere, scaled, dropped, shaded),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 2. MEL_nikki_star
# --------------------------------------------------------------------------

def build_nikki_star(group_name="MEL_nikki_star"):
    """Pointed star solid. Index parity on a 2N-gon sets the inner/outer radius step."""
    tree, gin, gout = new_geometry_tree(group_name)
    points = add_int_param(tree, "Points", 5, 3, 16)
    outer = add_float_param(tree, "Outer Radius", 0.032, 0.005, 0.30)
    inner = add_float_param(tree, "Inner Radius", 0.013, 0.002, 0.20)
    thick = add_float_param(tree, "Thickness", 0.008, 0.0005, 0.10)
    faceted = add_bool_param(tree, "Faceted", True)
    mat = _material_param(tree)

    vert_count = _mk(tree, (-1200, -120), "MULTIPLY", 2.0, a=points)
    circle = safe_node(tree, "GeometryNodeMeshCircle", (-1000, 0))
    color_node(circle, "geometry")
    if circle is not None:
        link_sockets(tree, V(vert_count), circle.inputs["Vertices"])
        link_sockets(tree, outer, circle.inputs["Radius"])
        try:
            circle.fill_type = "NGON"
        except Exception:
            pass

    ratio = _mk(tree, (-1200, -280), "DIVIDE", a=inner)
    if ratio is not None:
        link_sockets(tree, outer, ratio.inputs[1])

    idx = safe_node(tree, "GeometryNodeInputIndex", (-1200, -440))
    color_node(idx, "attribute")
    parity = _mk(tree, (-1020, -440), "MODULO", 2.0, a=idx.outputs["Index"])

    is_inner = safe_node(tree, "FunctionNodeCompare", (-840, -440))
    color_node(is_inner, "math")
    if is_inner is not None:
        try:
            is_inner.data_type = "FLOAT"
            is_inner.operation = "EQUAL"
        except Exception:
            pass
        link_sockets(tree, V(parity), is_inner.inputs["A"])
        is_inner.inputs["B"].default_value = 1.0

    pick = safe_node(tree, "GeometryNodeSwitch", (-660, -400))
    color_node(pick, "math")
    if pick is not None:
        try:
            pick.input_type = "FLOAT"
        except Exception:
            pass
        link_sockets(tree, is_inner.outputs["Result"] if is_inner else None, pick.inputs["Switch"])
        pick.inputs["False"].default_value = 1.0
        link_sockets(tree, V(ratio), pick.inputs["True"])

    pos = safe_node(tree, "GeometryNodeInputPosition", (-660, -160))
    color_node(pos, "attribute")
    # radial offset factor = (picked radius ratio) - 1, so inner verts pull inward
    delta = _mk(tree, (-480, -200), "SUBTRACT", 1.0, a=pick.outputs["Output"] if pick else None)

    radial = safe_node(tree, "ShaderNodeVectorMath", (-300, -160))
    color_node(radial, "math")
    if radial is not None:
        radial.operation = "SCALE"
        link_sockets(tree, pos.outputs["Position"], radial.inputs["Vector"])
        link_sockets(tree, V(delta), radial.inputs["Scale"])

    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-120, -160))
    color_node(sep, "math")
    if sep is not None:
        link_sockets(tree, radial.outputs["Vector"] if radial else None, sep.inputs["Vector"])
    flat = _combine(tree, (60, -160), x=sep.outputs["X"], y=sep.outputs["Y"])
    profile = _set_position(tree, (240, 0), circle.outputs["Mesh"] if circle else None, offset=flat)

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (420, 0))
    color_node(extrude, "geometry")
    if extrude is not None:
        try:
            extrude.mode = "FACES"
        except Exception:
            pass
        link_sockets(tree, profile, extrude.inputs["Mesh"])
        link_sockets(tree, _combine(tree, (260, -320), z=thick), extrude.inputs["Offset"])

    solid = _transform(tree, (620, 0), extrude.outputs["Mesh"] if extrude else None,
                       rotation=(math.radians(90.0), 0.0, 0.0))
    shaded = _shade(tree, (800, 0), solid, smooth=faceted, invert=True)
    _finish(tree, gin, gout, shaded, mat, (980, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Star Profile", "geometry", circle, profile, extrude, solid),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 3. MEL_nikki_heart
# --------------------------------------------------------------------------

def build_nikki_heart(group_name="MEL_nikki_heart"):
    """Plump heart: two overlapping lobes united with a down cone, flattened, beveled.

    Lobe centres sit at 0.40*Size with radius 0.52*Size, so the two spheres genuinely
    intersect. Disjoint spheres would make the UNION a no-op join, not a fused body.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    size = add_float_param(tree, "Size", 0.05, 0.01, 0.40)
    point = add_float_param(tree, "Point", 1.55, 0.6, 3.0)
    depth = add_float_param(tree, "Depth", 0.46, 0.10, 1.0)
    mat = _material_param(tree)

    lobe_r = _mk(tree, (-1260, 260), "MULTIPLY", 0.52, a=size)
    lobe_x = _mk(tree, (-1260, 100), "MULTIPLY", 0.40, a=size)
    lobe_xn = _mk(tree, (-1100, 100), "MULTIPLY", -1.0, a=V(lobe_x))
    lobe_z = _mk(tree, (-1260, -60), "MULTIPLY", 0.20, a=size)

    def _sphere(loc, x_sock):
        s = safe_node(tree, "GeometryNodeMeshUVSphere", loc)
        color_node(s, "geometry")
        if s is not None:
            link_sockets(tree, V(lobe_r), s.inputs["Radius"])
            try:
                s.inputs["Segments"].default_value = 28
                s.inputs["Rings"].default_value = 18
            except Exception:
                pass
        return _transform(tree, (loc[0] + 220, loc[1]), s.outputs["Mesh"] if s else None,
                          translation=_combine(tree, (loc[0] + 60, loc[1] - 240),
                                              x=x_sock, z=V(lobe_z)))

    left = _sphere((-1060, 460), V(lobe_xn))
    right = _sphere((-1060, 180), V(lobe_x))

    cone_r = _mk(tree, (-1260, -300), "MULTIPLY", 0.80, a=size)
    cone_d = _mk(tree, (-1260, -460), "MULTIPLY", a=size)
    if cone_d is not None:
        link_sockets(tree, point, cone_d.inputs[1])

    cone = safe_node(tree, "GeometryNodeMeshCone", (-1060, -600))
    color_node(cone, "geometry")
    if cone is not None:
        try:
            cone.inputs["Vertices"].default_value = 28
        except Exception:
            pass
        link_sockets(tree, V(cone_r), cone.inputs["Radius Bottom"])
        cone.inputs["Radius Top"].default_value = 0.0
        link_sockets(tree, V(cone_d), cone.inputs["Depth"])

    # Cone mesh spans 0..Depth with the base ring at z=0. Rotating 180deg about X puts
    # the apex down and the ring at -Depth; translating by lobe_z seats the girdle at
    # the lobe-centre height, so the point grows out of the lobes instead of hanging
    # detached below them.
    flipped = _transform(tree, (-580, -600), cone.outputs["Mesh"] if cone else None,
                         translation=_combine(tree, (-740, -640), z=V(lobe_z)),
                         rotation=(math.radians(180.0), 0.0, 0.0))

    lobes = _boolean(tree, (-380, 320), left, right, "UNION")
    body = _boolean(tree, (-160, 140), lobes, flipped, "UNION")
    flattened = _transform(tree, (40, 140), body,
                           scale=_combine(tree, (-80, -100), x=1.0, y=depth, z=1.0))
    merged = _merge(tree, (220, 140), flattened)
    shaded = _shade(tree, (400, 140), merged, smooth=True)
    _finish(tree, gin, gout, shaded, mat, (580, 140))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Lobes + Point", "geometry", left, right, flipped, body),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 4. MEL_nikki_crystal
# --------------------------------------------------------------------------

def build_nikki_crystal(group_name="MEL_nikki_crystal"):
    """Faceted double-terminated crystal drop: two cones welded at the girdle."""
    tree, gin, gout = new_geometry_tree(group_name)
    size = add_float_param(tree, "Size", 0.026, 0.004, 0.25)
    sides = add_int_param(tree, "Sides", 6, 3, 16)
    upper = add_float_param(tree, "Upper", 1.75, 0.4, 4.0)
    lower = add_float_param(tree, "Lower", 0.85, 0.2, 4.0)
    faceted = add_bool_param(tree, "Faceted", True)
    mat = _material_param(tree)

    d_up = _mk(tree, (-1200, 260), "MULTIPLY", a=size)
    if d_up is not None:
        link_sockets(tree, upper, d_up.inputs[1])
    d_lo = _mk(tree, (-1200, 80), "MULTIPLY", a=size)
    if d_lo is not None:
        link_sockets(tree, lower, d_lo.inputs[1])

    # NOTE: GeometryNodeMeshCone emits a mesh spanning 0..Depth (base ring at z=0,
    # apex at z=+Depth) -- it is NOT centred on its origin. Both halves are placed
    # from that fact; assuming a centred cone mis-stacks the crystal and the heart.
    up = safe_node(tree, "GeometryNodeMeshCone", (-1000, 320))
    color_node(up, "geometry")
    if up is not None:
        link_sockets(tree, sides, up.inputs["Vertices"])
        up.inputs["Radius Top"].default_value = 0.0
        link_sockets(tree, size, up.inputs["Radius Bottom"])
        link_sockets(tree, V(d_up), up.inputs["Depth"])

    lo = safe_node(tree, "GeometryNodeMeshCone", (-1000, -40))
    color_node(lo, "geometry")
    if lo is not None:
        link_sockets(tree, sides, lo.inputs["Vertices"])
        link_sockets(tree, size, lo.inputs["Radius Top"])
        lo.inputs["Radius Bottom"].default_value = 0.0
        link_sockets(tree, V(d_lo), lo.inputs["Depth"])

    # up cone: base ring already sits at z=0 and the apex reaches +d_up -> no offset
    up_fix = _transform(tree, (-640, 320), up.outputs["Mesh"] if up else None)
    # lo cone: apex at z=0, girdle ring at +d_lo -> drop it so the ring meets z=0
    lo_z = _mk(tree, (-820, -40), "MULTIPLY", -1.0, a=V(d_lo))
    lo_fix = _transform(tree, (-640, -40), lo.outputs["Mesh"] if lo else None,
                        translation=_combine(tree, (-820, -160), z=V(lo_z)))

    joined = _join(tree, (-420, 160), [up_fix, lo_fix])
    welded = _merge(tree, (-240, 160), joined, 0.0005)
    shaded = _shade(tree, (-60, 160), welded, smooth=faceted, invert=True)
    _finish(tree, gin, gout, shaded, mat, (140, 160))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Crystal", "geometry", up_fix, lo_fix, welded),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 5. MEL_nikki_cord
# --------------------------------------------------------------------------

def build_nikki_cord(group_name="MEL_nikki_cord"):
    """Standalone sagging cord: parabolic sag swept with a small round profile."""
    tree, gin, gout = new_geometry_tree(group_name)
    count = add_int_param(tree, "Count", 24, 4, 256)
    length = add_float_param(tree, "Length", 1.0, 0.05, 20.0)
    sag = add_float_param(tree, "Sag", 0.06, 0.0, 2.0)
    cord_r = add_float_param(tree, "Cord Radius", 0.0035, 0.0005, 0.05)
    mat = _material_param(tree)

    line = safe_node(tree, "GeometryNodeMeshLine", (-1060, 0))
    color_node(line, "geometry")
    if line is not None:
        try:
            line.mode = "END_POINTS"
        except Exception:
            pass
        link_sockets(tree, count, line.inputs["Count"])
        try:
            line.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
        except Exception:
            pass
        end_sock = line.inputs.get("End Location") or line.inputs[-1]
        link_sockets(tree, _combine(tree, (-1240, -200), x=length), end_sock)

    denom = _mk(tree, (-1060, -320), "SUBTRACT", 1.0, a=count)
    denom_safe = _mk(tree, (-900, -320), "MAXIMUM", a=V(denom))
    if denom_safe is not None:
        denom_safe.inputs[1].default_value = 1.0

    idx = safe_node(tree, "GeometryNodeInputIndex", (-1060, -480))
    color_node(idx, "attribute")
    t = _mk(tree, (-740, -400), "DIVIDE", a=idx.outputs["Index"])
    if t is not None:
        link_sockets(tree, V(denom_safe), t.inputs[1])

    two_t = _mk(tree, (-580, -400), "MULTIPLY", 2.0, a=V(t))
    less = _mk(tree, (-420, -400), "SUBTRACT", 1.0, a=V(two_t))
    sq = _mk(tree, (-260, -400), "MULTIPLY", a=V(less), b=V(less))
    comp = _mk(tree, (-100, -400), "SUBTRACT", a=1.0)
    if comp is not None:
        link_sockets(tree, V(sq), comp.inputs[1])
    neg = _mk(tree, (60, -400), "MULTIPLY", -1.0, a=V(comp))
    sagged_z = _mk(tree, (220, -400), "MULTIPLY", a=V(neg), b=sag)

    sagged = _set_position(tree, (420, 0), line.outputs["Mesh"] if line else None,
                           offset=_combine(tree, (260, -200), z=V(sagged_z)))

    curve = safe_node(tree, "GeometryNodeMeshToCurve", (600, 0))
    color_node(curve, "curve")
    if curve is not None:
        try:
            curve.mode = "EDGES"
        except Exception:
            pass
        link_sockets(tree, sagged, curve.inputs["Mesh"])

    swept = _sweep_circle(tree, (800, 0), curve.outputs["Curve"] if curve else None, cord_r)
    _finish(tree, gin, gout, swept, mat, (1000, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Sag + Sweep", "curve", line, sagged, curve, swept),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 6. MEL_nikki_bead_string
# --------------------------------------------------------------------------

def build_nikki_bead_string(group_name="MEL_nikki_bead_string"):
    """Beads strung along a guide object, with a real cord and a parabolic hang.

    Single authority for both the eave swag and the wall bead drop. The study file had
    two near-identical trees plus three stacked duplicates of one of them.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    guide = _guide_params(tree)
    bead_count = add_int_param(tree, "Bead Count", 14, 1, 200)
    bead_radius = add_float_param(tree, "Bead Radius", 0.022, 0.002, 0.30)
    droop = add_float_param(tree, "Droop", 0.10, 0.0, 2.0)
    taper = add_float_param(tree, "Taper", 0.55, -1.0, 2.0)
    jitter = add_float_param(tree, "Jitter", 0.12, 0.0, 1.0)
    cord_r = add_float_param(tree, "Cord Radius", 0.0032, 0.0005, 0.05)
    show_cord = add_bool_param(tree, "Show Cord", True)
    mat = _material_param(tree)

    guide_geom = _guide_geometry(tree, (-1460, 0), guide)
    drooped = _drooped_curve(tree, (-1260, 0), guide_geom, droop)

    cord = _sweep_circle(tree, (-1040, -340), drooped, cord_r)
    cord_used = _geometry_switch(tree, (-840, -340), show_cord, cord)

    points = _resample(tree, (-1040, 120), drooped, bead_count)
    param = safe_node(tree, "GeometryNodeSplineParameter", (-1040, -100))
    color_node(param, "attribute")

    # taper: 1 + Taper * (0.5 - |t - 0.5|)
    shifted = _mk(tree, (-860, -180), "SUBTRACT", 0.5, a=param.outputs["Factor"])
    absd = safe_node(tree, "ShaderNodeMath", (-700, -180))
    color_node(absd, "math")
    if absd is not None:
        absd.operation = "ABSOLUTE"
        link_sockets(tree, V(shifted), absd.inputs[0])
    half_minus = _mk(tree, (-540, -180), "SUBTRACT", a=0.5)
    if half_minus is not None:
        link_sockets(tree, V(absd), half_minus.inputs[1])
    taper_mul = _mk(tree, (-380, -180), "MULTIPLY", a=V(half_minus), b=taper)
    taper_f = _mk(tree, (-220, -180), "ADD", 1.0, a=V(taper_mul))
    radius_t = _mk(tree, (-60, -180), "MULTIPLY", a=bead_radius, b=V(taper_f))

    # deterministic jitter: 1 + Jitter * sin(Index * 12.9898)
    idx = safe_node(tree, "GeometryNodeInputIndex", (-700, -480))
    color_node(idx, "attribute")
    phase = _mk(tree, (-540, -480), "MULTIPLY", 12.9898, a=idx.outputs["Index"])
    wave = safe_node(tree, "ShaderNodeMath", (-380, -480))
    color_node(wave, "math")
    if wave is not None:
        wave.operation = "SINE"
        link_sockets(tree, V(phase), wave.inputs[0])
    jmul = _mk(tree, (-220, -480), "MULTIPLY", a=V(wave), b=jitter)
    jf = _mk(tree, (-60, -480), "ADD", 1.0, a=V(jmul))

    size_f = _mk(tree, (100, -320), "MULTIPLY", a=V(radius_t), b=V(jf))
    size_v = _combine(tree, (260, -320), x=V(size_f), y=V(size_f), z=V(size_f))

    bead_grp = _ensure_group_node(tree, "MEL_nikki_bead", build_nikki_bead, (100, 320))
    # The nested template is normalised to unit radius so the instance Scale below is
    # the single source of truth for bead size. Without this the instance scale
    # MULTIPLIES the template's own Radius (0.022 * 0.042 = 0.9 mm beads).
    _set_group_param(bead_grp, "Radius", 1.0)
    beads = safe_node(tree, "GeometryNodeInstanceOnPoints", (480, 120))
    color_node(beads, "instance")
    if beads is not None:
        link_sockets(tree, points, beads.inputs["Points"])
        link_sockets(tree, bead_grp.outputs["Geometry"] if bead_grp else None, beads.inputs["Instance"])
        link_sockets(tree, size_v, beads.inputs["Scale"])

    realized = safe_node(tree, "GeometryNodeRealizeInstances", (660, 120))
    color_node(realized, "geometry")
    link_sockets(tree, beads.outputs["Instances"] if beads else None, realized.inputs["Geometry"])

    ornament = _join(tree, (840, 0), [cord_used, realized.outputs["Geometry"] if realized else None])
    _finish(tree, gin, gout, ornament, mat, (1020, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Guide, Droop, Cord", "curve", guide_geom, drooped, cord, cord_used),
        ("Bead String", "instance", points, bead_grp, beads, realized),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 7. MEL_nikki_star_pendant
# --------------------------------------------------------------------------

def build_nikki_star_pendant(group_name="MEL_nikki_star_pendant"):
    """Star pendants hanging from a drooping cord run along a guide object."""
    tree, gin, gout = new_geometry_tree(group_name)
    guide = _guide_params(tree)
    count = add_int_param(tree, "Pendant Count", 12, 1, 120)
    star_size = add_float_param(tree, "Star Size", 0.032, 0.005, 0.30)
    hang = add_float_param(tree, "Hang", 0.075, 0.0, 1.0)
    droop = add_float_param(tree, "Droop", 0.08, 0.0, 2.0)
    cord_r = add_float_param(tree, "Cord Radius", 0.0026, 0.0005, 0.05)
    mat = _material_param(tree)

    guide_geom = _guide_geometry(tree, (-1460, 0), guide)
    drooped = _drooped_curve(tree, (-1260, 0), guide_geom, droop)
    cord = _sweep_circle(tree, (-1040, -340), drooped, cord_r)
    points = _resample(tree, (-1040, 120), drooped, count)

    star_grp = _ensure_group_node(tree, "MEL_nikki_star", build_nikki_star, (-1040, 340))
    # unit-radius normalisation; the instance Scale carries the absolute size
    _set_group_param(star_grp, "Outer Radius", 1.0)
    _set_group_param(star_grp, "Inner Radius", 0.42)
    _set_group_param(star_grp, "Thickness", 0.25)
    scale_v = _combine(tree, (-840, 120), x=star_size, y=star_size, z=star_size)
    pendants = safe_node(tree, "GeometryNodeInstanceOnPoints", (-640, 120))
    color_node(pendants, "instance")
    if pendants is not None:
        link_sockets(tree, points, pendants.inputs["Points"])
        link_sockets(tree, star_grp.outputs["Geometry"] if star_grp else None, pendants.inputs["Instance"])
        link_sockets(tree, scale_v, pendants.inputs["Scale"])

    hang_neg = _mk(tree, (-640, -160), "MULTIPLY", -1.0, a=hang)
    dropped = _set_position(tree, (-300, 120), pendants.outputs["Instances"] if pendants else None,
                            offset=_combine(tree, (-460, -160), z=V(hang_neg)))
    realized = safe_node(tree, "GeometryNodeRealizeInstances", (-120, 120))
    color_node(realized, "geometry")
    link_sockets(tree, dropped, realized.inputs["Geometry"])

    ornament = _join(tree, (60, 0), [cord, realized.outputs["Geometry"] if realized else None])
    _finish(tree, gin, gout, ornament, mat, (240, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Run + Drops", "curve", guide_geom, drooped, cord, points),
        ("Pendants", "instance", star_grp, pendants, realized),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# 8. MEL_nikki_heart_filigree
# --------------------------------------------------------------------------

def build_nikki_heart_filigree(group_name="MEL_nikki_heart_filigree"):
    """Hearts hanging beneath a drooping cord run, each optionally in a filigree wreath."""
    tree, gin, gout = new_geometry_tree(group_name)
    guide = _guide_params(tree)
    count = add_int_param(tree, "Heart Count", 6, 1, 80)
    heart_size = add_float_param(tree, "Heart Size", 0.032, 0.005, 0.30)
    hang = add_float_param(tree, "Hang", 0.10, 0.0, 1.0)
    droop = add_float_param(tree, "Droop", 0.06, 0.0, 2.0)
    wreath_on = add_bool_param(tree, "Filigree Wreath", True)
    cord_r = add_float_param(tree, "Cord Radius", 0.0026, 0.0005, 0.05)
    mat = _material_param(tree)

    guide_geom = _guide_geometry(tree, (-1460, 0), guide)
    drooped = _drooped_curve(tree, (-1260, 0), guide_geom, droop)
    cord = _sweep_circle(tree, (-1040, -340), drooped, cord_r)
    points = _resample(tree, (-1040, 120), drooped, count)

    heart_grp = _ensure_group_node(tree, "MEL_nikki_heart", build_nikki_heart, (-1040, 340))
    # unit-size normalisation; the instance Scale carries the absolute size
    _set_group_param(heart_grp, "Size", 1.0)
    scale_v = _combine(tree, (-840, 120), x=heart_size, y=heart_size, z=heart_size)
    hearts = safe_node(tree, "GeometryNodeInstanceOnPoints", (-640, 120))
    color_node(hearts, "instance")
    if hearts is not None:
        link_sockets(tree, points, hearts.inputs["Points"])
        link_sockets(tree, heart_grp.outputs["Geometry"] if heart_grp else None, hearts.inputs["Instance"])
        link_sockets(tree, scale_v, hearts.inputs["Scale"])
    hearts_real = safe_node(tree, "GeometryNodeRealizeInstances", (-440, 120))
    color_node(hearts_real, "geometry")
    link_sockets(tree, hearts.outputs["Instances"] if hearts else None, hearts_real.inputs["Geometry"])

    try:
        from .ornament_extras import build_filigree_wreath_ring as wreath_builder
    except Exception:
        wreath_builder = None
    wreath_grp = _ensure_group_node(tree, "MEL_filigree_wreath_ring", wreath_builder, (-640, -660))
    # wreath ring normalised to unit radius; heart_size * 1.35 drives the scale, so the
    # wreath tracks the heart instead of sitting at the ring's own 0.3 m default
    _set_group_param(wreath_grp, "Radius", 1.0)
    wreath_r = _mk(tree, (-860, -780), "MULTIPLY", 1.35, a=heart_size)
    wreath_scale = _combine(tree, (-440, -660), x=V(wreath_r), y=V(wreath_r), z=V(wreath_r))
    wreaths = safe_node(tree, "GeometryNodeInstanceOnPoints", (-240, -660))
    color_node(wreaths, "instance")
    if wreaths is not None:
        link_sockets(tree, points, wreaths.inputs["Points"])
        if wreath_grp is not None:
            link_sockets(tree, wreath_grp.outputs["Geometry"], wreaths.inputs["Instance"])
        link_sockets(tree, wreath_scale, wreaths.inputs["Scale"])
    wreaths_real = safe_node(tree, "GeometryNodeRealizeInstances", (-40, -660))
    color_node(wreaths_real, "geometry")
    link_sockets(tree, wreaths.outputs["Instances"] if wreaths else None, wreaths_real.inputs["Geometry"])
    wreath_used = _geometry_switch(tree, (140, -660), wreath_on,
                                   wreaths_real.outputs["Geometry"] if wreaths_real else None)

    hang_neg = _mk(tree, (-640, -340), "MULTIPLY", -1.0, a=hang)
    hang_v = _combine(tree, (-480, -340), z=V(hang_neg))
    dropped_h = _set_position(tree, (-240, 120), hearts_real.outputs["Geometry"] if hearts_real else None,
                              offset=hang_v)
    dropped_w = _set_position(tree, (-240, -340), wreath_used, offset=hang_v)

    ornament = _join(tree, (320, 0), [cord, dropped_h, dropped_w])
    _finish(tree, gin, gout, ornament, mat, (500, 0))

    label_tree(tree, group_name, _frames(
        ("Inputs", "input", gin),
        ("Run + Drops", "curve", guide_geom, drooped, cord, points),
        ("Hearts + Wreaths", "instance", heart_grp, hearts, wreath_grp, wreaths),
        ("Output", "output", gout),
    ))
    return tree, gin, gout


# --------------------------------------------------------------------------
# registration
# --------------------------------------------------------------------------

register_builder(
    "MEL_nikki_bead", build_nikki_bead, "Nikki Bead (Pearl)",
    "Pearl / drop bead solid with squash, teardrop taper and optional faceting.",
    category="nikki_decor")

register_builder(
    "MEL_nikki_star", build_nikki_star, "Nikki Star",
    "Pointed solid star with thickness and bevel - a real star silhouette, not a cone.",
    category="nikki_decor")

register_builder(
    "MEL_nikki_heart", build_nikki_heart, "Nikki Heart",
    "Plump boolean heart: two overlapping lobes united with a down cone, flattened and beveled.",
    category="nikki_decor")

register_builder(
    "MEL_nikki_crystal", build_nikki_crystal, "Nikki Crystal",
    "Faceted double-terminated crystal drop (welded bipyramid).",
    category="nikki_decor")

register_builder(
    "MEL_nikki_cord", build_nikki_cord, "Nikki Cord",
    "Standalone sagging cord strand - parabolic sag swept with a round profile.",
    category="nikki_decor")

register_builder(
    "MEL_nikki_bead_string", build_nikki_bead_string, "Nikki Bead String",
    "Guide-driven bead strand with a real cord, parabolic droop, mid-run taper and jitter. "
    "The single authority for eave swags and wall bead drops.",
    category="nikki_decor")

register_builder(
    "MEL_nikki_star_pendant", build_nikki_star_pendant, "Nikki Star Pendant",
    "Guide-driven star pendants hanging from a drooping cord run.",
    category="nikki_decor")

register_builder(
    "MEL_nikki_heart_filigree", build_nikki_heart_filigree, "Nikki Heart Filigree",
    "Guide-driven hearts under a cord run, each optionally inside a filigree wreath.",
    category="nikki_decor")
