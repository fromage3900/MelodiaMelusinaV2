# Echo Reflex — Adaptive Orchestration Contract

**Purpose:** add an adaptive decision layer to the existing Melodia Echo pipeline without creating a second project authority, editor surface, world compiler, or agent framework.  
**Status authority:** `CURRENT_STATE.md`.  
**Execution authority:** existing owners only (Echo, World Compiler, Monolith, Hython, Rider/RiderLink, guarded importers, specialist workers, and the human owner).  
**Canary implementation:** `Prototypes/EchoReflex/`.

## 1. Architecture

```text
OWNER GOAL
   ↓
ASTRA / HUMAN PLANNER
   ↓  mission DAG using registered capabilities only
ECHO-STYLE DETERMINISTIC CONTROL
   ↓  legal nodes / dependencies / locks / evidence state
JEV
   ↓  choose only among already-legal transitions
EXISTING EXECUTOR / OWNER
   ↓  Kimi/Claude, Hython, World Compiler, Monolith, Rider, etc.
EVIDENCE
   ↓
MISSION STATE / EXISTING ECHO GATES
```

Durable rule:

> **Plan rarely. Decide often. Execute through existing owners. Promote only from evidence.**

Astra is the System-2 planner. Jev is the System-1 decision layer. Code owns what transitions are legal. Specialists execute. The game/editor/build/evidence establishes what is real.

## 2. Extend Echo; do not replace it

Melodia already has the substrate:

- `specs/echo_pipeline.json` — gated production stages;
- `Tools/echo_run.py` — fail-closed runner and ledger integration;
- `specs/echo_topo.json` + `Tools/echo_topo.py` — DAG dependencies, eligible nodes, promote gates and model-lane classification;
- `Tools/model_router.py` — specialist/model routing;
- `CURRENT_STATE.md` — current truth;
- `Docs/Production/AGENTIC_STUDIO_OPERATING_MODEL.md` — production/evidence rules;
- `Docs/Production/JEV_CANONICAL_WORKFLOW.md` — Jev boundary;
- World Compiler, Monolith, Hython, guarded importers and other named owners — execution.

Echo Reflex is a **control layer over those contracts**, not a parallel production spine.

## 3. Capability registry

A planner does not receive arbitrary shell access as its orchestration vocabulary.

It receives named handles such as:

```text
project.read_current_state
echo.topo_schedule
world.validate_recipe
world.compile_recipe
world.apply_bundle
hython.run_registered_tool
model.delegate_code
monolith.scoped_editor_action
owner.visual_review
```

The v0 registry is `specs/echo_reflex_capabilities.v1.json`.

Each capability declares its owner, mutation class, resources, executor type, argument boundary, evidence, and auto-execution policy.

A capability id is a handle to an existing owner. Registering one must never silently create a competing authority.

## 4. Planner contract

Astra or a human outputs a `melodia.echo_reflex_mission.v1` DAG.

Schema: `specs/schemas/echo_reflex_mission.v1.schema.json`.

A mission contains:

- one explicit goal;
- planner provenance;
- registered capability id per node;
- validated arguments;
- dependency edges;
- acceptance evidence;
- bounded failure behavior.

The planner may compose registered capabilities. It may not invent executable capability ids.

If the goal cannot be represented by the registry, request a reviewed capability addition; do not invent a command.

## 5. Jev contract

Jev receives only **deterministically legal** candidate transitions.

Correct:

```text
legal candidates:
  inspect_echo
  validate_recipe
  HOLD
  REPLAN
```

Incorrect:

```text
"Jev, what command should we run?"
```

Jev may choose one eligible node, `HOLD`, or `REPLAN`.

It does not generate commands, paths, Blueprint mutations, gameplay IDs, arbitrary arguments, or new authorities.

A Jev selection is **not authorization**. Policy and resource checks still run afterward.

If exactly one legal transition exists, deterministic code selects it without spending a Jev call. If multiple legal nodes exist and Jev is unavailable, v0 fails closed to `HOLD`; lexical ordering must never masquerade as judgment.

## 6. Resource locks

Capabilities declare resources such as:

```text
ue_editor_writer
repo_writer
houdini_license
```

`ue_editor_writer` expresses the existing rule: **one editor, one writer, one mutation surface**.

Independent tasks may run concurrently only when their resource sets do not conflict.

## 7. Human gates

Owner judgment remains mandatory for artistic promotion: composition, silhouette/readability, gameplay feel, portfolio selection, and whether a world actually looks better.

Jev confidence never converts an artistic judgment into truth.

`owner.visual_review` is therefore an explicit capability/gate.

## 8. Retry and replan

No infinite autonomous recovery loop.

Default shape:

- one bounded retry only when the mission explicitly permits it;
- failed/held dependency → `REPLAN`;
- authority/policy conflict → `HOLD`;
- visual/runtime owner judgment → `HOLD`;
- graph cannot reach goal using registered capabilities → `REPLAN`.

Astra replans only when the graph genuinely needs a new trajectory, not at every step.

## 9. Evidence and promotion

Echo Reflex does not weaken the existing ladder:

```text
SOURCE-BUILT
  → LIVE-PROVEN
  → RESTART-PROVEN
  → PACKAGED-PROVEN
```

The canary never writes PASS to `Saved/gate_ledger.json`.

A future production executor may request an Echo gate record only after that existing gate's verifier/evidence contract has been satisfied and reviewed.

Agent output, planner claims, Jev confidence, subprocess exit 0, or a screenshot alone are not promotion evidence.

## 10. Canary safety boundary

`Prototypes/EchoReflex/echo_reflex.py` v0 is preview-only.

It currently implements:

- registry validation;
- mission DAG and cycle validation;
- eligible-node calculation;
- resource-lock exclusion;
- deterministic single-transition selection;
- Jev closed-choice routing among legal nodes;
- fail-closed ambiguity when Jev is unavailable;
- `HOLD`, `REPLAN`, and `COMPLETE`;
- human-review classification;
- execution preview.

It does **not** execute arbitrary commands, mutate Unreal, write Git, write the Echo ledger, auto-merge, or expose arbitrary shell text to Astra/Jev.

Real execution should be promoted one capability at a time, beginning with deterministic read-only actions.

## 11. First proof target

The first fixture is a non-mutating Melusina's Study canary:

```text
read CURRENT_STATE ─┐
                    ├─→ validate known World Compiler recipe → owner gate
inspect Echo DAG ───┘
```

The Morning recipe in the fixture is only a known compiler input used to prove the control contract. It is **not** a claim that Morning content belongs in the Study.

After this is green, replace that placeholder with the real `MelusinasStudyDecorated` / Studio / World Compiler path, still stopping before uncontrolled editor mutation.

## 12. Promotion criteria

Do not call Echo Reflex production infrastructure until:

1. registry/mission tests are green;
2. live Jev returns only legal transitions with provenance;
3. one read-only mission completes end-to-end;
4. one bounded mutating mission respects `ue_editor_writer` and produces independent readback;
5. one injected failure yields bounded retry or `REPLAN`, not an infinite loop;
6. owner review remains a hard gate;
7. existing Echo promotion/ledger behavior remains unchanged and fail-closed.

Until then, Echo Reflex is a canary layered over canonical infrastructure.
