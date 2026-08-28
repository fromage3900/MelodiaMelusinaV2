# Session Closeout - Source Control - 2026-08-27

## Current State

- Hybrid source control is approved: Git owns code, configuration, tooling, documentation, and automation; Perforce is for lock-sensitive or large creative assets.
- Local Helix Core pilot is reachable at `localhost:1667` as user `froma`, with depot `//melodia/...`.
- Typemap is verified: `.uasset`, `.umap`, `.blend`, and `.fbx` use `binary+l`; `.json` is `text`.
- Two-workspace test proved exclusive checkout enforcement. The one-file lock pilot is Perforce change `1`.
- Perforce change `2` seeds `//melodia/Exports/...` with 50 files. The staged source and workspace matched before submit; no files remain checked out.
- Git copies of `Exports/` remain intentionally until backup and clean-machine cutover validation. Do not edit the same export through both systems.

## Operational Commands

```powershell
p4 info -s
p4 files //melodia/Exports/...
p4 opened -a //melodia/Exports/...
```

## Twelve-Hour Git Triage

Windows Scheduled Task `Melodia Source Control Triage` runs every 12 hours as the interactive
`froma` user. It invokes `Tools/source_control_triage.py` in report-only mode and writes
`Saved/Audit/source_control_triage.json`. It never stages, commits, pushes, resets, or deletes.

The report groups changed paths by ownership. `review-only` includes `Content/`, `Exports/`,
`RawArt/`, and binary formats; these require an explicit human decision and are never eligible
for automatic Git batching.

To create an isolated Git batch, add exact text-only Git-owned paths to
`specs/source_control_batches.json`, set `ready` to `true`, then run:

```powershell
.venv\Scripts\python.exe Tools\source_control_triage.py --commit-ready <batch-name>
```

The command refuses a batch if the worktree contains extra changes, if a named path is not dirty,
if it includes review-only content, or if whitespace/Python syntax validation fails.

## Verified Guardrail

`Tools/art_gates.py` now uses Git-tracked `Content/**/*.uasset` while Git owns Content, and falls back to a workspace scan once Git has no Content assets after a Perforce cutover. This prevents a zero-asset false pass.

Validation command:

```powershell
.venv\Scripts\python.exe Tools\art_gates.py --summary
```

The current run found 2,671 assets and correctly ran all four offline gates. It currently fails `duplicate_short_names` due to 33 non-baselined duplicates; resolve or deliberately baseline that existing debt separately.

## Do Next

1. Move Helix Core from the local workstation to shared storage or a VPS, then configure backup, checkpoint, journal rotation, and a restore drill.
2. Add a collaborator workspace and prove selective sync plus an Unreal project open.
3. Complete the `Exports/` clean-machine and backup validation before removing its Git/LFS ownership.
4. Do not seed `Content/` until the active `.uasset` changes are committed or otherwise reconciled and sufficient storage is available. At this session, `Content` measured 72.09 GB, `Exports` 7.09 GB, and `C:` had about 35.93 GB free.
5. Fix the 33 new duplicate short-name violations before the next baseline change.

## Non-Negotiables

- One source-control owner per path after cutover.
- Never use `git clean -fd` or `git checkout -- .` during migration.
- Do not enable or configure the Unreal Perforce provider until the depot is shared and the editor configuration change is approved.
