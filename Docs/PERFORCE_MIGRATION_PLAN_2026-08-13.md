# Next phase — Perforce for content, git for code

**Status: IN PROGRESS. Hybrid Git + Perforce was approved and the completion gates are closed.**

**Pilot status, 2026-08-27:** Helix Core is running locally at `localhost:1667`, with depot
`//melodia/...`. The typemap has server-enforced `binary+l` locks for `.uasset`, `.umap`, `.blend`,
and `.fbx`, and maps `.json` as text. The lock behavior was verified from two workspaces. Perforce
change `1` is the one-file lock pilot; change `2` seeds `//melodia/Exports/...` with 50 files.
The staged source and Perforce workspace matched before submit. The Git `Exports/` copies remain
intentionally until cutover validation and backup sign-off.

Do not begin this migration while `save_load`, `repeat_consume` and `package_launch` are
open. Moving source control mid-vertical-slice costs a week and buys nothing the slice needs.

---

## Why

Four problems this repo has, which git+LFS cannot fix and Perforce solves directly.
All four are measured, not assumed — evidence in
[`Docs/Reports/LFS_HEALTH_2026-08-13.md`](Reports/LFS_HEALTH_2026-08-13.md).

| Problem, measured 2026-08-13 | Why git+LFS cannot fix it | What P4 does |
|---|---|---|
| **2,224 files marked `lockable`, 0 locks ever held.** LFS locking is advisory, needs network reach, and has no editor integration here. | Locks are a bolt-on. Nothing enforces taking one. | `typemap +l` gives **server-enforced exclusive checkout**. A second writer is refused, not warned. |
| **`Content/` is 65 GB on disk, ~2.7 GB tracked.** Bulk art lives only on the owner's C:/G: drives; onboarding ends at "ask the owner". | Every clone gets full history. Promoting 4.6 GB to LFS bills forever. | A workspace **view** syncs only the paths and revision you ask for. The view *is* the delivery mechanism. |
| **World Partition levels are shells.** `Config/DefaultEngine.ini:222` enables WP; **0 `__ExternalActors__` files are tracked**. Under one-file-per-actor the external actors *are* the level. | The `Content/*` blanket plus per-actor file churn makes this unmanageable in git. | Per-actor files are the case P4 + UE were designed around together. |
| **`.git` is 20 GB (19 GB LFS) against ~8.8 GB referenced.** `.git/lfs/bad` holds 1.75 GB. LFS storage is billed for **every object ever pushed**, until unreferenced *and* the month rolls over. | Structural to LFS. `prune` reclaims local disk, not the bill. | No per-object metered billing. You pay for a server. |

**The single most surprising number:** `Exports/` is **5.6 GB — 63% of all LFS content**,
almost entirely `.blend`. The dominant LFS cost is not `Content/` at all. Moving Blender
stage exports out of git removes most of the bill on its own, and is worth doing
*regardless* of whether the rest of this plan proceeds.

Secondary benefit: UE's Perforce source control provider is first-class (Epic builds
against it). The project currently has **no** source control provider configured at all —
no entry in `BS_GodFile.uproject`, no provider in any `Config/*.ini` — which is the direct
reason no artist has ever taken a lock.

## Why not

Stated plainly, because this is a real cost:

1. **Two version-control systems, six days after consolidating onto one.** The project just
   moved to `MelodiaMelusinaV2` as the single source of truth. This deliberately splits it
   again along a code/art seam.
2. **Code review gets worse.** No PRs, no inline comments. Swarm exists but is a downgrade
   from GitHub for a project whose CI and gates now live there.
3. **A change spanning both systems is not atomic.** A C++ change plus the asset that needs
   it are two commits in two systems with no shared transaction.
4. **Someone administers a server.** Backups, users, typemap, triggers.

## Recommended shape — hybrid

```
git (origin = MelodiaMelusinaV2)        Perforce (Helix Core Free)
  Source/  Tools/  Docs/  deploy/         //melodia/Content/...
  Plugins/  Config/  specs/  .github/     //melodia/Exports/...
  *.uproject                              //melodia/RawArt/...   (the G: drive material)
```

Rationale: keep in git everything the gates and CI act on — the art gates, echo pipeline,
hooks and workflows built on 2026-08-13 all read tracked text and `.uasset` paths. Move to
P4 everything whose problem is size, locking, or delivery.

**Helix Core Free**: 5 users, 20 workspaces, free permanently. That covers this team.

### The one seam that needs care

`Tools/art_gates.py` enumerates assets with `git ls-files Content`. After migration that
returns nothing and the gate silently passes on zero assets — a gate that cannot fail,
which is the exact failure mode this project already has ~130 instances of. **Before
migrating `Content/`, switch `_tracked_uassets()` to a `p4 files` query or a filesystem
walk scoped to the workspace root**, and re-baseline. Same applies to
`Content/Python/audit_mi_runtime.py` and anything else keyed on `git ls-files`.

## Phases

**P0 — decide (owner, ~30 min).** **Complete.** Hybrid Git + Perforce selected.

**P1 — server.** **Pilot complete.** Local Helix Core runs at `localhost:1667`; depot
`//melodia` exists. The server is workstation-local, so collaborators require a shared/VPS server
before this can become the team authority. Establish and verify a backup before further seeding.

**P2 — typemap first, before any submit.** **Complete for the pilot.** This is the step that is painful to retrofit:
```
binary+l   //melodia/....uasset
binary+l   //melodia/....umap
binary+l   //melodia/....blend
binary+l   //melodia/....fbx
text       //melodia/....json
```
`+l` = exclusive checkout. Getting this wrong after 65 GB is submitted means re-typing every
file.

**P3 — seed the depot.** **Exports complete; Content and RawArt blocked.** Perforce change `2`
contains 50 `Exports/` files. `Content/` is 72.09 GB and has active asset edits; local free space
was 35.93 GB during the seed, so do not attempt it until storage and ownership gates are met.
The remaining scope is `Content/` and the `G:\MelodiaMelusina\` raw-art tree
(the textures and rigs currently referenced by docs but present on exactly one machine —
see `Docs/MELUSINA_BLENDER_WARDROBE_SSOT.md`). Verify by hash, not by eye. Keep the git
copies until P6 signs off.

**P4 — wire the editor.** Enable the Perforce provider in `BS_GodFile.uproject`, configure
in `Config/DefaultEngine.ini`. **Both files are on the CLAUDE.md never-touch list and now
also guarded by `.githooks/pre-commit` — owner sign-off required.** Confirm Check Out /
Check In / Revert work from the Content Browser, and that a second editor is actually refused.

**P5 — fix the tooling seam.** `art_gates.py`, `audit_mi_runtime.py`, and any script keyed on
`git ls-files Content`. Re-baseline `specs/art_gates_baseline.json` afterwards and confirm
the gate still fails on a planted violation — a gate you cannot prove still fails is not a gate.

**P6 — strip git.** Only after P5 passes. Remove `Content/` and `Exports/` from git tracking,
update `.gitignore`, then `git lfs prune`. Rewrite onboarding: `COLLABORATOR_SETUP.md`,
`QUICKSTART.md`, `Docs/COLLABORATION_WORKFLOW.md`, `README.md`. The LFS-locking sections
written on 2026-08-13 get replaced by P4 checkout, not deleted piecemeal.

**P7 — the migration is done when a new collaborator can open `L_KaleidoNave` with no
missing references, from a clean machine, following only the written instructions.** That
is the acceptance test. Nothing short of it counts, and it is the thing that is untrue today.

## What must not happen

- **Do not run both systems over the same paths.** One owner per path, permanently. This is
  the `Decision 025` one-writer rule at the source-control level, and the project has already
  paid for violating it twice (three concurrent editors on 2026-08-08; two MCP surfaces on
  one graph).
- **Do not delete the git copy of anything until P6 signs off**, and not before the depot has
  a verified backup. `AGENTS.md` "NEVER RUN THESE" applies throughout — no `git clean -fd`,
  no `git checkout -- .`, at any point in this migration.
- **Do not migrate mid-slice.** Repeat of the header, because it is the most likely way this
  goes wrong.

## Cheap wins available now, without deciding anything

1. Get `Exports/*.blend` out of LFS — 63% of the LFS bill, and Blender stage exports are
   regenerable build artefacts, not source.
2. Re-fetch `Melodia_Portfolio_Stage_v18_SIR_VISIBLE.blend` — its 1.79 GB LFS object is in
   `.git/lfs/bad` and is **live-referenced**, not orphaned.
3. `git lfs prune --recent` — ~10 GB of the 19 GB local store is orphaned. Destructive;
   owner runs it.
4. Enable `GitSourceControl` (ships with UE 5.8, currently not enabled) as an interim. It
   makes the existing LFS locks usable from the Content Browser and costs nothing. If
   Perforce lands later this is thrown away — that is fine, it is a week of value for an
   hour of work.
