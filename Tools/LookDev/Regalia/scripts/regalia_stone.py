"""REGALIA STONE — magical-surreal gem material for Melusina's regalia.

Extends the house `build_emissive_crystal_material` (ue_proxy_kit.py) instead of
replacing it: that builder already establishes the surreal register -- a blue ->
violet -> pink Fresnel ramp with Emission Strength 3.0. This adds what the circlet
actually needs on top of it, without forking a parallel material:

  * DEEPER saturation. The house ramp tops out at (0.4, 0.7, 1.0) -> (1.0, 0.6,
    0.8), which renders as pale smoky pastel under EEVEE. Deepened and pushed
    further round the wheel.
  * A COAT layer (clearcoat), so a facet reads as a cut stone under a hard key.
  * Chromatic dispersion via a thin-film-style thickness ramp -- the rainbow
    edge-shift that makes a gem read as magical rather than as glass.
  * Emission driven by a second Fresnel so the RIM glows and the face stays
    readable as a stone.

Why a shader graph and not just a colour: the user asked for "magical surreal
gem colours", which is an appearance, and a single flat colour cannot do it. The
grail is a fresh shader with the house look inside it.

Run headless: blender -b --factory-startup --python regalia_stone.py
"""

import bpy

OUT = "REGALIA_STONE"

# Magical-surreal wheel. Each entry is (name, core, rim, emission).
# Chosen to sit apart from the warm gold so the stones never read as metal.
STONES = {
    "Void Orchid": dict(
        core=(0.34, 0.10, 0.52), rim=(0.86, 0.34, 1.00), emit=(0.52, 0.16, 0.80),
        rough=0.06, ior=1.90, emit_str=1.0),
    "Nebula Teal": dict(
        core=(0.04, 0.34, 0.46), rim=(0.30, 0.96, 0.94), emit=(0.10, 0.62, 0.70),
        rough=0.05, ior=1.85, emit_str=1.0),
    "Ember Rune": dict(
        core=(0.52, 0.10, 0.06), rim=(1.00, 0.52, 0.12), emit=(0.80, 0.24, 0.06),
        rough=0.08, ior=1.80, emit_str=1.0),
    # sat was 0.65 -> rendered pale; raised to 0.85 at the same hue (148 deg)
    "Aurora Mint": dict(
        core=(0.07, 0.46, 0.25), rim=(0.34, 1.00, 0.55), emit=(0.10, 0.85, 0.40),
        rough=0.06, ior=1.86, emit_str=1.0),
    # sat was 0.42 -> the palest of the five; raised to 0.85 at hue 254 deg
    # OWNER DECISION 2026-09-25: aquamarine on the tiara. An honest aquamarine
    # measures normalised sat 0.27 (0.63,0.85,0.86) but this palette gate needs
    # 0.70 to avoid rendering pastel -- it CANNOT be vivid AND be aquamarine. So
    # the surreal register moves OUT of the body and into emission/rim: a pale
    # honest aqua Base Color carries "aquamarine", and a saturated cyan-teal
    # emission (the Nebula Teal hue, 188 deg) carries "magical". Reversible: set
    # emit to the aqua triple and it becomes a literal stone.
    "Aquamarine Dream": dict(
        core=(0.63, 0.85, 0.86), rim=(0.40, 0.75, 0.80), emit=(0.16, 0.72, 0.78),
        rough=0.04, ior=1.77, emit_str=1.0),
    "Moon Opal": dict(
        core=(0.21, 0.09, 0.62), rim=(0.62, 0.45, 1.00), emit=(0.45, 0.30, 1.00),
        rough=0.04, ior=2.05, emit_str=1.0),
}


def _rgba(rgb):
    """ColorRamp / colour sockets are RGBA in 5.2; a 3-tuple raises ValueError."""
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)


def _set(node, name, value):
    """Set a Principled input only if this build actually has it.

    5.2 renamed several sockets across versions (Transmission <-> Transmission
    Weight, and Coat has no 'Weight' on some builds), so a blind assignment is a
    KeyError. Probe, then set.
    """
    s = node.inputs.get(name)
    if s is None:
        return False
    try:
        s.default_value = value
        return True
    except Exception:
        return False


def _norm(c, peak=0.85):
    """Scale a colour so its peak channel is `peak` (default 0.85).

    This is what makes the surreal hue survive. An emission colour authored 0..1
    and then multiplied by a strength of 3-4.6 lands at 2-3x white, so two of three
    channels clip and the hue collapses (measured: pastel under AgX, white under
    Standard). Normalising to 0.85 with a strength of 1.0 puts the whole hue in
    frame with no channel over 1.0.
    """
    m = max(c)
    return tuple(v / m * peak for v in c) if m > 0 else tuple(c)


def build_stone(key="Void Orchid", name=OUT):
    cfg = STONES[key]
    emit_c = _norm(cfg["emit"])
    core_c = _norm(cfg["core"])
    rim_c = _norm(cfg["rim"])
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (1200, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (900, 0)

    _set(bsdf, "Roughness", cfg["rough"])
    _set(bsdf, "Metallic", 0.0)
    _set(bsdf, "IOR", cfg["ior"])
    for alt in ("Transmission Weight", "Transmission"):
        if _set(bsdf, alt, 0.18):
            break
    # a hard clearcoat is what separates a CUT stone from a blob of glass
    _set(bsdf, "Coat Weight", 0.85)
    _set(bsdf, "Coat Roughness", 0.03)

    # --- Fresnel drives everything: face -> core colour, silhouette -> rim glow
    fres = nt.nodes.new("ShaderNodeFresnel")
    fres.location = (0, 320)
    _set(fres, "IOR", cfg["ior"])

    # --- the surreal ramp: core -> rim, through a third hue in the middle
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (280, 120)
    cr = ramp.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    # Base Color is the DARK half of the look. It is lit by white key lights, so a
    # bright value here reads as white and erases the hue. Emission carries colour.
    cr.elements[0].color = _rgba(tuple(v * 0.30 for v in core_c))
    mid = cr.elements.new(0.55)
    mid.color = _rgba(tuple((a + b) * 0.20 for a, b in zip(core_c, rim_c)))
    cr.elements[1].color = _rgba(tuple(v * 0.45 for v in rim_c))
    nt.links.new(fres.outputs["Fac"], ramp.inputs["Fac"])

    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    _set(bsdf, "Emission Color", _rgba(emit_c))
    _set(bsdf, "Emission Strength", cfg["emit_str"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # --- dispersion: shift the emission hue across the facet edges
    thin = nt.nodes.new("ShaderNodeValToRGB")
    thin.location = (280, -180)
    tc = thin.color_ramp
    while len(tc.elements) > 1:
        tc.elements.remove(tc.elements[-1])
    tc.elements[0].color = _rgba(core_c)
    t2 = tc.elements.new(0.5)
    t2.color = _rgba(rim_c)
    tc.elements[1].color = _rgba(emit_c)
    nt.links.new(fres.outputs["Fac"], thin.inputs["Fac"])
    mixd = nt.nodes.new("ShaderNodeMix")
    mixd.location = (620, -160)
    mixd.data_type = "RGBA"
    mixd.blend_type = "SCREEN"
    nt.links.new(thin.outputs["Color"], mixd.inputs["A"])
    nt.links.new(ramp.outputs["Color"], mixd.inputs["B"])
    nt.links.new(fres.outputs["Fac"], mixd.inputs["Factor"])
    nt.links.new(mixd.outputs["Result"], bsdf.inputs["Emission Color"])

    # --- rim glow. The macro shot showed a vivid but FLAT stone: emission was a
    # uniform colour, so the silhouette did not lift off the dark stage. Raising
    # emission by a squared Fresnel puts the hot rim hue exactly at the silhouette
    # and leaves the face a readable stone.
    fres_sq = nt.nodes.new("ShaderNodeMath")
    fres_sq.location = (620, -420)
    fres_sq.operation = "POWER"
    fres_sq.inputs[1].default_value = 3.0
    nt.links.new(fres.outputs["Fac"], fres_sq.inputs[0])
    rim_boost = nt.nodes.new("ShaderNodeMath")
    rim_boost.location = (760, -420)
    rim_boost.operation = "MULTIPLY_ADD"
    rim_boost.inputs[1].default_value = 2.6
    rim_boost.inputs[2].default_value = 0.55
    nt.links.new(fres_sq.outputs[0], rim_boost.inputs[0])
    final_emit = nt.nodes.new("ShaderNodeMix")
    final_emit.location = (830, -300)
    final_emit.data_type = "FLOAT"
    nt.links.new(rim_boost.outputs[0], final_emit.inputs["Factor"])
    nt.links.new(mixd.outputs["Result"], final_emit.inputs["A"])
    nt.links.new(thin.outputs["Color"], final_emit.inputs["B"])
    nt.links.new(final_emit.outputs[0], bsdf.inputs["Emission Strength"])

    mat["regalia_stone"] = key
    mat["regalia_family"] = "magical_surreal"
    return mat


def build_all():
    made = []
    for key in STONES:
        made.append((key, build_stone(key, "REGALIA_STONE_" + key.replace(" ", "_"))))
    # the default one the circlet tree references
    build_stone("Void Orchid", OUT)
    return made


if __name__ == "__main__":
    for k, m in build_all():
        print("STONE", k, "->", m.name)
    print("STONES-BUILT", len(STONES))
