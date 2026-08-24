# Melodia / Melusina Pipeline Review and Expansion — 2026-08-24

## Executive summary

The Melodia/Melusina pipeline is a multi-layer system spanning Blender
authoring, offline world generation, showroom rendering, UE5 runtime,
plugins, and portfolio surfaces. This review documents every active layer
from disk evidence, identifies honest gaps, and proposes concrete
expansions.

Current state:
- Blender authoring: `melodia_studio`, `melodia_pose_audit`,
  `melodia_showroom`, `melodia_stage`
- UE runtime: `Source/BS_GodFile/MelodiaIntegration/*`, `Plugins/`
- Tests: `melodia_studio` 53 OK / 1 expected failure; `melodia_showroom`
  5 OK; `melodia_pose_audit` smoke OK
- Open gates: `hud_single_writer`, `rhythm_grade_to_result`,
  `music_world_key`, `wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`,
  `rhythm_owner`

---

## 1. Pipeline architecture overview

```text
MIDI authoring
  -> Blender melodia_studio  -> terrain presets, dressing, walkability
  -> Blender melodia_pose_audit -> skeleton/pose verification
  -> Blender melodia_showroom -> frame/render/presentation
  -> Blender melodia_stage  -> Geometry Nodes, staging
  -> Tools/midi_to_voxel/midi_voxel_v3.py -> OBJ + vertex colors
  -> Content/MelodiaIntegration/MIDI -> authored MIDI assets

UE5 runtime
  -> Source/BS_GodFile/MelodiaIntegration/* -> subsystems/components
  -> Plugins/MelodiaCore -> locomotion, traversal
  -> Plugins/MelodiaNPR -> toon/NPR rendering
  -> Plugins/MelodiaWardrobe -> outfit management
  -> Plugins/MelodiaTokenWallet -> economy persistence
  -> Blueprint layer: BP_MelusinaJRPGCharacter, WBP_*, etc.

Portfolio/docs
  -> Docs/Architecture/*
  -> Docs/Handoffs/*
  -> Docs/Integrations/*
  -> deploy/surreal_arch/*
```

---

## 2. Blender authoring layer review

### 2.1 melodia_studio
Files:
- `Tools/BlenderAddons/melodia_studio/midi_bridge.py`
- `Tools/BlenderAddons/melodia_studio/terrain_dressing.py`
- `Tools/BlenderAddons/melodia_studio/studio_panel.py`
- `Tools/BlenderAddons/melodia_studio/walkable_world.py`
- `Tools/BlenderAddons/melodia_studio/tests/`

Presets:
- 14 terrain presets including tarantella_bounce, canon_echo,
  gavotte_hedges, rhapsody_fold, berceuse_overhang, ritornello_rings
- 16 dressing styles including pavane_grotto, saltarello_ledges,
  madrigal_canopy, chaconne_weave, aria_mist
- Dressing kinds: resonance_crystal, chime_pillar, moss_cluster,
  songstone, note_bloom
- Magic systems: aurora_veil, motif_wisps, cadence_pool,
  harmonic_rings, ground_glow

Verified behavior:
- v4 serpentine fold produces square-ish footprints, worst step == 1
- v5 placement: character seated within 0.086 units of local ground
- Dressing budget deterministic for fixed seed
- All dressing kinds place at least one prop
- Jitter cannot push props onto empty cells
- Water level inside terrain height range

Open defect D7:
- `surface_height_divisor` / `cave_height_divisor` ignored by
  `Tools/midi_to_voxel/midi_voxel_v3.py:generate()` because it
  hardcodes `vel // 32` / `vel // 40`. Guarded by
  `test_height_divisors_are_honoured` expectedFailure.

### 2.2 melodia_pose_audit
Files:
- `Tools/BlenderAddons/melodia_pose_audit/__init__.py`
- `Tools/BlenderAddons/melodia_pose_audit/properties.py`
- `Tools/BlenderAddons/melodia_pose_audit/operators.py`
- `Tools/BlenderAddons/melodia_pose_audit/panel.py`

Verified:
- Headless smoke test writes audit results to bpy.data.texts
- COMMON_MELODIA_BONES includes pelvis, spine_01/02/03, neck_01/02, head
- Registration clean in headless mode

### 2.3 melodia_showroom
Files:
- `Tools/BlenderAddons/melodia_showroom/__init__.py`
- `Tools/BlenderAddons/melodia_showroom/properties.py`
- `Tools/BlenderAddons/melodia_showroom/panel.py`
- `Tools/BlenderAddons/melodia_showroom/operators.py`
- `Tools/BlenderAddons/melodia_showroom/showroom_bridge.py`
- `Tools/BlenderAddons/melodia_showroom/tests/test_showroom.py`

Verified:
- End-to-end pipeline: MIDI -> terrain -> dressing -> frame -> render
- Drive-aware repo_root() resolves on C: and G:
- Junction-safe path resolution via os.path.realpath
- 14 combo presets wired through _preset_parts()
- EEVEE render output confirmed

### 2.4 melodia_stage
Files:
- `Tools/BlenderAddons/melodia_stage/`

Status:
- Blender-side staging addon present; parallel lane work synced in
  commit ff55800a

---

## 3. UE5 runtime layer review

### 3.1 Authoritative systems
Files:
- `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatTypes.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmSkillDefinition.h`

Status:
- Rhythm combat architecture documented in
  `Docs/MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md`
- Design locked; Cadence Strike vertical slice specified
- Grade balance: Miss 0.70, Good 1.00, Great 1.20, Perfect 1.45
- `MelodiaJRPGPresentationRhythmComponent` owns timing-window eval

### 3.2 Audio/Music time
Files:
- `Source/BS_GodFile/MelodiaIntegration/MelodiaMusicClockSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGPresentationRhythmComponent.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaAudioReactivePresentationSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/RhythmBeatTracker.cpp/.h`

Status:
- Single musical-time authority: `MelodiaMusicClockSubsystem`
- Harmonix preferred; Quartz fallback
- Beat/bar forwarding without DeltaTime scheduling

### 3.3 UI/Bridge
Files:
- `Source/BS_GodFile/MelodiaIntegration/MelodiaUIBridgeSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaJRPGBattleOverlaySubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaQuillPresentationWidgets.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaUIFeedbackSubsystem.cpp/.h`

Open defect:
- `hud_single_writer`: two subsystems independently create battle-time
  widgets. Merge `MelodiaJRPGBattleOverlaySubsystem` into
  `MelodiaUIBridgeSubsystem`.

### 3.4 Traversal/Water/Hair
Files:
- `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaWaterGameplayControllerComponent.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaHairComponent.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaSorrowSeamComponent.cpp/.h`

Status:
- Glide, swim, dive, dash mechanics implemented
- Water hair render pipeline present
- Sorrow Seam signature veil driver shipped

### 3.5 Economy/Save/Narrative
Files:
- `Source/BS_GodFile/MelodiaIntegration/MelodiaSaveSlotLibrary.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaSaveRecoverySubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaNarrativeSubsystem.cpp/.h`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaPersonaSubsystem.cpp/.h`

Status:
- Python reference implementation at `deploy/melodia_economy.py`
- Four economies + grief hook specified
- C++ port not started; no `*Econom*` or `*Grief*` source files
- Narrative idempotency guards audit available via MCP

### 3.6 Blueprint/runtime assets
Files:
- `Content/MelodiaIntegration/Blueprints/BP_MelusinaJRPGCharacter.uasset`
- `Content/Melodia/Characters/Melusina/ABP_Melusina_Current.uasset`
- `Content/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair.uasset`
- `Content/Melodia/DataStuctures/DT_MelodySlime_Skills.json`

Status:
- Canonical pawn: `BP_MelusinaJRPGCharacter` (JRPG base + Melodia SCS)
- Animation: `ABP_Melusina_Current`, water hair ABP
- Skill data: `DT_MelodySlime_Skills.json`

---

## 4. Plugin layer review

| Plugin | Role | Status |
|---|---|---|
| MelodiaCore | Locomotion, traversal, anim instance | Compiled |
| MelodiaNPR | Toon/NPR shading | Present |
| MelodiaWardrobe | Outfit/equip management | Present; compile verified |
| MelodiaTokenWallet | Economy persistence | Present |

---

## 5. Test/evidence inventory

### 5.1 Offline tests
- `melodia_studio/tests/test_midi_bridge.py`: 20 tests pass
- `melodia_studio/tests/test_terrain_dressing.py`: 33 tests pass
- `melodia_showroom/tests/test_showroom.py`: 5 tests pass
- `melodia_pose_audit`: smoke test passes

### 5.2 UE tests
- `MelodiaRhythmCombatTests.cpp`
- `MelodiaWiringContractTests.cpp`
- `MelodiaSanityTest.cpp`
- `MelodiaWaterGameplayTests.cpp`

### 5.3 Blender renders
- `Saved/Audit/midi_matrix/` — 30 frames, v3 ribbon
- `Saved/Audit/midi_walkable/` — 24 frames, v4 walkable
- `Saved/Audit/midi_v5/` — 20 frames, v5 dressed
- Showroom: `Tools/MelodiaProceduralStudio/GeneratedScenes/showroom/`

### 5.4 Evidence docs
- `Docs/Evidence/2026-08-22_melusina_idle_glide/` — animation capture
- `Docs/Evidence/2026-08-23_hud_single_writer/` — HUD writer audit

---

## 6. Open defects and gates

| ID | Defect | Layer | Status |
|---|---|---|---|
| D7 | Preset divisors ignored by voxel generator | Blender | OPEN |
| D14 | v5 renders not visually validated | Blender | OPEN |
| hud_single_writer | Two subsystems create battle widgets | UE | OPEN |
| rhythm_grade_to_result | Grade -> effect request not wired | UE | OPEN |
| music_world_key | Music -> world interaction key | UE | OPEN |
| wardrobe_equip_roundtrip | Equip state not round-tripping | UE | OPEN |
| wardrobe_gameplay_hook | Gameplay hook not connected | UE | OPEN |
| rhythm_owner | Rhythm ownership unclear | UE | OPEN |
| D16 | 37 GeneratedScenes missing material/UVs | Blender | OPEN |
| D17 | Only 1 substantive MIDI asset | Content | OPEN |

---

## 7. Expansion proposals

### 7.1 Preset expansion
Done:
- Added 7 terrain presets: tarantella_bounce, canon_echo,
  gavotte_hedges, rhapsody_fold, berceuse_overhang, ritornello_rings
- Added 5 dressing styles: pavane_grotto, saltarello_ledges,
  madrigal_canopy, chaconne_weave, aria_mist
- Wired through Studio UI, Showroom combo map, tests

### 7.2 Pipeline hardening
- Fix D7: expose `surface_div`/`cave_div` kwargs in
  `midi_voxel_v3.generate()` so preset variety is real, not nominal
- Add render verification harness that captures SHA + pixel stats for
  each preset so variety is measurable, not subjective
- Add `melodia_pose_audit` render output so pose checks produce
  visual evidence, not just log lines

### 7.3 UE expansion
- Port `MelodiaGlobalEconomy` to C++ with parity tests against
  `deploy/melodia_economy.py`
- Merge `MelodiaJRPGBattleOverlaySubsystem` into
  `MelodiaUIBridgeSubsystem`; build economy HUD on the existing
  design-system widgets
- Wire rhythm grade -> effect request -> stock resolver exactly once
- Connect wardrobe equip to gameplay hooks

### 7.4 Content expansion
- Author 3+ substantive MIDI files for real level variety
- Export heightfield from Blender as 16-bit PNG for Gaea erosion
- Build Geometry-Nodes scatter from `plan_dressing()` output
- Target 10k+ instances at interactive frame rate

### 7.5 Documentation expansion
- Create `Docs/MELODIA_MELUSINA_PIPELINE_2026-08-24.md` as the
  master review document
- Update `Docs/P0_TASK_LEDGER.json` with expanded preset/dressing work
- Add evidence ledger entries for each new preset

---

## 8. Immediate action items

1. Fix D7: add optional divisors to `midi_voxel_v3.generate()`
2. Run owner visual review of existing v5 renders
3. Expand MIDI library beyond 128BPM arpeggio
4. Start C++ economy port with parity tests
5. Merge HUD writers; build economy HUD
6. Wire rhythm grade to stock resolver
7. Add wardrobe gameplay hook

---

## 9. Verified evidence summary

| Layer | Evidence | Status |
|---|---|---|
| melodia_studio | 53 tests pass, 1 expected failure | VERIFIED |
| melodia_showroom | 5 tests pass, Blender render OK | VERIFIED |
| melodia_pose_audit | Smoke test OK | VERIFIED |
| UE compile | BP_MelusinaJRPGCharacter 0/0 | VERIFIED |
| Animation | Idle/glide captures in Docs/Evidence | VERIFIED |
| Git sync | Commit ff55800a, 17 files, 2662 insertions | VERIFIED |

---

## 10. Source of truth files

- `Docs/MELODIA_AUTHORITATIVE_RHYTHM_COMBAT_WIRING_2026-08-03.md`
- `Docs/HARMONIX_MIDI_RHYTHM_CONTRACT_2026-07-29.md`
- `Docs/MIDI_WORLDGEN_REVIEW_AND_AAA_PLAN_2026-08-24.md`
- `Docs/UNFINISHED_AND_PLANNED_WORK_PREP_2026-08-24.md`
- `Docs/Handoffs/P0_INTEGRATION_HANDOFF_2026-08-20.md`
- `Docs/Integrations/MELODIA_SHOWROOM_INTEGRATION_2026-08-24.md`
- `Tools/BlenderAddons/melodia_studio/midi_bridge.py`
- `Tools/BlenderAddons/melodia_studio/terrain_dressing.py`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaRhythmCombatSubsystem.cpp`
- `Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp`
