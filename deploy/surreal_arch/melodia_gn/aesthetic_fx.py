"""MEL aesthetic effect passes — absorbed from the monolith (P2 family 1).

70 effect-pass builders, one per _AESTHETIC_BUILDERS entry. Each is a
modifier-style group: Geometry IN -> decorated OUT. Params arrive as VALUES
at build time (monolith rebuild-on-change semantics); the group exposes the
same params as sockets for the UI and the P3 dispatch.

Generated 2026-09-04 by the P2 port (regenerable).
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)


# Monolith arch_type ids -> MEL_ ids (compat dispatch contract)
SLUGS = {
    "GOTH_TRACERY": "goth_tracery",
    "GOTH_DRIP": "goth_drip",
    "GOTH_SPIKES": "goth_spikes",
    "GOTH_RIBS": "goth_ribs",
    "GOTH_WEATHERED": "goth_weathered",
    "VAP_WIRE": "vap_wire",
    "VAP_PIXEL": "vap_pixel",
    "VAP_CHROMATIC": "vap_chromatic",
    "VAP_GRID": "vap_grid",
    "VAP_PALMS": "vap_palms",
    "ZEN_MOSS": "zen_moss",
    "ZEN_RIPPLE": "zen_ripple",
    "ZEN_SAND": "zen_sand",
    "ZEN_BAMBOO": "zen_bamboo",
    "ZEN_PETALS": "zen_petals",
    "SPI_AURA": "spi_aura",
    "SPI_MANDALA": "spi_mandala",
    "SPI_CHAKRA": "spi_chakra",
    "SPI_BEAM": "spi_beam",
    "SPI_RING": "spi_ring",
    "SPI_ASTRAL": "spi_astral",
    "SPI_EYE": "spi_eye",
    "SPI_LOTUS": "spi_lotus",
    "GOTH_LATTICE": "goth_lattice",
    "GOTH_NICHES": "goth_niches",
    "GOTH_FANS": "goth_fans",
    "GOTH_FINIALS": "goth_finials",
    "GOTH_LEADWORK": "goth_leadwork",
    "GOTH_SPIRES": "goth_spires",
    "VAP_SLICES": "vap_slices",
    "VAP_SCANLINES": "vap_scanlines",
    "VAP_BUSTS": "vap_busts",
    "VAP_SLABS": "vap_slabs",
    "VAP_SUN": "vap_sun",
    "VAP_NEON_WRAP": "vap_neon_wrap",
    "ZEN_ORBIT": "zen_orbit",
    "ZEN_SMOKE": "zen_smoke",
    "ZEN_POND": "zen_pond",
    "ZEN_TERRACE": "zen_terrace",
    "ZEN_GINKGO": "zen_ginkgo",
    "ZEN_RUNES": "zen_runes",
    "SPI_RUNES": "spi_runes",
    "SPI_HALO": "spi_halo",
    "SPI_TRIANGLES": "spi_triangles",
    "SPI_FLAMES": "spi_flames",
    "SPI_OUROBOROS": "spi_ouroboros",
    "SPI_PORTAL": "spi_portal",
    "MUS_PULSE": "mus_pulse",
    "MUS_EQ_BARS": "mus_eq_bars",
    "MUS_WAVE_DISP": "mus_wave_disp",
    "MUS_BEAT_RING": "mus_beat_ring",
    "MUS_HARMONIC": "mus_harmonic",
    "ADV_RAY_GROW": "adv_ray_grow",
    "ADV_NEAR_FUR": "adv_near_fur",
    "ADV_EDGE_TUBES": "adv_edge_tubes",
    "ADV_DUAL_MESH": "adv_dual_mesh",
    "ADV_VOR_FRAC": "adv_vor_frac",
    "ADV_CRYSTALS": "adv_crystals",
    "ADV_FIELD_LAT": "adv_field_lat",
    "GOTH_VAULT": "goth_vault",
    "GOTH_TRACERY2": "goth_tracery2",
    "VAP_DOLPHIN": "vap_dolphin",
    "ZEN_BONSAI": "zen_bonsai",
    "SPI_FLOWER": "spi_flower",
    "SPI_METATRON": "spi_metatron",
    "MECH_BOLTS": "mech_bolts",
    "MECH_PIPES": "mech_pipes",
    "MECH_GEARS": "mech_gears",
    "MECH_PISTONS": "mech_pistons",
    "MECH_PANELS": "mech_panels",
}

AESTHETIC_ENUM_MAP = {
    "GOTH_TRACERY": "MEL_aest_" + SLUGS["GOTH_TRACERY"],
    "GOTH_DRIP": "MEL_aest_" + SLUGS["GOTH_DRIP"],
    "GOTH_SPIKES": "MEL_aest_" + SLUGS["GOTH_SPIKES"],
    "GOTH_RIBS": "MEL_aest_" + SLUGS["GOTH_RIBS"],
    "GOTH_WEATHERED": "MEL_aest_" + SLUGS["GOTH_WEATHERED"],
    "VAP_WIRE": "MEL_aest_" + SLUGS["VAP_WIRE"],
    "VAP_PIXEL": "MEL_aest_" + SLUGS["VAP_PIXEL"],
    "VAP_CHROMATIC": "MEL_aest_" + SLUGS["VAP_CHROMATIC"],
    "VAP_GRID": "MEL_aest_" + SLUGS["VAP_GRID"],
    "VAP_PALMS": "MEL_aest_" + SLUGS["VAP_PALMS"],
    "ZEN_MOSS": "MEL_aest_" + SLUGS["ZEN_MOSS"],
    "ZEN_RIPPLE": "MEL_aest_" + SLUGS["ZEN_RIPPLE"],
    "ZEN_SAND": "MEL_aest_" + SLUGS["ZEN_SAND"],
    "ZEN_BAMBOO": "MEL_aest_" + SLUGS["ZEN_BAMBOO"],
    "ZEN_PETALS": "MEL_aest_" + SLUGS["ZEN_PETALS"],
    "SPI_AURA": "MEL_aest_" + SLUGS["SPI_AURA"],
    "SPI_MANDALA": "MEL_aest_" + SLUGS["SPI_MANDALA"],
    "SPI_CHAKRA": "MEL_aest_" + SLUGS["SPI_CHAKRA"],
    "SPI_BEAM": "MEL_aest_" + SLUGS["SPI_BEAM"],
    "SPI_RING": "MEL_aest_" + SLUGS["SPI_RING"],
    "SPI_ASTRAL": "MEL_aest_" + SLUGS["SPI_ASTRAL"],
    "SPI_EYE": "MEL_aest_" + SLUGS["SPI_EYE"],
    "SPI_LOTUS": "MEL_aest_" + SLUGS["SPI_LOTUS"],
    "GOTH_LATTICE": "MEL_aest_" + SLUGS["GOTH_LATTICE"],
    "GOTH_NICHES": "MEL_aest_" + SLUGS["GOTH_NICHES"],
    "GOTH_FANS": "MEL_aest_" + SLUGS["GOTH_FANS"],
    "GOTH_FINIALS": "MEL_aest_" + SLUGS["GOTH_FINIALS"],
    "GOTH_LEADWORK": "MEL_aest_" + SLUGS["GOTH_LEADWORK"],
    "GOTH_SPIRES": "MEL_aest_" + SLUGS["GOTH_SPIRES"],
    "VAP_SLICES": "MEL_aest_" + SLUGS["VAP_SLICES"],
    "VAP_SCANLINES": "MEL_aest_" + SLUGS["VAP_SCANLINES"],
    "VAP_BUSTS": "MEL_aest_" + SLUGS["VAP_BUSTS"],
    "VAP_SLABS": "MEL_aest_" + SLUGS["VAP_SLABS"],
    "VAP_SUN": "MEL_aest_" + SLUGS["VAP_SUN"],
    "VAP_NEON_WRAP": "MEL_aest_" + SLUGS["VAP_NEON_WRAP"],
    "ZEN_ORBIT": "MEL_aest_" + SLUGS["ZEN_ORBIT"],
    "ZEN_SMOKE": "MEL_aest_" + SLUGS["ZEN_SMOKE"],
    "ZEN_POND": "MEL_aest_" + SLUGS["ZEN_POND"],
    "ZEN_TERRACE": "MEL_aest_" + SLUGS["ZEN_TERRACE"],
    "ZEN_GINKGO": "MEL_aest_" + SLUGS["ZEN_GINKGO"],
    "ZEN_RUNES": "MEL_aest_" + SLUGS["ZEN_RUNES"],
    "SPI_RUNES": "MEL_aest_" + SLUGS["SPI_RUNES"],
    "SPI_HALO": "MEL_aest_" + SLUGS["SPI_HALO"],
    "SPI_TRIANGLES": "MEL_aest_" + SLUGS["SPI_TRIANGLES"],
    "SPI_FLAMES": "MEL_aest_" + SLUGS["SPI_FLAMES"],
    "SPI_OUROBOROS": "MEL_aest_" + SLUGS["SPI_OUROBOROS"],
    "SPI_PORTAL": "MEL_aest_" + SLUGS["SPI_PORTAL"],
    "MUS_PULSE": "MEL_aest_" + SLUGS["MUS_PULSE"],
    "MUS_EQ_BARS": "MEL_aest_" + SLUGS["MUS_EQ_BARS"],
    "MUS_WAVE_DISP": "MEL_aest_" + SLUGS["MUS_WAVE_DISP"],
    "MUS_BEAT_RING": "MEL_aest_" + SLUGS["MUS_BEAT_RING"],
    "MUS_HARMONIC": "MEL_aest_" + SLUGS["MUS_HARMONIC"],
    "ADV_RAY_GROW": "MEL_aest_" + SLUGS["ADV_RAY_GROW"],
    "ADV_NEAR_FUR": "MEL_aest_" + SLUGS["ADV_NEAR_FUR"],
    "ADV_EDGE_TUBES": "MEL_aest_" + SLUGS["ADV_EDGE_TUBES"],
    "ADV_DUAL_MESH": "MEL_aest_" + SLUGS["ADV_DUAL_MESH"],
    "ADV_VOR_FRAC": "MEL_aest_" + SLUGS["ADV_VOR_FRAC"],
    "ADV_CRYSTALS": "MEL_aest_" + SLUGS["ADV_CRYSTALS"],
    "ADV_FIELD_LAT": "MEL_aest_" + SLUGS["ADV_FIELD_LAT"],
    "GOTH_VAULT": "MEL_aest_" + SLUGS["GOTH_VAULT"],
    "GOTH_TRACERY2": "MEL_aest_" + SLUGS["GOTH_TRACERY2"],
    "VAP_DOLPHIN": "MEL_aest_" + SLUGS["VAP_DOLPHIN"],
    "ZEN_BONSAI": "MEL_aest_" + SLUGS["ZEN_BONSAI"],
    "SPI_FLOWER": "MEL_aest_" + SLUGS["SPI_FLOWER"],
    "SPI_METATRON": "MEL_aest_" + SLUGS["SPI_METATRON"],
    "MECH_BOLTS": "MEL_aest_" + SLUGS["MECH_BOLTS"],
    "MECH_PIPES": "MEL_aest_" + SLUGS["MECH_PIPES"],
    "MECH_GEARS": "MEL_aest_" + SLUGS["MECH_GEARS"],
    "MECH_PISTONS": "MEL_aest_" + SLUGS["MECH_PISTONS"],
    "MECH_PANELS": "MEL_aest_" + SLUGS["MECH_PANELS"],
}


# ---- helpers (ported from monolith, package-safe) ----

def _get_input_geom(tree):
    for n in tree.nodes:
        if n.type == 'GROUP_INPUT':
            for out in n.outputs:
                if out.type == 'GEOMETRY':
                    return out
    return None


def _link(tree, srcc, dst):
    if srcc is not None and dst is not None:
        try:
            tree.links.new(srcc, dst)
        except Exception:
            pass


def _safe_node(tree, bl_idname, loc=(0, 0)):
    try:
        n = tree.nodes.new(bl_idname)
        n.location = loc
        return n
    except Exception:
        return None


def _node(tree, bl_idname, loc=(0, 0), **kwargs):
    return _safe_node(tree, bl_idname, loc)


def _instance_on_surface(tree, in_geom, instance_mesh_out, density, seed,
                         align_normal=True, scale=None, rand_scale=0.0,
                         x_off=0, label="ornament"):
    pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (x_off, 0))
    if pts is None or in_geom is None or instance_mesh_out is None:
        return None
    pts.distribute_method = 'POISSON'
    pts.inputs['Distance Min'].default_value = 0.3 / max(0.1, density)
    pts.inputs['Density Max'].default_value = density * 3.0
    pts.inputs['Seed'].default_value = seed
    _link(tree, in_geom, pts.inputs['Mesh'])
    color_node(pts, "input")
    inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (x_off + 250, 0))
    if inst is None:
        return None
    _link(tree, pts.outputs['Points'], inst.inputs['Points'])
    _link(tree, instance_mesh_out, inst.inputs['Instance'])
    if align_normal:
        try:
            _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
        except Exception:
            pass
    if scale is not None:
        inst.inputs['Scale'].default_value = scale
    if rand_scale > 0.0:
        rs = _safe_node(tree, 'FunctionNodeRandomValue', (x_off + 250, -250))
        if rs:
            rs.data_type = 'FLOAT'
            try:
                rs.inputs['Min'].default_value = 1.0 - rand_scale
                rs.inputs['Max'].default_value = 1.0 + rand_scale
                rs.inputs['Seed'].default_value = seed
                _link(tree, rs.outputs['Value'], inst.inputs['Scale'])
            except Exception:
                pass
    real = _safe_node(tree, 'GeometryNodeRealizeInstances', (x_off + 500, 0))
    if real:
        _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        color_node(inst, label)
        color_node(real, label)
        return real.outputs['Geometry']
    return None


def _join_with_input(tree, in_geom, extra_out, x_off=1500):
    join = _safe_node(tree, 'GeometryNodeJoinGeometry', (x_off, 0))
    if join is None:
        return in_geom
    if in_geom:
        _link(tree, in_geom, join.inputs['Geometry'])
    if extra_out:
        _link(tree, extra_out, join.inputs['Geometry'])
    return join.outputs['Geometry']


def _aest_mask_field(tree, P, loc=(-700, 400)):
    """Ported mask-field helper: 1.0 everywhere unless a mask name is set."""
    name = (P.get("mask", "") or "").strip()
    if not name:
        const = _node(tree, 'ShaderNodeValue', loc)
        const.outputs[0].default_value = 1.0
        color_node(const, "input")
        return const.outputs[0]
    na = _safe_node(tree, 'GeometryNodeInputNamedAttribute', loc)
    if na is None:
        const = _node(tree, 'ShaderNodeValue', loc)
        const.outputs[0].default_value = 1.0
        return const.outputs[0]
    try:
        na.data_type = 'FLOAT'
        na.inputs[0].default_value = name
        return na.outputs[0]
    except Exception:
        const = _node(tree, 'ShaderNodeValue', loc)
        const.outputs[0].default_value = 1.0
        return const.outputs[0]

def _make_circle_profile(tree, radius, resolution=8, loc=(-400, -600), P=None):
    """Build the user-selected sweep profile and return a stub object whose
    `.outputs['Curve']` is the profile curve socket.

    Backwards-compatible wrapper: callers that pass no `P` get a circle.
    With `P`, picks from `P.aest_profile`."""
    kind = ['CIRCLE', 'SQUARE', 'FLUTE'][P.get("profile", 0)] if P else "CIRCLE"

    class _ProfileStub:
        def __init__(self, sock):
            self.outputs = {'Curve': sock}

    # CIRCLE - default round tube
    if kind == 'CIRCLE':
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = resolution
            prof.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        color_node(prof, "input")
        return prof

    # SQUARE - quadrilateral via 4-resolution circle (gives a diamond,
    # but a Curve Line ring of 4 points is closer)
    if kind == 'SQUARE':
        # Build a quad as a small bezier closed curve via Curve Line w/4 segments
        # Easiest: a circle with 4 verts (rotated 45deg gives diamond - fine).
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = 4
            prof.inputs['Radius'].default_value     = radius * 1.2
        except Exception:
            return None
        color_node(prof, "input")
        return prof

    # FLUTE - multi-lobed circle: build by Set Position on a high-res circle
    # using radial sin to perturb the radius
    if kind == 'FLUTE':
        base = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if base is None:
            return None
        try:
            base.inputs['Resolution'].default_value = 48
            base.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        # Per-point radial perturbation: sin(angle * 8) * radius * 0.25
        pos = _node(tree, 'GeometryNodeInputPosition', (loc[0] - 200, loc[1] - 200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (loc[0] - 50, loc[1] - 200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        atan = _node(tree, 'ShaderNodeMath', (loc[0] + 100, loc[1] - 200))
        atan.operation = 'ARCTAN2'
        _link(tree, sep.outputs['Y'], atan.inputs[0])
        _link(tree, sep.outputs['X'], atan.inputs[1])
        mul = _node(tree, 'ShaderNodeMath', (loc[0] + 250, loc[1] - 200))
        mul.operation = 'MULTIPLY'
        _link(tree, atan.outputs['Value'], mul.inputs[0])
        mul.inputs[1].default_value = 8.0   # 8 flutes
        sn = _node(tree, 'ShaderNodeMath', (loc[0] + 400, loc[1] - 200))
        sn.operation = 'SINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 200))
        amp.operation = 'MULTIPLY'
        _link(tree, sn.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = radius * 0.3
        # Push verts outward along their own direction (just X,Y scaled)
        scale_n = _node(tree, 'ShaderNodeVectorMath', (loc[0] + 700, loc[1] - 100))
        scale_n.operation = 'SCALE'
        _link(tree, pos.outputs['Position'], scale_n.inputs[0])
        # normalize-ish: we'll use the position itself; small offset is fine
        norm_div = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 300))
        norm_div.operation = 'DIVIDE'
        _link(tree, amp.outputs['Value'], norm_div.inputs[0])
        norm_div.inputs[1].default_value = max(0.001, radius)
        _link(tree, norm_div.outputs['Value'], scale_n.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (loc[0] + 900, loc[1]))
        if sp:
            _link(tree, base.outputs['Curve'], sp.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
            color_node(base, "input"); color_node(sp, "input")
            return _ProfileStub(sp.outputs['Geometry'])
        return base

    # OGEE - S-curve: two quadratic beziers stitched. Approximate with
    # a thin tall oval (circle scaled along Y) for now.
    if kind == 'OGEE':
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = 16
            prof.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        # Scale the circle into an oval via Transform
        tr = _node(tree, 'GeometryNodeTransform', (loc[0] + 250, loc[1]))
        tr.inputs['Scale'].default_value = (0.5, 1.4, 1.0)
        _link(tree, prof.outputs['Curve'], tr.inputs['Geometry'])
        color_node(prof, "input"); color_node(tr, "input")
        return _ProfileStub(tr.outputs['Geometry'])

    # LOTUS - pointed-petal cross-section (5-pointed)
    if kind == 'LOTUS':
        base = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if base is None:
            return None
        try:
            base.inputs['Resolution'].default_value = 60
            base.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        pos = _node(tree, 'GeometryNodeInputPosition', (loc[0] - 200, loc[1] - 200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (loc[0] - 50, loc[1] - 200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        atan = _node(tree, 'ShaderNodeMath', (loc[0] + 100, loc[1] - 200))
        atan.operation = 'ARCTAN2'
        _link(tree, sep.outputs['Y'], atan.inputs[0])
        _link(tree, sep.outputs['X'], atan.inputs[1])
        mul = _node(tree, 'ShaderNodeMath', (loc[0] + 250, loc[1] - 200))
        mul.operation = 'MULTIPLY'
        _link(tree, atan.outputs['Value'], mul.inputs[0])
        mul.inputs[1].default_value = 5.0   # 5 petals
        sn = _node(tree, 'ShaderNodeMath', (loc[0] + 400, loc[1] - 200))
        sn.operation = 'COSINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        abs_n = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 200))
        abs_n.operation = 'ABSOLUTE'
        _link(tree, sn.outputs['Value'], abs_n.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (loc[0] + 700, loc[1] - 200))
        amp.operation = 'MULTIPLY'
        _link(tree, abs_n.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = radius * 0.6
        scale_n = _node(tree, 'ShaderNodeVectorMath', (loc[0] + 700, loc[1] - 50))
        scale_n.operation = 'SCALE'
        _link(tree, pos.outputs['Position'], scale_n.inputs[0])
        norm_div = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 350))
        norm_div.operation = 'DIVIDE'
        _link(tree, amp.outputs['Value'], norm_div.inputs[0])
        norm_div.inputs[1].default_value = max(0.001, radius)
        _link(tree, norm_div.outputs['Value'], scale_n.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (loc[0] + 900, loc[1]))
        if sp:
            _link(tree, base.outputs['Curve'], sp.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
            color_node(base, "input"); color_node(sp, "input")
            return _ProfileStub(sp.outputs['Geometry'])
        return base

    # Fallback: circle
    prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
    if prof is None:
        return None
    try:
        prof.inputs['Resolution'].default_value = resolution
        prof.inputs['Radius'].default_value     = radius
    except Exception:
        return None
    color_node(prof, "input")
    return prof


def _music_mod(P, base, k=1.0):
    """Return base modulated by universal music influence × aest_music_gain."""
    if not P.get("music_react", False):
        return base
    inf = P.get("music_influence", 0.0)
    gain = P.get("music_gain", 1.0)
    return base * (1.0 + inf * gain * k)


def _sweep_curve(tree, curve_out, profile_out, loc=(0, 0), label="ornament"):
    """Curve to Mesh sweep helper."""
    c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', loc)
    if c2m is None or curve_out is None or profile_out is None:
        return None
    _link(tree, curve_out, c2m.inputs['Curve'])
    _link(tree, profile_out, c2m.inputs['Profile Curve'])
    try:
        c2m.inputs['Fill Caps'].default_value = True
    except Exception:
        pass
    color_node(c2m, label)
    return c2m.outputs['Mesh']


def _gothic_arch_curve(tree, width, height, pointiness=0.6, x=0, y=0):
    """Build a pointed-arch silhouette as a bezier curve.
    Returns the curve output socket, or None if quadratic bezier node missing.
    Uses 3 control points: bottom-left -> apex (pointy) -> bottom-right."""
    qb = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (x, y))
    if qb is None:
        return None
    try:
        qb.inputs['Resolution'].default_value = 32
        qb.inputs['Start'].default_value      = (-width * 0.5, 0, 0)
        # Middle controls "lift" - push it up + slightly outward for Gothic pointy
        qb.inputs['Middle'].default_value     = (0, 0, height * (1.0 + pointiness * 0.4))
        qb.inputs['End'].default_value        = (width * 0.5, 0, 0)
    except Exception:
        return None
    color_node(qb, "gothic")
    return qb.outputs['Curve']



def _noise_scale_for(P, base):
    return max(0.5, base * P["density"])


def _aest_val(P, kind):
    base = {
        'INTENSITY': P.get("intensity", 1.0),
        'DENSITY': P.get("density", 0.7),
        'SCALE': P.get("scale", 1.0),
    }
    return base.get(kind, 1.0)


DEFAULT_PARAMS = {
    "scale": 1.0, "intensity": 0.6, "density": 0.7,
    "layers": 2, "seed": 7, "mask": "", "profile": 0,
}


def _add_aesthetic_params(tree):
    add_float_param(tree, "Element Scale", 1.0, 0.1, 5.0)
    add_float_param(tree, "Intensity", 0.6, 0.0, 2.0)
    add_float_param(tree, "Density", 0.7, 0.05, 3.0)
    add_int_param(tree, "Layers", 2, 1, 5)
    add_int_param(tree, "Seed", 7, 0, 99999)
    add_string_param(tree, "Mask Attribute", "")
    add_int_param(tree, "Sweep Profile", 0, 0, 3)


def build_aest_goth_tracery_group(group_name="MEL_aest_goth_tracery"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Distribute Gothic cross/star ornaments on every face."""
        in_geom = _get_input_geom(tree)
        # Cross shape = two thin overlapping boxes
        arm_x = _node(tree, 'GeometryNodeMeshCube', (-500, -300))
        arm_x.inputs['Size'].default_value = (0.25 * P["scale"], 0.05 * P["scale"], 0.03 * P["scale"])
        arm_z = _node(tree, 'GeometryNodeMeshCube', (-500, -500))
        arm_z.inputs['Size'].default_value = (0.06 * P["scale"], 0.05 * P["scale"], 0.25 * P["scale"])
        j1 = _node(tree, 'GeometryNodeJoinGeometry', (-250, -400))
        _link(tree, arm_x.outputs['Mesh'], j1.inputs['Geometry'])
        _link(tree, arm_z.outputs['Mesh'], j1.inputs['Geometry'])
        color_node(arm_x, "gothic"); color_node(arm_z, "gothic"); color_node(j1, "gothic")
        real = _instance_on_surface(tree, in_geom, j1.outputs['Geometry'],
                                    P["density"] * 1.2, P["seed"],
                                    rand_scale=0.3, x_off=0, label="gothic")
        return _join_with_input(tree, in_geom, real)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_tracery")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_tracery", build_aest_goth_tracery_group,
    "Goth Tracery", "Aesthetic effect pass (absorbed from monolith build_aest_goth_tracery).",
    category="effects", role="modifier")


def build_aest_goth_drip_group(group_name="MEL_aest_goth_drip"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Vertical drips on lower portion of mesh via subdivision + downward displacement."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -250))
        # Noise to create drip mask
        noise = _safe_node(tree, 'ShaderNodeTexNoise', (250, -250))
        if noise:
            noise.inputs['Scale'].default_value = P["density"] * 6.0
            noise.inputs['Detail'].default_value = 4.0
            _link(tree, pos.outputs['Position'], noise.inputs['Vector'])
            color_node(noise, "noise")
        # Drip vector: only Z<0 direction
        vec = _node(tree, 'ShaderNodeCombineXYZ', (500, -250))
        if noise:
            # Scale drip by intensity
            mult = _node(tree, 'ShaderNodeMath', (500, -450))
            mult.operation = 'MULTIPLY'
            _link(tree, noise.outputs['Fac'], mult.inputs[0])
            mult.inputs[1].default_value = -P["intensity"] * 0.8
            _link(tree, mult.outputs['Value'], vec.inputs['Z'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (800, 0))
        if set_pos and subd:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, vec.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "gothic")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_drip")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_drip", build_aest_goth_drip_group,
    "Goth Drip", "Aesthetic effect pass (absorbed from monolith build_aest_goth_drip).",
    category="effects", role="modifier")


def build_aest_goth_spikes_group(group_name="MEL_aest_goth_spikes"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Sharp cone spikes outward along normals."""
        in_geom = _get_input_geom(tree)
        cone = _safe_node(tree, 'GeometryNodeMeshCone', (-500, -300))
        if cone:
            cone.inputs['Radius Bottom'].default_value = 0.08 * P["scale"]
            cone.inputs['Radius Top'].default_value    = 0.0
            cone.inputs['Depth'].default_value         = 0.5 * P["scale"] * P["intensity"]
            cone.inputs['Vertices'].default_value      = 6
            color_node(cone, "gothic")
            # Translate so base sits at origin
            t = _node(tree, 'GeometryNodeTransform', (-250, -300))
            t.inputs['Translation'].default_value = (0, 0, 0.25 * P["scale"] * P["intensity"])
            _link(tree, cone.outputs['Mesh'], t.inputs['Geometry'])
            # Rotate so cone points along +Z (default already)
            real = _instance_on_surface(tree, in_geom, t.outputs['Geometry'],
                                        P["density"], P["seed"],
                                        rand_scale=0.4, x_off=0, label="gothic")
            return _join_with_input(tree, in_geom, real)
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_spikes")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_spikes", build_aest_goth_spikes_group,
    "Goth Spikes", "Aesthetic effect pass (absorbed from monolith build_aest_goth_spikes).",
    category="effects", role="modifier")


def build_aest_goth_ribs_group(group_name="MEL_aest_goth_ribs"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Vertical Gothic ribs wrapping the silhouette."""
        in_geom = _get_input_geom(tree)
        # Build N vertical thin pillars in a circle around the bbox
        n_ribs = max(4, int(P["density"] * 8))
        pieces = []
        for i in range(n_ribs):
            import math
            ang = (i / n_ribs) * 6.283185
            radius = 1.2 * P["scale"]
            rib = _node(tree, 'GeometryNodeMeshCylinder', (-400 + (i % 4) * 200, -200 - (i // 4) * 200))
            rib.inputs['Radius'].default_value = 0.04 * P["scale"]
            rib.inputs['Depth'].default_value  = 3.0 * P["intensity"]
            rib.inputs['Vertices'].default_value = 6
            tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 4) * 200, -200 - (i // 4) * 200))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius, 1.5 * P["intensity"])
            _link(tree, rib.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(rib, "gothic"); color_node(tr, "gothic")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_ribs")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_ribs", build_aest_goth_ribs_group,
    "Goth Ribs", "Aesthetic effect pass (absorbed from monolith build_aest_goth_ribs).",
    category="effects", role="modifier")


def build_aest_goth_weathered_group(group_name="MEL_aest_goth_weathered"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Weathered/cracked stone: subdivide and noise-displace inward."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        noise = _safe_node(tree, 'ShaderNodeTexNoise', (250, -200))
        if noise:
            noise.inputs['Scale'].default_value = P["density"] * 5.0
            noise.inputs['Detail'].default_value = 6.0
            noise.inputs['Roughness'].default_value = 0.7
            _link(tree, pos.outputs['Position'], noise.inputs['Vector'])
            color_node(noise, "noise")
        # Normal direction for inward displace
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -400))
        sub_v = _node(tree, 'ShaderNodeVectorMath', (450, -350))
        sub_v.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], sub_v.inputs[0])
        if noise:
            mult = _node(tree, 'ShaderNodeMath', (450, -550))
            mult.operation = 'MULTIPLY'
            _link(tree, noise.outputs['Fac'], mult.inputs[0])
            mult.inputs[1].default_value = -P["intensity"] * 0.25
            _link(tree, mult.outputs['Value'], sub_v.inputs['Scale'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (800, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, sub_v.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "gothic")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    # ---- * VAPORWAVE ------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_weathered")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_weathered", build_aest_goth_weathered_group,
    "Goth Weathered", "Aesthetic effect pass (absorbed from monolith build_aest_goth_weathered).",
    category="effects", role="modifier")


def build_aest_vap_wire_group(group_name="MEL_aest_vap_wire"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Pastel neon wireframe overlay."""
        in_geom = _get_input_geom(tree)
        wire = _safe_node(tree, 'GeometryNodeWireframe', (0, 0))
        if wire and in_geom:
            try:
                wire.inputs['Radius'].default_value = 0.02 * P["intensity"] * P["scale"]
            except Exception:
                pass
            _link(tree, in_geom, wire.inputs['Mesh'])
            color_node(wire, "tracery")
            return _join_with_input(tree, in_geom, wire.outputs['Curve'] if 'Curve' in wire.outputs else wire.outputs[0])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_wire")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_wire", build_aest_vap_wire_group,
    "Vap Wire", "Aesthetic effect pass (absorbed from monolith build_aest_vap_wire).",
    category="effects", role="modifier")


def build_aest_vap_pixel_group(group_name="MEL_aest_vap_pixel"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Voxelize the mesh into floating cubes."""
        in_geom = _get_input_geom(tree)
        m2v = _safe_node(tree, 'GeometryNodeMeshToVolume', (0, 0))
        if m2v and in_geom:
            try: m2v.resolution_mode = 'VOXEL_SIZE'
            except (AttributeError, TypeError): pass
            m2v.inputs['Voxel Size'].default_value = max(0.05, 0.3 / max(0.1, P["density"]))
            try:
                m2v.inputs['Density'].default_value = 1.0
            except Exception:
                pass
            _link(tree, in_geom, m2v.inputs['Mesh'])
            color_node(m2v, "noise")
            # Distribute points in volume -> cube instances
            dpts = _safe_node(tree, 'GeometryNodeDistributePointsInVolume', (300, 0))
            if dpts:
                try: dpts.mode = 'DENSITY_GRID'

                except (AttributeError, TypeError):

                    try: dpts.inputs['Mode'].default_value = 'DENSITY_GRID'

                    except Exception: pass
                try:
                    dpts.inputs['Spacing'].default_value = (0.2 / max(0.1, P["density"]),) * 3
                except Exception:
                    pass
                _link(tree, m2v.outputs['Volume'], dpts.inputs['Volume'])
                cube = _node(tree, 'GeometryNodeMeshCube', (300, -250))
                sz = 0.15 * P["scale"]
                cube.inputs['Size'].default_value = (sz, sz, sz)
                inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (550, 0))
                if inst:
                    _link(tree, dpts.outputs['Points'], inst.inputs['Points'])
                    _link(tree, cube.outputs['Mesh'], inst.inputs['Instance'])
                    real = _safe_node(tree, 'GeometryNodeRealizeInstances', (800, 0))
                    if real:
                        _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
                        color_node(inst, "modular"); color_node(real, "modular")
                        return real.outputs['Geometry']
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_pixel")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_pixel", build_aest_vap_pixel_group,
    "Vap Pixel", "Aesthetic effect pass (absorbed from monolith build_aest_vap_pixel).",
    category="effects", role="modifier")


def build_aest_vap_chromatic_group(group_name="MEL_aest_vap_chromatic"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Three offset ghost copies in R/G/B-coded XY directions."""
        in_geom = _get_input_geom(tree)
        pieces = []
        offsets = [
            (P["intensity"] * 0.3, 0, 0),
            (-P["intensity"] * 0.15, P["intensity"] * 0.25, 0),
            (-P["intensity"] * 0.15, -P["intensity"] * 0.25, 0),
        ]
        for i, off in enumerate(offsets):
            t = _node(tree, 'GeometryNodeTransform', (250 * (i+1), -200 * (i+1)))
            t.inputs['Translation'].default_value = off
            if in_geom:
                _link(tree, in_geom, t.inputs['Geometry'])
            color_node(t, "ornament")
            pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (1100, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_chromatic")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_chromatic", build_aest_vap_chromatic_group,
    "Vap Chromatic", "Aesthetic effect pass (absorbed from monolith build_aest_vap_chromatic).",
    category="effects", role="modifier")


def build_aest_vap_grid_group(group_name="MEL_aest_vap_grid"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Tron grid lines on the surface (distribute thin bar instances)."""
        in_geom = _get_input_geom(tree)
        bar = _node(tree, 'GeometryNodeMeshCube', (-400, -300))
        bar.inputs['Size'].default_value = (0.6 * P["scale"], 0.025 * P["scale"], 0.025 * P["scale"])
        color_node(bar, "tracery")
        real = _instance_on_surface(tree, in_geom, bar.outputs['Mesh'],
                                    P["density"] * 1.5, P["seed"],
                                    rand_scale=0.0, x_off=0, label="tracery")
        return _join_with_input(tree, in_geom, real)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_grid")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_grid", build_aest_vap_grid_group,
    "Vap Grid", "Aesthetic effect pass (absorbed from monolith build_aest_vap_grid).",
    category="effects", role="modifier")


def build_aest_vap_palms_group(group_name="MEL_aest_vap_palms"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Pink/teal palm-tree-like cones in a ring around the base."""
        in_geom = _get_input_geom(tree)
        pieces = []
        n_palms = max(3, int(P["density"] * 6))
        radius = 2.5 * P["scale"]
        import math
        for i in range(n_palms):
            ang = (i / n_palms) * 6.283185
            # trunk
            trunk = _node(tree, 'GeometryNodeMeshCylinder', (-400, -200 - i * 80))
            trunk.inputs['Radius'].default_value = 0.08 * P["scale"]
            trunk.inputs['Depth'].default_value  = 2.0 * P["intensity"]
            trunk.inputs['Vertices'].default_value = 8
            # leaves cone
            leaves = _safe_node(tree, 'GeometryNodeMeshCone', (-200, -200 - i * 80))
            if leaves:
                leaves.inputs['Radius Bottom'].default_value = 0.45 * P["scale"]
                leaves.inputs['Radius Top'].default_value    = 0.0
                leaves.inputs['Depth'].default_value         = 0.7 * P["scale"]
                leaves.inputs['Vertices'].default_value      = 24
                tr_l = _node(tree, 'GeometryNodeTransform', (0, -200 - i * 80))
                tr_l.inputs['Translation'].default_value = (0, 0, 1.0 * P["intensity"] + 0.3)
                _link(tree, leaves.outputs['Mesh'], tr_l.inputs['Geometry'])
                color_node(leaves, "organic"); color_node(tr_l, "organic")
            j_palm = _node(tree, 'GeometryNodeJoinGeometry', (200, -200 - i * 80))
            _link(tree, trunk.outputs['Mesh'], j_palm.inputs['Geometry'])
            if leaves:
                _link(tree, tr_l.outputs['Geometry'], j_palm.inputs['Geometry'])
            # place around ring
            tr = _node(tree, 'GeometryNodeTransform', (400, -200 - i * 80))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius, 0.0)
            _link(tree, j_palm.outputs['Geometry'], tr.inputs['Geometry'])
            color_node(trunk, "organic"); color_node(j_palm, "organic"); color_node(tr, "organic")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (700, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    # ---- * ZEN ------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_palms")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_palms", build_aest_vap_palms_group,
    "Vap Palms", "Aesthetic effect pass (absorbed from monolith build_aest_vap_palms).",
    category="effects", role="modifier")


def build_aest_zen_moss_group(group_name="MEL_aest_zen_moss"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Soft moss spheres on upward-facing surfaces."""
        in_geom = _get_input_geom(tree)
        sph = _node(tree, 'GeometryNodeMeshUVSphere', (-500, -300))
        sph.inputs['Segments'].default_value = 8
        sph.inputs['Rings'].default_value    = 5
        sph.inputs['Radius'].default_value   = 0.12 * P["scale"]
        color_node(sph, "organic")
        real = _instance_on_surface(tree, in_geom, sph.outputs['Mesh'],
                                    P["density"] * 2.0, P["seed"],
                                    rand_scale=0.5, x_off=0, label="organic")
        return _join_with_input(tree, in_geom, real)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_moss")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_moss", build_aest_zen_moss_group,
    "Zen Moss", "Aesthetic effect pass (absorbed from monolith build_aest_zen_moss).",
    category="effects", role="modifier")


def build_aest_zen_ripple_group(group_name="MEL_aest_zen_ripple"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Concentric ripples from origin: sine of XY distance."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 2)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (200, -200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        # length(x,y)
        lenv = _node(tree, 'ShaderNodeVectorMath', (400, -200))
        lenv.operation = 'LENGTH'
        comb = _node(tree, 'ShaderNodeCombineXYZ', (250, -350))
        _link(tree, sep.outputs['X'], comb.inputs['X'])
        _link(tree, sep.outputs['Y'], comb.inputs['Y'])
        _link(tree, comb.outputs['Vector'], lenv.inputs[0])
        mul = _node(tree, 'ShaderNodeMath', (600, -200))
        mul.operation = 'MULTIPLY'
        _link(tree, lenv.outputs['Value'], mul.inputs[0])
        mul.inputs[1].default_value = P["density"] * 4.0
        sn = _node(tree, 'ShaderNodeMath', (800, -200))
        sn.operation = 'SINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (1000, -200))
        amp.operation = 'MULTIPLY'
        _link(tree, sn.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = P["intensity"] * 0.3
        vec = _node(tree, 'ShaderNodeCombineXYZ', (1200, -200))
        _link(tree, amp.outputs['Value'], vec.inputs['Z'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (1400, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, vec.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "organic")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_ripple")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_ripple", build_aest_zen_ripple_group,
    "Zen Ripple", "Aesthetic effect pass (absorbed from monolith build_aest_zen_ripple).",
    category="effects", role="modifier")


def build_aest_zen_sand_group(group_name="MEL_aest_zen_sand"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Karesansui raked sand on top: sine grooves in Z, on top faces only."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (200, -200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        mul_x = _node(tree, 'ShaderNodeMath', (400, -200))
        mul_x.operation = 'MULTIPLY'
        _link(tree, sep.outputs['X'], mul_x.inputs[0])
        mul_x.inputs[1].default_value = P["density"] * 6.0
        sn = _node(tree, 'ShaderNodeMath', (600, -200))
        sn.operation = 'SINE'
        _link(tree, mul_x.outputs['Value'], sn.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (800, -200))
        amp.operation = 'MULTIPLY'
        _link(tree, sn.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = P["intensity"] * 0.12
        # Top-face mask: ramp on normal.z
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -500))
        sep_n  = _node(tree, 'ShaderNodeSeparateXYZ', (200, -500))
        _link(tree, normal.outputs['Normal'], sep_n.inputs['Vector'])
        mask_mul = _node(tree, 'ShaderNodeMath', (600, -500))
        mask_mul.operation = 'MAXIMUM'
        _link(tree, sep_n.outputs['Z'], mask_mul.inputs[0])
        mask_mul.inputs[1].default_value = 0.0
        # multiply grooves by top mask
        gated = _node(tree, 'ShaderNodeMath', (1000, -400))
        gated.operation = 'MULTIPLY'
        _link(tree, amp.outputs['Value'], gated.inputs[0])
        _link(tree, mask_mul.outputs['Value'], gated.inputs[1])
        vec = _node(tree, 'ShaderNodeCombineXYZ', (1200, -400))
        _link(tree, gated.outputs['Value'], vec.inputs['Z'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (1400, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, vec.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "organic")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_sand")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_sand", build_aest_zen_sand_group,
    "Zen Sand", "Aesthetic effect pass (absorbed from monolith build_aest_zen_sand).",
    category="effects", role="modifier")


def build_aest_zen_bamboo_group(group_name="MEL_aest_zen_bamboo"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Vertical bamboo poles around the bbox perimeter."""
        in_geom = _get_input_geom(tree)
        n = max(6, int(P["density"] * 12))
        pieces = []
        import math
        radius = 1.8 * P["scale"]
        for i in range(n):
            ang = (i / n) * 6.283185
            # bamboo cylinder
            pole = _node(tree, 'GeometryNodeMeshCylinder', (-400 + (i % 5) * 200, -200 - (i // 5) * 200))
            pole.inputs['Radius'].default_value   = 0.05 * P["scale"]
            pole.inputs['Depth'].default_value    = 3.5 * P["intensity"]
            pole.inputs['Vertices'].default_value = 8
            tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 5) * 200, -200 - (i // 5) * 200))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius, 1.75 * P["intensity"])
            _link(tree, pole.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(pole, "organic"); color_node(tr, "organic")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (300, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_bamboo")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_bamboo", build_aest_zen_bamboo_group,
    "Zen Bamboo", "Aesthetic effect pass (absorbed from monolith build_aest_zen_bamboo).",
    category="effects", role="modifier")


def build_aest_zen_petals_group(group_name="MEL_aest_zen_petals"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Floating cherry blossom petals (flat squashed spheres around the object)."""
        in_geom = _get_input_geom(tree)
        petal = _node(tree, 'GeometryNodeMeshUVSphere', (-500, -300))
        petal.inputs['Segments'].default_value = 6
        petal.inputs['Rings'].default_value    = 4
        petal.inputs['Radius'].default_value   = 0.1 * P["scale"]
        tr = _node(tree, 'GeometryNodeTransform', (-250, -300))
        tr.inputs['Scale'].default_value = (1.0, 1.0, 0.25)
        _link(tree, petal.outputs['Mesh'], tr.inputs['Geometry'])
        color_node(petal, "organic"); color_node(tr, "organic")
        # Create a cloud-like point set around the bbox using a larger ico sphere
        cloud = _node(tree, 'GeometryNodeMeshIcoSphere', (-500, 200))
        cloud.inputs['Radius'].default_value = 2.5 * P["scale"]
        cloud.inputs['Subdivisions'].default_value = max(2, P["layers"] + 1)
        # Use cloud verts as positions
        pts_from_mesh = _safe_node(tree, 'GeometryNodeMeshToPoints', (-200, 200))
        if pts_from_mesh:
            _link(tree, cloud.outputs['Mesh'], pts_from_mesh.inputs['Mesh'])
            inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (100, 200))
            if inst:
                _link(tree, pts_from_mesh.outputs['Points'], inst.inputs['Points'])
                _link(tree, tr.outputs['Geometry'],          inst.inputs['Instance'])
                real = _safe_node(tree, 'GeometryNodeRealizeInstances', (400, 200))
                if real:
                    _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
                    color_node(inst, "organic"); color_node(real, "organic")
                    return _join_with_input(tree, in_geom, real.outputs['Geometry'])
        return in_geom


    # ---- * SPIRITUAL ------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_petals")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_petals", build_aest_zen_petals_group,
    "Zen Petals", "Aesthetic effect pass (absorbed from monolith build_aest_zen_petals).",
    category="effects", role="modifier")


def build_aest_spi_aura_group(group_name="MEL_aest_spi_aura"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Iridescent outer shell offset along normals."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(2, P["layers"])
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -200))
        scale_n = _node(tree, 'ShaderNodeVectorMath', (250, -200))
        scale_n.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], scale_n.inputs[0])
        scale_n.inputs['Scale'].default_value = P["intensity"] * 0.4
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (500, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "input")
            return _join_with_input(tree, in_geom, set_pos.outputs['Geometry'])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_aura")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_aura", build_aest_spi_aura_group,
    "Spi Aura", "Aesthetic effect pass (absorbed from monolith build_aest_spi_aura).",
    category="effects", role="modifier")


def build_aest_spi_mandala_group(group_name="MEL_aest_spi_mandala"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Radial mandala flat shape beneath the object."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        rings = max(2, min(6, P["layers"] + 2))
        for ring_i in range(rings):
            n_petals = 6 + ring_i * 4
            ring_r = (ring_i + 1) * 0.6 * P["scale"]
            for i in range(n_petals):
                ang = (i / n_petals) * 6.283185
                petal = _node(tree, 'GeometryNodeMeshUVSphere', (-400 + (i % 4) * 200, -200 - ring_i * 250 - (i // 4) * 200))
                petal.inputs['Segments'].default_value = 6
                petal.inputs['Rings'].default_value    = 4
                petal.inputs['Radius'].default_value   = 0.1 * P["scale"]
                tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 4) * 200, -200 - ring_i * 250 - (i // 4) * 200))
                tr.inputs['Translation'].default_value = (math.cos(ang) * ring_r, math.sin(ang) * ring_r, -0.05)
                tr.inputs['Scale'].default_value = (1.0, 1.0, 0.15)
                _link(tree, petal.outputs['Mesh'], tr.inputs['Geometry'])
                color_node(petal, "ornament"); color_node(tr, "ornament")
                pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (300, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_mandala")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_mandala", build_aest_spi_mandala_group,
    "Spi Mandala", "Aesthetic effect pass (absorbed from monolith build_aest_spi_mandala).",
    category="effects", role="modifier")


def build_aest_spi_chakra_group(group_name="MEL_aest_spi_chakra"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Seven floating chakra orbs in vertical alignment."""
        in_geom = _get_input_geom(tree)
        pieces = []
        base_h = 2.5 * P["intensity"]
        for i in range(7):
            orb = _node(tree, 'GeometryNodeMeshUVSphere', (-400, -200 - i * 120))
            orb.inputs['Segments'].default_value = 12
            orb.inputs['Rings'].default_value    = 8
            orb.inputs['Radius'].default_value   = 0.18 * P["scale"]
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - i * 120))
            tr.inputs['Translation'].default_value = (0, 0, base_h + i * 0.55 * P["scale"])
            _link(tree, orb.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(orb, "ornament"); color_node(tr, "ornament")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_chakra")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_chakra", build_aest_spi_chakra_group,
    "Spi Chakra", "Aesthetic effect pass (absorbed from monolith build_aest_spi_chakra).",
    category="effects", role="modifier")


def build_aest_spi_beam_group(group_name="MEL_aest_spi_beam"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Vertical pillar of light above the object."""
        in_geom = _get_input_geom(tree)
        beam = _node(tree, 'GeometryNodeMeshCylinder', (-400, -200))
        beam.inputs['Radius'].default_value = 0.4 * P["scale"]
        beam.inputs['Depth'].default_value  = 8.0 * P["intensity"]
        beam.inputs['Vertices'].default_value = 16
        tr = _node(tree, 'GeometryNodeTransform', (-150, -200))
        tr.inputs['Translation'].default_value = (0, 0, 4.0 * P["intensity"])
        _link(tree, beam.outputs['Mesh'], tr.inputs['Geometry'])
        color_node(beam, "input"); color_node(tr, "input")
        return _join_with_input(tree, in_geom, tr.outputs['Geometry'])


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_beam")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_beam", build_aest_spi_beam_group,
    "Spi Beam", "Aesthetic effect pass (absorbed from monolith build_aest_spi_beam).",
    category="effects", role="modifier")


def build_aest_spi_ring_group(group_name="MEL_aest_spi_ring"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Orbiting sacred ring(s) around the object."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n_rings = max(1, min(4, P["layers"]))
        for r_i in range(n_rings):
            torus = _safe_node(tree, 'GeometryNodeMeshTorus', (-400, -200 - r_i * 250))
            if torus is None:
                continue
            try:
                torus.inputs['Major Radius'].default_value = (1.5 + r_i * 0.3) * P["scale"]
                torus.inputs['Minor Radius'].default_value = 0.05 * P["scale"]
                torus.inputs['Major Segments'].default_value = 32
                torus.inputs['Minor Segments'].default_value = 6
            except Exception:
                pass
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - r_i * 250))
            ang = r_i * 0.7
            tr.inputs['Rotation'].default_value = (ang, 0, ang * 0.5)
            tr.inputs['Translation'].default_value = (0, 0, 1.0 * P["intensity"])
            _link(tree, torus.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(torus, "ornament"); color_node(tr, "ornament")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_ring")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_ring", build_aest_spi_ring_group,
    "Spi Ring", "Aesthetic effect pass (absorbed from monolith build_aest_spi_ring).",
    category="effects", role="modifier")


def build_aest_spi_astral_group(group_name="MEL_aest_spi_astral"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Ghosted duplicate offset upward."""
        in_geom = _get_input_geom(tree)
        tr = _node(tree, 'GeometryNodeTransform', (0, -200))
        tr.inputs['Translation'].default_value = (0, 0, 3.0 * P["intensity"])
        tr.inputs['Scale'].default_value = (0.95, 0.95, 0.95)
        if in_geom:
            _link(tree, in_geom, tr.inputs['Geometry'])
        color_node(tr, "ornament")
        return _join_with_input(tree, in_geom, tr.outputs['Geometry'])


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_astral")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_astral", build_aest_spi_astral_group,
    "Spi Astral", "Aesthetic effect pass (absorbed from monolith build_aest_spi_astral).",
    category="effects", role="modifier")


def build_aest_spi_eye_group(group_name="MEL_aest_spi_eye"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Single third-eye on the front face: torus + sphere."""
        in_geom = _get_input_geom(tree)
        iris = _node(tree, 'GeometryNodeMeshUVSphere', (-500, -200))
        iris.inputs['Segments'].default_value = 16
        iris.inputs['Rings'].default_value    = 10
        iris.inputs['Radius'].default_value   = 0.25 * P["scale"]
        eye_ring = _safe_node(tree, 'GeometryNodeMeshTorus', (-500, -400))
        if eye_ring:
            try:
                eye_ring.inputs['Major Radius'].default_value = 0.3 * P["scale"]
                eye_ring.inputs['Minor Radius'].default_value = 0.05 * P["scale"]
            except Exception:
                pass
        j = _node(tree, 'GeometryNodeJoinGeometry', (-250, -300))
        _link(tree, iris.outputs['Mesh'], j.inputs['Geometry'])
        if eye_ring:
            _link(tree, eye_ring.outputs['Mesh'], j.inputs['Geometry'])
        tr = _node(tree, 'GeometryNodeTransform', (0, -300))
        tr.inputs['Translation'].default_value = (0, -1.2 * P["scale"], 1.5 * P["intensity"])
        tr.inputs['Rotation'].default_value = (1.5708, 0, 0)
        _link(tree, j.outputs['Geometry'], tr.inputs['Geometry'])
        color_node(iris, "ornament"); color_node(j, "ornament"); color_node(tr, "ornament")
        return _join_with_input(tree, in_geom, tr.outputs['Geometry'])


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_eye")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_eye", build_aest_spi_eye_group,
    "Spi Eye", "Aesthetic effect pass (absorbed from monolith build_aest_spi_eye).",
    category="effects", role="modifier")


def build_aest_spi_lotus_group(group_name="MEL_aest_spi_lotus"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Lotus bloom petals around the base."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n_petals = max(6, int(P["density"] * 14))
        rings = max(1, min(3, P["layers"]))
        for ring_i in range(rings):
            r = 0.5 + ring_i * 0.4
            for i in range(n_petals):
                ang = (i / n_petals) * 6.283185 + ring_i * 0.2
                petal = _safe_node(tree, 'GeometryNodeMeshCone', (-400 + (i % 6) * 150, -200 - ring_i * 250 - (i // 6) * 200))
                if petal is None:
                    continue
                petal.inputs['Radius Bottom'].default_value = 0.15 * P["scale"]
                petal.inputs['Radius Top'].default_value    = 0.02 * P["scale"]
                petal.inputs['Depth'].default_value         = 0.5 * P["scale"]
                petal.inputs['Vertices'].default_value      = 24
                tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 6) * 150, -200 - ring_i * 250 - (i // 6) * 200))
                x = math.cos(ang) * r * P["scale"]
                y = math.sin(ang) * r * P["scale"]
                tr.inputs['Translation'].default_value = (x, y, ring_i * 0.15)
                tilt = 0.6 + ring_i * 0.15
                tr.inputs['Rotation'].default_value = (math.cos(ang) * tilt, math.sin(ang) * tilt, 0)
                _link(tree, petal.outputs['Mesh'], tr.inputs['Geometry'])
                color_node(petal, "organic"); color_node(tr, "organic")
                pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (300, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    # ======================================================================
    # v2.16 - additional procedurally-rich aesthetic effects
    # Each one uses noise / voronoi / fields / curve sweeps for variation.
    # ======================================================================

    def _noise_scale_for(P, base):
        return max(0.5, base * P["density"])


    # ---- * GOTHIC - extra ------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_lotus")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_lotus", build_aest_spi_lotus_group,
    "Spi Lotus", "Aesthetic effect pass (absorbed from monolith build_aest_spi_lotus).",
    category="effects", role="modifier")


def build_aest_goth_lattice_group(group_name="MEL_aest_goth_lattice"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Fractal Gothic lattice via Wireframe + Subdivide stack."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        wire = _safe_node(tree, 'GeometryNodeWireframe', (300, 0))
        if wire:
            try:
                wire.inputs['Radius'].default_value = 0.03 * P["scale"]
            except Exception:
                pass
            _link(tree, subd.outputs['Mesh'], wire.inputs['Mesh'])
            color_node(wire, "tracery")
        # Distribute small finial spheres on lattice nodes (vertices)
        finial = _node(tree, 'GeometryNodeMeshIcoSphere', (300, -300))
        finial.inputs['Radius'].default_value = 0.04 * P["scale"]
        finial.inputs['Subdivisions'].default_value = 1
        # Convert subd mesh to points, instance finials at vertices
        m2p = _safe_node(tree, 'GeometryNodeMeshToPoints', (600, -300))
        if m2p:
            _link(tree, subd.outputs['Mesh'], m2p.inputs['Mesh'])
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (900, -300))
        if inst and m2p:
            _link(tree, m2p.outputs['Points'], inst.inputs['Points'])
            _link(tree, finial.outputs['Mesh'], inst.inputs['Instance'])
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (1100, -300))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (1400, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        if wire:
            try:
                _link(tree, wire.outputs.get('Curve') or wire.outputs[0], join.inputs['Geometry'])
            except Exception:
                pass
        if real:
            _link(tree, real.outputs['Geometry'], join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_lattice")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_lattice", build_aest_goth_lattice_group,
    "Goth Lattice", "Aesthetic effect pass (absorbed from monolith build_aest_goth_lattice).",
    category="effects", role="modifier")


def build_aest_goth_niches_group(group_name="MEL_aest_goth_niches"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Voronoi-masked extruded arched niches: small recessed pockets."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        # Voronoi field
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -250))
        vor = _safe_node(tree, 'ShaderNodeTexVoronoi', (250, -250))
        if vor:
            vor.voronoi_dimensions = '3D'
            vor.feature = 'DISTANCE_TO_EDGE'
            vor.inputs['Scale'].default_value = _noise_scale_for(P, 1.5)
            _link(tree, pos.outputs['Position'], vor.inputs['Vector'])
            color_node(vor, "noise")
        # Mask: select faces where voronoi distance < threshold -> push inward
        less = _node(tree, 'ShaderNodeMath', (500, -250))
        less.operation = 'LESS_THAN'
        if vor:
            _link(tree, vor.outputs['Distance'], less.inputs[0])
        less.inputs[1].default_value = 0.12 * (1.0 / max(0.3, P["density"]))
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -500))
        scale_n = _node(tree, 'ShaderNodeVectorMath', (300, -500))
        scale_n.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], scale_n.inputs[0])
        mult = _node(tree, 'ShaderNodeMath', (500, -500))
        mult.operation = 'MULTIPLY'
        _link(tree, less.outputs['Value'], mult.inputs[0])
        mult.inputs[1].default_value = -P["intensity"] * 0.4
        _link(tree, mult.outputs['Value'], scale_n.inputs['Scale'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (800, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "gothic")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_niches")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_niches", build_aest_goth_niches_group,
    "Goth Niches", "Aesthetic effect pass (absorbed from monolith build_aest_goth_niches).",
    category="effects", role="modifier")


def build_aest_goth_fans_group(group_name="MEL_aest_goth_fans"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Radial fan ribs sprouting from the base center."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n_fans = max(4, int(P["density"] * 6))
        n_ribs_per_fan = max(3, int(P["layers"] + 3))
        for f_i in range(n_fans):
            base_ang = (f_i / n_fans) * 6.283185
            for r_i in range(n_ribs_per_fan):
                rib_ang = base_ang + (r_i - n_ribs_per_fan / 2) * 0.08
                length = 2.5 * P["intensity"]
                cyl = _node(tree, 'GeometryNodeMeshCylinder',
                            (-400 + (f_i % 4) * 200, -200 - (f_i // 4) * 250 - r_i * 80))
                cyl.inputs['Radius'].default_value = 0.025 * P["scale"]
                cyl.inputs['Depth'].default_value  = length
                cyl.inputs['Vertices'].default_value = 6
                tr = _node(tree, 'GeometryNodeTransform',
                           (-180 + (f_i % 4) * 200, -200 - (f_i // 4) * 250 - r_i * 80))
                # tilt outward in XY plane
                dx = math.cos(rib_ang) * length * 0.5
                dy = math.sin(rib_ang) * length * 0.5
                tr.inputs['Translation'].default_value = (dx, dy, length * 0.5)
                tr.inputs['Rotation'].default_value = (math.sin(rib_ang) * 0.4, -math.cos(rib_ang) * 0.4, 0)
                _link(tree, cyl.outputs['Mesh'], tr.inputs['Geometry'])
                color_node(cyl, "gothic"); color_node(tr, "gothic")
                pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_fans")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_fans", build_aest_goth_fans_group,
    "Goth Fans", "Aesthetic effect pass (absorbed from monolith build_aest_goth_fans).",
    category="effects", role="modifier")


def build_aest_goth_finials_group(group_name="MEL_aest_goth_finials"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Pointed Gothic finials clustered at upward-facing surfaces (top mask)."""
        in_geom = _get_input_geom(tree)
        # Compound finial: short cylinder + tall narrow cone
        base = _node(tree, 'GeometryNodeMeshCylinder', (-500, -300))
        base.inputs['Radius'].default_value = 0.08 * P["scale"]
        base.inputs['Depth'].default_value  = 0.2 * P["scale"]
        base.inputs['Vertices'].default_value = 8
        spire = _safe_node(tree, 'GeometryNodeMeshCone', (-500, -500))
        if spire:
            spire.inputs['Radius Bottom'].default_value = 0.08 * P["scale"]
            spire.inputs['Radius Top'].default_value    = 0.0
            spire.inputs['Depth'].default_value         = 0.5 * P["scale"] * P["intensity"]
            spire.inputs['Vertices'].default_value      = 24
            tr_s = _node(tree, 'GeometryNodeTransform', (-300, -500))
            tr_s.inputs['Translation'].default_value = (0, 0, 0.35 * P["scale"] * P["intensity"])
            _link(tree, spire.outputs['Mesh'], tr_s.inputs['Geometry'])
            color_node(spire, "gothic"); color_node(tr_s, "gothic")
        j = _node(tree, 'GeometryNodeJoinGeometry', (-100, -400))
        _link(tree, base.outputs['Mesh'], j.inputs['Geometry'])
        if spire:
            _link(tree, tr_s.outputs['Geometry'], j.inputs['Geometry'])
        color_node(base, "gothic"); color_node(j, "gothic")
        # Distribute on faces (will sit on every face - for top-bias add manual filter)
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (100, 0))
        if pts and in_geom:
            pts.distribute_method = 'POISSON'
            pts.inputs['Distance Min'].default_value = 0.5 / max(0.1, P["density"])
            pts.inputs['Density Max'].default_value  = P["density"] * 2.0
            pts.inputs['Seed'].default_value         = P["seed"]
            _link(tree, in_geom, pts.inputs['Mesh'])
            color_node(pts, "input")
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (400, 0))
        if inst and pts:
            _link(tree, pts.outputs['Points'], inst.inputs['Points'])
            _link(tree, j.outputs['Geometry'], inst.inputs['Instance'])
            try:
                _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
            except Exception:
                pass
            color_node(inst, "gothic")
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (700, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, real.outputs['Geometry'] if real else None)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_finials")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_finials", build_aest_goth_finials_group,
    "Goth Finials", "Aesthetic effect pass (absorbed from monolith build_aest_goth_finials).",
    category="effects", role="modifier")


def build_aest_goth_leadwork_group(group_name="MEL_aest_goth_leadwork"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Stained-glass lead lines: wireframe on voronoi-extruded cells."""
        in_geom = _get_input_geom(tree)
        # Build a subdivided base
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 2)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        # Voronoi displace creating cell terraces
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -250))
        vor = _safe_node(tree, 'ShaderNodeTexVoronoi', (250, -250))
        if vor:
            vor.voronoi_dimensions = '3D'
            vor.feature = 'F1'
            vor.inputs['Scale'].default_value = _noise_scale_for(P, 2.0)
            _link(tree, pos.outputs['Position'], vor.inputs['Vector'])
            color_node(vor, "noise")
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -450))
        scale_n = _node(tree, 'ShaderNodeVectorMath', (300, -450))
        scale_n.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], scale_n.inputs[0])
        if vor:
            mult = _node(tree, 'ShaderNodeMath', (500, -450))
            mult.operation = 'MULTIPLY'
            _link(tree, vor.outputs['Distance'], mult.inputs[0])
            mult.inputs[1].default_value = P["intensity"] * 0.15
            _link(tree, mult.outputs['Value'], scale_n.inputs['Scale'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (800, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "gothic")
            # Add wireframe on top for lead lines
            wire = _safe_node(tree, 'GeometryNodeWireframe', (1100, 0))
            if wire:
                try:
                    wire.inputs['Radius'].default_value = 0.025 * P["scale"]
                except Exception:
                    pass
                _link(tree, set_pos.outputs['Geometry'], wire.inputs['Mesh'])
                color_node(wire, "tracery")
                join = _node(tree, 'GeometryNodeJoinGeometry', (1400, 0))
                _link(tree, set_pos.outputs['Geometry'], join.inputs['Geometry'])
                try:
                    _link(tree, wire.outputs.get('Curve') or wire.outputs[0], join.inputs['Geometry'])
                except Exception:
                    pass
                return join.outputs['Geometry']
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_leadwork")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_leadwork", build_aest_goth_leadwork_group,
    "Goth Leadwork", "Aesthetic effect pass (absorbed from monolith build_aest_goth_leadwork).",
    category="effects", role="modifier")


def build_aest_goth_spires_group(group_name="MEL_aest_goth_spires"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Procedural spire forest growing from upward-facing peaks."""
        in_geom = _get_input_geom(tree)
        # Tall thin spire = cylinder + cone tip
        pole = _node(tree, 'GeometryNodeMeshCylinder', (-500, -300))
        pole.inputs['Radius'].default_value = 0.06 * P["scale"]
        pole.inputs['Depth'].default_value  = 1.0 * P["intensity"]
        pole.inputs['Vertices'].default_value = 6
        tip = _safe_node(tree, 'GeometryNodeMeshCone', (-500, -500))
        if tip:
            tip.inputs['Radius Bottom'].default_value = 0.06 * P["scale"]
            tip.inputs['Radius Top'].default_value    = 0.0
            tip.inputs['Depth'].default_value         = 0.4 * P["scale"]
            tip.inputs['Vertices'].default_value      = 24
            tip_tr = _node(tree, 'GeometryNodeTransform', (-300, -500))
            tip_tr.inputs['Translation'].default_value = (0, 0, 0.7 * P["intensity"])
            _link(tree, tip.outputs['Mesh'], tip_tr.inputs['Geometry'])
            color_node(tip, "gothic"); color_node(tip_tr, "gothic")
        pole_tr = _node(tree, 'GeometryNodeTransform', (-300, -300))
        pole_tr.inputs['Translation'].default_value = (0, 0, 0.5 * P["intensity"])
        _link(tree, pole.outputs['Mesh'], pole_tr.inputs['Geometry'])
        color_node(pole, "gothic"); color_node(pole_tr, "gothic")
        j = _node(tree, 'GeometryNodeJoinGeometry', (-100, -400))
        _link(tree, pole_tr.outputs['Geometry'], j.inputs['Geometry'])
        if tip:
            _link(tree, tip_tr.outputs['Geometry'], j.inputs['Geometry'])
        color_node(j, "gothic")
        real = _instance_on_surface(tree, in_geom, j.outputs['Geometry'],
                                    P["density"] * 0.5, P["seed"],
                                    rand_scale=0.6, x_off=200, label="gothic")
        return _join_with_input(tree, in_geom, real)


    # ---- * VAPORWAVE - extra ---------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_spires")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_spires", build_aest_goth_spires_group,
    "Goth Spires", "Aesthetic effect pass (absorbed from monolith build_aest_goth_spires).",
    category="effects", role="modifier")


def build_aest_vap_slices_group(group_name="MEL_aest_vap_slices"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Horizontal Z-band noise-offset slices: VHS-tracking glitch."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -250))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (200, -250))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        # Stepped Z: floor(z * density)
        mul_z = _node(tree, 'ShaderNodeMath', (400, -250))
        mul_z.operation = 'MULTIPLY'
        _link(tree, sep.outputs['Z'], mul_z.inputs[0])
        mul_z.inputs[1].default_value = P["density"] * 4.0
        flr = _node(tree, 'ShaderNodeMath', (600, -250))
        flr.operation = 'FLOOR'
        _link(tree, mul_z.outputs['Value'], flr.inputs[0])
        # Pseudo-random offset from floor
        noise = _safe_node(tree, 'ShaderNodeTexNoise', (800, -250))
        if noise:
            noise.inputs['Scale'].default_value = 2.0
            nb = _node(tree, 'ShaderNodeCombineXYZ', (800, -450))
            _link(tree, flr.outputs['Value'], nb.inputs['X'])
            _link(tree, nb.outputs['Vector'], noise.inputs['Vector'])
            color_node(noise, "noise")
        sub_v = _node(tree, 'ShaderNodeCombineXYZ', (1100, -250))
        if noise:
            mult_x = _node(tree, 'ShaderNodeMath', (1000, -350))
            mult_x.operation = 'MULTIPLY'
            _link(tree, noise.outputs['Fac'], mult_x.inputs[0])
            mult_x.inputs[1].default_value = P["intensity"] * 0.4
            _link(tree, mult_x.outputs['Value'], sub_v.inputs['X'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (1400, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, sub_v.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "input")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_slices")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_slices", build_aest_vap_slices_group,
    "Vap Slices", "Aesthetic effect pass (absorbed from monolith build_aest_vap_slices).",
    category="effects", role="modifier")


def build_aest_vap_scanlines_group(group_name="MEL_aest_vap_scanlines"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Raised horizontal scanlines via sine on Z."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 2)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -250))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (200, -250))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        mul = _node(tree, 'ShaderNodeMath', (400, -250))
        mul.operation = 'MULTIPLY'
        _link(tree, sep.outputs['Z'], mul.inputs[0])
        mul.inputs[1].default_value = P["density"] * 15.0
        sn = _node(tree, 'ShaderNodeMath', (600, -250))
        sn.operation = 'SINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        # Step-clamp positive only
        clip = _node(tree, 'ShaderNodeMath', (800, -250))
        clip.operation = 'MAXIMUM'
        _link(tree, sn.outputs['Value'], clip.inputs[0])
        clip.inputs[1].default_value = 0.0
        amp = _node(tree, 'ShaderNodeMath', (1000, -250))
        amp.operation = 'MULTIPLY'
        _link(tree, clip.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = P["intensity"] * 0.05
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -500))
        scale_n = _node(tree, 'ShaderNodeVectorMath', (1200, -300))
        scale_n.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], scale_n.inputs[0])
        _link(tree, amp.outputs['Value'], scale_n.inputs['Scale'])
        set_pos = _safe_node(tree, 'GeometryNodeSetPosition', (1500, 0))
        if set_pos:
            _link(tree, subd.outputs['Mesh'], set_pos.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], set_pos.inputs['Offset'])
            color_node(set_pos, "input")
            return set_pos.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_scanlines")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_scanlines", build_aest_vap_scanlines_group,
    "Vap Scanlines", "Aesthetic effect pass (absorbed from monolith build_aest_vap_scanlines).",
    category="effects", role="modifier")


def build_aest_vap_busts_group(group_name="MEL_aest_vap_busts"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Classical marble busts (sphere + tapered cylinder) around the base."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(3, int(P["density"] * 6))
        radius = 2.2 * P["scale"]
        for i in range(n):
            ang = (i / n) * 6.283185
            # head
            head = _node(tree, 'GeometryNodeMeshUVSphere', (-400, -200 - i * 100))
            head.inputs['Radius'].default_value = 0.25 * P["scale"]
            head.inputs['Segments'].default_value = 12
            head.inputs['Rings'].default_value    = 8
            h_tr = _node(tree, 'GeometryNodeTransform', (-200, -200 - i * 100))
            h_tr.inputs['Translation'].default_value = (0, 0, 1.0 * P["intensity"])
            _link(tree, head.outputs['Mesh'], h_tr.inputs['Geometry'])
            # plinth
            plinth = _node(tree, 'GeometryNodeMeshCylinder', (-400, -260 - i * 100))
            plinth.inputs['Radius'].default_value = 0.18 * P["scale"]
            plinth.inputs['Depth'].default_value  = 0.7 * P["intensity"]
            plinth.inputs['Vertices'].default_value = 10
            p_tr = _node(tree, 'GeometryNodeTransform', (-200, -260 - i * 100))
            p_tr.inputs['Translation'].default_value = (0, 0, 0.35 * P["intensity"])
            _link(tree, plinth.outputs['Mesh'], p_tr.inputs['Geometry'])
            j = _node(tree, 'GeometryNodeJoinGeometry', (0, -230 - i * 100))
            _link(tree, h_tr.outputs['Geometry'], j.inputs['Geometry'])
            _link(tree, p_tr.outputs['Geometry'], j.inputs['Geometry'])
            # place around ring
            tr = _node(tree, 'GeometryNodeTransform', (200, -230 - i * 100))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius, 0.0)
            tr.inputs['Rotation'].default_value = (0, 0, ang + 1.5708)
            _link(tree, j.outputs['Geometry'], tr.inputs['Geometry'])
            color_node(head, "tower"); color_node(plinth, "tower"); color_node(j, "tower"); color_node(tr, "tower")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (500, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_busts")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_busts", build_aest_vap_busts_group,
    "Vap Busts", "Aesthetic effect pass (absorbed from monolith build_aest_vap_busts).",
    category="effects", role="modifier")


def build_aest_vap_slabs_group(group_name="MEL_aest_vap_slabs"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Floating tilted holographic slabs orbiting the mesh."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(4, int(P["density"] * 10))
        for i in range(n):
            ang = (i / n) * 6.283185
            radius = (1.8 + (i % 3) * 0.5) * P["scale"]
            height = (i % 4) * 0.6 + 0.4
            slab = _node(tree, 'GeometryNodeMeshCube', (-400 + (i % 4) * 200, -200 - (i // 4) * 200))
            slab.inputs['Size'].default_value = (0.9 * P["scale"], 0.04 * P["scale"], 0.55 * P["scale"])
            tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 4) * 200, -200 - (i // 4) * 200))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius,
                                                       height * P["intensity"])
            tr.inputs['Rotation'].default_value = (0.15 * math.sin(i), 0.15 * math.cos(i), ang)
            _link(tree, slab.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(slab, "input"); color_node(tr, "input")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_slabs")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_slabs", build_aest_vap_slabs_group,
    "Vap Slabs", "Aesthetic effect pass (absorbed from monolith build_aest_vap_slabs).",
    category="effects", role="modifier")


def build_aest_vap_sun_group(group_name="MEL_aest_vap_sun"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Banded retro sun: half-disc with concentric ring bands behind."""
        in_geom = _get_input_geom(tree)
        pieces = []
        rings = max(3, min(8, P["layers"] + 4))
        for r_i in range(rings):
            r = (r_i + 1) * 0.5 * P["scale"]
            tor = _safe_node(tree, 'GeometryNodeMeshTorus', (-400, -200 - r_i * 200))
            if tor is None:
                continue
            try:
                tor.inputs['Major Radius'].default_value = r
                tor.inputs['Minor Radius'].default_value = 0.06 * P["scale"]
                tor.inputs['Major Segments'].default_value = 32
                tor.inputs['Minor Segments'].default_value = 6
            except Exception:
                pass
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - r_i * 200))
            tr.inputs['Rotation'].default_value = (1.5708, 0, 0)
            tr.inputs['Translation'].default_value = (0, -2.0 * P["scale"], 0.5 + r * 0.5)
            _link(tree, tor.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(tor, "input"); color_node(tr, "input")
            pieces.append(tr.outputs['Geometry'])
        # central solid disc
        disc = _safe_node(tree, 'GeometryNodeMeshCircle', (-400, 0))
        if disc:
            try:
                disc.inputs['Radius'].default_value = 0.45 * P["scale"]
                disc.fill_type = 'NGON'
            except Exception:
                pass
            d_tr = _node(tree, 'GeometryNodeTransform', (-150, 0))
            d_tr.inputs['Rotation'].default_value = (1.5708, 0, 0)
            d_tr.inputs['Translation'].default_value = (0, -1.99 * P["scale"], 1.5)
            _link(tree, disc.outputs['Mesh'], d_tr.inputs['Geometry'])
            color_node(disc, "input"); color_node(d_tr, "input")
            pieces.append(d_tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_sun")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_sun", build_aest_vap_sun_group,
    "Vap Sun", "Aesthetic effect pass (absorbed from monolith build_aest_vap_sun).",
    category="effects", role="modifier")


def build_aest_vap_neon_wrap_group(group_name="MEL_aest_vap_neon_wrap"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Neon tube ribbon: helix curve swept with a thin cylinder."""
        in_geom = _get_input_geom(tree)
        spiral = _safe_node(tree, 'GeometryNodeCurveSpiral', (-400, 0))
        if spiral:
            try:
                spiral.inputs['Resolution'].default_value = 64
                spiral.inputs['Rotations'].default_value  = 3.0 + P["density"]
                spiral.inputs['Start Radius'].default_value = 1.5 * P["scale"]
                spiral.inputs['End Radius'].default_value   = 1.5 * P["scale"]
                spiral.inputs['Height'].default_value       = 3.0 * P["intensity"]
            except Exception:
                pass
            # Profile circle
            circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-400, -300))
            if circ:
                try:
                    circ.inputs['Radius'].default_value = 0.04 * P["scale"]
                    circ.inputs['Resolution'].default_value = 8
                except Exception:
                    pass
                c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', (-100, -150))
                if c2m:
                    _link(tree, spiral.outputs['Curve'], c2m.inputs['Curve'])
                    _link(tree, circ.outputs['Curve'],   c2m.inputs['Profile Curve'])
                    color_node(c2m, "input")
                    return _join_with_input(tree, in_geom, c2m.outputs['Mesh'])
        return in_geom


    # ---- * ZEN - extra ---------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_neon_wrap")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_neon_wrap", build_aest_vap_neon_wrap_group,
    "Vap Neon Wrap", "Aesthetic effect pass (absorbed from monolith build_aest_vap_neon_wrap).",
    category="effects", role="modifier")


def build_aest_zen_orbit_group(group_name="MEL_aest_zen_orbit"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Paper lanterns orbiting in concentric rings."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        rings = max(1, min(3, P["layers"]))
        for r_i in range(rings):
            n = max(4, int(P["density"] * 6))
            radius = (1.5 + r_i * 0.8) * P["scale"]
            z = 1.5 * P["intensity"] + r_i * 0.7
            for i in range(n):
                ang = (i / n) * 6.283185 + r_i * 0.3
                # lantern body
                body = _node(tree, 'GeometryNodeMeshUVSphere', (-400 + (i % 4) * 180, -200 - r_i * 400 - (i // 4) * 200))
                body.inputs['Radius'].default_value = 0.18 * P["scale"]
                body.inputs['Segments'].default_value = 12
                body.inputs['Rings'].default_value    = 8
                tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 4) * 180, -200 - r_i * 400 - (i // 4) * 200))
                tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius, z)
                tr.inputs['Scale'].default_value = (1.0, 1.0, 1.25)
                _link(tree, body.outputs['Mesh'], tr.inputs['Geometry'])
                color_node(body, "lantern"); color_node(tr, "lantern")
                pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_orbit")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_orbit", build_aest_zen_orbit_group,
    "Zen Orbit", "Aesthetic effect pass (absorbed from monolith build_aest_zen_orbit).",
    category="effects", role="modifier")


def build_aest_zen_smoke_group(group_name="MEL_aest_zen_smoke"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Helical incense smoke trails rising from base - sweep cylinder along spiral."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(2, int(P["density"] * 4))
        for i in range(n):
            ang_off = (i / n) * 6.283185
            sp = _safe_node(tree, 'GeometryNodeCurveSpiral', (-400, -200 - i * 250))
            if sp is None:
                continue
            try:
                sp.inputs['Resolution'].default_value = 48
                sp.inputs['Rotations'].default_value  = 2.5
                sp.inputs['Start Radius'].default_value = 0.05
                sp.inputs['End Radius'].default_value   = 0.4 * P["scale"]
                sp.inputs['Height'].default_value       = 3.5 * P["intensity"]
            except Exception:
                pass
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-400, -350 - i * 250))
            if prof:
                try:
                    prof.inputs['Radius'].default_value = 0.025 * P["scale"]
                    prof.inputs['Resolution'].default_value = 6
                except Exception:
                    pass
                c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', (-100, -250 - i * 250))
                if c2m:
                    _link(tree, sp.outputs['Curve'], c2m.inputs['Curve'])
                    _link(tree, prof.outputs['Curve'], c2m.inputs['Profile Curve'])
                    tr = _node(tree, 'GeometryNodeTransform', (150, -250 - i * 250))
                    tr.inputs['Translation'].default_value = (math.cos(ang_off) * 0.6, math.sin(ang_off) * 0.6, 0)
                    tr.inputs['Rotation'].default_value = (0, 0, ang_off)
                    _link(tree, c2m.outputs['Mesh'], tr.inputs['Geometry'])
                    color_node(c2m, "organic"); color_node(tr, "organic")
                    pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (500, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_smoke")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_smoke", build_aest_zen_smoke_group,
    "Zen Smoke", "Aesthetic effect pass (absorbed from monolith build_aest_zen_smoke).",
    category="effects", role="modifier")


def build_aest_zen_pond_group(group_name="MEL_aest_zen_pond"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Reflective pond disc + lily pads beneath the object."""
        in_geom = _get_input_geom(tree)
        pieces = []
        # Pond disc
        disc = _safe_node(tree, 'GeometryNodeMeshCircle', (-400, 0))
        if disc:
            try:
                disc.inputs['Radius'].default_value = 3.0 * P["scale"]
                disc.inputs['Vertices'].default_value = 48
                disc.fill_type = 'NGON'
            except Exception:
                pass
            tr = _node(tree, 'GeometryNodeTransform', (-150, 0))
            tr.inputs['Translation'].default_value = (0, 0, -0.05)
            _link(tree, disc.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(disc, "input"); color_node(tr, "input")
            pieces.append(tr.outputs['Geometry'])
        # Lily pads
        n = max(3, int(P["density"] * 5))
        import math
        for i in range(n):
            ang = (i / n) * 6.283185
            r = 1.5 * P["scale"]
            pad = _node(tree, 'GeometryNodeMeshUVSphere', (-400, -300 - i * 100))
            pad.inputs['Radius'].default_value = 0.3 * P["scale"]
            pad.inputs['Segments'].default_value = 8
            pad.inputs['Rings'].default_value    = 4
            tr_p = _node(tree, 'GeometryNodeTransform', (-150, -300 - i * 100))
            tr_p.inputs['Translation'].default_value = (math.cos(ang) * r, math.sin(ang) * r, 0.02)
            tr_p.inputs['Scale'].default_value = (1.0, 1.0, 0.08)
            _link(tree, pad.outputs['Mesh'], tr_p.inputs['Geometry'])
            color_node(pad, "organic"); color_node(tr_p, "organic")
            pieces.append(tr_p.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_pond")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_pond", build_aest_zen_pond_group,
    "Zen Pond", "Aesthetic effect pass (absorbed from monolith build_aest_zen_pond).",
    category="effects", role="modifier")


def build_aest_zen_terrace_group(group_name="MEL_aest_zen_terrace"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Stepped terraced rock layers around the bbox."""
        in_geom = _get_input_geom(tree)
        pieces = []
        layers = max(2, min(6, P["layers"] + 2))
        for L in range(layers):
            r = (1.5 + L * 0.6) * P["scale"]
            h = 0.25 * P["intensity"]
            disc = _safe_node(tree, 'GeometryNodeMeshCylinder', (-400, -200 - L * 200))
            if disc is None:
                continue
            disc.inputs['Radius'].default_value = r
            disc.inputs['Depth'].default_value  = h
            disc.inputs['Vertices'].default_value = max(12, int(16 + L * 4))
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - L * 200))
            tr.inputs['Translation'].default_value = (0, 0, -h * (L + 0.5))
            _link(tree, disc.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(disc, "tower"); color_node(tr, "tower")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_terrace")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_terrace", build_aest_zen_terrace_group,
    "Zen Terrace", "Aesthetic effect pass (absorbed from monolith build_aest_zen_terrace).",
    category="effects", role="modifier")


def build_aest_zen_ginkgo_group(group_name="MEL_aest_zen_ginkgo"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Ginkgo leaves drifting in noise field (flat fan-shaped instances)."""
        in_geom = _get_input_geom(tree)
        # Simple leaf = squished + tilted cone
        leaf = _safe_node(tree, 'GeometryNodeMeshCone', (-500, -300))
        if leaf:
            leaf.inputs['Radius Bottom'].default_value = 0.18 * P["scale"]
            leaf.inputs['Radius Top'].default_value    = 0.02 * P["scale"]
            leaf.inputs['Depth'].default_value         = 0.06 * P["scale"]
            leaf.inputs['Vertices'].default_value      = 24
            tr_l = _node(tree, 'GeometryNodeTransform', (-300, -300))
            tr_l.inputs['Rotation'].default_value = (1.5708, 0, 0)
            _link(tree, leaf.outputs['Mesh'], tr_l.inputs['Geometry'])
            color_node(leaf, "organic"); color_node(tr_l, "organic")
        # Point cloud - use icosphere as scattered points
        cloud = _node(tree, 'GeometryNodeMeshIcoSphere', (-500, 200))
        cloud.inputs['Radius'].default_value = 2.5 * P["scale"]
        cloud.inputs['Subdivisions'].default_value = max(2, P["layers"] + 1)
        m2p = _safe_node(tree, 'GeometryNodeMeshToPoints', (-200, 200))
        if m2p:
            _link(tree, cloud.outputs['Mesh'], m2p.inputs['Mesh'])
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (100, 200))
        if inst and m2p and leaf:
            _link(tree, m2p.outputs['Points'], inst.inputs['Points'])
            _link(tree, tr_l.outputs['Geometry'], inst.inputs['Instance'])
            # Random per-leaf rotation
            rrot = _safe_node(tree, 'FunctionNodeRandomValue', (100, 0))
            if rrot:
                rrot.data_type = 'FLOAT_VECTOR'
                try:
                    rrot.inputs[0].default_value = (-1.5, -1.5, -3.14)  # min
                    rrot.inputs[1].default_value = (1.5, 1.5, 3.14)    # max
                    _link(tree, rrot.outputs['Value'], inst.inputs['Rotation'])
                except Exception:
                    pass
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (400, 200))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
            return _join_with_input(tree, in_geom, real.outputs['Geometry'])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_ginkgo")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_ginkgo", build_aest_zen_ginkgo_group,
    "Zen Ginkgo", "Aesthetic effect pass (absorbed from monolith build_aest_zen_ginkgo).",
    category="effects", role="modifier")


def build_aest_zen_runes_group(group_name="MEL_aest_zen_runes"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Calligraphy rune marks: small rectangular strokes distributed on faces."""
        in_geom = _get_input_geom(tree)
        pieces = []
        # Build a "rune" from a couple of bars at angles
        bar1 = _node(tree, 'GeometryNodeMeshCube', (-500, -200))
        bar1.inputs['Size'].default_value = (0.18 * P["scale"], 0.04 * P["scale"], 0.015 * P["scale"])
        bar2 = _node(tree, 'GeometryNodeMeshCube', (-500, -350))
        bar2.inputs['Size'].default_value = (0.05 * P["scale"], 0.14 * P["scale"], 0.015 * P["scale"])
        t2 = _node(tree, 'GeometryNodeTransform', (-300, -350))
        t2.inputs['Translation'].default_value = (0.0, 0.05 * P["scale"], 0)
        _link(tree, bar2.outputs['Mesh'], t2.inputs['Geometry'])
        j = _node(tree, 'GeometryNodeJoinGeometry', (-100, -250))
        _link(tree, bar1.outputs['Mesh'], j.inputs['Geometry'])
        _link(tree, t2.outputs['Geometry'], j.inputs['Geometry'])
        color_node(bar1, "ornament"); color_node(bar2, "ornament"); color_node(j, "ornament")
        real = _instance_on_surface(tree, in_geom, j.outputs['Geometry'],
                                    P["density"] * 1.5, P["seed"],
                                    rand_scale=0.4, x_off=200, label="ornament")
        return _join_with_input(tree, in_geom, real)


    # ---- * SPIRITUAL - extra ---------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_runes")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_runes", build_aest_zen_runes_group,
    "Zen Runes", "Aesthetic effect pass (absorbed from monolith build_aest_zen_runes).",
    category="effects", role="modifier")


def build_aest_spi_runes_group(group_name="MEL_aest_spi_runes"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Rune circle: large torus at base + radial bar inscriptions."""
        in_geom = _get_input_geom(tree)
        pieces = []
        ring = _safe_node(tree, 'GeometryNodeMeshTorus', (-400, 0))
        if ring:
            try:
                ring.inputs['Major Radius'].default_value = 2.0 * P["scale"]
                ring.inputs['Minor Radius'].default_value = 0.05 * P["scale"]
                ring.inputs['Major Segments'].default_value = 64
                ring.inputs['Minor Segments'].default_value = 8
            except Exception:
                pass
            rtr = _node(tree, 'GeometryNodeTransform', (-150, 0))
            rtr.inputs['Translation'].default_value = (0, 0, -0.02)
            _link(tree, ring.outputs['Mesh'], rtr.inputs['Geometry'])
            color_node(ring, "ornament"); color_node(rtr, "ornament")
            pieces.append(rtr.outputs['Geometry'])
        import math
        n = max(6, int(P["density"] * 12))
        for i in range(n):
            ang = (i / n) * 6.283185
            bar = _node(tree, 'GeometryNodeMeshCube', (-400, -200 - i * 50))
            bar.inputs['Size'].default_value = (0.15 * P["scale"], 0.035 * P["scale"], 0.02 * P["scale"])
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - i * 50))
            r = 2.0 * P["scale"]
            tr.inputs['Translation'].default_value = (math.cos(ang) * r, math.sin(ang) * r, 0)
            tr.inputs['Rotation'].default_value = (0, 0, ang)
            _link(tree, bar.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(bar, "ornament"); color_node(tr, "ornament")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_runes")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_runes", build_aest_spi_runes_group,
    "Spi Runes", "Aesthetic effect pass (absorbed from monolith build_aest_spi_runes).",
    category="effects", role="modifier")


def build_aest_spi_halo_group(group_name="MEL_aest_spi_halo"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Fractal subdivided halo above the object: subdivided torus."""
        in_geom = _get_input_geom(tree)
        tor = _safe_node(tree, 'GeometryNodeMeshTorus', (-400, 0))
        if tor:
            try:
                tor.inputs['Major Radius'].default_value = 1.2 * P["scale"]
                tor.inputs['Minor Radius'].default_value = 0.1 * P["scale"]
                tor.inputs['Major Segments'].default_value = 48
                tor.inputs['Minor Segments'].default_value = 12
            except Exception:
                pass
            subd = _node(tree, 'GeometryNodeSubdivisionSurface', (-150, 0))
            subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
            _link(tree, tor.outputs['Mesh'], subd.inputs['Mesh'])
            # Noise displacement
            pos = _node(tree, 'GeometryNodeInputPosition', (-150, -250))
            noise = _safe_node(tree, 'ShaderNodeTexNoise', (50, -250))
            if noise:
                noise.inputs['Scale'].default_value = _noise_scale_for(P, 4.0)
                _link(tree, pos.outputs['Position'], noise.inputs['Vector'])
                color_node(noise, "noise")
            normal = _node(tree, 'GeometryNodeInputNormal', (-150, -450))
            scale_n = _node(tree, 'ShaderNodeVectorMath', (250, -350))
            scale_n.operation = 'SCALE'
            _link(tree, normal.outputs['Normal'], scale_n.inputs[0])
            if noise:
                mult = _node(tree, 'ShaderNodeMath', (250, -550))
                mult.operation = 'MULTIPLY'
                _link(tree, noise.outputs['Fac'], mult.inputs[0])
                mult.inputs[1].default_value = P["intensity"] * 0.1
                _link(tree, mult.outputs['Value'], scale_n.inputs['Scale'])
            sp = _safe_node(tree, 'GeometryNodeSetPosition', (500, 0))
            if sp:
                _link(tree, subd.outputs['Mesh'], sp.inputs['Geometry'])
                _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
                tr = _node(tree, 'GeometryNodeTransform', (750, 0))
                tr.inputs['Translation'].default_value = (0, 0, 2.5 * P["intensity"])
                tr.inputs['Rotation'].default_value = (1.5708, 0, 0)
                _link(tree, sp.outputs['Geometry'], tr.inputs['Geometry'])
                color_node(tor, "ornament"); color_node(sp, "ornament"); color_node(tr, "ornament")
                return _join_with_input(tree, in_geom, tr.outputs['Geometry'])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_halo")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_halo", build_aest_spi_halo_group,
    "Spi Halo", "Aesthetic effect pass (absorbed from monolith build_aest_spi_halo).",
    category="effects", role="modifier")


def build_aest_spi_triangles_group(group_name="MEL_aest_spi_triangles"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Overlapping sacred-geometry triangles around the object (n equilateral, rotated)."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(3, int(P["layers"] + 2))
        for i in range(n):
            circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-500, -200 - i * 200))
            if circ is None:
                continue
            try:
                circ.inputs['Resolution'].default_value = 3   # triangle
                circ.inputs['Radius'].default_value = (1.3 + i * 0.15) * P["scale"]
            except Exception:
                pass
            # extrude / wrap with thin cylinder profile
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-500, -350 - i * 200))
            if prof:
                try:
                    prof.inputs['Resolution'].default_value = 6
                    prof.inputs['Radius'].default_value = 0.025 * P["scale"]
                except Exception:
                    pass
                c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', (-250, -250 - i * 200))
                if c2m:
                    _link(tree, circ.outputs['Curve'], c2m.inputs['Curve'])
                    _link(tree, prof.outputs['Curve'], c2m.inputs['Profile Curve'])
                    tr = _node(tree, 'GeometryNodeTransform', (0, -250 - i * 200))
                    tr.inputs['Rotation'].default_value = (0, 0, i * (6.283185 / n))
                    tr.inputs['Translation'].default_value = (0, 0, 0.3 + i * 0.05)
                    _link(tree, c2m.outputs['Mesh'], tr.inputs['Geometry'])
                    color_node(c2m, "ornament"); color_node(tr, "ornament")
                    pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (300, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_triangles")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_triangles", build_aest_spi_triangles_group,
    "Spi Triangles", "Aesthetic effect pass (absorbed from monolith build_aest_spi_triangles).",
    category="effects", role="modifier")


def build_aest_spi_flames_group(group_name="MEL_aest_spi_flames"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Wisp flames: tapered tall cones with noise twist around base."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(4, int(P["density"] * 8))
        for i in range(n):
            ang = (i / n) * 6.283185 + (P["seed"] % 17) * 0.13
            flame = _safe_node(tree, 'GeometryNodeMeshCone', (-400, -200 - i * 100))
            if flame is None:
                continue
            flame.inputs['Radius Bottom'].default_value = 0.18 * P["scale"]
            flame.inputs['Radius Top'].default_value    = 0.0
            flame.inputs['Depth'].default_value         = (0.8 + (i % 3) * 0.4) * P["intensity"]
            flame.inputs['Vertices'].default_value      = 24
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - i * 100))
            r = 1.6 * P["scale"]
            tr.inputs['Translation'].default_value = (math.cos(ang) * r, math.sin(ang) * r,
                                                       0.35 * P["intensity"])
            tr.inputs['Rotation'].default_value = (math.sin(ang) * 0.2, -math.cos(ang) * 0.2, 0)
            _link(tree, flame.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(flame, "ornament"); color_node(tr, "ornament")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_flames")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_flames", build_aest_spi_flames_group,
    "Spi Flames", "Aesthetic effect pass (absorbed from monolith build_aest_spi_flames).",
    category="effects", role="modifier")


def build_aest_spi_ouroboros_group(group_name="MEL_aest_spi_ouroboros"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Snake ring: segmented spheres around a circle."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(12, int(P["density"] * 24))
        radius = 1.8 * P["scale"]
        for i in range(n):
            ang = (i / n) * 6.283185
            # scale tapers like a snake (smaller near "tail")
            tail_factor = 1.0 - 0.5 * abs((i / n) - 0.5) * 2
            seg = _node(tree, 'GeometryNodeMeshUVSphere', (-400, -200 - i * 30))
            seg.inputs['Radius'].default_value = (0.12 + 0.08 * tail_factor) * P["scale"]
            seg.inputs['Segments'].default_value = 10
            seg.inputs['Rings'].default_value    = 6
            tr = _node(tree, 'GeometryNodeTransform', (-150, -200 - i * 30))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius,
                                                       0.7 * P["intensity"])
            _link(tree, seg.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(seg, "ornament"); color_node(tr, "ornament")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_ouroboros")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_ouroboros", build_aest_spi_ouroboros_group,
    "Spi Ouroboros", "Aesthetic effect pass (absorbed from monolith build_aest_spi_ouroboros).",
    category="effects", role="modifier")


def build_aest_spi_portal_group(group_name="MEL_aest_spi_portal"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Large flat ring portal behind the object."""
        in_geom = _get_input_geom(tree)
        pieces = []
        tor = _safe_node(tree, 'GeometryNodeMeshTorus', (-400, 0))
        if tor:
            try:
                tor.inputs['Major Radius'].default_value = 2.0 * P["scale"]
                tor.inputs['Minor Radius'].default_value = 0.15 * P["scale"]
                tor.inputs['Major Segments'].default_value = 64
                tor.inputs['Minor Segments'].default_value = 12
            except Exception:
                pass
            tr = _node(tree, 'GeometryNodeTransform', (-150, 0))
            tr.inputs['Rotation'].default_value = (1.5708, 0, 0)
            tr.inputs['Translation'].default_value = (0, 1.5 * P["scale"], 2.0 * P["intensity"])
            _link(tree, tor.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(tor, "input"); color_node(tr, "input")
            pieces.append(tr.outputs['Geometry'])
        # Inner swirling disc - subdivided + noise warped
        disc = _safe_node(tree, 'GeometryNodeMeshCircle', (-400, -300))
        if disc:
            try:
                disc.inputs['Radius'].default_value = 1.8 * P["scale"]
                disc.inputs['Vertices'].default_value = 64
                disc.fill_type = 'NGON'
            except Exception:
                pass
            subd = _node(tree, 'GeometryNodeSubdivisionSurface', (-200, -300))
            subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
            _link(tree, disc.outputs['Mesh'], subd.inputs['Mesh'])
            pos = _node(tree, 'GeometryNodeInputPosition', (-400, -550))
            noise = _safe_node(tree, 'ShaderNodeTexNoise', (-200, -550))
            if noise:
                noise.inputs['Scale'].default_value = _noise_scale_for(P, 3.0)
                _link(tree, pos.outputs['Position'], noise.inputs['Vector'])
            normal = _node(tree, 'GeometryNodeInputNormal', (-400, -750))
            sn = _node(tree, 'ShaderNodeVectorMath', (0, -550))
            sn.operation = 'SCALE'
            _link(tree, normal.outputs['Normal'], sn.inputs[0])
            if noise:
                mm = _node(tree, 'ShaderNodeMath', (0, -750))
                mm.operation = 'MULTIPLY'
                _link(tree, noise.outputs['Fac'], mm.inputs[0])
                mm.inputs[1].default_value = P["intensity"] * 0.3
                _link(tree, mm.outputs['Value'], sn.inputs['Scale'])
            sp = _safe_node(tree, 'GeometryNodeSetPosition', (250, -300))
            if sp:
                _link(tree, subd.outputs['Mesh'], sp.inputs['Geometry'])
                _link(tree, sn.outputs['Vector'], sp.inputs['Offset'])
                tr_d = _node(tree, 'GeometryNodeTransform', (500, -300))
                tr_d.inputs['Rotation'].default_value = (1.5708, 0, 0)
                tr_d.inputs['Translation'].default_value = (0, 1.51 * P["scale"], 2.0 * P["intensity"])
                _link(tree, sp.outputs['Geometry'], tr_d.inputs['Geometry'])
                color_node(disc, "input"); color_node(sp, "input"); color_node(tr_d, "input")
                pieces.append(tr_d.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (800, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    # ======================================================================
    # v2.17 - music-reactive + advanced-GN aesthetic effects
    # ======================================================================

    def _music_mod(P, base, k=1.0):
        """Return base modulated by universal music influence × aest_music_gain."""
        if not getattr(P, 'aest_music_react', False):
            return base
        inf = getattr(P, 'universal_music_influence', 0.0)
        gain = getattr(P, 'aest_music_gain', 1.0)
        return base * (1.0 + inf * gain * k)


    # ---- * MUSIC-REACTIVE ------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_portal")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_portal", build_aest_spi_portal_group,
    "Spi Portal", "Aesthetic effect pass (absorbed from monolith build_aest_spi_portal).",
    category="effects", role="modifier")


def build_aest_mus_pulse_group(group_name="MEL_aest_mus_pulse"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Whole-mesh radial sine pulse driven by musical_freq_a."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        lenv = _node(tree, 'ShaderNodeVectorMath', (250, -200))
        lenv.operation = 'LENGTH'
        _link(tree, pos.outputs['Position'], lenv.inputs[0])
        mul = _node(tree, 'ShaderNodeMath', (500, -200))
        mul.operation = 'MULTIPLY'
        _link(tree, lenv.outputs['Value'], mul.inputs[0])
        freq = getattr(P, 'musical_freq_a', 1.0)
        mul.inputs[1].default_value = freq * 2.0 * P["density"]
        sn = _node(tree, 'ShaderNodeMath', (700, -200))
        sn.operation = 'SINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (900, -200))
        amp.operation = 'MULTIPLY'
        _link(tree, sn.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = _music_mod(P, P["intensity"] * 0.2, k=2.0)
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -450))
        scale_n = _node(tree, 'ShaderNodeVectorMath', (1100, -300))
        scale_n.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], scale_n.inputs[0])
        _link(tree, amp.outputs['Value'], scale_n.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (1400, 0))
        if sp:
            _link(tree, subd.outputs['Mesh'], sp.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
            color_node(sp, "music")
            return sp.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mus_pulse")
    return tree, gin, gout

register_builder(
    "MEL_aest_mus_pulse", build_aest_mus_pulse_group,
    "Mus Pulse", "Aesthetic effect pass (absorbed from monolith build_aest_mus_pulse).",
    category="effects", role="modifier")


def build_aest_mus_eq_bars_group(group_name="MEL_aest_mus_eq_bars"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Vertical EQ bars around the silhouette, heights vary as 'spectrum' bands."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(8, int(P["density"] * 16))
        radius = 1.8 * P["scale"]
        fa = getattr(P, 'musical_freq_a', 1.0)
        fb = getattr(P, 'musical_freq_b', 1.5)
        for i in range(n):
            ang = (i / n) * 6.283185
            # pseudo-band amplitude from sin combination
            amp = abs(math.sin(i * fa * 0.4) + 0.7 * math.cos(i * fb * 0.5))
            amp = _music_mod(P, amp, k=2.5)
            h = (0.3 + amp * 1.6) * P["intensity"]
            bar = _node(tree, 'GeometryNodeMeshCube', (-400 + (i % 6) * 150, -200 - (i // 6) * 200))
            bar.inputs['Size'].default_value = (0.12 * P["scale"], 0.12 * P["scale"], h)
            tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 6) * 150, -200 - (i // 6) * 200))
            tr.inputs['Translation'].default_value = (math.cos(ang) * radius, math.sin(ang) * radius, h * 0.5)
            _link(tree, bar.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(bar, "music"); color_node(tr, "music")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mus_eq_bars")
    return tree, gin, gout

register_builder(
    "MEL_aest_mus_eq_bars", build_aest_mus_eq_bars_group,
    "Mus Eq Bars", "Aesthetic effect pass (absorbed from monolith build_aest_mus_eq_bars).",
    category="effects", role="modifier")


def build_aest_mus_wave_disp_group(group_name="MEL_aest_mus_wave_disp"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Noise displacement scaled by universal_music_influence × music_gain."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        noise = _safe_node(tree, 'ShaderNodeTexNoise', (250, -200))
        if noise:
            noise.inputs['Scale'].default_value = _noise_scale_for(P, 3.0)
            noise.inputs['Detail'].default_value = 5.0
            _link(tree, pos.outputs['Position'], noise.inputs['Vector'])
            color_node(noise, "music")
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -400))
        sn = _node(tree, 'ShaderNodeVectorMath', (500, -300))
        sn.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], sn.inputs[0])
        if noise:
            mm = _node(tree, 'ShaderNodeMath', (500, -500))
            mm.operation = 'MULTIPLY'
            _link(tree, noise.outputs['Fac'], mm.inputs[0])
            mm.inputs[1].default_value = _music_mod(P, P["intensity"] * 0.35, k=3.0)
            _link(tree, mm.outputs['Value'], sn.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (800, 0))
        if sp:
            _link(tree, subd.outputs['Mesh'], sp.inputs['Geometry'])
            _link(tree, sn.outputs['Vector'], sp.inputs['Offset'])
            color_node(sp, "music")
            return sp.outputs['Geometry']
        return subd.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mus_wave_disp")
    return tree, gin, gout

register_builder(
    "MEL_aest_mus_wave_disp", build_aest_mus_wave_disp_group,
    "Mus Wave Disp", "Aesthetic effect pass (absorbed from monolith build_aest_mus_wave_disp).",
    category="effects", role="modifier")


def build_aest_mus_beat_ring_group(group_name="MEL_aest_mus_beat_ring"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Orbiting ring of orbs with radii pulsing per-orb."""
        in_geom = _get_input_geom(tree)
        pieces = []
        import math
        n = max(6, int(P["density"] * 12))
        base_r = 2.0 * P["scale"]
        fa = getattr(P, 'musical_freq_a', 1.0)
        for i in range(n):
            ang = (i / n) * 6.283185
            amp = 0.5 + 0.5 * math.sin(i * fa * 0.7)
            r = base_r * (1.0 + _music_mod(P, amp * 0.3, k=2.0))
            orb = _node(tree, 'GeometryNodeMeshIcoSphere', (-400 + (i % 5) * 180, -200 - (i // 5) * 180))
            orb.inputs['Radius'].default_value = (0.1 + amp * 0.2) * P["scale"]
            orb.inputs['Subdivisions'].default_value = 2
            tr = _node(tree, 'GeometryNodeTransform', (-200 + (i % 5) * 180, -200 - (i // 5) * 180))
            tr.inputs['Translation'].default_value = (math.cos(ang) * r, math.sin(ang) * r, P["intensity"] * 1.2)
            _link(tree, orb.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(orb, "music"); color_node(tr, "music")
            pieces.append(tr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (200, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mus_beat_ring")
    return tree, gin, gout

register_builder(
    "MEL_aest_mus_beat_ring", build_aest_mus_beat_ring_group,
    "Mus Beat Ring", "Aesthetic effect pass (absorbed from monolith build_aest_mus_beat_ring).",
    category="effects", role="modifier")


def build_aest_mus_harmonic_group(group_name="MEL_aest_mus_harmonic"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Horizontal grooves at freq_a + freq_b mixed sine."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (200, -200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        fa = getattr(P, 'musical_freq_a', 1.0)
        fb = getattr(P, 'musical_freq_b', 1.5)
        ma = _node(tree, 'ShaderNodeMath', (400, -200)); ma.operation = 'MULTIPLY'
        _link(tree, sep.outputs['Z'], ma.inputs[0]); ma.inputs[1].default_value = fa * P["density"] * 5.0
        sna = _node(tree, 'ShaderNodeMath', (600, -200)); sna.operation = 'SINE'
        _link(tree, ma.outputs['Value'], sna.inputs[0])
        mb = _node(tree, 'ShaderNodeMath', (400, -380)); mb.operation = 'MULTIPLY'
        _link(tree, sep.outputs['Z'], mb.inputs[0]); mb.inputs[1].default_value = fb * P["density"] * 5.0
        snb = _node(tree, 'ShaderNodeMath', (600, -380)); snb.operation = 'SINE'
        _link(tree, mb.outputs['Value'], snb.inputs[0])
        add = _node(tree, 'ShaderNodeMath', (800, -290)); add.operation = 'ADD'
        _link(tree, sna.outputs['Value'], add.inputs[0])
        _link(tree, snb.outputs['Value'], add.inputs[1])
        amp = _node(tree, 'ShaderNodeMath', (1000, -290)); amp.operation = 'MULTIPLY'
        _link(tree, add.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = _music_mod(P, P["intensity"] * 0.08, k=2.5)
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -550))
        sn = _node(tree, 'ShaderNodeVectorMath', (1200, -350)); sn.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], sn.inputs[0])
        _link(tree, amp.outputs['Value'], sn.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (1500, 0))
        if sp:
            _link(tree, subd.outputs['Mesh'], sp.inputs['Geometry'])
            _link(tree, sn.outputs['Vector'], sp.inputs['Offset'])
            color_node(sp, "music")
            return sp.outputs['Geometry']
        return subd.outputs['Mesh']


    # ---- * ADVANCED GN ----------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mus_harmonic")
    return tree, gin, gout

register_builder(
    "MEL_aest_mus_harmonic", build_aest_mus_harmonic_group,
    "Mus Harmonic", "Aesthetic effect pass (absorbed from monolith build_aest_mus_harmonic).",
    category="effects", role="modifier")


def build_aest_adv_ray_grow_group(group_name="MEL_aest_adv_ray_grow"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Distribute points on input, raycast outward, instance cones at hit points."""
        in_geom = _get_input_geom(tree)
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (0, 0))
        if pts is None or in_geom is None:
            return in_geom
        pts.distribute_method = 'POISSON'
        pts.inputs['Distance Min'].default_value = 0.5 / max(0.1, P["density"])
        pts.inputs['Density Max'].default_value  = P["density"] * 2.0
        pts.inputs['Seed'].default_value         = P["seed"]
        _link(tree, in_geom, pts.inputs['Mesh'])
        color_node(pts, "input")
        # Cone instance
        cone = _safe_node(tree, 'GeometryNodeMeshCone', (0, -300))
        if cone:
            cone.inputs['Radius Bottom'].default_value = 0.06 * P["scale"]
            cone.inputs['Radius Top'].default_value    = 0.0
            cone.inputs['Depth'].default_value         = 0.5 * P["intensity"] * P["scale"]
            cone.inputs['Vertices'].default_value      = 6
            color_node(cone, "ornament")
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (300, 0))
        if inst and pts and cone:
            _link(tree, pts.outputs['Points'], inst.inputs['Points'])
            _link(tree, cone.outputs['Mesh'], inst.inputs['Instance'])
            try:
                _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
            except Exception:
                pass
            color_node(inst, "ornament")
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (600, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, real.outputs['Geometry'] if real else None)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_ray_grow")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_ray_grow", build_aest_adv_ray_grow_group,
    "Adv Ray Grow", "Aesthetic effect pass (absorbed from monolith build_aest_adv_ray_grow).",
    category="effects", role="modifier")


def build_aest_adv_near_fur_group(group_name="MEL_aest_adv_near_fur"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Index of Nearest fur: tiny cones whose lengths scale by distance."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(3, P["layers"] + 1)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        # Convert verts to points
        m2p = _safe_node(tree, 'GeometryNodeMeshToPoints', (250, 0))
        if m2p:
            _link(tree, subd.outputs['Mesh'], m2p.inputs['Mesh'])
        cone = _safe_node(tree, 'GeometryNodeMeshCone', (250, -300))
        if cone:
            cone.inputs['Radius Bottom'].default_value = 0.04 * P["scale"]
            cone.inputs['Radius Top'].default_value    = 0.0
            cone.inputs['Depth'].default_value         = 0.18 * P["intensity"] * P["scale"]
            cone.inputs['Vertices'].default_value      = 24
            color_node(cone, "input")
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -400))
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (550, 0))
        if inst and m2p and cone:
            _link(tree, m2p.outputs['Points'], inst.inputs['Points'])
            _link(tree, cone.outputs['Mesh'],  inst.inputs['Instance'])
            # rotate cones to align with normal - use Align Rotation to Vector if available
            align = _safe_node(tree, 'FunctionNodeAlignEulerToVector', (300, -500))
            if align:
                try:
                    _link(tree, normal.outputs['Normal'], align.inputs['Vector'])
                    _link(tree, align.outputs['Rotation'], inst.inputs['Rotation'])
                except Exception:
                    pass
            color_node(inst, "input")
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (850, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, real.outputs['Geometry'] if real else None)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_near_fur")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_near_fur", build_aest_adv_near_fur_group,
    "Adv Near Fur", "Aesthetic effect pass (absorbed from monolith build_aest_adv_near_fur).",
    category="effects", role="modifier")


def build_aest_adv_edge_tubes_group(group_name="MEL_aest_adv_edge_tubes"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Tube sweeps along edges where Edge Angle > threshold."""
        in_geom = _get_input_geom(tree)
        # Use Wireframe as a simple proxy (since selecting by edge angle requires per-edge selection)
        wire = _safe_node(tree, 'GeometryNodeWireframe', (0, 0))
        if wire and in_geom:
            try:
                wire.inputs['Radius'].default_value = 0.045 * P["scale"] * P["intensity"]
            except Exception:
                pass
            _link(tree, in_geom, wire.inputs['Mesh'])
            color_node(wire, "tracery")
            return _join_with_input(tree, in_geom, wire.outputs.get('Curve') or wire.outputs[0])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_edge_tubes")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_edge_tubes", build_aest_adv_edge_tubes_group,
    "Adv Edge Tubes", "Aesthetic effect pass (absorbed from monolith build_aest_adv_edge_tubes).",
    category="effects", role="modifier")


def build_aest_adv_dual_mesh_group(group_name="MEL_aest_adv_dual_mesh"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Convert to dual mesh and offset cells outward."""
        in_geom = _get_input_geom(tree)
        dual = _safe_node(tree, 'GeometryNodeDualMesh', (0, 0))
        if dual is None or in_geom is None:
            return in_geom
        _link(tree, in_geom, dual.inputs['Mesh'])
        color_node(dual, "tracery")
        normal = _node(tree, 'GeometryNodeInputNormal', (0, -250))
        sn = _node(tree, 'ShaderNodeVectorMath', (300, -250))
        sn.operation = 'SCALE'
        _link(tree, normal.outputs['Normal'], sn.inputs[0])
        sn.inputs['Scale'].default_value = P["intensity"] * 0.15
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (600, 0))
        if sp:
            _link(tree, dual.outputs['Dual Mesh'] if 'Dual Mesh' in dual.outputs else dual.outputs[0],
                  sp.inputs['Geometry'])
            _link(tree, sn.outputs['Vector'], sp.inputs['Offset'])
            color_node(sp, "tracery")
            return _join_with_input(tree, in_geom, sp.outputs['Geometry'])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_dual_mesh")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_dual_mesh", build_aest_adv_dual_mesh_group,
    "Adv Dual Mesh", "Aesthetic effect pass (absorbed from monolith build_aest_adv_dual_mesh).",
    category="effects", role="modifier")


def build_aest_adv_vor_frac_group(group_name="MEL_aest_adv_vor_frac"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """3D voronoi shatter: distribute points in volume + instance shards."""
        in_geom = _get_input_geom(tree)
        m2v = _safe_node(tree, 'GeometryNodeMeshToVolume', (0, 0))
        if m2v is None or in_geom is None:
            return in_geom
        try: m2v.resolution_mode = 'VOXEL_SIZE'
        except (AttributeError, TypeError): pass
        m2v.inputs['Voxel Size'].default_value = 0.15
        _link(tree, in_geom, m2v.inputs['Mesh'])
        dpts = _safe_node(tree, 'GeometryNodeDistributePointsInVolume', (250, 0))
        if dpts:
            try: dpts.mode = 'DENSITY_GRID'

            except (AttributeError, TypeError):

                try: dpts.inputs['Mode'].default_value = 'DENSITY_GRID'

                except Exception: pass
            try:
                dpts.inputs['Spacing'].default_value = (0.35 / max(0.1, P["density"]),) * 3
            except Exception:
                pass
            _link(tree, m2v.outputs['Volume'], dpts.inputs['Volume'])
        # Random octahedron shards: use ico sphere with 1 subdiv -> diamond
        shard = _node(tree, 'GeometryNodeMeshIcoSphere', (250, -300))
        shard.inputs['Radius'].default_value = 0.22 * P["scale"]
        shard.inputs['Subdivisions'].default_value = 1
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (500, 0))
        if inst and dpts:
            _link(tree, dpts.outputs['Points'], inst.inputs['Points'])
            _link(tree, shard.outputs['Mesh'],  inst.inputs['Instance'])
            rrot = _safe_node(tree, 'FunctionNodeRandomValue', (500, -300))
            if rrot:
                rrot.data_type = 'FLOAT_VECTOR'
                try:
                    rrot.inputs[0].default_value = (-3.14, -3.14, -3.14)
                    rrot.inputs[1].default_value = (3.14, 3.14, 3.14)
                    _link(tree, rrot.outputs['Value'], inst.inputs['Rotation'])
                except Exception:
                    pass
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (800, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
            color_node(inst, "noise"); color_node(real, "noise")
            return _join_with_input(tree, in_geom, real.outputs['Geometry'])
        return in_geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_vor_frac")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_vor_frac", build_aest_adv_vor_frac_group,
    "Adv Vor Frac", "Aesthetic effect pass (absorbed from monolith build_aest_adv_vor_frac).",
    category="effects", role="modifier")


def build_aest_adv_crystals_group(group_name="MEL_aest_adv_crystals"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Distribute crystals via 3D voronoi mask + instance pointy octahedra."""
        in_geom = _get_input_geom(tree)
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (0, 0))
        if pts and in_geom:
            pts.distribute_method = 'POISSON'
            pts.inputs['Distance Min'].default_value = 0.4 / max(0.1, P["density"])
            pts.inputs['Density Max'].default_value  = P["density"] * 2.5
            pts.inputs['Seed'].default_value         = P["seed"]
            _link(tree, in_geom, pts.inputs['Mesh'])
            color_node(pts, "input")
        # crystal = stretched octahedron via ico sphere subdiv 1 + Z scale
        octa = _node(tree, 'GeometryNodeMeshIcoSphere', (0, -300))
        octa.inputs['Radius'].default_value = 0.12 * P["scale"]
        octa.inputs['Subdivisions'].default_value = 1
        tr_o = _node(tree, 'GeometryNodeTransform', (250, -300))
        tr_o.inputs['Scale'].default_value = (0.4, 0.4, 1.4)
        _link(tree, octa.outputs['Mesh'], tr_o.inputs['Geometry'])
        color_node(octa, "noise"); color_node(tr_o, "noise")
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (500, 0))
        if inst and pts:
            _link(tree, pts.outputs['Points'], inst.inputs['Points'])
            _link(tree, tr_o.outputs['Geometry'], inst.inputs['Instance'])
            try:
                _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
            except Exception:
                pass
            rs = _safe_node(tree, 'FunctionNodeRandomValue', (500, -250))
            if rs:
                rs.data_type = 'FLOAT'
                try:
                    rs.inputs['Min'].default_value = 0.6
                    rs.inputs['Max'].default_value = 1.0 + 0.5 * P["intensity"]
                    _link(tree, rs.outputs['Value'], inst.inputs['Scale'])
                except Exception:
                    pass
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (800, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, real.outputs['Geometry'] if real else None)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_crystals")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_crystals", build_aest_adv_crystals_group,
    "Adv Crystals", "Aesthetic effect pass (absorbed from monolith build_aest_adv_crystals).",
    category="effects", role="modifier")


def build_aest_adv_field_lat_group(group_name="MEL_aest_adv_field_lat"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Subdivided lattice: position-driven X+Y+Z noise displacement."""
        in_geom = _get_input_geom(tree)
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (0, 0))
        subd.inputs['Level'].default_value = min(4, P["layers"] + 2)
        if in_geom:
            _link(tree, in_geom, subd.inputs['Mesh'])
        pos = _node(tree, 'GeometryNodeInputPosition', (0, -200))
        noise = _safe_node(tree, 'ShaderNodeTexNoise', (250, -200))
        if noise:
            noise.inputs['Scale'].default_value = _noise_scale_for(P, 5.0)
            noise.inputs['Detail'].default_value = 8.0
            noise.inputs['Distortion'].default_value = 1.5
            _link(tree, pos.outputs['Position'], noise.inputs['Vector'])
        # Take the noise color (vec3) directly as offset
        sn = _node(tree, 'ShaderNodeVectorMath', (550, -200))
        sn.operation = 'SCALE'
        if noise:
            _link(tree, noise.outputs.get('Color') or noise.outputs[0], sn.inputs[0])
        sn.inputs['Scale'].default_value = P["intensity"] * 0.25
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (800, 0))
        if sp:
            _link(tree, subd.outputs['Mesh'], sp.inputs['Geometry'])
            _link(tree, sn.outputs['Vector'], sp.inputs['Offset'])
            color_node(sp, "noise")
            # Wireframe overlay
            wire = _safe_node(tree, 'GeometryNodeWireframe', (1050, 0))
            if wire:
                try:
                    wire.inputs['Radius'].default_value = 0.02 * P["scale"]
                except Exception:
                    pass
                _link(tree, sp.outputs['Geometry'], wire.inputs['Mesh'])
                color_node(wire, "tracery")
                join = _node(tree, 'GeometryNodeJoinGeometry', (1300, 0))
                _link(tree, sp.outputs['Geometry'], join.inputs['Geometry'])
                try:
                    _link(tree, wire.outputs.get('Curve') or wire.outputs[0], join.inputs['Geometry'])
                except Exception:
                    pass
                color_node(join, "output")
                return join.outputs['Geometry']
            return sp.outputs['Geometry']
        return subd.outputs['Mesh']


    # ======================================================================
    # v2.18 - Curve-rich aesthetic effects (no cones/cubes)
    # Built from bezier curves swept with profile curves -> real ribbon geometry.
    # Music-driven via _aest_val(P, 'INTENSITY'/'DENSITY'/'SCALE').
    # ======================================================================

    def _make_circle_profile(tree, radius, resolution=8, loc=(-400, -600), P=None):
        """Build the user-selected sweep profile and return a stub object whose
        `.outputs['Curve']` is the profile curve socket.

        Backwards-compatible wrapper: callers that pass no `P` get a circle.
        With `P`, picks from `P["profile"]`."""
        kind = getattr(P, 'aest_profile', 'CIRCLE') if P else 'CIRCLE'

        class _ProfileStub:
            def __init__(self, sock):
                self.outputs = {'Curve': sock}

        # CIRCLE - default round tube
        if kind == 'CIRCLE':
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
            if prof is None:
                return None
            try:
                prof.inputs['Resolution'].default_value = resolution
                prof.inputs['Radius'].default_value     = radius
            except Exception:
                return None
            color_node(prof, "input")
            return prof

        # SQUARE - quadrilateral via 4-resolution circle (gives a diamond,
        # but a Curve Line ring of 4 points is closer)
        if kind == 'SQUARE':
            # Build a quad as a small bezier closed curve via Curve Line w/4 segments
            # Easiest: a circle with 4 verts (rotated 45deg gives diamond - fine).
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
            if prof is None:
                return None
            try:
                prof.inputs['Resolution'].default_value = 4
                prof.inputs['Radius'].default_value     = radius * 1.2
            except Exception:
                return None
            color_node(prof, "input")
            return prof

        # FLUTE - multi-lobed circle: build by Set Position on a high-res circle
        # using radial sin to perturb the radius
        if kind == 'FLUTE':
            base = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
            if base is None:
                return None
            try:
                base.inputs['Resolution'].default_value = 48
                base.inputs['Radius'].default_value     = radius
            except Exception:
                return None
            # Per-point radial perturbation: sin(angle * 8) * radius * 0.25
            pos = _node(tree, 'GeometryNodeInputPosition', (loc[0] - 200, loc[1] - 200))
            sep = _node(tree, 'ShaderNodeSeparateXYZ', (loc[0] - 50, loc[1] - 200))
            _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
            atan = _node(tree, 'ShaderNodeMath', (loc[0] + 100, loc[1] - 200))
            atan.operation = 'ARCTAN2'
            _link(tree, sep.outputs['Y'], atan.inputs[0])
            _link(tree, sep.outputs['X'], atan.inputs[1])
            mul = _node(tree, 'ShaderNodeMath', (loc[0] + 250, loc[1] - 200))
            mul.operation = 'MULTIPLY'
            _link(tree, atan.outputs['Value'], mul.inputs[0])
            mul.inputs[1].default_value = 8.0   # 8 flutes
            sn = _node(tree, 'ShaderNodeMath', (loc[0] + 400, loc[1] - 200))
            sn.operation = 'SINE'
            _link(tree, mul.outputs['Value'], sn.inputs[0])
            amp = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 200))
            amp.operation = 'MULTIPLY'
            _link(tree, sn.outputs['Value'], amp.inputs[0])
            amp.inputs[1].default_value = radius * 0.3
            # Push verts outward along their own direction (just X,Y scaled)
            scale_n = _node(tree, 'ShaderNodeVectorMath', (loc[0] + 700, loc[1] - 100))
            scale_n.operation = 'SCALE'
            _link(tree, pos.outputs['Position'], scale_n.inputs[0])
            # normalize-ish: we'll use the position itself; small offset is fine
            norm_div = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 300))
            norm_div.operation = 'DIVIDE'
            _link(tree, amp.outputs['Value'], norm_div.inputs[0])
            norm_div.inputs[1].default_value = max(0.001, radius)
            _link(tree, norm_div.outputs['Value'], scale_n.inputs['Scale'])
            sp = _safe_node(tree, 'GeometryNodeSetPosition', (loc[0] + 900, loc[1]))
            if sp:
                _link(tree, base.outputs['Curve'], sp.inputs['Geometry'])
                _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
                color_node(base, "input"); color_node(sp, "input")
                return _ProfileStub(sp.outputs['Geometry'])
            return base

        # OGEE - S-curve: two quadratic beziers stitched. Approximate with
        # a thin tall oval (circle scaled along Y) for now.
        if kind == 'OGEE':
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
            if prof is None:
                return None
            try:
                prof.inputs['Resolution'].default_value = 16
                prof.inputs['Radius'].default_value     = radius
            except Exception:
                return None
            # Scale the circle into an oval via Transform
            tr = _node(tree, 'GeometryNodeTransform', (loc[0] + 250, loc[1]))
            tr.inputs['Scale'].default_value = (0.5, 1.4, 1.0)
            _link(tree, prof.outputs['Curve'], tr.inputs['Geometry'])
            color_node(prof, "input"); color_node(tr, "input")
            return _ProfileStub(tr.outputs['Geometry'])

        # LOTUS - pointed-petal cross-section (5-pointed)
        if kind == 'LOTUS':
            base = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
            if base is None:
                return None
            try:
                base.inputs['Resolution'].default_value = 60
                base.inputs['Radius'].default_value     = radius
            except Exception:
                return None
            pos = _node(tree, 'GeometryNodeInputPosition', (loc[0] - 200, loc[1] - 200))
            sep = _node(tree, 'ShaderNodeSeparateXYZ', (loc[0] - 50, loc[1] - 200))
            _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
            atan = _node(tree, 'ShaderNodeMath', (loc[0] + 100, loc[1] - 200))
            atan.operation = 'ARCTAN2'
            _link(tree, sep.outputs['Y'], atan.inputs[0])
            _link(tree, sep.outputs['X'], atan.inputs[1])
            mul = _node(tree, 'ShaderNodeMath', (loc[0] + 250, loc[1] - 200))
            mul.operation = 'MULTIPLY'
            _link(tree, atan.outputs['Value'], mul.inputs[0])
            mul.inputs[1].default_value = 5.0   # 5 petals
            sn = _node(tree, 'ShaderNodeMath', (loc[0] + 400, loc[1] - 200))
            sn.operation = 'COSINE'
            _link(tree, mul.outputs['Value'], sn.inputs[0])
            abs_n = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 200))
            abs_n.operation = 'ABSOLUTE'
            _link(tree, sn.outputs['Value'], abs_n.inputs[0])
            amp = _node(tree, 'ShaderNodeMath', (loc[0] + 700, loc[1] - 200))
            amp.operation = 'MULTIPLY'
            _link(tree, abs_n.outputs['Value'], amp.inputs[0])
            amp.inputs[1].default_value = radius * 0.6
            scale_n = _node(tree, 'ShaderNodeVectorMath', (loc[0] + 700, loc[1] - 50))
            scale_n.operation = 'SCALE'
            _link(tree, pos.outputs['Position'], scale_n.inputs[0])
            norm_div = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 350))
            norm_div.operation = 'DIVIDE'
            _link(tree, amp.outputs['Value'], norm_div.inputs[0])
            norm_div.inputs[1].default_value = max(0.001, radius)
            _link(tree, norm_div.outputs['Value'], scale_n.inputs['Scale'])
            sp = _safe_node(tree, 'GeometryNodeSetPosition', (loc[0] + 900, loc[1]))
            if sp:
                _link(tree, base.outputs['Curve'], sp.inputs['Geometry'])
                _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
                color_node(base, "input"); color_node(sp, "input")
                return _ProfileStub(sp.outputs['Geometry'])
            return base

        # Fallback: circle
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = resolution
            prof.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        color_node(prof, "input")
        return prof


    def _aest_mask_field(tree, P, loc=(-700, 400)):
        """Return a Float output socket carrying the mask weight (1.0 everywhere
        when no mask is set; otherwise reads `P["mask"]` as a Named
        Attribute and returns its value). Builders multiply distribution density
        or displacement amplitude by this to honor the mask."""
        name = (getattr(P, 'aest_mask_attr', '') or '').strip()
        if not name:
            const = _node(tree, 'ShaderNodeValue', loc)
            const.outputs[0].default_value = 1.0
            color_node(const, "input")
            return const.outputs[0]
        na = _safe_node(tree, 'GeometryNodeInputNamedAttribute', loc)
        if na is None:
            const = _node(tree, 'ShaderNodeValue', loc)
            const.outputs[0].default_value = 1.0
            return const.outputs[0]
        try:
            na.data_type = 'FLOAT'
            na.inputs['Name'].default_value = name
        except Exception:
            pass
        color_node(na, "input")
        # Different Blender versions name the output socket differently
        for sname in ('Attribute', 'Value'):
            if sname in [s.name for s in na.outputs]:
                return na.outputs[sname]
        return na.outputs[0]


    def _sweep_curve(tree, curve_out, profile_out, loc=(0, 0), label="ornament"):
        """Curve to Mesh sweep helper."""
        c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', loc)
        if c2m is None or curve_out is None or profile_out is None:
            return None
        _link(tree, curve_out, c2m.inputs['Curve'])
        _link(tree, profile_out, c2m.inputs['Profile Curve'])
        try:
            c2m.inputs['Fill Caps'].default_value = True
        except Exception:
            pass
        color_node(c2m, label)
        return c2m.outputs['Mesh']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_adv_field_lat")
    return tree, gin, gout

register_builder(
    "MEL_aest_adv_field_lat", build_aest_adv_field_lat_group,
    "Adv Field Lat", "Aesthetic effect pass (absorbed from monolith build_aest_adv_field_lat).",
    category="effects", role="modifier")


def build_aest_goth_vault_group(group_name="MEL_aest_goth_vault"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Pointed Gothic ribbed vault: ribs rise from base perimeter to apex,
        each is a real bezier arch swept with a thin profile circle."""
        in_geom = _get_input_geom(tree)
        intensity = _aest_val(P, 'INTENSITY')
        density   = _aest_val(P, 'DENSITY')
        scale     = _aest_val(P, 'SCALE')
        import math
        pieces = []
        n_ribs = max(4, int(density * 8))
        prof = _make_circle_profile(tree, 0.04 * scale, 6, loc=(-700, -1000), P=P)
        base_r = 1.6 * scale
        apex_z = 2.6 * intensity
        for i in range(n_ribs):
            ang = (i / n_ribs) * 6.283185
            cx = math.cos(ang) * base_r
            cy = math.sin(ang) * base_r
            # Build arch as quadratic bezier from (cx,cy,0) -> apex (0,0,apex_z) -> (-cx,-cy,0)
            qb = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier',
                            (-400, -200 - i * 100))
            if qb is None:
                continue
            try:
                qb.inputs['Resolution'].default_value = 32
                qb.inputs['Start'].default_value  = (cx, cy, 0)
                # Middle pulled toward apex with pointed Gothic lift
                qb.inputs['Middle'].default_value = (cx * 0.15, cy * 0.15, apex_z * 1.15)
                qb.inputs['End'].default_value    = (-cx, -cy, 0)
            except Exception:
                continue
            color_node(qb, "gothic")
            mesh = _sweep_curve(tree, qb.outputs['Curve'],
                                prof.outputs['Curve'] if prof else None,
                                loc=(-100, -200 - i * 100), label="gothic")
            if mesh:
                pieces.append(mesh)
        # Add ring at base + boss at apex (real torus, not cube)
        base_ring = _safe_node(tree, 'GeometryNodeMeshTorus', (-400, 200))
        if base_ring:
            try:
                base_ring.inputs['Major Radius'].default_value = base_r
                base_ring.inputs['Minor Radius'].default_value = 0.06 * scale
                base_ring.inputs['Major Segments'].default_value = 48
                base_ring.inputs['Minor Segments'].default_value = 8
            except Exception:
                pass
            color_node(base_ring, "gothic")
            pieces.append(base_ring.outputs['Mesh'])
        apex_boss = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (-400, 400))
        if apex_boss:
            apex_boss.inputs['Radius'].default_value       = 0.15 * scale
            apex_boss.inputs['Subdivisions'].default_value = 3
            t = _node(tree, 'GeometryNodeTransform', (-150, 400))
            t.inputs['Translation'].default_value = (0, 0, apex_z * 1.1)
            _link(tree, apex_boss.outputs['Mesh'], t.inputs['Geometry'])
            color_node(apex_boss, "gothic"); color_node(t, "gothic")
            pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (400, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_vault")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_vault", build_aest_goth_vault_group,
    "Goth Vault", "Aesthetic effect pass (absorbed from monolith build_aest_goth_vault).",
    category="effects", role="modifier")


def build_aest_goth_tracery2_group(group_name="MEL_aest_goth_tracery2"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Branching bezier tracery: nested arches inside arches (real curves)."""
        in_geom = _get_input_geom(tree)
        intensity = _aest_val(P, 'INTENSITY')
        density   = _aest_val(P, 'DENSITY')
        scale     = _aest_val(P, 'SCALE')
        pieces = []
        prof = _make_circle_profile(tree, 0.025 * scale, 6, loc=(-700, -800), P=P)
        # Outer arch + 2 inner arches (recursive feel)
        main_w = 2.0 * scale
        main_h = 2.6 * intensity
        main = _gothic_arch_curve(tree, main_w, main_h, 0.5, x=-400, y=0)
        if main and prof:
            m = _sweep_curve(tree, main, prof.outputs['Curve'], loc=(-100, 0), label="gothic")
            if m:
                pieces.append(m)
        # Inner arches (left/right children)
        for i, (ox, oy_factor) in enumerate([(-0.45, 0.7), (0.45, 0.7)]):
            sub = _gothic_arch_curve(tree, main_w * 0.45, main_h * 0.6, 0.7,
                                     x=-400, y=-200 - i * 150)
            if sub and prof:
                sub_mesh = _sweep_curve(tree, sub, prof.outputs['Curve'],
                                        loc=(-100, -200 - i * 150), label="gothic")
                if sub_mesh:
                    t = _node(tree, 'GeometryNodeTransform',
                              (200, -200 - i * 150))
                    t.inputs['Translation'].default_value = (ox * scale, 0, 0)
                    _link(tree, sub_mesh, t.inputs['Geometry'])
                    color_node(t, "gothic")
                    pieces.append(t.outputs['Geometry'])
        # Quatrefoil at the apex (4 bezier circles)
        import math
        for k in range(4):
            ang = (k / 4) * 6.283185
            circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                              (-400, -600 - k * 100))
            if circ is None:
                continue
            try:
                circ.inputs['Radius'].default_value = 0.18 * scale
                circ.inputs['Resolution'].default_value = 24
            except Exception:
                continue
            sw = _sweep_curve(tree, circ.outputs['Curve'],
                              prof.outputs['Curve'] if prof else None,
                              loc=(-100, -600 - k * 100), label="gothic")
            if sw:
                t = _node(tree, 'GeometryNodeTransform', (200, -600 - k * 100))
                t.inputs['Translation'].default_value = (
                    math.cos(ang) * 0.22 * scale,
                    0,
                    main_h * 0.85 + math.sin(ang) * 0.22 * scale)
                t.inputs['Rotation'].default_value = (1.5708, 0, 0)
                _link(tree, sw, t.inputs['Geometry'])
                color_node(t, "gothic")
                pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (500, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_goth_tracery2")
    return tree, gin, gout

register_builder(
    "MEL_aest_goth_tracery2", build_aest_goth_tracery2_group,
    "Goth Tracery2", "Aesthetic effect pass (absorbed from monolith build_aest_goth_tracery2).",
    category="effects", role="modifier")


def build_aest_vap_dolphin_group(group_name="MEL_aest_vap_dolphin"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Sine-wave dolphin-jump arcs swept with a neon tube profile."""
        in_geom = _get_input_geom(tree)
        intensity = _aest_val(P, 'INTENSITY')
        density   = _aest_val(P, 'DENSITY')
        scale     = _aest_val(P, 'SCALE')
        pieces = []
        prof = _make_circle_profile(tree, 0.05 * scale, 8, loc=(-700, -800), P=P)
        n_arcs = max(3, int(density * 5))
        span = 4.0 * scale
        for i in range(n_arcs):
            # Each arc is a quadratic bezier arching up
            qb = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier',
                            (-400, -200 - i * 150))
            if qb is None:
                continue
            try:
                qb.inputs['Resolution'].default_value = 64
                qb.inputs['Start'].default_value  = (-span * 0.5, 0, 0)
                qb.inputs['Middle'].default_value = (0, 0, span * 0.5 * intensity)
                qb.inputs['End'].default_value    = (span * 0.5, 0, 0)
            except Exception:
                continue
            color_node(qb, "input")
            sw = _sweep_curve(tree, qb.outputs['Curve'],
                              prof.outputs['Curve'] if prof else None,
                              loc=(-100, -200 - i * 150), label="input")
            if sw:
                t = _node(tree, 'GeometryNodeTransform', (200, -200 - i * 150))
                t.inputs['Rotation'].default_value = (0, 0, (i / n_arcs) * 6.283185)
                t.inputs['Translation'].default_value = (0, 0, 0.3 + i * 0.4)
                t.inputs['Scale'].default_value = (1.0, 1.0, 0.7 + 0.3 * (i / max(1, n_arcs - 1)))
                _link(tree, sw, t.inputs['Geometry'])
                color_node(t, "input")
                pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (500, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_vap_dolphin")
    return tree, gin, gout

register_builder(
    "MEL_aest_vap_dolphin", build_aest_vap_dolphin_group,
    "Vap Dolphin", "Aesthetic effect pass (absorbed from monolith build_aest_vap_dolphin).",
    category="effects", role="modifier")


def build_aest_zen_bonsai_group(group_name="MEL_aest_zen_bonsai"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Recursive bezier branching: a tiny procedural bonsai growing from base."""
        in_geom = _get_input_geom(tree)
        intensity = _aest_val(P, 'INTENSITY')
        scale     = _aest_val(P, 'SCALE')
        pieces = []
        import math, random as _rnd
        _rnd.seed(P["seed"])
        # Trunk: bezier from origin up with slight curve
        trunk_top = 1.5 * intensity
        trunk = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (-400, 0))
        if trunk is None:
            return in_geom
        try:
            trunk.inputs['Resolution'].default_value = 32
            trunk.inputs['Start'].default_value  = (0, 0, 0)
            trunk.inputs['Middle'].default_value = (0.15 * scale, -0.1 * scale, trunk_top * 0.5)
            trunk.inputs['End'].default_value    = (0.05 * scale, -0.05 * scale, trunk_top)
        except Exception:
            return in_geom
        trunk_prof = _make_circle_profile(tree, 0.06 * scale, 8, loc=(-700, -200), P=P)
        sw_trunk = _sweep_curve(tree, trunk.outputs['Curve'],
                                trunk_prof.outputs['Curve'] if trunk_prof else None,
                                loc=(-100, 0), label="organic")
        if sw_trunk:
            pieces.append(sw_trunk)
        # Branches: a few bezier offshoots from the trunk
        branch_prof = _make_circle_profile(tree, 0.025 * scale, 6, loc=(-700, -500), P=P)
        n_branches = max(4, int(P["density"] * 6))
        for i in range(n_branches):
            ang = _rnd.uniform(0, 6.283185)
            rise = _rnd.uniform(0.35, 0.85) * trunk_top
            reach = _rnd.uniform(0.4, 0.8) * scale
            end_x = math.cos(ang) * reach
            end_y = math.sin(ang) * reach
            end_z = rise + _rnd.uniform(0.1, 0.4) * scale
            br = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier',
                            (-400, -300 - i * 100))
            if br is None:
                continue
            try:
                br.inputs['Resolution'].default_value = 16
                br.inputs['Start'].default_value  = (0, 0, rise)
                br.inputs['Middle'].default_value = (end_x * 0.5, end_y * 0.5, rise + 0.1)
                br.inputs['End'].default_value    = (end_x, end_y, end_z)
            except Exception:
                continue
            color_node(br, "organic")
            sw_br = _sweep_curve(tree, br.outputs['Curve'],
                                 branch_prof.outputs['Curve'] if branch_prof else None,
                                 loc=(-100, -300 - i * 100), label="organic")
            if sw_br:
                pieces.append(sw_br)
            # Leaf cluster = small subdivided icosphere at tip
            leaf = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (-400, -600 - i * 100))
            if leaf:
                leaf.inputs['Radius'].default_value = _rnd.uniform(0.08, 0.18) * scale
                leaf.inputs['Subdivisions'].default_value = 2
                t = _node(tree, 'GeometryNodeTransform', (-100, -600 - i * 100))
                t.inputs['Translation'].default_value = (end_x, end_y, end_z)
                _link(tree, leaf.outputs['Mesh'], t.inputs['Geometry'])
                color_node(leaf, "organic"); color_node(t, "organic")
                pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (400, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_zen_bonsai")
    return tree, gin, gout

register_builder(
    "MEL_aest_zen_bonsai", build_aest_zen_bonsai_group,
    "Zen Bonsai", "Aesthetic effect pass (absorbed from monolith build_aest_zen_bonsai).",
    category="effects", role="modifier")


def build_aest_spi_flower_group(group_name="MEL_aest_spi_flower"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Flower of Life: 7-19 overlapping bezier circles in hexagonal lattice."""
        in_geom = _get_input_geom(tree)
        scale     = _aest_val(P, 'SCALE')
        intensity = _aest_val(P, 'INTENSITY')
        pieces = []
        prof = _make_circle_profile(tree, 0.03 * scale, 6, loc=(-700, -800), P=P)
        R = 0.7 * scale  # circle radius
        # Hex lattice: 1 center, 6 around (ring 1), 12 around (ring 2)
        rings = max(1, min(3, P["layers"]))
        coords = [(0.0, 0.0)]
        import math
        for ring in range(1, rings + 1):
            n = 6 * ring
            for i in range(n):
                ang = (i / n) * 6.283185
                r = ring * R
                coords.append((math.cos(ang) * r, math.sin(ang) * r))
        for idx, (cx, cy) in enumerate(coords):
            circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                              (-400, -200 - idx * 60))
            if circ is None:
                continue
            try:
                circ.inputs['Radius'].default_value     = R
                circ.inputs['Resolution'].default_value = 32
            except Exception:
                continue
            sw = _sweep_curve(tree, circ.outputs['Curve'],
                              prof.outputs['Curve'] if prof else None,
                              loc=(-100, -200 - idx * 60), label="ornament")
            if sw:
                t = _node(tree, 'GeometryNodeTransform', (200, -200 - idx * 60))
                t.inputs['Translation'].default_value = (cx, cy, intensity * 0.05)
                t.inputs['Rotation'].default_value = (1.5708, 0, 0)
                _link(tree, sw, t.inputs['Geometry'])
                color_node(t, "ornament")
                pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (500, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_flower")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_flower", build_aest_spi_flower_group,
    "Spi Flower", "Aesthetic effect pass (absorbed from monolith build_aest_spi_flower).",
    category="effects", role="modifier")


def build_aest_spi_metatron_group(group_name="MEL_aest_spi_metatron"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Metatron's Cube: 13 spheres + lines connecting all pairs (sacred geometry)."""
        in_geom = _get_input_geom(tree)
        scale     = _aest_val(P, 'SCALE')
        intensity = _aest_val(P, 'INTENSITY')
        pieces = []
        import math
        # 13 node positions: 1 center, 6 inner ring, 6 outer ring
        R1 = 0.6 * scale; R2 = 1.2 * scale
        nodes = [(0.0, 0.0)]
        for i in range(6):
            ang = (i / 6) * 6.283185
            nodes.append((math.cos(ang) * R1, math.sin(ang) * R1))
        for i in range(6):
            ang = (i / 6) * 6.283185 + 0.5236  # offset by 30deg
            nodes.append((math.cos(ang) * R2, math.sin(ang) * R2))
        # Spheres at each node (icosphere - actual subdivided geometry)
        for idx, (x, y) in enumerate(nodes):
            sph = _safe_node(tree, 'GeometryNodeMeshIcoSphere',
                             (-400, -200 - idx * 70))
            if sph is None:
                continue
            sph.inputs['Radius'].default_value       = 0.07 * scale
            sph.inputs['Subdivisions'].default_value = 2
            t = _node(tree, 'GeometryNodeTransform', (-150, -200 - idx * 70))
            t.inputs['Translation'].default_value = (x, y, 0.05 * intensity)
            _link(tree, sph.outputs['Mesh'], t.inputs['Geometry'])
            color_node(sph, "ornament"); color_node(t, "ornament")
            pieces.append(t.outputs['Geometry'])
        # Connecting lines: every pair becomes a primitive line swept with thin tube
        prof = _make_circle_profile(tree, 0.012 * scale, 6, loc=(-700, -1500), P=P)
        # Limit pairs to keep node count reasonable
        line_idx = 0
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                line_idx += 1
                if line_idx > 30:  # cap pairs
                    break
                line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                                  (200, -200 - line_idx * 80))
                if line is None:
                    continue
                try:
                    line.inputs['Start'].default_value = (nodes[i][0], nodes[i][1], 0.05 * intensity)
                    line.inputs['End'].default_value   = (nodes[j][0], nodes[j][1], 0.05 * intensity)
                except Exception:
                    continue
                sw = _sweep_curve(tree, line.outputs['Curve'],
                                  prof.outputs['Curve'] if prof else None,
                                  loc=(500, -200 - line_idx * 80), label="tracery")
                if sw:
                    pieces.append(sw)
        join = _node(tree, 'GeometryNodeJoinGeometry', (1000, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    # ======================================================================
    # v2.19 - Mechanical aesthetic effects
    # ======================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_spi_metatron")
    return tree, gin, gout

register_builder(
    "MEL_aest_spi_metatron", build_aest_spi_metatron_group,
    "Spi Metatron", "Aesthetic effect pass (absorbed from monolith build_aest_spi_metatron).",
    category="effects", role="modifier")


def build_aest_mech_bolts_group(group_name="MEL_aest_mech_bolts"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Distribute hex bolts (curve-filled+extruded) across the surface,
        gated by the user's vertex-group mask."""
        in_geom = _get_input_geom(tree)
        scale = _aest_val(P, 'SCALE')
        density = _aest_val(P, 'DENSITY')
        mask = _aest_mask_field(tree, P, loc=(-900, 500))
        # Hex profile -> fill -> extrude -> bolt prism
        hex_c = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-800, -300))
        if hex_c:
            try:
                hex_c.inputs['Resolution'].default_value = 6
                hex_c.inputs['Radius'].default_value     = 0.06 * scale
            except Exception:
                pass
            color_node(hex_c, "modular")
        fill = _safe_node(tree, 'GeometryNodeFillCurve', (-550, -300))
        if fill and hex_c:
            try: fill.mode = 'NGONS'
            except Exception: pass
            _link(tree, hex_c.outputs['Curve'], fill.inputs['Curve'])
        ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (-300, -300))
        if ext and fill:
            ext.mode = 'FACES'
            ext.inputs['Offset Scale'].default_value = 0.05 * scale
            _link(tree, fill.outputs['Mesh'], ext.inputs['Mesh'])
            color_node(ext, "modular")
        bolt_mesh = ext.outputs['Mesh'] if ext else (fill.outputs['Mesh'] if fill else None)
        # Distribute on input faces, density modulated by mask
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (-100, 0))
        if pts and in_geom:
            pts.distribute_method = 'POISSON'
            pts.inputs['Distance Min'].default_value = 0.4 / max(0.1, density)
            mul_d = _node(tree, 'ShaderNodeMath', (-300, 200))
            mul_d.operation = 'MULTIPLY'
            mul_d.inputs[0].default_value = density * 2.0
            _link(tree, mask, mul_d.inputs[1])
            _link(tree, mul_d.outputs['Value'], pts.inputs['Density Max'])
            pts.inputs['Seed'].default_value = P["seed"]
            _link(tree, in_geom, pts.inputs['Mesh'])
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (200, 0))
        if inst and pts and bolt_mesh:
            _link(tree, pts.outputs['Points'], inst.inputs['Points'])
            _link(tree, bolt_mesh, inst.inputs['Instance'])
            try: _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
            except Exception: pass
            color_node(inst, "modular")
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (500, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, real.outputs['Geometry'] if real else None)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mech_bolts")
    return tree, gin, gout

register_builder(
    "MEL_aest_mech_bolts", build_aest_mech_bolts_group,
    "Mech Bolts", "Aesthetic effect pass (absorbed from monolith build_aest_mech_bolts).",
    category="effects", role="modifier")


def build_aest_mech_pipes_group(group_name="MEL_aest_mech_pipes"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Bezier-arc pipe network with flange torus rings at each end."""
        in_geom = _get_input_geom(tree)
        scale = _aest_val(P, 'SCALE')
        density = _aest_val(P, 'DENSITY')
        intensity = _aest_val(P, 'INTENSITY')
        pieces = []
        import math, random as _rnd
        _rnd.seed(P["seed"])
        prof = _make_circle_profile(tree, 0.05 * scale, 12, loc=(-700, -1500), P=P)
        n = max(3, int(density * 6))
        R = 1.6 * scale
        for i in range(n):
            a, b = _rnd.uniform(0, 6.28), _rnd.uniform(0, 6.28)
            za, zb = _rnd.uniform(0.2, 1.0) * intensity, _rnd.uniform(1.0, 2.4) * intensity
            sa = (math.cos(a) * R, math.sin(a) * R, za)
            eb = (math.cos(b) * R, math.sin(b) * R, zb)
            ma = (a + b) * 0.5
            mid = (math.cos(ma) * R * 1.35, math.sin(ma) * R * 1.35, (za + zb) * 0.5 + 0.4)
            qb = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (-400, -200 - i * 150))
            if qb is None:
                continue
            try:
                qb.inputs['Resolution'].default_value = 32
                qb.inputs['Start'].default_value  = sa
                qb.inputs['Middle'].default_value = mid
                qb.inputs['End'].default_value    = eb
            except Exception:
                continue
            color_node(qb, "modular")
            sw = _sweep_curve(tree, qb.outputs['Curve'],
                              prof.outputs['Curve'] if prof else None,
                              loc=(-100, -200 - i * 150), label="modular")
            if sw: pieces.append(sw)
            # Flanges (torus rings) at both ends
            for (px, py, pz) in (sa, eb):
                tor = _safe_node(tree, 'GeometryNodeMeshTorus', (200, -200 - i * 150))
                if tor is None:
                    continue
                try:
                    tor.inputs['Major Radius'].default_value = 0.09 * scale
                    tor.inputs['Minor Radius'].default_value = 0.025 * scale
                    tor.inputs['Major Segments'].default_value = 16
                    tor.inputs['Minor Segments'].default_value = 6
                except Exception:
                    continue
                t = _node(tree, 'GeometryNodeTransform', (400, -200 - i * 150))
                t.inputs['Translation'].default_value = (px, py, pz)
                _link(tree, tor.outputs['Mesh'], t.inputs['Geometry'])
                color_node(tor, "modular"); color_node(t, "modular")
                pieces.append(t.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (700, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mech_pipes")
    return tree, gin, gout

register_builder(
    "MEL_aest_mech_pipes", build_aest_mech_pipes_group,
    "Mech Pipes", "Aesthetic effect pass (absorbed from monolith build_aest_mech_pipes).",
    category="effects", role="modifier")


def build_aest_mech_gears_group(group_name="MEL_aest_mech_gears"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Gear-cog instances: extruded circle body + ring of tooth cubes via Curve to Points."""
        in_geom = _get_input_geom(tree)
        scale = _aest_val(P, 'SCALE')
        density = _aest_val(P, 'DENSITY')
        mask = _aest_mask_field(tree, P, loc=(-900, 500))
        # Body
        body_c = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-800, -200))
        if body_c:
            try:
                body_c.inputs['Resolution'].default_value = 32
                body_c.inputs['Radius'].default_value = 0.18 * scale
            except Exception:
                pass
            color_node(body_c, "modular")
        body_fill = _safe_node(tree, 'GeometryNodeFillCurve', (-600, -200))
        if body_fill and body_c:
            _link(tree, body_c.outputs['Curve'], body_fill.inputs['Curve'])
        body_ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (-400, -200))
        if body_ext and body_fill:
            body_ext.mode = 'FACES'
            body_ext.inputs['Offset Scale'].default_value = 0.08 * scale
            _link(tree, body_fill.outputs['Mesh'], body_ext.inputs['Mesh'])
            color_node(body_ext, "modular")
        # Teeth
        tooth_ring = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-800, -450))
        if tooth_ring:
            try:
                tooth_ring.inputs['Resolution'].default_value = 12
                tooth_ring.inputs['Radius'].default_value = 0.20 * scale
            except Exception:
                pass
        tooth = _node(tree, 'GeometryNodeMeshCube', (-800, -650))
        tooth.inputs['Size'].default_value = (0.06 * scale, 0.04 * scale, 0.08 * scale)
        c2p = _safe_node(tree, 'GeometryNodeCurveToPoints', (-550, -450))
        if c2p and tooth_ring:
            try: c2p.mode = 'EVALUATED'
            except Exception: pass
            _link(tree, tooth_ring.outputs['Curve'], c2p.inputs['Curve'])
        t_inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (-300, -450))
        if t_inst and c2p:
            _link(tree, c2p.outputs['Points'], t_inst.inputs['Points'])
            _link(tree, tooth.outputs['Mesh'], t_inst.inputs['Instance'])
            try: _link(tree, c2p.outputs['Rotation'], t_inst.inputs['Rotation'])
            except Exception: pass
        t_real = _safe_node(tree, 'GeometryNodeRealizeInstances', (-100, -450))
        if t_real and t_inst:
            _link(tree, t_inst.outputs['Instances'], t_real.inputs['Geometry'])
        # Combine
        gear_join = _node(tree, 'GeometryNodeJoinGeometry', (100, -300))
        if body_ext:
            _link(tree, body_ext.outputs['Mesh'], gear_join.inputs['Geometry'])
        if t_real:
            _link(tree, t_real.outputs['Geometry'], gear_join.inputs['Geometry'])
        color_node(gear_join, "modular")
        # Distribute gear unit on faces
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (300, 0))
        if pts and in_geom:
            pts.distribute_method = 'POISSON'
            pts.inputs['Distance Min'].default_value = 0.7 / max(0.1, density)
            mul_d = _node(tree, 'ShaderNodeMath', (100, 200))
            mul_d.operation = 'MULTIPLY'
            mul_d.inputs[0].default_value = density * 1.0
            _link(tree, mask, mul_d.inputs[1])
            _link(tree, mul_d.outputs['Value'], pts.inputs['Density Max'])
            pts.inputs['Seed'].default_value = P["seed"]
            _link(tree, in_geom, pts.inputs['Mesh'])
        g_inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (600, 0))
        if g_inst and pts:
            _link(tree, pts.outputs['Points'], g_inst.inputs['Points'])
            _link(tree, gear_join.outputs['Geometry'], g_inst.inputs['Instance'])
            try: _link(tree, pts.outputs['Normal'], g_inst.inputs['Rotation'])
            except Exception: pass
        g_real = _safe_node(tree, 'GeometryNodeRealizeInstances', (900, 0))
        if g_real and g_inst:
            _link(tree, g_inst.outputs['Instances'], g_real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, g_real.outputs['Geometry'] if g_real else None)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mech_gears")
    return tree, gin, gout

register_builder(
    "MEL_aest_mech_gears", build_aest_mech_gears_group,
    "Mech Gears", "Aesthetic effect pass (absorbed from monolith build_aest_mech_gears).",
    category="effects", role="modifier")


def build_aest_mech_pistons_group(group_name="MEL_aest_mech_pistons"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Pistons: thin shaft line swept thin + thick bell line swept thick."""
        in_geom = _get_input_geom(tree)
        scale = _aest_val(P, 'SCALE')
        intensity = _aest_val(P, 'INTENSITY')
        density = _aest_val(P, 'DENSITY')
        pieces = []
        import math
        n = max(3, int(density * 6))
        R = 1.6 * scale
        prof_thin  = _make_circle_profile(tree, 0.05 * scale, 12, loc=(-700, -1200), P=P)
        prof_thick = _make_circle_profile(tree, 0.13 * scale, 16, loc=(-700, -1400), P=None)
        for i in range(n):
            ang = (i / n) * 6.283185
            cx = math.cos(ang) * R
            cy = math.sin(ang) * R
            line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (-400, -200 - i * 200))
            if line is None: continue
            try:
                line.inputs['Start'].default_value = (cx, cy, 0.0)
                line.inputs['End'].default_value   = (cx * 0.4, cy * 0.4, 1.4 * intensity)
            except Exception:
                continue
            sw_shaft = _sweep_curve(tree, line.outputs['Curve'],
                                    prof_thin.outputs['Curve'] if prof_thin else None,
                                    loc=(-100, -200 - i * 200), label="modular")
            if sw_shaft: pieces.append(sw_shaft)
            bell_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (-400, -350 - i * 200))
            if bell_line is None: continue
            try:
                bell_line.inputs['Start'].default_value = (cx, cy, -0.18 * scale)
                bell_line.inputs['End'].default_value   = (cx, cy, 0.15 * scale)
            except Exception:
                continue
            sw_bell = _sweep_curve(tree, bell_line.outputs['Curve'],
                                   prof_thick.outputs['Curve'] if prof_thick else None,
                                   loc=(-100, -350 - i * 200), label="modular")
            if sw_bell: pieces.append(sw_bell)
        join = _node(tree, 'GeometryNodeJoinGeometry', (300, 0))
        if in_geom:
            _link(tree, in_geom, join.inputs['Geometry'])
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mech_pistons")
    return tree, gin, gout

register_builder(
    "MEL_aest_mech_pistons", build_aest_mech_pistons_group,
    "Mech Pistons", "Aesthetic effect pass (absorbed from monolith build_aest_mech_pistons).",
    category="effects", role="modifier")




def build_aest_mech_panels_group(group_name="MEL_aest_mech_panels"):
    tree, gin, gout = new_geometry_tree(group_name)
    _add_aesthetic_params(tree)
    P = dict(DEFAULT_PARAMS)
    def _impl():
        """Industrial panel inserts: rectangle curve -> fill -> extrude, distributed on faces."""
        in_geom = _get_input_geom(tree)
        scale = _aest_val(P, 'SCALE')
        density = _aest_val(P, 'DENSITY')
        mask = _aest_mask_field(tree, P, loc=(-900, 500))
        rect_c = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-800, -200))
        if rect_c:
            try:
                rect_c.inputs['Resolution'].default_value = 4
                rect_c.inputs['Radius'].default_value = 0.22 * scale
            except Exception:
                pass
            rtr = _node(tree, 'GeometryNodeTransform', (-600, -200))
            rtr.inputs['Scale'].default_value = (1.0, 0.55, 1.0)
            rtr.inputs['Rotation'].default_value = (0, 0, 0.7854)
            _link(tree, rect_c.outputs['Curve'], rtr.inputs['Geometry'])
            color_node(rect_c, "modular"); color_node(rtr, "modular")
        fill = _safe_node(tree, 'GeometryNodeFillCurve', (-400, -200))
        if fill and rect_c:
            try: fill.mode = 'NGONS'
            except Exception: pass
            _link(tree, rtr.outputs['Geometry'], fill.inputs['Curve'])
        ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (-200, -200))
        if ext and fill:
            ext.mode = 'FACES'
            ext.inputs['Offset Scale'].default_value = 0.04 * scale
            _link(tree, fill.outputs['Mesh'], ext.inputs['Mesh'])
        panel_mesh = ext.outputs['Mesh'] if ext else (fill.outputs['Mesh'] if fill else None)
        pts = _safe_node(tree, 'GeometryNodeDistributePointsOnFaces', (0, 0))
        if pts and in_geom:
            pts.distribute_method = 'POISSON'
            pts.inputs['Distance Min'].default_value = 0.5 / max(0.1, density)
            mul_d = _node(tree, 'ShaderNodeMath', (-200, 200))
            mul_d.operation = 'MULTIPLY'
            mul_d.inputs[0].default_value = density * 1.2
            _link(tree, mask, mul_d.inputs[1])
            _link(tree, mul_d.outputs['Value'], pts.inputs['Density Max'])
            pts.inputs['Seed'].default_value = P["seed"]
            _link(tree, in_geom, pts.inputs['Mesh'])
        inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (300, 0))
        if inst and pts and panel_mesh:
            _link(tree, pts.outputs['Points'], inst.inputs['Points'])
            _link(tree, panel_mesh, inst.inputs['Instance'])
            try: _link(tree, pts.outputs['Normal'], inst.inputs['Rotation'])
            except Exception: pass
        real = _safe_node(tree, 'GeometryNodeRealizeInstances', (600, 0))
        if real and inst:
            _link(tree, inst.outputs['Instances'], real.inputs['Geometry'])
        return _join_with_input(tree, in_geom, real.outputs['Geometry'] if real else None)



    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_aest_mech_panels")
    return tree, gin, gout

register_builder(
    "MEL_aest_mech_panels", build_aest_mech_panels_group,
    "Mech Panels", "Aesthetic effect pass (absorbed from monolith build_aest_mech_panels).",
    category="effects", role="modifier")
# 70 builders registered
