# Current System Architecture Map — Melodia (BS_GodFile)

**Target Engine:** Unreal Engine 5.8.0 | Blender 5.2 LTS | C++20 | Python 3.11
**Last Updated:** 2026-09-01 (Evening P0 Closeout & Chapter Loop Checkpoint)
**Status:** **10/10 P0 Completion Gates PASS | Preflight Ready for Final Packaged Golden Run**

---

## 1. System Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TWO ABSOLUTE STATE AUTHORITIES                            │
├────────────────────────────────────────────┬───────────────────────────────────────────┤
│    QUILLSCRIPT NARRATIVE AUTHORITY         │       TURN-BASED JRPG STATE AUTHORITY     │
│       (UMelodiaNarrativeSubsystem)         │       (BP_JRPGSaveGame & Combat Core)     │
│  - Branching Dialogue & Cutscenes          │  - Party Stats, HP/MP Calculations        │
│  - Quest Flag Progression                  │  - Turn Queue & Action Resolution         │
│  - 7-Verb Notification Dispatch            │  - Inventory & Key Item Tracking          │
│  - Exactly-Once Reward Delivery            │  - Canonical Save/Load Persistence        │
└─────────────────────┬──────────────────────┴─────────────────────┬─────────────────────┘
                      │                                            │
                      ▼                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FOUR CONVERGED PILLARS                                 │
├──────────────────────┬──────────────────────┬────────────────────┬─────────────────────┤
│ 1. RHYTHM COMBAT     │ 2. WARDROBE SYSTEM   │ 3. MUSIC AS KEY    │ 4. SINGLE-WRITER UI │
│ (Harmonix Overlay)   │ (Traversal Provider) │ (Resonant World)   │ (UI Bridge)         │
│                      │                      │                    │                     │
│ - Rides on JRPG cmd  │ - Mesh visual swap   │ - Stepping nodes   │ - Sole HUD writer   │
│ - Note accuracy grade│ - Traversal provider │ - Resonant phrases │ - Zero race conds   │
│ - Damage multiplier  │ - Glide / Swim / Dash│ - Unlocks routes   │ - Clean transitions │
│ - MPC Palette pulse  │ - State persistence  │ - Emits 7-verbs    │ - No widget leaks   │
└──────────────────────┴──────────────────────┴────────────────────┴─────────────────────┘
```

---

## 2. Reusable Chapter Gameplay Pipeline

Every single chapter in Melodia executes the standardized 6-phase gameplay loop:

1. **Phase 1: Narrative Initiation & Sanctuary Departure** (`L_MelusinaMorning` -> QuillScript NPC dialogue -> quest started flag -> departure gate opens).
2. **Phase 2: Overworld Traversal & Music-as-Key Route Unlock** (`LV_SeaAbove_Prototype` -> traversal & Starskiff navigation -> `APCGHeroMusicGraphHost` harmonic phrase match -> route barrier cleared).
3. **Phase 3: Turn-Based JRPG Combat with Rhythm Command Timing** (`L_KaleidoNave` -> single-writer HUD -> command selection -> Rhythm Highway accuracy grading -> scaled damage applied to boss).
4. **Phase 4: Battle Resolution & Idempotent Reward Distribution** (Boss defeat -> narrative callback -> idempotent reward delivery -> wardrobe unlock).
5. **Phase 5: Traversal Upgrade & World Progression** (Equip new outfit -> `Glide` capability activated -> traverse chasm to reach chapter climax gateway).
6. **Phase 6: Canonical Checkpoint & Seamless Chapter Transition** (Save full player state to `BP_JRPGSaveGame` slot -> seamless transition to next chapter).

---

## 3. Subsystem Health & Test Validation

- **Automated Tests:** 524 / 524 Passing (GMM Python simulations, P0 integration, ECHO contracts, Melodia MCP regression, release hygiene).
- **Completion Gates:** 10 / 10 Passing in `Saved/gate_ledger.json`.
- **Evening Plan:** [Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md](Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md).
