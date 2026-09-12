---
name: melodia-p0-closeout
description: Professor-facing P0 closure runbook for BS_GodFile UE5.8 — protect the proven First Dream / Sea Above loop, harden persistence/idempotency/package proof, and do not revive stale blockers.
---

# Melodia P0 closeout — durable runbook

Read `CURRENT_STATE.md` first. It is the only authority for current status, priorities, blockers, and next work. This skill defines **how** to close P0 work safely; it does not maintain a task queue.

## Baseline rule

Do not regress newer evidence to an older snapshot. Before claiming a system is absent, broken, or unproven, inspect current source plus the evidence named by `CURRENT_STATE.md`.

The established vertical-slice ownership remains:

```text
Quill / narrative truth
  -> Phoenix / JRPG action and result
  -> Melodia rhythm execution
  -> Wardrobe / traversal capability
  -> world consequence
  -> canonical save
```

Do not create parallel save, combat, rhythm, Wardrobe, traversal, UI, or narrative authorities while closing the loop.

## Closeout method

For any P0 closure task:

1. identify the exact current claim in `CURRENT_STATE.md`;
2. inspect the current source/evidence rather than old handoffs;
3. reproduce the smallest missing proof or blocker;
4. change only the owner system required to close it;
5. rerun the narrowest relevant test/runtime proof;
6. label the achieved evidence level honestly;
7. update `CURRENT_STATE.md` in the same change if project status changed;
8. stop when the requested evidence level is reached.

Issue/PR history may contain useful implementation work, but stale branches are never merge-ready merely because they once targeted the same problem. Extract or reapply bounded changes against current `main`.

## Scope guard

- Do not hand-edit `.uasset` files.
- One Unreal Editor / one mutating MCP holder.
- Never use deleted `_TASK_QUEUE.md` / `_SESSION_HANDOFF.md` or old roadblock files as current status.
- For laptop/DCC work, use `Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md` plus `Docs/Production/BRANCH_WORKSTATION_POLICY.md`.
- For visual boards, use `Docs/Art/VISUAL_REFERENCE_INDEX.md`.
- Do not claim packaged proof from PIE or source proof.
- Do not expand a closure pass into framework work, branch cleanup, or speculative redesign.

## Evidence levels

Use the repository ladder without collapsing levels:

1. **SOURCE-BUILT** — code/assets exist and compile.
2. **LIVE-PROVEN** — observed in intended PIE/runtime.
3. **RESTART-PROVEN** — survives save -> full process exit -> relaunch -> load.
4. **PACKAGED-PROVEN** — reproduced in the packaged Development build.

A later level never follows automatically from an earlier one.

## Persistence/idempotency proof shape

When persistence is the active closure target, the decisive chain is conceptually:

```text
owned/equipped state
  -> traversal / encounter / rhythm consequence
  -> durable reward/checkpoint
  -> save
  -> quit process
  -> relaunch
  -> load exact durable state
  -> load again
  -> no duplication / drift
```

Before extending a save schema, separate durable ownership from derived/presentation state and audit restore mutation ordering.

## Review-safe presentation

A professor/recruiter proof should favor one reliable route over feature breadth. Show the authored environment, one meaningful music/rhythm interaction, a visible consequence or capability, and only the persistence/package evidence that is actually proven.

The milestone is **closure and captured proof**, not the number of systems touched.