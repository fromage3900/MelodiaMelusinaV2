# Melusina Anatomical Study — 2026-09-09

## What was studied

Concept art reference sheets (committed to main):
- `Docs/References/VisualBoards/2026-09-08/Melusina/melusina_field_song_reference.webp` — front full-body
- `Docs/References/VisualBoards/2026-09-08/Melusina/melusina_cymatic_instruments.webp` — action/equipped states
- `Docs/References/VisualBoards/2026-09-08/Melusina/melusina_performance_outfit_song_states.webp` — chibi + full-body variants
- `Docs/References/VisualBoards/2026-09-08/MaraEllettraVell/mara_character_field_luthier.webp` — Mara reference

Plus skeleton data extracted from the `.uasset` binary (no editor):
- `Content/Melodia/Characters/Melusina/SK_Melusina_FIXED_Hair.uasset` (9.8 MB)
- `Content/Melodia/Characters/Melusina/SK_Melusina_Skeleton.uasset`

## Concept art proportions

| Sheet | Head:body | Shoulder | Waist | Hips | Legs |
|---|---|---|---|---|---|
| field_song_reference | ~6.5 heads | Narrow, slope | Extreme cinch | Wide (skirt) | Elongated ~1.5x head |
| cymatic_instruments | ~7-7.5 heads | Narrow | Extreme corset | Wide (bell) | Long, slender |
| performance_outfit | Chibi ~3.5 / Full ~6.5-7.5 | Narrow | Severe X | Wide | Spindly in dance pose |

Consistent: 6.5-7.5 head full-body, narrow shoulders, exaggerated waist-hip contrast.

## Skeleton (from binary, not editor)

20 primary bones + face controls. MetaHuman retarget (`c_kilt_` prefix).

Hierarchy:
- master_x → spine_01_x → spine_02_x → spine_03_x → neck_x → neck_1_x → neck_master_x → head_x
  - head_free, head_L/R (eye bones), jaw (with FACS: jawDrop, jawOpen, slideL/R, thrust, forward, tongueOut)
  - neck_twist, neck_global_twist
  - shoulder_l/R → arm_l/R → upperarm_twist_01/02 → lowerarm_l/R → hand_l/R
    - hand_fk/ik, elbow_pin, arm_pin, fingers_grasp
    - thumb_01/02/03, index_01/02/03, middle_01/02/03, ring_01/02/03, pinky1/2/3
  - arms_pole_l/R
- leg_l/R → leg_fk/ik → foot_l/R, foot_fk/ik, toes_l/R, toes_fk/ik, toes_ik
  - leg_twist_01/02, leg_stretch, leg_pole, foot_roll_cursor
  - foot_ik auto_stretch, fix_roll, ik_fk_switch

Full eye rig: 6-direction look + blink + squint + wide + follow.
FACS-lite face: lipCornerDepressorL/R, lipPressor, lipSuck, lipStretcherL/R, lowerLipDepressorL/R, upperLipRaiserL/R, squintL/R.

## Key findings

- Skeleton has individual finger bones — concept art's "fused fingers" are drawing simplification, NOT a rig limitation
- Hand/foot anatomy is the weak point in the concept art
- Pose: consistent contrapposto, strong bell silhouette
- Rig supports dynamic action poses (FK/IK switch + pole vector + stretch on all limbs)

## Gaps

- No committed UE5.8 viewport beauty render of the full Melusina mesh on main
- Mesh bounding box from binary is unreliable (garbled values) — proportions need editor CDO read
- The V2Test folder has SM_MelusinaBase/Shirt/Skirt/Boots/Hair pieces but no full assembled mesh reference

## Next step (UE tomorrow)

editor → blueprint_query on BP_MelusinaJRPGCharacter → get CDO skeletal mesh → read bone positions → proportion ratios → compare to concept sheets → report discrepancy
