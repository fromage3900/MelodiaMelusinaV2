# Blueprint + Mechanics Integration Review — 2026-07-18

Scope: audit every gameplay Blueprint against the C++ authority layer for seamless integration, per Fable's queue item 4. Method: `editor_query.list_errored_blueprints` baseline, then `blueprint_query.validate_blueprint` + `get_interfaces` across the enumerated gameplay BPs, cross-checked against C++ `Execute_` call sites and live PIE evidence gathered earlier this session.

**Not exhaustively run**: `analyze_blueprint_graph`, `audit_cdo_drift`, `validate_animbp_variable_contract` per-BP deep dives. What's below is real, verified findings from the checks that were run — not a claim of full coverage. Flagging this honestly rather than padding the doc with unchecked boxes.

## Baseline

`list_errored_blueprints` → **0 errored blueprints** project-wide at time of audit.

## Findings

### BLOCKER: presentation interfaces have zero implementers anywhere

`MelodiaBattleSession.cpp` calls into two interfaces at real gameplay moments:

```
Execute_OnMelodiaCommandResolved(PlayerPawn, ...)   — line 194
Execute_OnMelodiaVictory(PlayerPawn)                — line 203
Execute_OnMelodiaEnemyIntentStarted(EnemyActor, ...) — line 212
Execute_OnMelodiaEnemyHit(EnemyActor, ...)          — line 222
Execute_OnMelodiaEnemyBroken(EnemyActor, ...)       — line 231
Execute_OnMelodiaEnemyDefeated(EnemyActor, ...)     — line 247
```

Checked `get_interfaces` on `BP_Melusina` (the player pawn target) and `BP_MelodiaEnemyBase` (the enemy target, parent of all 3 enemy BPs): **both return `count: 0`** — not even inherited. Grepped the whole plugin source for `public IMelodiaEnemyPresentationInterface` / `public IMelodiaCombatPresentationInterface`: **zero C++ classes implement either interface.**

`Execute_X` on an object that doesn't implement the interface is a safe no-op in UE (no crash) — but it means **every one of these six presentation hooks currently does nothing, visually, ever.** No hit reaction, no victory pose, no enemy intent telegraph animation, no broken/defeated reaction — despite the C++ authority layer correctly firing the calls at the right moments.

This is not a new regression — it restates and confirms the original plan doc's own audit note ("Presentation plumbing... exist unused — Phase 1 mostly writes CALLERS for hooks that were built for this"). It's still true today. **Fixing it requires actual animation/VFX authoring decisions** (which montage plays on which event, timing, blending) — out of scope for a pure-wiring fix, flagged for the coordinator/animation lane rather than invented here.

### COSMETIC: orphaned duplicate `BP_Melusina`

`/Game/Characters/Melusina/BP_Melusina` (old root) exists alongside the real `/Game/Melodia/Characters/Melusina/BP_Melusina`. `find_references` on the old one returns zero in both directions (`depends_on: []`, `referenced_by: []`) — a true orphan, safe to quarantine. Matches the project's known 7-dupe-root pattern. **Not deleted** (hard rule); flagging for the existing `DUPE_ROOT_QUARANTINE_2026-07.md` list.

### COSMETIC: unused variables on all 4 enemy BPs

`BP_Enemy_StoneGolem`, `BP_Enemy_CrystalShard`, `BP_Enemy_SakuraPhantom`, and their shared parent `BP_MelodiaEnemyBase` all report the identical unused-variable set: `EnemyId`, `EnemyDisplayName`, `EnemyScale`. Consistent across all 4 (same base-class origin), and these names are referenced across 24 C++ files project-wide — almost certainly C++/data-driven (set externally, never read inside the BP's own graphs), not genuinely dead. Not chased further given the volume of cross-references; low severity either way.

### CLEAN — validated, no issues found

`validate_blueprint` (unused vars / disconnected nodes / node errors / unimplemented interface functions / duplicate custom events) ran clean — zero disconnected nodes, zero node errors, zero duplicate custom events — on:

| Blueprint | Notes |
|---|---|
| `BP_Melusina` | Player pawn — PIE-confirmed spawns correctly as `BP_Melusina_C_0` (multiple runs this session) |
| `BP_SirMelodious_Flight` | |
| `BP_MelodiaDungeonRunCoordinator` | |
| `BP_MelodiaRoomExit` | |
| `BP_DungeonFloorManager` | |
| `BP_RoguelikeDungeonGenerator` | Deep-audited separately this session (see commits `847a637a`, `5d0cd216`) |
| `BP_MelodiaGameMode` | data-only BP (class-default overrides only, no graph logic) |
| `WBP_Battle_Rhythm` | |
| `WBP_Battle_Results` | Authored this session — 27-node EventGraph compiles clean, data-bound |
| `WBP_UltCutIn` | Authored this session — static layout |
| `ABP_Melusina_Current` | Glide state added this session, compiles clean |
| `ABP_Melusina_WaterHair` | |

No JRPG-template-bridge references found in any of the above (would show as `find_references` hits on `/Game/_ThirdParty/TurnBasedJRPGTemplate/...` classes — not checked exhaustively across all 13, but none surfaced incidentally during the audit).

## Recommended next steps, in order

1. **Presentation-interface implementation** is the single highest-leverage remaining gap — it's why combat currently has zero hit-reaction/victory/intent feedback despite the C++ firing correctly. Needs an animator/designer to decide what `BP_Melusina` and `BP_MelodiaEnemyBase` actually *do* on each of the 6 events (which montage, what timing) — a judgment call, not wiring.
2. Add the old-root `BP_Melusina` to the dupe-quarantine list (zero-reference, safe).
3. If pursuing full coverage later: `audit_cdo_drift` + `validate_animbp_variable_contract` on the two AnimBPs, and `analyze_blueprint_graph` on the enemy BPs specifically (their shared unused-var pattern is worth one confirmatory pass even though it's almost certainly benign).
