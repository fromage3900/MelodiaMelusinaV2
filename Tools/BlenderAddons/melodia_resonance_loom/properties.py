# Resonance Loom - Blender scene properties (bpy imported only by Blender).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT

from __future__ import annotations

import bpy

from .loom_core import lanes


def _skill_id_items(_self, _context):
    """Stable sorted enum of the eight authored rhythm ids."""
    return [(sid, sid, sid) for sid in sorted(lanes.SKILL_IDS)]


def _lane_strategy_items(_self, _context):
    """Deterministic lane arrangement strategies (presentation only)."""
    return [(s, s, s) for s in lanes.LANE_STRATEGIES]


class LOOM_PG_scene(bpy.types.PropertyGroup):
    """Per-scene Loom state. Everything here is derived or authored, never simulated."""

    midi_path: bpy.props.StringProperty(
        name="Beatgrid MIDI",
        description="Project beat authority (128BPMarpeggiomelody_beatgrid.mid)",
        subtype="FILE_PATH",
    )
    skill_id: bpy.props.EnumProperty(
        name="Rhythm Skill",
        description="Which authored rhythm session drives this garment's flourish",
        items=_skill_id_items,
    )
    cosmetic_id: bpy.props.StringProperty(
        name="Cosmetic ID",
        description="Cos_<Name> id from the garment's draft JSON",
    )
    bpm: bpy.props.FloatProperty(name="BPM", description="Tempo parsed from the beatgrid", default=0.0)
    duration_sec: bpy.props.FloatProperty(name="Duration (s)", default=0.0)
    pattern_density: bpy.props.FloatProperty(name="Density", default=0.0)
    lane_hits_json: bpy.props.StringProperty(
        name="Lane Hits",
        description="Per-lane hit counts as JSON (Q/W/O/P single-source vocabulary)",
        default="{}",
    )
    lane_strategy: bpy.props.EnumProperty(
        name="Lane Strategy",
        description="How note onsets map to the Q/W/O/P lanes (presentation only)",
        items=_lane_strategy_items,
    )
    beatgrid_loaded: bpy.props.BoolProperty(name="Beatgrid Loaded", default=False)
    bake_scale: bpy.props.FloatProperty(
        name="Bake Scale (m)",
        description="Peak vertex displacement per unit weight (Tier A authored motion)",
        default=0.08,
        min=0.001,
        max=1.0,
    )
    output_dir: bpy.props.StringProperty(
        name="Export Directory",
        description="Default FBX + sidecar destination (repo Imports/Meshes/Loom)",
        subtype="DIR_PATH",
    )


def register() -> None:
    bpy.utils.register_class(LOOM_PG_scene)
    bpy.types.Scene.loom = bpy.props.PointerProperty(type=LOOM_PG_scene)


def unregister() -> None:
    del bpy.types.Scene.loom
    bpy.utils.unregister_class(LOOM_PG_scene)
