# Jev — Canonical Decision & Orchestration Workflow

**Purpose:** define Jev as an always-available canonical production service for bounded judgment, orchestration, and authored-state selection across Melodia.  
**Status authority:** `CURRENT_STATE.md`.  
**Execution authority:** the existing lane that owns the mutation (Monolith, World Compiler, Hython, Rider/RiderLink, FL bridge, etc.).

Jev is not a prototype-only curiosity. It is a standard production surface that agents may reach for whenever a task benefits from structured judgment among authored options.

## 1. What Jev owns

Jev owns **decision quality**, not game/editor state.

Use Jev for:

- selecting among explicit authored candidates;
- choosing the next bounded verification/action step;
- adjudicating competing production strategies;
- directing phrase-level world/animation/music responses;
- choosing which existing tool/lane should execute next;
- ranking or filtering bounded implementation plans;
- confidence-aware go/hold decisions;
- comparing fallback/classical policy against live model judgment when validating a director.

Existing examples include Choral Sheep direction, bow presentation, portfolio canonicalization, hair-physics finalization, retarget strategy, Listening Field directives, FL phrase conduction, and P0 triage.

## 2. Jev is always part of the canonical toolbox

A production agent does not need to treat Jev as an exotic opt-in experiment.

When judgment is genuinely ambiguous, prefer:

```text
observe current state
  -> assemble closed candidate set
  -> define explicit criteria
  -> ask Jev once at the correct decision boundary
  -> record choice + confidence/distribution + source
  -> execute through the existing owner
  -> verify the result independently
```

Do not replace a deterministic validation rule with Jev. Use Jev where judgment is the missing piece, not where a schema/test can answer exactly.

## 3. Closed candidate sets

Jev should normally choose among authored, validated options.

Examples:

- `BOW_V1 | BOW_V2 | HOLD`
- `GRAZE | TURN_TO_PLAYER | SETTLE`
- `THIN | BUILD | BLOOM | RESTRAIN | FULL_CHORUS`
- a bounded set of World Compiler identities/recipes/seeds;
- a bounded set of next verification actions;
- a bounded set of implementation strategies already checked for architectural legality.

Never send Jev an unconstrained request that lets it invent a new runtime authority, arbitrary asset path, gameplay ID, or editor mutation.

## 4. Provenance contract

Every Jev-backed production decision should preserve:

- `source=jev-live`;
- selected option;
- confidence and/or full distribution when available;
- short reason/criteria result;
- input-state identity or receipt;
- execution result;
- independent verification result.

A deterministic/classical fallback may remain in tests and resilience code, but it must be labeled as fallback and must never be presented as Jev evidence.

## 5. Jev + editor mutation

Jev does **not** directly mutate Unreal.

Correct shape:

```text
Jev chooses/directs
  -> Monolith / existing UE action executes
  -> readback/assertion proves state
```

For worldbuilding:

```text
Jev selects bounded identity / strategy
  -> World Compiler recipe/data changes
  -> compiler + UE driver execute
  -> scene-context/readback proves result
```

For animation:

```text
Jev selects authored clip/presentation strategy
  -> guarded Rokoko / ABP / Monolith lane executes
  -> PIE capture + audit receipt proves result
```

For native engineering:

```text
Jev can adjudicate implementation/test strategy
  -> Rider edits existing owner
  -> Qodana + build + RiderLink/focused tests
  -> UE runtime proof
```

## 6. Jev + Listening Field / phrase systems

The existing canonical director shape is:

```text
melodia.phrase/v1
  -> Jev judgment at phrase boundary
  -> melodia.directive/v1 closed allowlist
  -> existing consumers
```

Jev does not compile meadows, write MPCs, move actors directly, or become a second PhraseBus.

Use:
- `Tools/listening_field/jev_director.py`
- `Tools/listening_field/directive_schema.py`
- `Docs/Production/LISTENING_FIELD_SPEC_2026-09-20.md`

## 7. Jev + agent orchestration

For multi-agent work, Jev may serve as the decision layer over specialist executors.

A good orchestration packet contains:

- current branch/head;
- `CURRENT_STATE.md` facts relevant to the task;
- candidate next actions;
- dependencies and blockers;
- cost/risk/verification criteria;
- allowed mutation surface;
- stop condition.

Jev chooses the next bounded action. The specialist agent/tool executes it. Evidence is returned to the orchestrator before the next decision.

This prevents a planner from becoming another implementation authority.

## 8. When not to ask Jev

Do not spend a judgment call on:

- whether a JSON schema validates;
- whether a C++ build compiles;
- whether Qodana reports a defect;
- whether an LFS pointer is valid;
- whether an exact allowlist contains an ID;
- whether a file exists;
- whether a unit test passes.

Use deterministic tools for deterministic questions.

## 9. Canonical production stack

Jev should be thought of alongside the always-available engineering surfaces:

```text
Jev          = judgment / orchestration / direction
Rider        = native code navigation / editing / debug
RiderLink    = focused live-editor automation tests
Qodana       = static-analysis quality gate
Monolith     = bounded editor mutation/readback
World Compiler = authored procedural-world compilation
Hython       = deterministic DCC forge
Rokoko guarded lane = performance-capture ingestion
```

The goal is composition, not replacement.

**Jev decides where judgment is needed; deterministic tools prove what can be proven; existing owners execute.**

## 10. Echo Reflex canary

The experimental Echo Reflex layer applies this contract to project-wide mission routing:

- durable contract: `Docs/Production/ECHO_REFLEX_CONTRACT.md`;
- capability registry: `specs/echo_reflex_capabilities.v1.json`;
- mission schema: `specs/schemas/echo_reflex_mission.v1.schema.json`;
- canary controller/tests: `Prototypes/EchoReflex/`.

Echo Reflex is **not yet a production executor**. Its v0 boundary is preview-only: deterministic code computes legal transitions, Jev may select only among those transitions, and existing owners remain the only mutation surfaces.

The intended long-term split is:

```text
Astra / human = plan or replan the mission DAG
Echo/policy   = decide what transitions are legal
Jev           = resolve bounded ambiguity among legal transitions
specialists   = execute through existing owners
evidence      = determine whether the transition actually succeeded
owner         = retain visual/gameplay promotion judgment
```

Do not bypass the normal Jev provenance contract simply because the choice was made inside Echo Reflex.
