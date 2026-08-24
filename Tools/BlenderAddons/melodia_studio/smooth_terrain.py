"""Smooth terrain mesh generator — replaces voxel cubes with continuous landscape.

Takes the walkable heightfield and produces a smooth, biomes-colored mesh:
- Bilinear subdivision (each cell → 4×4 sub-cells)
- Smooth shading
- Biome vertex colors (peak=snow, valley=grass, slope=rock, path=sand)
- Deterministic (seed 3900)

Pure Python + bpy. Blender 5.2 compatible.
"""

import bpy
import os
import sys
import math
import random

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)

import walkable_world as ww
import terrain_dressing as td

BIOME_COLORS = {
    "peak": (0.95, 0.95, 0.98),    # snow
    "ridge": (0.75, 0.70, 0.65),   # rocky
    "slope": (0.55, 0.50, 0.45),   # dirt/rock
    "path": (0.85, 0.80, 0.65),    # sand
    "valley": (0.35, 0.55, 0.30),  # grass
}


def generate_smooth_terrain(midi_path, preset_id="walkable_valley"):
    """Generate a smooth terrain mesh from MIDI.

    Returns bpy mesh or None.
    """
    field, preset, _metrics = _build_field(midi_path, preset_id)
    if field is None:
        return None

    # Subdivide heightfield
    subdivided = _subdivide_field(field, factor=4)

    # Build mesh
    mesh = _build_mesh(subdivided, field)

    return mesh


def _build_field(midi_path, preset_id):
    """Build heightfield from MIDI."""
    mv = ww.load_voxel_module()
    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return None, None, None
    preset = ww.WALKABLE_PRESETS.get(preset_id)
    if preset is None:
        return None, None, None
    notes = list(tracks[0])
    stem, ext = os.path.splitext(midi_path)
    bg = stem + "_beatgrid" + ext
    if os.path.exists(bg):
        b_tracks, b_tpb = mv.parse_midi(bg)
        if b_tracks and b_tpb:
            scale = float(tpb) / float(b_tpb)
            notes.extend((int(n[0] * scale), n[1] + 36, n[2]) for n in b_tracks[0])
            notes.sort()
    field, _gw = ww.build_heightfield(
        notes, preset["cells_per_beat"], preset["height_scale"],
        preset["plateau_radius"], tpb, preset.get("fold", "serpentine"))
    field = ww.limit_slope(ww.fill_gaps(field), preset["max_slope"],
                           preset["smooth_passes"])
    metrics = ww.walkability(field, preset["max_slope"])
    return field, preset, metrics


def _subdivide_field(field, factor=4):
    """Bilinear subdivision of heightfield."""
    if not field:
        return {}

    xs = [k[0] for k in field]
    ys = [k[1] for k in field]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    result = {}
    for x in range(x_min * factor, (x_max + 1) * factor):
        for y in range(y_min * factor, (y_max + 1) * factor):
            # Bilinear interpolation
            x0 = x / factor
            y0 = y / factor
            x_low = int(math.floor(x0))
            y_low = int(math.floor(y0))
            x_high = x_low + 1
            y_high = y_low + 1

            # Get corner heights
            h_ll = field.get((x_low, y_low), (0, 0))[0]
            h_lh = field.get((x_low, y_high), (0, 0))[0]
            h_hl = field.get((x_high, y_low), (0, 0))[0]
            h_hh = field.get((x_high, y_high), (0, 0))[0]

            # Bilinear
            fx = x0 - x_low
            fy = y0 - y_low
            h = (h_ll * (1 - fx) * (1 - fy) +
                 h_hl * fx * (1 - fy) +
                 h_lh * (1 - fx) * fy +
                 h_hh * fx * fy)

            # Velocity from nearest cell
            nearest = field.get((x_low, y_low), (0, 0))[1]
            result[(x, y)] = (h, nearest)

    return result


def _build_mesh(subdivided, original_field):
    """Build smooth mesh from subdivided heightfield."""
    if not subdivided:
        return None

    xs = [k[0] for k in subdivided]
    ys = [k[1] for k in subdivided]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    verts = []
    faces = []
    colors = []

    # Classify cells for biome coloring
    tags = td.classify_cells(original_field)

    # Create vertices
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            h, vel = subdivided.get((x, y), (0, 0))
            verts.append((x, y, h))

            # Determine biome color
            orig_cell = (int(x / factor), int(y / factor))
            tag_info = tags.get(orig_cell, {})
            tag = tag_info.get("tag", "slope")
            color = BIOME_COLORS.get(tag, BIOME_COLORS["slope"])
            colors.append((*color, 1.0))

    # Create faces
    width = x_max - x_min + 1
    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            i0 = (x - x_min) + (y - y_min) * width
            i1 = (x + 1 - x_min) + (y - y_min) * width
            i2 = (x - x_min) + (y + 1 - y_min) * width
            i3 = (x + 1 - x_min) + (y + 1 - y_min) * width
            faces.append([i0, i1, i3, i2])

    # Create mesh
    mesh = bpy.data.meshes.new("SmoothTerrain")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # Vertex colors
    attr = mesh.color_attributes.new(name="BiomeColor", type='FLOAT_COLOR',
                                     domain='CORNER')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            if vi < len(colors):
                attr.data[li].color = colors[vi]

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    return mesh
