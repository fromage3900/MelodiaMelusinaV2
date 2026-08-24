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
5. **Never push abandoned branches, and never delete one casually.**
   - A branch that appears dead may be the only ref to another lane's commits or
     LFS objects. Branch deletion requires the destructive-operation approval
     gate below. Prefer marking it HOLD until ownership and remote reachability
     are proven.
6. **Inspection is routine; pruning is not.**
   - Dry-run and reachability reports may be routine. `git lfs prune`, object
     pruning, aggressive garbage collection, worktree removal, and branch
     deletion are destructive maintenance and require the approval gate below.
7. **The guard script.**
   - `Tools/git_safe_push.py` runs before every push (via `.githooks/pre-push`)
     and in `echo_gates` CI: it lists LFS candidates with sizes and refuses to
     proceed if the batch exceeds the limit (50 MB on `collab/`/`cursor/`/`docs/`,
     else 512 MB). Companion: `Tools/lfs_health_audit.py`.

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

## Destructive-operation approval gate

The following are **never** routine agent maintenance in this repository:

- worktree removal or prune that could affect a live checkout;
- local or remote branch deletion, including forced deletion;
- `git gc` with an explicit prune window, object pruning, reflog expiry, or LFS
  pruning;
- reset/clean/checkout/restore/stash operations that can discard or hide a
  mixed worktree;
- rebase, filter-repo/filter-branch, replace refs, force push, or any other
  history rewrite;
- setting `lfs.allowincompletepush`, skipping required LFS objects, or bypassing
  a failed LFS/push guard.

Before any such action, all of these conditions are mandatory:

1. The exact target paths, refs, commits, worktrees, and LFS objects are listed;
   no unresolved glob or broad workspace target is allowed.
2. The owner of the affected lane gives explicit approval for that exact
   action. General cleanup or Git-health authorization is not enough.
3. A recoverable backup or protected remote ref is created and independently
   verified to contain every commit and file being placed at risk.
4. Remote URLs and the fetched remote tips are verified, and the target's
   reachability from those refs is recorded.
5. Dirty, staged, untracked, ignored-but-material, locked, and linked-worktree
   state is inventoried immediately before execution.
6. A dry run is used where supported, its output is reviewed, and a rollback or
   recovery procedure is written down.

If any condition fails, leave the item on HOLD. Never use
`lfs.allowincompletepush` to convert missing remote data into a nominally
successful push; missing objects are a blocker that must be repaired or
explicitly resolved by the repository owner.
