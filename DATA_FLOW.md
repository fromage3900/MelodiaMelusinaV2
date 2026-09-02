# Technical Data Flow Specification — Melodia Rhythm-JRPG

**Canonical Data Flow & State Lifecycle**
**Last Updated:** 2026-09-01 (Evening P0 Closeout & Chapter Loop Checkpoint)
**Target Engine:** Unreal Engine 5.8.0 | C++20 | Python 3.11

---

## 1. End-to-End Chapter Gameplay Data Lifecycle

The diagram below traces the end-to-end data lifecycle across the 6-phase universal chapter gameplay loop:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: NARRATIVE INITIATION                                                          │
│   QuillScript Node ──► UMelodiaNarrativeSubsystem::ProcessNotification()               │
│                        └── Dispatches "melodia:quest:quest.first_dream.started"        │
│                        └── Triggers BP_SanctuaryDepartureGate (bIsOpen = true)         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 2: OVERWORLD TRAVERSAL & MUSIC-AS-KEY PUZZLE                                     │
│   BP_Melusina_Character ──► Steps on Resonant Piano Node                               │
│                             └── APCGHeroMusicGraphHost::RegisterNote(EHeroMusicNote)   │
│                             └── Matches Harmonic Phrase -> Dispatches "melodia:inspect"│
│                             └── Route barrier deactivates collision                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 3: JRPG COMBAT WITH RHYTHM HIGHWAY TIMING                                        │
│   BP_TurnBasedBattleManager ──► UMelodiaUIBridgeSubsystem (Render Battle HUD)          │
│                                 ├── Player selects Attack / Resonance Skill            │
│                                 ├── WBP_MelodiaRhythmHighway spawns notes              │
│                                 ├── Player hits key (Q/W/O/P) -> Computes Timing Delta │
│                                 ├── Grade Multiplier: Poor(0.35) .. Perfect(1.50)      │
│                                 ├── MPC_Melodia_Palette receives PulseImpact scalar    │
│                                 └── JRPG Combat Engine applies FinalDamage = Base * Grd│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 4: BATTLE RESOLUTION & IDEMPOTENT REWARD DELIVERY                                │
│   Boss HP <= 0 ──► Combat Subsystem emits TerminalResult(EVictory)                     │
│                    ├── Exactly-once QuillScript Resume                                 │
│                    └── Reward Intent-ID: "reward.wardrobe.dress_shorewake"             │
│                    └── UMelodiaWardrobeSubsystem registers unlocked outfit piece       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 5: WARDROBE TRAVERSAL UPGRADE                                                    │
│   Player Equips Outfit ──► UMelodiaWardrobeSubsystem updates SkeletalMesh parts        │
│                            └── Activates IMelodiaTraversalCapabilityProvider (Glide)   │
│                            └── BP_Melusina_Character enables airborne glide physics    │
│                            └── Player glides across chasm to reach chapter gateway     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ Phase 6: CANONICAL CHECKPOINT & SAVE GAME PERSISTENCE                                  │
│   BP_CheckpointAnchor ──► BP_JRPGSaveGame::SaveToSlot("CanonicalSaveSlot_0")           │
│                           ├── Serializes Character Stats & Party HP/MP                 │
│                           ├── Serializes Active & Unlocked Wardrobe Outfits            │
│                           ├── Serializes Quest Flags & Narrative Record Version        │
│                           └── Serializes Inventory Contents & Key Items                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase-by-Phase Technical Data Schemas

### 2.1 Narrative Notification Schema
- **Payload Structure (`FMelodiaNotification`):**
  ```json
  {
    "verb": "quest",
    "target_id": "first_dream",
    "action": "started",
    "intent_id": "intent.quest.first_dream.001",
    "timestamp": 1725219900
  }
  ```
- **Idempotency Rule:** `UMelodiaNarrativeSubsystem` records consumed `intent_id` strings in `FMelodiaNarrativeRecord`. Replaying the same dialogue or notification will never duplicate rewards or quest state.

### 2.2 Rhythm Combat Input & Grade Schema
- **Input Channels:** Key mappings `Q`, `W`, `O`, `P` corresponding to 4 highway lanes.
- **Grading Windows & Multipliers:**
  - `Perfect`: $\pm 45\text{ ms} \implies 1.50\times \text{ Damage Multiplier}$
  - `Great`: $\pm 90\text{ ms} \implies 1.20\times \text{ Damage Multiplier}$
  - `Good`: $\pm 140\text{ ms} \implies 1.00\times \text{ Damage Multiplier}$
  - `Poor`: $> 140\text{ ms} \implies 0.35\times \text{ Damage Multiplier}$
- **Material Pulse:** Writes scalar `RhythmPulse = 1.0` and `Mid = 0.8` to `MPC_Melodia_Palette` via game thread Slate post-tick flush.

### 2.3 Wardrobe Traversal Capability Interface
- **Interface:** `IMelodiaTraversalCapabilityProvider`
- **Properties:**
  - `bCanGlide`: Boolean enabling low-gravity horizontal air velocity.
  - `bCanSwim`: Boolean enabling aquatic volume navigation.
  - `bCanDash`: Boolean enabling ground speed boost burst.
- **Round-Trip Serialization:** Outfit ID and active slot indices serialize into `FMelodiaWardrobeSaveRecord` within `BP_JRPGSaveGame`.

### 2.4 Canonical Checkpoint Save Structure (`BP_JRPGSaveGame`)
- **Serialized Structs:**
  1. `FPartySaveData`: Member IDs, current HP/MP, base stats, equipped gear.
  2. `FInventorySaveData`: Item IDs, quantities, unique key items.
  3. `FWardrobeSaveData`: Unlocked outfit IDs, currently equipped wardrobe parts.
  4. `FNarrativeSaveData`: Narrative record version, quest flags dictionary, consumed reward intent IDs.
  5. `FWorldPositionSaveData`: Active level path, checkpoint transform `(X, Y, Z, Roll, Pitch, Yaw)`.

---

## 3. Data Integrity & Invariants

1. **Zero Dual-Writer Collisions:** UI surfaces and HUD elements receive state strictly from `UMelodiaUIBridgeSubsystem`.
2. **Deterministic Replay:** Given the same initial save slot and input stream, the battle resolution and narrative progression yield identical state.
3. **Save Forward Compatibility:** All serialized records declare explicit `Version` fields (e.g., `FMelodiaNarrativeRecord::CurrentVersion`). Deserialization checks version compatibility before parsing.
