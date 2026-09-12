# Melodia Agentic Studio Operating Model

**Status:** CANONICAL OPERATING CONTRACT  
**Owner:** Brennan Shepherd  
**Purpose:** Define how AI agents, workstations, Git, evidence, and knowledge tools cooperate without replacing owner judgment or turning agent activity into fake production progress.

This document does **not** create a task queue or status surface.

- `CURRENT_STATE.md` owns **all current status, priorities, blockers, and open work**.
- `SYSTEM_MAP.md` + `DATA_FLOW.md` own runtime architecture/ownership explanations.
- durable subsystem contracts/specs/reference bibles own long-lived rules.
- PR/commit bodies own session narrative and handoff context.
- dated plans, handoffs, scorecards, and session notes are historical only and must not be recreated as a parallel authority.

## 1. Studio principle

Melodia is a solo-authored art/game project using AI to approximate parts of studio infrastructure that a solo student does not have: repo maintenance, repetitive implementation, QA preparation, research, test generation, evidence organization, and bounded technical investigation.

AI is infrastructure, not artistic authority.

The owner chooses the artistic target, gameplay intent, acceptable visual result, and final production decision. Agents may propose, implement, test, organize, and falsify; they do not turn confidence into truth.

```text
OWNER SETS TARGET
  -> appropriate agent gathers / executes
  -> tests, build, or runtime establish what is real
  -> stronger model handles genuine ambiguity / blockers
  -> owner reviews visual / gameplay result
  -> evidence is captured
  -> only then is the milestone promoted
```

## 2. Capability routing

Do not default to the most expensive model. Route by task shape and demonstrated reliability.

```text
cheap endurance model
  -> archaeology, repetitive edits, docs normalization, validation,
     manifests, test setup, evidence packets, branch comparison

mid/high reasoning model
  -> bounded implementation, difficult refactors, subtle debugging,
     architecture review

frontier closer
  -> genuine P0 deadlock, ambiguous cross-system failure,
     release-critical falsification, problems cheaper agents failed to close
```

Provider/model names change. The durable rule is capability routing, not vendor loyalty.

Prefer:

```text
CHEAP AGENT gathers / reproduces / executes
  -> EVIDENCE PACKET
  -> STRONGER AGENT decides / closes hard remainder
  -> CHEAP AGENT verifies / cleans up
```

## 3. Mobile is the control room

Mobile work is for direction and delegation, not pretending a phone can prove Unreal runtime state.

Good mobile-delegated work includes current Git/PR/issue inspection, bounded source/doc drift repair, exact PC command preparation, non-GUI checks, branch/LFS inspection, and evidence preparation.

A successful mobile shift reduces workstation startup friction and leaves a concise next owner action in the conversation / PR body rather than generating a new handoff document.

## 4. Workstation truth hierarchy

### Interactive Unreal workstation

Truth machine for editor/runtime behavior, packaged behavior, save/restart proof, gameplay feel, materials/lookdev, topology/deformation, animation, camera-scale readability, performance, and final owner acceptance.

### Home PC / long-job worker

For explicitly assigned render, bake, package, compile, or long-running jobs. Worker mode must not invent unrelated edits.

### ASUS Nitro / auxiliary DCC workstation

For Blender/Geometry Nodes, secondary DCC work, batch processing, investigation, and explicit auxiliary lanes. Durable contract: `LAPTOP_PROCEDURAL_LANE_2026-09-11.md`. It is not runtime authority.

### Phone

Production control room: specify, delegate, review, approve/reject direction, and prepare workstation execution.

## 5. Evidence beats activity

Commits, messages, plans, agent runtime, and Markdown PASS labels are not proof that the game works.

```text
SOURCE-BUILT
  -> LIVE-PROVEN
  -> RESTART-PROVEN
  -> PACKAGED-PROVEN
```

Never promote a claim above the evidence actually captured. For visual assets, evaluate in real production context at authored scale/camera and capture the result before promoting the milestone.

Unreal/runtime/art output is the lie detector.

## 6. Smallest decisive milestone

Agents should close the smallest production unit that produces a meaningful yes/no result: one reproduced blocker, build proof, scale test, silhouette decision, integration capture, restart proof, packaged proof, or bounded PR.

Avoid broad cleanup, speculative frameworks, TODO forests, unbounded research sweeps, and "while we're here" expansion.

## 7. Stop rules

An agent must stop and report rather than expand when current source contradicts the task premise, a semantic conflict touches authority, runtime-only judgment is required, owner visual judgment is required, credentials/licenses/hardware are required, the next step would create a second authority, the requested evidence level is reached, or one reproduced blocker explains failure.

Good blocked result:

```text
BLOCKER
exact command / file / runtime action
exact first real error or missing evidence
smallest next action
STOP
```

Do not compensate for uncertainty by producing more prose.

## 8. Git and documentation are infrastructure, not the product

Run existing health checks first. If Git is healthy, leave it alone and return to production.

Do not reconstruct history for curiosity, merge branches merely to reduce count, delete intentional workstation lanes, treat every stale document as a task, or create another health report when tooling already answers the question.

Documentation doctrine:

```text
What is true now?        -> CURRENT_STATE.md
How does runtime work?   -> SYSTEM_MAP.md / DATA_FLOW.md
What rules persist?      -> durable contract / spec / runbook
What should it look like?-> reference / bible
What did we learn?       -> research
What happened before?    -> Git history / clearly HISTORICAL stub
```

There is no active-plan-document category. If a task changes current status, update `CURRENT_STATE.md` in the same change set.

## 9. Owner authority and artistic authorship

Brennan retains final authority over visual identity, composition, environment design, character presentation, gameplay feel, musical identity, scope, portfolio selection, and whether a generated/modified asset is actually better.

Do not redesign approved visuals, replace approved material parents, or reinterpret established aesthetics unless explicitly asked.

## 10. Preferred agent brief

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

For expensive models, reduce ambiguity first.

## 11. PC landing-strip contract

A remote/mobile agent may do every safe prerequisite that does not require owner/runtime/art judgment, then leave one concise workstation handoff in the conversation or PR body.

It may fetch refs, inspect divergence, reconcile safe non-semantic drift, run static/non-GUI checks, inspect LFS signals, locate exact commands, and prepare evidence capture names/paths.

It may not claim runtime PASS from source reasoning, redesign the subsystem, expand milestones, merge gated work without evidence, or replace owner judgment.

## 12. Definition of productive agent work

Productive agent work reduces uncertainty or produces verifiable project value: fewer blockers, passing tests/builds, reproduced failures, bounded integrated features, stronger art/runtime captures, useful evidence, less workstation friction, or safely landed canonical changes.

Agent motion is not automatically progress.

**The project is judged by the game, the art, the build, and the captured evidence—not by how many agents ran or how many commits/documents were generated.**

## 13. Obsidian / knowledge-browser rule

Obsidian is approved as an **optional human navigation layer over the repository Markdown**.

Recommended setup:

- open the repository root (or a read-focused copy of its Markdown tree) as the vault;
- keep Git files as canonical; Obsidian does not own project truth;
- prefer links/backlinks, search, local graph, bookmarks, and tags for discovery;
- do not create duplicate Obsidian-only status notes, dashboards, task queues, or handoffs;
- do not treat graph centrality as authority — the authority rules above still apply;
- keep `.obsidian/` machine-local unless a deliberately reviewed shared configuration is ever needed.

The value of Obsidian is **finding and relating durable knowledge**, not generating another knowledge base beside Git.
