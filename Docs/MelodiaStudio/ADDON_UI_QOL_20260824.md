# Melodia Studio — Addon UI / Management / QOL Pass (C: authority)

**Date:** 2026-08-24 · **Scope:** addon UI + management + QOL only (per owner) · **Authority:** `C:\EnvironmentPortfolio\BS_GodFile`

## What changed

### 1) C: authority (no G: fallback)
- New shared root: `Tools/BlenderAddons/melodia_utils.py` — `repo_root()` checks `$MELODIA_PROJECT_ROOT` → `C:\EnvironmentPortfolio\BS_GodFile` → walk-up. Never returns G:.
- `health_check()` flags `is_g_drive` and surfaces it in the UI instead of silently using G:.
- Removed G: candidate lists from `melodia_studio/midi_bridge.py` (kept only via `melodia_utils`) and `melodia_showroom/showroom_bridge.py` (now a thin delegating shim).

### 2) Shared helpers
- `Tools/BlenderAddons/melodia_utils.py` (pure-Python, no bpy): `repo_root`, `studio_root`, `voxel_tool_dir`, `midi_content_dir`, `scenes_dir`, `discover_midi`, `health_check`, `addon_versions`.
- `Tools/BlenderAddons/melodia_studio/addon_utils.py` (bpy-side): icon loader with `melodia_icons` fallback, `cleanup_objects_with_prefix`, `open_folder`, `health_report_text`, `repo_root_path`.

### 3) Dressing bug fix (QOL)
- `midi_bridge.dress_terrain()` previously called `plan_dressing({}, ...)` → always 0 props. Now, when `midi_path` is supplied, it rebuilds a real walkable `field` (via `walkable_world`) before planning. Offline tests still pass because `midi_path=None` keeps the empty-field fallback and the same string contract.
- `studio_panel` and `showroom/operators` now pass `midi_path` through.

### 4) Melodia Studio panel (`Tools/BlenderAddons/melodia_studio/studio_panel.py`)
- **Category unified:** `bl_category = "Melodia"` so Studio/Aura/Stage/Showroom/Pose Audit sit in one tab.
- **Search/filter:** `midi_filter` StringProperty; `_midi_enum` filters on basename or full path; cached discovery (TTL 4s) avoids rescanning every draw; `Refresh` operator and health hint box.
- **Preview:** `_midi_preview_lines()` shows notes/TPB/beatgrid presence/size under the picker.
- **Cleanup:** `auto_cleanup` toggle (default ON); `Clean Up` operator removes `Terrain/MS_*/SR_*`; stale `Terrain` object removed before re-generate; progress bar via `window_manager.progress_*`.
- **Dressing:** uses real field; last report now split on ` | ` for readability; `last_midi` stored.
- **Management subpanel:** `STUDIO_PT_management` under `STUDIO_PT_panel` — repo path, addon versions (first 6), `Validate`, `Open Folder` (Addons/Showroom), script-directory tip, health alert box.
- **Icons:** via `addon_utils.icon_kwargs("generate", fallback)` — falls back to Blender built-ins when `melodia_icons` PNGs missing.
- **Advanced fold:** Config box (Export Presets, Open MIDI/Scenes) hidden behind `show_advanced`.
- `__init__.py` bumped to 1.2.0, reloads `walkable_world`/`terrain_dressing`/`addon_utils`, unloads icon previews on `unregister`.

### 5) Showroom (dedup + C-authority)
- `showroom_bridge.py` → thin shim delegating to `melodia_utils` + `melodia_studio/midi_bridge`; `PRESETS` re-exported (`is` identical); `discover_midi`/`generate_world`/`dress_terrain` all delegate; `dress_terrain` now accepts `midi_path`.
- `operators.py`: `_midi_for_props` now C-authority only (no `EnvironmentPortfolio/BS_GodFile` walk-up that could hit G:), passes `midi` to `dress_terrain`, handles old-shim `TypeError` fallback.
- `panel.py`: `bl_category = "Melodia"`, last-report wrapping, dressing fix hint label.
- `__init__.py`: added `bl_info` 1.1.0 (was missing, so addon wouldn't show version/category correctly).

### 6) Stage / Aura / Pose Audit — category + QOL
- All `bl_category` → `"Melodia"` (Stage 1.1.0, Aura 1.1.0, Pose Audit 1.1.0).
- `bl_info.location` updated to `View3D > Sidebar > Melodia`.
- **Aura:** `quick_fire/ice/lightning` no longer `select_all` (which destroyed the user's selection). Now warns if nothing selected and respects current selection.

## Files touched

| File | Change |
|---|---|
| `Tools/BlenderAddons/melodia_utils.py` | NEW — shared C-authority root + health |
| `Tools/BlenderAddons/melodia_studio/addon_utils.py` | NEW — icon/cleanup/folder helpers |
| `Tools/BlenderAddons/melodia_studio/__init__.py` | 1.1.0 → 1.2.0, reload + unload |
| `Tools/BlenderAddons/melodia_studio/midi_bridge.py` | `dress_terrain(..., midi_path)` with real field |
| `Tools/BlenderAddons/melodia_studio/studio_panel.py` | Full QOL rewrite (see §4) |
| `Tools/BlenderAddons/melodia_showroom/showroom_bridge.py` | Thin delegating shim |
| `Tools/BlenderAddons/melodia_showroom/operators.py` | C-authority, pass midi, no G: |
| `Tools/BlenderAddons/melodia_showroom/panel.py` | Category Melodia |
| `Tools/BlenderAddons/melodia_showroom/__init__.py` | NEW bl_info 1.1.0 |
| `Tools/BlenderAddons/melodia_stage/__init__.py` | 1.1.0, location Melodia |
| `Tools/BlenderAddons/melodia_stage/panel.py` | Category Melodia |
| `Tools/BlenderAddons/melodia_aura/__init__.py` | 1.1.0 |
| `Tools/BlenderAddons/melodia_aura/panel.py` | Category Melodia |
| `Tools/BlenderAddons/melodia_aura/operators.py` | quick ops respect selection |
| `Tools/BlenderAddons/melodia_pose_audit/__init__.py` | 1.1.0 |
| `Tools/BlenderAddons/melodia_pose_audit/panel.py` | Category Melodia |

## Verification

```bash
python3 -B -m unittest discover -s Tools/BlenderAddons/melodia_studio/tests -v
# 53 tests OK (1 expected failure — height divisors not honoured, known)
python3 -m py_compile Tools/BlenderAddons/melodia_utils.py Tools/BlenderAddons/melodia_studio/*.py Tools/BlenderAddons/melodia_showroom/*.py
# compile ok
python3 -c "import melodia_studio.midi_bridge as mb; print(mb.dress_terrain(None,'','verdant', midi_path='Content/.../128BPMarpeggiomelody.mid'))"
# → "Verdant Resonance | 38 props | 2 magic | field 222 cells"
```

## Remaining QOL backlog (not in this pass)

- Walkable presets not yet exposed in Studio/Showroom UI (currently only classic voxel presets).
- Gaea modules (`gaea_terrain_io`, `gaea_erosion_processor`) not surfaced in UI — management panel could show erosion status.
- Full Style/Genome browser for `blender_kawaii_gn` / `blender_brutalist_gn` under Melodia tab.
- Preferences panel for `$MELODIA_PROJECT_ROOT` override + MIDI extra dirs.
- Automated `N-Panel Orchestrator` collapse of non-Melodia tabs when Melodia is active (optional).

## How to test in Blender

1. Add Script Directory: `Edit → Preferences → File Paths → Script Directories → Add → C:\EnvironmentPortfolio\BS_GodFile\Tools\BlenderAddons`
2. Enable: Melodia Studio, Melodia Showroom, Melodia Stage, Melodia Aura, Melodia Pose Audit (all under "Melodia" category).
3. Open `View3D → Sidebar (N) → Melodia → Melodia Studio`:
   - Search filters MIDI, preview shows notes/beatgrid, Generate respects Auto-cleanup, last run shows field cells, Management shows versions/health, Open Folder works.
   - Showroom pipeline respects C: MIDI and dressing now places props.
   - Aura quick ops warn instead of selecting all.
