# Melodia Visual Reference Index

**Status:** 2026-09-04  
**Purpose:** Canonical discovery point for image reference boards, concept sheets, visual targets, and known missing/uncommitted boards.

> Agents: **start here before searching dated art/research handoffs.** Never fabricate a path for a board you cannot find.

## Committed visual canon on `main`

## Melusina House reference boards

**Canonical folder:** `Docs/References/MelusinasHouse/`

These are committed, immediately viewable working boards on `main` and should be the first stop for Melusina House visual/modeling work:

- `Docs/References/MelusinasHouse/REF_01_EXTERIOR_ROUND_BAROQUE_PINK_BLUE.jpg` — exterior silhouette, pearl-pink / blue-lavender / gold palette, tower balance, shell/ornament language.
- `Docs/References/MelusinasHouse/REF_02_GEOMETRY_NODES_BUILD_SHEET.jpg` — Geometry Nodes decomposition and procedural-vs-hero-authored breakdown.
- `Docs/References/MelusinasHouse/REF_03_CUTAWAY_INTERIOR_FLOW.jpg` — cutaway, room flow, stair/tower relationships, interior-light rhythm.
- `Docs/References/MelusinasHouse/README.md` — canonical usage order and interpretation notes.

Important reconciliation note: old laptop PR #81 stored 130-byte Git LFS pointer forms of these JPEG paths. The pointer metadata declares the same nominal image sizes as the viewable copies already on `main`; do **not** replace the current visible working copies merely because a recovery branch shows different blob SHAs.


### Mara Elettra Vell + Ebenezer

**Primary canonical image**

`Docs/Art/Images/CharacterConcepts/mara_elettra_vell_ebenezer_primary_visual_canon_2026-08-30.webp`

Use this as the first visual reference for:

- Mara modeling/sculpting;
- silhouette and outfit work;
- expression/pose blocking;
- Ebenezer styling;
- future concept elaboration.

Supporting specification:

`Docs/Art/MARA_EBENEZER_STYLIZATION_SPEC_2026-08-29.md`

### Sea Above / Shorewake P0 visual target

`Docs/Art/Images/shorewake_shader_flow_sea_above_p0_visual_target_2026-08-29.svg`

Use as a committed technical/visual target, not as proof that every referenced runtime asset is final.

## Production sheets that describe visual direction

These are text-first production sheets and should not be mistaken for committed raster boards:

- `Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md`
- `Docs/Art/GOD_THAT_MOLTS_PRODUCTION_SHEET_2026-08-29.md`
- `Docs/Art/WHITE_CURRENT_PRODUCTION_SHEET_2026-08-29.md`
- `Docs/Art/MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md`
- `Docs/Art/MONOLITH_CONCEPT_ART_BACKLOG_2026-08-26.md`
- `Docs/Art/FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md`

## Important missing / stranded-board reality

Several older research documents discuss planned 16:9 boards that are **not actually present on current `main`**.

For example, older toolchain research mentions planned/recovered boards under paths such as:

- `Docs/Research/Images/Toolchain/`
- `Docs/Art/Images/sea_above_level_stack_16x9.svg`
- `Docs/Art/Images/sea_above_melusina_character_board_v0.svg`

Those paths are **not current committed-main canon** as of this index.

Do not tell the owner “the board exists” merely because a dated research document planned it.

## PR #28 note

PR #28 contains 25 changed files, but only two image assets:

- Mara/Ebenezer primary visual canon
- Shorewake/Sea Above shader-flow SVG

Those same two image assets are already present on current `main`.

PR #28 is therefore **not** a hidden cache of the missing toolchain/Monolith boards.

## Laptop / house visual evidence

`recovery/laptop-main-20260904` contains current Melusina House Blender source versions and documents a hero render at:

`Saved/Audit/melusinashouse/v7_base_hero.png`

That hero PNG is referenced by the recovered session notes but was **not found committed on current `main`** during this discovery pass.

The committed branch does contain many `Saved/MelusinasHouse/*.blend` source versions. Use the laptop discovery index before declaring house visual work absent.

## Discovery rules

When asked for a visual reference:

1. check this index;
2. check the exact listed path;
3. check `Docs/References/` (especially `Docs/References/MelusinasHouse/` for house work);
4. check `Docs/Art/Images/`;
5. check relevant recovery/laptop branches only if the current indexes explicitly say work is stranded there;
6. only then search dated research/handoff prose.

Classify the result as one of:

- **CANONICAL COMMITTED IMAGE**
- **COMMITTED TECHNICAL VISUAL**
- **TEXT-ONLY PRODUCTION SHEET**
- **BRANCH-ONLY SOURCE**
- **REFERENCED BUT UNCOMMITTED**
- **PLANNED / MISSING**

This prevents agents from confusing a plan to create art with art that actually exists.
