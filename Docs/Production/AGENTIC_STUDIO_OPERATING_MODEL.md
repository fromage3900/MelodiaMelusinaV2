# Melodia Agentic Studio Operating Model

**Status:** CANONICAL OPERATING CONTRACT  
**Owner:** Brennan Shepherd  
**Purpose:** Define how AI agents, workstations, Git, and evidence cooperate without replacing owner judgment or turning agent activity into fake production progress.

This document does **not** create a second task queue. `CAPSTONE_NOW.md` owns immediate priority. `AGENT_START_HERE.md` owns discovery. This file defines how assigned work should be executed.

## 1. Studio principle

Melodia is a solo-authored art/game project using AI to approximate parts of studio infrastructure that a solo student does not have: repo maintenance, repetitive implementation, QA preparation, documentation, research, test generation, evidence organization, and bounded technical investigation.

AI is infrastructure, not artistic authority.

The owner chooses the artistic target, gameplay intent, acceptable visual result, and final production decision. Agents may propose, implement, test, organize, and falsify; they do not turn confidence into truth.

Core loop:

```text
OWNER SETS TARGET
  → cheap/appropriate agent gathers + executes
  → tests/build/runtime establish what is real
  → stronger model handles genuine ambiguity/blockers
  → owner reviews visual/gameplay result
  → evidence is captured
  → only then is the milestone promoted
```

## 2. The cheapest reliable model should do the most work

Do not default to the most expensive model.

Route by task shape and demonstrated reliability:

```text
cheap endurance model
  → archaeology, repetitive edits, docs normalization, validation,
    manifests, test setup, evidence packets, branch comparison

mid/high reasoning model
  → bounded implementation, difficult refactors, subtle debugging,
    architecture review

frontier closer
  → genuine P0 deadlock, ambiguous cross-system failure,
    release-critical falsification, problems cheaper agents failed to close
```

Provider/model names change. The durable rule is capability routing, not loyalty to a vendor.

Empirical project performance outweighs leaderboard prestige. A cheap model that survives a long Melodia shift coherently and produces verifiable useful work is a trusted workhorse until evidence says otherwise.

Use this pattern whenever practical:

```text
CHEAP AGENT gathers / reproduces / executes
  → EVIDENCE PACKET
  → EXPENSIVE AGENT decides / closes hard remainder
  → CHEAP AGENT verifies / documents / cleans up
```

Do not pay a frontier model to rediscover repository context a cheaper model can prepare safely.

## 3. Mobile is the control room

Mobile work is for direction and delegation, not pretending a phone can prove Unreal runtime state.

Good mobile-delegated work:
- inspect current Git/PR/issue state;
- reconcile bounded docs/source drift;
- prepare exact PC commands;
- run non-GUI tests and static validation;
- inspect branches and LFS signals;
- generate evidence checklists from current source;
- perform repetitive safe edits;
- prepare a `WHEN YOU SIT DOWN AT THE PC` handoff.

A successful mobile agent shift should reduce workstation startup friction.

Preferred landing-strip output:

```text
WHEN YOU SIT DOWN AT THE PC
1. pull/switch to the named branch
2. run the exact build/test
3. observe the named pass signal
4. capture the named evidence
5. if failure: preserve the first real error and stop expansion
```

The goal is that the owner reaches Unreal/art judgment quickly instead of spending the first hours reconstructing agent/Git history.

## 4. Workstation truth hierarchy

### Interactive Unreal workstation

The interactive UE workstation is the truth machine for:
- editor/runtime behavior;
- packaged-build behavior;
- save/restart proof;
- gameplay feel;
- material/lookdev judgment;
- topology/deformation judgment;
- animation quality;
- camera-scale readability;
- performance/profiling;
- final owner acceptance.

### Home PC / long-job worker

Use for explicitly assigned render, bake, packaging, compile, or long-running jobs. Do not let worker mode invent unrelated project edits.

### ASUS Nitro / auxiliary workstation

Use for Blender/Geometry Nodes, secondary DCC work, batch processing, investigation, and explicitly assigned auxiliary lanes. It is not automatically runtime authority.

### Phone

Use as production control room: specify, delegate, review summaries, approve/reject direction, and prepare PC execution.

## 5. Evidence beats agent activity

Commits, messages, generated plans, agent runtime, and Markdown PASS labels are not proof that the game works.

Use the repository evidence ladder:

```text
SOURCE-BUILT
  → LIVE-PROVEN
  → RESTART-PROVEN
  → PACKAGED-PROVEN
```

Never promote a claim above the evidence actually captured.

Examples:
- code exists + compiles statically = source-built at best;
- editor interaction observed = live-proven;
- full process exit/relaunch preserves required state = restart-proven;
- packaged executable repeats the required behavior after process restart = packaged-proven.

For visual assets, source files or generated meshes are not final proof. Put the asset in the actual production context, evaluate it at authored scale and the real gameplay camera/FOV, and capture the result before promoting the milestone.

Unreal/runtime/art output is the lie detector.

## 6. Smallest decisive milestone

Agents should close the smallest production unit that produces a meaningful yes/no result.

Prefer:
- one reproduced blocker;
- one build proof;
- one scale test;
- one silhouette decision;
- one integration capture;
- one restart proof;
- one packaged proof;
- one clearly bounded PR.

Avoid:
- broad cleanup because adjacent files look untidy;
- new frameworks while proving an existing one;
- speculative architecture during a validation pass;
- TODO forests;
- research sweeps without a concrete blocker;
- "while we're here" expansion.

If a task can be rejected independently, it is easier to delegate safely.

## 7. Stop rules

An agent must stop and report rather than expand when:
- current source contradicts the task premise;
- a semantic merge conflict touches gameplay authority;
- a runtime-only decision cannot be established remotely;
- owner visual judgment is required;
- a missing credential/license/payment/hardware action is required;
- the next step would create a second authority for an existing system;
- the task has reached its requested evidence level;
- one reproduced blocker explains the failure.

A good blocked result is:

```text
BLOCKER
exact command / file / runtime action
exact first real error or missing evidence
smallest next action
STOP
```

Do not compensate for uncertainty by producing more prose.

## 8. Git is infrastructure, not the product

Run the repository's existing Git/front-door health checks first.

If Git is healthy, leave it alone and return to production.

Do not:
- reconstruct history for curiosity;
- merge branches merely to reduce branch count;
- delete intentional workstation lanes;
- treat every stale document as a task;
- create another Git health report when existing tooling already answers the question.

Branches are work/evidence; `main` is durable canon after accepted integration.

Agent work is not complete until its meaningful result is pushed, reviewable, and the receiving workstation can consume it safely.

## 9. Owner authority and artistic authorship

Agents may execute technical/art-production instructions, but Brennan retains final authority over:
- visual identity;
- composition;
- environment design;
- character presentation;
- gameplay feel;
- musical identity;
- scope;
- what is portfolio-worthy;
- whether a generated/modified asset is actually better.

Do not "fix" reference art, redesign approved visuals, replace an approved material parent, or reinterpret an established aesthetic unless explicitly asked.

Technical correctness does not override owner art direction.

## 10. Preferred agent brief

A strong task brief should state:

```text
OBJECTIVE
one measurable finish line

SOURCE OF TRUTH
current main + named issue/PR/files/evidence

ALLOWED
specific edits/tests/investigation

FORBIDDEN
adjacent systems and redesigns

EVIDENCE REQUIRED
what would make the claim real

STOP CONDITIONS
success or one reproduced blocker

FINAL RESPONSE
what changed, validation performed, first owner action
```

For expensive models, always reduce ambiguity first. Do not spend premium quota on "look around and improve things."

## 11. PC landing-strip contract

Before a planned owner workstation session, a remote/mobile agent may be assigned a landing-strip pass.

Its job is to do every safe prerequisite that does **not** require owner/runtime/art judgment, then leave exactly one concise workstation handoff.

A landing-strip agent may:
- fetch latest `main` and target branch;
- inspect divergence;
- reconcile safe non-semantic drift;
- run static/non-GUI checks;
- inspect LFS/asset availability signals;
- locate exact build/test/package commands;
- prepare evidence capture names/paths.

It may not:
- claim runtime PASS from source reasoning;
- redesign the target subsystem;
- expand into another milestone;
- merge a gated PR without its required evidence;
- replace the owner's visual/gameplay judgment.

Success means the first owner workstation action is concrete, preferably a build/test/open-and-judge action rather than Git archaeology.

## 12. Definition of productive agent work

Productive agent work reduces uncertainty or produces verifiable project value.

Good outputs:
- fewer real blockers;
- passing tests/builds;
- a reproduced failure;
- an integrated bounded feature;
- a stronger art/runtime capture;
- a clean evidence packet;
- less PC setup friction;
- a safely landed canonical change.

Agent motion is not automatically progress.

**The project is judged by the game, the art, the build, and the captured evidence—not by how many agents ran or how many commits were generated.**
