"""Path resolution and generator access. No bpy, so it is unit-testable."""

import os
import sys


def addon_dir():
    """Real on-disk directory of this addon.

    The addon is junction-linked into Blender's AppData, so a plain
    dirname(__file__) yields the AppData path and repo_root() then walks up
    into '...Blender/5.2', not BS_GodFile. realpath resolves the junction back
    to the repo, which is the source of truth.
    """
    return os.path.dirname(os.path.realpath(os.path.abspath(__file__)))


def repo_root():
    """Tools/BlenderAddons/resonant_world_studio -> up 3 = BS_GodFile."""
    root = os.path.normpath(os.path.join(addon_dir(), "..", "..", ".."))
    if os.path.basename(root).lower() != "bs_godfile":
        # Junction not resolvable on this filesystem: fall back to the known
        # project path rather than silently pointing at Blender's config dir.
        fallback = r"C:\EnvironmentPortfolio\BS_GodFile"
        if os.path.isdir(fallback):
            return fallback
    return root


def melodia_studio_dir():
    """Where walkable_world / terrain_dressing live."""
    return os.path.join(repo_root(), "Tools", "BlenderAddons",
                        "melodia_studio")


def midi_dir():
    return os.path.join(repo_root(), "Content", "MelodiaIntegration", "MIDI")


def _ensure_path():
    d = melodia_studio_dir()
    if d not in sys.path:
        sys.path.insert(0, d)
    return d


def load_modules():
    """Import the proven walkable-mapping and dressing modules."""
    _ensure_path()
    import walkable_world
    import terrain_dressing
    return walkable_world, terrain_dressing


def discover_midi():
    roots = [midi_dir(), os.path.join(repo_root(), "Imports", "Audio")]
    found, seen = [], set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, _d, files in os.walk(root):
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


def build_field(midi_path, preset_id):
    """Heightfield + metrics for a MIDI/preset pair.

    Returns (field, preset, metrics). The field is needed for local height
    sampling; using global bounds instead is what made props and characters
    float in earlier versions.
    """
    ww, td = load_modules()
    mv = ww.load_voxel_module()

    preset = ww.WALKABLE_PRESETS.get(preset_id)
    if preset is None:
        preset_id = "walkable_valley"
        preset = ww.WALKABLE_PRESETS[preset_id]

    tracks, tpb = mv.parse_midi(midi_path)
    if not tracks:
        return None, preset, None

    notes = list(tracks[0])
    stem, ext = os.path.splitext(midi_path)
    bg = stem + "_beatgrid" + ext
    if os.path.exists(bg):
        b_tracks, b_tpb = mv.parse_midi(bg)
        if b_tracks and b_tpb:
            scale = float(tpb) / float(b_tpb)
            notes.extend((int(n[0] * scale), n[1] + 36, n[2])
                         for n in b_tracks[0])
            notes.sort()

    field, _gw = ww.build_heightfield(
        notes,
        cells_per_beat=preset["cells_per_beat"],
        height_scale=preset["height_scale"],
        plateau_radius=preset["plateau_radius"],
        tpb=tpb,
        fold=preset.get("fold", "serpentine"),
    )
    field = ww.limit_slope(ww.fill_gaps(field), preset["max_slope"],
                           preset["smooth_passes"])

    metrics = ww.walkability(field, preset["max_slope"])
    metrics["largest_region"] = ww.largest_connected_region(
        field, preset["max_slope"])
    metrics["largest_region_fraction"] = round(
        metrics["largest_region"] / float(max(1, metrics["cells"])), 3)
    return field, preset, metrics


def export_obj(field, out_path):
    """Voxelize the heightfield and write the coloured OBJ."""
    ww, _td = load_modules()
    mv = ww.load_voxel_module()
    voxels = ww.field_to_voxels(field, mv)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    verts, faces = mv.export_obj(voxels, out_path, name="ResonantWorld")
    return len(voxels), verts, faces
