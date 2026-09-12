# Melodia Showroom Integration Doc — 2026-08-24

## What it is
`Tools/BlenderAddons/melodia_showroom` is the single Blender addon that ties together:
- terrain generation from project MIDI
- musical expansion dressing styles
- one-click showroom framing and render

This document explains how it integrates with the rest of the Melodia toolchain, what it expects on disk, and how to verify it.

## Integration map

- `melodia_showroom/operators.py` → `melodia_showroom/showroom_bridge.py`
  - preset combo mapping: showroom preset → terrain preset + dressing style
- `showroom_bridge.py` → `melodia_studio/midi_bridge.py`
  - terrain generation: `generate_world(midi, preset_id, out_obj)`
- `showroom_bridge.py` → `melodia_studio/terrain_dressing.py`
  - dressing application: `dress_terrain(terrain_obj, obj_path, style_id)`
- showroom pipeline outputs:
  - OBJ: `GeneratedScenes/showroom/terrain.obj`
  - PNG: `GeneratedScenes/showroom/<preset_id>.png`

## Drive-aware path resolution

This repo has active copies on both `C:\EnvironmentPortfolio\BS_GodFile` and `G:\EnvironmentPortfolio\BS_GodFile`.
`showroom_bridge.repo_root()` now searches both drive prefixes via `realpath`, so:
- addon can be loaded from either drive
- Blender junction/copy doesn’t matter
- MIDI and generated scene paths resolve correctly regardless of mount

## Verified evidence

- Blender headless render:
  - `C:\EnvironmentPortfolio\BS_GodFile\Tools\MelodiaProceduralStudio\GeneratedScenes\showroom\waltz_garden_waltz.png`
  - `C:\EnvironmentPortfolio\BS_GodFile\Tools\MelodiaProceduralStudio\GeneratedScenes\showroom\terrain.obj`
- Smoke log:
  - `Tools/BlenderAddons/melodia_showroom/_smoke.log`
  - confirmed `waltz_garden_waltz | terrain=357v/2856f | dress=Waltz Garden | render=...`

## Addon manifest status

`Tools/BlenderAddons/BLENDER_ADDON_MANIFEST_2026-07-30.md` has been updated:
- added `melodia_pose_audit`, `melodia_showroom`, `melodia_stage`, `melodia_studio`
- current custom addon count: 13

## Repo-wide integration summary

This commit set also documents and integrates the broader work done in this session:

- `melodia_pose_audit` — headless-safe pose audit addon
  - writes audit results to `bpy.data.texts`
  - verified via Blender 5.2 headless smoke test
- `melodia_studio` — musical expansion presets + dressing styles
  - added: `Waltz Garden`, `Ballad Plaza`, `Toccata Surface`, `Lullaby Cave`, `Fugue Maze`, `Nocturne Reflection`
  - panel now exposes a `Dressing` selector for terrain expansion
- `melodia_showroom` — integrated pipeline
  - single UI preset: terrain + dressing + render in one operator
  - self-contained bridge so it doesn’t depend on fragile AppData junction state
  - drive-aware repo root resolution

## Verification checklist

- [x] `melodia_showroom` tests pass
- [x] `melodia_studio` tests pass
- [x] headless Blender render produced
- [x] manifest updated
- [x] integration doc written
- [ ] user confirms manifest handoff step:
  - Blender → Edit → Preferences → File Paths → Script Directories → Add `Tools/BlenderAddons/`

## Notes

- generated output lives under `GeneratedScenes/showroom/` at the repo root
- rendered PNGs are not committed; only the addon source and docs are
- if moving this work between drives, no path edits are needed — `repo_root()` auto-discovers
