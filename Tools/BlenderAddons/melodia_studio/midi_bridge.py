"""MIDI bridge for Melodia Studio.

Connects the Blender addon to the proven voxel generator at
Tools/midi_to_voxel/midi_voxel_v3.py. Previously the addon did a bare
`from midi_voxel_v3 import ...` with that directory never on sys.path, and
resolved STUDIO_ROOT to Tools/Tools/MelodiaProceduralStudio, so the
"Load MIDI" button could never work.

Offline-safe: importing this module does not require bpy.
"""

import os
import sys
import json

# ---------------------------------------------------------------- paths

def _addon_dir():
    return os.path.dirname(os.path.abspath(__file__))


def repo_root():
    """BS_GodFile root, from Tools/BlenderAddons/melodia_studio/ -> up 3."""
    return os.path.normpath(os.path.join(_addon_dir(), "..", "..", ".."))


def studio_root():
    """Tools/MelodiaProceduralStudio (the old '..','..','Tools' was wrong)."""
    return os.path.join(repo_root(), "Tools", "MelodiaProceduralStudio")


def voxel_tool_dir():
    return os.path.join(repo_root(), "Tools", "midi_to_voxel")


def midi_content_dir():
    return os.path.join(repo_root(), "Content", "MelodiaIntegration", "MIDI")


def scenes_dir():
    return os.path.join(studio_root(), "GeneratedScenes")


def presets_path():
    return os.path.join(studio_root(), "midi_presets.json")


# ---------------------------------------------------------------- import

def load_voxel_module():
    """Import midi_voxel_v3 by putting its real directory on sys.path."""
    vdir = voxel_tool_dir()
    if not os.path.isdir(vdir):
        raise RuntimeError("midi_to_voxel not found: %s" % vdir)
    if vdir not in sys.path:
        sys.path.insert(0, vdir)
    import midi_voxel_v3
    return midi_voxel_v3


def walkable_tool_dir():
    return os.path.join(repo_root(), "Tools", "BlenderAddons", "melodia_studio")


# ---------------------------------------------------------------- presets

# Musical -> spatial mapping presets. chunk_beats controls how much song
# time is packed per world chunk; the scale/height factors shape relief.
DEFAULT_PRESETS = {
    "resonant_default": {
        "label": "Resonant Default",
        "description": "Balanced 4-beat chunks; melody surface + cave layer.",
        "chunk_beats": 4,
        "surface_height_divisor": 32,
        "cave_height_divisor": 40,
        "use_beatgrid": True,
        "aura_emission": 3.0,
    },
    "cathedral_wide": {
        "label": "Cathedral (Wide)",
        "description": "8-beat chunks stretch time; tall naves, sparse pillars.",
        "chunk_beats": 8,
        "surface_height_divisor": 20,
        "cave_height_divisor": 50,
        "use_beatgrid": True,
        "aura_emission": 4.5,
    },
    "dense_spire": {
        "label": "Dense Spire",
        "description": "2-beat chunks compress time; jagged vertical terrain.",
        "chunk_beats": 2,
        "surface_height_divisor": 16,
        "cave_height_divisor": 32,
        "use_beatgrid": True,
        "aura_emission": 2.5,
    },
    "surface_only": {
        "label": "Surface Only",
        "description": "Melody terrain with no cave layer; clean silhouette.",
        "chunk_beats": 4,
        "surface_height_divisor": 32,
        "cave_height_divisor": 40,
        "use_beatgrid": False,
        "aura_emission": 3.0,
    },
    "abyss_caves": {
        "label": "Abyss Caves",
        "description": "Deep beatgrid caverns dominate; low melody relief.",
        "chunk_beats": 4,
        "surface_height_divisor": 48,
        "cave_height_divisor": 20,
        "use_beatgrid": True,
        "aura_emission": 3.5,
    },
    "waltz_corridors": {
        "label": "Waltz Corridors",
        "description": "3-beat triple-meter chunks; flowing, interconnected corridors.",
        "chunk_beats": 3,
        "surface_height_divisor": 26,
        "cave_height_divisor": 34,
        "use_beatgrid": True,
        "aura_emission": 3.8,
    },
    "ballad_broadstage": {
        "label": "Ballad Broadstage",
        "description": "6-beat wide phrases; slow unfolding landscape with gentle relief.",
        "chunk_beats": 6,
        "surface_height_divisor": 22,
        "cave_height_divisor": 36,
        "use_beatgrid": False,
        "aura_emission": 3.2,
    },
    "toccata_spires": {
        "label": "Toccata Spires",
        "description": "2-beat rapid-fire chunks; dense, sharp vertical architecture.",
        "chunk_beats": 2,
        "surface_height_divisor": 18,
        "cave_height_divisor": 28,
        "use_beatgrid": True,
        "aura_emission": 4.2,
    },
    "lullaby_undergrowth": {
        "label": "Lullaby Undergrowth",
        "description": "8-beat slow phrases; flat surface with dominant cave network.",
        "chunk_beats": 8,
        "surface_height_divisor": 36,
        "cave_height_divisor": 14,
        "use_beatgrid": True,
        "aura_emission": 2.6,
    },
    "fugue_labyrinth": {
        "label": "Fugue Labyrinth",
        "description": "4-beat contrapuntal density; interwoven surface and cave layers.",
        "chunk_beats": 4,
        "surface_height_divisor": 28,
        "cave_height_divisor": 18,
        "use_beatgrid": True,
        "aura_emission": 3.9,
    },
    "nocturne_ribbon": {
        "label": "Nocturne Ribbon",
        "description": "Single melodic line with long sustain; minimal branching.",
        "chunk_beats": 5,
        "surface_height_divisor": 30,
        "cave_height_divisor": 30,
        "use_beatgrid": False,
        "aura_emission": 3.4,
    },
    "tarantella_bounce": {
        "label": "Tarantella Bounce",
        "description": "Driving 6/8 propulsion; rapid relief changes and low caves.",
        "chunk_beats": 3,
        "surface_height_divisor": 17,
        "cave_height_divisor": 34,
        "use_beatgrid": True,
        "aura_emission": 4.1,
    },
    "canon_echo": {
        "label": "Canon Echo",
        "description": "Staggered overlapping phrases; broad naves with repeated ridge motifs.",
        "chunk_beats": 7,
        "surface_height_divisor": 24,
        "cave_height_divisor": 46,
        "use_beatgrid": True,
        "aura_emission": 3.6,
    },
    "gavotte_hedges": {
        "label": "Gavotte Hedges",
        "description": "Courtly clipped phrases; narrow ridges and tidy low relief.",
        "chunk_beats": 4,
        "surface_height_divisor": 20,
        "cave_height_divisor": 52,
        "use_beatgrid": False,
        "aura_emission": 2.9,
    },
    "rhapsody_fold": {
        "label": "Rhapsody Fold",
        "description": "Free dramatic arcs; sharp folded ridges and deep basins.",
        "chunk_beats": 6,
        "surface_height_divisor": 14,
        "cave_height_divisor": 22,
        "use_beatgrid": True,
        "aura_emission": 4.6,
    },
    "berceuse_overhang": {
        "label": "Berceuse Overhang",
        "description": "Rocking 6/8 lullaby; soft overhangs and sheltered hollows.",
        "chunk_beats": 6,
        "surface_height_divisor": 34,
        "cave_height_divisor": 16,
        "use_beatgrid": True,
        "aura_emission": 2.4,
    },
    "ritornello_rings": {
        "label": "Ritornello Rings",
        "description": "Recurring theme with circular emphasis; layered plateaus and rings.",
        "chunk_beats": 8,
        "surface_height_divisor": 26,
        "cave_height_divisor": 36,
        "use_beatgrid": True,
        "aura_emission": 3.3,
    },
}


def load_presets():
    """Presets from disk, falling back to the built-in defaults."""
    path = presets_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("presets"):
                return data["presets"]
        except Exception:
            pass
    return dict(DEFAULT_PRESETS)


def write_presets(presets=None):
    """Materialize presets to disk so they are editable outside Blender."""
    payload = {
        "schema": "melodia.midi_presets.v1",
        "presets": presets or DEFAULT_PRESETS,
    }
    path = presets_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def preset_items():
    """(id, label, description) tuples for a Blender EnumProperty."""
    out = []
    for key, val in sorted(load_presets().items()):
        out.append((key,
                    val.get("label", key),
                    val.get("description", "")))
    return out


# ---------------------------------------------------------------- discovery

def discover_midi(extra_dirs=None):
    """All .mid files in the project's known MIDI locations."""
    roots = [midi_content_dir(),
             os.path.join(repo_root(), "Imports", "Audio")]
    if extra_dirs:
        roots.extend(extra_dirs)

    found = []
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if not fn.lower().endswith((".mid", ".midi")):
                    continue
                full = os.path.join(dirpath, fn)
                key = os.path.normcase(full)
                if key in seen:
                    continue
                seen.add(key)
                found.append(full)
    return sorted(found)


def beatgrid_for(melody_path):
    """Matching _beatgrid file for a melody, if one exists."""
    stem, ext = os.path.splitext(melody_path)
    cand = stem + "_beatgrid" + ext
    return cand if os.path.exists(cand) else None


# ---------------------------------------------------------------- generate

def generate_world(midi_path, preset_id="resonant_default", out_obj=None):
    """Parse MIDI -> voxels -> OBJ. Returns a report dict.

    Pure Python; no bpy. Callable from the addon or headless tooling.
    """
    mv = load_voxel_module()
    presets = load_presets()
    preset = presets.get(preset_id, DEFAULT_PRESETS["resonant_default"])

    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return {"ok": False, "reason": "no note tracks parsed"}

    report = {
        "ok": True,
        "midi": midi_path,
        "preset": preset_id,
        "ticks_per_beat": tpb,
        "melody_notes": len(tracks[0]),
        "used_beatgrid": False,
    }

    all_tracks = [list(tracks[0])]

    if preset.get("use_beatgrid", True):
        bg = beatgrid_for(midi_path)
        if bg:
            b_tracks, b_tpb = mv.parse_midi(bg)
            if b_tracks and b_tpb:
                scale = float(tpb) / float(b_tpb)
                rescaled = [(int(n[0] * scale), n[1], n[2])
                            for n in b_tracks[0]]
                all_tracks.append(sorted(rescaled))
                report["used_beatgrid"] = True
                report["beatgrid"] = bg
                report["beat_notes"] = len(rescaled)

    chunks = mv.generate(all_tracks, tpb,
                         chunk_beats=int(preset.get("chunk_beats", 4)))
    report["voxels"] = len(chunks)

    stats = {}
    for block in chunks.values():
        name = mv.BLOCK_NAMES.get(block, "unknown")
        stats[name] = stats.get(name, 0) + 1
    report["blocks"] = stats

    if out_obj is None:
        out_obj = os.path.join(studio_root(), "current_terrain.obj")
    os.makedirs(os.path.dirname(out_obj), exist_ok=True)

    verts, faces = mv.export_obj(chunks, out_obj, name="ResonantWorld")
    report["obj"] = out_obj
    report["verts"] = verts
    report["faces"] = faces
    return report


def dress_terrain(terrain_obj, obj_path, style_id="verdant", seed=11, budget=1400, midi_path=None):
    """Plan dressing/magic for an already-generated terrain mesh.

    If midi_path is given, builds a real heightfield so planned props use
    grounded coordinates. Instancing is deliberately not claimed here; the
    current Blender operator reports the plan count only.

    Returns a short human-readable status string, or raises.
    """
    try:
        from . import terrain_dressing as td
    except ImportError:
        # Fallback for direct script execution
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "terrain_dressing",
            os.path.join(walkable_tool_dir(), "terrain_dressing.py"))
        td = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(td)

    # Try to build a real field when a MIDI is available — this is the QOL
    # fix for the {} bug that left every dressing at 0 props. Offline tests
    # call with midi_path=None and still expect a string, so empty is kept
    # as a valid fallback.
    field = {}
    field_ok = False
    if midi_path and os.path.exists(midi_path):
        try:
            from . import walkable_world as ww
            mv = ww.load_voxel_module()
            tracks, tpb = mv.parse_midi(midi_path)
            if tracks and tracks[0]:
                notes = list(tracks[0])
                # Include beatgrid if it exists — same as generate_world
                bg = beatgrid_for(midi_path)
                if bg:
                    try:
                        b_tracks, b_tpb = mv.parse_midi(bg)
                        if b_tracks and b_tpb:
                            scale = float(tpb) / float(b_tpb)
                            notes.extend((int(n[0] * scale), n[1] + 36, n[2]) for n in b_tracks[0])
                            notes.sort()
                    except Exception:
                        pass
                wpreset = ww.WALKABLE_PRESETS.get("walkable_valley", {})
                field, _gw = ww.build_heightfield(
                    notes,
                    cells_per_beat=wpreset.get("cells_per_beat", 2),
                    height_scale=wpreset.get("height_scale", 1.9),
                    plateau_radius=wpreset.get("plateau_radius", 2),
                    tpb=tpb,
                )
                field = ww.fill_gaps(field)
                field = ww.limit_slope(field, wpreset.get("max_slope", 1), wpreset.get("smooth_passes", 3))
                field_ok = True
        except Exception:
            field = {}

    plan, stats = td.plan_dressing(field, style_id=style_id, seed=seed, budget=budget)
    magic_plan, magic_stats = td.plan_magic(field, style_id=style_id)
    style = td.load_styles().get(style_id, {}).get("label", style_id)
    # Keep the contract string, but annotate when real field was used so UI can show it
    base = "%s | %d props | %d magic" % (style, len(plan), len(magic_plan))
    if field_ok and field:
        base += " | field %d cells" % len(field)
    return base
