# Melusina Bake Staging Lane — 2026-09-22 (hair + eyes for Copernicus + FLIP)

Owner ask: stage UV-unwrapped hair + eyes for tonight's Copernicus and FLIP bakes.
Status: STAGED AND VERIFIED. Copernicus maps DONE. FLIP full bake RUNNING (background).

## Sources (never modified)
- Live GUI session (owner's, read-only): C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend
- Staging copy (this lane): harp_wip_stage_src.blend (2.39 GB disk copy of the above)
- FLIP bake-gen copy: harp_FLIP_bake_gen1.blend (res 72, frames 1-240, full cache configured)

## UV verdicts (staging_probe.json)
- Hair render meshes Hair Strand.004 / .007 / .010: primary sets shp_uv_map + shp_uv_hair LIVE;
  shp_uv_flys / shp_uv_orn ZERO (secondary, unused tonight). 146 hair vgroups each.
- R_Iris.001 / R_Iris.002 / R_Eyelash: UVMap LIVE (full range).
- NO left-side iris/cornea mesh objects exist in this WIP (left eye likely a body-mesh
  material region on Melusina_Base / Melusina.001). Only R-side staged. Owner call later.

## Staged geometry (obj/)
- Melusina_HairA_Strand004.obj (manual v2 writer, vertex-class uv)
- Melusina_HairB_Strand007.obj (manual v2 writer, vertex-class uv)
- Melusina_HairC_Strand010.obj, Melusina_IrisA_R1.obj, Melusina_IrisB_R2.obj,
  Melusina_Eyelash_R.obj (Blender exporter)

## Copernicus bakes — DONE (copernicus_out/<stem>/T_<stem>_{BaseColor,Normal,Emission,Roughness}.png)
- 24 PNGs, 1024x1024 (Apprentice cap), seed 20260922, chain = proven dress-bake clone
  (File SOP -> VEX thickness/curvature -> 64-ray AO -> bakegeometrytextures::2.0 UVfill
  -> per-channel -> OIDN denoise -> /out image ROPs).
- Verified: copernicus_bake_verify.json — fresh mtimes, 4 distinct shas per mesh,
  zero duplicates across meshes, real per-channel pixel spread.
- Manifest: copernicus_bake_manifest.json (HIP per mesh in hip/).

## FLIP bakes
- Smoke PASS at res 48 (20/20 non-empty bobjs, fluid growing per frame): flip_config_smoke_evidence.json
- Known blockers fixed on the bake-gen copy: unhidden participants, x2.5 emitter bulk
  (FF_Drip/FF_Sheet are the only inflows; LF_TipDrip_* are TYPE_NONE GN props),
  non-mesh (CURVES) participants deactivated, frame range via TIMELINE mode.
- Engine manifest confirmed: Hair Strand.004/.007 are obstacles (hair collision live).
- FULL BAKE: res 72, frames 1-240 -> C:/EnvironmentPortfolio/FlipCache/hair_hero_20260922/
  running headless (PID 27840); evidence on completion: flip_full_bake_evidence.json
- Smoke caches (superseded): hair_hero_20260922_smoke{,2}

## Render lane — LIT RERUN (final state 2026-09-22 evening)
- Contact-sheet review drove fixes: thickness re-baked via MERGED cross-strand bake
  (quadrant-padded UVs; HairB real variation, A/C honest 0.5 fallback), HairB AO restored
  (auto-levels rejected — p99 was 0; gamma-lifted re-bake is the keeper).
- Prep gen2 = per-mesh water materials with baked AO in emission (kills the "purple
  jelly"), 3-point rig 6x-strengthened after vision review, SUBJECT-CROP exposure gate
  (full-frame gate lied — sky dominated). Vision pass: GO.
- Lit 240-frame render running on gen2 (Cycles 48 samples + adaptive 0.02, OPTIX);
  notify on completion, then render_sequence_evidence.json + regenerated sheet.
- PR #299: docs/plans/MELUSINA_WATERHAIR_BAKE_RENDER_POLISH_PLAN_2026-09-22.md
- UE bundle STAGED: Exports/MelusinaBakeStaging_20260922/UE_import/ (24/24 textures +
  IMPORT_MANIFEST.json + RUNBOOK; no mesh re-imports; FLIP via staged Alembic script).

## Trap ledger (new lessons paid for tonight)
1. Blender C++ wm.obj_export writes 0-byte OBJs for some meshes (HairA/B) with no error;
   healthy evaluated geometry, unrelated to materials/hidden flags. Manual OBJ writer
   bypasses it deterministically.
- Iris AO (Copernicus BaseColor maps) multiplied into Base Color of Material.015 /
  Material.023 / Iris.002 — the only safe wiring tonight; the water hair material is
  fully procedural (Fresnel/PBR/noise groups) and stays authored (single water writer).
- FLIP: 240 surface meshes imported into collection FLIPMeshes with the Water
  (Advance).002 material, visibility keyed to their own frame. 0 particle-only files.
- Camera: scene's authored Cam_Turntable. Output: Saved/PIE/melusina_hair_flip_20260922/frame_####.png
- ENGINE NOTE: EEVEE headless crashes nvoglv64.dll on the animation loop
  (EXCEPTION_ACCESS_VIOLATION after ~4 frames; single frames render fine). Sequence
  renders on Cycles (OPTIX fallback chain), 64 samples + OIDN denoise.
- Known pre-existing defect (not tonight's blocker): G:\Material.021_Normal.png missing
  (0.05% magenta in frame, non-hero material) — hand to the texture-relink lane.
- Verify on completion: render_sequence_evidence.json (count, motion diffs, stats).

## Trap ledger (new lessons paid for tonight)
1. Blender C++ wm.obj_export writes 0-byte OBJs for some meshes (HairA/B) with no error;
   healthy evaluated geometry, unrelated to materials/hidden flags. Manual OBJ writer
   bypasses it deterministically.
2. bakegeometrytextures::2.0 bakes FLAT when the imported uv attribute is POINT-class.
   One-vt-per-v-line OBJs produce point-class uv; Blender-style per-corner vt produces
   vertex-class uv and bakes correctly. HairC (Blender exporter) baked; v1 manual did not.
3. FLIP DomainSimulationProperties.frame_range_custom is read-only — use
   FRAME_RANGE_TIMELINE + scene.frame_start/frame_end.
4. FLIP exporter dies on non-MESH participants ("Exported object not found: <Hair Strand.002>")
   — deactivate flip participation on CURVES/EMPTY objects before any bake.
5. Res 24 smoke leaves an x2.5-bulked 4.2 cm drip at 1.17 voxels -> silent zero fluid.
   Smoke at res 48+ for cm-scale drips; full bake res 72 = 3.5 voxels.
