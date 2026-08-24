# Minimal embedded preset bridge for Melodia Showroom.
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

import os
import sys


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    here = os.path.realpath(here)
    candidates = [
        here,
        os.path.normpath(os.path.join(here, "..")),
        os.path.normpath(os.path.join(here, "..", "..")),
        os.path.normpath(os.path.join(here, "..", "..", "..")),
        os.path.normpath(os.path.join(here, "..", "..", "..", "..")),
        os.path.normpath(os.path.join(here, "..", "..", "..", "..", "..")),
        r"C:\EnvironmentPortfolio\BS_GodFile",
        "/c/EnvironmentPortfolio/BS_GodFile",
        r"G:\EnvironmentPortfolio\BS_GodFile",
        "/g/EnvironmentPortfolio/BS_GodFile",
    ]
    for root in candidates:
        if os.path.isdir(os.path.join(root, "Content", "MelodiaIntegration", "MIDI")):
            return root
    return os.path.normpath(os.path.join(here, "..", "..", ".."))


def content_dir():
    return os.path.join(repo_root(), "Content", "MelodiaIntegration", "MIDI")


def voxel_tool_dir():
    return os.path.join(repo_root(), "Tools", "midi_to_voxel")


def load_voxel_module():
    vdir = voxel_tool_dir()
    if vdir not in sys.path:
        sys.path.insert(0, vdir)
    import midi_voxel_v3
    return midi_voxel_v3


PRESETS = {
    "resonant_default": {
        "label": "Resonant Default",
        "chunk_beats": 4,
        "surface_height_divisor": 32,
        "cave_height_divisor": 40,
        "use_beatgrid": True,
    },
    "cathedral_wide": {
        "label": "Cathedral Wide",
        "chunk_beats": 8,
        "surface_height_divisor": 20,
        "cave_height_divisor": 50,
        "use_beatgrid": True,
    },
    "dense_spire": {
        "label": "Dense Spire",
        "chunk_beats": 2,
        "surface_height_divisor": 16,
        "cave_height_divisor": 32,
        "use_beatgrid": True,
    },
    "surface_only": {
        "label": "Surface Only",
        "chunk_beats": 4,
        "surface_height_divisor": 32,
        "cave_height_divisor": 40,
        "use_beatgrid": False,
    },
    "abyss_caves": {
        "label": "Abyss Caves",
        "chunk_beats": 4,
        "surface_height_divisor": 48,
        "cave_height_divisor": 20,
        "use_beatgrid": True,
    },
    "waltz_corridors": {
        "label": "Waltz Corridors",
        "chunk_beats": 3,
        "surface_height_divisor": 26,
        "cave_height_divisor": 34,
        "use_beatgrid": True,
    },
    "ballad_broadstage": {
        "label": "Ballad Broadstage",
        "chunk_beats": 6,
        "surface_height_divisor": 22,
        "cave_height_divisor": 36,
        "use_beatgrid": False,
    },
    "toccata_spires": {
        "label": "Toccata Spires",
        "chunk_beats": 2,
        "surface_height_divisor": 18,
        "cave_height_divisor": 28,
        "use_beatgrid": True,
    },
    "lullaby_undergrowth": {
        "label": "Lullaby Undergrowth",
        "chunk_beats": 8,
        "surface_height_divisor": 36,
        "cave_height_divisor": 14,
        "use_beatgrid": True,
    },
    "fugue_labyrinth": {
        "label": "Fugue Labyrinth",
        "chunk_beats": 4,
        "surface_height_divisor": 28,
        "cave_height_divisor": 18,
        "use_beatgrid": True,
    },
    "nocturne_ribbon": {
        "label": "Nocturne Ribbon",
        "chunk_beats": 5,
        "surface_height_divisor": 30,
        "cave_height_divisor": 30,
        "use_beatgrid": False,
    },
}


def preset_items():
    return [(k, v.get("label", k), k) for k, v in sorted(PRESETS.items())]


def beatgrid_for(path):
    stem, ext = os.path.splitext(path)
    cand = stem + "_beatgrid" + ext
    return cand if os.path.exists(cand) else None


def discover_midi():
    roots = [content_dir(), os.path.join(repo_root(), "Imports", "Audio")]
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


def generate_world(midi_path, preset_id="resonant_default", out_obj=None):
    mv = load_voxel_module()
    preset = PRESETS.get(preset_id, PRESETS["resonant_default"])
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
        out_obj = os.path.join(repo_root(), "Tools", "MelodiaProceduralStudio", "current_terrain.obj")
    os.makedirs(os.path.dirname(out_obj), exist_ok=True)

    verts, faces = mv.export_obj(chunks, out_obj, name="ResonantWorld")
    report["obj"] = out_obj
    report["verts"] = verts
    report["faces"] = faces
    return report


def dress_terrain(terrain_obj, obj_path, style_id="verdant", seed=11, budget=1400):
    root = repo_root()
    td_path = os.path.join(root, "Tools", "BlenderAddons", "melodia_studio", "terrain_dressing.py")
    if not os.path.exists(td_path):
        known_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "EnvironmentPortfolio", "BS_GodFile"))
        td_path = os.path.join(known_root, "Tools", "BlenderAddons", "melodia_studio", "terrain_dressing.py")
    td_path = os.path.realpath(td_path)
    if not os.path.exists(td_path):
        raise RuntimeError("terrain_dressing not found: %s" % td_path)
    import importlib.util
    spec = importlib.util.spec_from_file_location("showroom_terrain_dressing", td_path)
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)

    plan, stats = td.plan_dressing({}, style_id=style_id, seed=seed, budget=budget)
    magic_plan, magic_stats = td.plan_magic({}, style_id=style_id)
    style = td.load_styles().get(style_id, {}).get("label", style_id)
    return "%s | %d props | %d magic" % (style, len(plan), len(magic_plan))
