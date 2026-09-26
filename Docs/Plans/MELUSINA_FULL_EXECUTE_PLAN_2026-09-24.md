# Melusina E1–E8 execution plan — updated 2026-09-24

Current status authority: `CURRENT_STATE.md`. This document specifies the remaining execution sequence. The goal remains the complete segmented BJD runtime unit, with Ashlotte and Orianna used as close visual/construction references.

## Resume here

1. Read the Melusina E1–E8 continuation paragraph in CURRENT_STATE.md and the evidence listed below.
2. Verify the connected Blender filepath is `C:/EnvironmentPortfolio/harp_bow_pipeline/Melusina_DollKit_SurfaceDetail_20260924.blend`. Live session was Blender 5.2.1 LTS, frame 0, MCP :9876, GUI PID 37756; recheck these transient values. Never open/save the hero WIP for this task.
3. Resolve the E1/P9 authority mismatch before any more bevels, gear detail, exports, or approval requests. Do not blindly rerun E0, E1 bulk, or p9_seating.py.

## New evidence that changes the next action

Fresh Cycles renders using evaluated source meshes show detached assemblies among the named E1 keepers:

| Station | Ball-to-outer-ring center distance | Current named ball radius | P9 receipt radius |
|---|---:|---:|---:|
| neck | 60.18 mm | 26 mm | 35 mm |
| shoulder_l | 142.62 mm | 24 mm | 42 mm |

These are measurements of the E1 named meshes, not proof that the P9 procedural assembly itself is defective. `deploy/surreal_arch/dollkit_pipeline/p9_seating.py` explicitly hides `MEL_dk2_*` fallback meshes after creating the procedural assembly. Earlier E1 scripts unhid and detailed those legacy meshes. This is the first discrepancy to reconcile, not a reason to translate the balls to old rings by eye.

Evidence in `Saved/Audit/melusina_doll_surface_20260924/`:
- `E1_seating_discrepancy.json`: live transforms and distances.
- `E1_material_preview.json`: render inputs and reference criteria.
- `stills_e1/E1_neck_material_cycles.png` and `E1_shoulder_l_material_cycles.png`: actual shader renders, not workbench previews.
- `_e1_material_preview.py`: reproducible isolated-scene render script; source geometry unchanged and blend not saved. It currently targets legacy E1 names and must be adapted after authority reconciliation. It leaves orphan preview datablocks; clean only its own unused preview data before a production save.

Prior key/fill/rim files were angle substitutes. They do not prove independently lit material readability. The capture completed despite unrelated FLIP Fluids Action.fcurves callback warnings; do not treat those warnings as failed renders or fix the FLIP lane here.

## Reference use throughout

- Ashlotte: inspect the landed `Reference/Ashlotte_Maedel/SC4_Ashlotte_Maedel.zip` and its balljoint/cog/ceramic/metal study parts. Use exposed ceramic spheres, seated metal cuffs, visible gaps and restrained cog clusters as concrete comparison criteria. The older runtime gap map's claim that Ashlotte is unavailable is stale.
- Orianna: inspect `Reference/Orianna_StarGuardian/StarGuardian Orianna WildRift/` for silhouette, joint rhythm, and companion/weapon placement. Use `Saved/Audit/ORIANNA_TO_MELDOLLRIG_MAP_2026-09-24.md` for the existing 15-bone mapping.
- Before declaring visual completion, compare actual study views with Melusina full-body and joint closeups. Written census notes alone are insufficient close-reference proof.
- References stay study-only; keep Melusina original geometry/materials and ship no reference meshes/textures.

## Execution and acceptance

### E1 — correct authority, then surface finish
- Inspect live `MEL_dollkit_stations` point coordinates and attributes `axis`, `ball_r`, `ball_off`, `rim`, `ball_scale`, `ring_proud`; identify the evaluated P9 hardware object and its node graph.
- Compare the procedural evaluated assembly against named E1 meshes and the p9_seating receipt. Retain the authoritative P9 construction; hide legacy duplicates. If editable parts are required, derive them from evaluated P9 geometry with station identity preserved, rather than promoting the old P6 fallbacks.
- Reconcile all 14 stations, preserve measured radii and exposed ball silhouette. Verify in segment context and across a posed sample, not only detached parts.
- Preserve stashes and apply appropriate rim/edge refinements only to the corrected keepers. Avoid modal MESHmachine operators over MCP. Script-safe stash utility and mesh bevel are available; interactive Chamfer/Fillet remains an owner operation if needed.
- Capture full assembly plus neck/shoulder closeups under real materials and separate key/fill/rim lighting. Record measured seating, no duplicate hardware, and actual render evidence.
- Only when the result is reviewable request the existing owner E1 taste approval or explicit waiver before E2. Do not mark approval on the owner's behalf. E1 bulk script completion is not E1 completion.

### E2 — clockwork gears
Resolve the installed Higgsas Spur Gear through higgsas_bridge; inspect its sockets before use. Rebuild shoulder/hip tooth silhouettes and clusters on corrected P9 keepers. No silent native fallback. Preserve joint exposure; prove evaluated geometry and moving gears with stills and distinct animation samples.

### E3 — segment detail
Light panel seams, rim holds and restrained edge treatment on the 15 MEL_seg_* pieces. Preserve porcelain character and articulation clearances; no full armor conversion. Verify full-body silhouette plus closeups.

### E4 — bone binding
Bind corrected ball/cuff/ring/gear keepers to MEL_DollRig's existing 15 bones using the Orianna station map. Account for the two segment sides of a cuff where needed. Preserve world placement on parenting. Emit hierarchy evidence with no unbound exported keeper; verify rest and posed motion without separation or double transforms.

### E5 — reusable GN presets
Build/refresh MEL_doll_* presets from reconciled P9 and E1 measurements, through the installed Higgsas lane. Require resolved groups, repeatable measured output and headless evaluation evidence. Test meaningful parameter changes; no parallel hardware authority.

### E6 — export and UE visual gate
Export only corrected original Melusina keepers to detail GLB; verify names/counts, material mapping, dimensions, rig and transforms. Prepare the existing `_dollkit_p9_reimport_inner.py` lineage for the exact export. Owner Output Log reimport and owner Ctrl+S remain the specified UE gates; no agent save_packages. Verify seated joints, gear motion, retained Nikki materials and CuteIdle after import. Export presence alone is not UE proof.

### E7 — runtime unit
Use DOLLKIT_RUNTIME_GAP_MAP_2026-09-24.md for requirements, not current status. Preserve existing gameplay ownership. Implement weapon/familiar/VFX/gear sockets; segment collision with cosmetic gear collision disabled; camera/grip proportions; DollRig-compatible animation; and the DollKit pawn path. Verify possession, input, locomotion, CuteIdle, joint motion and relevant gameplay integration in actual PIE. A preview blueprint or scaffold is not runtime completion.

### E8 — closeout
Update CURRENT_STATE.md with distinct Blender, export, UE and live PIE evidence. Audit every E1–E7 requirement before marking the overall goal complete. Prepare scoped docs/source publication as requested by the original plan; respect the working agreement's no-commit/push-without-owner-request boundary. Do not claim a docs PR exists unless created and linked. Keep this goal active while any gate remains open.

## Constraints

SurfaceDetail is the only writable blend for this lane. Hero WIP remains untouched. Staging DollBall_* is not authority. MEL_DollRig stays 15 bones. Higgsas must resolve, not silently fall back. No UE package saves by the agent. Check active editor ownership before any Unreal mutation. Reuse existing plans; put live status only in CURRENT_STATE.md. No model-specific dependency: the next model can execute this plan directly.
