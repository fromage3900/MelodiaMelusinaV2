# Session Closeout — 2026-09-22 (water-hair bake + render lane)

Lane folder: `Saved/Audit/melusina_bake_staging_20260922/` (README_STAGING.md is the
front door). Plan: `docs/plans/MELUSINA_WATERHAIR_BAKE_RENDER_POLISH_PLAN_2026-09-22.md`
(PR #299). Evidence + harness: PR #300. Closeout adds this handoff, the final bake
verify, and the lane skill.

## What worked (counts)
- 6 meshes UV-staged from a fresh disk copy of the 2.39 GB harp WIP (GUI session untouched)
- 6 OBJs staged (2 via manual writer after a silent 0-byte exporter failure)
- 24 Copernicus maps baked (1024², seed 20260922) + re-bakes (two-sided merged thickness,
  HairB AO restore) — FINAL VERIFY PASS on all 24
- FLIP: smoke res-48 PASS, full res-72 bake 240 frames = 480/480 non-empty bobj
- Render: lit 240-frame turntable running overnight on gen2 (Cycles OPTIX 48+adaptive),
  vision-gated GO at frame 60
- UE bundle staged: 24/24 textures + manifest + runbook (editor closed; imports = next sitting)
- Merged: PR #299 (plan), PR #300 (evidence + harness scripts)
- New skill: `melodia-waterhair-bake-render-lane`

## What I learned (hazards)
- Blender C++ wm.obj_export silently writes 0-byte OBJs (bypass: hand-rolled writer).
- bakegeometrytextures::2.0 bakes flat on point-class uv; vertex-class required.
- Baker has ONE custom output (11); second custom signal needs a second baker.
- One-sided thickness rays self-hit open sheets; two-sided + >=8 mm offset + merged bake
  + quadrant UV padding is the honest pattern (uvtransform parms: sx/sy/sz, tx/ty/tz).
- Auto-levels on a p99==0 map makes a binary mask — check percentiles first.
- EEVEE headless animation crashes the NV GL driver; Cycles OPTIX is the stable path.
- write_still=True writes the filepath literally; only animation=True numbers frames.
- Full-frame exposure gates lie when sky dominates — gate the subject crop, then eyes.
- FLIP: frame_range_custom read-only; deactivate non-MESH participants; smoke at res 48.

## What remains blocked
- UE imports: editor closed tonight — run RUNBOOK_UE_IMPORT_20260922.md next sitting.
- Left eye: no L-side iris/cornea mesh exists in the WIP — owner must choose
  (body-material region vs new mesh) before any left-eye bake/wiring.
- Lit render completion: overnight background process; its evidence JSON
  (render_sequence_evidence.json) + regenerated frame sheet land when the notify fires;
  push as a tiny follow-up branch if the session is gone.
- Queued (R5): hair UV island-padding pass, FLIP Alembic export + import, G: texture
  relink (Material.021_Normal.png, pre-existing), flipbook lookdev wiring.

## Key discoveries
- The baker's single-custom-output constraint and the merged cross-strand thickness
  pattern (now in the copernicus skill).
- FLIP engine manifest (`flipdata.sim`) proves obstacle/inflow config before debugging.
- Subject-crop exposure gating; contact-sheet-driven review as the polish driver.

## Final stats
| Item | Count |
|---|---|
| Staged meshes | 6 (3 hair, 2 iris, 1 eyelash) |
| Copernicus maps | 24 (1024², 4 channels × 6) — final verify PASS |
| FLIP frames | 240 @ res 72 (480/480 bobj non-empty) |
| Render frames | 240 @ 1080p (lit, running overnight) |
| PRs merged | #299, #300 |
| Skills touched | copernicus-dress-bake, flip-fluids-bake, blender-headless-stage (patches) + 1 new |
| Owner gates open | G-A left eye, G-B dusk frames (deleted), G-C material variants |
