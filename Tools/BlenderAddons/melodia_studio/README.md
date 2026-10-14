# Melodia Studio — Blender addon

MIDI-driven Resonant World generation. Blender 4.0+ (live on 5.2).
Loads via an extra Script Directory (see `../BLENDER_ADDON_MANIFEST_2026-07-30.md`).
Panel: **View3D > Sidebar > Melodia Studio**. `Gaea` work lives in its own
`Melodia Gaea` panel, surfaced 2026-08-24.

## Two kinds of files live here

1. **The addon** — a registered module chain, loaded automatically by
   `__init__.py`. Everything the N-panel does is in this set.
2. **Standalone scripts** — NOT imported by the addon. They are exec'd
   manually from the Blender text editor (live session) or run headless via
   `blender --background ... --python ...`. They use bare sibling imports
   (`import walkable_world`), which rely on the addon root being on
   `sys.path` — keep them at the root, or add an import shim if you move one.

## The addon (registered)

| File | Role |
|---|---|
| `__init__.py` | Entry point. Registers `melodia_chrome`, `studio_panel`, `gaea_panel`, `tandem_bridge`; loads the rest as optional modules and logs (never silently drops) failures. Also reloads the studio split submodules on addon refresh. |
| `studio_panel.py` | Registration facade only (split 2026-10-04): assembles `classes` and does `register()`/`unregister()` in the original order; re-exports `_selected_midi` for `tandem_bridge`. All `bl_idname`s unchanged. |
| `properties.py` | `MelodiaStudioPreferences` (bl_idname `melodia_studio`) + `StudioProps` PropertyGroup + all enum item helpers. |
| `operators.py` | The 11 operators: `melodia_studio.generate_from_midi`, `frame_terrain`, `write_presets`, `save_scene`, `cleanup_scene`, `setup_script_directory`, `render_proof`, `batch_render`, `open_folder`, `refresh_midi`, `validate_health`. |
| `panel.py` | `STUDIO_PT_panel` + `STUDIO_PT_management` N-panels ("Melodia Studio" category). |
| `terrain_build.py` | `build_terrain_mesh`, `build_aura_material`, dressing collection/template/instancing helpers. |
| `midi_picker.py` | MIDI discovery cache (4 s TTL), `_selected_midi` picker, `_midi_preview_lines`. |
| `midi_bridge.py` | MIDI → voxel worldgen; bridges to the proven `Tools/midi_to_voxel/midi_voxel_v3.py` generator. |
| `ancient_cultures.py` | Twelve instrument-tradition-derived presets; imported by `midi_bridge`, `tandem_bridge`, `terrain_dressing`. |
| `tandem_bridge.py` | Terrain ↔ Surreal Architecture city bridge. The ONLY place that touches both systems; no edits to the GN baby (`deploy/surreal_architecture_gen.py`). |
| `gaea_panel.py` | Gaea inspector + erosion processor + UE handoff. Lazily imports `gaea_terrain_io` / `gaea_erosion_processor` at draw time. |
| `walkable_world.py` | v4 walkable terrain mapping (time→X, pitch-class→Y without the ribbon defect). |
| `terrain_dressing.py` | v5 dressing + magical systems; derived from the musical heightfield. |
| `melodia_chrome.py` | Panel chrome (gold-ivory tokens, offline-safe). |
| `addon_utils.py` | Blender-side helpers (icons etc.); `unload_icons()` on unregister. |
| `core/field.py` | Shared MIDI → heightfield builder; deduplicates the pipeline previously copy-pasted across 6 modules. |
| `tests/` | Offline unit tests (no bpy, no Blender, no UE). |

Run the tests from the repo root:

```
python -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -v
```

## Standalone scripts — worldgen

Exec from the Blender text editor with a Resonant World scene open:

| File | What it does |
|---|---|
| `atmosphere.py` | Volumetric fog (velocity-driven), dynamic sky (tempo-driven), three-point mood lighting. |
| `musical_structure.py` | Song section detection (intro/verse/chorus/bridge/outro) → biome mapping; BPM + dynamics per section. |
| `roll_field.py` | MIDI → walkable note-field JSON (`melodia_roll_field_v1`); SSOT so Blender GN and UE PCG instance the same piano-roll. |
| `smooth_terrain.py` | Voxel cubes → smooth biome-colored mesh (bilinear subdivision, smooth shading). |
| `world_streaming.py` | Chunked world scaling (16×16 chunks, LOD, view-distance culling). |

## Standalone scripts — Choral Sheep

| File | What it does |
|---|---|
| `export_choral_sheep.py` | Headless UE export. `blender --background choral_sheep.blend --python Tools/BlenderAddons/melodia_studio/export_choral_sheep.py -- --out .../SK_ChoralSheep.fbx` (targets `/Game/Melodia/Companions/ChoralSheep/`). |
| `sheep_bake_prep.py` | High→low texture bake prep; marks targets, writes `choral_sheep_bake_manifest.json`. |
| `sheep_shapekeys.py` | Shape-key authoring panel — **manual exec only; NOT registered by the addon.** Exec it, then N > Melodia > Choral Sheep Shape Keys appears. |
| `sheep_shine.py` | Woolly Principled shader + named color variations. Materials only — never touches geometry/rig. |

## Standalone scripts — batch (`batch/`)

Overnight UE-handoff runners; not imported by the addon (see `batch/__init__.py`):

| File | What it does |
|---|---|
| `batch/expand_worldgen.py` | Heightfield PNG from generated OBJ + dressing plan JSON + evidence JSON (SHA, voxel stats, paths). |
| `batch/assemble_ue_manifest.py` | Assembles the UE import manifest for the world-build preset set. |
| `batch/batch_remaining_presets.py` | Overnight preset batch through the Python erosion fallback. **This is the source of truth** — a byte-identical root-level copy (`_batch_remaining_presets.py`) was deleted 2026-10-04. |

## Notes

- The repo copy under `Tools/BlenderAddons/` is the source of truth; the copy
  in Blender's `scripts/addons/` is a mirror pending the one-time
  Script-Directory step (see the manifest).
- Destructive-adjacent caution: bulk `Content/` in this repo is untracked —
  never run `git clean` here.
