# Melusina — most-fluid runtime presentation: audit + plan

Owner request 2026-10-05: *"stage proper idles from Shinbi, and use our learned and working systems
to finalize and do final contact sheets for Melusina, and audit and make an updated plan for the
absolute most fluid runtime presentation for Melusina possible."*

Author: Hermes (Melusina). Status: **PLAN + AUDIT.** Everything marked DONE was measured today;
nothing else is claimed.

---

## PART A — AUDIT: what is actually true right now

### A1. The retarget pipeline — SOLVED today (was the biggest blocker)

**Symptom.** Every retarget into Melusina produced the same arm defect — the
"reference-pose interruption" named as a red blocker in `CURRENT_STATE.md`.

**Proof it was the pipeline, not the donor.** A brand-new Shinbi retarget reproduced the Sparrow
numbers *exactly*, to three decimals and symmetric:

| measurement                       | shoulder→arm | arm→forearm | forearm→hand |
|-----------------------------------|-------------:|------------:|-------------:|
| Her own mocap convention          |       15.774 |      28.561 |       28.615 |
| Sparrow bake (old, "broken")      |       34.789 |       9.520 |       28.615 |
| **Fresh Shinbi retarget (before)**|   **34.789** |   **9.520** |   **28.615** |

Two independent donors, identical output ⇒ the defect lived in the retarget path.

**Root cause.** The target skeleton's *reference pose* holds `arm_stretch_l` at 34.758 and
`forearm_stretch_l` at 9.520, while her mocap clips actively write 15.774 / 28.561. A retarget
that does not write a translation for those bones inherits the reference pose. Note
34.758 + 9.520 = 44.278 and 15.774 + 28.561 = 44.335 — **the same total arm length, redistributed.**
It is a redistribution, not a longer arm. That is why it reads as a raised/stretched shoulder.

**Levers that do NOT work (tested, do not retry):**
- `translation_mode` on the arm chains — set `StretchBoneLengthUniformly` on both arms, saved,
  re-retargeted: output **byte-identical**. The chain setting does not reach these bones.
- The retarget pose — `get_retarget_pose` returns rotations only, no translation field at all.
- Skeleton `Skeleton`-mode translation retargeting — already tried and rejected earlier.

**The fix that works.** A clip-level correction, non-destructive:
`copy_bone_pose_between_sequences` (source = `A_Melusina_Idle_Mocap_RootX`, bones =
`arm_stretch_l/r`, `forearm_stretch_l/r`, `apply_to_all_dest_frames = true`). It writes her
convention's constant translation onto the retargeted clip. Verified: all outputs now read
**15.774 / 28.561 / 28.615** exactly. Touches neither the shared skeleton nor the target IK rig,
so her working mocap lane is untouched.

**This is now the standard retarget recipe:**
```
1. batch_retarget_animations   (NEVER pass overwrite=true — it crashes the editor)
2. copy_bone_pose_between_sequences on the four arm bones
3. measure with get_animated_bone_transform; require 15.774 / 28.561 / 28.615 ± 1 cm
4. save_asset each output explicitly (save_dirty_assets does not pick these up)
```

**Editor crash, isolated.** `batch_retarget_animations` dies inside Monolith's own
`HandleBatchRetargetAnimations()`. The trigger is the `overwrite` parameter; the identical call
without it succeeds. This is the crasher already recorded in `CURRENT_STATE.md` — now it has a
specific repro.

### A2. Assets staged today

| asset | path | state |
|---|---|---|
| `IK_Shinbi` | `Melodia/Characters/Melusina/Retarget/` | created from `Shinbi_Skeleton` |
| `RTG_Shinbi_To_Melusina` | same | 19 FK chains, 9 ops, saved |
| `A_Shin_Cast` | `Animations/ShinbiCast_20261005/` | retargeted + arm fix, saved |
| `A_Shin_Idle` | `Animations/ShinbiIdles_20261005/` | retargeted + arm fix, saved |
| `A_Shin_Idle_pose` | same | retargeted + arm fix, saved |
| `A_Shin_Idle_stand` | same | retargeted + arm fix, saved |

`AnimationWarping` is now enabled in `BS_GodFile.uproject` (uncommitted) — the engine's own
`FAnimNode_FootPlacement` is the foot-IK solution; see D1.

### A3. Runtime state that is already good (do not regress)

- Upper-body aim offset on `ABP_Melusina_Current`: `AimRotation` + `ModifyBone` on `spine_02_x`,
  layered into the `UpperBody` slot. Verified live in PIE.
- Slot discipline: `PoseSlot = TEXT("UpperBody")` — draw/hold/fire no longer replace the legs.
- Layer-mask fix: the `UpperBody` slot feeds `LayeredBoneBlend.BlendPoses_0` as a layer, and the
  layer's branch filters previously excluded the arm chain, so **the draw montage never reached
  her arms**. 11 filters added; the draw pose is now real.
- Kawaii physics on the skirt (`c_kilt_master_x`), hair on its own rig.

### A4. The single biggest remaining defect

**The draw hand is 73.4 cm from the string centre at full draw.** Measured live, after the
layer-mask fix, with the bow correctly gripped. This is not a graph bug and cannot be closed in
the AnimGraph: her hands are **101 cm** apart at full draw while the authored `Draw` moves the
string only **30 cm**. The string physically cannot reach the hand.

Contributors, in order:
1. **Pose reach** — her draw pose spans 101 cm of hand separation; the source rig's was 80 cm.
2. **Draw travel** — 30 cm, authored in the Blender source blend (`ME_WaveHarp_Rev08_...blend`),
   and the shape keys are frozen under the current owner freeze.

---

## PART B — the most fluid runtime presentation: plan

Ordered by value per unit of risk. Each step has a measurable exit gate.

### B1. Wire the staged Shinbi idles (highest value, lowest risk)

The owner ruling already names Shinbi the **feminine caster reference**. Her idles are staged and
arm-corrected. Replace the Idle state's clip in `ABP_Melusina_Current` (currently
`Animations/Locomotion/A_Melusina_Idle_Mocap_RootX`) with `A_Shin_Idle_stand`, keeping the mocap
clip documented as the fallback.

**Exit gate:** PIE idle holds 9 s with no T-pose, no arm pop at the state entry, and feet planted.
Rollback is one clip reference.

### B2. Real aim offset from Shinbi's AO grid (replaces the procedural stand-in)

Shinbi ships a **complete aim-offset grid** — 16 assets, `Idle_AO_C/L/R × U/C/D` plus the `LB*`
column. Retarget the 9 needed poses with the recipe in A1, build an `AimOffsetBlendSpace` on
`SK_Melusina_Skeleton`, then **replace** the procedural `ModifyBone` aim with a real
`RotationOffsetBlendSpace`.

This is the correct destination for the aim: the procedural node is a stand-in that works today,
but a real AO gives authored, art-directed extremes instead of a clamped linear rotation.

**Exit gate:** at ±30° pitch and ±45° yaw the pose matches the corresponding AO asset within
tolerance, and no shoulder stress at the extremes.

### B3. Foot IK via the engine's own node (AnimationWarping is enabled)

Add `FAnimNode_FootPlacement` to the ABP and configure it for her rig:

| setting | value | note |
|---|---|---|
| `PlantSpeedMode` | **Graph** | Manual mode needs per-foot speed curves she does not have; Graph derives speed from root motion |
| `IKFootRootBone` | `root` | her skeleton has **no `pelvis`** |
| `PelvisBone` | `spine_01_x` | closest available; she has no pelvis bone |
| Leg L | FK `foot_l`, Ball `toes_01_l`, `NumBonesInLimb = 2` | chain is `thigh_stretch → leg_stretch → foot` |
| Leg R | FK `foot_r`, Ball `toes_01_r` | |

**Two honest caveats, both unverified until tested:** she has **no dedicated IK foot bone**
(`ik_foot_l/r` do not exist), so `IKFootBone` must fall back to `foot_l/r`; and her leg chain is
stretch-bone rigged, not mannequin. If the engine node cannot be configured for that, *that* is
the demonstrated blocker that justifies a bespoke node — not before.

**Exit gate:** feet plant on a slope and on stairs with no interpenetration, and no foot slide
over a 10 m walk at the measured 217 cm/s.

### B4. Close the draw contact (the real blocker)

Owner decision required — three routes:

1. **Scale the draw pose's reach** from 101 cm toward ~80 cm (retarget the Sparrow draw set with a
   reach correction). Cheapest; no rig work; the 30 cm draw travel stays authored.
2. **Increase the bow's draw travel** past 30 cm. Correct end state, but the shape keys are frozen
   and it means touching the Blender source blend.
3. **Split it** — modest pose pull-in plus a modest travel increase.

Recommendation: **1 first**, because it is measurable in isolation and reversible, and it will show
how much of the 73 cm it actually closes before anyone touches the rig.

### B5. Final contact sheets (G6)

After B1–B4 settle. Per the existing G6 spec: transient diagnostic cameras in Morning with PPV
disabled, 36×24 mm filmback, full-body front at 24–35 mm, left/right 30–45° three-quarter views,
side profile, 50 mm hero contact view. Rows = view, columns = idle / cast onset / release /
recovery / draw / hold / fire / return, each frame labelled with run, time, active clip and slot.

Capture with `editor.capture_pie_movement_clip` (writes lit PIE frames) — **and never pass
`overwrite`**. The earlier Gemini path is unavailable (account out of credits) and is not needed.

---

## PART C — traps to carry forward

1. `batch_retarget_animations` + `overwrite=true` ⇒ editor crash. Never pass it.
2. Retarget output inherits the skeleton reference pose for any bone the retarget does not write —
   always run the A1 arm fix and **measure**, never assume.
3. `set_retargeter_rigs` takes `asset_path`, not `retargeter_path`; `get_retargeter_info` cannot
   resolve any retargeter — use `get_retarget_chain_settings` instead.
4. Monolith action params are not guessable — wrong key names are silently accepted and do nothing
   (e.g. an empty layer mask still reports success). Read the schema from
   `Plugins/Monolith/Source/**` before a first call on any action.
5. Her skeleton has **no `pelvis`** and **no `ik_foot_l/r`**; her limb chains are
   `*_stretch` rigged. Any tool assuming mannequin bone names needs substituting, not assuming.
6. The canonical skeleton, the six owner-approved Sparrow clips and the WaveHarp shape keys are
   frozen. The A1 fix respects all three.