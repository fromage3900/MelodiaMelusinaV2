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
    """BS_GodFile root, from Tools/BlenderAddons/melodia_studio/ -> up 3.

    Honors AddonPreferences project_root (if set in Blender) and $MELODIA_PROJECT_ROOT env.
    """
    # 1) Blender AddonPreferences override
    try:
        import bpy  # type: ignore
        prefs = bpy.context.preferences.addons.get("melodia_studio")  # type: ignore
        if prefs and hasattr(prefs, "preferences"):
            pr = getattr(prefs.preferences, "project_root", "") or ""
            if pr.strip() and os.path.isdir(pr.strip()):
                return os.path.normpath(pr.strip())
    except Exception:
        pass
    # 2) Env override
    env = os.environ.get("MELODIA_PROJECT_ROOT", "").strip()
    if env and os.path.isdir(env):
        return os.path.normpath(env)
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
#
# D7 FIXED 2026-08-26: midi_voxel_v3.generate now honours
# surface_height_divisor / cave_height_divisor (vel//div). Threaded via
# midi_bridge.generate_world surface_div/cave_div kwargs. Presets that differ
# only in divisor now yield distinct voxel heights.
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

# Ancient Cultures instrument presets (see ancient_cultures.py) merged in at
# import so the UI dropdown and batch tooling pick them up automatically.
try:
    from .ancient_cultures import ANCIENT_PRESETS as _ANCIENT_PRESETS  # type: ignore
    for _k, _v in _ANCIENT_PRESETS.items():
        DEFAULT_PRESETS.setdefault(_k, dict(_v))
except Exception:
    try:
        import os as _os, importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "ancient_cultures",
            _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                          "ancient_cultures.py"))
        if _spec is not None and _spec.loader is not None:
            _ac = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_ac)
            for _k, _v in getattr(_ac, "ANCIENT_PRESETS", {}).items():
                DEFAULT_PRESETS.setdefault(_k, dict(_v))
    except Exception:
        pass


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

    # D7 fix: per-preset divisors now honoured (vel//surface_div vs cave_div)
    chunks = mv.generate(all_tracks, tpb,
                         chunk_beats=int(preset.get("chunk_beats", 4)),
                         surface_div=int(preset.get("surface_height_divisor", 32)),
                         cave_div=int(preset.get("cave_height_divisor", 40)))
    report["voxels"] = len(chunks)
    report["surface_div"] = int(preset.get("surface_height_divisor", 32))
    report["cave_div"] = int(preset.get("cave_height_divisor", 40))

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
    grounded coordinates. Uses shared core.field.build_field() pipeline.

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

    # Build a real field when MIDI is available, so dressing uses grounded coords
    field = {}
    field_ok = False
    if midi_path and os.path.exists(midi_path):
        try:
            from .core.field import build_field
            result = build_field(midi_path, "walkable_valley", source="walkable")
            if result["ok"]:
                field = result["field"]
                field_ok = True
        except Exception:
            field = {}

    plan, stats = td.plan_dressing(field, style_id=style_id, seed=seed, budget=budget)
    magic_plan, magic_stats = td.plan_magic(field, style_id=style_id)
    style = td.load_styles().get(style_id, {}).get("label", style_id)
    base = "%s | %d props | %d magic" % (style, len(plan), len(magic_plan))
    if field_ok and field:
        base += " | field %d cells" % len(field)
    return base
