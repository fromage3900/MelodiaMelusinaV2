> **CURRENT DISCOVERY RULE:** Read [`CURRENT_STATE.md`](../CURRENT_STATE.md) first. It is the only current status / priority / open-work authority. Use [`SYSTEM_MAP.md`](../SYSTEM_MAP.md) and [`DATA_FLOW.md`](../DATA_FLOW.md) for architecture, [`Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md`](../Docs/Production/LAPTOP_PROCEDURAL_LANE_2026-09-11.md) for the laptop/DCC workstation contract, and [`Docs/Art/VISUAL_REFERENCE_INDEX.md`](../Docs/Art/VISUAL_REFERENCE_INDEX.md) for visual references.
>
> Dated handoffs, old task queues, session notes, recovery docs, and historical snapshots are not task authority. Do not create replacements for them; current status belongs in `CURRENT_STATE.md` and session narrative belongs in the PR/commit body.

# MelodiaMelusinaV2 swarm policy (rewritten 2026-09-26)

Binding rules: `AGENTS.md` → "BINDING RULES" and `CLAUDE.md`. Orchestration design:
`.hermes/plans/2026-09-26_hermes-orchestrator-infra-plan.md` (Hermes runs, Jev routes, Claude verifies).
The PGA/MPA/PPA/WIA/SQA/WEB/MUSE roles were retired by Decision 002 — workers are **lanes**, not owners.

## Shape

- **Light swarm:** the coordinator spawns workers; workers never spawn children. Cap **6** live workers.
- **One worker = one git worktree** on its own branch, cut from `origin/main`
  (`GIT_LFS_SKIP_SMUDGE=1 git worktree add -b <lane>/<task>-<date> <path> origin/main`).
  No two workers share a checkout; no overlapping write paths.
- **Workers return a patch, never land it.** No `/commit` to shared branches, no push, merge, rebase,
  reset or PR — the owner approves each git/p4 operation (git pipeline law). A worker may commit
  inside its own worktree branch so the patch is reviewable; that branch is never pushed by the swarm.
- **No editor.** Swarm workers get no Monolith / Claireon / UE access and never launch Unreal. The
  editor belongs to one agent at a time (Hermes-in-Claireon or a Claude session) — editor tasks are
  handed back to the coordinator as a packet, not attempted.
- **Text/code only:** Python, C++ source, docs, specs, tests, Blender `-b` scripts. No `.uasset`/`.umap`
  writes, no `Content/` binaries, no material masters, no `Config/` edits.

## Lanes (model choice = `python Tools/model_router.py pick <class>`)

| Lane | Router class | First pick (verified 2026-09-26) | Use |
|---|---|---|---|
| `code` | `code` / `cpp` | Mantle `qwen.qwen3-coder-next` / `qwen3-coder-480b` | tools, harness fixes, tests, C++ |
| `fast` | `docs` / `triage` / `audit` | Mantle `zai.glm-4.7-flash` | docs, log triage, manifests |
| `deep` | `deep` / `review` | Mantle `qwen.qwen3-235b-a22b-2507` | long reasoning, independent review |
| `local` | `daemon` / `author` / `quill_author` | Ollama `qwen3-coder:30b` / `heretic-27b` / `muse-glimmer:30b` | free overnight / drafts |

Mantle key: env `AWS_BEARER_TOKEN_BEDROCK` (never in the repo). Claude is **not** available on this
Bedrock account. Setup: `deploy/setup_agent_lanes.ps1`.

## Task packet (coordinator writes one per worker)

`id` · `lane` · `goal` · `may_write` (path globs) · `must_not` · `done_when` (a file the verifier can
open: test output, JSON, image, diff) · `worktree` · `budget` (turns).

## Completion report (required)

1. **Outcome:** done | blocked | partial
2. **Branch/worktree + changed paths** (or "none — read-only")
3. **Validation:** exact commands run and their result; the artifact path for `done_when`
4. **Blockers / follow-ups**

A report is not evidence. The verifier (Claude or the `review` lane) opens the artifact before anything
is accepted.

## Red lines (all lanes)

- Never-touch table in `CLAUDE.md` (`.gitignore`, `.gitattributes`, `Config/Default*.ini`,
  `MF_MeshBlend_*`, `deploy/run_verify.ps1`); `L_SakuraPath` / `L_MelusinaMorning` composition;
  `Content/_PROJECT/`; `MelodiaIntegrationMap` layout.
- No destructive deletes; no clearing `deploy/*_LOOP_STOP` files.
- No new handoff / status / scorecard / session-note / plan files: status → `CURRENT_STATE.md`
  (coordinator only), narrative → the patch description.
- No new router, orchestrator, lease or lane framework — extend `Tools/model_router.py` and the
  orchestrator plan.
- If code shifts under you: stop, report the conflict to the coordinator.
