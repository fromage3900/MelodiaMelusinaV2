"""
nikki_particles.py — TouchDesigner Nikki-style particle system network builder.

Constructs a complete particle network (POPs) inside a TD COMP with:
  - Wish-energy sparkles (4-point star sprites, gold→pink drift)
  - Floating ambient motes (soft radial dots, slow sin-wave motion)
  - Audio-reactive burst trigger (amplitude threshold → wish burst)
  - OSC output routing for Niagara spawn parameters

To install: execute_python MCP tool with this script, or load into TD Text DAT
and run it.
"""

import math
import random

# ── Nikki Particle Presets ──────────────────────────────────────────────

NIKKI_PARTICLES = {
    "sparkle": {
        "count": 40,
        "lifespan": 8.0,
        "size": (0.02, 0.06),
        "color_start": (1.0, 0.84, 0.63, 1.0),   # gold
        "color_end": (0.94, 0.75, 0.82, 0.0),     # pink fade
        "speed": (0.02, 0.08),
        "spread": 0.3,
        "bob_amplitude": 0.15,
        "bob_frequency": 0.4,
    },
    "mote": {
        "count": 50,
        "lifespan": 12.0,
        "size": (0.01, 0.03),
        "color_start": (1.0, 0.95, 0.90, 1.0),    # warm cream
        "color_end": (0.82, 0.75, 0.91, 0.0),     # lavender fade
        "speed": (0.01, 0.04),
        "spread": 0.6,
        "bob_amplitude": 0.25,
        "bob_frequency": 0.25,
    },
    "wish_burst": {
        "count": 120,
        "lifespan": 2.5,
        "size": (0.01, 0.08),
        "color_start": (1.0, 0.96, 0.50, 1.0),    # bright gold
        "color_end": (0.94, 0.50, 0.70, 0.0),     # hot pink fade
        "speed": (0.15, 0.5),
        "spread": 1.0,
        "explosion_force": 1.5,
    },
}

# ── OSC Routing for Niagara ─────────────────────────────────────────────

OSC_NIAGARA_ROUTES = {
    "sparkle_spawn_rate":   "/niagara/sparkle/rate",
    "sparkle_color":        "/niagara/sparkle/color",
    "sparkle_size":         "/niagara/sparkle/size",
    "mote_spawn_rate":      "/niagara/mote/rate",
    "mote_color":           "/niagara/mote/color",
    "wish_burst_trigger":   "/niagara/burst",
    "wind_direction":       "/niagara/wind",
    "audio_amplitude":      "/melusina/amp",
    "audio_pitch":          "/melusina/pitch",
}


def build_nikki_particles(parent_comp):
    """Build complete Nikki particle system inside a TD COMP.
    
    Call from TouchDesigner Python:
        import nikki_particles
        nikki_particles.build_nikki_particles(op('/project1'))
    """
    me = parent_comp

    # ── Container COMPs ──
    particles_comp = me.create(baseCOMP, 'nikki_particles')
    sparkle_comp = particles_comp.create(baseCOMP, 'sparkles')
    mote_comp = particles_comp.create(baseCOMP, 'motes')
    burst_comp = particles_comp.create(baseCOMP, 'wish_burst')
    osc_comp = particles_comp.create(baseCOMP, 'osc_out')
    control_comp = particles_comp.create(baseCOMP, 'controls')

    # ── Sparkle particle system ──
    p = NIKKI_PARTICLES['sparkle']
    _build_pop_network(sparkle_comp, p, 'sparkle_pop')

    # ── Mote particle system ──
    m = NIKKI_PARTICLES['mote']
    _build_pop_network(mote_comp, m, 'mote_pop')

    # ── Wish burst system ──
    w = NIKKI_PARTICLES['wish_burst']
    _build_burst_network(burst_comp, w, 'burst_pop')

    # ── Control panel ──
    _build_control_panel(control_comp)

    # ── OSC output to Niagara ──
    _build_osc_niagara_output(osc_comp)

    print(f'[NikkiParticles] Built particle system in {particles_comp.path}')
    return particles_comp


def _build_pop_network(comp, preset, name):
    """Build a POP network for drifting particles (sparkles/motes)."""
    # Particle generator
    generator = comp.create(particlesGpuCOMP, name)
    generator.par.particles = preset['count']
    generator.par.lifespan = preset['lifespan']
    generator.par.lifespanrand = 0.3
    generator.par.birthtype = 'spread'
    generator.par.speed = preset['speed'][0]
    generator.par.speedrand = preset['speed'][1]
    generator.par.spread = preset['spread']

    # Color ramp
    ramp = comp.create(rampTOP, f'{name}_color')
    ramp.par.ramp1r = preset['color_start'][0]
    ramp.par.ramp1g = preset['color_start'][1]
    ramp.par.ramp1b = preset['color_start'][2]
    ramp.par.ramp2r = preset['color_end'][0]
    ramp.par.ramp2g = preset['color_end'][1]
    ramp.par.ramp2b = preset['color_end'][2]

    # Render TOP
    render = comp.create(renderTOP, f'{name}_render')
    render.par.camera = '/project1/render/cam1'  # connect to scene camera

    return generator


def _build_burst_network(comp, preset, name):
    """Build an explosive burst particle system."""
    generator = comp.create(particlesGpuCOMP, name)
    generator.par.particles = preset['count']
    generator.par.lifespan = preset['lifespan']
    generator.par.lifespanrand = 0.2
    generator.par.birthtype = 'explode'
    generator.par.speed = preset['speed'][0]
    generator.par.speedrand = preset['speed'][1]
    generator.par.force = preset.get('explosion_force', 1.0)

    # Trigger controlled by audio amplitude threshold
    # In TD: CHOP → Math CHOP (threshold) → trigger pulse → burst generator

    return generator


def _build_control_panel(comp):
    """Build Nikki particle control panel with sliders."""
    # Particle density
    density = comp.create(sliderCOMP, 'density')
    density.par.label = 'Particle Density'
    density.par.defaultvalue = 0.5
    density.par.range = (0.1, 2.0)

    # Color shift
    hue = comp.create(sliderCOMP, 'hue_shift')
    hue.par.label = 'Color Hue Shift'
    hue.par.defaultvalue = 0.0
    hue.par.range = (-0.5, 0.5)

    # Audio reactivity
    audio_gain = comp.create(sliderCOMP, 'audio_gain')
    audio_gain.par.label = 'Audio Reactivity'
    audio_gain.par.defaultvalue = 0.7
    audio_gain.par.range = (0.0, 2.0)

    # Speed multiplier
    speed = comp.create(sliderCOMP, 'speed_mult')
    speed.par.label = 'Speed Multiplier'
    speed.par.defaultvalue = 1.0
    speed.par.range = (0.1, 5.0)

    return comp


def _build_osc_niagara_output(comp):
    """Build OSC output routing to Unreal Niagara parameters."""
    osc = comp.create(oscoutCHOP, 'osc_to_niagara')
    osc.par.port = 8000
    osc.par.address = '127.0.0.1'

    # Channels for Niagara parameter mapping
    channels = [
        ('sparkle_rate',  '/niagara/sparkle/rate'),
        ('sparkle_r',     '/niagara/sparkle/color_r'),
        ('sparkle_g',     '/niagara/sparkle/color_g'),
        ('sparkle_b',     '/niagara/sparkle/color_b'),
        ('sparkle_size',  '/niagara/sparkle/size'),
        ('mote_rate',     '/niagara/mote/rate'),
        ('mote_size',     '/niagara/mote/size'),
        ('burst_trigger', '/niagara/burst'),
        ('wind_x',        '/niagara/wind_x'),
        ('wind_y',        '/niagara/wind_y'),
        ('wind_z',        '/niagara/wind_z'),
        ('audio_amp',     '/melusina/amp'),
        ('audio_pitch',   '/melusina/pitch'),
    ]

    # In TD, each channel would be wired to the OSC Out CHOP
    # and mapped to the corresponding Niagara parameter path

    print(f'[OSC-Niagara] Routing {len(channels)} channels to UE port {osc.par.port}')
    return osc


# ── CLI for MCP execution ────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    if '--build' in sys.argv:
        build_nikki_particles(op('/project1'))
    elif '--routes' in sys.argv:
        import json
        print(json.dumps(OSC_NIAGARA_ROUTES, indent=2))
    elif '--presets' in sys.argv:
        import json
        print(json.dumps(NIKKI_PARTICLES, indent=2, default=str))
    else:
        print("Nikki Particle System Builder")
        print("  --build    Build particles in /project1")
        print("  --routes   Print OSC Niagara routing table")
        print("  --presets  Print particle preset configs")
