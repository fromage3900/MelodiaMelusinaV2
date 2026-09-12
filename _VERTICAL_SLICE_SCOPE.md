# Active Vertical Slice Scope & Universal Chapter Gameplay Loop

**Canonical Scope Document**
**Last Updated:** 2026-09-08
**Current status:** **8/8 active P0 gates PASS** in `Docs/P0_TASK_LEDGER.json`. First Dream music → wardrobe → Glide → portal is live-proven. Long-chain persistence / repeat-load / packaged golden-run certification remains open (Issue #51).
**Authorities:** [`AGENT_START_HERE.md`](AGENT_START_HERE.md), [`CURRENT_STATE.md`](CURRENT_STATE.md), [`MELODIA_TECHNICAL_VERTICAL_SLICE.md`](MELODIA_TECHNICAL_VERTICAL_SLICE.md)

> The 10-row completion-gate matrix below is **historical evidence vocabulary** from the 2026-09-01 closeout. It is not a second current gate count and it is not a claim that Issue #51 is closed.

---

## 1. Product Goal & The Paradigm Shift

Melodia delivers a focused, highly polished **Rhythm-JRPG vertical slice ("First Dream")** and an extensible, reusable architecture for later chapters. The design blends the intimate narrative rhythm of *OMORI*, the musical world-unlocking of *The Legend of Zelda: Ocarina of Time*, and the high-fidelity fashion and traversal presentation of *Infinity Nikki*.

### The Two Absolute Authorities
1. **QuillScript (`UMelodiaNarrativeSubsystem`)**: Absolute authority on branching dialogue, cutscene flow, quest flags, and 7-verb notifications.
2. **TurnBased JRPG Template (`BP_JRPGSaveGame` & Combat Subsystem)**: Absolute authority on combat turn queue, damage calculation, party stats, inventory, and canonical game state persistence.

### The Four Converged Pillars
1. **Rhythm Combat Layer**: Harmonix rhythm timing rides on top of JRPG command execution (Attack / Skill / Item / Flee). Note accuracy grades (`Poor: 0.35`, `Good: 1.0`, `Great: 1.2`, `Perfect: 1.5`) scale damage output and pulse material parameter collections (`MPC_Melodia_Palette`).
2. **Wardrobe System**: Outfits provide visual customization and implement `IMelodiaTraversalCapabilityProvider` to grant physical world traversal capabilities (Glide, Swim, Dash), persisted via `UMelodiaWardrobeSubsystem`.
3. **Music as Key (World Puzzle)**: Environmental barriers respond to played musical phrases (`APCGHeroMusicGraphHost` / Piano node stepping), dispatching narrative notifications to unlock physical routes.
4. **Single-Writer UI Bridge**: Strict UI hierarchy where every surface has exactly one designated writer (`UMelodiaUIBridgeSubsystem`), eliminating race conditions and dual-widget leaks.

---

## 2. First Dream integration loop

The six-phase route below is the proven **First Dream integration song**. Later chapters may use different shapes as long as they keep the same authorities, IDs, persistence rules, and evidence labels. It is **not** a mandatory script for every future chapter.

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        FIRST DREAM FULL-STACK INTEGRATION LOOP                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
[ Phase 1: Narrative Initiation & Sanctuary Departure ]
   ├── QuillScript dialogue node with chapter key NPC
   ├── Authoring of active quest flag (`quest.<chapter_id>.start`)
   └── Authoring of Sanctuary departure gate unlock
   │
   ▼
[ Phase 2: Overworld Traversal & Music-as-Key Route Unlock ]
   ├── Traversal across overworld using active Wardrobe traversal capabilities
   ├── Discovery of environmental musical puzzle / route barrier
   ├── Player steps on musical nodes / plays resonant melody
   └── Route / portal barrier unlocks via 7-verb narrative notification
   │
   ▼
[ Phase 3: Turn-Based JRPG Combat with Rhythm Command Timing ]
   ├── Seamless encounter transition to battle arena
   ├── Single HUD writer (`UMelodiaUIBridgeSubsystem`) displays command menu
   ├── Player selects action (Attack / Resonance Skill / Item / Flee)
   ├── Harmonix Rhythm Highway engages for real-key timed inputs
   └── Grade multiplier scales stock JRPG damage calculation
   │
   ▼
[ Phase 4: Battle Resolution & Idempotent Reward Distribution ]
   ├── Terminal combat outcome reached (Victory / Defeat / Flee / Timeout)
   ├── QuillScript narrative resumes once
   └── Idempotent reward distribution via Intent-ID (Wardrobe unlock, Stat increase, Item)
   │
   ▼
[ Phase 5: Traversal Upgrade & World Progression ]
   ├── Player equips newly acquired wardrobe piece
   ├── `UMelodiaWardrobeSubsystem` grants new traversal capability (e.g., Glide / Dash)
   └── Player accesses previously unreachable chapter climax portal / landmark
   │
   ▼
[ Phase 6: Canonical Checkpoint & Seamless Chapter Transition ]
   ├── State serialized to `BP_JRPGSaveGame` slot
   ├── Verified round-trip persistence (Party, Stats, Flags, Wardrobe, Inventory)
   └── Level streaming / transition to next Chapter map
```

---

## 3. P0 Vertical Slice ("First Dream") Scope Definition

### Canonical Maps & Route
1. **`L_MelusinaMorning` (`/Game/Melodia/Levels/Opening/L_MelusinaMorning`)**: Sanctuary opening, QuillScript dialogue with Sir Melodious, departure gate.
2. **`LV_SeaAbove_Prototype` (`/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype`)**: Overworld journey, Starskiff docking & navigation, musical stepping puzzle (`APCGHeroMusicGraphHost`).
3. **`L_KaleidoNave` (`/Game/EnvSandbox/Environments/L_KaleidoNave`)**: Gothic sci-fi cathedral battle arena, `BP_MelodySlime_Boss` encounter, Rhythm Highway execution.
4. **`MelodiaMainMenu` (`/Game/Melodia/Maps/MelodiaMainMenu`)**: Title screen & canonical save slot loading.

---

## 4. Historical completion-gate taxonomy (10 IDs)

Recorded during the 2026-09-01 closeout. Current tracked authority is the **8 active P0 gates** in `Docs/P0_TASK_LEDGER.json`. These 10 IDs remain useful vocabulary; they are not a second live scoreboard.

| Gate | Target System | Acceptance Criteria | Recorded status |
|---|---|---|:---:|
| `runtime` | Full Loop PIE | Real-input playthrough from sanctuary through battle and checkpoint | historical PASS |
| `save_load` | Persistence | Slot serialization and roundtrip restore via `BP_JRPGSaveGame` | historical PASS |
| `repeat_consume` | Narrative Queue | Exactly-once consumption of narrative notifications and rewards | historical PASS |
| `package_launch` | Standalone Executable | Clean boot and initialization outside Unreal Editor | historical PASS |
| `rhythm_owner` | Rhythm Layer | Rhythm highway scales JRPG command execution without taking state ownership | **active PASS** |
| `hud_single_writer` | UI Hierarchy | `UMelodiaUIBridgeSubsystem` is the sole designated writer for HUD surfaces | **active PASS** |
| `wardrobe_equip_roundtrip` | Wardrobe Subsystem | Mesh swap and equipped outfit state persist across save/reload | **active PASS** |
| `rhythm_grade_to_result` | Combat Scaling | Note accuracy grades scale JRPG damage calculations | **active PASS** |
| `music_world_key` | Resonant World | Musical phrase stepping unlocks route barriers via narrative subsystem | **active PASS** |
| `wardrobe_gameplay_hook` | Traversal Provider | Equipping outfit grants physical world traversal capabilities (`Glide`) | **active PASS** |

Also passing as active gates, not in this 10-row list: `static_gates`, `battle_integration_map`.

Still open beyond this matrix: Issue #51 long-chain persistence / repeat-load / packaged golden-run certification.

---

## 5. Evening P0 Closeout sequence (historical)

This sequence is retained for audit. Do not read the future-tense lines as work that has not started.

1. **Test Preflight (Completed):** 524/524 automated tests recorded across GMM simulations, P0 integration, ECHO contracts, MCP regression, and release hygiene for that captured revision.
2. **Clean Win64 Standalone Packaging:** `BuildCookRun` covering canonical maps (`L_MelusinaMorning`, `L_KaleidoNave`, `LV_SeaAbove_Prototype`, `MelodiaMainMenu`).
3. **Packaged Binary Launch Verification:** `Saved/Packages/P0_Closeout_20260901/Windows/BS_GodFile.exe` boot check.
4. **Packaged Golden Run Execution:** `specs/p0/core_p0_dream_golden_run.v1.json` through the 6-phase chapter loop.
5. **Evidence Ledger Freezing:** reports under `Saved/Audit/` and `Saved/gate_ledger.json` (local evidence; may be absent from a fresh clone).
