# Reference Board Integrity Receipt — 2026-09-08

**Status:** PASS WITH ONE REPAIRED PATH  
**Repository:** `fromage3900/MelodiaMelusinaV2`  
**Authority:** current `main`

This receipt exists so agents do not reopen reference-board archaeology without a concrete reason.

## September 8 capstone / character visual batch

Verified present on `main`:

### Choral Sheep analytical + owner-approved boards
- `Docs/References/ChoralSheepCapstone/BOARD_01_CREATURE_FLEECE.md`
- `Docs/References/ChoralSheepCapstone/BOARD_02_CHLADNI_PATTERN_LANGUAGE.md`
- `Docs/References/ChoralSheepCapstone/BOARD_03_HYPERPOP_RAVE_CONCERT_DRAMATURGY.md`
- `Docs/References/ChoralSheepCapstone/BOARD_04_TD_HARMONIC_FIELD.md`
- `Docs/References/ChoralSheepCapstone/BOARD_05_CAMERA_COMPOSITE.md`
- `Docs/References/ChoralSheepCapstone/BOARD_06_OWNER_APPROVED_CONCEPT_SHEETS_2026-09-08.md`
- `Docs/References/ChoralSheepCapstone/REFERENCE_MANIFEST.md`

### Choral Sheep visual boards
- `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_creature_fleece.webp`
- `Docs/References/VisualBoards/2026-09-08/ChoralSheep/choral_sheep_chladni_fleece.webp`

### Mara Elettra Vell / Electra / Ebenezer visual boards
- `Docs/References/VisualBoards/2026-09-08/MaraEllettraVell/mara_character_field_luthier.webp`
- `Docs/References/VisualBoards/2026-09-08/MaraEllettraVell/mara_instrument_variants.webp`
- `Docs/References/VisualBoards/2026-09-08/MaraEllettraVell/electra_cymatic_instruments.webp`
- `Docs/References/VisualBoards/2026-09-08/MaraEllettraVell/electra_ebenezer_relationship.webp`

### Melusina visual boards
- `Docs/References/VisualBoards/2026-09-08/Melusina/melusina_field_song_reference.webp`
- `Docs/References/VisualBoards/2026-09-08/Melusina/melusina_cymatic_instruments.webp`
- `Docs/References/VisualBoards/2026-09-08/Melusina/melusina_performance_outfit_song_states.webp`

### Batch front door
- `Docs/References/VisualBoards/2026-09-08/README.md`

The nine September 8 WebP image boards are regular Git blobs on `main`; their repository paths and blob identities were verified during this closeout.

## Melusina House board set

Canonical paths:
- `Docs/References/MelusinasHouse/REF_01_EXTERIOR_ROUND_BAROQUE_PINK_BLUE.jpg`
- `Docs/References/MelusinasHouse/REF_02_GEOMETRY_NODES_BUILD_SHEET.jpg`
- `Docs/References/MelusinasHouse/REF_03_CUTAWAY_INTERIOR_FLOW.jpg`
- `Docs/References/MelusinasHouse/README.md`

These JPGs are intentionally Git LFS-managed by `.gitattributes`, so the Git tree stores pointer blobs and a hydrated checkout resolves the image bytes through Git LFS.

During this audit, `REF_01_EXTERIOR_ROUND_BAROQUE_PINK_BLUE.jpg` was missing from current `main` even though the index and README referenced it. The exact surviving LFS pointer was recovered from `collab/laptop/longterm` and restored to `main`:

- REF_01 LFS object: `sha256:4d0507ebe80649723c0092f327baf81a3ad4eb6f9d0dd7742a0aada9c708040b`, declared size 12,641 bytes.
- REF_02 LFS object: `sha256:0b3de3508c8b911fab2a1878e3943cb60ca4790894bb214e38f0686a74dab77f`, declared size 13,425 bytes.
- REF_03 LFS object: `sha256:4fb7f05c4c7a106fba59560605b9b54031f96b8b724b9bf9f0f27b75fa64ee78`, declared size 11,291 bytes.

Remote Git pointer integrity is now restored. A workstation still needs normal `git lfs pull` hydration before treating local image bytes as proven present.

## Canonical discovery rule

Start at `Docs/Art/VISUAL_REFERENCE_INDEX.md`.

Do not:
- recreate these boards because an old branch lacks them;
- replace the owner-approved Sheep boards with generic concert imagery;
- treat analytical/source-link boards as redistributed third-party image archives;
- claim an image is locally hydrated solely because its LFS pointer exists remotely.

Reopen this audit only if:
1. a canonical path 404s on current `main`;
2. Git LFS hydration fails for a listed board;
3. the owner explicitly replaces the visual lock.

**Result: the September 8 Choral Sheep / Mara / Melusina batch is intact, and the missing Melusina House REF_01 path has been repaired.**
