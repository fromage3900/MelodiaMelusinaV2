# Collaboration Workflow

## Repository lanes

**Remote:** `origin` = `https://github.com/fromage3900/MelodiaMelusinaV2` — the source
of truth. `legacy-melodia` is the superseded `MelodiaMelusina` repo; never push to it.

Branch names **must** carry one of the prefixes `.githooks/pre-push:13` accepts, or the
push is rejected:

```
feature/   fix/   docs/   cleanup/   collab/   integration/   codex/   recovery/   cursor/
```

Use them for lanes: `collab/level-design/kaleido-nave`, `collab/material-art/toon-outline`,
`feature/pcg-environment`, `fix/character-melusina-hair`, `docs/onboarding`.
Use `integration/*` for reviewed cross-workstation extraction/handoff branches such as
`integration/house-handoff-20260904`.

> Superseded 2026-08-13: this file previously told collaborators to use bare lane names
> (`gameplay`, `pcg-environment`, `materials-vfx`, `character-melusina`, `docs-onboarding`).
> **Every one of those is rejected by the pre-push hook.** The prefixed forms above are the
> real convention and match `CONTRIBUTING.md:22-28`.

Git tracks source, Python, C++,
contracts, docs, configuration, and small metadata. Git LFS is intended to be
selective: add large UE binaries only after ownership and history justify it;
do not expand the current broad attribute policy without a migration review.
Narrowing existing tracking is a separate follow-up because it changes clone
behavior and must be coordinated with remote history.

## Editor reservation

Only one editor writer owns a given `.umap`, `.uasset`, or plugin binary at a
time. Before opening the editor, announce the map/assets and expected lane in
the shared task handoff. Before handing off, close the editor when possible and
report validation commands, changed assets, and remaining warnings.

## File locking (Git LFS) — the actual concurrency mechanism

There is **no Unreal Multi-User Editing / Concert / Switchboard** in this project.
Binary conflict prevention is Git LFS locking plus the reservation protocol above.

`.gitattributes:28-64` marks 2,224 files `lockable` (`.uasset .umap .blend .fbx .png
.psd .wav .dll` and more). LFS checks lockable files out **read-only**. A read-only
error when saving from Unreal or Blender is the lock system working, not a corrupt file.

```bash
git lfs locks                                    # who holds what
git lfs lock   Content/EnvSandbox/Environments/L_KaleidoNave.umap
#   ... edit, commit, push ...
git lfs unlock Content/EnvSandbox/Environments/L_KaleidoNave.umap
```

Rules:

- **Lock before you open the asset in an editor**, not after you have edited it.
- **Unlock immediately after your push lands.** A forgotten lock blocks everyone.
- `git lfs unlock --force <path>` steals a lock. Ask first; it can discard work.
- Locking requires network reach to `origin`. GitHub connectivity from the main
  workstation is intermittent — if `git lfs locks` times out, retry rather than
  assuming the lock server is broken.

As of 2026-08-13 **zero locks have ever been held** on this repo. That was survivable
with one contributor and is not survivable with two.

## Commit gates

- No `Saved/`, `Intermediate/`, `DerivedDataCache/`, bundles, or local machine paths.
- No unresolved merge markers.
- Run the relevant Python/GMM tests and audit scripts.
- Binary-heavy changes include an audit report or concise verification note.
- Do not force-push divergent project branches.
- Do not mix catalog-only documentation work with mass asset relocation.

## Ownership boundaries

GMM owns deterministic contracts and simulation. Unreal owns runtime assets,
Blueprints, materials, Niagara, WaterBody actors, and presentation. PCG owns
static support scatter; Niagara owns motion. Human artists own hero placement,
final composition, and authored landmark decisions.

## Handoff template

```text
Lane:
Editor: open | closed
Map/assets:
Expected files:
Validation:
Reports:
Known warnings:
Next owner:
```
