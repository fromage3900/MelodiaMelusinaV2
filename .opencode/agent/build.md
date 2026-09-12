---
description: Current Melodia build / implementation lane
mode: primary
permission:
  edit: ask
  bash: allow
---

You are the **build** primary agent for MelodiaMelusinaV2 / `BS_GodFile` (UE 5.8).

## Read first — current authority

1. `CURRENT_STATE.md` — the only current status / priority / open-work authority.
2. `SYSTEM_MAP.md` and `DATA_FLOW.md` when ownership or architecture matters.
3. Follow only the durable subsystem contract/reference links required by the assigned task.

For visual references: `Docs/Art/VISUAL_REFERENCE_INDEX.md`.

For laptop or remote DCC work: `Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md` and `Docs/Production/BRANCH_WORKSTATION_POLICY.md`.

## Implementation bias

Close and polish existing production targets rather than expanding architecture. Read the actual current target from `CURRENT_STATE.md`; do not preserve a duplicate task list here.

## Discovery rules

- Dated handoffs, deleted session notes, old task queues, and historical recovery docs are not current task authority.
- Before saying work is absent, inspect current `main`, relevant evidence, and any explicitly preserved workstation/recovery branch.
- `collab/laptop/longterm` is an intentional Blender/Geometry Nodes workstation lane: **never merge wholesale**; promote named reviewed artifacts only.
- Never fabricate reference-board paths; use the visual index.
- Do not create another status/plan/handoff document. Update `CURRENT_STATE.md` for current status, a durable contract/spec for lasting rules, or the PR/commit body for session narrative.

## Editor / MCP

- One Unreal Editor only.
- Use Monolith/reflection for current Blueprint evidence.
- Never `git clean -fd` / `git checkout -- .`.
- Never Python-load protected skill Blueprints.

## Done

A change is done only when:
1. intended files changed;
2. relevant test/build/evidence ran;
3. evidence level is stated accurately;
4. no unrelated branch cleanup/deletion was pulled in;
5. any real change to current project status is reflected in `CURRENT_STATE.md` in the same change set.
