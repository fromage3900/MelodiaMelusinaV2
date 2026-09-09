# `collab/laptop/longterm` salvage audit — 2026-09-09 (READ-ONLY, no merges)

**Status:** INVENTORY FOR OWNER BATCH PICKS · branch class: WORKSTATION (per
`BRANCH_WORKSTATION_POLICY.md` §1) · tip `825fb91c` · 90 content + 15 merge
commits unique vs `main` (`765e7ab5`) · full delta 150 files, +32,916/−293.
**Multiple merge bases** with `main` (one used: `0f9d8b8b`); per-batch base pins below.

## Batch A — House GN builders + shell proof (laptop home lane)
- `825fb91c` `melodia_house.py` +144, `presets.py` +18, roadmap +16/−4 (base: `69c442b1`)
- Grand-master absorb chain `fcef35a1..7e5304d2` (P2 families 1–9 ported) + kernel
  `4a2113b5` (param-schema layer) + shell proof `e0328da7` (C1
  `mh6_shell_adapter`, identity PASS) — base: `643510e4`-chain ancestor
- Validation: `python -m py_compile` on touched GN modules +
  `python Tools/verify_melusina_house_gn_catalog.py` + `run_blender_smoke_queue.ps1`
- Risk: Blender-addon registration collisions vs current `main` melodia_gn tree.

## Batch B — Character + SeaAbove world assets (capstone-visible)
- `0f55c2b7` `MI_Melusina_Hair.uasset` (+3 pointer — **LFS object check required**)
- `1c2cfe18` beveled reef meshes + pre-bevel backups (SeaAbove prototype)
- `59c04343` Gaea landscape + SeaAbove PCG integration scripts
  (`build_sea_above_pcg_integration.py` 843, `apply_gaea_fabric_terrain_to_environment.py` 314, …)
- Validation: LFS object presence for `.uasset`/`.blend` pointers, SeaAbove map smoke.

## Batch C — RawArt house intermediates (LFS-heavy, lowest urgency)
- 31 files under `RawArt/MelusinasHouse/`, +99/−1 — mostly `.blend` **pointers**
  (House_Mansion_v6_*, RoofRibbon, ShinglePatch, Base) + READMEs.
- Gate: `git lfs ls-files` census first; promote only blends whose objects exist
  on the LFS server; rest stay on the lane.

## Batch D — Docs/governance absorb (safe, review-only)
- `69c442b1` GIT PIPELINE LAW · `9aef3a15` sync contract + hook lanes ·
  `b8d2330d` P0/P1 + P2 ledger reconciliation (claims DONE-with-evidence —
  **re-verify each claim against current source before accepting**, discovery rule).

## Explicitly EXCLUDED from promotion
- `deploy/archive/` (quarantine history), broad `Docs/` prose not tied to a build,
  any whole-dir sync (wholesale merge is prohibited by policy).
- 21 `Imports/Data` files are tracked on the lane but `Imports/*` is gitignored on
  `main` — per-file include/exclude decision required before any batch touches them.

## Owner pick requested
Reply with batch letters to promote (e.g. "A only"); each approved batch gets its
own scoped branch + validation run before any PR to `main`.
