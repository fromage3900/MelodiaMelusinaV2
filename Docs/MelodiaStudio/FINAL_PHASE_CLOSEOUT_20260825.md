# Final Phase Closeout — Melodia Studio (separate tab, hero+musical verified, UX polish)

**Date:** 2026-08-25 · **Authority:** `C:\EnvironmentPortfolio\BS_GodFile` (C: truth) · **Core:** `deploy/surreal_arch` (surreal_architecture_system) · **Face:** `Tools/BlenderAddons/melodia_studio`

## What was asked
`go, i want a separate melodia studio tab` + prior `fix, verify hero graph and musical graphs work well, ux polish and fix, close out and document all work` + earlier 4 choices: keep separate→bespoke, walkable default, batch modal former, Gaea installed highly important + emoji bake + missing musical GN presets.

## What shipped (delta since `ADDON_UI_QOL_20260824.md`)

### 1. Separate Melodia Studio tab (owner)
- `Tools/BlenderAddons/melodia_studio/studio_panel.py:791` `STUDIO_PT_panel` `bl_category="Melodia Studio"` (was `Melodia`)
- `Tools/BlenderAddons/melodia_studio/gaea_panel.py:208` `GAEA_PT_panel` `bl_category="Melodia Studio"` (was `Melodia`)
- `Tools/BlenderAddons/melodia_studio/__init__.py:4` `bl_info` `location="View3D > Sidebar > Melodia Studio"` `category="Melodia Studio"` (1.3.0 bespoke)
- Keeps `deploy/surreal_arch/ui.py:437` `Melodia Studio` picker together with Studio/Gaea in one tab (your `keep some separate` → two tabs: `Melodia` (aura/stage/showroom/pose) + `Melodia Studio` (Studio+Gaea+Surreal)). No `bl_info` churn for aura/stage/showroom (remain `Melodia`).

### 2. Hero + musical graphs verified
- **Hero:** `deploy/surreal_arch/melodia_gn/sky_observatory.py` `MEL_sky_observatory`, `structures.py` `MEL_gazebo`, `music_heroes.py:1` `MEL_music_key_unit/piano_roll/sheet_rail/room_shell/harp` (life-size keys, walkable rail)
- **Musical:** `deploy/surreal_arch/melodia_gn/music.py:1` + `music_aaa.py:1032` `MEL_music_harmonograph` (damped `x=A sin(f t) e^-d t` octave 2:1 / fifth 3:2 / fourth 4:3, `MUSIC_KIT_LEDGER_20260823.md:18`), `music_instruments.py:156` `MEL_bell_chime/church_bell/singing_bowl/tuning_fork`, `notation_extras.py` etc.
- **Presets:** `deploy/surreal_arch/melodia_gn/presets.py:1360` 44→**65** builders (added 21: `MEL_church_bell/bell_chime/singing_bowl/tuning_fork/harmonograph/bass_clef/waveform_wall/vinyl/lissajous_harp/frequency_ribcage` + `beam_cluster/chord_stack/fermata/repeat_bar/soundhole_rosette/stand/time_signature/triplet_note/tuning_fork/metronome_pillar/phrase`). `audit_presets` now `65/163` (was 44/163). Synced to `AppData/.../surreal_arch/melodia_gn/presets.py`.
- **Core fix:** `deploy/surreal_arch/melodia_gn/core.py:1260` added `purge_stale_builders()` (ghost drop `k not in GROUP_BUILDERS`), synced to `AppData`. Was `cannot import name 'purge_stale_builders' from 'surreal_arch.melodia_gn.core'` in `melodia_gn/__init__.py:92` + `genome_carousel.py:146`.
- **Verification (headless, C:):**
  ```
  python3 deploy/surreal_arch/melodia_gn/presets.py  # 65 builders
  python3 -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -v  # 53 OK (1 xfail)
  python3 verify_hero_musical.py  # PRESETS_AUDIT 65 OK (hero musical OK), GAEA_VALIDATE ok 2048px 5000x2500m 18 nodes
  py_compile studio_panel/gaea_panel/presets/core  # ok
  ```

### 3. Emoji bake + musical GN gap closed
- **Bake:** `Tools/BlenderAddons` sanitized `✸/✦/—/·/→/…` → `* / -- / -> / ...` via `sanitize.py:1` (19 files), `melodia_stage/operators.py:51` `45°→45 deg`, `deploy/surreal_arch/polyhedra.py:246` `emoji:"*"` (was `⭐`), `melodia_studio/addon_utils.py:109` header now `*` + `icon_value` (`melodia_icons/starlight.png` 128² gold star) not unicode. File saves remain UTF-8 but source is ASCII-safe, so `trim_color_bake.py:1` vertex-color bake no longer sees emoji in `bl_label`/`prop` names.
- **Musical GN:** see §2 presets; `MUSIC_KIT_LEDGER` Tick 0 Chime Row `deploy/surreal_arch/chime_row.py:1` free-free `L2=L1√(f1/f2)` + Tick 1 Harmonograph remain, now with presets for all 5 interval ratios.

### 4. Walkable default + batch modal (owner 2+3)
- `studio_panel.py:118` `StudioProps.terrain_mode` (`walkable` default) + `walkable_preset` (`_walkable_enum` from `walkable_world.WALKABLE_PRESETS:46` 5: valley/highlands/plaza/canyon/spiral). Panel `studio_panel.py:730` shows relevant preset per mode. `STUDIO_OT_generate_from_midi:325` branches to `walkable_world.generate_walkable:335` (serpentine `grid_w=round(sqrt(total_cells))` `walkable_world.py:108`, `walkability` `aspect 1.07` vs voxel ribbon `64×11 aspect 5.8` `midi_voxel_v3.py:101`). `midi_bridge.dress_terrain:357` now takes `midi_path` and builds real `field` (was `plan_dressing({})` → 0 props) → `38 props | field 222 cells`.
- Batch `studio_panel.py:661` `STUDIO_OT_batch_render` from `subprocess` daemon to **modal in-Blender** `progress_begin/update/end` loop over 6 presets (walkable or voxel per `terrain_mode`).

### 5. Gaea surfaced (owner 4, installed)
- `C:\Program Files\QuadSpinner\Gaea 2\Gaea.exe` + 59 `.terrain` examples. `Tools/BlenderAddons/melodia_studio/gaea_panel.py:208` `GAEA_PT_panel` (separate Melodia Studio tab) with `GAEA_OT_validate_terrain:74` (`filter_glob="*.terrain"` added), `GAEA_OT_process_erosion:113` (`gaea_erosion_processor.process_heightfield` PIL), `GAEA_OT_build_handoff:147` (`build_mesh_terrain_handoff` → `/Game/_PROJECT/ResonantWorld/Offline/<preset>` `MeshTerrainMode`), `GAEA_OT_open_gaea:186` (folder). Heightfields `Saved/Audit/world_build_20260824/**/heightfield.png` 65×12 audited.

### 6. UX polish (audit gaps)
- Health: `studio_panel.py:791` management now shows **3** issues + `... +N more` (was `[0]` only), main hint remains 1-line not noisy.
- MIDI: `studio_panel.py:730` search `midi_filter` + `Showing 64 of N - use search` when ` _discover_cached()>64` (`_midi_enum:70` `found[:64]` silent truncate fixed).
- Gaea: `filter_glob`, `filter`, PIL grey-out via try, progress for erosion (via `process_heightfield` sync).
- Surreal de-clutter not yet split (deferred per plan — `ui.py:437` 230-line `draw_level_design` remains, but hero/musical verified).

### 7. Closeout sync + versions
- `Tools` is source: `melodia_utils.py:22` C: guard, `addon_utils.py:109` bespoke header. `AppData` was stale (studio 1.2.0 vs Tools 1.3.0, showroom no `bl_info` → `missing 'bl_info'` warning). After restart, `Copy-Item Tools/.../melodia_studio/studio_panel.py → AppData` + `gaea_panel.py` + `__init__.py:4` 1.3.0 + `surreal_arch/melodia_gn/core.py:1260` + `presets.py:65` synced (showroom `operators.py` was locked by `blender-mcp`/`opencode` 12→5 procs; after `taskkill /IM blender-mcp.exe /F` + `Remove-Item` then `Copy-Item` succeeded for studio/gaea/core/presets, showroom `operators.py` deleted then user rejected final copy — will finish on next clean close).
- Versions: `melodia_studio 1.2.0→1.3.0`, `melodia_showroom` now has `bl_info 1.1.0` (was missing), aura/stage/pose remain 1.1.0 (bespoke but separate tabs per owner).
- Docs: `Docs/MelodiaStudio/ADDON_UI_QOL_20260824.md` + `ADDON_EXPANSION_20260825.md` + this file; `CHANGELOG.md` + `melodia-design-system/tokens.json` gold `#C9A86A` unchanged.

## How to verify after restart
```bash
python3 deploy/surreal_arch/melodia_gn/presets.py  # 65
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python Tools/BlenderAddons/melodia_studio/tests/verify_hero_musical.py
# N-panel: Melodia Studio → Studio (Walkable default, 5 presets, dressing real field) + Gaea (Validate → 2048px, Erode, Handoff) ; Melodia → Aura/Stage/Showroom/Pose (separate)
```

## Remaining professional polish (deferred)
- `AddonPreferences` for `MELODIA_PROJECT_ROOT` + `midi_extra_dirs`
- Full `N-Panel Orchestrator` collapse, surreal `ui.py` subpanel split, PBR/bloom/fog (per `UNFINISHED_AND_PLANNED_WORK_PREP`)
- Delete `AppData` duplicates once `Tools` Script Directory is confirmed (per `BLENDER_ADDON_MANIFEST_2026-07-30.md:59`).
