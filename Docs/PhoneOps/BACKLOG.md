# Backlog (Now / Next / Later)

Simple queue for phone agents. Prefer updating this file over inventing parallel TODO files.

**Authority (2026-09-02):** [`Docs/P0_TASK_LEDGER.json`](../P0_TASK_LEDGER.json) ·
[`../Handoffs/P0_CLOSEOUT_TODAY_2026-09-01.md`](../Handoffs/P0_CLOSEOUT_TODAY_2026-09-01.md) ·
phone snapshot [`../Handoffs/PHONE_PARTY_TRICK_2026-09-02.md`](../Handoffs/PHONE_PARTY_TRICK_2026-09-02.md) ·
Aug 24 plan (historical) [`../Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md`](../Handoffs/MELODIA_CONVERGENCE_CLOSEOUT_AND_P0_PLAN_2026-08-24.md) ·
playbook [`../P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md`](../P0_CLOSEOUT_TEST_PLAYBOOK_2026-08-24.md).

Career sendoffs (downstream): [`../Career/RECRUITER_SENDOFFS_2026-08-25.md`](../Career/RECRUITER_SENDOFFS_2026-08-25.md).

## Now

### P0 — Ship Melodia (certify — prefer over R&D)

0. **FAMILY LOCKS — RHYTHM + QUILLSCRIPT WORKED**. Do not reopen without evidence. [RHYTHM…](../Handoffs/RHYTHM_GAME_LOCKED_2026-08-12.md) · [QUILL…](../Handoffs/QUILLSCRIPT_LOCKED_2026-08-12.md).
1. **Task ledger:** all eight active P0 gates are **pass** in [`Docs/P0_TASK_LEDGER.json`](../P0_TASK_LEDGER.json) (Sep 1). Do not rebuild those systems.
2. **Echo ledger drift (PC):** `Saved/gate_ledger.json` may still disagree with the task ledger — record missing PASS rows via the normal recorder (`wardrobe_equip_roundtrip`, `wardrobe_gameplay_hook`, `music_world_key`, and any other missing rows). Cloud VMs with no ledger file will report OPEN; that is not a rebuild request. See [PHONE_PARTY_TRICK…](../Handoffs/PHONE_PARTY_TRICK_2026-09-02.md).
3. **Shipping closeout (PC):** focused pre-package checks → current Win64 package → uninterrupted golden run → fresh `package_launch` row. Aug 13–14 historical rows are not current certification. Playbook: [P0_CLOSEOUT_TODAY…](../Handoffs/P0_CLOSEOUT_TODAY_2026-09-01.md).
4. **Claireon:** **PARKED** (disabled in `.uproject` for C1076 PCH). Do not re-enable on the critical path. Monolith stays.

### P1 — Recruiter sendoffs (NVIDIA withdrawn)

5. **Send OpenCode first** — paste from [RECRUITER_SENDOFFS…](../Career/RECRUITER_SENDOFFS_2026-08-25.md) §1.
6. Certain Affinity → Velan → Infold campus (Oct 31) → Nous optional (corrected evidence only).
7. **Do not send NVIDIA.**

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
- Claireon re-enable only after P0 clears and PCH heap is fixed.

## Explicitly not Now

- Sakura level composition / hero placement (human-owned).
- Deletes, master architecture rewrites, external publish without approval.
- Writes under `Content/_PROJECT/`.
- NVIDIA applications.
- Reopening Claireon on the P0 critical path.
- Citing withdrawn MATH 98.8% figures in any outgoing draft.

## How to update from phone

```text
Reconcile Docs/PhoneOps/BACKLOG.md with Docs/P0_TASK_LEDGER.json and
Docs/Handoffs/P0_CLOSEOUT_TODAY_2026-09-01.md (see PHONE_PARTY_TRICK_2026-09-02).
Move finished items out; do not add speculative work. Commit + PR.
```
