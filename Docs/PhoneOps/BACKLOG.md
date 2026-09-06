# Backlog (Now / Next / Later)

Simple queue for phone agents. Prefer updating this file over inventing parallel TODO files.

**Authority (2026-08-25):** [`PROJECT.md`](../../PROJECT.md) · P0 closeout
[`../Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md`](../Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md) ·
playbook [`../P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md`](../P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md).

**Live standing (read before acting):** last row per gate id in `Saved/gate_ledger.json`
(`Docs/P0_TASK_LEDGER.json` carries scope notes + `as_of`). A dated handoff below is memory,
not orders — verify against the ledger first. Session start: `python Tools/project_state.py --view session_start`.

Career sendoffs (downstream): [`../Career/RECRUITER_SENDOFFS_2026-08-25.md`](../Career/RECRUITER_SENDOFFS_2026-08-25.md).

## Now

### P0 — Ship Melodia (live proof — prefer over R&D)

0. **FAMILY LOCKS — RHYTHM + QUILLSCRIPT WORKED**. Do not reopen without evidence. Locks recorded in [RHYTHM…](../Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md) · [QUILL…](../Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md) — confirm standing in `Saved/gate_ledger.json` (last row per gate wins) before citing them.
1. **Smaller scope — certification only** ([2026-09-06 plan](../P0_INTEGRATION_EXECUTION_PLAN_2026-09-06.md)): a current closed-editor package + one uninterrupted owner-played golden run. No new authorities — no dungeon coordinator/persistence, audio, HUD, or PCG-framework additions. Quarantines stay quarantined.
2. **Proof backlog (existing paths only):** Starskiff board/move/disembark real-input PIE; music-key → dock Glide transition; dungeon probe sequence (`FirstDungeonGate` → seed run → typed result → exit once → save/restart); lookdev/PCG extension-only pass.
3. **Claireon:** **LIVE** (owner 2026-09-06 — MCP traffic in the editor log; the PARKED/C1076 claim was stale). Still keep it off the P0 critical path. Monolith stays.

### P1 — Recruiter sendoffs (NVIDIA withdrawn)

4. **Send OpenCode first** — paste from [RECRUITER_SENDOFFS…](../Career/RECRUITER_SENDOFFS_2026-08-25.md) §1.
5. Certain Affinity → Velan → Infold campus (Oct 31) → Nous optional (corrected evidence only).
6. **Do not send NVIDIA.**

## Next

1. Validate material-system repairs via audits — no master rewrites.
2. Website lane: keep `_github_deploy/` until `my-site-clean/` is explicitly promoted.
3. Relationship building after OpenCode is out: UE Toronto meetup, MCP Dev Summit Toronto (Oct 5–6).
4. Optional P3: Nemotron background only if it does not take the single editor from P0.

## Later / Backlog

- Zen Tier B/C modules + genome → `.world.json` export.
- Material Maker / Houdini phases.
- Ornament store screenshots + Gumroad (`store_live` stays false until then).
- Pillar hero captures when editor is free after P0.
- Claireon work stays off the P0 critical path.

## Explicitly not Now

- Sakura level composition / hero placement (human-owned).
- Deletes, master architecture rewrites, external publish without approval.
- Writes under `Content/_PROJECT/`.
- NVIDIA applications.
- Putting Claireon MCP work on the P0 critical path.
- Citing withdrawn MATH 98.8% figures in any outgoing draft.

## How to update from phone

```text
Reconcile Docs/PhoneOps/BACKLOG.md with PROJECT.md and the Aug 24 P0 closeout.
Move finished items out; do not add speculative work. Commit + PR.
```

First command before any edit: `python Tools/project_state.py --view session_start`
(tip + latest gate rows + staleness flags — this output outranks dated handoffs).
