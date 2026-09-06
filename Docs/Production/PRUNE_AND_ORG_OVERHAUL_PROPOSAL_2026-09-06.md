# Prune + org overhaul proposal — 2026-09-06

**Status:** PROPOSAL. Nothing below is executed. Every deletion needs owner (Red) sign-off per checkbox.
**Basis:** branch audit + blob audit run 2026-09-06 on local `main` (`dc240023` + working tree).

## 1. Git state at proposal time

- Local heads: only `main` + `codex/game-state-2026-09-04-checkpoint`. Local is clean.
- `main` vs `origin/main`: **3 ahead / 4 behind** — the 09-05 unify already drifted (`origin/main` tip is `40eb5cc0`, PR #96). Re-unify cadence needed or the two-lineage problem returns.
- LFS: healthy — 5213 files under a comprehensive `.gitattributes`. No action.
- Hooks: `.githooks` active (`core.hooksPath=.githooks`); pre-push forbids `main`, branch names constrained. No action.
- Dirty tree (do not commit blind): 9 files from the staleness fix (this lane) + 10 `Docs/T3D_Baseline/materials/*` mods/deletes from another active lane + 3 GN-adjacent files. Reconcile owners before any commit.

## 2. Branch prune table (remote-only; all need owner checkbox)

**Update 2026-09-06:** a ~90-branch tag archival already landed (`archive/branches/2026-09-05/*`:
copilot ×5, cursor ×13, docs ×14, feat ×7, fix ×11, integrate B00–B08, recovery ×6 incl.
`recovery/laptop-main-20260904`, triage, rescue, `fix-mh6-shell-promotion`). The remaining asks
below are the leftovers NOT covered by those tags. Verify with `git tag --list
'archive/branches/2026-09-05/*'` before deleting anything.

| Branch | Last touch | Verdict | Owner |
|---|---|---|---|
| `legacy-melodia/*` (15 branches, Jun–Aug) | dead lineage | confirm tag coverage, then delete remote | [ ] |
| `origin/copilot/fix-runners-and-review-logs`, `origin/copilot/fix-issue-in-algorithm` (if still live) | bot noise | delete remote if tag-archived | [ ] |
| `origin/cursor/surreal-architecture-slices-*` (7 branches, 07-16) | superseded slices | delete remote after extraction check | [ ] |
| merged PR branches: `cleanup/baseline-refreeze-2026-09-05` (#100), `cleanup/final-reconcile-2026-09-05` (#99), `cleanup/unify-2026-09-05` (#98), `fix/mh6-shell-promotion-20260904` (#96) | merged | safe delete remote | [ ] |
| `origin/codex/weapon-gallery-20260902`, `origin/rnd/2026-08-30-blender52-music-gn-studio`, `origin/docs/2026-08-29-character-p1-p2-canon-audit`, `origin/feature/grandmaster-melodia-studio`, `origin/pr/melusina-v22-sync` | unaudited | adjudicate one by one | [ ] |
| `origin/backup/pre-consolidation-2026-08-30` | pre-consolidation backup | keep (cheap insurance) | [ ] |
| `origin/collab/laptop/main-reconciliation-2026-09-04` | laptop lineage | keep until laptop work fully extracted | [ ] |
| `codex/game-state-2026-09-04-checkpoint` (local) | checkpoint | keep until game-state transplant lands | [ ] |

Rule: delete remote branches only (`git push origin --delete`), never rewrite shared history. `legacy-melodia` remote itself stays until its 15 branches are adjudicated.

## 3. Blob prune table (tracked; sizes at HEAD)

| Path | Size | Verdict | Owner |
|---|---|---|---|
| `Content/Python/quantum/qsharp_project/build_diag.txt` | 16 MB | build log committed by accident — delete | [ ] |
| `Content/Melodia/Characters/Melusina/Hair/SK_MelusinaHair.uasset.boneless_20260730.bak` | 9.8 MB | `.bak` in tree — move out of repo or delete | [ ] |
| `TDImportCache/hairhairhairt.tdc`, `_TouchDesigner/.../shot_import.tdn`, `project1_full.tdn` | 19 + 6.9 + 2.6 MB | TouchDesigner caches — gitignore + delete from tree | [ ] |
| `Tools/BlenderAddons/rust_gpu_sdf_addon/**/rust_gpu_sdf.pyd` (×2, same blob) | 6.2 MB | keep one path, remove the duplicate | [ ] |
| `Plugins/PCGExtendedToolkit/.git_disabled/objects/pack/*.pack` | 5.2 MB | disabled-plugin internals — delete | [ ] |
| `audit_inst_cache.json` | 4.4 MB | root-level cache file — gitignore + delete | [ ] |
| `Content/MelodiaIntegration/ResonantWorld/OfflineWorldGen/PetalCantata_3900/world.json` | 4.8 MB | review: generated output that may not belong in git | [ ] |
| `Saved/Audit/mi_naming_fix_2026-08-30.json` (+ `sweep_pbr_state.json` 9.6 MB on disk) | 7.9 MB | allowlisted, keep; cap future daemon dumps (the 09-05 +140k-line audit commit is the pattern to bound) | [ ] |

Note: deleting a tracked blob shrinks future clones, not past history. Full history surgery is explicitly out of scope.

## 4. Doc-archive policy (going forward)

- `Docs/_Superseded/` (46 entries, precedent `53321a9b`) is the archive. Superseded docs move there; they are never deleted, never edited in place.
- `Docs/Handoffs/` (283 files) is append-only memory. New sessions write `_SESSION_HANDOFF.md` + ledger rows, not new "current status" docs.
- Session-start rule stands: `python Tools/project_state.py --view session_start` before prose.

## 5. Unify cadence (prevents the next divergence)

- `main` ↔ `origin/main` re-unify at least weekly during semesters; record in `Docs/Production/MERGE_TO_MAIN_RECORD_*`.
- Daemon lanes must not check out branches mid-operation (observed 09-04) — coordinate or pin daemon to its own branch.
