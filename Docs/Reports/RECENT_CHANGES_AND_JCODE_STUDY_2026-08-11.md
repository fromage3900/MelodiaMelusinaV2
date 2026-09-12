# Recent changes, new git, and jcode workflows — study memo

**Date:** 2026-08-11  
**Workspace:** `C:\EnvironmentPortfolio`  
**Authority repos:** `BS_GodFile` (tracks MelodiaMelusinaV2), `MelodiaMelusinaV2`

## Verdict

The portfolio root is no longer a live git repository. Melodia day-to-day work lives in nested Unreal checkouts. On 2026-08-11 the tree gained: MelodiaMelusina V2 import, enterprise LFS `lockable` live-ops attributes, agent Tools infrastructure, and a ported **[jcode](https://jcode.sh)** light-swarm harness (from remote branch `origin/cursor/phone-ops-docs-0e29` onto `main`).

## Git topology

```text
EnvironmentPortfolio/          (NO .git — orphan .github + .git.backup.mirror)
├── BS_GodFile/                ★ primary UE repo → remote v2 = MelodiaMelusinaV2
├── MelodiaMelusinaV2/         ★ published V2 clone → origin
├── my-site-clean/             website repo
├── .repo_recovery_20260727/   cold recovery (mass-deleted worktree)
└── .agents/                   multi-agent coordination (not a git root)
```

### Enterprise LFS / live-ops

- Spec: `.agents/worker_m3/gacha_git_liveops_workflow.md`
- `.gitattributes`: `lockable` on `.uasset`, `.umap`, `.blend`, textures, audio, fonts, DLLs
- Hooks: `.githooks/` + `.pre-commit-config.yaml`
- Batch discipline: `Docs/GIT_BATCH_DISCIPLINE.md`

## 2026-08-11 commit spine (`BS_GodFile` / V2)

| Commit | Summary |
|--------|---------|
| `13717fb3` | MelodiaMelusina V2: Electric Boogaloo (mega-import) |
| `2623f02a` | Post-snapshot: MelodiaCore, iOS input, lockable upgrade |
| `fd645ce3` | Docs V2 refresh, G:→C: paths, LFS push guard |
| `87b2938d` | Agent Tools: model_router, playtest_harness, video_review_lane, memory_index, lane_dispatcher |
| `78867a33` | Closeout verdicts + **jcode harness port** (`.jcode/`, PhoneOps, deploy scripts) |
| `e3908f57` | `AGENTS.md` §5 jcode swarm constitution |

## Agent Tools (replacing Echo runner scripts)

Doc: `Docs/Production/AGENT_INFRASTRUCTURE_2026-08-11.md`

- `Tools/model_router.py` — lane/cost policy
- `Tools/playtest_harness.py` — real-input PIE + gate ledger (`record` replaces `record_gate.py`)
- `Tools/video_review_lane.py` — vision regression on captures
- `Tools/memory_index.py` — docs/ledger search index
- `Tools/lane_dispatcher.py` — queue → model class assignment

Echo multi-modal topology docs remain (`Docs/ECHO_PIPELINE_2026-08-09.md`); runtime gate evidence now flows through the playtest harness.

## jcode swarm

**What:** Parallel **repo** coding lane (coordinator → ≤6 workers: PGA/MPA/PPA/WIA/SQA/WEB). Does not replace Unreal/Blender or surreal production loops.

**Harness:**

| Path | Role |
|------|------|
| `.jcode/swarm-prompt.md` | Ownership scopes + red lines |
| `.jcode/coordinator-bootstrap.md` | Recipe A/B paste prompt |
| `.jcode/mcp.json` | Monolith stdio proxy |
| `deploy/start_jcode_swarm.ps1` | Launch (UTF-8 BOM; add `%LOCALAPPDATA%\jcode\bin` to PATH) |
| `deploy/install_jcode_melodia_skills.ps1` | Monolith skills → `~\.jcode\skills` |
| `Docs/PhoneOps/JCODE_SWARM_PIPELINE.md` | Full pipeline |

**Policy:** Keep surreal/world/`run_verify` loops. Deprecate `deploy/cursor_*_loop.ps1` for parallel coding wakes. Phone/Cursor cloud remains the PR/mobile lane.

**Acceptance (2026-08-11):** Recipes A/B reports + filled `Docs/Reports/jcode_swarm_acceptance.md`. jcode v0.75.3 preflight PASS; Monolith MCP not required for A/B.

## Follow-through completed this session

1. Synced agent Tools + jcode commits onto `MelodiaMelusinaV2` and pushed `main` (`e3908f5`).
2. Ported jcode harness onto current `main` (file-set port, not full branch merge).
3. Ran Recipe A/B acceptance artifacts; fixed launch script encoding for Windows PowerShell 5.
4. Renormalized V2 LFS pointer files (font + assimp); triage note for recovery/orphan root leftovers.
5. This study memo.

## Related docs

- `MELODIA_ARCHITECTURAL_MASTER_PLAN.md`
- `Docs/MOBILE_IOS_PIPELINE_AND_AI_WORKFLOWS_2026-08-11.md`
- `Docs/Reports/GIT_LEFTOVERS_TRIAGE_2026-08-11.md`
- `Docs/Reports/jcode_swarm_acceptance.md`
