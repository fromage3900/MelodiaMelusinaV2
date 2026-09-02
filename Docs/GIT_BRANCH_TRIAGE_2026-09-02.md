# Branch triage — 2026-09-02

Census source: [`GIT_BRANCH_HEALTH_2026-09-02.md`](GIT_BRANCH_HEALTH_2026-09-02.md) /
[`Saved/Audit/branch_health_2026-09-02.json`](../Saved/Audit/branch_health_2026-09-02.json).

**Policy:** classify first. Remote deletion, force-delete, and worktree removal
require the destructive-operation approval gate in
[`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md). Prefer HOLD over delete.

Ahead/behind counts are vs `origin/main` at `8b3d2666` (post-fetch).

## MERGE (ahead-only, text/CI — land via PR)

| Branch | Ahead | Behind | Contents | Disposition |
| --- | --- | --- | --- | --- |
| `origin/docs/toolchain-consolidation-2026-08-31` | 39 | 0 | Research/plans: toolchain, PCG, Magpie, Dash, Mara Elletra, experimental systems | **MERGE** into health PR |
| `origin/cursor/fix-ci-workflows-529c` | 4 | 0 | Actions v7 bumps, site sync cron guard, `quick-deploy.ps1` CRLF normalize, repair-plan doc | **MERGE** into health PR |
| `origin/claude/tonight-cymatic-ecology-interaction` | 2 | 0 | Cymatic/RTX spike docs + `specs/cymatic_ecology_bridge.json` + `specs/nvidia_rtx_canary_manifest.json` | **MERGE** unique specs; docs may already be covered by toolchain branch (resolve favoring fuller toolchain text) |
| `origin/docs/2026-08-31-mara-instrument-cymatics-plan` | 1 | 0 | `Docs/Houdini/MARA_INSTRUMENT_CYMATICS_EXECUTION_PLAN_2026-08-31.md` | **MERGE** into health PR |

## HOLD (divergent / backup / WIP — do not delete)

| Branch | Ahead | Behind | Why HOLD |
| --- | --- | --- | --- |
| `origin/backup/pre-consolidation-2026-08-30` | 75 | 54 | Pre-consolidation backup; may be only ref to unique work |
| `origin/docs/2026-08-29-character-p1-p2-canon-audit` | 26 | 33 | Divergent character canon docs |
| `origin/feature/zenforest-glam-headless` | 17 | 71 | Feature / glam lane |
| `origin/feature/repo-lockin-20260813` | 9 | 187 | Historical lock-in; far behind |
| `origin/rnd/2026-08-30-blender52-music-gn-studio` | 5 | 27 | R&D studio lane |
| `origin/cursor/nemotron-research-docs-2d2d` | 3 | 186 | Stale research docs |
| `origin/docs/monolith-concept-art-backlog-2026-08-26` | 3 | 58 | Concept backlog |
| `origin/codex/perforce-migration-handoff-2026-08-26` | 2 | 58 | Perforce handoff |
| `origin/cursor/model-lanes-agents-slim-f425` | 2 | 199 | Likely superseded AGENTS slim |
| `origin/cursor/perforce-docs-batch-ca02` | 2 | 54 | Perforce docs batch |
| `origin/feature/credits-20260813` | 2 | 186 | Credits feature |
| `origin/copilot/new-feature-implementation` | 1 | 58 | Unclear Copilot tip |
| `origin/cursor/branch-cleanup-executed-ca02` | 1 | 58 | Cleanup report branch |
| `origin/cursor/nemotron-docs-batch-ca02` | 1 | 58 | Docs batch |
| `origin/cursor/recruiter-sendoffs-no-nvidia-ca02` | 1 | 71 | Career packet |
| `origin/cursor/zenforest-docs-batch-ca02` | 1 | 58 | Zenforest docs |
| `origin/feature/echo-topo-chapter2` | 1 | 188 | Echo topo |
| `origin/feature/sea-above-choralsheep-20260826` | 1 | 54 | Sea Above / ChoralSheep |
| `origin/pr/melusina-v22-sync` | 1 | 71 | Melusina v22 PR line |

## MERGED (no unique commits vs main — deletion still needs approval)

| Branch | Notes |
| --- | --- |
| `origin/copilot/fix-issue-in-algorithm` | Fully merged |
| `origin/copilot/git-status-check` | Merged tip; behind metadata only |
| `origin/copilot/review-recent-documents-on-git` | Fully merged |
| `origin/copilot/validate-source-control-claims` | Merged tip |
| `origin/cursor/docs-safe-batches-ca02` | Merged tip |
| `origin/docs/p1-monolith-character-concepts-2026-08-28` | Merged tip |
| `origin/docs/sea-above-system-shader-breakdowns-2026-08-26` | Merged tip |
| `origin/triage/nemotron-research-p3` | Merged tip |

Leave these remotes until the owner explicitly approves `git push origin --delete <branch>`.

## Excluded by design

`refs/heads/legacy*` and `remotes/legacy-melodia/*` share no V2 lineage and are
never merge candidates (`Tools/branch_health.py`).
