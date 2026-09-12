# Battle Encounter Debug — Root Cause Found (2026-08-18)

## Status
Monolith HTTP server unresponsive after PIE session. Editor process alive (PID 42048) but MCP calls fail.
`monolith_proxy.exe` (PID 5292) stuck in SYN_SENT to 127.0.0.1:9316.

**Requires editor restart before any further live work.**

---

## 🎯 Root Cause: InteractionBattles are UNCONFIGURED

The battle starts but **no units spawn** because the `BP_InteractionBattle` instances in `MelodiaIntegrationMap` have **empty enemy lists and no unit configuration**.

### Evidence

**CDO inspection via `blueprint_query get_cdo_properties`:**

| Property | CDO Default | Instance (assumed) |
|---|---|---|
| `enemyList` | `[]` (empty) | Likely empty |
| `offLevelBattleData.BattleLevelName` | `"None"` | Likely `"None"` |
| `battleController` | `None` | May auto-find |
| `playerUnits` | `[]` | Empty until spawned |
| `enemyUnits` | `[]` | Empty until spawned |
| `playerUnitLevels` | `{}` | Empty |
| `playerSpawnLocations` | `[]` | 18 in map |
| `enemySpawnLocations` | `[]` | 14 in map |

### PIE Error Pattern (Confirmed)
When `StartBattle` is called:
1. ✅ BattleController spawns
2. ✅ `BP_BattleUI_C_1` created and added to viewport
3. ❌ `BP_UnitBattleDetails` throws **"Accessed None trying to read property `unit`"** (×24+)
4. ❌ `BP_PlayerUnitBase` throws **"Accessed None trying to read property `currentTarget`"**
5. ❌ `BP_JRPGFunctionLibrary` throws **"Accessed None trying to read property `actor`"** in `DisableActor`

**No infinite loop observed in this session.** The previous session's "infinite loop in `BP_BattleController::Show`" may have been a downstream symptom of the empty party, or may require specific timing to reproduce.

---

## 📋 Map State (Verified Live)

| | |
|---|---|
| **Map** | `MelodiaIntegrationMap` (149 actors) |
| **GameMode** | `BP_MelodiaJRPGGameMode` ✅ |
| **PlayerStart** | (-332, 300, 112) — next to `BP_InteractionBattle_2` ⚠️ **Saved?** Verify after restart |
| **InteractionBattles** | 4, all tagged `melodia_smoke_encounter` |
| **BP_BattleController** | 1 at origin |
| **PlayerSpawnLocations** | 18 |
| **EnemySpawnLocations** | 14 |

---

## 🔧 Fix Path (in order)

### Option A: Configure existing InteractionBattles (fastest)

Each `BP_InteractionBattle` instance needs:
1. **`enemyList`** — array of enemy unit classes to spawn (e.g., `BP_EnemyUnitBase` subclass)
2. **`offLevelBattleData.BattleLevelName`** — either `"None"` for on-level battle, or a specific battle level name
3. **`battleController`** — reference to the `BP_BattleController_2` in the level (may auto-find)
4. **`playerUnitLevels`** — map of player unit class → level (or empty for default)

**Verification:** After configuring, start PIE and call `StartBattle`. Check logs for:
- `SpawnEnemyUnits` completing
- `SpawnPlayerUnits` completing  
- `InitUnits` completing
- **No** "Accessed None" for `unit` or `currentTarget`

### Option B: Copy working battles from stock template reference

Check `CompatibilityLabs/TurnBasedJRPGUE58` or `_ThirdParty/TurnBasedJRPGTemplate` for a map with properly configured `BP_InteractionBattle` instances. Copy the configured instances (not the whole map) into `MelodiaIntegrationMap`.

**Trap:** `mesh_query spawn_blueprint_actor` returns success but actors don't persist without save. Use `EditorLevelLibrary.spawn_actor_from_class` + `set_actor_label` + **native UE Ctrl+S** (Monolith `save_packages` crashes on `.umap`).

### Option C: Use `BP_MelodiaEncounter_FirstDream` or `BP_MelodiaEncounter_Base`

The Melodia integration has its own encounter base classes:
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaEncounter_Base`
- `/Game/MelodiaIntegration/Blueprints/BP_MelodiaEncounter_FirstDream`

These may be the intended integration path rather than stock `BP_InteractionBattle`. Check if these are already wired to the narrative subsystem and if they handle unit spawning through the Melodia bridge.

---

## 🧪 Verified Working Commands (for next session)

```bash
# Load map
editor_query load_level {"path": "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"}

# Start PIE
editor_query start_pie

# Find interaction battle in PIE
editor_query pie_get_object_properties {"class_name": "BP_InteractionBattle_C", "properties": ["ActorLabel"]}
# Returns: BP_InteractionBattle2_2 (label: BP_InteractionBattle2)

# Trigger battle
editor_query pie_call_function {"object_name": "BP_InteractionBattle2_2", "function": "StartBattle"}

# Check PIE logs
editor_query search_logs {"text": "Accessed None", "category": "PIE"}
```

---

## ⚠️ Known Monolith Issues

1. **`save_packages` on `.umap` crashes Monolith HTTP server** — always use native UE Ctrl+S
2. **Monolith becomes unresponsive after PIE + certain operations** — may need editor restart
3. **`pie_get_object_properties` with `class_name` returns FIRST match only** — use specific `object_name` when possible
4. **`editor_query run_python` returning `None` for `get_editor_world()` in PIE** — expected, use PIE-specific endpoints

---

## 📝 Files Changed This Session

- `Docs/Handoffs/INTEGRATION_MAP_AUDIT_2026-08-18.md` (this file)
- PlayerStart moved to (-332, 300, 112) in `MelodiaIntegrationMap` — **verify saved after restart**

---

## Next Work

1. **Restart editor** (Monolith is dead)
2. **Verify PlayerStart move persisted**
3. **Configure one InteractionBattle** with enemy data
4. **Re-test PIE battle**
5. **Record `battle_encounter` gate result** in `Saved/gate_ledger.json`

*Session: 2026-08-18 | Editor PID: 42048 (Monolith dead) | monolith_proxy: 5292 (SYN_SENT)*
