---
name: melodia-p0-closeout
description: Current professor-facing P0 closure runbook for BS_GodFile UE5.8 — protect the proven First Dream / Sea Above loop, harden persistence/idempotency/package proof, and do not revive stale August blockers.
---

# Melodia P0 closeout — current authority

**Authority date:** 2026-09-04

Read first:

1. `AGENT_START_HERE.md`
2. `MELODIA_TECHNICAL_VERTICAL_SLICE.md`
3. `CURRENT_STATE.md`
4. `_VERTICAL_SLICE_SCOPE.md`
5. `TODO.md`

Older August P0 plans and handoffs are historical evidence. They are not the current task list.

## Current proven baseline

The current evidence in `Docs/Evidence/P0_EXPLORATION_WARDROBE_GLIDE_PORTAL_PROBE_2026-08-31.md` records the 2026-09-01 closeout checks:

- music/challenge completion reaches the canonical reward path;
- Wardrobe grants and equips the Accessories item;
- Glide capability becomes available through the existing traversal authority;
- the visible portal/route transitions from locked to unlocked;
- canonical save was written;
- the UnrealEditor process was fully restarted;
- canonical load returned `LOADED_NARRATIVE_RESTORED`;
- Wardrobe state restored after restart;
- `Melodia.Wardrobe` 6/6 passed;
- `Melodia.P0` 4/4 passed;
- `Melodia.Quest.Shorewake` 1/1 passed;
- traversal capability contract 1/1 passed;
- `BP_Starskiff_MK2` boarding and movement were exercised in PIE.

Do not regress this to the old “Phase 1 content is inert” or “Starskiff is only a shell” interpretation.

## Current closure target

The remaining high-value proof is:

```text
Outfit
 → Starskiff / exploration
 → Encounter
 → Phoenix command
 → Rhythm phrase
 → Convergence consequence
 → Reward
 → Save
 → Quit
 → Relaunch
 → Load same durable state
 → Load again
 → no duplication / drift
 → packaged execution
```

PR #54 / Issue #51 contain persistence work and history, but are not automatically current/merge-ready. Reapply or extract against current `main` rather than merging stale work wholesale.

## Scope guard

- Do not hand-edit `.uasset`.
- One Unreal Editor / one mutating MCP holder.
- Do not create a second save, wardrobe, traversal, combat, rhythm, or UI authority.
- Do not claim packaged proof from PIE/source proof.
- Do not use deleted `_TASK_QUEUE.md` / `_SESSION_HANDOFF.md`.
- Do not use `_ROADBLOCKS_2026-07-31.md` as current status.
- Before declaring laptop work absent, read `Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`.
- Before declaring a visual board absent, read `Docs/Art/VISUAL_REFERENCE_INDEX.md`.

## Evidence levels

Always label the strongest evidence honestly:

1. **SOURCE-BUILT** — code/assets exist and compile.
2. **LIVE-PROVEN** — observed in intended PIE/runtime.
3. **RESTART-PROVEN** — survives full save → process exit → relaunch → load.
4. **PACKAGED-PROVEN** — reproduced in packaged Development build.

A later level does not follow automatically from an earlier one.

## Current work order

1. Protect the existing First Dream / Sea Above route from unrelated feature churn.
2. Re-run / harden repeat-load and idempotency checks.
3. Trace durable vs derived Starskiff and Convergence state before extending schema.
4. Audit restore mutation ordering and duplicate rebuild side effects.
5. Run full process restart proof on the current baseline.
6. Run packaged-build proof.
7. Capture a stable professor-facing demo and backup recording.

## Review-safe presentation

Prefer one reliable 5–10 minute route:

```text
environment
  → music/rhythm
  → reward
  → Wardrobe equip
  → Glide/world access
  → Sea Above / Starskiff if stable
  → checkpoint/save
  → explain or show recorded restart proof
```

The milestone is closure, not expansion.
