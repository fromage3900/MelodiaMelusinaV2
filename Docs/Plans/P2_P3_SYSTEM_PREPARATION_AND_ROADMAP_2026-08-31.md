# P2 & P3 System Preparation and Progression Roadmap

**Date:** 2026-08-31
**Status:** System Preparation & Schema Alignment Complete
**Reference Architecture:** `REUSABLE_CHAPTER_VALIDATION_SYSTEM_2026-08-31.md`

---

## 1. Overview & Progression Architecture

The Melodia narrative and environmental systems follow a modular, contract-driven architecture. Chapter progression is represented through standardized data packages that delegate state authority to established single-writer subsystems:

```
[P0: First Dream / Sanctuary]
    ↓ (Wardrobe Equip / Choral Sheep / Sea Above Cutscene)
[P1: Shorewake Calling & Mara Elletra Vell]
    ↓ (Starskiff Mooring / Seam-Reading / Veil Passage)
[P2: Faraway Mother — Living Anatomy & Fabric Mountains]
    ↓ (Cymatics Audio-Reactive WPO / Hemlands / Shoulder Folds)
[P3: Horizon Eater — Celestial Needle & Seam Strata]
    ↓ (Horizon Apex / Needle Threading / Seam Harmonization)
```

### Canonical Subsystem Authorities
1. **`UMelodiaNarrativeSubsystem` / `FMelodiaNarrativeRecord`:** Single-writer persistence for quests, flags, intents, and checkpoints.
2. **QuillScript (`.qsc` / `.uasset`):** Strict 7-verb notification dialogue system (`battle`, `quest`, `questcomplete`, `flag`, `travel`, `reward`, `stat`, `item`).
3. **`UMelodiaCymaticsSubsystem` & Audio Presentation:** Chladni standing-wave calculations and audio-reactive parameters (`BeatPulse`, `BassIntensity`, `MidIntensity`) driving material World Position Offset (WPO).
4. **`UMelodiaWardrobeSubsystem`:** Cosmetic asset inventory, capability gates (`Glide`, `ResonantWeave`), and gameplay state hooks.
5. **Oceanology & Traversal Blueprints:** Water physics and vehicle traversal (`BP_Starskiff_MK2`).

---

## 2. P2 System Preparation: Faraway Mother & Fabric Mountains

### 2.1 Core Concepts
* **Thesis:** Fabric behaves like geography; landscape is draped anatomy.
* **Level Route:** `/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype` → `LV_FarawayMother_Hemlands`.
* **Progression Package:** `specs/progression/melodia_p2_fabric_mountains_progression.v1.json`.

### 2.2 Audio-Reactive WPO Architecture
* **Signal Flow:**
  `Music Clock (128 BPM)` → `UMelodiaAudioReactivePresentationSubsystem` (`MPC_Melodia_Palette`) → `UMelodiaCymaticsSubsystem` (Chladni $n,m$ harmonic calculation) → `MF_FabricMountainWPO` → `M_FabricMountain_Master` / `MI_FabricMountain_Base`.
* **WPO Frequency Layers:**
  1. *Macro Swell:* Cymatics Chladni modes driven by `BassIntensity` (1 km wavelength, 50–100 m amplitude).
  2. *Medium Folds:* Higher-frequency standing waves driven by `MidIntensity` (100 m wavelength, 10–20 m amplitude).
  3. *Micro Detail:* Copernicus PBR height maps sampled with `BeatPulse` (1 m wavelength, 0.5–2 m amplitude).
  4. *Wind Response:* Dynamic cloth drape from `MF_ClothWindDrape`.

### 2.3 Assets & Material Instances
* **HDAs & GN Builders:** 8 Faraway Mother geometry nodes builders (`deploy/surreal_arch/melodia_gn/mother.py`) and 6 HDAs (`faraway_p2_corset`, `cradle`, `gown`, `mantle`, `ornament`, `veil`).
* **Copernicus Fabric Maps:** 11 baked PBR variants (`GildedLoom`, `SilkWaterfall`, `CherryBlossomWood`, `DancingCrystals`, `FinalDreamweaver`).
* **Allowlist Entries Queued for P2:**
  * Quests: `quest.p2.fabric_mountains.attunement`, `quest.p2.hemlands.crossing`
  * Flags: `flag.p2.fabric_mountains.attuned`, `flag.p2.hemlands.traversed`, `flag.p2.cymatics.wpo_active`
  * Rewards: `reward.p2.chladni_tuning_fork`, `reward.p2.faraway_mother_veil_fragment`

---

## 3. P3 System Preparation: Horizon Eater & Seam Strata

### 3.1 Core Concepts
* **Thesis:** The boundary of the world where draped fabric transitions into monumental vertical needle architecture and cosmic seam strata.
* **Level Route:** `LV_FarawayMother_Hemlands` → `LV_HorizonEater_Apex`.
* **Progression Package:** `specs/progression/melodia_p3_horizon_eater_progression.v1.json`.

### 3.2 Architectural & Traversal Escalation
* **Celestial Needle Encounter:** Precision acoustic attunement aligning resonant frequencies to thread the monumental needle monolith.
* **Vertical Seam Strata:** Multi-tier vertical climbing and gliding routes requiring unlocked traversal capabilities (`ResonantWeave` + `Glide`).
* **Allowlist Entries Queued for P3:**
  * Quests: `quest.p3.horizon_eater.apex_ascent`, `quest.p3.celestial_needle.threading`
  * Flags: `flag.p3.horizon_eater.apex_reached`, `flag.p3.celestial_needle.threaded`, `flag.p3.seam_strata_unlocked`
  * Rewards: `reward.p3.celestial_thread_spool`, `reward.p3.horizon_eater_resonance_crest`

---

## 4. Integration & Validation Pipeline

Before promoting P2 or P3 content packages into live gameplay:
1. **Offline Spec Validation:** Run `Tools/test_melodia_chapter_content_package_contract.py` and `Tools/test_melodia_progression_contract.py`.
2. **C++ Automation Tests:** Execute test suites under `Melodia.Quest.*` and `Melodia.Chapter.*`.
3. **Allowlist Sync:** Verify all referenced IDs exist in `DA_MelodiaIntegrationConfig.uasset` before authoring active Quill scripts.
4. **PIE Smoke & Save/Load Roundtrip:** Confirm zero state leakage across level transitions and process restarts.
