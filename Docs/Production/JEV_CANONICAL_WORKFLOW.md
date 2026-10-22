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

### 4a. Two packet traps that produce a receipt that looks fine and is not (found 2026-10-22)

Both were caught on the house-leg packet (`Tools/house_dressing/jev_house_dressing_decisions_20261022.py`); the receipt that exposed them is in `Saved/Audit/house_dressing/`.

1. **The criteria TEXT must be transmitted.** `Choice(criteria={option: None})` sends four EMPTY options: the service sees the question with nothing to choose between and answers arbitrarily. The first run of that packet returned `"A"` for all five questions, with no distribution - it was not a judgement, it was a coin that lands the same way. Send `criteria=dict(spec["criteria"])` - the option descriptions are the whole point of a closed candidate set.
2. **Read the fields the answer actually has.** `ChoiceAnswer` carries `choice`, `confidence` and a full `probabilities` distribution. It has **no `reason` and no `score` field** (model `jev-1.14.0`), so a receipt that looks for `.reason`/`.score` records nulls that read as "Jev had no opinion" when the confidence and the distribution were there all along. Do not cite a reason that the model did not produce; cite the distribution.

And the sampling rule that falls out of this: **one run is one sample.** When the answer is a close call, run the packet more than once and record the mean distribution AND the run-to-run agreement - a single draw at 0.11 confidence is not a decision. `Tools/house_dressing/jev_house_dressing_decisions_aggregate.py` is the worked example: three samples, per-question mean distribution, agreement rate, and a `DECIDED` / `NEAR_TIE_OWNER_CALL` verdict.

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

## 7a. Jev + Universe Foundry\n\nUniverse Foundry may emit Jev tasks from authored World Genome decision points. Each task must carry a closed candidate set. Jev selects; it does not generate world data or execute the selected mutation.\n\nCanonical flow:\n\n\`\`\`text\nWorld Genome decision point\n  -> Jev selects one authored candidate + confidence/distribution\n  -> Hermes routes the now-bounded specialist task\n  -> existing World Compiler / Hython / TD / UE owner executes\n  -> independent evidence returns to the mission DAG\n\`\`\`\n\nContract: [\`UNIVERSE_FOUNDRY_CONTRACT.md\`](UNIVERSE_FOUNDRY_CONTRACT.md).\n\n## 8. When not to ask Jev

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
