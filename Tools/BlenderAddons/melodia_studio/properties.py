"""Melodia Studio - AddonPreferences + StudioProps + enum helpers.

Split out of studio_panel.py on 2026-10-04 (monolith split, no logic change).
Registration happens in the studio_panel facade, in the original order.
"""

import os
import sys

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_bridge
from . import midi_picker


# ------------------------------------------------------------- enum helpers

def _preset_enum(self, context):
    items = midi_bridge.preset_items()
    return items if items else [("resonant_default", "Resonant Default", "")]


def _midi_enum(self, context):
    # Allow filtering by search string
    filt = ""
    try:
        filt = (context.scene.melodia_studio.midi_filter or "").strip().lower()
    except Exception:
        pass
    found = midi_picker._discover_cached()
    if filt:
        found = [p for p in found if filt in os.path.basename(p).lower() or filt in p.lower()]
    if not found:
        # Keep operator reachable even with no results
        if filt:
            return [("", f"No match for '{filt}'", "")]
        return [("", "No MIDI found", "")]
    root = midi_bridge.repo_root()
    items = []
    for path in found[:64]:
        try:
            label = os.path.relpath(path, root)
        except ValueError:
            label = os.path.basename(path)
        # label shown in dropdown; path is the value
        items.append((path, os.path.basename(path), label))
    return items


def _dressing_items():
    """Dressing styles - single source of truth from terrain_dressing.
    Falls back to a minimal list if terrain_dressing is unavailable."""
    try:
        from . import terrain_dressing as td
        items = []
        for key, val in sorted(td.DRESSING_STYLES.items()):
            items.append((key, val.get("label", key), val.get("description", "")))
        return items if items else [("bare", "Bare", "")]
    except Exception:
        return [
            ("bare", "Bare", "Control case"),
            ("verdant", "Verdant Resonance", "Lush walkable ground, soft magic"),
            ("crystalline", "Crystalline Choir", "Hard glowing mineral world"),
            ("cathedral", "Sunken Cathedral", "Flooded basin, tall pillars"),
            ("full_bloom", "Full Bloom", "Everything on"),
        ]


def _tandem_preset_items(self, context):
    """Merged preset list for tandem: walkable + voxel. Indicates walkable vs voxel."""
    items = []
    try:
        from . import walkable_world as ww
        for key, val in sorted(ww.WALKABLE_PRESETS.items()):
            items.append((key, val.get("label", key) + " [Walkable]", val.get("description", "")))
    except Exception:
        pass
    try:
        mid = midi_bridge.preset_items()
        for key, label, desc in mid:
            # avoid dup if same key as walkable
            if not any(k == key for k, _, _ in items):
                items.append((key, label + " [Voxel]", desc))
    except Exception:
        pass
    return items if items else [("walkable_valley", "Walkable Valley [Walkable]", "")]


def _tandem_style_items(self, context):
    try:
        deploy = os.path.join(midi_bridge.repo_root(), "deploy")
        if deploy not in sys.path:
            sys.path.insert(0, deploy)
        from surreal_world import compose as _comp  # type: ignore
        return [(k, k.replace("_", " ").title(), "") for k in sorted(_comp.COMPOSE_STYLES.keys())]
    except Exception:
        # fallback to pairing keys
        try:
            from . import tandem_bridge as _tb  # type: ignore
            return [(k, k.replace("_", " ").title(), "") for k in sorted(set(v[0] for v in _tb.MELODIA_TO_SURREAL.values()))]
        except Exception:
            return [("WESTERN_CASTLE", "Western Castle", "")]


def _tandem_plan_items(self, context):
    try:
        from . import tandem_bridge as _tb  # type: ignore
        return [(k, k.replace("_", " ").title(), "") for k in _tb.PLAN_KINDS]
    except Exception:
        return [("castle", "Castle", ""), ("zen_roji", "Zen Roji", ""), ("village", "Village", "")]


# ------------------------------------------------------------- addon preferences (v1.5 +)

if bpy is not None:
    class MelodiaStudioPreferences(bpy.types.AddonPreferences):
        """Addon Preferences — C: authority root + extra MIDI dirs. Surface in Edit > Preferences > Add-ons > Melodia Studio."""
        bl_idname = "melodia_studio"

        project_root: bpy.props.StringProperty(
            name="Project Root",
            description="Override BS_GodFile root (default: auto-detect C:\\EnvironmentPortfolio\\BS_GodFile via $MELODIA_PROJECT_ROOT or walk-up). Leave empty for auto.",
            subtype='DIR_PATH',
            default="",
        )
        midi_extra_dirs: bpy.props.StringProperty(
            name="Extra MIDI Dirs",
            description="Semicolon-separated extra MIDI search dirs (e.g., G:\\MyMIDIs;D:\\Songs). Appended to Content/MelodiaIntegration/MIDI and Imports/Audio.",
            default="",
        )

        def draw(self, context):
            layout = self.layout
            layout.label(text="C Authority — empty = auto-detect (env $MELODIA_PROJECT_ROOT preferred)", icon='INFO')
            layout.prop(self, "project_root")
            layout.prop(self, "midi_extra_dirs")
            # hint
            row = layout.row()
            row.label(text="Extra dirs are appended to discover_midi()", icon='FILE_SOUND')


    class StudioProps(bpy.types.PropertyGroup):
        midi_file: bpy.props.EnumProperty(
            name="MIDI",
            description="Project MIDI to build terrain from (filtered by Search)",
            items=_midi_enum,
        )
        midi_filter: bpy.props.StringProperty(
            name="Search",
            description="Filter MIDI list (substring, case-insensitive)",
            default="",
            options={'TEXTEDIT_UPDATE'},
        )
        preset: bpy.props.EnumProperty(
            name="Preset",
            description="Musical to spatial mapping preset",
            items=_preset_enum,
        )
        custom_midi: bpy.props.StringProperty(
            name="Custom MIDI",
            description="Override with a MIDI file outside the project",
            subtype='FILE_PATH',
            default="",
        )
        dressing_style: bpy.props.EnumProperty(
            name="Dressing",
            description="Musical expansion preset applied to the terrain mesh",
            items=_dressing_items(),
            default="verdant",
        )
        auto_cleanup: bpy.props.BoolProperty(
            name="Auto-cleanup old Terrain",
            description="Remove previous Terrain / MS_* objects before generating",
            default=True,
        )
        last_report: bpy.props.StringProperty(name="Last Report", default="")
        last_midi: bpy.props.StringProperty(name="Last MIDI", default="")
        show_advanced: bpy.props.BoolProperty(
            name="Advanced",
            description="Show advanced/debug options",
            default=False,
        )
        # Tandem (terrain -> surreal city) - field-wins, snap plan to terrain height
        tandem_preset: bpy.props.EnumProperty(
            name="Tandem Preset",
            description="Preset that drives both terrain shape and city pairing (walkable preferred for clean ground)",
            items=_tandem_preset_items,
            default=0,
        )
        tandem_style: bpy.props.EnumProperty(
            name="Style",
            description="Surreal COMPOSE_STYLE override (empty = auto from preset pairing)",
            items=_tandem_style_items,
        )
        tandem_plan: bpy.props.EnumProperty(
            name="Plan",
            description="Surreal plan kind (castle/zen_roji/village etc). Empty = auto from preset",
            items=_tandem_plan_items,
        )
        dress_instance: bpy.props.BoolProperty(
            name="Instance Dressing",
            description="Actually instance dressing props as linked objects (not just count string)",
            default=True,
        )
        dress_seed: bpy.props.IntProperty(
            name="Seed",
            description="Deterministic seed for dressing placement",
            default=11,
            min=0, max=9999,
        )
        dress_budget: bpy.props.IntProperty(
            name="Budget",
            description="Max props to instance",
            default=400,
            min=0, max=5000,
        )

else:
    MelodiaStudioPreferences = object  # type: ignore
    StudioProps = object  # type: ignore
