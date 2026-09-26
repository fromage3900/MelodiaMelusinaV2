# Melusina Bake Staging Lane — 2026-09-22 (hair + eyes for Copernicus + FLIP)

Owner ask: stage UV-unwrapped hair + eyes for tonight's Copernicus and FLIP bakes,
then contact-sheet review, polish, render, and UE import staging.
Final state: ALL LANES DONE + VERIFIED (lit render completing overnight on its own).

## Sources & copies
- Canonical: C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend
  (2.39 GB, owner's GUI session PID 6812 held it live all night — never touched).
- Staging copy (never saved, read-only probes): harp_wip_stage_src.blend
- Prep blends: harp_FLIP_bake_gen1.blend (smoke-verified bake config), harp_render_prep_gen1.blend
  (iris AO + FLIP sequence), harp_render_prep_gen2.blend (FINAL: per-mesh AO water materials + 3-point rig).

## UV verdicts (staging_probe.json)
- Hair Strand.004/.007/.010: shp_uv_map + shp_uv_hair live; shp_uv_flys/orn zero-filled (unused).
  146 hair vgroups each.
- R_Iris.001/.002 + R_Eyelash: full-range UVs. NO L-side iris/cornea mesh exists in this
  WIP (left eye likely a body-mesh material region on Melusina_Base / Melusina.001) — owner gate G-A.

## OBJ staging (obj/)
- Melusina_HairA_Strand004 / HairB_Strand007: manual v2 writer (one v per unique position,
  per-corner vt/vn -> Houdini reads VERTEX-class uv).
- HairC_Strand010, IrisA_R1, IrisB_R2, Eyelash_R: Blender exporter (clean).
- Blender C++ wm.obj_export wrote 0-byte OBJs for HairA/B silently — bypassed, not fixed.

## Copernicus bakes (copernicus_out/<stem>/T_<stem>_{BaseColor,Normal,Emission,Roughness}.png)
- 24 PNGs, 1024 (Apprentice cap), seed 20260922, proven dress-bake chain via token
  replacement (copernicus_bake_hair_eyes_v2.py, merged to Tools/Houdini/copernicus/).
- v2 fixes: TWO bakers (baker exposes exactly one custom output, index 11); thickness =
  two-sided rays (>=8 mm offset, sub-10 mm = honest 0.5 fallback) baked MERGED across the
  3 hair meshes with quadrant-padded UVs (thickn_merge_bake.py; HairB std 0.057 real
  variation, HairA/C open at 8 mm -> 0.5 fallback); HairB AO gamma-lift re-bake
  (hairB_ao_restore.py; auto-levels REJECTED — p99 was 0, would have made a binary mask).
- Iris AO plausible; iris/eyelash thickness = honest 0.5 (thickness not meaningful on shells).
- CLOSEOUT VERIFY: final_bake_verify.json — PASS on all 24 (real channels: fresh mtime,
  square, distinct shas, real spread; Roughness fallback maps validated as exactly
  0.5-flat, dup-check relaxed ONLY for byte-identical honest fallbacks).

## FLIP bakes
- Smoke-first at res 48 PASS (20/20 non-empty; res 24 = sub-voxel zero-fluid trap).
- Blockers fixed: frame_range_custom read-only -> FRAME_RANGE_TIMELINE; CURVES participant
  crash -> non-MESH participants deactivated; stale cache rmtree before every bake;
  emitter x2.5 bulk (FF_Drip/FF_Sheet only inflows; hair meshes = obstacles, confirmed
  in engine manifest). Cache: C:/EnvironmentPortfolio/FlipCache/hair_hero_20260922/
- FULL: res 72, frames 1-240 -> flip_full_bake_evidence.json: 480/480 bobj non-empty,
  fluid to ~33k verts/frame. Smoke caches superseded: hair_hero_20260922_smoke{,2}
  (first is a Windows-lock orphan; harmless).

## Render lane (final)
- Contact sheets: contact_sheets/copernicus_maps_sheet.png + render_sequence_sheet.png;
  vision-reviewed; findings drove every fix below. Sheets regenerate at render completion.
- EEVEE headless BANNED for animation (nvoglv64.dll EXCEPTION_ACCESS_VIOLATION ~4 frames;
  single stills fine). Sequence: Cycles OPTIX->CUDA->CPU, 48 samples + adaptive 0.02 + OIDN.
- Prep gen2: per-mesh water materials Water_Advance_AO_{A,B,C} with each mesh's baked AO
  multiplied into emission (0.85) — strand-depth variation; FLIP meshes keep the authored
  material (single water writer; variants are render-lane only, gate G-C documented).
- Lighting: 3-point rig x6 after vision review caught the full-frame exposure gate lying
  (sky dominated) -> SUBJECT-CROP gate (mean 0.10-0.32); second vision pass: GO.
- Output: Saved/PIE/melusina_hair_flip_20260922/frame_####.png, 240 frames, Cam_Turntable,
  1920x1080. Unlit dusk frames deleted at lit launch (gate G-B).
- Known pre-existing defect (not tonight's): G:\Material.021_Normal.png missing
  (0.05% magenta, non-hero) -> texture-relink lane.

## UE import staging
- Exports/MelusinaBakeStaging_20260922/UE_import/: 24/24 textures (contract names),
  IMPORT_MANIFEST.json (sRGB OFF all channels; TC_Normalmap/TC_Masks), RUNBOOK (W1 maps
  on existing SK meshes — no re-import; W2 FLIP via Alembic geometry cache, Nanite OFF,
  collision NONE; W3 what NOT to import). Versioned copies: ue_import_manifest_copy.json,
  ue_import_runbook_copy.md. Alembic exporter staged: flip_alembic_export.py.

## Where things live now (merged to main)
- PR #299: docs/plans/MELUSINA_WATERHAIR_BAKE_RENDER_POLISH_PLAN_2026-09-22.md
- PR #300: lane README + evidence JSONs (Saved/Audit/...), hython drivers
  (Tools/Houdini/copernicus/), Blender harness (Tools/Blender/melusina_bake_staging_20260922/).
- Large binaries stay on disk by convention: staging/prep blends, map PNGs, render frames.

## Open items (owner-gated / queued)
- G-A left eye: body-material region or new mesh? (blocks left-eye bake/wiring)
- G-B dusk frames: deleted at lit launch (default; say so if you wanted them kept)
- G-C water material render variants: render-lane only, never the authored master
- R5 queue: hair UV island-padding pass (normal-map bleed), FLIP Alembic export + U2 import,
  G: texture relink, flipbook lookdev wiring (grandmaster W6/W7).

## Trap ledger (new lessons paid for tonight)
1. Blender C++ wm.obj_export can write 0-byte OBJs silently (healthy geometry; material
   renames/mute don't help) -> hand-rolled writer.
2. bakegeometrytextures::2.0 bakes FLAT on point-class uv; VERTEX-class required
   (one-vt-per-v-line = point-class; Blender per-corner vt = vertex-class).
3. Baker exposes exactly ONE custom output (11); a second custom signal needs a second baker.
4. One-sided thickness rays self-hit open sheets at ~0 or find nothing; two-sided rays +
   >=8 mm offset + MERGED sibling bake is the honest signal. uvtransform parms are
   sx/sy/sz + tx/ty/tz, not "scale"/"t".
5. Auto-levels on a map whose p99 is already 0 makes a binary mask — check percentiles first.
6. EEVEE headless animation crashes the NV GL driver; Cycles OPTIX is the stable path.
7. Full-frame exposure gates lie when sky dominates; gate the subject crop, then EYES.
8. FLIP: frame_range_custom is read-only (FRAME_RANGE_TIMELINE + scene.frame_start/end);
   deactivate non-MESH participants ("Exported object not found"); res 24 smokes an
   x2.5-bulked cm drip at 1.17 voxels = silent zero fluid (res 48 smoke / 72 full).
