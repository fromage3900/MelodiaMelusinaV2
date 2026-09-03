# Echo Battle Test — MelodiaIntegrationMap

**Gate ID:** `battle_integration_map`  
**Purpose:** Verify the JRPG battle system functions end-to-end in the MelodiaIntegrationMap with the stock encounter fixture.  
**Map:** `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`  
**Date:** 2026-08-18

---

## Preconditions

1. Editor running with Monolith reachable on `127.0.0.1:9316`
2. `MelodiaIntegrationMap.umap` exists on disk
3. `BP_MelodiaJRPGGameMode` and `BP_MelodiaJRPGGameInstance` compile clean
4. `DA_MelodiaIntegrationConfig` allowlist includes the stock encounter ID
5. `BP_MelodiaEncounter_FirstDream` is placed in the map or spawnable

---

## Test Sequence

### Phase 1: Static verification (offline-safe)

```bash
python Tools/test_melodia_mcp.py
python deploy/melodia_mcp_server.py  # verify tools list
```

Expected: 13/13 tests pass.

### Phase 2: PIE smoke — Integration Map Load

```bash
python Tools/pie_smoke_runner.py \
    --map "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap" \
    --duration 15 \
    --output "Saved/Echo/BattleIntegrationMap" \
    --console-script "StartBattle" \
    --name battle_integration_map_load
```

Expected:
- Map loads without crash
- GameMode initializes correctly
- Player pawn spawns
- No `Blueprint Runtime Error` or `Accessed None` in active bucket

### Phase 3: Battle encounter trigger

Trigger the encounter via:
- Console command: `ce StartSession` (if bound)
- Or: interact with `BP_MelodiaEncounter_FirstDream` in the level
- Or: QuillScript notification `melodia:battle:first_dream_encounter`

Verify:
- Battle UI appears (`BP_BattleUI` or `UMelodiaRhythmHUDWidget`)
- Highway becomes active
- Player input (Q/W/O/P) registers lane hits
- Damage scalar applies correctly
- Enemy HP decreases

### Phase 4: Battle completion

Win or lose the battle. Verify:
- Battle result is broadcast (`Victory` / `Defeat` / `Fled`)
- `UMelodiaNarrativeSubsystem::CompleteBattle` is called
- `bBattleCompletionConsumed` guard prevents double-reward
- Narrative record is updated
- Game returns to exploration (or game over)

### Phase 5: Save / reload verification

```bash
# After battle, trigger save
ce SaveGame
# Then reload and verify narrative record
```

Verify:
- `BP_JRPGSaveGame` slot contains `melodiaNarrativeRecord`
- `ConsumedIntentIds` includes the battle intent
- Re-triggering the same encounter is a no-op (idempotent)

---

## Success Criteria

| Check | Expected |
|---|---|
| PIE load | No crash, map loads in < 5s |
| GameMode init | `BP_MelodiaJRPGGameMode` possesses player |
| Encounter trigger | Battle starts, UI appears |
| Input registration | Q/W/O/P produce lane hits |
| Damage application | Enemy HP decreases, scalar latches |
| Battle completion | Result broadcast, record updated |
| Save/Reload | Record persists, idempotency holds |

---

## Recording

Record the gate result:

```bash
python Tools/echo_run.py record battle_integration_map pass \
    --note "PIE battle in MelodiaIntegrationMap: <result summary>"
```

---

## Related

- `specs/echo_pipeline.json` — runner contract
- `Docs/ECHO/campaign_01_rhythm_damage_delta.md` — rhythm gate campaign
- `Docs/Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md` — rhythm game owner lock
