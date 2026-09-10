# Melodia Studio — Deep Intake Report

**Date:** 2026-09-02
**Status:** Comprehensive audit of Blender 5.2 Geometry Nodes infrastructure

---

## 1. Architecture Overview

Melodia Studio is a **Blender 5.2 LTS addon** for procedural world/character/architecture generation using Geometry Nodes. It consists of three layers:

| Layer | Location | Purpose |
|-------|----------|---------|
| **Melodia Studio** | `Tools/BlenderAddons/melodia_studio/` | Main addon (30 Python files) |
| **Surreal Arch** | `deploy/surreal_arch/` | 120-file GN framework + 173 builders |
| **GN Addons** | `Tools/BlenderAddons/blender_kawaii_gn/`, `blender_brutalist_gn/` | Specialized sub-frameworks |

---

## 2. Melodia Studio Addon (v1.5.0)

**Module:** `surreal_architecture_gen`  
**Operators:** `surreal_arch.*`  
**N-panel tab:** Melodia Studio  
**Blender:** 5.2 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`)

### Core Modules
| Module | Purpose |
|--------|---------|
| `core/field.py` | Shared MIDI→heightfield pipeline (single source of truth) |
| `midi_bridge.py` | MIDI file parsing → world generation |
| `studio_panel.py` | Main N-panel UI |
| `walkable_world.py` | Walkable terrain generation |
| `terrain_dressing.py` | Set dressing placement |
| `tandem_bridge.py` | Tandem City field-wins snap |
| `gaea_panel.py` | Gaea terrain integration |
| `melodia_chrome.py` | Chrome/material presets |
| `world_streaming.py` | World streaming |
| `roll_field.py` | Roll field generation |
| `smooth_terrain.py` | Terrain smoothing |
| `ancient_cultures.py` | Ancient culture presets |
| `atmosphere.py` | Atmosphere presets |
| `musical_structure.py` | Musical structure generation |
| `export_choral_sheep.py` | Choral Sheep export |
| `gaea_erosion_processor.py` | Gaea erosion processing |
| `gaea_terrain_io.py` | Gaea terrain I/O |
| `sheep_bake_prep.py` | Sheep bake preparation |
| `sheep_shapekeys.py` | Sheep shape keys |
| `sheep_shine.py` | Sheep shine/material |

### Batch System
| Script | Purpose |
|--------|---------|
| `batch/assemble_ue_manifest.py` | Assemble UE manifest from batch output |
| `batch/batch_remaining_presets.py` | Batch remaining presets |
| `batch/expand_worldgen.py` | Expand world generation |

---

## 3. Surreal Arch GN Framework (173 Builders)

**Location:** `deploy/surreal_arch/`  
**Main monolith:** `deploy/surreal_architecture_gen.py`  
**Categories:** 12 sections, 173 builders (27 hidden factory aliases)

### Builder Counts
| Category | Count |
|----------|-------|
| Set Dressing | 39 |
| Structures | 12 |
| Musical Notation | 7+ |
| Castle Kit | Many |
| Ornament | Many |
| Magic Effects | Many |
| Others | Various |

### Key Builders
| Builder | Purpose |
|---------|---------|
| `MEL_audio_spectrum_terrain` | Frequency-displaced terrain |
| `MEL_audio_spectrum_towers` | Frequency-bin mesh cities |
| `MEL_audio_radial_field` | Concentric arena terrain |
| `MEL_music_key_unit` | Life-size key generation |
| `MEL_music_piano_roll` | Piano roll keys on spline |
| `MEL_music_sheet_rail` | Walkable staff lines |
| `MEL_music_harp` | Harp with strings |
| `MEL_music_room_shell` | Greybox room |
| `MEL_greybox_room_kit` | Hollow room shell |
| `MEL_greybox_openings` | Door/window boxes |
| `MEL_greybox_corridor` | Tileable hall |
| `MEL_greybox_junction` | T/X union of halls |
| `MEL_greybox_composer` | Join room+corridor+junction |

---

## 4. Specialized GN Addons

### Kawaii GN (`Tools/BlenderAddons/blender_kawaii_gn/`)
**Framework:** `core/gn_framework.py` (Blender 4.2-5.1 compatible)  
**Generators (15):**
- `kawaii_architecture.py` — Kawaii buildings
- `kawaii_characters.py` — Kawaii characters
- `kawaii_decorations.py` — Basic decorations
- `kawaii_decorations_advanced.py` — Advanced decorations
- `kawaii_effects.py` — Magic effects
- `kawaii_food.py` — Food items
- `kawaii_food_advanced.py` — Advanced food
- `kawaii_furniture.py` — Furniture
- `kawaii_greybox.py` — Greybox structures
- `kawaii_ice_cream.py` — Ice cream
- `kawaii_nature.py` — Nature elements
- `kawaii_nature_advanced.py` — Advanced nature
- `kawaii_plushies.py` — Plushies
- `kawaii_plushies_advanced.py` — Advanced plushies
- `kawaii_props.py` — Props

### Brutalist GN (`Tools/BlenderAddons/blender_brutalist_gn/`)
**Generators (4):**
- `complexes.py` — Building complexes
- `details.py` — Architectural details
- `structures.py` — Structures
- `walls.py` — Walls

---

## 5. Validated Working Pipelines

### Audio Terrain Pipeline
**Scripts:** `Tools/audio_terrain_pipeline.py` + `Content/Python/import_audio_terrain_handoff.py`  
**Status:** ✅ Validated (2026-09-02)

```powershell
# Dry run
python Tools/audio_terrain_pipeline.py --audio Content/Melodia/Characters/Itako/Audio/ita_battle_debuff_01.wav --times 0 15 30 --output Saved/AudioTerrain --dry-run

# Full run
python Tools/audio_terrain_pipeline.py --audio Content/Melodia/Characters/Itako/Audio/ita_battle_debuff_01.wav --times 0 15 30 --output Saved/AudioTerrain
```

**Output:** `.blend` + `.audio_terrain_handoff.json` (tile coords, frequency bands, FBX paths, SHA-256 hashes)

### Sea Above AAA Presets
**Script:** `Tools/stage_melodia_aaa_presets.py`  
**Status:** ✅ Validated (2026-09-02)

```powershell
python Tools/stage_melodia_aaa_presets.py --audio Content/Melodia/Characters/Metan/Audio/met_bond_01.wav --output Saved/MelodiaPresetReview/Melodia_AAA_Preset_Review.blend --export
```

**Output:** 10 presets → 10 FBX files + manifest JSON

---

## 6. Sync & Deployment

### AppData Sync
**Script:** `deploy/sync_surreal_to_live.ps1`  
**Target:** `%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons\surreal_arch\`  
**Note:** Only runs when `blender.exe` is NOT running

### Blender MCP
**Client:** `Tools/blender_mcp_client.py`  
**Port:** 9876 (TCP)  
**Protocol:** JSON over socket

```powershell
python Tools/blender_mcp_client.py get_scene_info
python Tools/blender_mcp_client.py execute_code "bpy.data.objects.keys()[:5]"
```

---

## 7. Health & Smoke Systems

### Smoke Queue
**Config:** `deploy/blender_smoke_queue.json` (6 jobs)  
**Runner:** `deploy/run_blender_smoke_queue.ps1`  
**Status:** ❌ Fails — missing `_health_check_gn_builders.py`, `_health_check_full.py`, etc.

### Health Check
**Script:** `deploy/run_melodia_health.ps1`  
**Expected output:** `sections=12/12 section_trees=173`

---

## 8. Top-of-the-Line GN Workflows (Research)

### Current State-of-the-Art in Melodia Studio

1. **MIDI-Driven World Generation**
   - Parse MIDI → extract notes → generate heightfields
   - Beatgrid merging (transpose +36 semitones)
   - Walkable terrain with instanced dressing

2. **Audio Terrain Pipeline**
   - `Sample Sound Frequencies` node (Blender 5.2)
   - Frequency-displaced geometry
   - Tiled UE handoff with deterministic partitioning

3. **Procedural Architecture Grammar**
   - Metric massing from footprints
   - Floors, bays, openings, roof outlines
   - Facade/socket points for kitbashing

4. **Greybox System**
   - Mesh Boolean DIFFERENCE for hollow rooms
   - Tileable corridors with optional end caps
   - T/X junctions for level design

5. **Preset Library**
   - 42 builders × 173 looks
   - STUDIO_LABELS for organization
   - Review Queue for visual QA

6. **Tandem City**
   - Field-wins snap to Surreal GN
   - No monolith edits required

---

## 9. Immediate Action Items

| Priority | Task | Status |
|----------|------|--------|
| 🔴 High | Sync Melodia Studio to AppData | Needs `deploy/sync_surreal_to_live.ps1` |
| 🔴 High | Fix smoke queue scripts | Missing 6 scripts |
| 🟡 Medium | Run audio terrain on more songs | 116 audio sources available |
| 🟡 Medium | Validate Sea Above presets in UE | 10 FBX files ready |
| 🟢 Low | Update GN builder catalog | 173 builders, last audited 2026-08-17 |
| 🟢 Low | Sync kawaii/brutalist GN addons | Not synced to AppData |

---

## 10. Long-term GN Roadmap

### Phase 1: Core GN Stability
- Sync all addons to AppData
- Fix smoke queue scripts
- Validate all 173 builders headless

### Phase 2: Audio Terrain Expansion
- Run pipeline on all 100+ audio sources
- Generate continent-scale tiles (16×16 grid)
- Export FBX batches for UE intake

### Phase 3: Chapter Authoring
- Lock canonical Chapter-package template
- Use GN builders for rapid prototyping
- Validate offline → PIE → restart/load

### Phase 4: Evergreen Content
- Starskiff mailbox/archive
- GN-generated gift assets
- Browser presentation (GLB export)

---

## 11. Key File Locations

| What | Path |
|------|------|
| Blender 5.2 | `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` |
| Melodia Studio addon | `Tools/BlenderAddons/melodia_studio/` |
| Surreal Arch framework | `deploy/surreal_arch/` |
| Main monolith | `deploy/surreal_architecture_gen.py` |
| Audio terrain pipeline | `Tools/audio_terrain_pipeline.py` |
| Sea Above presets | `Tools/stage_melodia_aaa_presets.py` |
| Sync script | `deploy/sync_surreal_to_live.ps1` |
| MCP client | `Tools/blender_mcp_client.py` |
| Generated assets | `Saved/AudioTerrain/`, `Saved/MelodiaPresetReview/` |
