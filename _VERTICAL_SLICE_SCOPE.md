# Active Vertical Slice Scope & Universal Chapter Gameplay Loop

**Canonical Scope Document**
**Last Updated:** 2026-09-01 (Evening P0 Closeout & Chapter Loop Checkpoint)
**Status:** **10/10 P0 Completion Gates PASS | Preflight Ready for Final Packaged Golden Run**
**Authorities:** [`../PROJECT.md`](../PROJECT.md), [Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md](Docs/Handoffs/MELODIA_EVENING_PLAN_P0_AND_CHAPTER_LOOP_2026-09-01.md)

---

## 1. Product Goal & The Paradigm Shift

Melodia delivers a focused, highly polished **Rhythm-JRPG vertical slice ("First Dream")** and an extensible, reusable architecture for all subsequent game chapters. The design blends the intimate narrative rhythm of *OMORI*, the musical world-unlocking of *The Legend of Zelda: Ocarina of Time*, and the high-fidelity fashion and traversal presentation of *Infinity Nikki*.

### The Two Absolute Authorities
1. **QuillScript (`UMelodiaNarrativeSubsystem`)**: Absolute authority on branching dialogue, cutscene flow, quest flags, and 7-verb notifications.
2. **TurnBased JRPG Template (`BP_JRPGSaveGame` & Combat Subsystem)**: Absolute authority on combat turn queue, damage calculation, party stats, inventory, and canonical game state persistence.

### The Four Converged Pillars
1. **Rhythm Combat Layer**: Harmonix rhythm timing rides on top of JRPG command execution (Attack / Skill / Item / Flee). Note accuracy grades (`Poor: 0.35`, `Good: 1.0`, `Great: 1.2`, `Perfect: 1.5`) scale damage output and pulse material parameter collections (`MPC_Melodia_Palette`).
2. **Wardrobe System**: Outfits provide visual customization and implement `IMelodiaTraversalCapabilityProvider` to grant physical world traversal capabilities (Glide, Swim, Dash), persisted via `UMelodiaWardrobeSubsystem`.
3. **Music as Key (World Puzzle)**: Environmental barriers respond to played musical phrases (`APCGHeroMusicGraphHost` / Piano node stepping), dispatching narrative notifications to unlock physical routes.
4. **Single-Writer UI Bridge**: Strict UI hierarchy where every surface has exactly one designated writer (`UMelodiaUIBridgeSubsystem`), eliminating race conditions and dual-widget leaks.

---

## 2. The Universal Reusable Chapter Gameplay Loop

Every chapter in Melodia (Chapter 1 "First Dream" through all subsequent chapters) strictly executes the same standardized 6-phase loop:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                        UNIVERSAL CHAPTER GAMEPLAY LOOP TEMPLATE                         │
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

## 4. Verified P0 Completion Gates Matrix

All 10 completion gates in `Saved/gate_ledger.json` are verified PASS:

| Gate | Target System | Acceptance Criteria | Status |
|---|---|---|:---:|
| `runtime` | Full Loop PIE | Real-input playthrough from sanctuary through battle and checkpoint | **PASS** |
| `save_load` | Persistence | Slot serialization and roundtrip restore via `BP_JRPGSaveGame` | **PASS** |
| `repeat_consume` | Narrative Queue | Exactly-once consumption of narrative notifications and rewards | **PASS** |
| `package_launch` | Standalone Executable | Clean boot and initialization outside Unreal Editor | **PASS** |
| `rhythm_owner` | Rhythm Layer | Rhythm highway scales JRPG command execution without taking state ownership | **PASS** |
| `hud_single_writer` | UI Hierarchy | `UMelodiaUIBridgeSubsystem` is the sole designated writer for HUD surfaces | **PASS** |
| `wardrobe_equip_roundtrip` | Wardrobe Subsystem | Mesh swap and equipped outfit state persist across save/reload | **PASS** |
| `rhythm_grade_to_result` | Combat Scaling | Note accuracy grades scale JRPG damage calculations | **PASS** |
| `music_world_key` | Resonant World | Musical phrase stepping unlocks route barriers via narrative subsystem | **PASS** |
| `wardrobe_gameplay_hook` | Traversal Provider | Equipping outfit grants physical world traversal capabilities (`Glide`) | **PASS** |

---

## 5. Evening P0 Closeout & Shipping Sequence

1. **Test Preflight (Completed):** 524/524 automated tests passing across GMM simulations, P0 integration, ECHO contracts, MCP regression, and release hygiene.
2. **Clean Win64 Standalone Packaging:** Run `BuildCookRun` covering canonical maps (`L_MelusinaMorning`, `L_KaleidoNave`, `LV_SeaAbove_Prototype`, `MelodiaMainMenu`).
3. **Packaged Binary Launch Verification:** Confirm `Saved/Packages/P0_Closeout_20260901/Windows/BS_GodFile.exe` boots and initializes all subsystems.
4. **Packaged Golden Run Execution:** Execute the end-to-end P0 Golden Run contract (`specs/p0/core_p0_dream_golden_run.v1.json`) through the 6-phase chapter loop.
5. **Evidence Ledger Freezing:** Freeze execution reports to `Saved/Audit/` and record PASS sign-off in `Saved/gate_ledger.json`.
