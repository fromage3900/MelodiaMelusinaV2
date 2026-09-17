"""brooch_sky.py — Melusina Sky v3: editorial gradient + glow + stars + clouds + aurora + grain.

Spec: Saved/Accessories/brooch_lab/MELUSINA_SKY_SHADER_PLAN_2026-09-17.md (sections 4, 5, 7).
v3 stack: L0 base gradient, L1 horizon glow, L4 stars (Voronoi crush + brightness variance +
zenith concentration), L3 cloud band (3D noise x height mask, occludes stars), L5 aurora
(streak noise x soft upper falloff, emissive-only), L6 grain, L7 strength trim. Carriers: world
(reflections/lighting) + the PRES_Back card (visible pixels). Every layer is a Mix with a zeroable
factor: editorial_dark (clouds 0, stars 0, aurora 0) reproduces the v1 look exactly.
Variant selection: `--sky <name>` > genome (compose_style / gems.material_a via sky_for_genome) >
editorial_dark (plan 3.3).

Contract: idempotent, regenerated per run, never saved into the working file by itself.
No texture nodes. No SceneTime (stills are deterministic). Node budget <= 60 per tree.

Deviations from the plan sketch (noted): the L1 glow mask feeds mapped Z straight into its
ColorRamp (a Gradient node adds nothing on a scalar); stars composite BEFORE clouds so dense cloud
occludes them (plan 2.4's cited technique); star coordinates are the carrier coordinate scaled 18x
(consistent between background and reflections) rather than Window space (the plan's alternative
for camera-locked stills).

Usage standalone:  blender -b FlowerBrooch.blend --python Tools/brooch_sky.py -- --sky tide
Via the rig:       brooch_pres_rig.py imports this and calls apply_sky(scene, variant=...).
"""
import bpy
import sys

# ---------------------------------------------------------------- presets ----
# Linear (scene) triples: zenith / horizon / ground; glow = the horizon band colour.
# editorial_dark is fully authored; the element rows are FIRST-PASS (the plan tunes them in v3).
SKY_PRESETS = {
    "editorial_dark": dict(
        zenith=(0.0035, 0.0045, 0.0070), horizon=(0.010, 0.013, 0.022),
        ground=(0.0015, 0.0020, 0.0030), glow=(0.012, 0.013, 0.020),
        horizon_glow=0.45, band_contrast=0.10, cloud_coverage=0.0, cloud_height=0.55,
        star_density=0.0, star_brightness=0.35, aurora_strength=0.0, grain=0.0035,
        sky_strength=0.35, seed=17),
    "forte": dict(
        zenith=(0.006, 0.0035, 0.0030), horizon=(0.030, 0.011, 0.006),
        ground=(0.003, 0.0015, 0.0012), glow=(0.036, 0.014, 0.008),
        horizon_glow=0.60, band_contrast=0.30, cloud_coverage=0.25, cloud_height=0.55,
        star_density=0.0, star_brightness=0.35, aurora_strength=0.0, grain=0.0040,
        sky_strength=0.45, seed=23),
    "radiant": dict(
        zenith=(0.010, 0.013, 0.022), horizon=(0.10, 0.085, 0.055),
        ground=(0.004, 0.004, 0.006), glow=(0.055, 0.085, 0.115),
        horizon_glow=0.85, band_contrast=0.55, cloud_coverage=0.35, cloud_height=0.55,
        star_density=0.30, star_brightness=0.35, aurora_strength=0.0, grain=0.0030,
        sky_strength=0.80, seed=31),
    "arcane": dict(
        zenith=(0.005, 0.004, 0.009), horizon=(0.022, 0.016, 0.040),
        ground=(0.002, 0.0015, 0.004), glow=(0.030, 0.024, 0.058),
        horizon_glow=0.50, band_contrast=0.35, cloud_coverage=0.0, cloud_height=0.55,
        star_density=0.45, star_brightness=0.40, aurora_strength=0.0, grain=0.0045,
        sky_strength=0.55, seed=41),
    "tide": dict(
        zenith=(0.004, 0.007, 0.014), horizon=(0.014, 0.024, 0.045),
        ground=(0.002, 0.003, 0.006), glow=(0.020, 0.034, 0.060),
        horizon_glow=0.55, band_contrast=0.25, cloud_coverage=0.30, cloud_height=0.55,
        star_density=0.15, star_brightness=0.35, aurora_strength=0.0, grain=0.0035,
        sky_strength=0.55, seed=53),
    "stone": dict(
        zenith=(0.008, 0.007, 0.006), horizon=(0.030, 0.024, 0.016),
        ground=(0.003, 0.003, 0.0025), glow=(0.038, 0.030, 0.020),
        horizon_glow=0.65, band_contrast=0.45, cloud_coverage=0.20, cloud_height=0.55,
        star_density=0.0, star_brightness=0.35, aurora_strength=0.0, grain=0.0040,
        sky_strength=0.50, seed=61),
    "gale": dict(
        zenith=(0.005, 0.006, 0.009), horizon=(0.016, 0.020, 0.030),
        ground=(0.002, 0.0025, 0.0035), glow=(0.022, 0.028, 0.042),
        horizon_glow=0.50, band_contrast=0.30, cloud_coverage=0.45, cloud_height=0.55,
        star_density=0.20, star_brightness=0.35, aurora_strength=0.25, grain=0.0045,
        sky_strength=0.55, seed=71),
    "umbral": dict(
        zenith=(0.0015, 0.0015, 0.0025), horizon=(0.006, 0.008, 0.012),
        ground=(0.001, 0.001, 0.0015), glow=(0.010, 0.016, 0.022),
        horizon_glow=0.70, band_contrast=0.40, cloud_coverage=0.15, cloud_height=0.55,
        star_density=0.55, star_brightness=0.30, aurora_strength=0.35, grain=0.0030,
        sky_strength=0.65, seed=83),
}

CARD_MAT = "SKY_Card_Mat"
WORLD_NAME = "SKY_Melusina"

_LAYERS = ("L0 base gradient", "L1 horizon glow", "L4 stars", "L3 cloud band", "L5 aurora",
           "L6 grain", "L7 strength trim")

# ---------------------------------------------------------------- genome map ----
GENOME_DIR = r"P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/brooch_lab/genome"

GENOME_VARIANT = {
    "BROOCH_GALA_TIDE": "tide", "BROOCH_GALA_UMBRA": "umbral",
    "BROOCH_GALA_FORTE": "forte", "BROOCH_GALA_RADIANT": "radiant",
    "BROOCH_GALA_ARCANE": "arcane", "BROOCH_GALA_STONE": "stone",
    "BROOCH_GALA_GALE": "gale",
}
MATERIAL_VARIANT = {
    "MID_Gem_Tide": "tide", "MID_Gem_Umbral": "umbral", "MID_Gem_Forte": "forte",
    "MID_Gem_Radiant": "radiant", "MID_Gem_Arcane": "arcane", "MID_Gem_Stone": "stone",
    "MID_Gem_Gale": "gale",
}


def sky_for_genome(gid):
    """Variant for a genome id (plan 3.3: compose_style first, then gems.material_a, else default)."""
    import json
    import os
    path = os.path.join(GENOME_DIR, "%s.json" % gid)
    if not os.path.exists(path):
        return "editorial_dark"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return "editorial_dark"
    style = str(d.get("compose_style", ""))
    if style in GENOME_VARIANT:
        return GENOME_VARIANT[style]
    gems = (d.get("traits") or {}).get("gems") or d.get("gems") or {}
    mat = str(gems.get("material_a", ""))
    if mat in MATERIAL_VARIANT:
        return MATERIAL_VARIANT[mat]
    return "editorial_dark"


def sky_for_object(ob):
    """Variant inferred from the hero's GN tree name (e.g. GN_FlowerBrooch_gala_tide_v10)."""
    import os
    try:
        ids = [f[:-5] for f in os.listdir(GENOME_DIR) if f.endswith(".json")]
    except Exception:
        ids = []
    for m in getattr(ob, "modifiers", []):
        ng = getattr(m, "node_group", None)
        if ng is None or not ng.name.startswith("GN_FlowerBrooch"):
            continue
        nm = ng.name.replace("GN_FlowerBrooch", "").replace("v10", "").strip("_")
        if not nm:
            gid = "melodia_brooch_v1"
        else:
            cands = [i for i in ids if nm in i]
            gid = cands[0] if cands else "melodia_brooch_v1"
        return sky_for_genome(gid), gid
    return "editorial_dark", None


def _mix_rgba(nt, label, blend='MIX'):
    """ShaderNodeMix with data_type RGBA. Sockets are index-based: factor=0, A=6, B=7."""
    n = nt.nodes.new('ShaderNodeMix')
    n.label = label
    n.data_type = 'RGBA'
    n.blend_type = blend
    assert n.data_type == 'RGBA'
    assert n.inputs[0].type == 'VALUE' and n.inputs[6].type == 'RGBA' and n.inputs[7].type == 'RGBA', \
        "Mix socket layout changed -- re-derive indices"
    return n


def _ramp(nt, label, stops):
    """ColorRamp with explicit stops [(pos, (r,g,b)), ...]. Positions must be increasing."""
    n = nt.nodes.new('ShaderNodeValToRGB')
    n.label = label
    cr = n.color_ramp
    while len(cr.elements) > 2:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1.0)
    cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1.0)
    for pos, col in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = (*col, 1.0)
    return n


def build_sky_tree(nt, p, carrier="world"):
    """Build the v1 stack into nt (World.node_tree or Material.node_tree). Returns terminal node."""
    nt.nodes.clear()

    if carrier == "card":
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        term = nt.nodes.new('ShaderNodeEmission')
        nt.links.new(term.outputs[0], out.inputs['Surface'])
        coord_sock = 'Object'
    else:
        out = nt.nodes.new('ShaderNodeOutputWorld')
        term = nt.nodes.new('ShaderNodeBackground')
        nt.links.new(term.outputs[0], out.inputs['Surface'])
        coord_sock = 'Generated'

    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs[coord_sock], sep.inputs['Vector'])
    # 2026-09-17 fix: the backdrop card is rotated 90 deg about X, so its local Z is HORIZONTAL.
    # The card's "up" is local Y. The world carrier's Generated Z is elevation as usual.
    up_sock = sep.outputs['Z'] if carrier == "world" else sep.outputs['Y']

    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.label = "z -> 0..1 (horizon placed)"
    mr.inputs['From Min'].default_value = -0.15
    mr.inputs['From Max'].default_value = 0.35
    mr.inputs['To Min'].default_value = 0.0
    mr.inputs['To Max'].default_value = 1.0
    try:
        mr.clamp = True
    except AttributeError:
        mr.use_clamp = True
    nt.links.new(up_sock, mr.inputs['Value'])

    # L0 -- base gradient (ground / horizon / mid / zenith)
    zen, hor, gnd = p["zenith"], p["horizon"], p["ground"]
    mid = tuple((hor[i] + zen[i]) * 0.5 for i in range(3))
    r0 = _ramp(nt, "L0 base gradient", [(0.0, gnd), (0.42, hor), (0.68, mid), (1.0, zen)])
    nt.links.new(mr.outputs['Result'], r0.inputs['Fac'])

    # L1 -- horizon glow band
    r1 = _ramp(nt, "L1 glow band mask", [(0.12, (0, 0, 0)), (0.30, (1, 1, 1)), (0.62, (0, 0, 0))])
    nt.links.new(mr.outputs['Result'], r1.inputs['Fac'])
    glow_amt = nt.nodes.new('ShaderNodeMath')
    glow_amt.label = "x horizon_glow"
    glow_amt.operation = 'MULTIPLY'
    glow_amt.inputs[1].default_value = float(p["horizon_glow"])
    nt.links.new(r1.outputs['Color'], glow_amt.inputs[0])
    mix1 = _mix_rgba(nt, "L1 mix glow")
    nt.links.new(r0.outputs['Color'], mix1.inputs[6])
    mix1.inputs[7].default_value = (*p["glow"], 1.0)
    nt.links.new(glow_amt.outputs['Value'], mix1.inputs[0])

    # L4 -- stars (composited BEFORE clouds so clouds occlude them)
    vco = nt.nodes.new('ShaderNodeTexVoronoi')
    vco.label = "L4 star cells"
    vco.voronoi_dimensions = '3D'
    vco.feature = 'F1'
    vco.distance = 'EUCLIDEAN'
    assert vco.feature == 'F1' and vco.voronoi_dimensions == '3D'
    smap = nt.nodes.new('ShaderNodeMapping')
    smap.inputs['Scale'].default_value = (18.0, 18.0, 18.0)
    nt.links.new(tc.outputs[coord_sock], smap.inputs['Vector'])
    nt.links.new(smap.outputs['Vector'], vco.inputs['Vector'])
    rs = _ramp(nt, "L4 star crush", [(0.0, (1, 1, 1)), (0.02 + 0.10 * (1.0 - float(p["star_brightness"])), (0, 0, 0))])
    nt.links.new(vco.outputs['Distance'], rs.inputs['Fac'])
    nzs = nt.nodes.new('ShaderNodeTexNoise')
    nzs.label = "L4 brightness variance"
    nzs.noise_dimensions = '3D'
    nzs.inputs['Scale'].default_value = 4.0
    nzs.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs[coord_sock], nzs.inputs['Vector'])
    rb = _ramp(nt, "L4 variance ramp", [(0.30, (0, 0, 0)), (0.75, (1, 1, 1))])
    nt.links.new(nzs.outputs['Fac'], rb.inputs['Fac'])
    star_comb = _mix_rgba(nt, "L4 star value", blend='MULTIPLY')
    star_comb.inputs[0].default_value = 1.0
    nt.links.new(rs.outputs['Color'], star_comb.inputs[6])
    nt.links.new(rb.outputs['Color'], star_comb.inputs[7])
    zen = _ramp(nt, "L4 zenith concentration", [(0.55, (0, 0, 0)), (1.0, (1, 1, 1))])
    nt.links.new(mr.outputs['Result'], zen.inputs['Fac'])
    s_fac1 = nt.nodes.new('ShaderNodeMath')
    s_fac1.operation = 'MULTIPLY'
    nt.links.new(star_comb.outputs[2], s_fac1.inputs[0])
    nt.links.new(zen.outputs['Color'], s_fac1.inputs[1])
    s_fac2 = nt.nodes.new('ShaderNodeMath')
    s_fac2.label = "x star_density"
    s_fac2.operation = 'MULTIPLY'
    s_fac2.inputs[1].default_value = float(p["star_density"])
    nt.links.new(s_fac1.outputs['Value'], s_fac2.inputs[0])
    mix3 = _mix_rgba(nt, "L4 mix stars")
    nt.links.new(mix1.outputs[2], mix3.inputs[6])
    mix3.inputs[7].default_value = (0.85, 0.88, 1.0, 1.0)
    nt.links.new(s_fac2.outputs['Value'], mix3.inputs[0])

    # L3 -- cloud band (mixed OVER the stars: dense cloud occludes them)
    nzc = nt.nodes.new('ShaderNodeTexNoise')
    nzc.label = "L3 cloud mass"
    nzc.noise_dimensions = '3D'
    nzc.inputs['Scale'].default_value = 3.0
    nzc.inputs['Detail'].default_value = 5.0
    nt.links.new(tc.outputs[coord_sock], nzc.inputs['Vector'])
    rc = _ramp(nt, "L3 cloud mass ramp", [(0.35, (0, 0, 0)), (0.62, (1, 1, 1))])
    nt.links.new(nzc.outputs['Fac'], rc.inputs['Fac'])
    ch = float(p.get("cloud_height", 0.55))
    hm = _ramp(nt, "L3 height mask", [(ch, (0, 0, 0)), (min(ch + 0.15, 1.0), (1, 1, 1))])
    nt.links.new(mr.outputs['Result'], hm.inputs['Fac'])
    c_fac1 = nt.nodes.new('ShaderNodeMath')
    c_fac1.operation = 'MULTIPLY'
    nt.links.new(rc.outputs['Color'], c_fac1.inputs[0])
    nt.links.new(hm.outputs['Color'], c_fac1.inputs[1])
    c_fac2 = nt.nodes.new('ShaderNodeMath')
    c_fac2.label = "x cloud_coverage"
    c_fac2.operation = 'MULTIPLY'
    c_fac2.inputs[1].default_value = float(p["cloud_coverage"])
    nt.links.new(c_fac1.outputs['Value'], c_fac2.inputs[0])
    mix4 = _mix_rgba(nt, "L3 mix clouds")
    nt.links.new(mix3.outputs[2], mix4.inputs[6])
    cl = p["glow"]
    # first-pass cloud colour: the glow hue lifted by a base grey so clouds read at all under the
    # doctrine clamp (v3 tunes per variant; the plan's "lit cloud" rule needs visible pixels first)
    mix4.inputs[7].default_value = (min(cl[0] * 1.25 + 0.022, 1.0), min(cl[1] * 1.25 + 0.022, 1.0),
                                    min(cl[2] * 1.25 + 0.026, 1.0), 1.0)
    nt.links.new(c_fac2.outputs['Value'], mix4.inputs[0])

    # L5 -- aurora band (v3; emissive-only per plan 2.7: vertical streaks x soft upper falloff x
    # aurora_strength; composited over the stars/clouds, under the grain)
    amap = nt.nodes.new('ShaderNodeMapping')
    amap.label = "L5 streak stretch"
    amap.inputs['Scale'].default_value = (5.0, 5.0, 1.2)  # compressed Z -> vertically stretched streaks
    nt.links.new(tc.outputs[coord_sock], amap.inputs['Vector'])
    naz = nt.nodes.new('ShaderNodeTexNoise')
    naz.label = "L5 aurora streaks"
    naz.noise_dimensions = '3D'
    naz.inputs['Scale'].default_value = 2.2
    naz.inputs['Detail'].default_value = 3.0
    nt.links.new(amap.outputs['Vector'], naz.inputs['Vector'])
    ra = _ramp(nt, "L5 streak mask", [(0.52, (0, 0, 0)), (0.68, (1, 1, 1)), (0.80, (0, 0, 0))])
    nt.links.new(naz.outputs['Fac'], ra.inputs['Fac'])
    fa = _ramp(nt, "L5 vertical falloff", [(0.58, (0, 0, 0)), (0.88, (1, 1, 1))])
    nt.links.new(mr.outputs['Result'], fa.inputs['Fac'])
    a_fac1 = nt.nodes.new('ShaderNodeMath')
    a_fac1.operation = 'MULTIPLY'
    nt.links.new(ra.outputs['Color'], a_fac1.inputs[0])
    nt.links.new(fa.outputs['Color'], a_fac1.inputs[1])
    a_fac2 = nt.nodes.new('ShaderNodeMath')
    a_fac2.label = "x aurora_strength"
    a_fac2.operation = 'MULTIPLY'
    a_fac2.inputs[1].default_value = float(p["aurora_strength"])
    nt.links.new(a_fac1.outputs['Value'], a_fac2.inputs[0])
    mix5 = _mix_rgba(nt, "L5 mix aurora")
    nt.links.new(mix4.outputs[2], mix5.inputs[6])
    mix5.inputs[7].default_value = (min(cl[0] * 2.0 + 0.010, 1.0), min(cl[1] * 2.0 + 0.014, 1.0),
                                    min(cl[2] * 2.0 + 0.018, 1.0), 1.0)
    nt.links.new(a_fac2.outputs['Value'], mix5.inputs[0])

    # L6 -- grain (anti-banding)
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
    wn.label = "L6 grain noise"
    nt.links.new(tc.outputs['Window'], wn.inputs['Vector'])
    sub = nt.nodes.new('ShaderNodeMath')
    sub.operation = 'SUBTRACT'
    sub.inputs[1].default_value = 0.5
    nt.links.new(wn.outputs['Value'], sub.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.label = "x grain"
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = float(p["grain"])
    nt.links.new(sub.outputs['Value'], mul.inputs[0])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(mul.outputs['Value'], comb.inputs['X'])
    nt.links.new(mul.outputs['Value'], comb.inputs['Y'])
    nt.links.new(mul.outputs['Value'], comb.inputs['Z'])
    mix2 = _mix_rgba(nt, "L6 mix grain", blend='ADD')
    mix2.inputs[0].default_value = 1.0
    nt.links.new(mix5.outputs[2], mix2.inputs[6])
    nt.links.new(comb.outputs['Vector'], mix2.inputs[7])

    # L7 -- strength trim (doctrine clamp) on the terminal
    nt.links.new(mix2.outputs[2], term.inputs['Color'])
    term.inputs['Strength'].default_value = float(p["sky_strength"])

    return term


def _set_sun_threshold(scn):
    """G6: keep a bright horizon band from being extracted as a sun."""
    for attr in ("sun_threshold", "world_sun_threshold"):
        if hasattr(scn.eevee, attr):
            try:
                setattr(scn.eevee, attr, 0.0)
                print("sky: eevee.%s = 0.0" % attr)
                return attr
            except Exception as exc:
                print("sky: could not set %s (%r)" % (attr, exc))
    print("sky: no sun-threshold property found on scene.eevee")
    return None


def apply_sky(scene, variant="editorial_dark", with_card=True, **overrides):
    """Idempotent: (re)build the world + card carriers for the named variant. Returns info dict."""
    if variant not in SKY_PRESETS:
        raise KeyError("unknown sky variant %r (have: %s)" % (variant, ", ".join(SKY_PRESETS)))
    p = dict(SKY_PRESETS[variant])
    p.update(overrides)

    world = bpy.data.worlds.get(WORLD_NAME)
    if world is None:
        world = bpy.data.worlds.new(WORLD_NAME)
    world.use_nodes = True
    scene.world = world
    build_sky_tree(world.node_tree, p, carrier="world")
    n_world = len(world.node_tree.nodes)

    n_card = 0
    if with_card:
        ob = bpy.data.objects.get("PRES_Back")
        if ob is not None:
            mat = bpy.data.materials.get(CARD_MAT)
            if mat is None:
                mat = bpy.data.materials.new(CARD_MAT)
            mat.use_nodes = True
            build_sky_tree(mat.node_tree, p, carrier="card")
            n_card = len(mat.node_tree.nodes)
            if ob.data.materials:
                ob.data.materials[0] = mat
            else:
                ob.data.materials.append(mat)

    sun = _set_sun_threshold(scene)

    # gates: no textures, node budget
    bad = []
    for nt, tag in ((world.node_tree, "world"),) + \
            (((bpy.data.materials[CARD_MAT].node_tree, "card"),) if n_card else ()):
        for n in nt.nodes:
            if n.type in ('TEX_IMAGE', 'TEX_ENVIRONMENT'):
                bad.append((tag, n.name))
        assert len(nt.nodes) <= 60, "%s tree has %d nodes (>60)" % (tag, len(nt.nodes))
    assert not bad, "texture nodes present: %r" % (bad,)

    info = dict(variant=variant, nodes_world=n_world, nodes_card=n_card, sun_attr=sun,
                strength=p["sky_strength"], layers=_LAYERS)
    print("SKY| variant=%s nodes_world=%d nodes_card=%d strength=%.2f sun=%s"
          % (variant, n_world, n_card, p["sky_strength"], sun))
    return info


def _arg(name, default=None):
    a = sys.argv
    if name in a:
        i = a.index(name)
        if i + 1 < len(a):
            return a[i + 1]
    return default


if __name__ == "__main__":
    v = _arg("--sky", "editorial_dark")
    info = apply_sky(bpy.context.scene, variant=v, with_card=("--no-card" not in sys.argv))
    print("done sky build")
