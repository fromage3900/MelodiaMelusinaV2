# Git Batch Discipline — MelodiaMelusinaV2

Adopted 2026-08-11 after the V1 LFS budget failure. GitHub LFS is now metered
billing: free quota is 10 GiB storage + 10 GiB bandwidth/month; overages bill
to the account payment method by hourly storage accrual, and **storage is
charged for every LFS object ever associated with the repo** — it does not drop
until the object is unreferenced *and* the month rolls over.

That means the cost lever is not "commit less often". It is:

## The rules

1. **Text is cheap; binaries are expensive.**
   - `Source/`, `Config/`, `Docs/`, `Tools/`, `deploy/` scripts, `.md`, `.py`,
     `.json`, `.ini`, `.uproject`: commit early, commit often, one concern per
     commit. These never touch LFS billing.
2. **One LFS change = one commit, immediately.**
   - Every commit that touches a `.uasset`/`.umap`/`.fbx`/`.png`/`.wav` pushes
     the **entire new file version** to LFS storage. Editing a 500 MB uasset
     three times = 1.5 GB of billed storage. If you must iterate on a binary,
     do it in one session and commit once when it is done.
3. **Never mix binaries with refactors.**
   - A commit that rewires Blueprint logic *and* touches unrelated textures
     doubles the storage delta for no reason. Separate them.
4. **Branch discipline.**
   - Feature branches: `feature/…`, `fix/…`, `docs/…`, `collab/…`, `recovery/…`.
   - Keep binary-only work on its own branch; merge when stable.
5. **Never push abandoned branches.**
   - V1's corrupt branches are gone locally and were never pushed to V2. If a
     branch is dead, delete it (`git branch -D`) — orphaned LFS objects in
     pushed history are *billed forever*.
6. **Prune locally, routinely.**
   - `git lfs prune --recent` reclaims local disk (V1: 64 GB → 18 GB).
   - `git gc --prune=now` after branch deletions.
7. **The guard script.**
   - `python Tools/git_safe_push.py --limit-mb 512` runs before every push: it
     lists staged LFS objects with sizes and refuses to proceed if the batch
     exceeds the limit (default 512 MB). CI calls the same check.

## Cost reference (metered)

| Action | Cost |
|---|---|
| Free quota | 10 GiB storage + 10 GiB bandwidth / month |
| Commit an LFS file (new version) | +full file size to storage |
| Clone / pull an LFS file | +file size to bandwidth |
| Push an LFS file | storage only (no bandwidth) |
| Orphaned LFS object in pushed history | billed until repo deleted + month rollover |

Target: keep monthly storage growth in the low GBs by never re-uploading
unchanged binaries and never pushing dead branches.
