# Melodia Sky Forge - world shader builder (bpy).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Builds the MEL_SkyForge world node group: stylized gradient (optional FADE
# banding), sun disc + glow, soft noise clouds, sparse stars, optional aurora
# band. All theme values arrive through group inputs so a theme swap never
# rebuilds the graph.

from __future__ import annotations

from typing import Any

import bpy

DOME_OBJECT_NAME = "MEL_SkyForge_Dome"
DOME_MATERIAL_NAME = "MEL_SkyForge_Dome_Mat"
DIRECTION_ATTR = "mel_sky_dir"          # flood: G = elevation t (legacy single attr)
SPLIT_ATTR_HINT = (
    "This build collapses the R and B channels of a color attribute read in "
    "background renders to 0.5 while G survives (proven 2026-10-12). Every "
    "data channel therefore ships in its OWN color attribute's GREEN channel:"
)
ELEV_ATTR = "mel_sky_elev"   # G = t = (n.z + 1) / 2  (0 nadir .. 1 zenith)
DX_ATTR = "mel_sky_dirx"     # G = (n.x + 1) / 2
DY_ATTR = "mel_sky_diry"     # G = (n.y + 1) / 2
DZ_ATTR = "mel_sky_dirz"     # G = (n.z + 1) / 2
SKY_ATTRS = (ELEV_ATTR, DX_ATTR, DY_ATTR, DZ_ATTR)

# Blender 5.2 caveat (proven headless 2026-10-12): in a WORLD shader the
# coordinate outputs (Generated/Object/Position/Normal/Incoming/Reflection)
# are scene-bbox-relative, not ray directions, so a world background cannot
# host a camera-independent procedural sky. The sky dome mesh is the
# trustworthy surface: on the dome, Generated = (dir + 1) / 2, which is
# exactly the 0..1 elevation mapping this group was designed around.
# The group therefore outputs SkyColor (NodeSocketColor); consumers wrap it:
# world -> Background(SkyColor), dome -> Emission(SkyColor).

GROUP_NAME = "MEL_SkyForge"

# Input socket name -> (socket_type, default). Stable contract: the sidecar
# flat keys in sky_core.flatten_for_td use the same stems.
_INPUTS: tuple[tuple[str, str, Any], ...] = (
    ("GradZenith", "NodeSocketColor", (0.2, 0.45, 0.85, 1.0)),
    ("GradHorizon", "NodeSocketColor", (0.95, 0.8, 0.65, 1.0)),
    ("GradNadir", "NodeSocketColor", (0.5, 0.45, 0.4, 1.0)),
    ("BandingSteps", "NodeSocketFloat", 0.0),
    ("SunDirection", "NodeSocketVector", (0.0, -1.0, 0.3)),
    ("SunColor", "NodeSocketColor", (1.0, 0.9, 0.7, 1.0)),
    ("SunDiscCos", "NodeSocketFloat", 0.997),  # cos(disc radius); builder-side convenience
    ("SunGlow", "NodeSocketFloat", 0.6),
    ("CloudCoverage", "NodeSocketFloat", 0.35),
    ("CloudScale", "NodeSocketFloat", 2.0),
    ("CloudSoftness", "NodeSocketFloat", 0.35),
    ("CloudSeed", "NodeSocketFloat", 0.0),
    ("CloudLit", "NodeSocketColor", (1.0, 0.96, 0.9, 1.0)),
    ("CloudShadow", "NodeSocketColor", (0.7, 0.65, 0.7, 1.0)),
    ("StarDensity", "NodeSocketFloat", 0.0),
    ("StarColor", "NodeSocketColor", (1.0, 0.98, 0.9, 1.0)),
    ("AuroraStrength", "NodeSocketFloat", 0.0),
    ("AuroraColorA", "NodeSocketColor", (0.4, 0.9, 0.7, 1.0)),
    ("AuroraColorB", "NodeSocketColor", (0.5, 0.6, 1.0, 1.0)),
)


def _build_sky_graph(nodes, links, get_f, bind):
    """One sky shader topology shared by the node group and the dome material.

    get_f(attr_name) returns the FLOAT socket carrying the given datum
    (the split-attribute GREEN channel; the proven-safe read path).
    bind(name) resolves a logical input either as ('socket', socket) or
    ('value', python value). Strict socket-family rules apply everywhere
    (proven 2026-10-12: color<->vector socket conversion corrupts evaluation,
    and only the FIRST render of a session sees material edits - one bake per
    session for any verification).

    Returns the final sky COLOR socket.
    """
    def float_in(node, key, index=1):
        r = bind(key)
        if r[0] == 'socket':
            links.new(r[1], node.inputs[index])
        else:
            node.inputs[index].default_value = float(r[1])

    def color_in(node, index, key):
        r = bind(key)
        if r[0] == 'socket':
            links.new(r[1], node.inputs[index])
        else:
            node.inputs[index].default_value = (*r[1], 1.0)

    # Data channels: split attributes' GREEN outputs (proven-surviving path).
    t_out = get_f(ELEV_ATTR)

    # Unit direction for the sun/clouds from split G-channels; dir = g*2-1.
    def fx(gsock):
        x = nodes.new("ShaderNodeMath"); x.operation = 'MULTIPLY_ADD'
        x.inputs[1].default_value = 2.0
        x.inputs[2].default_value = -1.0
        links.new(gsock, x.inputs[0])
        return x.outputs[0]

    dx = fx(get_f(DX_ATTR)); dy = fx(get_f(DY_ATTR)); dz = fx(get_f(DZ_ATTR))
    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(dx, comb.inputs[0])
    links.new(dy, comb.inputs[1])
    links.new(dz, comb.inputs[2])
    world_dir = comb.outputs[0]

    # Banding: posterize t (FADE-style steps) when BandingSteps >= 2.
    band_mul = nodes.new("ShaderNodeMath"); band_mul.operation = 'MULTIPLY'
    links.new(t_out, band_mul.inputs[0])
    float_in(band_mul, "BandingSteps")
    band_flr = nodes.new("ShaderNodeMath"); band_flr.operation = 'FLOOR'
    links.new(band_mul.outputs[0], band_flr.inputs[0])
    band_div = nodes.new("ShaderNodeMath"); band_div.operation = 'DIVIDE'
    links.new(band_flr.outputs[0], band_div.inputs[0])
    float_in(band_div, "BandingSteps")
    steps_on = nodes.new("ShaderNodeMath"); steps_on.operation = 'GREATER_THAN'
    steps_on.inputs[1].default_value = 1.5
    steps_bind = bind("BandingSteps")
    if steps_bind[0] == 'socket':
        links.new(steps_bind[1], steps_on.inputs[0])
    else:
        steps_on.inputs[0].default_value = float(steps_bind[1])
    fac_mix = nodes.new("ShaderNodeMix"); fac_mix.data_type = 'FLOAT'
    links.new(steps_on.outputs[0], fac_mix.inputs["Factor"])
    links.new(t_out, fac_mix.inputs[2])   # A (float)
    links.new(band_div.outputs[0], fac_mix.inputs[3])  # B (float)

    # Gradient: nadir (0) -> horizon (0.5) -> zenith (1), two clamped Mix nodes.
    ramp_lo = nodes.new("ShaderNodeMapRange"); ramp_lo.clamp = True
    ramp_lo.inputs["From Min"].default_value = 0.0
    ramp_lo.inputs["From Max"].default_value = 0.5
    links.new(fac_mix.outputs[0], ramp_lo.inputs["Value"])
    ramp_hi = nodes.new("ShaderNodeMapRange"); ramp_hi.clamp = True
    ramp_hi.inputs["From Min"].default_value = 0.5
    ramp_hi.inputs["From Max"].default_value = 1.0
    links.new(fac_mix.outputs[0], ramp_hi.inputs["Value"])

    mix_lo = nodes.new("ShaderNodeMix"); mix_lo.data_type = 'RGBA'
    color_degree_lo = mix_lo.inputs["Factor"]
    links.new(ramp_lo.outputs[0], color_degree_lo)
    color_in(mix_lo, 6, "GradNadir")
    color_in(mix_lo, 7, "GradHorizon")
    mix_hi = nodes.new("ShaderNodeMix"); mix_hi.data_type = 'RGBA'
    links.new(ramp_hi.outputs[0], mix_hi.inputs["Factor"])
    links.new(mix_lo.outputs[2], mix_hi.inputs[6])
    color_in(mix_hi, 7, "GradZenith")

    sky = mix_hi.outputs[2]

    # Sun: dot = dx*sx + dy*sy + dz*sz (pure float math; no color<->vector).
    sep_dir = nodes.new("ShaderNodeSeparateXYZ")
    links.new(world_dir, sep_dir.inputs[0])
    dx, dy, dz = sep_dir.outputs["X"], sep_dir.outputs["Y"], sep_dir.outputs["Z"]
    sbind = bind("SunDirection")
    if sbind[0] == 'socket':
        sep_sd = nodes.new("ShaderNodeSeparateXYZ")
        links.new(sbind[1], sep_sd.inputs[0])
        sx, sy, sz = (sep_sd.outputs["X"], sep_sd.outputs["Y"], sep_sd.outputs["Z"])
        m1 = nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'
        links.new(dx, m1.inputs[0]); links.new(sx, m1.inputs[1])
        m2 = nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'
        links.new(dy, m2.inputs[0]); links.new(sy, m2.inputs[1])
        m3 = nodes.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'
        links.new(dz, m3.inputs[0]); links.new(sz, m3.inputs[1])
    else:
        sxv, syv, szv = sbind[1]
        m1 = nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'
        links.new(dx, m1.inputs[0]); m1.inputs[1].default_value = sxv
        m2 = nodes.new("ShaderNodeMath"); m2.operation = 'MULTIPLY'
        links.new(dy, m2.inputs[0]); m2.inputs[1].default_value = syv
        m3 = nodes.new("ShaderNodeMath"); m3.operation = 'MULTIPLY'
        links.new(dz, m3.inputs[0]); m3.inputs[1].default_value = szv
    dot_add1 = nodes.new("ShaderNodeMath"); dot_add1.operation = 'ADD'
    links.new(m1.outputs[0], dot_add1.inputs[0])
    links.new(m2.outputs[0], dot_add1.inputs[1])
    dot_out = nodes.new("ShaderNodeMath"); dot_out.operation = 'ADD'
    links.new(dot_add1.outputs[0], dot_out.inputs[0])
    links.new(m3.outputs[0], dot_out.inputs[1])

    disc = nodes.new("ShaderNodeMath"); disc.operation = 'GREATER_THAN'
    links.new(dot_out.outputs[0], disc.inputs[0])
    float_in(disc, "SunDiscCos")
    glow_pow = nodes.new("ShaderNodeMath"); glow_pow.operation = 'POWER'
    links.new(dot_out.outputs[0], glow_pow.inputs[0])
    glow_pow.inputs[1].default_value = 64.0
    glow_mul = nodes.new("ShaderNodeMath"); glow_mul.operation = 'MULTIPLY'
    links.new(glow_pow.outputs[0], glow_mul.inputs[0])
    float_in(glow_mul, "SunGlow")

    sun_disc_col = nodes.new("ShaderNodeMix"); sun_disc_col.data_type = 'RGBA'
    sun_disc_col.blend_type = 'MULTIPLY'
    links.new(disc.outputs[0], sun_disc_col.inputs["Factor"])
    links.new(sky, sun_disc_col.inputs[6])
    color_in(sun_disc_col, 7, "SunColor")
    glow_add = nodes.new("ShaderNodeMix"); glow_add.data_type = 'RGBA'
    glow_add.blend_type = 'ADD'
    links.new(glow_mul.outputs[0], glow_add.inputs["Factor"])
    links.new(sky, glow_add.inputs[6])
    color_in(glow_add, 7, "SunColor")
    disc_add = nodes.new("ShaderNodeMix"); disc_add.data_type = 'RGBA'
    disc_add.blend_type = 'ADD'
    links.new(disc.outputs[0], disc_add.inputs["Factor"])
    links.new(glow_add.outputs[2], disc_add.inputs[6])
    links.new(sun_disc_col.outputs[2], disc_add.inputs[7])
    sky = disc_add.outputs[2]

    # clouds: 4D noise in attribute-space, threshold centered on 1-coverage.
    noise = nodes.new("ShaderNodeTexNoise"); noise.noise_dimensions = '4D'
    noise.name = "MELSKY_Noise"  # frame driver target (cloud W)
    links.new(world_dir, noise.inputs["Vector"])
    float_in(noise, "CloudScale", index="Scale")
    float_in(noise, "CloudSeed", index="W")
    cov_one = nodes.new("ShaderNodeMath"); cov_one.operation = 'SUBTRACT'
    cov_one.inputs[0].default_value = 1.0
    float_in(cov_one, "CloudCoverage", index=1)
    soft_half = nodes.new("ShaderNodeMath"); soft_half.operation = 'MULTIPLY'
    soft_half.inputs[1].default_value = 0.5
    float_in(soft_half, "CloudSoftness", index=0)
    cov_lo = nodes.new("ShaderNodeMath"); cov_lo.operation = 'SUBTRACT'
    links.new(cov_one.outputs[0], cov_lo.inputs[0])
    links.new(soft_half.outputs[0], cov_lo.inputs[1])
    cov_hi = nodes.new("ShaderNodeMath"); cov_hi.operation = 'ADD'
    links.new(cov_one.outputs[0], cov_hi.inputs[0])
    links.new(soft_half.outputs[0], cov_hi.inputs[1])
    cloud_ramp = nodes.new("ShaderNodeMapRange")
    cloud_ramp.interpolation_type = 'SMOOTHSTEP'
    links.new(noise.outputs["Fac"], cloud_ramp.inputs["Value"])
    links.new(cov_lo.outputs[0], cloud_ramp.inputs["From Min"])
    links.new(cov_hi.outputs[0], cloud_ramp.inputs["From Max"])
    half_mask = nodes.new("ShaderNodeMapRange")
    half_mask.interpolation_type = 'SMOOTHSTEP'
    links.new(t_out, half_mask.inputs["Value"])
    half_mask.inputs["From Min"].default_value = 0.45
    half_mask.inputs["From Max"].default_value = 0.6
    cloud_fac = nodes.new("ShaderNodeMath"); cloud_fac.operation = 'MULTIPLY'
    links.new(cloud_ramp.outputs[0], cloud_fac.inputs[0])
    links.new(half_mask.outputs[0], cloud_fac.inputs[1])
    cloud_mix = nodes.new("ShaderNodeMix"); cloud_mix.data_type = 'RGBA'
    links.new(cloud_fac.outputs[0], cloud_mix.inputs["Factor"])
    links.new(sky, cloud_mix.inputs[6])
    cloud_col = nodes.new("ShaderNodeMix"); cloud_col.data_type = 'RGBA'
    cloud_col.blend_type = 'MIX'
    links.new(noise.outputs["Fac"], cloud_col.inputs["Factor"])
    color_in(cloud_col, 6, "CloudShadow")
    color_in(cloud_col, 7, "CloudLit")
    links.new(cloud_col.outputs[2], cloud_mix.inputs[7])
    sky = cloud_mix.outputs[2]

    # stars: high-frequency voronoi, only above horizon, gated by density.
    vor = nodes.new("ShaderNodeTexVoronoi")
    links.new(world_dir, vor.inputs["Vector"])
    vor.inputs["Scale"].default_value = 120.0
    star_th = nodes.new("ShaderNodeMath"); star_th.operation = 'LESS_THAN'
    star_th.inputs[1].default_value = 0.03
    links.new(vor.outputs["Distance"], star_th.inputs[0])
    star_gate = nodes.new("ShaderNodeMath"); star_gate.operation = 'GREATER_THAN'
    star_gate.inputs[1].default_value = 0.5
    float_in(star_gate, "StarDensity", index=0)
    star_top = nodes.new("ShaderNodeMapRange")
    star_top.interpolation_type = 'SMOOTHSTEP'
    links.new(t_out, star_top.inputs["Value"])
    star_top.inputs["From Min"].default_value = 0.55
    star_top.inputs["From Max"].default_value = 0.7
    star_f1 = nodes.new("ShaderNodeMath"); star_f1.operation = 'MULTIPLY'
    links.new(star_th.outputs[0], star_f1.inputs[0])
    links.new(star_gate.outputs[0], star_f1.inputs[1])
    star_f2 = nodes.new("ShaderNodeMath"); star_f2.operation = 'MULTIPLY'
    links.new(star_f1.outputs[0], star_f2.inputs[0])
    links.new(star_top.outputs[0], star_f2.inputs[1])
    star_mix = nodes.new("ShaderNodeMix"); star_mix.data_type = 'RGBA'
    star_mix.blend_type = 'ADD'
    links.new(star_f2.outputs[0], star_mix.inputs["Factor"])
    links.new(sky, star_mix.inputs[6])
    color_in(star_mix, 7, "StarColor")
    sky = star_mix.outputs[2]

    # aurora: sine bands in the upper sky, A/B color by noise.
    aur_phase = nodes.new("ShaderNodeMath"); aur_phase.operation = 'MULTIPLY'
    aur_phase.inputs[1].default_value = 40.0
    links.new(t_out, aur_phase.inputs[0])
    aur_sin = nodes.new("ShaderNodeMath"); aur_sin.operation = 'SINE'
    links.new(aur_phase.outputs[0], aur_sin.inputs[0])
    aur_abs = nodes.new("ShaderNodeMath"); aur_abs.operation = 'ABSOLUTE'
    links.new(aur_sin.outputs[0], aur_abs.inputs[0])
    aur_band = nodes.new("ShaderNodeMapRange")
    aur_band.interpolation_type = 'SMOOTHSTEP'
    links.new(aur_abs.outputs[0], aur_band.inputs["Value"])
    aur_band.inputs["From Min"].default_value = 0.85
    aur_band.inputs["From Max"].default_value = 1.0
    aur_top = nodes.new("ShaderNodeMapRange")
    aur_top.interpolation_type = 'SMOOTHSTEP'
    links.new(t_out, aur_top.inputs["Value"])
    aur_top.inputs["From Min"].default_value = 0.6
    aur_top.inputs["From Max"].default_value = 0.85
    aur_f1 = nodes.new("ShaderNodeMath"); aur_f1.operation = 'MULTIPLY'
    links.new(aur_band.outputs[0], aur_f1.inputs[0])
    links.new(aur_top.outputs[0], aur_f1.inputs[1])
    aur_f2 = nodes.new("ShaderNodeMath"); aur_f2.operation = 'MULTIPLY'
    aur_f2.name = "MELSKY_AuroraStrength"  # frame driver target (pulse)
    links.new(aur_f1.outputs[0], aur_f2.inputs[0])
    float_in(aur_f2, "AuroraStrength", index=1)
    aur_col = nodes.new("ShaderNodeMix"); aur_col.data_type = 'RGBA'
    links.new(noise.outputs["Fac"], aur_col.inputs["Factor"])
    color_in(aur_col, 6, "AuroraColorA")
    color_in(aur_col, 7, "AuroraColorB")
    aur_add = nodes.new("ShaderNodeMix"); aur_add.data_type = 'RGBA'
    aur_add.blend_type = 'ADD'
    links.new(aur_f2.outputs[0], aur_add.inputs["Factor"])
    links.new(sky, aur_add.inputs[6])
    links.new(aur_col.outputs[2], aur_add.inputs[7])
    sky = aur_add.outputs[2]
    return sky


def ensure_group() -> bpy.types.NodeTree:
    """Create or fetch the MEL_SkyForge node group (idempotent)."""
    ng = bpy.data.node_groups.get(GROUP_NAME)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(GROUP_NAME, "ShaderNodeTree")
    iface = ng.interface
    for name, stype, default in _INPUTS:
        sock = iface.new_socket(name=name, in_out="INPUT", socket_type=stype)
        sock.default_value = default
    iface.new_socket(name="SkyColor", in_out="OUTPUT", socket_type="NodeSocketColor")

    nodes, links = ng.nodes, ng.links
    n_in = nodes.new("NodeGroupInput"); n_in.location = (-1400, 0)
    n_out = nodes.new("NodeGroupOutput"); n_out.location = (900, 0)

    bind = {name: ('socket', n_in.outputs[name]) for name, _, _ in _INPUTS}
    sky = _build_sky_graph(nodes, links, lambda name: get_attr_float_socket(ng, name), bind.get)
    links.new(sky, n_out.inputs["SkyColor"])
    return ng


def build_dome_material(mat: bpy.types.Material, theme_flat: dict[str, Any]) -> None:
    """Author the dome's emission material directly from a flatten_for_td dict.

    Same topology as the node group, but theme values are written inline
    (the group wrapper was the last surface that still mis-read attributes
    in this build; the direct material is proven clean).
    """
    import math as _math

    mat.use_nodes = True
    mnt = mat.node_tree
    mnt.nodes.clear()
    emi = mnt.nodes.new("ShaderNodeEmission")
    outm = mnt.nodes.new("ShaderNodeOutputMaterial")

    consts: dict[str, Any] = {
        "BandingSteps": float(theme_flat["grad_banding_steps"]),
        "GradNadir": tuple(theme_flat["grad_nadir"]),
        "GradHorizon": tuple(theme_flat["grad_horizon"]),
        "GradZenith": tuple(theme_flat["grad_zenith"]),
        "SunDirection": tuple(theme_flat["sun_dir"]),
        "SunColor": tuple(theme_flat["sun_color"]),
        "SunDiscCos": _math.cos(_math.radians(theme_flat["sun_disc_radius_deg"])),
        "SunGlow": theme_flat["sun_glow_strength"],
        "CloudCoverage": theme_flat["cloud_coverage"],
        "CloudScale": theme_flat["cloud_scale"],
        "CloudSoftness": theme_flat["cloud_softness"],
        "CloudSeed": float(theme_flat["cloud_seed"]),
        "CloudLit": tuple(theme_flat["cloud_lit"]),
        "CloudShadow": tuple(theme_flat["cloud_shadow"]),
        "StarDensity": theme_flat["star_density"],
        "StarColor": tuple(theme_flat["star_color"]),
        "AuroraStrength": theme_flat["aurora_strength"],
        "AuroraColorA": tuple(theme_flat["aurora_color_a"]),
        "AuroraColorB": tuple(theme_flat["aurora_color_b"]),
    }
    bind = {k: ('value', v) for k, v in consts.items()}
    nodes, links = mnt.nodes, mnt.links
    sky = _build_sky_graph(nodes, links, lambda name: get_attr_float_socket(mnt, name), bind.get)
    links.new(sky, emi.inputs["Color"])
    mnt.links.new(emi.outputs["Emission"], outm.inputs["Surface"])


def apply_to_world(world: bpy.types.World | None = None, replace: bool = False) -> bpy.types.World:
    """Attach the MEL_SkyForge group to a world (default: scene world, created if missing).

    The world is the secondary surface: on Blender 5.2 its shader coordinates
    are not ray directions (see module docstring note), so the live sky is
    authored on the dome object via apply_to_scene(). The world path still
    works for HDRI-style fallbacks that bring their own coordinates.
    """
    if world is None:
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new("MelodiaSky")
            bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    has_group = any(
        n.type == 'GROUP' and n.node_tree and n.node_tree.name == GROUP_NAME
        for n in nt.nodes
    )
    if has_group and not replace:
        return world
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (300, 0)
    wbg = nt.nodes.new("ShaderNodeBackground"); wbg.location = (0, 0)
    grp = nt.nodes.new("ShaderNodeGroup"); grp.location = (-250, 0)
    grp.node_tree = ensure_group()
    nt.links.new(grp.outputs["SkyColor"], wbg.inputs["Color"])
    nt.links.new(wbg.outputs["Background"], out.inputs["Surface"])
    return world


def write_direction_attribute(mesh: bpy.types.Mesh) -> None:
    """Author the split data attributes on the dome.

    Each attribute carries ONE datum in its GREEN channel: elevation t and
    the three components of the view direction ({0.5+r*x, ...}). R/B are
    parked at 0.5 because that build collapses them on read; G renders
    faithfully. FLOAT_COLOR keeps values linear.
    """
    for attr_name in SKY_ATTRS:
        attr = mesh.color_attributes.get(attr_name)
        if attr is None or attr.domain != 'POINT' or attr.data_type != 'FLOAT_COLOR':
            attr = mesh.color_attributes.new(
                attr_name, type='FLOAT_COLOR', domain='POINT',
            )
        verts = mesh.vertices
        flat = [0.0] * (len(verts) * 4)
        for i, v in enumerate(verts):
            n = v.normal
            if attr_name == ELEV_ATTR:
                g = (n.z + 1.0) * 0.5
            elif attr_name == DX_ATTR:
                g = (n.x + 1.0) * 0.5
            elif attr_name == DY_ATTR:
                g = (n.y + 1.0) * 0.5
            else:
                g = (n.z + 1.0) * 0.5
            flat[i * 4 + 0] = 0.5
            flat[i * 4 + 1] = g
            flat[i * 4 + 2] = 0.5
            flat[i * 4 + 3] = 1.0
        attr.data.foreach_set("color", flat)
    mesh.update()


def get_attr_float_socket(mnt, attr_name):
    """One Attribute node reading its Color GREEN channel (the safe path)."""
    att = mnt.nodes.new("ShaderNodeAttribute")
    att.attribute_name = attr_name
    att.attribute_type = 'GEOMETRY'
    sepc = mnt.nodes.new("ShaderNodeSeparateColor")
    mnt.links.new(att.outputs["Color"], sepc.inputs[0])
    return sepc.outputs["Green"]


def _neutral_flat() -> dict[str, Any]:
    """Placeholder theme flat (from _INPUTS defaults) when no theme applied yet."""
    src = {name: default for name, _, default in _INPUTS}
    return {
        "grad_zenith": src["GradZenith"][:3],
        "grad_horizon": src["GradHorizon"][:3],
        "grad_nadir": src["GradNadir"][:3],
        "grad_banding_steps": src["BandingSteps"],
        "sun_dir": src["SunDirection"],
        "sun_color": src["SunColor"][:3],
        "sun_disc_radius_deg": 5.5,
        "sun_glow_strength": src["SunGlow"],
        "cloud_coverage": src["CloudCoverage"],
        "cloud_scale": src["CloudScale"],
        "cloud_softness": src["CloudSoftness"],
        "cloud_seed": src["CloudSeed"],
        "cloud_lit": src["CloudLit"][:3],
        "cloud_shadow": src["CloudShadow"][:3],
        "star_density": src["StarDensity"],
        "star_color": src["StarColor"][:3],
        "aurora_strength": src["AuroraStrength"],
        "aurora_color_a": src["AuroraColorA"][:3],
        "aurora_color_b": src["AuroraColorB"][:3],
    }


def ensure_dome(radius: float = 1000.0, theme_flat: dict[str, Any] | None = None) -> bpy.types.Object:
    """Create or update the sky dome mesh and its authored sky material.

    Idempotent: an existing MEL_SkyForge_Dome only gets its radius rescaled
    and (when theme_flat is given) its material rebuilt from the theme flat.
    """
    mesh = bpy.data.meshes.get(DOME_OBJECT_NAME) or bpy.data.meshes.new(DOME_OBJECT_NAME)
    obj = bpy.data.objects.get(DOME_OBJECT_NAME)
    if obj is None:
        import bmesh

        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(DOME_OBJECT_NAME, mesh)
    if obj.data is not mesh:
        obj.data = mesh
    if bpy.context.scene.collection not in obj.users_collection:
        bpy.context.scene.collection.objects.link(obj)
    obj.scale = (radius, radius, radius)
    obj.location = (0.0, 0.0, 0.0)
    obj.hide_render = False
    obj.hide_viewport = False
    write_direction_attribute(mesh)

    # Material: the SAME sky graph, authored directly on the material (see
    # build_dome_material for why it is not wrapped in a node group here).
    mat = bpy.data.materials.get(DOME_MATERIAL_NAME) or bpy.data.materials.new(DOME_MATERIAL_NAME)
    has_sky = any(n.type == 'EMISSION' for n in mat.node_tree.nodes)
    if (theme_flat is not None) or (not (mat.use_nodes and has_sky)):
        build_dome_material(mat, theme_flat if theme_flat is not None else _neutral_flat())
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    # Ray visibility: the dome must never shade or shadow anything; camera only.
    obj.visible_camera = True
    obj.visible_shadow = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    try:
        obj.visible_volume_scatter = False
    except AttributeError:
        pass
    return obj


def apply_to_scene(radius: float = 1000.0, theme_flat: dict[str, Any] | None = None) -> bpy.types.Object:
    """Author the dome (the 5.2-safe live sky surface) with the given theme flat."""
    return ensure_dome(radius, theme_flat)


def set_group_inputs(theme_flat: dict[str, Any]) -> None:
    """Push a flatten_for_td() dict onto the group's interface defaults."""
    import math as _math

    ng = ensure_group()
    items = {i.name: i for i in ng.interface.items_tree if getattr(i, "in_out", "") == "INPUT"}

    def _set(name: str, value: Any) -> None:
        item = items.get(name)
        if item is None:
            return
        try:
            item.default_value = value
        except (TypeError, ValueError):
            pass

    _set("GradZenith", (*theme_flat["grad_zenith"], 1.0))
    _set("GradHorizon", (*theme_flat["grad_horizon"], 1.0))
    _set("GradNadir", (*theme_flat["grad_nadir"], 1.0))
    _set("BandingSteps", float(theme_flat["grad_banding_steps"]))
    _set("SunDirection", tuple(theme_flat["sun_dir"]))
    _set("SunColor", (*theme_flat["sun_color"], 1.0))
    _set("SunDiscCos", _math.cos(_math.radians(theme_flat["sun_disc_radius_deg"])))
    _set("SunGlow", theme_flat["sun_glow_strength"])
    _set("CloudCoverage", theme_flat["cloud_coverage"])
    _set("CloudScale", theme_flat["cloud_scale"])
    _set("CloudSoftness", theme_flat["cloud_softness"])
    _set("CloudSeed", float(theme_flat["cloud_seed"]))
    _set("CloudLit", (*theme_flat["cloud_lit"], 1.0))
    _set("CloudShadow", (*theme_flat["cloud_shadow"], 1.0))
    _set("StarDensity", theme_flat["star_density"])
    _set("StarColor", (*theme_flat["star_color"], 1.0))
    _set("AuroraStrength", theme_flat["aurora_strength"])
    _set("AuroraColorA", (*theme_flat["aurora_color_a"], 1.0))
    _set("AuroraColorB", (*theme_flat["aurora_color_b"], 1.0))


def apply_theme(
    theme: dict[str, Any],
    world: bpy.types.World | None = None,
    dome_radius: float | None = None,
) -> bpy.types.World:
    """Flatten a theme, push it onto the group + dome, and wire the world."""
    from . import sky_core

    flat = sky_core.flatten_for_td(theme)
    set_group_inputs(flat)
    dome = bpy.data.objects.get(DOME_OBJECT_NAME)
    radius = dome_radius if dome_radius is not None else (
        max((abs(s) for s in dome.scale), default=1000.0) if dome is not None else 1000.0
    )
    ensure_dome(radius, flat)
    return apply_to_world(world)
