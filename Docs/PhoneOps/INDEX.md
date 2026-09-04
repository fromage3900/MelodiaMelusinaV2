# Phone Ops Index

**Current authority:** 2026-09-04

Front door for driving **MelodiaMelusinaV2** from iOS / mobile agents / remote workstation control.

> **Do not start from the old August PhoneOps queues.** Read the current project discovery contract first.

## Start here

1. [`../../AGENT_START_HERE.md`](../../AGENT_START_HERE.md) — freshness and branch-discovery rules.
2. [`../../MELODIA_TECHNICAL_VERTICAL_SLICE.md`](../../MELODIA_TECHNICAL_VERTICAL_SLICE.md) — what the playable slice actually proves.
3. [`../../CURRENT_STATE.md`](../../CURRENT_STATE.md) — present-tense project state.
4. [`../../TODO.md`](../../TODO.md) — current production queue.
5. [`../Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`](../Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md) — committed laptop/recovery work not necessarily on `main`.
6. [`../Art/VISUAL_REFERENCE_INDEX.md`](../Art/VISUAL_REFERENCE_INDEX.md) — canonical image/reference-board discovery.
7. [`AGENT_LANE_HANDOFF.md`](AGENT_LANE_HANDOFF.md) — lightweight branch handoff format.
8. [`REMOTE_WSL_AGENT_STACK_2026-08-25.md`](REMOTE_WSL_AGENT_STACK_2026-08-25.md) — remote stack mechanics only; historical status claims inside are subordinate to current discovery docs.
9. [`MOBILE_LANES.md`](MOBILE_LANES.md) — phone vs PC ownership.
10. [`JCODE_SWARM_PIPELINE.md`](JCODE_SWARM_PIPELINE.md) — jcode mechanics; use current project authority above for task selection.

## Current mobile interpretation

The First Dream / Sea Above runtime is **not “still open because nothing works.”**

September evidence records a functioning chain across music/challenge → reward → Wardrobe equip → Glide/world unlock, plus canonical save → full process restart → wardrobe restore. Starskiff boarding and movement have also been exercised.

What remains open is **closure quality**: deeper persistence/idempotency, current packaged proof, and professor-facing stability.

## Multi-workstation rule

Before saying “I cannot find the laptop work”:

- inspect `Docs/Production/LAPTOP_WORK_DISCOVERY_2026-09-04.md`;
- compare `main` with `recovery/laptop-main-20260904`;
- inspect relevant `collab/laptop/*` branches if needed.

Never merge the recovery branch wholesale: it also contains broad export/quarantine deletions.

## Visual-reference rule

Before saying a reference board does not exist, use `Docs/Art/VISUAL_REFERENCE_INDEX.md`.

That index explicitly distinguishes committed images, text-only production sheets, branch-only sources, referenced-but-uncommitted images, and planned/missing boards.

## Historical PhoneOps documents

The following remain useful for mechanics/history, but they are **not current project authority**:

- `PHONE_ARTIST_BRIDGE_HANDOFF_2026-08-11.md`
- `PIE_2026-08-11.md`
- `HIGHEST_LEVERAGE_NOW.md`
- `NORTH_STAR.md`
- `BACKLOG.md`
- `RECENT_STUDY.md`
- `SCRATCHPAD.md`

Use them only after the current front door.

## Safe phone workflow

For a focused agent request:

```text
Read AGENT_START_HERE.md first.
Then read the exact current subsystem or branch-discovery document for this task.
Do not infer current project state from dated handoffs.
Check non-main laptop/recovery branches before declaring committed work absent.
Make one scoped change, validate it, and report the exact branch + SHA.
```

## Red lines

- Do not edit human-owned composition without explicit owner direction.
- Do not write into `Content/_PROJECT/`.
- Do not publish externally without explicit approval.
- Do not push broad LFS/binary batches from a phone lane.
- Do not rebuild JRPG, save, Wardrobe, traversal, rhythm, or UI authority.
- Do not promote stale prose over current source/evidence.
