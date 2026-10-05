# Melusina Runtime Rig + Retarget CANON — 2026-10-05

**Status: CANON.** This document defines the authoritative runtime rig, retarget pipeline and
idle/aim chain for Melusina as of 2026-10-05. Where any older doc, plan or asset name disagrees
with this file, this file wins. Owner-authorized commit: *"the CANON RUNTIME MELUSINA RIG AND
RETARGET"*.

---

## 1. THE CANON RETARGET RECIPE

**Every** retarget into `SK_Melusina_Skeleton` must use this recipe. Raw retarget output is
**known-defective** and must never be shipped.

```
1. batch_retarget_animations(retargeter_path, source_anims, output_folder, name_prefix)
      NEVER pass overwrite=true — it crashes the editor inside
      FMonolithAnimationActions::HandleBatchRetargetAnimations().

2. copy_bone_pose_between_sequences(
      source_path = /Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX,
      dest_path   = <each retargeted clip>,
      bone_names  = [arm_stretch_l, arm_stretch_r, forearm_stretch_l, forearm_stretch_r],
      source_time = 0.0,
      apply_to_all_dest_frames = true)

3. VERIFY with get_animated_bone_transform (space=world, frame=0) on
   shoulder_l / arm_stretch_l / forearm_stretch_l / hand_l.
   REQUIRE:  15.774 | 28.561 | 28.615  (±1 cm)
   REJECT:   34.789 |  9.520 | 28.615

4. save_asset on EACH output. save_dirty_assets does NOT pick these up.
```

### Why (the reference-pose interruption, solved)

The target skeleton's **reference pose** holds `arm_stretch_l` at 34.758 and `forearm_stretch_l`
at 9.520. Melusina's mocap clips actively write **15.774 / 28.561**. Totals match — 44.278 vs
44.335 — so it is the **same arm length redistributed**, which is why it reads as raised/stretched
shoulders rather than a longer arm. Any retarget that does not write a translation for those bones
inherits the reference pose and ships the defect.

Proven with two independent donors (Sparrow, Shinbi) producing byte-identical bad output, and
confirmed present in her **own live idle** (`CuteIdle V10`, fixed 2026-10-05).

### Levers that do NOT work — do not retry

| lever | result |
|---|---|
| `set_retarget_chain_settings` `translation_mode` on the arm chains | output byte-identical; never reaches those bones |
| the retarget pose (`get_retarget_pose`) | returns **rotations only** — no translation field |
| skeleton `Skeleton`-mode translation retargeting | tried and rejected earlier; same lever |

---

## 2. THE CANON RIG FACTS

Her rig is **not** mannequin. Assume nothing.

| chain | bones |
|---|---|
| arm | `shoulder_l → arm_stretch_l → forearm_stretch_l → hand_l` (+ `arm_twist_*`, `forearm_twist_*`) |
| leg | `thigh_stretch_l → leg_stretch_l → foot_l → toes_01_l` (+ `thigh_twist_*`, `leg_twist_*`) |
| root | `root` — **there is no `pelvis` bone** |
| feet | `foot_l/r`, `toes_01_l/r` — **there are no `ik_foot_l/r` bones** |
| aim | `spine_01_x`, `spine_02_x`, `spine_03_x` |

Donors (Sparrow, Shinbi) are standard UE4-mannequin: `clavicle / upperarm / lowerarm / hand`.

**Frozen — never modify:** the canonical skeleton, the six owner-approved SparrowArchery clips,
the WaveHarp shape keys.

---

## 3. CANON RUNTIME ASSETS

| asset | path | role |
|---|---|---|
| `ABP_Melusina_Current` | `Melodia/Characters/Melusina/` | the runtime AnimBP (canonical) |
| `IK_Shinbi` | `Melodia/Characters/Melusina/Retarget/` | source IK rig for Shinbi (mannequin-named) |
| `RTG_Shinbi_To_Melusina` | same | Shinbi → Melusina retargeter (19 FK chains, 9 ops) |
| `A_Shin_Idle`, `A_Shin_Idle_pose`, `A_Shin_Idle_stand` | `Animations/ShinbiIdles_20261005/` | staged Shinbi idles, arm-corrected |
| `A_Shin_Cast` | `Animations/ShinbiCast_20261005/` | staged Shinbi cast, arm-corrected |
| `A_Melusina_Idle_Mocap_RootX` | `Animations/Locomotion/` | **the arm-convention reference clip** |
| `A_HERO01_..._CuteIdle_..._V10_RetargetedExactV10` | `Cinematics/Shorewake/HERO01/IdleCanonicalDirect_20260909_V10/Retargeted_V10Exact/` | her live overworld idle — **arm-corrected 2026-10-05** |

### ABP runtime chain (canonical)

```
StateMachine(MelusinaLocomotion) → Slot_0(DefaultSlot) → { Slot_4(UpperBody), LBB_0.BasePose }
Slot_4(UpperBody) → L2C_2 → ModifyBone_0(spine_02_x aim) → C2L_2 → LBB_0.BlendPoses_0
LBB_0.Pose → L2C_0 → FootPlacement_1 → KawaiiPhysics_0(c_kilt_master_x) → CopyBone_0(eyes)
           → C2L_1 → ModifyCurve_1(blink) → L2C_1 → C2L_0 → Root
```

- **Upper-body aim**: `AimRotation` (Rotator) + `ModifyBone` on `spine_02_x`, additive, layered into
  the `UpperBody` slot. Verified live.
- **Layer-mask law**: `Slot_4(UpperBody)` feeds `LBB_0.BlendPoses_0` as a **blend layer**. A layer
  only affects bones its branch filters select. The mask must carry **11 filters** — `spine_01_x`,
  `spine_02_x`, `spine_03_x`, `shoulder_l/r`, `arm_stretch_l/r`, `forearm_stretch_l/r`, `hand_l/r`.
  Without the arm filters the draw/cast montage is **silently blended away** and the arms never move.
- **Slot discipline**: `PoseSlot = TEXT("UpperBody")` — cast/charge clips must never replace the legs.
- **Foot IK**: `FAnimNode_FootPlacement` (AnimationWarping, enabled in the `.uproject`).
  `PlantSpeedMode=Graph`, `IKFootRootBone=root`, `PelvisBone=spine_01_x`,
  legs `foot_l/toes_01_l` and `foot_r/toes_01_r`. Verified: feet level (`foot_z_delta 0.004`),
  arms unaffected. **Caveat: the node is marked Experimental in the engine.**

---

## 4. THE CASTER / ARCHER HYBRID SCHEMA (binding)

This hybrid is **intentional** — preserve it. Owner ruling: *"LMB is caster animation with floating
astrolabe; RMB is full Sparrow charged draw/hold/fire."*

| input | mode | clips | instrument form |
|---|---|---|---|
| LMB press → release | **caster basic** | `CastStanceAnim` → `CastShootAnim` | floating astrolabe (`AstrolabeOffset`) |
| RMB (aim) + LMB | **archer charged** | `ChargeDrawAnim` → `ChargeHoldAnim` → `ChargeFireAnim` | bow form (`Bow_Deployment`) |

Live measurement 2026-10-05:

| phase | arm chain | state |
|---|---|---|
| idle | 15.774 / 28.561 / 28.615 | ✅ canon |
| caster stance + release | 15.774 / 28.561 / 28.615 | ✅ canon |
| **archer full draw** | **34.789 / 9.520 / 28.615** | ❌ **defect — open** |

**Open item:** the six owner-approved SparrowArchery clips carry the reference-pose defect, so her
arms currently change convention between LMB and RMB — a visible pop at the mode boundary. The fix
is the §1 recipe applied to those clips or to fixed copies in a new folder. **Owner decision
required — the clips are frozen.**

---

## 5. DEPRECATED / STALE — superseded by this canon

Do not use these as a current health proxy, do not resurrect them, and do not build new work on
them. They are retained for provenance only.

| asset | location | why stale |
|---|---|---|
| `RTG_UE4Mannequin_To_Melusina` | `Retarget/_Archive/` | `translation_mode=None` on every chain; source of the reference-pose defect class |
| `RTG_Sparrow_to_Melusina` | **deleted** | owner-rejected collapsed-shoulder result |
| `RTG_Melusina_OldToV2`, `RTG_Melusina_to_DollRig`, `RTG_Melusina_to_Zundamon` | `Retarget/_Archive/` | superseded rig generations |
| `IK_Melusina_Source_Old`, `IK_Melusina_Target_V2` | `V2Test/` | superseded rig generations |
| `IK_Melusina`, `IK_Melusina_Body` | `Characters/Melusina/` | superseded by `IK_Melusina_Body_Current` |
| legacy retargets | `Animations/_Archive/LegacyRetargets_20261001/` | already archived |

**Still live — do NOT deprecate:** `IK_Melusina_Body_Current` (the shared target rig used by the
working mocap lane; the §1 fix deliberately avoids editing it) and `IK_UE4Mannequin_Source`.

### Superseded claims in older docs

- `A_Melusina_Idle_Mocap_RootX` as the Idle state's clip — **stale**. The Idle state plays the
  `CuteIdle V10` clip (now arm-corrected).
- "shoulder stress / reference-pose interruption is open" — **resolved for the idle and the
  retarget pipeline**; still open for the six Sparrow clips only.

---

## 6. OPERATIONAL TRAPS

1. `batch_retarget_animations` + `overwrite=true` ⇒ **editor crash**. Never pass it.
2. Monolith param key names are not guessable. Wrong keys are **accepted silently and do nothing**
   (an empty layer mask still reports success). Read the schema from
   `Plugins/Monolith/Source/**` before a first call on any action.
3. `set_retargeter_rigs` takes **`asset_path`**, not `retargeter_path`.
   `get_retargeter_info` cannot resolve any retargeter — use `get_retarget_chain_settings`.
4. Creating a retargeter leaves it with **0 ops**; assigning rigs seeds them. **Save afterwards** or
   the seeded ops are lost (the on-disk asset stays a ~1 KB stub).
5. `set_retarget_chain_bones` edits the **IK Rig**, not the retargeter.
6. To clone a retargeter use UE Python (`unreal.EditorAssetLibrary.duplicate_asset`) — no Monolith
   action exists.
7. `save_dirty_assets` does not pick up retarget outputs — `save_asset` each one.
8. Capture PIE with `editor.capture_pie_movement_clip` (lit frames). **Never pass `overwrite`.**
   Gemini video QA is unavailable (account out of credits) and is not needed — `vision_analyze` on
   the captured PNGs is the working eye. **Single-frame vision reads are unreliable; prefer
   numbers, and treat contradictory reads as noise.**
9. `set_state_animation` **recreates** the state's player node — re-set `bLoopAnimation=true`
   afterwards or the state will not loop.

---

## 7. EVIDENCE

- `Saved/Audit/MelusinaWaveHarpContact_20261004/draw_pose_layer_mask_fix.json` — the layer-mask fix
- `Saved/Audit/MelusinaWaveHarpContact_20261004/shoulder_reference_pose_interruption.json` — the arm diagnosis
- `Saved/Audit/MelusinaWaveHarpContact_20261004/ABP_Backup/` — pre-change ABP
- `Saved/Audit/MelusinaWaveHarpContact_20261004/ClipBackups/` — `CuteIdle V10` original
- `.hermes/plans/2026-10-05_melusina-fluid-runtime-presentation.md` — the audit + presentation plan
- `.hermes/plans/2026-10-05_shinbi-caster-integration.md` — the Shinbi integration plan
- Skill: `melodia-retarget-to-melusina`