---
name: melodia-conductor
description: Route Melodia tasks to the smallest correct repo skill and context surface so agents start work promptly instead of loading the whole project. Use when a task spans systems, when the right workflow is unclear, or when coordinating multiple agents/models/workstations.
---

# Melodia conductor

This is a **router**, not a new authority, task queue, or planning framework.

Its job is to answer one question quickly:

> What is the smallest true context + runbook that lets this task execute safely now?

## 0. Universal intake

Always begin with:

1. the owner's literal request;
2. `_AGENT_WORKING_AGREEMENT.md`;
3. `CURRENT_STATE.md` only when current status / blockers / evidence level matter;
4. exactly one primary skill or durable contract for the task.

Do not preload every project document.

If the owner already named the level/asset/system and the task is clear, route and act.

## 1. Skill router

| Task shape | Primary skill | Additional context only when needed |
|---|---|---|
| Environment art, Sea Above, PCG biomes, level composition, cameras, traversal readability, spatial polish | `melodia-world-builder` | `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`, `Docs/Production/PCG/README.md` |
| Blueprint graph/CDO gameplay mutation or runtime proof | `melodia-p0-loop` | `SYSTEM_MAP.md` / `DATA_FLOW.md` for the named owner seam |
| Persistence, restart, package, professor-facing P0 closure | `melodia-p0-closeout` | current evidence named by `CURRENT_STATE.md` |
| UI/dialogue/widget styling and visual polish | `melodia-ui-artist` | `melodia-design-system/tokens.json` |
| `.usf` / `.ush` shader source work in Rider | `melodia-shader-rider` | the consuming material/presentation contract only if needed |
| Static-mesh inventory / duplicates / naming proposal | `melodia-mesh-catalog` | read-only asset scope named by owner |

If no skill fits, use the relevant durable subsystem contract directly. **Do not invent a new skill/framework merely because routing is imperfect.** Add a durable skill only after repeated real tasks show the same specialized workflow.

## 2. Worldbuilding orchestration

For 3D tasks, the conductor delegates spatial perception and measured art direction to the world-builder skill immediately:

```text
owner intent
  -> scene_context_cycle.begin()
  -> read live transforms / bounds / counts / current camera
  -> MEASURED BUILD CARD
       camera + FOV/focal length
       player route dimensions
       reveal distance / clear zone
       transform deltas
       PCG bounds + instance budget
       exact before/after comparison view
  -> BUILDER edits the actual level
  -> scene_context_cycle.end()
  -> FALSIFIER checks measurements + spatial diff + captures
  -> owner judges viewport / gameplay
  -> provenance check
  -> done
```

For substantial environment work, “make it prettier / more epic / more lush / more readable” is not an executable brief by itself. The routed task must convert subjective intent into falsifiable spatial targets using actual live scene measurements.

Do not invent fake precision. Read the level first. If the owner did not provide numbers, choose provisional working targets, label them as such, and execute.

Do not substitute source-code inspection for scene perception when the editor is available.

## 3. Multiple agents/models

Multiple agents are temporary roles around one bounded deliverable, not permanent departments.

Preferred pattern:

```text
CONDUCTOR
  -> BUILDER
  -> FALSIFIER / REVIEWER
  -> optional CHEAP VERIFIER
  -> OWNER
```

Rules:

- one editor-mutating holder at a time;
- one primary owner for each changed asset/graph during the task;
- parallel agents may research/read separate surfaces but must not concurrently mutate the same graph/level;
- the reviewer does not start a redesign campaign;
- cheap models collect/read/verify; stronger models close genuinely ambiguous implementation blockers;
- do not ask two models to independently redesign the same thing and then create a reconciliation problem.

## 4. Prompt budget rule

Prefer **references over pasted lore**.

A task packet should usually contain:

```text
OBJECTIVE
named level / asset / system

CURRENT FACT
only the relevant excerpt/evidence

RUNBOOK
one selected skill / contract

LIVE CONTEXT
scene packet / graph export / failing test / source diff as appropriate

MEASURED TARGETS
for 3D: camera, distance, width, clearance, bounds, transform, density/count budget
for systems: exact input/output/state/evidence target

FINISH LINE
one falsifiable result
```

Do not paste the entire architecture into a prompt when the relevant skill already carries it.

## 5. Escalation rule

Escalate only when there is a real blocker:

```text
cheap/read agent reproduces or gathers
  -> bounded evidence packet
  -> stronger implementation agent closes ambiguity
  -> verifier checks the exact claim
```

Do not escalate because a task feels important. Importance does not require more agents; ambiguity does.

## 6. Done means the orchestra stops playing

A task is done when the requested change is made and the required evidence level is reached.

Do not create another plan, handoff, retrospective, or adjacent task merely because the pipeline worked.

Report:

- what changed;
- what measurable target it was aiming at;
- actual before/after result;
- what proved it;
- what the owner should look at/play if visual judgment remains.
