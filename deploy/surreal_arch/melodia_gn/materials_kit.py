"""MEL materials — absorbed from the monolith (P2 family 9a). Full closure."""
from __future__ import annotations
import bpy
from . import core
MAT_NAMES = {
    'STONE':       "SurrealArch_Stone",
    'MARBLE':      "SurrealArch_Marble",
    'WATER':       "SurrealArch_MusicalWater",
    'STAINED':     "SurrealArch_StainedGlass",
    'IRIDESCENT':  "SurrealArch_Iridescent",
    'GOLD':        "SurrealArch_Gold",
    'CLEF_GLOW':   "SurrealArch_ClefGlow",
    'GOTHIC_DARK': "SurrealArch_GothicDark",
    'GENSHIN':     "SurrealArch_GenshinToon",
}


MATERIAL_PALETTE = {
    'STONE':       (0.78, 0.76, 0.72, 1.0),    # warm grey
    'MARBLE':      (0.95, 0.94, 0.92, 1.0),    # off-white
    'WATER':       (0.32, 0.62, 0.85, 1.0),    # surreal blue
    'STAINED':     (0.65, 0.45, 0.85, 1.0),    # purple-violet
    'IRIDESCENT':  (0.55, 0.75, 0.95, 1.0),    # blueish metal
    'GOLD':        (0.95, 0.78, 0.30, 1.0),    # warm gold
    'CLEF_GLOW':   (0.95, 0.50, 0.85, 1.0),    # magenta glow
    'GOTHIC_DARK': (0.35, 0.32, 0.40, 1.0),    # dark stone
    'GENSHIN':     (0.95, 0.85, 0.95, 1.0),    # soft pastel pink (Genshin toon)
}

# Material name registry (name in bpy.data.materials)

WORLD_NAME = "SurrealArch_DayNightWorld"

# Musical note pattern -> frequency multiplier

COLORS = {
    "input":     (0.55, 0.65, 0.85),
    "tower":     (0.85, 0.75, 0.85),
    "organic":   (0.76, 0.92, 0.78),
    "noise":     (0.95, 0.85, 0.70),
    "deform":    (1.00, 0.95, 0.75),
    "optimize":  (0.75, 0.90, 0.95),
    "output":    (0.85, 0.75, 0.95),
    "railing":   (0.90, 0.80, 0.95),
    "stair":     (0.80, 0.95, 0.85),
    "arch":      (0.95, 0.80, 0.80),
    "buttress":  (0.92, 0.88, 0.78),
    "ornament":  (0.95, 0.92, 0.78),
    "penrose":   (0.85, 0.85, 1.00),    # impossible stairs
    "pillar":    (0.95, 0.92, 0.85),    # classical column
    "dome":      (0.80, 0.92, 0.95),    # spherical roof
    "crenel":    (0.90, 0.88, 0.85),    # castle battlements
    "fractal":   (0.95, 0.85, 0.95),    # recursive structures
    "bevel":     (0.92, 0.95, 0.92),    # soft-bevel pass
    "music":     (0.95, 0.80, 0.92),    # musical notation
    "gothic":    (0.85, 0.80, 0.95),    # Gothic architectural elements
    "tracery":   (0.92, 0.92, 1.00),    # Gothic tracery / tracing
    "venetian":  (0.95, 0.85, 0.78),    # Venetian Gothic (warm sandstone)
    "ogee":      (0.92, 0.78, 0.85),    # Venetian ogee curves
    "palazzo":   (0.88, 0.82, 0.95),    # Palazzo composite
    "entropiombo":(0.85,0.95, 0.85),    # Inward-lean deformation
    "brick":     (0.95, 0.78, 0.72),    # Brick masonry
    "bridge":    (0.85, 0.92, 0.95),    # Venetian bridge
    "path":      (0.92, 0.85, 0.95),    # Escher walkway
    "universal": (1.00, 0.92, 0.85),    # Universal modulation pass
    "synthia":   (0.85, 0.92, 0.78),    # Synthia math viz integration
    "modular":   (0.92, 0.95, 0.85),    # Modular building pieces
    "window":    (0.85, 0.92, 0.95),    # Window opening
    "door":      (0.95, 0.85, 0.78),    # Door
    "fountain":  (0.78, 0.92, 0.95),    # Fountain
    "tile":      (0.95, 0.92, 0.85),    # Floor tile
    "roof":      (0.95, 0.78, 0.78),    # Roof tiles
    "lantern":   (1.00, 0.92, 0.65),    # Lamppost
    "spline":    (0.78, 0.92, 0.95),    # Spline instancing
    "radial":    (0.95, 0.85, 0.85),    # Radial array
    "tessellation":(0.85, 0.95, 0.78),  # Escher tessellation
    "hyperbolic": (0.92, 0.78, 0.95),   # Hyperbolic disk
    "genshin":   (1.00, 0.85, 0.92),    # Genshin Impact stylization
    "sheet_music":(0.95, 0.95, 0.85),   # Sheet music railing
    "level":      (0.85, 0.95, 0.85),   # Level design / greybox
    "wall":       (0.90, 0.85, 0.80),   # Wall pieces
    "ceiling":    (0.78, 0.82, 0.92),   # Ceiling
    "house":      (0.95, 0.85, 0.92),   # Modular house composite
    "beams":      (0.85, 0.92, 0.95),   # Cascading beams (Erindale)
    "cleanup":    (0.92, 0.92, 0.92),   # Topology cleanup pass
    "fence":      (0.88, 0.92, 0.80),   # Fence / barrier generators
}


# Forward-declared base for all sub-panels (referenced by panels defined
# both before and after the original definition site further down).
class _SubPanelBase:
    """Mixin for all sub-panels (sets parent and properties context)."""
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "modifier"
    bl_parent_id   = "SURREAL_ARCH_PT_panel"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'


class _EffectsSubPanelBase:
    """Nested under Effects & Atmosphere - optional overlay panels."""
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "modifier"
    bl_parent_id   = "SURREAL_ARCH_PT_effects"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'


# Synthia preset list (curated subset with the most surreal/architectural shapes)

def build_base_material():
    """Default stylized PBR - soft pastel matte base."""
    name = MAT_NAMES['STONE']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (350, 0)
    _color_shader_node(bsdf, "tower")
    _set_principled(bsdf,
        **{'Base Color': MATERIAL_PALETTE['STONE'],
           'Roughness': 0.78,
           'Specular IOR Level': 0.4})

    # Subtle noise variation
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.location = (-100, -200)
    _color_shader_node(noise, "noise")
    noise.inputs['Scale'].default_value = 8.0
    noise.inputs['Detail'].default_value = 4.0
    noise.inputs['Roughness'].default_value = 0.55

    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (100, -200)
    _color_shader_node(ramp, "ornament")
    ramp.color_ramp.elements[0].color = (0.65, 0.62, 0.58, 1.0)
    ramp.color_ramp.elements[1].color = (0.88, 0.86, 0.83, 1.0)

    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    fr = _frame(nt, "Stone - Stylized PBR", "tower", x=-200, y=200)
    for n in (out, bsdf, noise, ramp): n.parent = fr
    return mat



def build_marble_material():
    """Marble with veining for pillars/buttresses."""
    name = MAT_NAMES['MARBLE']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (1000, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (700, 0)
    _color_shader_node(bsdf, "pillar")
    _set_principled(bsdf, Roughness=0.25, **{'Specular IOR Level': 0.6})

    coord = nt.nodes.new('ShaderNodeTexCoord'); coord.location = (-600, 0)

    # Marble veins - Wave + Noise distortion
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.location = (-300, -200)
    _color_shader_node(noise, "noise")
    noise.inputs['Scale'].default_value = 2.0
    noise.inputs['Detail'].default_value = 6.0
    noise.inputs['Distortion'].default_value = 1.5
    nt.links.new(coord.outputs['Generated'], noise.inputs['Vector'])

    wave = nt.nodes.new('ShaderNodeTexWave'); wave.location = (-300, 0)
    _color_shader_node(wave, "ornament")
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'X'
    wave.inputs['Scale'].default_value = 4.0
    wave.inputs['Distortion'].default_value = 8.0
    wave.inputs['Detail'].default_value = 2.0
    nt.links.new(coord.outputs['Generated'], wave.inputs['Vector'])

    # Distort wave with noise
    add = nt.nodes.new('ShaderNodeMixRGB'); add.location = (-100, 0)
    add.blend_type = 'ADD'
    add.inputs['Fac'].default_value = 0.5
    nt.links.new(wave.outputs['Color'], add.inputs['Color1'])
    nt.links.new(noise.outputs['Color'], add.inputs['Color2'])

    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (200, 0)
    _color_shader_node(ramp, "tracery")
    ramp.color_ramp.elements[0].color = MATERIAL_PALETTE['MARBLE']
    ramp.color_ramp.elements[1].color = (0.4, 0.4, 0.45, 1.0)
    ramp.color_ramp.elements[1].position = 0.3

    nt.links.new(add.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    fr = _frame(nt, "Marble - Veined Stone", "pillar", x=-700, y=300)
    for n in (out, bsdf, coord, noise, wave, add, ramp): n.parent = fr
    return mat



def build_musical_water_material():
    """
    MAGICAL LAYERED WATER - 5 stacked layers:
      1. Depth-color gradient (deep blue -> cyan based on Z)
      2. 3-band sine ripples (low/mid/high freq, driven by harmonic params)
      3. Voronoi sparkles (twinkling pink highlights)
      4. Fresnel iridescence (purple rim color)
      5. Foam crests (white at wave peaks)
    All layers tinted, mixed, and bumped - harmonic params drive ripple frequencies.
    """
    name = MAT_NAMES['WATER']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()

    # === Output + BSDF ===
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (2400, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (2000, 0)
    _color_shader_node(bsdf, "organic")
    _set_principled(bsdf,
        Roughness=0.04,
        **{'Specular IOR Level': 0.7,
           'Transmission Weight': 0.55,
           'IOR': 1.33})
    if 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = 0.5

    # === Coordinate sources ===
    coord = nt.nodes.new('ShaderNodeTexCoord'); coord.location = (-1800, 0)
    _color_shader_node(coord, "input")
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (-1500, 0)
    nt.links.new(coord.outputs['Generated'], sep.inputs['Vector'])

    geom = nt.nodes.new('ShaderNodeNewGeometry'); geom.location = (-1800, 250)
    sep_g = nt.nodes.new('ShaderNodeSeparateXYZ'); sep_g.location = (-1500, 250)
    nt.links.new(geom.outputs['Position'], sep_g.inputs['Vector'])

    # === Driver-controllable harmonic frequency knobs ===
    freq_a = nt.nodes.new('ShaderNodeValue'); freq_a.location = (-1800, -250); freq_a.label = "Harmonic A"
    freq_a.outputs[0].default_value = 6.0
    _color_shader_node(freq_a, "music")
    freq_b = nt.nodes.new('ShaderNodeValue'); freq_b.location = (-1800, -400); freq_b.label = "Harmonic B"
    freq_b.outputs[0].default_value = 12.0
    _color_shader_node(freq_b, "music")
    freq_c = nt.nodes.new('ShaderNodeValue'); freq_c.location = (-1800, -550); freq_c.label = "Harmonic C"
    freq_c.outputs[0].default_value = 24.0
    _color_shader_node(freq_c, "music")
    phase = nt.nodes.new('ShaderNodeValue'); phase.location = (-1800, -700); phase.label = "Phase"
    phase.outputs[0].default_value = 0.0
    _color_shader_node(phase, "music")

    # === LAYER 1: Depth-color gradient ===
    depth_norm = nt.nodes.new('ShaderNodeMapRange'); depth_norm.location = (-1100, 200)
    depth_norm.inputs['From Min'].default_value = -2.0
    depth_norm.inputs['From Max'].default_value = 2.0
    nt.links.new(sep_g.outputs['Z'], depth_norm.inputs['Value'])
    depth_ramp = nt.nodes.new('ShaderNodeValToRGB'); depth_ramp.location = (-850, 200)
    _color_shader_node(depth_ramp, "organic")
    cr = depth_ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.05, 0.16, 0.42, 1.0)
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.4, 0.85, 1.0, 1.0)
    nt.links.new(depth_norm.outputs['Result'], depth_ramp.inputs['Fac'])

    # === LAYER 2: 3-band sine ripples ===
    def _sine_layer(axis_socket, freq_socket, x, y, label):
        mul = nt.nodes.new('ShaderNodeMath'); mul.location = (x, y); mul.operation = 'MULTIPLY'
        nt.links.new(axis_socket, mul.inputs[0])
        nt.links.new(freq_socket, mul.inputs[1])
        add_p = nt.nodes.new('ShaderNodeMath'); add_p.location = (x + 200, y); add_p.operation = 'ADD'
        nt.links.new(mul.outputs[0], add_p.inputs[0])
        nt.links.new(phase.outputs[0], add_p.inputs[1])
        sn = nt.nodes.new('ShaderNodeMath'); sn.location = (x + 400, y); sn.operation = 'SINE'
        sn.label = label
        _color_shader_node(sn, "ornament")
        nt.links.new(add_p.outputs[0], sn.inputs[0])
        return sn

    sx_a = _sine_layer(sep.outputs['X'], freq_a.outputs[0], -1300, -200, "Low X")
    sy_b = _sine_layer(sep.outputs['Y'], freq_b.outputs[0], -1300, -400, "Mid Y")
    xy_add = nt.nodes.new('ShaderNodeMath'); xy_add.location = (-1500, -600); xy_add.operation = 'ADD'
    nt.links.new(sep.outputs['X'], xy_add.inputs[0]); nt.links.new(sep.outputs['Y'], xy_add.inputs[1])
    sd_c = _sine_layer(xy_add.outputs[0], freq_c.outputs[0], -1300, -600, "Hi Diag")

    sum_xy = nt.nodes.new('ShaderNodeMath'); sum_xy.location = (-650, -400); sum_xy.operation = 'ADD'
    nt.links.new(sx_a.outputs[0], sum_xy.inputs[0])
    nt.links.new(sy_b.outputs[0], sum_xy.inputs[1])
    sum_all = nt.nodes.new('ShaderNodeMath'); sum_all.location = (-450, -400); sum_all.operation = 'ADD'
    nt.links.new(sum_xy.outputs[0], sum_all.inputs[0])
    nt.links.new(sd_c.outputs[0], sum_all.inputs[1])

    norm_waves = nt.nodes.new('ShaderNodeMapRange'); norm_waves.location = (-250, -400)
    norm_waves.inputs['From Min'].default_value = -3.0
    norm_waves.inputs['From Max'].default_value = 3.0
    norm_waves.inputs['To Min'].default_value = 0.0
    norm_waves.inputs['To Max'].default_value = 1.0
    nt.links.new(sum_all.outputs[0], norm_waves.inputs['Value'])

    wave_color = nt.nodes.new('ShaderNodeValToRGB'); wave_color.location = (-50, -400)
    _color_shader_node(wave_color, "ornament")
    cr2 = wave_color.color_ramp
    cr2.elements[0].position = 0.0; cr2.elements[0].color = (0.10, 0.30, 0.55, 1.0)
    cr2.elements[1].position = 1.0; cr2.elements[1].color = (0.7, 0.95, 1.0, 1.0)
    nt.links.new(norm_waves.outputs['Result'], wave_color.inputs['Fac'])

    # Layer 1 + Layer 2 -> overlay mix
    mix_dw = nt.nodes.new('ShaderNodeMixRGB'); mix_dw.location = (250, 0)
    mix_dw.blend_type = 'OVERLAY'; mix_dw.inputs['Fac'].default_value = 0.6
    _color_shader_node(mix_dw, "deform")
    nt.links.new(depth_ramp.outputs['Color'], mix_dw.inputs['Color1'])
    nt.links.new(wave_color.outputs['Color'], mix_dw.inputs['Color2'])

    # === LAYER 3: Voronoi sparkles ===
    voronoi = nt.nodes.new('ShaderNodeTexVoronoi'); voronoi.location = (-450, 600)
    _color_shader_node(voronoi, "ornament")
    voronoi.feature = 'SMOOTH_F1'
    voronoi.inputs['Scale'].default_value = 18.0
    nt.links.new(coord.outputs['Generated'], voronoi.inputs['Vector'])

    spark_ramp = nt.nodes.new('ShaderNodeValToRGB'); spark_ramp.location = (-150, 600)
    _color_shader_node(spark_ramp, "ornament")
    cr3 = spark_ramp.color_ramp
    cr3.elements[0].position = 0.0;  cr3.elements[0].color = (0,0,0,1)
    cr3.elements[1].position = 0.05; cr3.elements[1].color = (1.0, 0.85, 0.95, 1.0)  # pink sparkle
    nt.links.new(voronoi.outputs['Distance'], spark_ramp.inputs['Fac'])

    mix_sp = nt.nodes.new('ShaderNodeMixRGB'); mix_sp.location = (550, 200)
    mix_sp.blend_type = 'ADD'; mix_sp.inputs['Fac'].default_value = 0.5
    _color_shader_node(mix_sp, "ornament")
    nt.links.new(mix_dw.outputs['Color'], mix_sp.inputs['Color1'])
    nt.links.new(spark_ramp.outputs['Color'], mix_sp.inputs['Color2'])

    # === LAYER 4: Fresnel iridescent rim ===
    fresnel = nt.nodes.new('ShaderNodeFresnel'); fresnel.location = (-450, 850)
    fresnel.inputs['IOR'].default_value = 1.45
    _color_shader_node(fresnel, "ornament")

    iri_ramp = nt.nodes.new('ShaderNodeValToRGB'); iri_ramp.location = (-150, 850)
    _color_shader_node(iri_ramp, "ornament")
    cr4 = iri_ramp.color_ramp
    cr4.elements[0].position = 0.0; cr4.elements[0].color = (0,0,0,1)
    e_mid = cr4.elements.new(0.5); e_mid.color = (0.7, 0.5, 1.0, 1.0)
    cr4.elements[2].color = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(fresnel.outputs[0], iri_ramp.inputs['Fac'])

    mix_fr = nt.nodes.new('ShaderNodeMixRGB'); mix_fr.location = (850, 400)
    mix_fr.blend_type = 'SCREEN'; mix_fr.inputs['Fac'].default_value = 0.4
    _color_shader_node(mix_fr, "ornament")
    nt.links.new(mix_sp.outputs['Color'], mix_fr.inputs['Color1'])
    nt.links.new(iri_ramp.outputs['Color'], mix_fr.inputs['Color2'])

    # === LAYER 5: Foam crests ===
    foam_ramp = nt.nodes.new('ShaderNodeValToRGB'); foam_ramp.location = (250, -600)
    _color_shader_node(foam_ramp, "ornament")
    cr5 = foam_ramp.color_ramp
    cr5.elements[0].position = 0.85; cr5.elements[0].color = (0,0,0,1)
    cr5.elements[1].position = 0.95; cr5.elements[1].color = (1,1,1,1)
    nt.links.new(norm_waves.outputs['Result'], foam_ramp.inputs['Fac'])

    mix_foam = nt.nodes.new('ShaderNodeMixRGB'); mix_foam.location = (1150, 200)
    mix_foam.blend_type = 'ADD'; mix_foam.inputs['Fac'].default_value = 0.7
    _color_shader_node(mix_foam, "ornament")
    nt.links.new(mix_fr.outputs['Color'], mix_foam.inputs['Color1'])
    nt.links.new(foam_ramp.outputs['Color'], mix_foam.inputs['Color2'])

    # Final -> BSDF
    nt.links.new(mix_foam.outputs['Color'], bsdf.inputs['Base Color'])
    if 'Emission Color' in bsdf.inputs:
        nt.links.new(mix_foam.outputs['Color'], bsdf.inputs['Emission Color'])

    # Bump from waves
    bump = nt.nodes.new('ShaderNodeBump'); bump.location = (1500, -300)
    bump.inputs['Strength'].default_value = 0.45
    _color_shader_node(bump, "deform")
    nt.links.new(norm_waves.outputs['Result'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    fr = _frame(nt, "Magical Layered Water - 5 layers (depth + 3 sine bands + sparkle + fresnel + foam)",
                "music", x=-1900, y=950)
    for n in (out, bsdf, coord, sep, geom, sep_g, freq_a, freq_b, freq_c, phase,
              depth_norm, depth_ramp, sx_a, sy_b, sd_c, xy_add, sum_xy, sum_all,
              norm_waves, wave_color, mix_dw, voronoi, spark_ramp, mix_sp,
              fresnel, iri_ramp, mix_fr, foam_ramp, mix_foam, bump):
        n.parent = fr
    return mat



def build_stained_glass_material():
    """Stained glass - Voronoi cells in jewel tones, perfect for rose windows."""
    name = MAT_NAMES['STAINED']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (1100, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (800, 0)
    _color_shader_node(bsdf, "tracery")
    _set_principled(bsdf,
        Roughness=0.15,
        **{'Transmission Weight': 0.7, 'IOR': 1.45})
    bsdf.inputs['Emission Strength'].default_value = 0.5

    coord = nt.nodes.new('ShaderNodeTexCoord'); coord.location = (-700, 0)

    # Voronoi cells = stained glass panels
    voronoi = nt.nodes.new('ShaderNodeTexVoronoi'); voronoi.location = (-450, 0)
    _color_shader_node(voronoi, "tracery")
    voronoi.feature = 'F1'
    voronoi.inputs['Scale'].default_value = 6.0
    nt.links.new(coord.outputs['Generated'], voronoi.inputs['Vector'])

    # Color the cells - use position output to offset hue
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (-150, -100)
    _color_shader_node(ramp, "ornament")
    # Add jewel-tone color stops
    cr = ramp.color_ramp
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].color = (0.85, 0.20, 0.30, 1.0)  # ruby
    e2 = cr.elements.new(0.33); e2.color = (0.20, 0.55, 0.85, 1.0)  # sapphire
    e3 = cr.elements.new(0.66); e3.color = (0.30, 0.75, 0.40, 1.0)  # emerald
    e4 = cr.elements.new(1.0); e4.color = (0.90, 0.75, 0.20, 1.0)  # amber

    nt.links.new(voronoi.outputs['Distance'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Emission Color'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    fr = _frame(nt, "Stained Glass - Jewel-Tone Voronoi", "tracery", x=-800, y=300)
    for n in (out, bsdf, coord, voronoi, ramp): n.parent = fr
    return mat



def build_iridescent_material():
    """Iridescent metal for railings/ornaments - Layer Weight + color gradient."""
    name = MAT_NAMES['IRIDESCENT']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (900, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (600, 0)
    _color_shader_node(bsdf, "railing")
    _set_principled(bsdf, Metallic=1.0, Roughness=0.15)

    layer_w = nt.nodes.new('ShaderNodeLayerWeight'); layer_w.location = (-200, 0)
    layer_w.inputs['Blend'].default_value = 0.5
    _color_shader_node(layer_w, "ornament")

    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.location = (100, 0)
    _color_shader_node(ramp, "ornament")
    cr = ramp.color_ramp
    while len(cr.elements) > 1: cr.elements.remove(cr.elements[-1])
    cr.elements[0].color = (0.95, 0.55, 0.85, 1.0)
    e2 = cr.elements.new(0.5); e2.color = (0.55, 0.85, 0.95, 1.0)
    e3 = cr.elements.new(1.0); e3.color = (0.85, 0.95, 0.55, 1.0)

    nt.links.new(layer_w.outputs['Fresnel'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    fr = _frame(nt, "Iridescent Metal", "railing", x=-300, y=200)
    for n in (out, bsdf, layer_w, ramp): n.parent = fr
    return mat



def build_gold_material():
    name = MAT_NAMES['GOLD']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (500, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (200, 0)
    _color_shader_node(bsdf, "ornament")
    _set_principled(bsdf,
        **{'Base Color': MATERIAL_PALETTE['GOLD']},
        Metallic=1.0, Roughness=0.25)
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    fr = _frame(nt, "Gold - Warm Metal", "ornament", x=100, y=200)
    for n in (out, bsdf): n.parent = fr
    return mat



def build_clef_glow_material():
    """Emissive glowing material for musical notation pieces."""
    name = MAT_NAMES['CLEF_GLOW']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (400, 0)
    _color_shader_node(bsdf, "music")
    _set_principled(bsdf,
        **{'Base Color': MATERIAL_PALETTE['CLEF_GLOW'],
           'Emission Color': MATERIAL_PALETTE['CLEF_GLOW']},
        Roughness=0.3)
    bsdf.inputs['Emission Strength'].default_value = 3.0

    # Pulse Value driver-able
    pulse = nt.nodes.new('ShaderNodeValue'); pulse.location = (100, -200); pulse.label = "Pulse"
    pulse.outputs[0].default_value = 3.0
    _color_shader_node(pulse, "music")
    nt.links.new(pulse.outputs[0], bsdf.inputs['Emission Strength'])

    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    fr = _frame(nt, "Clef Glow - Musical Emissive", "music", x=0, y=200)
    for n in (out, bsdf, pulse): n.parent = fr
    return mat



def build_genshin_material():
    """
    Genshin-Impact-inspired toon shader:
      * Soft 3-step cel-shading on diffuse
      * Pastel base color
      * Fresnel rim light (anime glow)
      * Subtle gradient between two tints
      * Slight emissive lift in shadows for that "always lit" Genshin feel
    """
    name = MAT_NAMES['GENSHIN']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (1500, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (1200, 0)
    _color_shader_node(bsdf, "genshin")
    _set_principled(bsdf,
        Roughness=0.35,
        **{'Specular IOR Level': 0.3})
    if 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = 0.4

    # Layer Weight for cel-shading  (facing -> mid -> grazing)
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.location = (-200, 200)
    lw.inputs['Blend'].default_value = 0.4
    _color_shader_node(lw, "genshin")

    # 3-step color ramp (cel shading)
    cel_ramp = nt.nodes.new('ShaderNodeValToRGB'); cel_ramp.location = (100, 200)
    _color_shader_node(cel_ramp, "ornament")
    cr = cel_ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.50, 0.42, 0.55, 1.0)  # shadow
    e1 = cr.elements.new(0.5); e1.color = (0.90, 0.80, 0.92, 1.0)                  # mid
    cr.elements[2].position = 1.0; cr.elements[2].color = (1.0, 0.95, 0.98, 1.0)  # highlight
    nt.links.new(lw.outputs['Facing'], cel_ramp.inputs['Fac'])

    # Pastel tint multiply
    tint = nt.nodes.new('ShaderNodeRGB'); tint.location = (-200, 0); tint.label = "Pastel Tint"
    tint.outputs[0].default_value = MATERIAL_PALETTE['GENSHIN']
    _color_shader_node(tint, "genshin")

    mix_tint = nt.nodes.new('ShaderNodeMixRGB'); mix_tint.location = (400, 0)
    mix_tint.blend_type = 'MULTIPLY'
    mix_tint.inputs['Fac'].default_value = 0.6
    _color_shader_node(mix_tint, "ornament")
    nt.links.new(cel_ramp.outputs['Color'], mix_tint.inputs['Color1'])
    nt.links.new(tint.outputs[0], mix_tint.inputs['Color2'])

    # Rim light (Fresnel)
    fres = nt.nodes.new('ShaderNodeFresnel'); fres.location = (-200, -250); fres.label = "Rim"
    fres.inputs['IOR'].default_value = 1.6
    _color_shader_node(fres, "ornament")

    rim_color = nt.nodes.new('ShaderNodeRGB'); rim_color.location = (100, -250); rim_color.label = "Rim Color"
    rim_color.outputs[0].default_value = (1.0, 0.92, 0.95, 1.0)  # warm pink rim
    _color_shader_node(rim_color, "genshin")

    rim_mul = nt.nodes.new('ShaderNodeMixRGB'); rim_mul.location = (400, -250)
    rim_mul.blend_type = 'MULTIPLY'
    rim_mul.inputs['Fac'].default_value = 1.0
    nt.links.new(fres.outputs[0], rim_mul.inputs['Color1'])
    nt.links.new(rim_color.outputs[0], rim_mul.inputs['Color2'])

    rim_add = nt.nodes.new('ShaderNodeMixRGB'); rim_add.location = (700, 0)
    rim_add.blend_type = 'ADD'
    rim_add.inputs['Fac'].default_value = 0.6
    _color_shader_node(rim_add, "ornament")
    nt.links.new(mix_tint.outputs['Color'], rim_add.inputs['Color1'])
    nt.links.new(rim_mul.outputs['Color'], rim_add.inputs['Color2'])

    # Final -> BSDF base + emission (so shadows still glow softly)
    nt.links.new(rim_add.outputs['Color'], bsdf.inputs['Base Color'])
    if 'Emission Color' in bsdf.inputs:
        nt.links.new(rim_mul.outputs['Color'], bsdf.inputs['Emission Color'])

    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    fr = _frame(nt, "Genshin Toon - cel-shaded, pastel, Fresnel-rim", "genshin", x=-300, y=350)
    for n in (out, bsdf, lw, cel_ramp, tint, mix_tint, fres, rim_color, rim_mul, rim_add):
        n.parent = fr
    return mat



def build_world_shader():
    """Day/night world: Hosek-Wilkie sky mixed with night sky."""
    world = bpy.data.worlds.get(WORLD_NAME) or bpy.data.worlds.new(name=WORLD_NAME)
    world.use_nodes = True
    nt = world.node_tree; nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputWorld'); out.location = (1000, 0)
    bg = nt.nodes.new('ShaderNodeBackground'); bg.location = (700, 0)
    _color_shader_node(bg, "output")

    sky = nt.nodes.new('ShaderNodeTexSky'); sky.location = (-200, 200); sky.label = "Sun Sky"
    _color_shader_node(sky, "input")
    sky.sky_type = 'HOSEK_WILKIE'
    sky.sun_elevation = math.radians(40)  # default mid-day
    sky.turbidity = 2.5

    # Night color - RGB node so user can re-tint
    night = nt.nodes.new('ShaderNodeRGB'); night.location = (-200, -200); night.label = "Night Color"
    _color_shader_node(night, "ornament")
    night.outputs[0].default_value = (0.02, 0.04, 0.10, 1.0)

    # Time-of-day mix factor (driven by surreal_arch_props.time_of_day)
    tod = nt.nodes.new('ShaderNodeValue'); tod.location = (-200, 0); tod.label = "Night Blend"
    _color_shader_node(tod, "music")
    tod.outputs[0].default_value = 0.0

    mix = nt.nodes.new('ShaderNodeMix'); mix.location = (300, 0); mix.data_type = 'RGBA'
    _color_shader_node(mix, "ornament")
    nt.links.new(sky.outputs['Color'], mix.inputs[6])
    nt.links.new(night.outputs[0], mix.inputs[7])
    nt.links.new(tod.outputs[0], mix.inputs['Factor'])

    nt.links.new(mix.outputs['Result'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

    fr = _frame(nt, "Day / Night Sky - Time of Day Mix", "music", x=-300, y=400)
    for n in (out, bg, sky, night, tod, mix): n.parent = fr
    return world



def build_shader_library():
    """Build (or refresh) all materials and the world shader. Idempotent."""
    materials = {
        'STONE':       build_base_material(),
        'MARBLE':      build_marble_material(),
        'WATER':       build_musical_water_material(),
        'STAINED':     build_stained_glass_material(),
        'IRIDESCENT':  build_iridescent_material(),
        'GOLD':        build_gold_material(),
        'CLEF_GLOW':   build_clef_glow_material(),
        'GOTHIC_DARK': build_gothic_dark_material(),
        'GENSHIN':     build_genshin_material(),
    }
    world = build_world_shader()
    return materials, world


# Default material recommendation per architecture type

def _color_shader_node(n, color_key):
    """Pastel-color a shader node using the same palette as geometry nodes."""
    if color_key in COLORS:
        n.use_custom_color = True
        n.color = COLORS[color_key]



def _set_principled(bsdf, **kwargs):
    """Safely set Principled BSDF inputs by name (skips unknown keys)."""
    for k, v in kwargs.items():
        if k in bsdf.inputs:
            try: bsdf.inputs[k].default_value = v
            except: pass



def _frame(tree, label, color_key, x=0, y=0):
    """Create a labelled, color-coded NodeFrame in any node tree."""
    f = tree.nodes.new('NodeFrame')
    f.label = label
    f.location = (x, y)
    f.use_custom_color = True
    if color_key in COLORS:
        f.color = COLORS[color_key]
    return f



def build_gothic_dark_material():
    name = MAT_NAMES['GOTHIC_DARK']
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); out.location = (700, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (400, 0)
    _color_shader_node(bsdf, "gothic")
    _set_principled(bsdf,
        **{'Base Color': MATERIAL_PALETTE['GOTHIC_DARK']},
        Roughness=0.85)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.location = (0, -200)
    _color_shader_node(noise, "noise")
    noise.inputs['Scale'].default_value = 12.0
    noise.inputs['Detail'].default_value = 8.0
    bump = nt.nodes.new('ShaderNodeBump'); bump.location = (200, -200)
    bump.inputs['Strength'].default_value = 0.3
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    fr = _frame(nt, "Gothic Dark - Worn Stone", "gothic", x=-100, y=200)
    for n in (out, bsdf, noise, bump): n.parent = fr
    return mat


# ----------------------------------------------------------------------
# WORLD SHADER  -  day/night sky synced to time-of-day prop
# ----------------------------------------------------------------------



# Track in registry metadata (role="material", no GN Stack entry).
for _n in ("build_base_material","build_marble_material","build_musical_water_material",
           "build_stained_glass_material","build_iridescent_material","build_gold_material",
           "build_clef_glow_material","build_genshin_material","build_world_shader",
           "build_shader_library"):
    core.GROUP_METADATA[_n] = {
        "label": _n.replace("build_", "").replace("_", " ").title(),
        "description": "Material builder (absorbed from monolith).",
        "category": "materials", "builder": None, "hidden": True,
        "role": "material", "params": None,
    }
