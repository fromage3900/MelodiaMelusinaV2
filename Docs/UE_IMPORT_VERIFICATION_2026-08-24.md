# UE World-Building Import Verification — 2026-08-24

## Goal
Verify every artifact produced by the expanded Melodia pipeline can be
imported into UE 5.8 without manual repair.

## Verified outputs

### Renders
- `Tools/MelodiaProceduralStudio/GeneratedScenes/showroom/waltz_garden_waltz.png`
- `Tools/MelodiaProceduralStudio/GeneratedScenes/showroom/tarantella_bounce_saltarello.png`
- `Tools/MelodiaProceduralStudio/GeneratedScenes/showroom/canon_echo_pavane.png`
- `Tools/MelodiaProceduralStudio/GeneratedScenes/showroom/gavotte_hedges_aria.png`
- `Tools/MelodiaProceduralStudio/GeneratedScenes/showroom/rhapsody_fold_chaconne.png`

All renders: PNG, 1.2–1.3 MB, EEVEE output, same resolution.

### Heightfields
- `Saved/Audit/world_build_20260824/heightfield_waltz_garden.png` — 65x12, 295 bytes
- `Saved/Audit/world_build_20260824/heightfield_tarantella_bounce.png` — 66x13, 394 bytes
- `Saved/Audit/world_build_20260824/heightfield_canon_echo.png` — 65x11, 262 bytes
- `Saved/Audit/world_build_20260824/heightfield_gavotte_hedges.png` — 64x11, 265 bytes
- `Saved/Audit/world_build_20260824/heightfield_rhapsody_fold.png` — 66x12, 277 bytes

All heightfields: PNG, grayscale 16-bit (`I;16`), dimensions match terrain footprint.

### Dressing plans
- `Saved/Audit/world_build_20260824/dressing_plan_waltz_garden.json` — 22 props, 2 magic
- `Saved/Audit/world_build_20260824/dressing_plan_tarantella_bounce.json` — 34 props, 2 magic
- `Saved/Audit/world_build_20260824/dressing_plan_canon_echo.json` — 15 props, 2 magic
- `Saved/Audit/world_build_20260824/dressing_plan_gavotte_hedges.json` — 17 props, 2 magic
- `Saved/Audit/world_build_20260824/dressing_plan_rhapsody_fold.json` — 14 props, 2 magic

All dressing plans: valid JSON, schema matches UE PCG bridge expectations.

## UE import checklist

### Landscape
- [ ] Create new level or use test level
- [ ] Import heightfield PNG as Landscape
- [ ] Apply material: `M_Master_Toon_Landscape_HeightBlend`
- [ ] Verify heightfield dimensions match terrain footprint
- [ ] Verify no import errors in Output Log

### Materials
- [ ] `M_Master_Toon_Landscape_HeightBlend` exists at:
  `Content/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Landscape_HeightBlend/`
- [ ] Landscape layer info matches heightfield channels

### PCG placement
- [ ] Import dressing plan JSON via PCG framework
- [ ] Place 100-500 props from plan
- [ ] Verify no prop overlap or floating props
- [ ] Verify prop count matches plan JSON `dressing.count`

### Bridge components
- [ ] `UMelodiaPCGWaterGameplayBridgeComponent` attaches to `APCGHeroMusicGraphHost`
- [ ] `UMelodiaPCGNarrativeChallengeBridgeComponent` attaches to `APCGHeroMusicGraphHost`
- [ ] Water resonance events fire on pattern completion
- [ ] Narrative challenge commits on pattern completion

## Evidence

| Preset | Render | Heightfield | Props | Magic | Dressing Plan |
|---|---|---|---|---|---|
| waltz_garden_waltz | 1.3 MB | 65x12 | 22 | 2 | JSON valid |
| tarantella_bounce_saltarello | 1.3 MB | 66x13 | 34 | 2 | JSON valid |
| canon_echo_pavane | 1.3 MB | 65x11 | 15 | 2 | JSON valid |
| gavotte_hedges_aria | 1.3 MB | 64x11 | 17 | 2 | JSON valid |
| rhapsody_fold_chaconne | 1.3 MB | 66x12 | 14 | 2 | JSON valid |

## Next actions

1. Import first heightfield (`waltz_garden_waltz`) into UE
2. Verify Landscape material applies without errors
3. Import dressing plan JSON via PCG
4. Place props and verify collision
5. Test water/narrative bridge components in PIE
