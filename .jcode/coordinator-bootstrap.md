# Coordinator bootstrap — MelodiaMelusina jcode swarm

Paste this into the **root** jcode session after `.\deploy\start_jcode_swarm.ps1`.

---

You are the Melodia **coordinator** (light-swarm only). Read:

- `.jcode/swarm-prompt.md`
- `Docs/PhoneOps/NORTH_STAR.md`
- `Docs/PhoneOps/BACKLOG.md`
- `CURRENT_STATE.md`

Do **not** spawn recursive workers. Cap at 6. No overlapping write paths. No Sakura / `Content/_PROJECT/` / parallel material-master regenerates.

## Recipe A (run first — docs only)

Spawn exactly **2** workers:

1. **WEB** — update `Docs/PhoneOps/` hygiene only if needed; ensure INDEX links to JCODE_SWARM_PIPELINE; no `wix/` redesign.
2. **SQA** — read-only: list `deploy/run_verify.ps1` and `deploy/_mcp_verify_*.py`; write a short note under `Docs/Reports/jcode_swarm_recipe_a.md` with what verify covers (create file if missing).

When both report back: reconcile, `/commit` if there are real changes, summarize for the human.

## Recipe B (after A — audits, no masters)

Spawn exactly **2** workers with non-overlapping paths:

1. **MPA** — read-only audit of material pipeline entrypoints (`Content/Python/setup_master_universal.py`, `material_family_manifest_full.py` if present); write findings to `Docs/Reports/jcode_swarm_recipe_b_mpa.md`. **No** master regenerate, **no** `.uasset` writes.
2. **PPA** — read-only: summarize PCG Ex / spline blockers from `CURRENT_STATE.md` + `.junie/plans/pcg-universal-expansion.md` if present; write `Docs/Reports/jcode_swarm_recipe_b_ppa.md`.

No UE required for A/B. Monolith MCP is optional and only when the editor is open.

## Stop conditions

- Any worker requests master rewrite or Sakura edits → reject and rescope.
- Code-shift conflict on owned paths → pause that worker, DM, reassign.
