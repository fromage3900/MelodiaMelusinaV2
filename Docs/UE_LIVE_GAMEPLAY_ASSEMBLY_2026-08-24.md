# UE Live Gameplay Assembly Guide — 2026-08-24

## Goal
Import Melodia world-gen outputs into UE 5.8 for immediate playable terrain + props + magic.

## Inputs ready

### Heightfields (16-bit PNG)
- `Saved/Audit/world_build_20260824/<preset>/heightfield_<preset>.png`
- 14 presets generated

### Dressing plans (JSON)
- `Saved/Audit/world_build_20260824/<preset>/dressing_plan_<preset>.json`
- Schema: `style_id`, `style_label`, `seed`, `budget`, `field_cells`, `dressing.count`, `magic.count`, `terrain_obj`, `items[]`

### Runtime manifest
- `Saved/Audit/world_build_20260824/runtime_manifest.json`
- Maps preset IDs to heightfield/dressing plan/material/PCG paths

## Import steps

### 1. Landscape
1. Open UE Editor
2. Create new level or use test level
3. Import heightfield PNG via Landscape tool
4. Set material: `M_Master_Toon_Landscape_HeightBlend`
5. Verify scale: 1 unit = 1 meter recommended

### 2. PCG placement
1. Place `BP_MelodiaPCGControl` in level
2. Set `DressingPlanPath` to JSON path from runtime manifest
3. Set `PresetId` to chosen preset (e.g. `waltz_garden_waltz`)
4. Run PCG generation

### 3. Props
- Dressing plan items provide: `kind`, `location [x,y,z]`, `scale`, `rotation_z`, `colour`, `emissive`
- Map `kind` to static mesh via data table (to be created)
- Place via PCG or runtime spawner

### 4. Magic systems
- Magic plan items: `system`, `location [x,y,z]`, `radius`, `colour`
- Map system to VFX blueprint:
  - `cadence_pool` → water ripple
  - `motif_wisps` → particle trail
  - `aurora_veil` → volumetric fog
  - `harmonic_rings` → ring decal
  - `ground_glow` → emissive plane

### 5. Water/narrative bridge
- Attach `UMelodiaPCGWaterGameplayBridgeComponent` to `APCGHeroMusicGraphHost`
- Attach `UMelodiaPCGNarrativeChallengeBridgeComponent` to `APCGHeroMusicGraphHost`
- Verify water resonance + narrative challenge events in PIE

## Validation checklist

- [ ] Landscape imports without errors
- [ ] Heightfield dimensions match terrain footprint
- [ ] Material applies without missing splatmaps
- [ ] PCG spawns props at plan locations
- [ ] No prop overlap or floating props
- [ ] Magic VFX fire at plan locations
- [ ] Water/narrative bridge events fire in PIE
- [ ] Frame rate >= 30fps with full PCG density

## Evidence to capture

- PIE screenshot: `Saved/Audit/world_build_20260824/pie_<preset>_<timestamp>.png`
- PCG stats: `Saved/Audit/world_build_20260824/pcg_stats_<preset>.json`
- Performance: `Saved/Audit/world_build_20260824/perf_<preset>.csv`
