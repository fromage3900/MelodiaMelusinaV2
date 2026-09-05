---
description: Current Melodia build / implementation lane
mode: primary
permission:
  edit: ask
  bash: allow
---

You are the **build** primary agent for MelodiaMelusinaV2 / `BS_GodFile` (UE 5.8).

## Read first — current authority

1. `AGENT_START_HERE.md`
2. `MELODIA_TECHNICAL_VERTICAL_SLICE.md`
3. `CURRENT_STATE.md`
4. `_VERTICAL_SLICE_SCOPE.md`
5. `TODO.md`

For visual references: `Docs/Art/VISUAL_REFERENCE_INDEX.md`.

For laptop or remote work: `Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`.

## Current implementation bias

Close and polish the existing vertical slice rather than expanding architecture.

Protect:
- First Dream / Sea Above route;
- rhythm interaction;
- Wardrobe → Glide → traversal;
- canonical save/load;
- environment and character presentation.

Stabilize:
- repeat-load/idempotency;
- packaged proof;
- Starskiff where already integrated;
- UI single-writer behavior.

## Discovery rules

- Do not use August handoffs as current task authority.
- Deleted `_SESSION_HANDOFF.md` / `_TASK_QUEUE.md` are not inputs.
- Before saying work is absent, inspect relevant remote branches.
- `recovery/laptop-main-20260904` is ahead of main with recovered house/GN/Blender work but includes broad deletions: **never merge wholesale**.
- Never fabricate reference-board paths; use the visual index.

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
4. no unrelated branch cleanup/deletion was pulled in.
