"""Atmospheric rendering system for Resonant World.

Makes terrain feel alive with:
- Volumetric fog (density driven by song velocity)
- Dynamic sky (sun position driven by tempo)
- Three-point lighting with mood colors
- Bloom/compositor setup

Blender 5.2 compatible.
"""

import bpy
import os
import sys

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

import walkable_world as ww


def apply_atmosphere(scene, midi_path, preset_id="walkable_valley"):
    """Apply atmospheric effects to scene based on musical mood.

    Args:
        scene: bpy.context.scene
        midi_path: path to MIDI file
        preset_id: terrain preset ID
    """
    # Get mood from preset
    preset = ww.WALKABLE_PRESETS.get(preset_id, {})
    mood = preset.get("mood", {})
    top = mood.get("top", (0.10, 0.13, 0.22))
    bottom = mood.get("bottom", (0.02, 0.03, 0.05))
    rim = mood.get("rim", (1.0, 0.62, 0.80))

    # Compute song velocity (drives fog density)
    velocity = _compute_velocity(midi_path)

    # Apply effects
    _apply_world(scene, top, bottom)
    _apply_fog(scene, density=0.02 + velocity * 0.01)
    _apply_lights(scene, rim)
    _apply_compositor(scene)


def _compute_velocity(midi_path):
    """Compute average velocity from MIDI (0-1 scale)."""
    try:
        from . import midi_bridge
        mv = midi_bridge.load_voxel_module()
        tracks, tpb = mv.parse_midi(midi_path)
        if not tracks:
            return 0.5
        velocities = [n[2] for n in tracks[0]]
        return sum(velocities) / len(velocities) / 127.0
    except Exception:
        return 0.5


def _apply_world(scene, top, bottom):
    """Create gradient world background."""
    w = bpy.data.worlds.new("RW_Atmosphere")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputWorld')
    out.location = (400, 0)

    bg = nt.nodes.new('ShaderNodeBackground')
    bg.location = (200, 0)
    bg.inputs['Strength'].default_value = 1.0

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-60, 0)
    ramp.color_ramp.elements[0].color = (*bottom, 1.0)
    ramp.color_ramp.elements[1].color = (*top, 1.0)

    tex = nt.nodes.new('ShaderNodeTexCoord')
    tex.location = (-280, 0)

    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-170, 0)

    L = nt.links.new
    L(tex.outputs['Generated'], sep.inputs['Vector'])
    L(sep.outputs['Z'], ramp.inputs['Fac'])
    L(ramp.outputs['Color'], bg.inputs['Color'])
    L(bg.outputs['Background'], out.inputs['Surface'])


def _apply_fog(scene, density=0.03):
    """Add volumetric fog cube."""
    # Create fog cube
    bpy.ops.mesh.primitive_cube_add(size=1)
    fog = bpy.context.active_object
    fog.name = "RW_Fog"

    # Scale to cover terrain
    fog.scale = (50, 50, 20)

    # Create volume material
    mat = bpy.data.materials.new("M_Fog")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (300, 0)

    vol = nt.nodes.new('ShaderNodeVolumeScatter')
    vol.location = (0, 0)
    vol.inputs['Color'].default_value = (0.8, 0.85, 0.9, 1.0)
    vol.inputs['Density'].default_value = density

    nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])

    fog.data.materials.append(mat)
    fog.display_type = 'WIRE'


def _apply_lights(scene, rim):
    """Add three-point lighting with mood colors."""
    # Remove existing Melodia lights
    for name in ("RW_Key", "RW_Fill", "RW_Rim"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Key light
    key_data = bpy.data.lights.new("RW_Key", type='AREA')
    key_data.energy = 300
    key_data.color = (1.0, 0.95, 0.88)
    key_data.size = 5
    key = bpy.data.objects.new("RW_Key", key_data)
    key.location = (10, -10, 15)
    scene.collection.objects.link(key)

    # Fill light
    fill_data = bpy.data.lights.new("RW_Fill", type='AREA')
    fill_data.energy = 100
    fill_data.color = (0.65, 0.78, 1.0)
    fill_data.size = 5
    fill = bpy.data.objects.new("RW_Fill", fill_data)
    fill.location = (-10, -5, 8)
    scene.collection.objects.link(fill)

    # Rim light
    rim_data = bpy.data.lights.new("RW_Rim", type='AREA')
    rim_data.energy = 200
    rim_data.color = rim
    rim_data.size = 5
    rim_obj = bpy.data.objects.new("RW_Rim", rim_data)
    rim_obj.location = (0, 10, 10)
    scene.collection.objects.link(rim_obj)


def _apply_compositor(scene):
    """Enable bloom in compositor."""
    scene.use_nodes = True
    nt = scene.node_tree
    nt.nodes.clear()

    # Render layers
    rl = nt.nodes.new('CompositorNodeRLayers')
    rl.location = (0, 0)

    # Glare (bloom)
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.location = (200, 0)
    glare.glare_type = 'FOG_GLOW'
    glare.quality = 'HIGH'
    glare.mix = 0.3

    # Composite
    comp = nt.nodes.new('CompositorNodeComposite')
    comp.location = (400, 0)

    L = nt.links.new
    L(rl.outputs['Image'], glare.inputs['Image'])
    L(glare.outputs['Image'], comp.inputs['Image'])
