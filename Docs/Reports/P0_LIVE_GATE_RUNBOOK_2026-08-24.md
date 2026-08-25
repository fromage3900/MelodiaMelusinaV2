# P0 Live-Gate Runbook — 2026-08-24

**Scope:** documentation-only preparation for one serialized live gameplay
session. This document does not promote source checks to runtime proof, does
not authorize an editor launch, and does not modify a map, asset, save, or
controller.

Machine-readable counterpart:
`Docs/Reports/P0_LIVE_GATE_EVIDENCE_MATRIX_2026-08-24.json`.

**Execution state:** `MOVING_BASELINE_HOLD`. The initial baseline
`9e7e44488bfdc0317b59c478549e3e9daacdb457` refreshed once to
`df404e84a5e0be32cac489c080d6e612f7c19d98`, then moved again to
`35aa86bcf63a2e117f9e84cd5579c27b509575ee` before any live execution.
Historical evidence remains useful at its recorded tier, but no live row may
start until an owner supplies one new stable baseline and serialized editor
reservation.

## Proof tiers

| Tier | Meaning | Promotion rule |
| --- | --- | --- |
| T0 — source | Code, assets, or static topology exist. | Never proves execution. |
| T1 — offline | A contract, syntax, or native build passes. | Never proves an editor route. |
| T2 — scoped runtime | One named PIE route runs cleanly with a log marker. | Proves only that route and session. |
| T3 — player-visible | Real input and viewport/UI behavior are observed. | Required for HUD, rhythm, and interaction claims. |
| T4 — durable loop | The action survives its required save/reload or replay boundary. | Required for save and world-key claims. |

## Accepted historical evidence

These results are historical T1/T2 evidence, not a claim that the current
editor session is healthy:

| Area | Evidence | Tier | Status / boundary |
| --- | --- | --- | --- |
| Enemy territory guard | `pie_smoke_43_113022`, `MELODIA_P0_ENEMY_TERRITORY_FUNCTION_PROBE_20260822`; Average + detector; 30 s; forbidden runtime matches 0 | T2 | PASS for the inherited Average path. Direct Aggressive-base spawn remains unavailable because it is abstract. |
| Guard compile | Base, Aggressive, Average, detector: 0 errors/0 warnings | T1 | PASS; does not prove a full battle. |
| HUD ownership | `Tools/test_melodia_hud_ownership_contract.py` | T1 | PASS source contract; viewport ownership is still unproven. |
| Wardrobe transaction | `Tools/test_melodia_wardrobe_transaction_contract.py`, 67/67 | T1 | PASS contract only; no gameplay/save replay proof. |
| Echo | `Tools/test_echo_contract.py`, 77/77 | T1 | PASS contract only. |

Sources: `Saved/Dashboards/melodia_integration_map_live_20260822.json`,
`Saved/Echo/BattleIntegrationMap/enemy_territory_matrix_20260822_report.json`,
and `Saved/Echo/BattleIntegrationMap/runtime_log_audit_20260822_report.json`.

## Entry gate — before any live test

All items must be true. Otherwise record `HOLD` and stop; do not fix code
during the live session.

1. Exactly one healthy editor is bound to the agreed endpoint; no stale or
   second editor owns the world.
2. The test map is explicitly named and is not a protected lookdev map.
3. `list_dirty_packages` and errored-Blueprint baselines are recorded.
4. The baseline SHA matches this runbook, or a single documented refresh is
   accepted. A second movement is `MOVING_BASELINE_HOLD`.
5. The log marker, expected actors, duration, teardown check, and forbidden
   patterns are written before PIE starts.

## Serialized P0 execution matrix

Run one row at a time. A row’s failure is evidence for its owner; it is not
authorization to patch a neighboring subsystem.

| Order | Gate | Required proof | Current status | Stop condition |
| --- | --- | --- | --- | --- |
| 0 | Controller regression control | Average + detector in the already-proven territory route; zero `Blueprint Runtime Error`, `Accessed None`, Fatal, Ensure after marker | Historical T2 PASS | Any forbidden log match; retain exact marker/log. |
| 1 | HUD single writer | Open/close a battle; one main battle widget and one rhythm surface only; visible ownership handoff | T1 PASS / T3 OPEN | Duplicate widget, missing legend/prompt, or UI error. |
| 2 | Rhythm owner | Real key input travels `BP_BattleUI::OnKeyDown → UMelodiaRhythmCombatSubsystem → BP_BattleController::DealDamage` exactly once | T0 source path / T3 OPEN | No damage, duplicate damage, or unowned input. |
| 3 | Grade to result | One rated input reaches `FinishSession → SubmitRatedInput/SubmitResult → stock resolver`; result is visible | T0 source path / T3 OPEN | Grade/result mismatch or missing viewport result. |
| 4 | Wardrobe round trip | Grant/equip approved cosmetic, save, reload, and verify `ApplyWardrobeState` restores it | T1 contract / T4 OPEN | Cosmetic changes without durable replay proof. |
| 5 | Wardrobe gameplay hook | An approved capability changes Glide availability and restores correctly | T0 seam / T3 OPEN | Traversal changes without an owned capability decision. |
| 6 | Music world key | Place **one owner-approved active-level host**, play one phrase, then reload/replay and verify commit | T0 seam / T4 OPEN | No owner-approved host. Do not attach globally. |
| 7 | Choral Sheep integration | Finished owner-approved rig, definition asset, first actor spawn, follow + Graze/Harmonize/Guide range smoke | T1 build / T3 OPEN | Rig missing, editor unhealthy, or map-selection conflict unresolved. |

## Decisions and collisions requiring an owner

| Item | Why it blocks promotion | Required owner decision |
| --- | --- | --- |
| Music-world-key host | No active authored host is approved for the bridge. | Name one allowed level and host; no global attachment. |
| Choral Sheep first map | `Docs/CHORAL_SHEEP_INTEGRATION_RUNBOOK.md` currently names isolated `L_ChoralSheep_Prototype` and also says to use `MelodiaIntegrationMap`. | Choose one first-test map and update only the owning runbook. |
| Choral Sheep rig | No owner-approved mesh/Groom/animation kit yet. | Deliver the rig at the reserved path; base mesh is sufficient for the first gameplay smoke. |
| Oceanology | Binary-only; descriptor/source/build/shader proof absent. | Acquire an appropriately licensed source package in a separate lane; not a P0 live-session task. |

## Evidence packet for each executed row

Record the baseline SHA, map, session/marker, action sequence, runtime-log
match counts, teardown result, proof tier achieved, screenshots only where the
row requires T3, and the exact next owner if it remains open. Do not call a
clean capture beauty proof, and do not call a source contract a completed
gameplay loop.
