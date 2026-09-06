# Semester onboarding — game dev cohorts

**Read time:** 10 minutes. **Then:** pick one BACKLOG item, nothing else.

## 1. What this project is

MelodiaMelusinaV2: a UE 5.8 rhythm-JRPG vertical slice ("First Dream"). QuillScript owns
narrative. The TurnBased JRPG template owns combat/saves. Everything else is presentation
that converges onto those two authorities — never a parallel system.

## 2. Reading order (in this order, stop when you have your task)

1. `AGENT_START_HERE.md` — discovery contract + freshness rule.
2. `CURRENT_STATE.md` — what is true right now.
3. `Docs/PhoneOps/BACKLOG.md` — the task queue (Now / Next / Later).
4. `Saved/gate_ledger.json` — last row per gate id is standing; older rows are history.
5. `Docs/PhoneOps/JCODE_SWARM_PIPELINE.md` — only if you join the parallel coding swarm.

Never start from a dated handoff. Never cite one as current without a ledger row behind it.

## 3. Session start (every session, every lane)

```powershell
python Tools/project_state.py --view session_start
```

Tip, dirty files, latest gate rows, staleness flags. This output outranks any doc.

## 4. Lanes (pick one, stay in it)

| Lane | Tool | Does |
|---|---|---|
| Repo swarm | jcode (`.\deploy\start_jcode_swarm.ps1`) | Python, docs, audits — ≤6 workers, coordinator-owned paths |
| Gameplay IDE | OpenCode in Rider (`Ctrl+\`) | C++, PIE, Blueprint proof |
| Meta terminal | Muse Code (WSL) | Review, log analysis |
| Phone/cloud | Cursor | PRs, backlog, mobile-safe docs |

One Unreal Editor at a time. Port 9316 has exactly one listener before any editor work.

## 5. Red lines (violations cost days)

- No `git clean -fd` / `git checkout -- .` — bulk `Content/` is untracked; `clean` erases the protagonist permanently.
- No writes under `Content/_PROJECT/`, no Sakura art direction.
- No Python against `Content/TurnBasedJRPGTemplate/Blueprints/Skills/` (fatal editor death) — use Monolith `blueprint_query`.
- No new parallel authorities (second combat, save, HUD writer, audio writer).
- No destructive deletes without owner (Red) sign-off. Archive to `Docs/_Superseded/`, don't delete.
- Branch names must start with `feature/ fix/ docs/ cleanup/ collab/ codex/ recovery/ cursor/` (hook-enforced). Never push `main`.

## 6. First tasks (good semester starters)

- Reproduce a `session_start` + offline contract run (`Docs/P0_INTEGRATION_EXECUTION_PLAN_2026-09-06.md` §1).
- Close a `_Superseded` move from the prune proposal (no authority needed beyond the checkbox).
- Claim one proof-backlog item from BACKLOG Now with assertion JSON beside every frame.
