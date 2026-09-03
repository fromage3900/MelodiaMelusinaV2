# T3D injection payloads

Reusable `inject_nodes_t3d` payloads, and the sequence for running them.

## Why these exist

`add_node` + `connect_pins` is the Recipe 15 path. For anything past two or three
nodes it is, in the guide's own words, "the slow and dangerous path": every call
is a round trip, and a failure halfway leaves a half-wired graph to unpick by
hand. On 2026-08-09 an attempt to author a cross-object `VariableSet` that way
produced an unbound `Set` node with no variable and no target pin — the empty
shell defect class this project keeps paying for.

T3D is the editor's own clipboard format, so it can express node classes the
structured API cannot reach — including `K2Node_CallParentFunction`, which the
co-op skill spec recorded as "could not confirm Monolith can author". That line
was a previous session's *uncertainty*, and it hardened into a documented
constraint that went untested for a day. Test it; do not inherit it.

## The sequence (Recipe 16)

```
python Tools/bp_live_path.py <asset>     # step 0 — abort on ORPHAN or AMBIGUOUS
blueprint.validate_nodes_t3d             # zero-mutation pre-flight
blueprint.get_graph_fingerprint          # before
blueprint.inject_nodes_t3d               # one transaction, compile: true
blueprint.get_graph_fingerprint          # after
blueprint.assert_graph_matches           # prove it landed
blueprint.save_asset
```

**Step 0 is not optional here.** `BP_SirSkyboundRefrain` and `BP_Resonance` each
exist twice — once live under `/Game/MelodiaIntegration/Party/Skills/`, once in
the untracked `Content_MelodiaIntegration/` mirror. `BP_FocusAttack` also exists
in `_ThirdParty`. Injecting into an unreachable copy is worse than a bad payload
because it **succeeds**.

**The pre-flight is free and carries zero risk of mutation.** A payload whose
node 7 names a renamed function aborts before the graph is touched, leaving it
byte-identical. Iterate against `validate_nodes_t3d` as many times as needed.
It reports `valid: false` — it does not throw. Branch on the field.

**Re-injection is not idempotent.** Guid collisions are forced unique on import,
so injecting twice yields two working copies of the cluster. Delete first or
assert absence before re-running.

## Grammar notes (read off live exports, not invented)

- Nodes are `Begin Object Class=<class> Name=<name>` … `End Object`.
- `NodeGuid=` and each `PinId=` are 32 hex chars; parameterise them as
  `{{GUID:name}}`. One distinct name mints one guid per call — using the same
  name in a node's guid and inside another node's `LinkedTo=(...)` is what makes
  the link survive.
- Links are `LinkedTo=(<NodeName> <PinGuid>,)` — node **name**, pin **guid**.
- Member refs: `FunctionReference=(MemberName="X",MemberParent=<class>,bSelfContext=)`.

## Safe against the skills landmine

`Content/TurnBasedJRPGTemplate/Blueprints/Skills/` kills the editor when touched
from **Python** (`D_DamageType` glue generation, fatal). `validate_nodes_t3d` and
`inject_nodes_t3d` are native C++ and do not take that path, so authoring skill
Blueprints this way is safe. Do not reach for `editor_query run_python` here.

## Files

| File | Purpose | State |
|---|---|---|
| `parent_call_probe.t3d` | One `K2Node_CallParentFunction`, nothing else. Run **validate only** — never inject it. Decides whether the node class is authorable at all. | ready, untested |

**Run the probe first.** The full Skybound Refrain cluster is ten nodes whose
single novel element is the parent call. Betting ten blind nodes on one unproven
node class is a bad trade when proving it in isolation costs one free call.

### Probe result (2026-08-09) — the "hand-only" constraint is dead

`validate_nodes_t3d` against `BP_SirSkyboundRefrain` returned
**`valid: true`, `engine_accepts: true`, `declared_nodes: 1`**.
`K2Node_CallParentFunction` IS authorable through T3D. The line in
`COOP_SKILL_RESONANCE_SPEC_2026-08-08.md` saying otherwise was an untested
assumption and should not be relied on again.

One open detail: `MemberParent` still reports
`unresolved_member_parent ... (function existence not checked)` as a **warning**
under both quoting forms tried (`Class'"..."'` and `"...'...'"`), even with
`BP_FocusAttack_C` resident. The class path itself is confirmed correct via
`get_parent_class`. Resolve this by copying a real parent-call node in the editor
and reading its exact `FunctionReference=` spelling — do not keep guessing, and
do not inject while this warning stands: Recipe 16 notes that a bad member ref
passes `CanImportNodesFromText` cleanly and imports as a red node.

### Member references — RESOLVED, read from the live graph

| Member | Declaring class | Type / default |
|---|---|---|
| `battleController` | `BP_BattleSkillBase_C` | `object:BP_BattleController_C` |
| `damageMultiplier` | `BP_FocusAttack_C` | `double`, default **1.2** |
| `buffs` | `BP_BattleSkillBase_C` | `array:class:BP_BuffBase_C` |
| `activeBuffs` | `BP_UnitBase_C` | `map:class:BP_BuffBase_C` |

Still unread: the exact `PinType.PinValueType` / `PinSubCategoryObject` spelling
for a **class-keyed map** pin. Copy that off a live export rather than guessing.

### Petal Cadence needs no graph at all

`BP_MelusinaPetalCadence` has no authored logic — three disabled default events
and a construction-script parent call. It applies Resonance through the `buffs`
array on `BP_BattleSkillBase`, i.e. **data, not nodes**. So only Sir's half of
the co-op pair needs authoring. Do not "fix" Petal Cadence; it is already done.

Note `damageMultiplier` already defaults to 1.2, so the spec's `False -> set 1.2`
branch is only load-bearing if skill actors are reused between casts (a 1.8 write
would otherwise persist). Confirm reuse before deciding to drop that branch.
