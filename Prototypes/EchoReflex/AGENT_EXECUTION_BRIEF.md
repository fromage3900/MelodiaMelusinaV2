# Echo Reflex — Agent Execution Brief

**Audience:** Muse, Kimi, Claude, Codex, or any specialist agent landing cold on the Echo Reflex canary.  
**Branch:** `feat/echo-reflex-canary-20260922`  
**PR:** #286  
**Authority:** `CURRENT_STATE.md` + `Docs/Production/ECHO_REFLEX_CONTRACT.md`  
**Goal:** prove the Astra-plan / Jev-control / existing-owner execution loop without creating a second project authority or touching Unreal mutation yet.

---

## 0. Your job

Execute the canary. Do **not** redesign the architecture unless a concrete failing test or missing control surface blocks execution.

Success means:

```text
mission validates
  -> fail-closed ambiguity is proven
  -> live Jev selects only a legal node
  -> that exact registered read-only node executes
  -> evidence is captured
  -> mission state advances
  -> the next real Melusina's Study mission graph is authored
  -> STOP before UE/Git mutation execution
```

Do not broaden scope into a new agent framework, general scheduler, new MCP server, new world compiler, or alternate state store.

---

## 1. Read first

Before writing code:

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `Docs/Production/ECHO_REFLEX_CONTRACT.md`
4. `Docs/Production/JEV_CANONICAL_WORKFLOW.md`
5. `specs/echo_reflex_capabilities.v1.json`
6. `specs/schemas/echo_reflex_mission.v1.schema.json`
7. `Prototypes/EchoReflex/echo_reflex.py`
8. `Prototypes/EchoReflex/example_melusinas_study_canary.v1.json`

Treat the existing Echo, World Compiler, Monolith, Hython, Melodia Studio, Rider/RiderLink, Qodana, guarded Rokoko and model-router surfaces as owners. Echo Reflex routes work between them; it does not replace them.

---

## 2. Hard boundaries

### You may

- run the existing Echo Reflex tests;
- run the existing Echo/static/offline gates;
- call live Jev through the existing TypeSafe/Jev client path;
- execute registry-approved `mutation=none` capabilities through Echo Reflex;
- improve Echo Reflex only when a reproduced blocker prevents the canary;
- author/validate the next mission DAG using registered capability ids;
- add a capability definition only when an existing canonical owner genuinely lacks a handle and the addition does not create a second authority;
- record machine-readable evidence and update PR #286 / `CURRENT_STATE.md` only when the actual state changes.

### You may not

- merge PR #286;
- enable auto-merge;
- write an Echo PASS merely because an agent/Jev says work succeeded;
- enable `ue_editor`, `repo_write`, Hython, specialist-agent, or human capabilities for automatic execution;
- mutate Unreal;
- run two editor writers;
- give Jev arbitrary shell, path, Blueprint, gameplay-id, or argument generation;
- give Astra unrestricted shell as its orchestration vocabulary;
- create another status/handoff authority;
- install a new orchestration framework to solve this mission;
- silently replace live Jev with a heuristic and call it Jev evidence.

If any of these becomes necessary, **HOLD and report the precise blocker**.

---

## 3. Phase A — structural proof

Run from repository root.

### A1. Echo Reflex unit contract

```powershell
python Prototypes/EchoReflex/test_echo_reflex.py
```

Required result:

```text
Ran 11 tests
OK
```

If this fails, fix only the reproduced defect, rerun, and do not continue until green.

### A2. Repository offline contract gate

```powershell
python Tools/run_contract_tests.py --offline --ci
```

Required result:

```text
23/23 passed
```

Do not lower the coverage floor or remove Echo Reflex from the suite to make this pass.

### A3. Validate the mission

```powershell
python Prototypes/EchoReflex/echo_reflex.py validate Prototypes/EchoReflex/example_melusinas_study_canary.v1.json
```

Required:

- `ok: true`;
- four mission nodes;
- only registered capability ids.

---

## 4. Phase B — prove fail-closed behavior

Run:

```powershell
python Prototypes/EchoReflex/echo_reflex.py next Prototypes/EchoReflex/example_melusinas_study_canary.v1.json --no-jev
```

Expected result:

- process exits non-zero by design;
- `action = HOLD`;
- `source = fail-closed`;
- reason states that multiple legal nodes require Jev or owner judgment;
- distribution contains only:
  - `read_state`
  - `inspect_echo`

This is a **PASS condition**, not a failure.

If the controller chooses a node without Jev when multiple legal roots exist, stop and fix that defect before continuing.

---

## 5. Phase C — live Jev decision proof

Prerequisite:

```text
TYPESAFE_API_KEY available in environment
```

Never commit the key.

Run:

```powershell
python Prototypes/EchoReflex/echo_reflex.py next Prototypes/EchoReflex/example_melusinas_study_canary.v1.json
```

The legal response set is closed:

```text
read_state
inspect_echo
HOLD
REPLAN
```

### Required Jev evidence

Capture the complete JSON response. A valid live selection must preserve:

- `source = jev-live`;
- selected node or HOLD/REPLAN;
- confidence;
- probability/distribution where the SDK returns it;
- only authored legal choices.

### Verdicts

**PASS:** Jev selects `read_state` or `inspect_echo` and returns live provenance.

**VALID HOLD:** Jev selects `HOLD` with a defensible evidence/owner reason. Record it and stop the execution portion; do not override Jev with a heuristic.

**REPLAN:** Jev selects `REPLAN`. Inspect whether the state packet is insufficient. Do not let another model invent an unregistered action.

**FAIL:** Jev returns any unauthored transition, arbitrary command/path, or the controller labels a fallback as `jev-live`.

---

## 6. Phase D — execute the selected read-only capability

The selected node must be:

- currently eligible;
- present in the mission;
- present in the capability registry;
- `mutation=none`;
- `auto_execute=true`;
- not marked as requiring human review.

Use the Echo Reflex read-only executor, not an ad-hoc substitute.

If a second `next --execute-readonly` invocation would create a fresh Jev decision rather than execute the already selected node, treat that as a controller ergonomics blocker. The preferred bounded fix is an explicit command that executes **one already-selected eligible read-only node by id** after re-running policy checks.

If that command must be added, its contract is:

```text
input: mission + current state + node_id
checks:
  node exists
  node is currently eligible
  capability exists
  mutation == none
  auto_execute == true
  no resource conflict
  arguments validate against capability declaration
action:
  execute only registered handler
output:
  PASS/FAIL + evidence + updated mission state
forbidden:
  arbitrary shell
  mutating capability
  bypass of eligibility/policy checks
```

Do not add a generic executor.

### Required evidence

For `project.read_current_state`:

- repo-relative path;
- byte count;
- SHA-256.

For `echo.topo_schedule`:

- exact registered argv;
- exit code;
- structured stdout;
- stderr.

Record the node PASS only in **mission state**. Do not write an Echo production gate.

---

## 7. Phase E — state advances deterministically

After the chosen root node passes, feed the updated mission state back into Echo Reflex.

Expected topology:

```text
read_state     inspect_echo
    \            /
     \          /
      validate_recipe
            |
        owner_gate
```

After one root passes, the other root remains eligible and should become the sole legal next node. That transition should therefore be selected **deterministically without another Jev spend**.

Execute the second read-only root using the same bounded mechanism.

After both root nodes PASS, `validate_recipe` becomes the sole legal transition.

Run it through registered capability:

```text
world.validate_recipe
recipe = recipes/morning_rainbow_bloom.v1.json
```

This recipe is a known compiler canary only. **Do not infer that Morning assets belong in Melusina's Study.**

Required result:

- World Compiler recipe validation returns exit 0;
- evidence is captured;
- no world bundle is applied;
- no editor is contacted.

Then the next node should be `owner_gate`.

Stop there. The canary has succeeded.

---

## 8. Phase F — author the real Study mission

Once A–E are green, create the next mission specification for the real Study pipeline.

Do not execute mutation yet.

Target mission id:

```text
melusinas_study_real_canary_v1
```

Goal:

> Stage `MelusinasStudyDecorated` into the canonical `L_MelusinasStudy` production path using existing Melodia Studio / GN builders, World Compiler/world-authoring owners, and UE evidence gates, while preserving one-editor/one-writer and stopping before unapproved artistic promotion.

### Discover before authoring

Verify actual canonical paths/names from repository state. Do not guess.

Specifically resolve:

- the current `MelusinasStudyDecorated` source path;
- relevant Melodia Studio builder/registry identities;
- existing decoration builders;
- the intended `L_MelusinasStudy` level path/owner;
- whether an existing World Compiler recipe already represents the Study;
- existing scene-context/evidence commands;
- any existing Study-specific branch/doc that is provenance rather than authority.

### Preferred mission shape

Use registered capabilities or add **handles to existing owners** where necessary:

```text
read canonical state
        |
inspect Study source + builder registry
        |
validate source identities
        |
[future mutation boundary]
        |
run registered Studio/GN/Hython source step if actually required
        |
validate produced artifacts
        |
compile/validate Study world recipe
        |
acquire ue_editor_writer
        |
scene-context BEFORE
        |
apply through existing World Compiler / Monolith owner
        |
scene-context AFTER
        |
runtime/static proof
        |
owner.visual_review
        |
STOP
```

In this PR, author only the graph and any missing **non-mutating handles/tests** needed to make it valid.

Do not automatically execute the future mutation boundary.

---

## 9. Astra planner contract for the real mission

When using Astra to plan/replan, give it:

### Inputs

- goal;
- relevant `CURRENT_STATE.md` slice;
- capability registry;
- mission schema;
- current mission state;
- observed evidence/failure;
- one-editor/one-writer rule;
- human visual promotion rule.

### Required output

A mission DAG containing only:

- registered capability ids;
- declared arguments;
- explicit dependencies;
- acceptance evidence;
- bounded `RETRY | REPLAN | HOLD` behavior.

### Reject planner output if it

- invents a capability;
- emits arbitrary shell as a mission action;
- creates a second World Compiler/editor bridge/state authority;
- bypasses a canonical owner;
- treats a model assertion as runtime evidence;
- removes the human visual gate.

Astra writes the score. It does not conduct every beat.

---

## 10. Jev decision policy

Use Jev only when deterministic code has produced **two or more legal, semantically meaningful next actions**.

Do not ask Jev:

- whether a file exists;
- whether JSON validates;
- whether a build/test passed;
- whether a resource lock is held;
- whether an allowlist contains an exact id;
- whether a dependency is complete.

Do ask Jev:

- which of several legal verification/actions is the best next move;
- whether the mission should HOLD for owner judgment;
- whether accumulated evidence indicates the current plan should REPLAN.

Every live call must preserve `source=jev-live` and confidence/distribution.

---

## 11. Evidence bundle

At the end, produce one concise machine-readable canary receipt with at least:

```json
{
  "schema": "melodia.echo_reflex_canary_receipt.v1",
  "mission_id": "...",
  "branch": "feat/echo-reflex-canary-20260922",
  "tests": {
    "echo_reflex": "PASS",
    "offline_contracts": "23/23 PASS"
  },
  "fail_closed_probe": "PASS",
  "jev": {
    "source": "jev-live",
    "selection": "...",
    "confidence": 0.0,
    "distribution": {}
  },
  "executed_readonly_nodes": [],
  "mutation_executed": false,
  "echo_gate_written": false,
  "next_mission_authored": true,
  "blockers": []
}
```

Use the existing audit/evidence conventions in the repository. Do not create a second status document just to store the receipt.

---

## 12. Definition of done

This execution brief is complete when:

1. Echo Reflex 11/11 unit tests PASS;
2. hosted/offline contract gate remains 23/23 PASS or better;
3. no-Jev parallel-root probe HOLDs exactly as designed;
4. one real Jev call selects only an authored legal transition with provenance;
5. both initial read-only root nodes execute through registered capability handlers;
6. `world.validate_recipe` executes after both roots PASS;
7. mission reaches `owner_gate` without touching Unreal;
8. the real `melusinas_study_real_canary_v1` DAG is authored from verified repo paths;
9. no mutation capability has been automatically executed;
10. PR #286 remains draft unless the owner explicitly promotes it.

Then report:

```text
ECHO REFLEX READ-ONLY CANARY: PASS
REAL STUDY MISSION: AUTHORED / NOT EXECUTED
NEXT HUMAN DECISION: approve first ue_editor_writer mutation canary or hold
```

Anything weaker should be reported precisely as HOLD / BLOCKED / REPLAN, never rounded up to PASS.
