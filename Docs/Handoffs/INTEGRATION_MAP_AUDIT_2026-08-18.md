# Session Handoff — 2026-08-18 (Integration Map Audit + Editor Recovery)

**Editor status:** Monolith HTTP server down after save crash. UnrealEditor.exe PID 34452 still alive but port 9316 in TIME_WAIT. Requires editor restart.
**Previous session:** PID 16120 (see `SESSION_HANDOFF_2026-08-18.md`) — all four completion gates PASS, MelodiaLocomotionAnimInstance crash fixed, battle encounter triggers but infinite loops in `BP_BattleController::Show`.

---

## Verified: MelodiaIntegrationMap is the correct integration proof map

**Do not use `L_KaleidoNave` for the integration proof.** The P0 golden run uses `MelodiaIntegrationMap` exclusively. This map is already fully stocked with stock JRPG template infrastructure.

### Actor inventory (verified live via Monolith `editor_query run_python`)

| Actor Type | Count | Key Instance | Location |
|---|---|---|---|
| PlayerStart | 1 | PlayerStart | ~~(-6247, 200, 112)~~ → **(-332, 300, 112)** |
| BP_InteractionBattle | 4 | BP_InteractionBattle_2 | (-332, 156, 112) |
| | | BP_InteractionBattle2_2 | (-3570, -1120, 20) |
| | | BP_InteractionBattle3 | (-3570, 1500, 20) |
| | | BP_InteractionBattle4_2 | (-5050, 1470, 80) |
| BP_BattleController | 1 | BP_BattleController_2 | (0, 0, 0) |
| BP_PlayerSpawnLocation | 18 | various | — |
| BP_EnemySpawnLocation | 14 | various | — |
| DirectionalLight | 1 | LightSource | (-3050, -2400, 570) |
| SkyLight | 1 | SkyLight_1 | (-3129, -2231, 505) |
| **Total** | **149** | | |

**All 4 InteractionBattles carry tag `melodia_smoke_encounter`.**

### WorldSettings
- **GameMode Override:** `/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode.BP_MelodiaJRPGGameMode_C` ✅
- **Map:** `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` ✅

### What I changed (unsaved due to crash)
- Moved PlayerStart from (-6247, 200, 112) to (-332, 300, 112) — now spawns adjacent to BP_InteractionBattle_2 for fast PIE testing.
- **This move is NOT on disk.** The `.umap` file still has the old PlayerStart location. After editor restart, re-apply this move and save.

---

## PIE behavior (verified before crash)

### Player character
- PIE spawns `BP_MelusinaJRPGCharacter_C_1` (label: `BP_MelusinaJRPGCharacter1`)
- Confirmed via `pie_get_object_properties {class_name: "Character"}`
- Initial location when spawned from original PlayerStart: `(-5910, 31, 110)`

### Teleport + interaction attempts
- Teleported character to interaction battle locations using `pie_call_function K2_SetActorLocation`
- `GetOverlappingActors` returned **empty** at both locations — interaction battles do NOT use simple collision overlap
- `pie_inject_input_action` failed because the exact `UInputAction` asset path for "Interact" could not be resolved
- The interaction battle likely requires either:
  1. A line-trace/interaction-detector component on the player
  2. A specific input action binding that must be injected by full `/Game/...` path
  3. Direct `StartBattle` call on the interaction actor (see previous handoff — this worked)

### Confirmed working path (from previous handoff)
```
pie_call_function → BP_InteractionBattle_2 → "StartBattle"
```
This successfully:
- ✅ Triggered battle
- ✅ Pushed input context to `EMelodiaInputContext::Battle`
- ✅ Created `BP_BattleUI_C_0` and added to viewport
- ❌ **Then infinite loop in `BP_BattleController::Show`**

---

## The save crash (reproduced)

**Trigger:** `save_packages` on `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`
**Stack:** CoreUObject `UPackage::SavePackage` → `FMonolithEditorActions::HandleSavePackages` → `FMonolithHttpServer::HandlePostMcp`
**Result:** Editor process survives but Monolith HTTP server dies (port 9316 → TIME_WAIT)

**This is the same crash class as 2026-08-08 and 2026-08-14.** Do NOT attempt to save the integration map through Monolith until this is root-caused. Use the editor's native Ctrl+S or save through UE's file menu instead.

### Recovery procedure
1. Kill the surviving UnrealEditor.exe process (PID 34452)
2. Relaunch editor from the `.uproject`
3. Re-load `MelodiaIntegrationMap`
4. Re-apply the PlayerStart move to (-332, 300, 112)
5. **Save via native UE file menu, NOT Monolith `save_packages`**

---

## Next work (highest priority)

1. **Restart editor** and verify Monolith on 9316
2. **Fix `BP_BattleController::Show` infinite loop** — the only gameplay blocker
   - Export EventGraph to T3D
   - Find the Branch node in `Show` call stack missing terminating condition
   - Likely: `SetReadyUnits` → `OnUnitsTurnStarted` → `SetReadyUnits` recursion
3. **Re-run battle encounter** via `pie_call_function` + `StartBattle` and verify no loop
4. **Record `battle_encounter` gate pass** in `Saved/gate_ledger.json`

---

## Tooling notes for other agents

### ✅ Working Monolith commands
```bash
# Load the integration map
editor_query load_level {"path": "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"}

# Get actor count and key actors
editor_query run_python {"command": "import unreal; actors=list(unreal.EditorLevelLibrary.get_all_level_actors()); print(len(actors))"}

# Start/stop PIE
editor_query start_pie
editor_query stop_pie

# Call functions on PIE actors
editor_query pie_call_function {"object_name": "BP_MelusinaJRPGCharacter_C_1", "function": "K2_SetActorLocation", "args": [{"X": -332, "Y": 300, "Z": 112}]}

# Get object properties
editor_query pie_get_object_properties {"class_name": "Character", "properties": ["ActorLocation"]}
```

### ❌ Broken / unreliable
- `save_packages` on `.umap` files — crashes Monolith HTTP server
- `mesh_query spawn_blueprint_actor` — returns success but actors do not persist (no auto-save)
- `pie_inject_input_action` by action name alone — requires full `/Game/...` UInputAction asset path
- `editor_query run_python` accessing PIE world via `unreal.Engine` or `get_editor_world()` — returns None in PIE context

### Finding PIE actor names
- Use `class_name` with a broad class like `"Character"` in `pie_get_object_properties`
- PIE actors get `_C_1`, `_C_0` suffixes but `object_name` matching is exact
- `actor_label` in PIE is often the same as editor label minus numbering

---

*Session: 2026-08-18 | Editor PID: 34452 (Monolith dead) | Monolith: 127.0.0.1:9316 (TIME_WAIT)*
