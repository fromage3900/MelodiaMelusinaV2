# Afternoon Work Session Plan — 2026-07-12

## Objective

Turn the current mixed development workspace into a controlled, reversible work session without deleting active UE, Blender, GMM, Melodia, asset, or documentation work.

## Current baseline

- Branch: `feature/recursive-learner`
- Upstream relationship: 66 commits ahead of `origin/feature/recursive-learner`
- Working tree: source edits, binary assets, new tools/docs, daemon output, and PID files are mixed together.
- Focused GMM tests: 242 passing with `PYTHONPATH=Content/Python`.
- Python syntax compilation: passing for `Content/Python/gmm` and `deploy/surreal_arch`.
- Unreal/Blender live validation: unavailable until the relevant editor/MCP services are running.

## Safety rules

1. Do not run `git reset --hard`, `git clean -fd`, broad checkout, or destructive asset cleanup.
2. Do not commit the entire working tree as one batch.
3. Treat `.uasset`, `.umap`, `.blend`, `.fbx`, `.png`, and generated packages as evidence requiring ownership review.
4. Keep daemon staging output out of the source review set, but retain it until a retention policy is approved.
5. Every implementation slice gets its own focused diff and validation result.

## Phase 0 — Preserve and classify

- [ ] Record branch, upstream, status counts, and active PID files.
- [ ] Create a repository bundle of committed history.
- [ ] Export a patch of tracked working-tree changes for emergency recovery.
- [ ] Inventory untracked files into: source, docs, assets, products, runtime output, and unknown.
- [ ] Confirm whether PID values correspond to live processes before stopping anything.

## Phase 1 — Make the workspace readable

- [ ] Stop only confirmed stale project daemons; do not kill unrelated processes.
- [ ] Establish a local ignore/retention policy for `_staging/**`, daemon PID files, caches, and loop logs.
- [ ] Preserve daemon evidence in a dated archive or retention folder before deleting anything.
- [ ] Separate current afternoon work into explicit areas:
  - `GMM family contract`
  - `Melodia GN correctness`
  - `one Blender → UE vertical slice`
  - `documentation/status`
- [ ] Re-run Git status with ignored files hidden and a path-scoped source review.

## Phase 2 — Execute the highest-leverage engineering slice

### A. GMM family contract

- [ ] Add a pure-Python `gmm.family` package.
- [ ] Define `melodia_project_manifest_v1` fixture and validator.
- [ ] Define shared role/style IDs, provenance, units, and validation result shape.
- [ ] Add standard-library tests that do not import `unreal` or `bpy`.

### B. Melodia GN correctness

- [ ] Change the GN panel category to `Melodia Studio`.
- [ ] Make stack `enabled` update Blender modifier visibility.
- [ ] Make stack move reorder the actual Blender modifier stack.
- [ ] Add a Blender-side smoke script for register/build/attach/export/unregister.

### C. First bridge slice

- [ ] Use `musical_ornament` as the first cross-application capability.
- [ ] Export one Blender manifest.
- [ ] Validate it outside Blender.
- [ ] Add a GMM dry-run importer.
- [ ] Verify paths, transforms, counts, material hints, and provenance.

## Phase 3 — Validation and checkpoint

- [ ] Run focused GMM tests.
- [ ] Run Python compile checks.
- [ ] Run contract fixture/schema validation.
- [ ] If Blender is available, run the Blender smoke test.
- [ ] If Unreal/MCP is available, run dry-run import followed by deterministic test-stage verification.
- [ ] Review only the focused implementation diff.
- [ ] Commit only after the slice is internally coherent and its validation is recorded.

## End-of-session deliverables

1. A cleanly classified workspace, not an indiscriminate reset.
2. A recoverable snapshot of the starting state.
3. A shared GMM/Melodia contract scaffold.
4. One verified or explicitly blocked vertical slice.
5. Updated status and next-task documentation.
6. A clear list of runtime artifacts that are retained, ignored, archived, or safe to remove.

## Stop conditions

Stop and report instead of guessing if:

- a binary asset’s ownership cannot be determined;
- a process may belong to another project or user session;
- Blender or Unreal live validation is unavailable;
- a generated artifact cannot be reproduced;
- a change would require broad line-ending normalization or mass regeneration.
