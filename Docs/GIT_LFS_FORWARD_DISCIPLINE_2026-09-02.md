# LFS forward discipline — 2026-09-02

Operational checklist that **applies** (does not replace)
[`GIT_BATCH_DISCIPLINE.md`](GIT_BATCH_DISCIPLINE.md) and
[`LFS_COLD_ARCHIVE.md`](LFS_COLD_ARCHIVE.md).

No history rewrite. No `.gitignore` / `.gitattributes` edits in this pass
(never-touch without `SKIP_PROTECTION=1` + owner instruction).

## Rules in force

1. **Text is cheap; binaries are expensive.** Commit `Source/`, `Docs/`, `Tools/`,
   `deploy/`, specs early and often, one concern per commit.
2. **One LFS change = one commit, immediately.** Every new `.uasset` / `.umap` /
   `.blend` / `.fbx` / `.png` / `.wav` version bills full size.
3. **Never mix binaries with refactors.** Separate asset commits from code/docs.
4. **Push budgets** via `Tools/git_safe_push.py`: 50 MB on `collab/` / `cursor/` /
   `docs/` branches; else 512 MB.
5. **Before any LFS push:** `python Tools/git_health_audit.py --remote` then
   `python Tools/git_safe_push.py --check-only`.
6. **Hybrid SoT:** Git owns text/code; Perforce pilot owns lock-sensitive creative
   assets. Do **not** move bulk `Content/` until cutover validation completes.

## Stop committing into these roots (unless owner promotes)

| Path | Why |
| --- | --- |
| `_QuarantineAssets_*` / `_Quarantine_InvalidCookAssets_*` | Quarantine; still LFS-billed while reachable |
| `CompatibilityLabs/**` (new dumps) | Labs/backups; use filesystem archive instead |
| Scratch FBX / root-level experiment meshes | One-off names (`wasteoftime.fbx`, etc.) |
| `Exports/PortfolioStages` superseded blends | Cold-archive candidates (`v16`/`v17`) |
| Nested `.git` / `.git_disabled` trees | Pack objects inflate the repo forever |

## Cold archive (owner-scheduled)

Follow [`LFS_COLD_ARCHIVE.md`](LFS_COLD_ARCHIVE.md):

- Target: archive superseded portfolio stage blends + CompatibilityLabs backup
  outside Git (S3 Glacier), keep a manifest in-repo.
- Historical estimate: reclaiming `v16`+`v17`+CompatibilityLabs backup ≈ 3.65 GB
  toward free-tier headroom (billing trails until objects are unreferenced *and*
  the month rolls over — rewrite still requires explicit approval).

## Agent / collab checklist

- [ ] Path-limited `git add` only — never `git add -A` on a mixed tree
- [ ] No `git clean -fd` / `git checkout -- .`
- [ ] No new quarantine or CompatibilityLabs commits without owner say-so
- [ ] LFS batch sized under `git_safe_push` limit
- [ ] Cloud audits labeled `CLOUD_SPARSE` when objects are missing locally

## Related

- [`GIT_HEALTH_2026-09-02.md`](GIT_HEALTH_2026-09-02.md)
- [`GIT_HISTORY_LANDMINES_2026-09-02.md`](GIT_HISTORY_LANDMINES_2026-09-02.md)
- [`Tools/git_safe_push.py`](../Tools/git_safe_push.py)
- [`Tools/lfs_health_audit.py`](../Tools/lfs_health_audit.py)
