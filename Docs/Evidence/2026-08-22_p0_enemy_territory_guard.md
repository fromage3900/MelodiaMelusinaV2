# P0 enemy-territory guard evidence

Status: local Blueprint fix compiled and scoped PIE-tested on 2026-08-22. This
document is the versioned summary for the authoritative runtime reports under
`Saved/Echo/BattleIntegrationMap/`, which remain intentionally ignored.

## Versioned asset boundary

Only these two stock-template Blueprint assets are intentionally brought under
Git LFS tracking:

- `/Game/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/BP_EnemyExplorePawnBase`
- `/Game/TurnBasedJRPGTemplate/Blueprints/EnemyExplorePawns/AggressiveEnemyExplorePawns/BP_AggressiveEnemyExplorePawnBase`

`BP_AverageEnemyExplorePawn` and `BP_InteractionDetector` are test coverage
subjects, not changed assets; they remain outside this exception.

## Proven path and correction

`BP_AverageEnemyExplorePawn` has an empty EventGraph and inherits
`BP_AggressiveEnemyExplorePawnBase::IsPlayerInsideAITerritory`, which calls
`BP_EnemyExplorePawnBase::GetAITerritory`. The latter dereferenced the `battle`
reference for radius and actor location without a validity check.

`GetAITerritory` now routes `IsValid(battle)` through a branch: the valid path
uses the original return; the invalid path returns zero defaults. The existing
Aggressive-child BeginPlay binding is also guarded by
`IsValid(Get jRPGPlayerController)` before it binds `On Possessed Character`.

## Verification

- Parent, Aggressive, Average, and detector Blueprints compiled with 0 errors
  and 0 warnings.
- PIE session `pie_smoke_43_113022` ran for 30 seconds on
  `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`.
- The concrete Average child and detector control each spawned once.
- `GetAITerritory` returned origin `(-3570, 1500, 20)` and radius
  `725.0287056`; `IsPlayerInsideAITerritory` returned `false`.
- Post-marker Blueprint Runtime Error, Accessed None, Fatal, and Ensure counts
  were all zero.

The Aggressive base is abstract and cannot be spawned directly; its inherited
runtime path is covered through the concrete Average child. This does not close
the separate music-key, wardrobe, rhythm, or full-battle gates.

## Authoritative local evidence

- `Saved/Echo/BattleIntegrationMap/enemy_territory_matrix_20260822_report.json`
- `Saved/Echo/BattleIntegrationMap/runtime_log_audit_20260822_report.json`
- `Saved/Dashboards/melodia_integration_map_live_20260822.json`

Git LFS locking was attempted before this tracking exception. It is pending
because GitHub connectivity was unavailable; acquire both locks before staging
or pushing the two assets.
