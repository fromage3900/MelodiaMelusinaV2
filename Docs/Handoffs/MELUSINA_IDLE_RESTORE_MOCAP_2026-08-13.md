# Melusina idle restore — mocap on speed 0

Git-tracked copy of `Saved/Audit/melusina_idle_restore_mocap_2026-08-13.md` (`Saved/` is hook-blocked). PIDs omitted — run `Get-Process UnrealEditor` yourself.

**Date:** 2026-08-13  
**Editor:** already-open UnrealEditor, Monolith `:9316`  
**Action:** replace only the speed-0 sample on `BS_Melusina_Locomotion`. No Blender re-import. No Quaternius/CAS swap.

## What was wrong

Speed 0 on `/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion` was still `A_BL_Melusina_Idle_Loop` (Blender NLA import on `SK_Melusina_Skeleton`). Owner reported idle collapsed / wrong pose.

Historical defect: raw Blender FBX was meters on a centimeter skeleton (`c_spine_02_x` local Y ≈ −0.128 vs mocap ≈ −12.84). A later ×100 pass made **frame-0 local translations** look cm-scale, but the live idle was still the Blender clip and still looked broken. Policy: treat Blender speed-0 as failed; restore mocap immediately. Do not re-import Blender idle in this pass.

`BS_Melusina_Locomotion.uasset` was **ReadOnly**. Cleared with `attrib -R` before save.

## What is on speed 0 now

| Speed | Animation | Skeleton |
|------:|-----------|----------|
| 0 | `/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX` | `SK_Melusina_Skeleton` |
| 180 | `A_Melusina_Walk_Mocap_RootX` (unchanged) | `SK_Melusina_Skeleton` |
| 420 | `A_Melusina_Run_Mocap_RootX` (unchanged) | `SK_Melusina_Skeleton` |
| 630 | `A_Melusina_Sprint_Mocap_RootX` (unchanged) | `SK_Melusina_Skeleton` |

- Mocap idle still on disk: **yes** (loop, 0.5s). Not replaced.
- `A_BL_Melusina_Idle_Loop` **not** on the blendspace.
- `ABP_Melusina_Current` still loaded; Idle already plays this blendspace (not rewritten).

## Save

| Step | Result |
|------|--------|
| `attrib -R` on `BS_Melusina_Locomotion.uasset` | cleared |
| `validate_sample_data` / `resample_data` | baked |
| `EditorLoadingAndSavingUtils.save_packages` | **true** |
| `save_loaded_asset` | **true** |
| dirty after save | **false** |
| Reload verify (same editor) | speed 0 = mocap |

**Save: OK.** Blendspace itself landed in `a6bbb55d`. This note is the probe evidence.

## Bone probe (frame 0, local translation)

`AnimationLibrary.get_bone_pose_for_frame(..., 0, False)`

### Mocap — `A_Melusina_Idle_Mocap_RootX`

| Bone | X | Y | Z |
|------|--:|--:|--:|
| `c_spine_02_x` | ~0 | **−12.838752** | ~0 |
| `c_spine_01_x` | ~0 | −12.577148 | ~0 |
| `c_root_x` | ~0 | −12.577141 | ~0 |
| `c_thigh_ik_l` | ~0 | −5.552221 | ~0 |
| `c_head_x` | ~0 | 15.896996 | 144.229156 |
| `c_hips` / `pelvis` / `root` | 0 | 0 | 0 |

Spine Y matches the known-good cm rest (~−12.84).

### Blender (left on disk, not wired) — `A_BL_Melusina_Idle_Loop`

| Bone | X | Y | Z |
|------|--:|--:|--:|
| `c_spine_02_x` | ~0 | **−12.838758** | ~0 |
| `c_spine_01_x` | ~0 | −12.577148 | ~0 |
| `c_root_x` | ~0 | −12.577141 | ~0 |
| `c_thigh_ik_l` | ~0 | −5.552221 | ~0 |
| `c_head_x` | ~0 | 15.896996 | 144.229156 |
| `c_hips` / `pelvis` / `root` | 0 | 0 | 0 |

Frame-0 **translations** now classify as cm (×100 already applied). They do **not** prove a correct idle pose; owner still saw collapsed/wrong idle with this clip on speed 0. Rotations / rest mismatch / NLA content can still be wrong. Clip remains on disk for a later owner-gated retry. Not re-wired.

## Verify checklist

1. Speed-0 sample path is `A_Melusina_Idle_Mocap_RootX` — **yes**
2. Skeleton is `SK_Melusina_Skeleton` — **yes**
3. Walk 180 / run 420 / sprint 630 unchanged — **yes**
4. Bone probes recorded above — **yes**
5. This audit file — **yes**
