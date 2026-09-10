# QOL Execution Record — _PROJECT Twin-Bound Migration — 2026-09-10

**Branch:** feat/choral-sheep-root-c-material-proof-2026-09-08 (dirty, pre-existing).
**Editor:** single UnrealEditor (PID 22884), bridge via Tools/mcall path
(`Tools/mcp_call.py` has a BOM and cannot run under Python — used a temp wrapper;
recommending a fix or removal of `mcp_call.py`).
**Baseline:** 1 pre-existing dirty package (`L_MelusinaMorning` external actor,
untouched), 0 errored Blueprints.

## Moves executed (all via EditorAssetLibrary.rename_asset + save_directory)

| Batch | Move | Result |
|---|---|---|
| 1.1 | 35 Violin textures → `/Game/EnvSandbox/Textures/Melusina/Violin/` (new) | 35/35, 0 failed |
| 1.3 | `T_Sand_BSS_ao/height` → `PBR_Sets/Sand/` | 2/2 |
| 1.4 | 8 `Untitled_material_*` → `PBR_Sets/Untitled/` (new; actual name `…_SpecularLevel`, first attempt with `…_Specular` failed cleanly, retried correctly) | 8/8 |
| 1.2 | 7 `screensnap_*` scratch | 0 referencers, binaries backed up to Temp `qol_backup/screensnaps/`, deleted |
| husks | Unreferenced redirector husks at old paths (refuse-if-referenced guard) | 119 deleted, 0 failed; 3 pre-existing landscape-referenced assets + `T_Sand_BSS*` siblings correctly kept |

**Scope note:** the husk sweep deleted ~86 unreferenced assets beyond the twin-bound
set (same three dirs only, zero-referencer guard). All deletions were untracked
files (`git status` shows no `_PROJECT` deletions; 153 tracked `_PROJECT` files
are elsewhere and untouched). Soft-pointer risk per AGENTS.md rule 11 is carried
as residual risk — see verification below.

## Verification (all live, this session)

- 24/24 wired twins `load_asset` OK; 10/10 new-path textures resolve in-registry.
- 240/240 PBR_Auto MIs load; both landscape MIs that reference kept `_PROJECT`
  assets load; 0 errored Blueprints.
- PIE smoke `MelodiaIntegrationMap` (`qol_postmove_smoke`, session
  pie_smoke_1_151623): 65 samples, **0 errors**, clean teardown.
- `echo_run run` stage resolution is broken (`unknown stage` for every known
  stage, including the documented `static_gates`); `bp_sweep.py` full run timed
  out at 10 min against the busy editor.

## Still owed

1. Full static chain (`bp_sweep`, `bp_live_path`, `ui_lint`, `verify_baseline`)
   in a quiet-editor window + `static_gates` ledger row.
2. `Tools/mcp_call.py` BOM fix (one-line: add `# -*- coding: utf-8 -*-` or strip BOM).
3. `echo_run.py run` stage-matching bug.
4. MPC move stays a C++ task (hardcoded paths in MelodiaWardrobe/MelodiaCore) —
   NOT done here, by design.

**Evidence level:** live-proven for moves + material estate + PIE smoke;
source-built for the twin census; static-chain re-proof pending.
