# Trim Sheet Lab — close-out record (2026-09-12)

Session scope: bake 3 trim-sheet variants for Melodia Studio grounded in the
current scene meshes + Infinity Nikki doctrine; grew into a full pipeline.

## Shipped to main

- PR #195 (merged 2026-09-12, dde72faf; re-applied lane commit 62ff42f7):
  - deploy/surreal_arch/trim_sheet_lab.py — Trim Sheet Lab N-panel:
    scene-palette-driven painterly baker (albedo/height/normal/orm/zone),
    UE-emulating proxy materials (BaseTint×albedo, 3-step toon ramp, ORM,
    normal+bump; look-match only — POM/height-compete stay engine-side),
    manifest merge (schema 2: hybrid_of / wear_layer_b / lerp / emission).
  - Content/Python/melodia_trimsheet_ue.py — editor-side MI builder
    (imports Saved/TrimSheets/out PNGs to /Game/Textures/MelodiaTrimSheets,
    creates MI_TS_Melodia_{Stone,Music,Dream,Salon,Reverie} on
    M_Master_Toon_Universal with Layer-B wear wiring via the zen-family
    param contract). NOT executed — runs on desktop with editor up.
  - integration.py registers MELTS_CLASSES; material_bridge.py catalog gains
    the MI paths so the crosswalk fuzzy-matches PROXY_* slots.
  - Static CI gates pass; editor-backed gates skipped (no editor claims).
  - Registry census after merge: 564 builders, lost 0 / new 0 / errors 0.

## Machine-local artifacts (gitignored by design; reproducible from committed code)

- Saved/TrimSheets/bake_trimsheets_v2.py — painterly master bake (numpy/PIL).
- Saved/TrimSheets/bake_trimsheets_v3_hybrid.py — band-remix hybrids
  (Salon = music hero + stone body; Reverie = dream hero/body + stone millwork),
  wear Layer B (TS_Wear_Cracks; height-gated crack walks, measured 2.1%
  crack-on-flat), emission masks, manifest schema 2 merge.
- Saved/TrimSheets/stage_platform_trim.py + House_Stage_v2_trimvariant.blend —
  FND_Plinth_TRIM / FND_PorchStep_TRIM proxies: realized GN meshes, band-correct
  UVs (top=floor-ledge, sides=baseboard, corner-aligned u-axis), PROXY material;
  sources hidden, file packed. Vision-verified unlit proof.
- Saved/TrimSheets/out/ — 5 sheets × 5 maps + hybrid/emission/zone PNGs +
  trimsheet_manifest.json (schema 2) + proof renders.
- P:/tools/ArmorPaint_Test/trimsheet_sessions/ — 6 relief-jig GLBs (256² grid
  displaced by real height, packed textures, round-trip verified) + PAINT_NOTES.md.
- Tools for tests: Saved/TrimSheets/_test_lab.py (lab ops, orientation asserts),
  _test_manifest_merge.py (hybrid/wear survive rebake), _probe_* (5.2 facts).

## Verified 5.2 facts this session (bake/EEVEE research)

- EEVEE has NO bake API: bpy.ops.object.bake raises "Current render engine does
  not support baking" (probed 2026-09-12). Cycles-only for selected-to-active.
- Headless Cycles CPU selected→active NORMAL bake works: bevel+boolean highpoly
  → flat lowpoly, 16-31% non-neutral texels captured relief, margin/cage honored.
- 1024² CPU normal+AO bakes are minutes+; design the operator to bake per-band
  strips (~8× fewer texels) and run it background/overnamed, engine set inside
  the operator only — user-facing surfaces stay EEVEE.
- HEIGHT/AO need no Cycles: EEVEE ortho EMIT z-render gives the relief map;
  AO stays numpy-on-height (already shipped).
- img.pixels is bottom-up (flip ndarray rows before foreach_set); set
  colorspace BEFORE writing pixels or the buffer wipes to black.
- ShaderNodeJoinShader undefined in 5.2 — use ShaderNodeMixShader.

## Open items (owner-gated)

1. Desktop + editor up: run `py Content/Python/melodia_trimsheet_ue.py` →
   Saved/Audit/melodia_trimsheet_ue.json; that run is the MI proof (prose ≠ row).
2. ArmorPaint art pass on the relief sessions (Stone first); painted maps flow
   back through the v3 compositor with zero pipeline change.
3. melodia_ts.bake_bands (approved design, not yet built): per-band strip
   targets, EEVEE Z-render height, Cycles NORMAL only for opted-in bands,
   headless/overnight safe, manifest "hi_bake" key; pilot on Roof sheet.
4. Sheet roadmap from coverage audit: Roof, Column (closes ids 4,5,7,8,9),
   Floor+Ceiling, Opening, Ornament, Zen family + TRIM_COLOR_MAP extension
   (zen roles currently default to id 1; variant_hero 6 collides with arch_ring).
5. Known cosmetic debt: piano octave grouping in Music hero; 2K
   parameterization (band rows are hardcoded px — make fractions of S);
   _emission.png for the three base sheets.
6. Laptop local main is 20 commits ahead of origin (eyewear/GN lanes) —
   reconcile per workstation-sync skill, desktop-in-the-loop, from the
   collab/laptop/* task-branch pattern proven twice this session.
