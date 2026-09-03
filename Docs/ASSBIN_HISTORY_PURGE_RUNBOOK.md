# assbin History Purge Runbook — quiet-window operation

**Status:** QUEUED — must run when no agent commits to `main`, editor closed, swarm idle.
**Why:** `Content/Melodia/Companions/ChoralSheep/choralsheephi.assbin` (164.86 MB) was committed
as raw git in `5aa27101` (pre-LFS) and exceeds GitHub's 100 MB limit. The push of `main` is
rejected (`GH001: Large files detected`) until the blob is unreachable from history.
**Working tree already cleaned:** `e93f8571` removed the file from the tree; this purge removes
it from **history** so the push succeeds.
**Future-proofing already landed:** `98844ee0` tracks `*.assbin` / `*.assbin.gz` via LFS.

---

## Preconditions (all must hold)

1. **No concurrent commits to `main`.** The last 30-min `filter-branch` attempt was aborted
   because a parallel lane committed while it ran. Verify:
   ```powershell
   git fetch origin; git rev-list --count origin/main..main   # expect 0 ahead once pushed; else wait
   ```
2. **Editor closed** (avoid `.uasset` churn / locks during ref rewrite).
3. **Stash popped or dropped** — a clean, committed working tree (`git status --porcelain` empty
   except the known `temp: choral sheep edits` stash). Do NOT run with uncommitted work.
4. **Fresh bundle backup** (history rewrite is irreversible):
   ```powershell
   git bundle create C:\EnvironmentPortfolio\BS_GodFile_Bundles_20260830\pre_purge_<DATE>.bundle --all
   ```

---

## Procedure (prefer git-filter-repo — not installed; install once)

```powershell
pip install git-filter-repo
git filter-repo --invert-paths --path Content/Melodia/Companions/ChoralSheep/choralsheephi.assbin --force
```

This rewrites every commit touching that single path; all other content is preserved.

> **Fallback if filter-repo is unavailable:** `git filter-branch` with the same index-filter,
> but ONLY in the quiet window (it is the tool that hung before).

## After rewrite

```powershell
# filter-repo removes the origin remote and drops refs/original — re-add remote + prune
git remote add origin https://github.com/fromage3900/MelodiaMelusinaV2.git
git push --force-with-lease origin main
# then push all other refs (or rerun Tools/push_queue.ps1)
git fetch origin; python Tools/branch_health.py
```

## Verify

- `git log --all --oneline -- Content/Melodia/Companions/ChoralSheep/choralsheephi.assbin` → empty
- `git rev-list --objects --all | Select-String choralsheephi.assbin` → empty
- `git push origin main` succeeds
- `git fsck` clean

## Rollback

The pre-purge bundle (step 4 preconditions) restores full history if anything is wrong:
```powershell
git fetch C:\EnvironmentPortfolio\BS_GodFile_Bundles_20260830\pre_purge_<DATE>.bundle
# or clone from the bundle into a fresh dir and inspect before force-pushing anything
```

**Owner sign-off required before running.** This rewrites shared history; `--force-with-lease`
(not plain `--force`) on push. Do not run under a live editor or active lane.