# P0 Vertical Slice Content, Quests & Playthrough Integration

**Date**: 2026-08-27
**Authority**: Melodia Narrative Subsystem (`UMelodiaNarrativeSubsystem`) & Echo Pipeline Manifest v2.0
**Status**: Ready for Playthrough / Verified Contracts

---

## 1. Overview & Goals

This document specifies the four foundational gameplay and narrative pillars required to complete the Melodia P0 vertical slice:
1. **P0 Playthrough Loop**: Awakening in the Kaleido Nave, resolving the smoke echo in rhythm battle, and achieving the First Dream victory.
2. **Wardrobe Outfit Equip**: Discovering the Resonant Weave / Sorrow Seam outfit in the sanctum mirror, equipping it to Melusina, restoring her sorrow seam, and unlocking the `Glide` traversal capability.
3. **Choral Sheep Companion Recruitment**: Performing pitch-class call-and-response with the lost Choral Sheep motif creature (Pitch Class C / middle C) and recruiting it into the active party.
4. **Sea Above Cutscene**: Ascending the cathedral overlook, traveling to `LV_SeaAbove_Prototype`, witnessing the inverted ocean in the sky with a 16s biological membrane pulse, and watching upward water droplet anomalies.

---

## 2. Narrative Architecture & 7-Verb Notification Contract

All four systems adhere strictly to the Melodia 7-verb notification specification handled by `UMelodiaNarrativeSubsystem`:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MELODIA 7-VERB NOTIFY CONTRACT                        │
├───────────────────┬─────────────────────────────────────────────────────────┤
│ Verb              │ Syntax & Purpose                                        │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ battle            │ melodia:battle:<EncounterId>                            │
│                   │ Initiates stock JRPG turn-based rhythm encounter.       │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ quest             │ melodia:quest:<QuestId>                                 │
│                   │ Completes single quest ID.                              │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ questcomplete     │ melodia:questcomplete:<QuestId>:<FlagId>:<RewardId>:    │
│                   │                       <IntentId>:<CheckpointId>         │
│                   │ Atomic 5-way transactional commit.                      │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ flag              │ melodia:flag:<FlagId>:<true|false>                      │
│                   │ Sets persistent narrative flag.                         │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ travel            │ melodia:travel:<LevelPath>                              │
│                   │ Requests level transition / prototype map travel.       │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ reward            │ melodia:reward:<RewardId>                               │
│                   │ Grants dialogue reward idempotently.                    │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ stat              │ melodia:stat:<IntentId>:<StatId>:<Delta>                │
│                   │ Increments social/musical stat with once-guard.         │
├───────────────────┼─────────────────────────────────────────────────────────┤
│ item              │ melodia:item:give:<ItemId>:<Count>                      │
│                   │ Grants inventory / cosmetic outfit items.               │
└───────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 3. Authored Deliverables

### Pillar 1: P0 Playthrough
* **Quill Script**: `Content/MelodiaIntegration/Narrative/MelodiaQuillP0Playthrough.qsc`
* **Flow**:
  1. Melusina harmonizes with morning chime (`$ Notify melodia:stat:intent.p0.morning_resonance:melodia_harmony:2`).
  2. Advances to altar and confronts smoke echo (`$ Notify melodia:battle:melodia_smoke_encounter`).
  3. On victory: commits atomic quest completion (`quest.first_dream`), sets `flag.p0.playthrough.completed:true`, grants `reward.first_resonance_echo`.
  4. On defeat/flee: handles graceful state flags (`flag.p0.playthrough.attempted` / `flag.p0.playthrough.fled`).

### Pillar 2: Wardrobe Outfit Equip
* **Quill Script**: `Content/MelodiaIntegration/Narrative/MelodiaQuillWardrobeEquip.qsc`
* **Manifest**: `specs/wardrobe/wardrobe_equip_p0_manifest.v1.json`
* **Flow**:
  1. Inspects woven Resonant Weave garment in sanctum mirror.
  2. Grants item (`$ Notify melodia:item:give:item.outfit.melusina_v2:1`) and reward (`reward.wardrobe.first_outfit`).
  3. Increments elegance stat (`$ Notify melodia:stat:intent.wardrobe.elegance:melodia_elegance:3`).
  4. Sets persistent flags (`flag.wardrobe.outfit_equipped:true` and `flags.melusina.sorrow_seam_restored:true`).
  5. Unlocks `EMelodiaFormCapability::Glide` (forward speed 750 cm/s, gravity scale 0.25).
  6. Commits quest `quest.wardrobe.equip_outfit`.

### Pillar 3: Choral Sheep Companion Recruitment
* **Quill Script**: `Content/MelodiaIntegration/Narrative/MelodiaQuillChoralSheepRecruit.qsc`
* **Manifest**: `specs/companions/choral_sheep_recruit_manifest.v1.json`
* **Flow**:
  1. Discovers Choral Sheep grazing near the resonance spring.
  2. Melusina sings triad call-and-response in Pitch Class C (C4-E4-G4).
  3. Choral Sheep harmonizes back, incrementing harmony stat (`$ Notify melodia:stat:intent.choral_sheep.call_response:melodia_harmony:2`).
  4. Sets companion recruitment flag (`flag.companion.choral_sheep_recruited:true`).
  5. Binds `companion.choral_sheep` to party following and rhythm assistance.
  6. Commits quest `quest.companion.choral_sheep`.

### Pillar 4: Sea Above Cutscene
* **Quill Script**: `Content/MelodiaIntegration/Narrative/MelodiaQuillSeaAboveCutscene.qsc`
* **Manifest**: `specs/cinematics/sea_above_cutscene_manifest.v1.json`
* **Flow**:
  1. Reaches Cathedral Overlook and initiates level travel (`$ Notify melodia:travel:/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`).
  2. Triggers cinematic camera tracks (pan across overlook, 65° upward tilt to sky membrane, Melusina reaction shot).
  3. Modulates biological membrane pulse (16.0s period) on `MPC_Melodia_Palette` (`MembranePulse` and `MembraneSheen` $0.18 \rightarrow 0.32$).
  4. Spawns upward water droplet anomalies (`NS_SeaAbove_UpwardDroplets_Prototype`).
  5. Awards resonance stat (`$ Notify melodia:stat:intent.sea_above.witness:melodia_resonance:5`).
  6. Sets `flag.cutscene.sea_above_witnessed:true` and `flag.sea_above.membrane_pulse_active:true`.
  7. Commits quest `quest.cutscene.sea_above`.

---

## 4. Specification Packages & Manifests

* **Progression Package**: `specs/progression/melodia_p0_slice_quests.v1.json`
* **Wardrobe Equip Manifest**: `specs/wardrobe/wardrobe_equip_p0_manifest.v1.json`
* **Companion Recruit Manifest**: `specs/companions/choral_sheep_recruit_manifest.v1.json`
* **Cutscene Manifest**: `specs/cinematics/sea_above_cutscene_manifest.v1.json`

---

## 5. Verification & Test Evidence

### Python Contract Tests
```powershell
$env:PYTHONPATH="C:\EnvironmentPortfolio\BS_GodFile\Content\Python;C:\EnvironmentPortfolio\BS_GodFile\Tools"
& "C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe" `
  -B -m unittest Content.Python.Tests.test_p0_quests_and_content_contract
```
* **Outcome**: 8/8 tests passed in 0.005s (OK).

### Full Contract Suite
* `Content.Python.Tests.test_p0_quests_and_content_contract`: PASS (8/8)
* `Content.Python.Tests.test_sea_above_t3d_contract`: PASS (4/4)
* `Content.Python.Tests.test_melusina_systems_contract`: PASS (4/4)
* `Tools/test_melodia_progression_contract.py`: PASS (6/6 checks)
* `Tools/test_echo_contract.py`: PASS (77/77 checks)

### Unreal C++ Automation Test
* `Source/BS_GodFile/MelodiaIntegration/Tests/MelodiaP0ContentQuestsTests.cpp`:
  * `Melodia.P0.PlaythroughQuest`
  * `Melodia.P0.WardrobeEquip`
  * `Melodia.P0.ChoralSheepRecruit`
  * `Melodia.P0.SeaAboveCutscene`
