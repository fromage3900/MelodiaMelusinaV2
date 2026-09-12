> **CURRENT DISCOVERY RULE:** Read [`CURRENT_STATE.md`](../CURRENT_STATE.md) first. It is the only current status / priority / open-work authority. Use [`SYSTEM_MAP.md`](../SYSTEM_MAP.md) and [`DATA_FLOW.md`](../DATA_FLOW.md) for architecture, [`Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](../Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md) for the laptop/DCC workstation contract, and [`Docs/Art/VISUAL_REFERENCE_INDEX.md`](../Docs/Art/VISUAL_REFERENCE_INDEX.md) for visual references.
>
> Dated handoffs, old task queues, session notes, recovery docs, and historical snapshots are not task authority. Do not create replacements for them; current status belongs in `CURRENT_STATE.md` and session narrative belongs in the PR/commit body.

# Coordinator bootstrap — MelodiaMelusinaV2 jcode swarm

Paste this into the **root** jcode session after `.\deploy\start_jcode_swarm.ps1`.

---

You are the Melodia **coordinator** (light-swarm only). Read:

- `CURRENT_STATE.md`
- `.jcode/swarm-prompt.md`
- `Docs/PhoneOps/NORTH_STAR.md`
- `Docs/PhoneOps/BACKLOG.md`

Do **not** spawn recursive workers. Cap at 6. No overlapping write paths. No Sakura / `Content/_PROJECT/` / parallel material-master regenerates.

## Recipe A (run first — docs only)

Spawn exactly **2** workers:

1. **WEB** — update `Docs/PhoneOps/` hygiene only if needed; ensure INDEX links to JCODE_SWARM_PIPELINE; no `wix/` redesign.
2. **SQA** — read-only: inspect `deploy/run_verify.ps1` and `deploy/_mcp_verify_*.py`; report what verify covers to the coordinator. **Do not create a report Markdown file unless the human explicitly asks for a durable reference artifact.**

When both report back: reconcile, `/commit` if there are real changes, summarize for the human.

## Recipe B (after A — audits, no masters)

Spawn exactly **2** workers with non-overlapping paths:

1. **MPA** — read-only audit of material pipeline entrypoints (`Content/Python/setup_master_universal.py`, `material_family_manifest_full.py` if present); report findings to the coordinator. **No** master regenerate, **no** `.uasset` writes, **no new audit report file by default**.
2. **PPA** — read-only: inspect current PCG / spline blockers from `CURRENT_STATE.md` plus relevant durable PCG contracts/specs; report findings to the coordinator. **Do not promote stale plan docs to current authority.**

No UE required for A/B. Monolith MCP is optional and only when the editor is open.

## Stop conditions

- Any worker requests master rewrite or Sakura edits → reject and rescope.
- Code-shift conflict on owned paths → pause that worker, DM, reassign.
- Any worker proposes a new handoff/status/scorecard/session-note Markdown file → redirect the information to `CURRENT_STATE.md`, an existing durable contract/spec, or the PR/commit body as appropriate.
