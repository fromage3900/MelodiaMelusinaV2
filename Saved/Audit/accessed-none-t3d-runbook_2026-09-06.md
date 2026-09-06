# Accessed-None T3D runbook — 2026-09-06 (EXECUTE ONLY WITH EDITOR UP)

Source: battle PIE log, 19 errors in 6 sites, all stock-template null reads. No probe data —
all sites confirmed by error text against live asset paths (disk-verified 2026-09-06).

## Guard primitive (all sites)

Standard `IsValid` (KismetSystemLibrary, covers null AND pending-kill) with its two exec
outs wired directly — no Branch node needed:

- `then` → existing guarded chain
- `Is Not Valid` → bypass (skip) or safe terminal (DestroyActor self / Return)

```text
Begin Object Class=/Script/BlueprintGraph.K2Node_CallFunction Name="IsValid_GUARD"
   FunctionReference=(MemberParent=Class'"/Script/Engine.KismetSystemLibrary"',MemberName="IsValid")
   NodePosX={{x}} NodePosY={{y}}
   NodeGuid={{GUID:isvalid}}
   CustomProperties Pin (PinId={{GUID:iv_exec}},PinName="execute",Direction="EGPD_Input",PinType.PinCategory="exec",PinType.PinSubCategoryObject=None,LinkedTo=(PREV {{GUID:prev_out}},),)
   CustomProperties Pin (PinId={{GUID:iv_then}},PinName="then",Direction="EGPD_Output",PinType.PinCategory="exec",PinType.PinSubCategoryObject=None,LinkedTo=(NEXT {{GUID:next_in}},),)
   CustomProperties Pin (PinId={{GUID:iv_obj}},PinName="Object",Direction="EGPD_Input",PinType.PinCategory="object",PinType.PinSubCategoryObject=Class'"/Script/CoreUObject.Object"',LinkedTo=(READER {{GUID:var_out}},),)
   CustomProperties Pin (PinId={{GUID:iv_valid}},PinName="ReturnValue",Direction="EGPD_Output",PinType.PinCategory="bool",PinType.PinSubCategoryObject=None,)
   CustomProperties Pin (PinId={{GUID:iv_invalid}},PinName="Is Not Valid",Direction="EGPD_Output",PinType.PinCategory="exec",PinType.PinSubCategoryObject=None,LinkedTo=(BYPASS {{GUID:bypass_in}},),)
End Object
```

PREV/NEXT/BYPASS pin ids come from the live export at execution time — never hand-fill.

## Sites (all under Content/TurnBasedJRPGTemplate — live copies, NOT _ThirdParty)

Linkage resolved offline 2026-09-06 from live exports in
`Saved/Audit/accessed-none-*-EventGraph_2026-09-06.json` (+ fingerprints-before).
Positions (`pos`) are live values; place guards at the given coords.

| # | Asset / graph | Cut point (exec link to reroute) | Guard Object ← | Invalid → | New nodes / pos |
|---|---|---|---|---|---|
| 1 | EnemyUnitBase / EventGraph | `SetHP_13.then` → `SetVis_2.execute` | `VariableGet_1.EnemyUnitWidget` | `VariableSet_1.execute` (null store is safe) | IsValid @ [550,0] |
| 2 | EnemyBossBase / EventGraph | `StopRotate_1.then` → `DestroyComp_0.execute` | `VariableGet_0.EnemyUnitWidget` | — (chain end) | IsValid @ [710,128] |
| 3 | ProjectileBase / EventGraph | `MoveProjectileToTarget.then` → `SetPlayRate_13.execute` | `VariableGet_9.target` | NEW `Destroy Projectile` call (self) @ [950,1300] — reuses stock destroy path, do NOT steal `_5` (owned by `_6.then`) | IsValid @ [950,1095] + CallFunction |
| 4 | BattleController / EventGraph | `IfThenElse_1.then` → `AdjustBackCam_16.execute` | `Knot_7.OutputPin` (playerUnit chain) | — (`_16.then` already empty) | IsValid @ [500,4340] |
| 5a | EnemyUnitBase / EventGraph | `VariableSet_2.then` → `Focus_24.execute` | `VariableSet_2.Output_Get` | `CallFunction_39.execute` | IsValid @ [2640,1210] |
| 5b | EnemyUnitBase / EventGraph | `AdjustCam_27.then` → `Focus_36.execute` | `VariableGet_15.currentTarget` | `CallFunction_40.execute` | IsValid @ [1260,2272] |
| 5c | EnemyUnitBase / EventGraph | `IfThenElse_1.then` → `Focus_19.execute` | `VariableGet_15.currentTarget` | `CallFunction_32.execute` (existing else branch) | IsValid @ [1130,2800] |
| 6 | JRPGFunctionLibrary / DisableActor | `FunctionEntry_0.then` → `SetHidden_4.execute` | `FunctionEntry_0.actor` | NEW `K2Node_FunctionResult` (graph has none) | IsValid @ [140,0] + FunctionResult @ [140,160] |

Total: 9 IsValid + 1 Destroy-Projectile call + 1 FunctionResult = 11 nodes, 5 assets.
No new VariableGets (all guard subjects reuse live outputs). No Branch nodes
(IsValid's own `then` / `Is Not Valid` outs carry the fork).

## Execution sequence (per asset, in order)

1. `get_graph_fingerprint` → record BEFORE fingerprint.
2. `export_graph` the target graph → fill PREV/NEXT/BYPASS linkage.
3. `validate_nodes_t3d` dry_run → must read valid + engine_accepts.
4. `inject_nodes_t3d` → `connect_pins_bulk` for the rerouted exec/data pins.
5. `compile_blueprint` → 0 errors, 0 warnings tolerance: errors are HARD STOP.
6. `get_graph_fingerprint` → record AFTER; delta must equal guard nodes only.
7. Save asset → `list_dirty_packages` to confirm (success:true is not proof).
8. Re-export graph → JSON to `Saved/Audit/accessed-none-postfix_<asset>_<date>.json`.

Do NOT "fix" by widening: no behavior change beyond null-safety (site 3 DestroyActor
choice is the one judgment call — confirm against live graph).

## Acceptance

- Battle PIE (MelodiaIntegrationMap, authored encounter): log grep `Accessed None` = 0
  and `pending kill or garbage` = 0 across a full Victory + Defeat cycle.
- Before/after fingerprints + compile logs archived next to this runbook.
- No ledger row owed (bugfix, not a gate) — unless owner wants a `runtime` re-record,
  in which case run the golden route, not this probe.
