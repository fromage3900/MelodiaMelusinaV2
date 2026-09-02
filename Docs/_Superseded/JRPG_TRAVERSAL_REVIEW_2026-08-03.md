# JRPG Template & Traversal Systems Review — 2026-08-03

**Reviewer:** BS_GodFile Gameplay Systems Analyst  
**Editor state:** Successful closed-editor native build, Monolith :9316 live  
**Scope:** Battle loop wiring, save/load chain, traversal state, off-level battle path, next-phase readiness

---

## 1. Battle Loop Current State

### Narrative binding status

The stock JRPG battle controller (`BP_BattleController`) and the Melodia narrative subsystem are **NOT bound together in content**.

- **`OnJRPGBattleEnded`** (declared on `UMelodiaExternalJRPGBridgeSubsystem` in C++) — 0 content references found via `project_query search`. The delegate exists but nothing in any Blueprint binds to it.
- **`OnBattleCompleted`** — 0 content references. No content-level dispatch wires battle results back to the narrative subsystem.
- **`MELUSINA_LOOP_BATTLE_COMPLETED` / `MELUSINA_LOOP_QUILL_RESTORE` / `MELUSINA_LOOP_QUILL_NEXT`** — 0 content references. The three required log markers are not emitted from any Blueprint graph in the content index.
- **`NarrativeSubsystem`** — 0 content references. No Blueprint graph calls `GetMelodiaNarrativeSubsystem` or binds to its events.
- **`MelodiaExternalJRPG`** — 0 content references. The bridge subsystem class (`UMelodiaExternalJRPGBridgeSubsystem`) exists in compiled C++ but is not instantiated or called by any content Blueprint.

### What IS wired

- `BP_MelodiaJRPGGameInstance` has **`SyncNarrativeRecordToSave`** and **`RestoreNarrativeRecordFromSave`** calls in its save/load paths — the persistence seam is structurally present.
- `BP_MelodiaJRPGGameInstance` has **`TravelTo`** calls (MelodiaTravelSubsystem) in `ChangeMapForBattle` and `ChangeMapAfterBattle` custom events.
- The stock `BP_OffLevelBattleController` routes `SwitchToExploreMode` ? `RemoveBattle` ? cast to `BP_JRPGGameInstance` ? `ChangeMapAfterBattle` — this is the **stock JRPG pipeline**, not the Melodia bridge.

### Result matrix coverage

| Outcome | State in content |
|---------|-----------------|
| **Victory** | Stock JRPG result screen displayed; no `OnJRPGBattleEnded` dispatch to narrative |
| **Defeat** | Stock defeat dialogue map open (`Open Level` in BP_DefeatDialogue); no narrative recovery path wired |
| **Fled** | Flee is present in stock command UI; no typed flee result routed to narrative |
| **Unavailable** | No unavailable-handling logic wired to the encounter request path |

**Conclusion:** The battle loop diagram from the composition contract (Quill ? encounter ? battle ? typed result ? narrative resume) is **broken at the "typed result ? narrative resume" edge**. The C++ infrastructure exists but every content-level wire is missing.

---

## 2. Save/Load Chain

### Full path broken down

| Step | Asset | State | Comment |
|------|-------|-------|---------|
| **Main Menu ? New Game** | `WBP_MainMenu` / `BP_MelodiaJRPGGameInstance` | **Proven** (static) | `OnNewGameStarted` ? creates save object ? sets defaults ? `SyncNarrativeRecordToSave` ? `SaveGameToSlot` |
| **Slot creation** | `BP_MelodiaJRPGGameInstance` | **Proven** (static) | Slot name, date, map name, narrative record all set |
| **Travel to Melusina Morning** | `BP_MelodiaJRPGGameInstance` | **Partially** | Still uses `Open Level (by Name)` in LoadGame path; `TravelTo` from MelodiaTravelSubsystem available but not used for initial load |
| **Morning ? Dreamstate ? KaleidoNave travel** | GameInstance | **Mixed** | `ChangeMapForBattle` and `ChangeMapAfterBattle` use `TravelTo` ?. Dreamstate ? KaleidoNave travel not confirmed via TravelTo |
| **Save in KaleidoNave** | GameInstance | **Proven** (static) | SaveGame path writes narrative record + all JRPG state |
| **Full PIE exit** | N/A | **Proven** (by test script) | Clean exit confirmed in playtest procedure |
| **Load from Main Menu** | GameInstance | **Blocked** | LoadGame uses `Open Level (by Name)` rather than `TravelTo`; Continue button disabled until gate 4.2 passes |
| **State restore** | GameInstance | **Proven** (static) | `RestoreNarrativeRecordFromSave` called, restores flags/rewards/quests/stats |
| **Harmony stat persistence** | `FMelodiaNarrativeRecord` (v2) | **Proven** (schema) | `SocialStats` map is now a save field (version 2), `MigrateRecord` handles upgrade |

### What is proven vs. blocked

- **Proven (static-only, not runtime):** All node wiring in BP_MelodiaJRPGGameInstance exists — save creation, narrative sync, narrative restore, TravelTo calls. The graph topology is structurally correct.
- **Blocked:** Full process restart round trip has NEVER passed in PIE. Main menu Continue/Load buttons remain intentionally disabled. `Open Level (by Name)` still used in LoadGame path instead of `TravelTo` (which means no allowlist validation, no spawn tag placement on load).
- **Blocked:** Input context system (`PushContext`/`PopContext`) has 0 content bindings — widgets are not pushing contexts on open or popping on close. This means cursor/input mode management is still ad-hoc.
- **Gap:** The `BP_MelodiaJRPGGameInstance` graph has both `Open Level (by Name)` AND `TravelTo` nodes coexisting. The migration is incomplete.

---

## 3. Traversal State

### Travel allowlist

- **DA_MelodiaIntegrationConfig** `TravelLevelIds` confirmed via `get_cdo_properties`:
  - `melodia_integration_map`
  - `/Game/EnvSandbox/Environments/L_KaleidoNave`
- **KaleidoNave IS allowlisted** ?

### PlayerStart tagging

- **"Arrive_FromDreamstate"** search returns **0 results** — no PlayerStart in any level has this tag.
- The wiring checklist (step 2b) requires this tag on one of KaleidoNave's PlayerStarts; it has NOT been applied.
- Only 2 PlayerStarts found in KaleidoNave's external actors (vs. the 4 mentioned in docs).
- **Gap:** Without the tag, `PlacePawnAtSpawn` will log `placed=0` and the engine picks the first PlayerStart arbitrarily. This is one of the causes of spawn-at-world-origin bugs.

### Input context on arrival

- **"PushContext"** — 0 content references. No widget pushes its context.
- **"ClearAllContexts"** — 0 content references. Travel arrival does not clear stale contexts in any Blueprint path.
- `UMelodiaInputContextSubsystem` C++ code has `ClearAllContexts()` called automatically on travel arrival in the C++ layer, but since no contexts are being pushed, the clearing has nothing to clear.
- **Gap:** The entire input context migration (step 3 in wiring checklist) is undone. Every widget that should push `Dialogue`, `Battle`, or `Menu` context is still using ad-hoc `Set Input Mode` / `Show Mouse Cursor` calls.

### TravelTo adoption

- **"TravelTo"** — 0 content references in the indexed project search (stale index likely). However, `BP_MelodiaJRPGGameInstance` graph summary confirms `TravelTo` nodes exist in `ChangeMapForBattle` and `ChangeMapAfterBattle`.
- **"Open Level (by Name)"** — found in 10+ assets including `BP_MelodiaJRPGGameInstance`, `BP_JRPGGameInstance`, `BP_MainMenu`, `BP_MelodiaTeleporterVolume`, `WBP_ComicOrrery`, `BP_EscapeToLevel`. The migration from `Open Level` to `TravelTo` is not complete.
- **"MelodiaMapTransition"** — 0 results. The `MelodiaMapTransitionComponent` has not been placed on any trigger actor.

---

## 4. Off-Level Battle Path

### Current architecture

- **BP_OffLevelBattle** (`/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattle`): Standard stock JRPG off-level battle actor. BeginPlay ? loads battle data from `BP_OffLevelBattleController` ? camera fade ? delay ? runs battle.
- **BP_OffLevelBattleController** (`/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattleController`): Has `SwitchToExploreMode` ? fades audio, fades camera ? casts to `BP_JRPGGameInstance` ? calls `ChangeMapAfterBattle`.

### Allowlist compatibility

- The off-level battle path does NOT use `TravelTo` to return to the exploration map — it uses the legacy `BP_JRPGGameInstance.ChangeMapAfterBattle` chain which ultimately calls `Open Level (by Name)` (found in the GameInstance graph).
- The exploration map name saved at battle start is passed as a string to Open Level, bypassing the TravelTo allowlist entirely.
- **Result:** Off-level battle return does NOT respect the travel allowlist. If the exploration map were removed from the allowlist, off-level battle would still return there.
- **BP_InteractionBattle** instance exists in KaleidoNave (external actor path confirms a placed instance). This is the stock encounter trigger — but it triggers the stock battle flow, not the Melodia bridge.

### Path to Melodia bridge

The C++ `UMelodiaExternalJRPGBridgeSubsystem` provides `StartTaggedJRPGBattle(FName EncounterId)` and `OnJRPGBattleEnded` — but nothing calls these from content. The planned pipeline would be:
1. `BP_InteractionBattle` ? trigger ? `StartTaggedJRPGBattle("melodia_smoke_encounter")`
2. Battle completes ? `OnJRPGBattleEnded` fires with typed result
3. Narrative subsystem receives result ? resumes Quill ? produces `MELUSINA_LOOP_*` markers

Step 1 is not wired. Steps 2-3 are not wired. The encounter `melodia_smoke_encounter` is in the config allowlist but has 0 content references.

---

## 5. Ready-for-Next-Phase Assessment

### Battle/travel work remaining (priority order)

| # | Work item | Where | Blocked by |
|---|-----------|-------|------------|
| **P0** | Bind `OnJRPGBattleEnded` delegate to narrative resume | BP_BattleController / BP_MelodiaJRPGGameInstance | Nothing — C++ exists, just needs Blueprint wiring |
| **P0** | Wire `StartTaggedJRPGBattle` into `BP_InteractionBattle` trigger | BP_InteractionBattle | Nothing — bridge C++ exists |
| **P0** | Wire `PushContext`/`PopContext` on all UI widgets (Dialogue, Battle, Menu) | 6+ widgets | Nothing — C++ exists, documented in wiring checklist step 3 |
| **P1** | Replace all `Open Level (by Name)` with `TravelTo` | BP_MelodiaJRPGGameInstance (LoadGame), BP_MainMenu, BP_MelodiaTeleporterVolume, WBP_ComicOrrery, BP_EscapeToLevel | Nothing — TravelSubsystem built and working |
| **P1** | Tag KaleidoNave PlayerStart with `Arrive_FromDreamstate` | L_KaleidoNave map | Nothing — editor work |
| **P1** | Wire result matrix (victory/defeat/fled/unavailable) ? typed narrative dispatch | BP_OffLevelBattleController, BP_BattleController | P0 battle wiring must land first |
| **P2** | Place `MelodiaMapTransitionComponent` on transition triggers | KaleidoNave, Dreamstate | Nothing — component exists in C++ |
| **P2** | PIE-walk save round trip with full process restart | All systems | P0 input context + P1 LoadGame TravelTo must land first |
| **P2** | Enable Main Menu Continue/Load buttons | WBP_MainMenu | P2 save round trip must pass |

### Unblocked items ready now

1. **PlayerStart tagging** — purely editor work, no code dependency, zero risk.
2. **`TravelTo` replacement in LoadGame** — the TravelSubsystem is compiled and working; the node exists in the BP_MelodiaJRPGGameInstance palette. This is a one-node substitution.
3. **`StartTaggedJRPGBattle` wiring** — the bridge subsystem exists; `BP_InteractionBattle` exists in KaleidoNave; the encounter ID `melodia_smoke_encounter` is already allowlisted.

### Items requiring a closed-editor build

- None — all C++ is already compiled and green. The remaining work is Blueprint wiring and editor tagging only.

---

## Key Asset Paths Referenced

| Asset | Path | Status |
|-------|------|--------|
| BP_BattleController | `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_BattleController` | Stock template, no Melodia wires |
| BP_MelodiaJRPGGameInstance | `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance` | Has TravelTo + Narrative sync, still uses Open Level |
| DA_MelodiaIntegrationConfig | `/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig` | KaleidoNave allowlisted ?, melodia_smoke_encounter allowlisted ? |
| BP_OffLevelBattle | `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattle` | Stock, no Melodia bridge |
| BP_OffLevelBattleController | `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_OffLevelBattleController` | Stock, uses ChangeMapAfterBattle (Open Level) |
| BP_InteractionBattle | `/Game/TurnBasedJRPGTemplate/Blueprints/Battle/BP_InteractionBattle` | Instance exists in KaleidoNave, not wired to bridge |
| BP_MelodiaJRPGGameMode | `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode` | Exists ? |
| UMelodiaTravelSubsystem | `Source/BS_GodFile/MelodiaIntegration/MelodiaTravelSubsystem.h` | Compiled, TravelTo ready |
| UMelodiaInputContextSubsystem | `Source/BS_GodFile/MelodiaIntegration/MelodiaInputContextSubsystem.h` | Compiled, 0 content bindings |
| UMelodiaExternalJRPGBridgeSubsystem | `Source/BS_GodFile/MelodiaIntegration/MelodiaExternalJRPGBridgeSubsystem.h` | Compiled, 0 content references |

---

## Summary Assessment

The C++ foundation for the battle loop, traversal, and save/load is **compiled and structurally correct** — every subsystem class, delegate, and method exists and builds without errors. The gap is entirely at the **Blueprint wiring layer**: `OnJRPGBattleEnded` is unbound, `PushContext`/`PopContext` is unwired, `TravelTo` coexists with `Open Level` rather than replacing it, and PlayerStarts are untagged. Of the 12 foundation gates listed in `_VERTICAL_SLICE_SCOPE.md`, **only 2 are passing (x-marked)**; the remaining 10 are blocked by content wiring, not engine code. The highest-value single action to unblock the playtest is binding `BP_InteractionBattle` ? `StartTaggedJRPGBattle("melodia_smoke_encounter")` and routing `OnJRPGBattleEnded` ? Quill resume — that closes the entire narrative loop.
