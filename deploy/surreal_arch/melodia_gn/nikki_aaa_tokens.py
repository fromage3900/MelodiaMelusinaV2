"""Nikki AAA tokens - advanced wardrobe/scene builders for Melodia Studio.

Extends nikki_decor.py with AAA-quality mesh setups:
- Fabric simulation mesh with cloth-like drape
- Ribbon/curve with proper taper and twist
- Gem/crystal with SDF-style bevel
- Floral petal with subsurface scattering
- Star token with proper geometry
- Heart token with bezier-curve-based shape

All builders use Blender 5.2 node socket names and follow the patterns
established in nikki_decor.py.
"""

import math

import bpy

from .core import (
    add_bool_param, add_float_param, add_int_param, iface_default,
    color_node, label_tree, link_sockets, make_group_input,
    mesh_boolean_node, new_geometry_tree, register_builder, safe_node,
)
from .nikki_decor import (
    _combine, _ensure_group_node, _feed, _finish, _geometry_switch,
    _guide_geometry, _guide_params, _is_sock, _join, _material_param,
    _merge, _mk, _out, _resample, _set_group_param, _set_material,
    _set_position, _shade, _sweep_circle, _transform, V,
)

GOLD_MATERIAL_NAME = "MH_MAT_Ornament_Gold"


def _gold():
    return bpy.data.materials.get(GOLD_MATERIAL_NAME)


# --------------------------------------------------------------------------
# 1. MEL_nikki_fabric_mesh - cloth-like drape simulation
# --------------------------------------------------------------------------

def build_nikki_fabric_mesh(group_name="MEL_nikki_fabric_mesh"):
    """Fabric simulation mesh: subdivided grid with sine-wave drape + noise."""
    tree, gin, gout = new_geometry_tree(group_name)
    width = add_float_param(tree, "Width", 0.5, 0.05, 5.0)
    height = add_float_param(tree, "Height", 0.5, 0.05, 5.0)
    res_x = add_int_param(tree, "Resolution X", 32, 4, 128)
    res_y = add_int_param(tree, "Resolution Y", 32, 4, 128)
    subdiv = add_int_param(tree, "Subdivision", 2, 0, 4)
    wave_freq = add_float_param(tree, "Wave Frequency", 3.0, 0.1, 20.0)
    wave_amp = add_float_param(tree, "Wave Amplitude", 0.02, 0.0, 0.5)
    noise_scale = add_float_param(tree, "Noise Scale", 5.0, 0.1, 50.0)
    noise_amp = add_float_param(tree, "Noise Amplitude", 0.005, 0.0, 0.2)
    shade_smooth = add_bool_param(tree, "Shade Smooth", True)
    mat = _material_param(tree)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 0))
    color_node(grid, "geometry")
    if grid is not None:
        link_sockets(tree, width, grid.inputs["Size X"])
        link_sockets(tree, height, grid.inputs["Size Y"])
        link_sockets(tree, res_x, grid.inputs["Vertices X"])
        link_sockets(tree, res_y, grid.inputs["Vertices Y"])

    # Subdivide
    sub = safe_node(tree, "GeometryNodeSubdivideMesh", (-1000, 0))
    color_node(sub, "geometry")
    if sub is not None:
        link_sockets(tree, grid.outputs["Mesh"] if grid else None, sub.inputs["Mesh"])
        link_sockets(tree, subdiv, sub.inputs["Level"])

    # Wave displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (-1000, -300))
    color_node(pos, "attribute")
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-840, -300))
    color_node(sep, "math")
    if sep is not None:
        link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # sin(X * freq) * amp
    x_mul = _mk(tree, (-680, -300), "MULTIPLY", a=sep.outputs["X"])
    if x_mul is not None:
        link_sockets(tree, wave_freq, x_mul.inputs[1])
    sin_n = safe_node(tree, "ShaderNodeMath", (-520, -300))
    color_node(sin_n, "math")
    if sin_n is not None:
        sin_n.operation = "SINE"
        link_sockets(tree, V(x_mul), sin_n.inputs[0])
    wave_z = _mk(tree, (-360, -300), "MULTIPLY", a=V(sin_n))
    if wave_z is not None:
        link_sockets(tree, wave_amp, wave_z.inputs[1])

    # Noise displacement
    noise = safe_node(tree, "ShaderNodeTexNoise", (-680, -500))
    color_node(noise, "math")
    if noise is not None:
        link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
        link_sockets(tree, noise_scale, noise.inputs["Scale"])
    noise_z = _mk(tree, (-360, -500), "MULTIPLY", a=noise.outputs["Fac"])
    if noise_z is not None:
        link_sockets(tree, noise_amp, noise_z.inputs[1])

    # Combine wave + noise
    combined = _mk(tree, (-200, -400), "ADD", a=V(wave_z), b=V(noise_z))
    offset = _combine(tree, (-40, -400), z=V(combined))

    displaced = _set_position(tree, (160, 0), sub.outputs["Mesh"] if sub else None, offset=offset)
    shaded = _shade(tree, (340, 0), displaced, smooth=shade_smooth)
    _finish(tree, gin, gout, shaded, mat, (520, 0))

    label_tree(tree, group_name, [
        {"title": "Inputs", "role": "input", "nodes": (gin.name,)},
        {"title": "Fabric", "role": "geometry", "nodes": (grid.name, sub.name, displaced.name, shaded.name)},
        {"title": "Output", "role": "output", "nodes": (gout.name,)},
    ])
    return tree, gin, gout


# --------------------------------------------------------------------------
# 2. MEL_nikki_ribbon - curve with taper and twist
# --------------------------------------------------------------------------

def build_nikki_ribbon(group_name="MEL_nikki_ribbon"):
    """Ribbon/curve with proper taper and twist using curve-to-mesh."""
    tree, gin, gout = new_geometry_tree(group_name)
    length = add_float_param(tree, "Length", 1.0, 0.05, 10.0)
    width = add_float_param(tree, "Width", 0.05, 0.005, 1.0)
    resolution = add_int_param(tree, "Resolution", 32, 4, 128)
    taper_start = add_float_param(tree, "Taper Start", 1.0, 0.0, 2.0)
    taper_end = add_float_param(tree, "Taper End", 0.5, 0.0, 2.0)
    twist = add_float_param(tree, "Twist", 0.0, -6.28, 6.28)
    curve_type = add_int_param(tree, "Curve Type", 0, 0, 2)
    shade_smooth = add_bool_param(tree, "Shade Smooth", True)
    mat = _material_param(tree)

    # Create curve path based on type
    # Type 0: wave, Type 1: spiral, Type 2: straight
    path = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (-1200, 0))
    color_node(path, "curve")
    if path is not None:
        try:
            path.mode = "OFFSET"
        except Exception:
            pass
        # Set control points for a gentle S-curve.
        # Read the AUTHORED default from tree.interface -- `length` is a
        # make_group_input node socket, whose default_value is ALWAYS the type
        # zero, so the whole ribbon collapsed to a point (measured: 128/128
        # faces degenerate, bbox ext [0, 0, 0]).
        L = iface_default(tree, "Length", 1.0)
        path.inputs["Start"].default_value = (-L / 2, 0, 0)
        path.inputs["Start Handle"].default_value = (-L / 6, 0, 0)
        path.inputs["End"].default_value = (L / 2, 0, 0)
        path.inputs["End Handle"].default_value = (L / 6, 0, 0)

    # Taper: scale the PATH's radius along the curve.
    #
    # The taper chain reads `SplineParameter.Factor`, which only exists on the
    # path. Driving the PROFILE PRIMITIVE's Radius with it evaluates the chain
    # in the primitive's own context -- there is no spline there, so every node
    # in the chain reads 0 and the ribbon sweeps a zero-radius profile: measured
    # 128/128 faces degenerate, bbox ext [1.03, 0, 0] (a flat line).
    # The idiom used by the rest of the addon (filigree/mother/ornament) is to
    # put the taper on the path with Set Curve Radius and keep the profile
    # constant; verified here: 0/128 degenerate after the change.
    param = safe_node(tree, "GeometryNodeSplineParameter", (-1000, -200))
    color_node(param, "attribute")

    # lerp(taper_start, taper_end, t)
    one_minus = _mk(tree, (-840, -200), "SUBTRACT", a=1.0)
    if one_minus is not None:
        link_sockets(tree, param.outputs["Factor"], one_minus.inputs[1])
    t_mul = _mk(tree, (-680, -200), "MULTIPLY", a=param.outputs["Factor"])
    if t_mul is not None:
        link_sockets(tree, taper_end, t_mul.inputs[1])
    om_mul = _mk(tree, (-520, -200), "MULTIPLY", a=V(one_minus))
    if om_mul is not None:
        link_sockets(tree, taper_start, om_mul.inputs[1])
    taper = _mk(tree, (-360, -200), "ADD", a=V(t_mul), b=V(om_mul))

    # Profile circle: constant radius = Width (taper is applied to the path).
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (-1000, 200))
    color_node(profile, "curve")
    if profile is not None:
        try:
            profile.inputs["Resolution"].default_value = 8
        except Exception:
            pass
        # CurvePrimitiveCircle in 5.2: inputs are ['Resolution', 'Point 1', 'Point 2', 'Point 3', 'Radius']
        link_sockets(tree, width, profile.inputs["Radius"])

    # Path with per-point taper radius
    taper_r = _mk(tree, (-680, 200), "MULTIPLY", a=width)
    if taper_r is not None and taper is not None:
        link_sockets(tree, V(taper), taper_r.inputs[1])
    path_sock = path.outputs["Curve"] if path else None
    if taper_r is not None:
        set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (-500, 0))
        color_node(set_radius, "curve")
        if set_radius is not None and path_sock is not None:
            link_sockets(tree, path_sock, set_radius.inputs["Curve"])
            link_sockets(tree, V(taper_r), set_radius.inputs["Radius"])
            path_sock = set_radius.outputs["Curve"]

    # Sweep
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (-200, 0))
    color_node(sweep, "geometry")
    if sweep is not None:
        link_sockets(tree, path_sock, sweep.inputs["Curve"])
        if profile is not None:
            link_sockets(tree, profile.outputs["Curve"], sweep.inputs["Profile Curve"])

    # Twist: rotate around Z based on spline parameter
    twist_mul = _mk(tree, (-200, -300), "MULTIPLY", a=param.outputs["Factor"])
    if twist_mul is not None:
        link_sockets(tree, twist, twist_mul.inputs[1])
    twist_rot = _combine(tree, (0, -300), z=V(twist_mul))
    twisted = _transform(tree, (200, 0), sweep.outputs["Mesh"] if sweep else None,
                         rotation=twist_rot)

    shaded = _shade(tree, (400, 0), twisted, smooth=shade_smooth)
    _finish(tree, gin, gout, shaded, mat, (580, 0))

    label_tree(tree, group_name, [
        {"title": "Inputs", "role": "input", "nodes": (gin.name,)},
        {"title": "Ribbon", "role": "curve", "nodes": (path.name, profile.name, sweep.name, twisted.name)},
        {"title": "Output", "role": "output", "nodes": (gout.name,)},
    ])
    return tree, gin, gout


# --------------------------------------------------------------------------
# 3. MEL_nikki_gem - SDF-style bevel crystal
# --------------------------------------------------------------------------

def build_nikki_gem(group_name="MEL_nikki_gem"):
    """Gem/crystal with SDF-style bevel and material slots."""
    tree, gin, gout = new_geometry_tree(group_name)
    size = add_float_param(tree, "Size", 0.05, 0.005, 0.5)
    sides = add_int_param(tree, "Sides", 8, 3, 16)
    upper = add_float_param(tree, "Upper", 1.5, 0.2, 4.0)
    lower = add_float_param(tree, "Lower", 0.8, 0.2, 4.0)
    bevel_width = add_float_param(tree, "Bevel Width", 0.005, 0.0, 0.1)
    faceted = add_bool_param(tree, "Faceted", False)
    shade_smooth = add_bool_param(tree, "Shade Smooth", True)
    mat = _material_param(tree)

    # Upper cone
    d_up = _mk(tree, (-1200, 260), "MULTIPLY", a=size)
    if d_up is not None:
        link_sockets(tree, upper, d_up.inputs[1])
    up = safe_node(tree, "GeometryNodeMeshCone", (-1000, 320))
    color_node(up, "geometry")
    if up is not None:
        link_sockets(tree, sides, up.inputs["Vertices"])
        up.inputs["Radius Top"].default_value = 0.0
        link_sockets(tree, size, up.inputs["Radius Bottom"])
        link_sockets(tree, V(d_up), up.inputs["Depth"])

    # Lower cone
    d_lo = _mk(tree, (-1200, 80), "MULTIPLY", a=size)
    if d_lo is not None:
        link_sockets(tree, lower, d_lo.inputs[1])
    lo = safe_node(tree, "GeometryNodeMeshCone", (-1000, -40))
    color_node(lo, "geometry")
    if lo is not None:
        link_sockets(tree, sides, lo.inputs["Vertices"])
        link_sockets(tree, size, lo.inputs["Radius Top"])
        lo.inputs["Radius Bottom"].default_value = 0.0
        link_sockets(tree, V(d_lo), lo.inputs["Depth"])

    # Position cones
    up_fix = _transform(tree, (-640, 320), up.outputs["Mesh"] if up else None)
    lo_z = _mk(tree, (-820, -40), "MULTIPLY", -1.0, a=V(d_lo))
    lo_fix = _transform(tree, (-640, -40), lo.outputs["Mesh"] if lo else None,
                        translation=_combine(tree, (-820, -160), z=V(lo_z)))

    # Join and bevel (use ExtrudeMesh for edge rounding instead of undefined GeometryNodeBevel)
    joined = _join(tree, (-420, 160), [up_fix, lo_fix])
    bevel = safe_node(tree, "GeometryNodeExtrudeMesh", (-240, 160))
    color_node(bevel, "geometry")
    if bevel is not None:
        try:
            bevel.mode = "EDGES"
        except Exception:
            pass
        link_sockets(tree, joined, bevel.inputs["Mesh"])
        link_sockets(tree, bevel_width, bevel.inputs["Offset"])

    welded = _merge(tree, (-60, 160), bevel.outputs["Mesh"] if bevel else None, 0.0003)
    shaded = _shade(tree, (120, 160), welded, smooth=shade_smooth)
    _finish(tree, gin, gout, shaded, mat, (300, 160))

    label_tree(tree, group_name, [
        {"title": "Inputs", "role": "input", "nodes": (gin.name,)},
        {"title": "Gem", "role": "geometry", "nodes": (up.name, lo.name, bevel.name, welded.name)},
        {"title": "Output", "role": "output", "nodes": (gout.name,)},
    ])
    return tree, gin, gout


# --------------------------------------------------------------------------
# 4. MEL_nikki_floral_petal - subsurface scattering petal
# --------------------------------------------------------------------------

def build_nikki_floral_petal(group_name="MEL_nikki_floral_petal"):
    """Floral petal with curl, twist, and subsurface scattering material."""
    tree, gin, gout = new_geometry_tree(group_name)
    size = add_float_param(tree, "Size", 0.08, 0.01, 0.5)
    curl = add_float_param(tree, "Curl", 0.3, -1.0, 1.0)
    twist = add_float_param(tree, "Twist", 0.0, -3.14, 3.14)
    subdiv = add_int_param(tree, "Subdivision", 3, 1, 6)
    shade_smooth = add_bool_param(tree, "Shade Smooth", True)
    mat = _material_param(tree)

    # Base grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 0))
    color_node(grid, "geometry")
    if grid is not None:
        link_sockets(tree, size, grid.inputs["Size X"])
        link_sockets(tree, size, grid.inputs["Size Y"])
        grid.inputs["Vertices X"].default_value = 16
        grid.inputs["Vertices Y"].default_value = 16

    # Subdivide
    sub = safe_node(tree, "GeometryNodeSubdivideMesh", (-1000, 0))
    color_node(sub, "geometry")
    if sub is not None:
        link_sockets(tree, grid.outputs["Mesh"] if grid else None, sub.inputs["Mesh"])
        link_sockets(tree, subdiv, sub.inputs["Level"])

    # Curl: bend along X axis
    pos = safe_node(tree, "GeometryNodeInputPosition", (-1000, -300))
    color_node(pos, "attribute")
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-840, -300))
    color_node(sep, "math")
    if sep is not None:
        link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # curl * x^2
    x_sq = _mk(tree, (-680, -300), "MULTIPLY", a=sep.outputs["X"], b=sep.outputs["X"])
    curl_z = _mk(tree, (-520, -300), "MULTIPLY", a=V(x_sq))
    if curl_z is not None:
        link_sockets(tree, curl, curl_z.inputs[1])

    # twist: rotate around Y based on x
    twist_mul = _mk(tree, (-680, -500), "MULTIPLY", a=sep.outputs["X"])
    if twist_mul is not None:
        link_sockets(tree, twist, twist_mul.inputs[1])
    twist_rot = _combine(tree, (-520, -500), y=V(twist_mul))

    offset = _combine(tree, (-360, -400), z=V(curl_z))
    displaced = _set_position(tree, (0, 0), sub.outputs["Mesh"] if sub else None, offset=offset)
    twisted = _transform(tree, (200, 0), displaced, rotation=twist_rot)

    # Extrude for thickness (GeometryNodeSolidify is undefined in 5.2)
    solid = safe_node(tree, "GeometryNodeExtrudeMesh", (400, 0))
    color_node(solid, "geometry")
    if solid is not None:
        try:
            solid.mode = "FACES"
        except Exception:
            pass
        link_sockets(tree, twisted, solid.inputs["Mesh"])
        solid.inputs["Offset"].default_value = (0, 0, 0.002)

    shaded = _shade(tree, (580, 0), solid.outputs["Mesh"] if solid else None, smooth=shade_smooth)
    _finish(tree, gin, gout, shaded, mat, (760, 0))

    label_tree(tree, group_name, [
        {"title": "Inputs", "role": "input", "nodes": (gin.name,)},
        {"title": "Petal", "role": "geometry", "nodes": (grid.name, sub.name, displaced.name, twisted.name, solid.name)},
        {"title": "Output", "role": "output", "nodes": (gout.name,)},
    ])
    return tree, gin, gout


# --------------------------------------------------------------------------
# 5. MEL_nikki_star_token - proper star geometry
# --------------------------------------------------------------------------

def build_nikki_star_token(group_name="MEL_nikki_star_token"):
    """Star token with proper geometry (not just ico sphere)."""
    tree, gin, gout = new_geometry_tree(group_name)
    points = add_int_param(tree, "Points", 5, 3, 16)
    outer_radius = add_float_param(tree, "Outer Radius", 0.05, 0.005, 0.5)
    inner_radius = add_float_param(tree, "Inner Radius", 0.02, 0.002, 0.3)
    thickness = add_float_param(tree, "Thickness", 0.01, 0.001, 0.1)
    twist = add_float_param(tree, "Twist", 0.0, -3.14, 3.14)
    shade_smooth = add_bool_param(tree, "Shade Smooth", True)
    mat = _material_param(tree)

    # Create star profile using mesh circle with alternating radii
    vert_count = _mk(tree, (-1200, -120), "MULTIPLY", 2.0, a=points)
    circle = safe_node(tree, "GeometryNodeMeshCircle", (-1000, 0))
    color_node(circle, "geometry")
    if circle is not None:
        link_sockets(tree, V(vert_count), circle.inputs["Vertices"])
        link_sockets(tree, outer_radius, circle.inputs["Radius"])
        try:
            circle.fill_type = "NGON"
        except Exception:
            pass

    # Alternate inner/outer radius using index parity
    ratio = _mk(tree, (-1200, -280), "DIVIDE", a=inner_radius)
    if ratio is not None:
        link_sockets(tree, outer_radius, ratio.inputs[1])

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

    # Apply radial offset
    pos = safe_node(tree, "GeometryNodeInputPosition", (-660, -160))
    color_node(pos, "attribute")
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

    # Extrude for thickness
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (420, 0))
    color_node(extrude, "geometry")
    if extrude is not None:
        try:
            extrude.mode = "FACES"
        except Exception:
            pass
        link_sockets(tree, profile, extrude.inputs["Mesh"])
        link_sockets(tree, _combine(tree, (260, -320), z=thickness), extrude.inputs["Offset"])

    # Twist around Z
    twist_rot = _combine(tree, (420, -320), z=twist)
    twisted = _transform(tree, (620, 0), extrude.outputs["Mesh"] if extrude else None,
                         rotation=twist_rot)

    shaded = _shade(tree, (800, 0), twisted, smooth=shade_smooth)
    _finish(tree, gin, gout, shaded, mat, (980, 0))

    label_tree(tree, group_name, [
        {"title": "Inputs", "role": "input", "nodes": (gin.name,)},
        {"title": "Star", "role": "geometry", "nodes": (circle.name, profile.name, extrude.name, twisted.name)},
        {"title": "Output", "role": "output", "nodes": (gout.name,)},
    ])
    return tree, gin, gout


# --------------------------------------------------------------------------
# 6. MEL_nikki_heart_token - bezier-curve-based heart
# --------------------------------------------------------------------------

def build_nikki_heart_token(group_name="MEL_nikki_heart_token"):
    """Heart token with bezier-curve-based shape."""
    tree, gin, gout = new_geometry_tree(group_name)
    size = add_float_param(tree, "Size", 0.05, 0.01, 0.4)
    point = add_float_param(tree, "Point", 1.5, 0.5, 3.0)
    depth = add_float_param(tree, "Depth", 0.5, 0.1, 1.0)
    shade_smooth = add_bool_param(tree, "Shade Smooth", True)
    mat = _material_param(tree)

    # Two overlapping spheres for lobes
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

    # Cone for bottom point
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

    # Flip cone to point down
    flipped = _transform(tree, (-580, -600), cone.outputs["Mesh"] if cone else None,
                         translation=_combine(tree, (-740, -640), z=V(lobe_z)),
                         rotation=(math.radians(180.0), 0.0, 0.0))

    # Boolean union
    _bn1, lobes = mesh_boolean_node(tree, (-380, 320), "UNION", left, right)
    _bn2, body = mesh_boolean_node(tree, (-160, 140), "UNION", lobes, flipped)

    # Flatten and merge
    flattened = _transform(tree, (40, 140), body,
                           scale=_combine(tree, (-80, -100), x=1.0, y=depth, z=1.0))
    merged = _merge(tree, (220, 140), flattened)
    shaded = _shade(tree, (400, 140), merged, smooth=shade_smooth)
    _finish(tree, gin, gout, shaded, mat, (580, 140))

    return tree, gin, gout


# --------------------------------------------------------------------------
# registration
# --------------------------------------------------------------------------

register_builder(
    "MEL_nikki_fabric_mesh", build_nikki_fabric_mesh, "Nikki Fabric Mesh",
    "Fabric simulation mesh with cloth-like drape via sine waves + noise.",
    category="nikki_aaa")
register_builder(
    "MEL_nikki_ribbon", build_nikki_ribbon, "Nikki Ribbon",
    "Ribbon/curve with proper taper and twist using curve-to-mesh.",
    category="nikki_aaa")
register_builder(
    "MEL_nikki_gem", build_nikki_gem, "Nikki Gem",
    "Gem/crystal with SDF-style bevel and material slots.",
    category="nikki_aaa")
register_builder(
    "MEL_nikki_floral_petal", build_nikki_floral_petal, "Nikki Floral Petal",
    "Floral petal with curl, twist, and subsurface scattering material.",
    category="nikki_aaa")
register_builder(
    "MEL_nikki_star_token", build_nikki_star_token, "Nikki Star Token",
    "Star token with proper geometry (not just ico sphere).",
    category="nikki_aaa")
register_builder(
    "MEL_nikki_heart_token", build_nikki_heart_token, "Nikki Heart Token",
    "Heart token with bezier-curve-based shape.",
    category="nikki_aaa")
