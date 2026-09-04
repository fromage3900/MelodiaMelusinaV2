# MELUSINA HOUSE — V6 ROOM-SHELL BUILD PLAN (from-scratch reset)

**Created:** 2026-09-03
**Status:** ACTIVE — supersedes V4/V5 incremental passes
**Canonical refs:** `melusinashouseplan.md` (working scale + palette + assembly contract), REF_01 (massing/trim/color spec), REF_02 (kit-of-parts decomposition)
**Note:** REF_03 (cutaway interior) is corrupt on disk (renders black); interior layout authority is melusinashouseplan.md §12 until re-exported.

---

## Why reset

The V4 STAGED2 checkpoint fails AAA on its own render evidence: hero camera buried inside
geometry, untextured clay surfaces, trim reads as pasted boxes, no cornice articulation, no
UV-projected shingles. The V4/V5 scripts were scene surgery — one-off Python against one
blend — not reusable builders. V6 rebuilds as a **kit of GN room-shell presets inside Melodia
Studio**, assembled piece by piece, each stage screenshot-verified live.

## Authority

- All geometry via Melodia Studio builders (`deploy/surreal_arch/melodia_gn/`), registered with
  `register_builder`, category-tagged. No standalone scene scripts that bypass the addon.
- Working scale, palette, and assembly contract from `melusinashouseplan.md` (13.2 × 9.8 m,
  wall 3.42 m, ridge 8.4 m, tower 10.5 m; blush plaster / iridescent blue-lavender roof /
  warm brass / pearl trim / aqua glass / lavender fabric).
- Massing from REF_01: **three interlocking volumes** — tall 2.5-story core, lower left
  veranda wing with wraparound porch, right cylindrical tower (~¼ facade width, 3.5 stories,
  onion cap + finial, set slightly forward). U-shaped footprint embracing the front yard.
- Roof grammar: steep (~60°) main roof, undulating/scalloped bargeboards, arched dormers,
  trefoil gable peak, secondary lower gable left, onion dome right.
- Window rhythm: **tall-skinny → round oculus → tall-skinny**, vertical bias, no repetitive grid.
- Trim: carved bargeboards, clustered/spiral columns, thick surrounds with keystones,
  lace-like balusters.
- Color hierarchy (from board): dark saturated iridescent blue-lavender roof > light cream
  walls > bright white trim > warm amber glass glow > grey stone hardscape > periwinkle
  landscape, twilight sky.

## Module set (exact GN group names)

Registered in Melodia Studio, one builder each, all `MEL_mh6_` prefix:

| # | Group | Role | Category |
|---|-------|------|----------|
| 0 | GN_MH6_00_BaseDisc | Circular terrain plot, stone ring, path stubs | structures |
| 1 | GN_MH6_01_RoomShell | THE core preset: curved wall segment w/ floor slab, cornice ring, window/door cutter boolean branch, bevel; params: Width, Depth, Height, Curve, Thickness, Openings | structures |
| 2 | GN_MH6_02_RoofShell | Steep tent/gable shell w/ scalloped bargeboard edge, dormer cutout branch; params: Span, Rise, Curl, Eave | structures |
| 3 | GN_MH6_03_TowerShell | Cylinder body, string course, balcony ring, onion cap + finial; params: Diameter, Height, Cap Bulge | structures |
| 4 | GN_MH6_04_WindowDoorKit | Arched door, round window, tall arched window, shutter pair; each emits frame + cutter pair | set_dressing |
| 5 | GN_MH6_05_PorchKit | Clustered spiral columns, vaulted ceiling hint, curved stair, lace balustrade | set_dressing |
| 6 | GN_MH6_06_TrimPass | Cornice/dentil/string-course profiles (reuses MEL_mh_aaa_cornice + dentil), keystones, bargeboard scrollwork | ornament |
| 7 | GN_MH6_07_ScallopRoof | UV-projected shingles (reuses MEL_mh_aaa_scallop_uv) per roof shell | set_dressing |
| 8 | GN_MH6_08_GardenKit | Beds, bushes, hanging vines, wisteria, mushrooms, lanterns | set_dressing |
| 9 | GN_MH6_09_InteriorRoom | Round-plan interior partitions per plan §12: music nook (left), kitchen (right), stair (rear-right), loft above | structures |
| 10 | GN_MH6_10_MasterAssembly | Joins 0–9, exposes master controls, visibility switches | structures |

Existing builders to REUSE (no duplication): `MEL_mh_aaa_cornice`, `MEL_mh_aaa_dentil`,
`MEL_mh_aaa_scallop_uv`, `MEL_mh_aaa_lissajous_pearl`, `MEL_music_treble_clef`,
greybox room kit, house_dress set-dressing, `MEL_greybox_*`.

## Room shells (the piece-by-piece sequence)

Each piece = build preset → stage on base disc → screenshot gate → next piece.

1. **Base disc** — ground plane, stone ring, path stubs
2. **Core shell** — center volume w/ entry opening + oculus cutter
3. **Veranda wing shell** — lower left volume, open porch edge
4. **Tower shell** — right cylinder, slightly forward
5. **Roof shells** — main steep tent + left lower gable + onion cap
6. **Window/door placement** — rhythm pass per REF_01
7. **Trim pass** — cornices, bargeboards, keystones, balustrades
8. **Porch kit** — columns, stair, vault
9. **Garden kit** — periwinkle masses, wisteria on tower
10. **Interior rooms** — round-plan partitions + hero furniture anchors
11. **Master assembly + lookdev** — golden-hour light, emission glass, render sheet

## Verification contract

- Every builder passes headless verify (realized vert count > 0) before staging.
- Screenshot gate after every numbered piece into
  `C:/Users/brenn/melodiamelusinav2/Saved/Audit/melusinashouse/v6_*.png`, vision-checked.
- New blend per session: `Saved/MelusinasHouse/House_Mansion_v6_<piece>.blend`.
- No agent saves over V4/V5 blends or the live portfolio stage.

## Known defects carried forward

- `MH_PearlPlaster_Pink` etc. materials exist but are flat — lookdev pass (noise roughness,
  iridescent roof variation, warm emission) is piece 11, not skipped.
- REF_03 corrupt: re-export from source before interior piece 10 if the boards matter.
