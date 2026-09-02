# Git health report — 2026-09-02

## Status: CLOUD_SPARSE PASS-WITH-HOLDS / WINDOWS SOT OBJECT CERT UNVERIFIED / MAIN PUBLISHED

This checkpoint **supersedes** [`GIT_HEALTH_2026-08-24.md`](GIT_HEALTH_2026-08-24.md).
The August 24 note described `HEAD cfb2bef8`, twelve unpushed commits, and mixed WIP
holds. Those publication facts are obsolete: `origin/main` is published and this
checkout matches it after rebase.

Evidence for LFS **object** completeness was gathered on a Cloud Agent sparse
checkout (`CLOUD_SPARSE`). Do **not** treat missing LFS payloads here as Windows
SoT corruption. Certify object health only on the full Windows worktree (or after
an intentional `git lfs pull` slice).

## Audited baseline

| Item | State |
| --- | --- |
| Branch (this session) | `cursor/git-health-checkpoint-c2b1` (docs/health) — PR #48 |
| Documented baseline `origin/main` | `09d852a7` — merge-train B04 HoudiniEngine (synced into PR branch) |
| Ahead / behind vs `origin/main` | health PR tip ahead with docs/CI/toolchain landings; main tip included via merge |
| Remote publication | PR #48 open; branch rebased/merged onto latest merge-train main |
| Evidence tier | `CLOUD_SPARSE` |
| Local `.git` / LFS cache | ~84 MB / ~16 MB (not a full hydrate) |
| LFS-tracked paths at HEAD | 3920 |
| Worktree (cloud) | Single `/workspace`; no secondary worktrees registered |

## Evidence and proof tier

| Check | Result | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Git object-graph integrity (`fsck`) | **PASS** | Local object graph has no reported corruption | Windows SoT identity beyond shared commits |
| LFS pointers (`git lfs fsck --pointers`) | **PASS** | Tracked LFS-suffix paths are pointer stubs | Payloads exist locally |
| LFS objects (`git lfs fsck`) | **FAIL (`CLOUD_SPARSE`)** | 3871 pointers lack local objects in this checkout | Remote LFS store health; Windows hydrate |
| Non-pointer LFS-suffix files | **0** | HEAD has no raw binaries where pointers are required | Historical non-pointer blobs elsewhere in graph |
| Origin `main` visibility | **PASS** | `refs/heads/main` resolves | Push authorization |
| LFS locks query | **PASS** | Lock endpoint answered | That lockable assets are being used |
| Pre-commit hook | **PASS** | Hook ran in this environment | Every other machine has `core.hooksPath=.githooks` |
| P0 allowlist / ignore carve-outs | **PASS** | Reviewed P0 assets remain versionable+LFS; exceptions stay ignored | Runtime gameplay |

Artifacts:

- [`Saved/Audit/git_health_summary_2026-09-02.json`](../Saved/Audit/git_health_summary_2026-09-02.json)
- [`Saved/Audit/git_health_audit_cloud_remote_2026-09-02.txt`](../Saved/Audit/git_health_audit_cloud_remote_2026-09-02.txt) (full cloud log; may be gitignored)
- [`Docs/GIT_BRANCH_HEALTH_2026-09-02.md`](GIT_BRANCH_HEALTH_2026-09-02.md)
- [`Docs/GIT_BRANCH_TRIAGE_2026-09-02.md`](GIT_BRANCH_TRIAGE_2026-09-02.md)

## Last-320 commit review (full V2 history)

`main` has **224 commits** (`13717fb3` … current). There is no deeper V2 window —
this is 100% of MelodiaMelusinaV2 history (2026-08-11 → 2026-08-30+).

| Metric | Finding |
| --- | --- |
| Authors | fromage3900 176 · Brennan Shepherd 43 · Cursor Agent 5 |
| Conventional messages | ~82% (`docs` / `feat` / `fix` / `chore` dominate) |
| Theme mix | Docs ~38 · P0/gameplay ~37 · worldgen/GN ~33 · tools/CI ~23 · git/LFS ~22 |
| LFS-touching commits | 36 |
| Velocity spikes | Aug 20 (40), Aug 24 (43), Aug 30 (33) |
| Healthy | Hooks, `git_safe_push`, batch discipline docs, pointer integrity at HEAD |
| Unhealthy / expensive | Root ~8k-file dump; mega mixed commits; quarantine + CompatibilityLabs still reachable; nested `.git_disabled` packs; 23 unique remotes; `.gitignore` touched 14× |

Grades: message B+ · text/binary split C+ · hooks A- · branch lifecycle D+ · docs currency C (this file refreshes health) · collab clone story C (Content mostly untracked by design).

## Remaining holds

1. **Windows SoT LFS object certification** — re-run `python Tools/git_health_audit.py --remote` on the full hydrate before any large LFS push claim.
2. **Branch unique work** — 23 remotes still carry unique commits. Triage table: [`GIT_BRANCH_TRIAGE_2026-09-02.md`](GIT_BRANCH_TRIAGE_2026-09-02.md). No casual deletes.
3. **Secondary Windows worktrees** — prior HOLD rows (`.claude` worktree, `Melodia_ClaireonTest`) remain owner-audit items on the SoT machine; this cloud checkout cannot see them. See [`GIT_WORKTREE_INVENTORY_2026-09-02.md`](GIT_WORKTREE_INVENTORY_2026-09-02.md).
4. **Forever-cost landmines** — nested packs, large non-LFS blobs, quarantine trees. Inventory only unless owner orders rewrite: [`GIT_HISTORY_LANDMINES_2026-09-02.md`](GIT_HISTORY_LANDMINES_2026-09-02.md).
5. **LFS budget** — free tier ~10 GiB; live payload historically ~9.19 GB. Forward discipline: [`GIT_LFS_FORWARD_DISCIPLINE_2026-09-02.md`](GIT_LFS_FORWARD_DISCIPLINE_2026-09-02.md) + [`LFS_COLD_ARCHIVE.md`](LFS_COLD_ARCHIVE.md).

## Safe path forward

1. Keep text/code on Git with path-limited commits; one LFS change = one commit.
2. Land ahead-only docs/CI branches via normal PRs (this health PR includes that batch).
3. HOLD divergent remotes until ownership is proven; do not delete.
4. Cold-archive superseded `Exports/PortfolioStages` blends per the Glacier runbook when the owner schedules it.
5. Continue Perforce hybrid for lock-sensitive creative assets; do not move bulk `Content/` until cutover validation.
6. Never run `git clean -fd`, `git checkout -- .`, force-push, filter-repo, or LFS prune without the destructive-operation approval gate in [`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md).

## Related documents

- [`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md)
- [`GIT_CONSOLIDATION_RUNBOOK_2026-08-30.md`](GIT_CONSOLIDATION_RUNBOOK_2026-08-30.md)
- [`LFS_COLD_ARCHIVE.md`](LFS_COLD_ARCHIVE.md)
- [`GIT_HEALTH_2026-08-24.md`](GIT_HEALTH_2026-08-24.md) — historical; superseded by this file
