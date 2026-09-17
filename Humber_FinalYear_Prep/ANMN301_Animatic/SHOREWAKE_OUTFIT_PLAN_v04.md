# Shorewake Outfit Plan v04 — verification + garnish + special-pass inventory (2026-09-17)

School scope: Blender 5.2 only, ANMN301 animatic. No UE, no Substance session.

## 1. Verdict: she WEARS the proper Shorewake outfit (proven, not assumed)

Stage (v03) vs canonical (`Saved/CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc`):

| Stage mesh | Verts | Canonical twin | Bound to |
|---|---|---|---|
| EXPORT_Body | 18,891 | mesh_035, 18,891 (exact) | MelusinaRig, 164 vgroups, 0 orphans |
| EXPORT_Skirt | 24,356 | Melusina_Skirt family (23,656 + panels) | MelusinaRig, 73 vgroups |
| EXPORT_Shirt | 782 | collar layer | MelusinaRig, 40 vgroups |
| EXPORT_Boots | 4,092 | boot layer | MelusinaRig, 12 vgroups |

Materials match families on both sides: SBW_MELUSINA, SKIRT.003, Halftone lines-and-
circles, pearl Gradient Radial, outline shaders. (SBW is the Shorewake authoring
prefix — it appears inside the canonical itself, so it is NOT the "old look" here.
The pipeline doc's warning was about wiring old FLAT maps onto new sets; our stage
uses the canonical's own sets.)

Canonical ground truth: 267 meshes, 270,389 verts, armature-bound to rig_002.
Stage carries the 4 deforming hero layers; what it lacks is the garnish.

## 2. Garnish pass: Melusina_Bow (headless attempted honestly, GUI handoff)

Result: the bow was located (1,144 verts, canonical) but headless placement was
REFUSED by its own gate — and that refusal is the deliverable. The kinematics:
canonical space arrives rotated 90° about Z vs stage (X/Y extents swapped, Z
identical — proven by mesh_035↔EXPORT_Body comparison), AND the canonical body
stands while our Melusina sits, so no rigid transform lands the bow on her head
(closest attempt: 0.23 m from the skull — plausibly a correct hair offset, but my
image eye is down (vision 500s) and a wrong bow baked into 7 intimate panels is
worse than an unworn one. Nothing was saved; v03 is untouched.

GUI handoff (2 min, in the open v03 — do NOT headless this):
1. File > Import > USD > Saved/CANONICALSHOREWAKEOUTFITWEIGHTEDUNWRAPPED.usdc.
2. Delete every imported object except Melusina_Bow (incl. rig_002 — never let a
   foreign armature live in the stage file; the bow script's first version ate
   our own rig this way, fixed).
3. Rotate bow +90° Z, snap onto her hair beside the head, select bow then
   MelusinaRig > Pose Mode head_x > Ctrl+P > Bone (rigid — beads don't bend).
4. Eye-check CAM_Intimate, then re-render intimates 02/04/06/07/11/12/17 at 100%,
   relabel, rebuild the cut (ffmpeg trim recipe in session history), save v04.

## 3. Full addon + tool inventory to make this special (all present, all 5.2)

VSE / cut:
- VSEQF-master — 3 fades + title/end text. Audio-fade defaults OFF (silent cut).
- sound_waveform_display — timeline waveforms. Silent brief, but time the 07-08
  ripple reads to the unheard phrase for the later sound version.
- AE2BLEND_1_3_1 — After Effects camera/titles bridge. Reserve for title cards
  if VSEQF text feels thin.

Acting / motion:
- animaide-master, Animation_Layers, AnimationRetimer-main — elbow/hand passes,
  non-destructive layers over the 17 keyed poses. Retime = rebuild the cut.
- SwingyBonePhysicsAddon, Jiggle_Maker, coiled_spring — spring for the bow +
  ribbons on boarding/crossing (14-15). Bake before render, never live-sim stills.
- audvis — audio-viz; silent now, useful when the phrase gets sound.
- melodia_pose_audit (personal kit) — pose verification helper; run before panels.

Cloth / garment:
- Curtain_Maker_Pro, ctools_braids — braid/trim authoring if the bow wants company.
- voxel_skinning, wrapper_addon, quad_remesher, quad_unwrap-master, UvSquares,
  ZenUV, Mesh Cleaner Pro, MESHmachine, Beavel — the weight/retopo bench. Needed
  ONLY if a canonical deforming layer (not the bow) must move to MelusinaRig.
  Today: on the bench, not on the field.
- melodia-garment-motion (skill, Blender 5.2 cloth) — skirt settle per shot is the
  dream pass; storyboard grade says holds read fine without it. Optional special.

Look / atmosphere:
- physical-starlight-atmosphere — night-sky dome option for 01/16 wides. Current
  Sun+Area reads; try only if the mooring feels empty.
- cloud_generator, fluffy_maker, LightPainter, deep_paint_pro, Bligify,
  inkform + inkform_v1.0 — glow/line accents over wake shots (09-10, 12, 16).
- blender_kawaii_gn, blender_brutalist_gn — house GN shelves; kawaii first.
- projection_modeling — camera-projected matte backing for 16 (far shore glow)
  without modeling a shoreline. Cheap, storyboard-legal.
- SimpleBake, Sanctus-Bake, BakeLab2, auto_bake — bake the bow/glow to maps if
  EEVEE re-renders get slow.

Set dressing (reserve):
- archipack_20, surreal_arch + surreal_greybox + surreal_world + surreal_os,
  FromageRoof_v3.1, Procedural_Generation_Toolkit, sverchok-master — mooring
  architecture ONLY if 01/16 feel empty after the sky attempt. No redress before
  submission without owner call.

Pipeline ( cautions ):
- send2ue, Blender-Unreal-Export-Addon, BlenderTools-20231109043947 — UE bridges.
  OFF for school work. Enabling risks the game tree.
- LiquiFeel — ZOMBIE. Hangs headless runs; DISABLED everywhere; GUI-only if ever.
- rokoko-studio-live, Rokoko Libraries — mocap, capstone weeks 6-8.
- flip_fluids_addon — HOLD; Ocean modifier (built-in) for any real waves.
- nijigp — GP accents over renders (Lane A), draw in a 2D scene, never the stage.
- poliigon-addon — external assets need license discipline; skip for coursework.
- blender_mcp_addon, N-Panel Orchestrator, _HOLD_20260730 — leave exactly as is.

## 4. Special-pass shortlist (ranked, after the bow)

1. Tidepool glow: `Saved/Audit/copernicus_cymatic/ShorewakeTidepool/` PNGs exist
   (Chladni eigenmode maps, deterministic). Wire one as EMISSION on a COPY of the
   skirt material (never the shared original) for shots 09-16 — the reef wakes
   onto her dress. v04-blend-local, zero game impact.
2. Bow spring (SwingyBone) on 14-15 + skirt settle (garment-motion) on 11-12.
3. Projection matte far shore (projection_modeling) for 16.
4. Starlight dome (physical-starlight) if 01 feels empty.

## 5. 5.2 headless truths re-confirmed today

--factory-startup (LiquiFeel zombie); strips/strips_all + length= effects;
no Python path to GN modifier inputs (mute, don't fight); interface defaults DO
write but didn't cure MK38 (tree-internal constants); depsgraph update before
to_mesh reads; MSYS paths double — native C:/ in headless scripts; PIL/numpy
from system python, never bundled.
