# Shinbi → Melusina caster integration — plan for the next closed build

Owner request 2026-10-05: "make an updated plan for how we will integrate Shinbi on our next closed build".
Author: Hermes (Melusina). Status: PLAN — nothing here is executed except where marked DONE.

## Why Shinbi

Owner ruling (`CURRENT_STATE.md` §5): **Shinbi is the feminine caster reference; Sparrow is the
charged archery/contact reference.** Shinbi is installed but no donor binding is promoted yet.

Measured today (`mesh_query.get_mesh_info`, `animation_query.get_skeleton_info`, `get_sequence_info`):

- Mesh `Shinbi`: 85,131 tris, 53,763 verts, **169 bones**, extent 97.0 x 94.6 x 189.3 cm.
- Skeleton naming is **standard UE4-mannequin**: `pelvis`, `spine_01..03`, `clavicle_l/r`,
  `upperarm_l/r`, `lowerarm_l/r`, `hand_l/r` (+ twist bones). Not a bespoke rig.
- Caster-relevant animation set: `Cast` (0.967 s, 29 frames @ 30 fps, no root motion),
  `Ability_Q_Target_*`, `Ability_E_Jog_*`, `Ability_R_PeaceOut`, `Ability_AttackWolves_*`,
  Emotes, HitReacts, full Idle/Jog/Walk family.
- **A complete aim-offset grid**: `Animations/AimOffsets/` = 16 assets — `Idle_AO_Blendspace`
  plus `Idle_AO_C/L/R x U/C/D` and the `LB*` column (`LBC/LBD/LBU/LC/LD/LU/...`).
- `Shinbi_Wolf` companion: 5,562 tris, 59 bones, own skeleton + physics asset.

What Shinbi does **not** provide in this project: an IK Rig for her skeleton (`IK_Sparrow` exists;
`IK_Shinbi` does not) and any retargeter from her to Melusina.

## GATE 0 — fix the arm-chain mapping first, or Shinbi inherits the shoulder bug

This is the whole reason the plan is ordered this way. Measured today with
`animation_query.get_animated_bone_transform` (world space, frames 0 and 5, identical on both):

| segment                          | Melusina mocap idle | Sparrow hold |
|----------------------------------|--------------------:|-------------:|
| shoulder -> arm_stretch          |           15.774 cm |    34.789 cm |
| arm_stretch -> forearm_stretch   |           28.561 cm |     9.520 cm |
| forearm_stretch -> hand          |           28.615 cm |    28.615 cm |
| **shoulder -> hand (total)**     |       **72.83 cm**  | **70.84 cm** |

Both families total the same arm length, so her arm is **not** longer in the Sparrow clips.
The difference is *where the elbow sits*: the Sparrow bake puts 34.8 cm into the
shoulder/clavicle segment (2.2x her own convention) and only 9.5 cm into the upper arm
(0.33x). That distribution is the visible "stretched shoulder / raised arms" — not a longer arm.

Root-cause class: Melusina's arm bones are `shoulder_l → arm_stretch_l → forearm_stretch_l → hand_l`.
Shinbi (and Sparrow before her) are UE4-mannequin `clavicle → upperarm → lowerarm → hand`.
A chain map that lands the source's chain boundary one bone too far out reproduces exactly
this 34.8 / 9.5 split.

**Therefore: any Shinbi retarget using the same chain conventions as the Sparrow bake will
reproduce the identical shoulder defect on the caster clips.** Gate 0 must pass before step 3.

Gate 0 acceptance (measured, not eyeballed):
a retargeted clip must reproduce `shoulder->arm ≈ 15.8`, `arm->forearm ≈ 28.6`,
`forearm->hand ≈ 28.6` cm within ~1 cm. Use `A_Melusina_Idle_Mocap_RootX` as the reference.

## Steps for the next closed build

1. Create `IK_Shinbi` source rig from `Shinbi_Skeleton` (`animation_query.create_ik_rig`).
   Consider first testing against the existing `Retarget/IK_UE4Mannequin_Source`, since
   Shinbi's bone names are already the mannequin convention — if that rig already maps her,
   skip the new rig.
2. Create `RTG_Shinbi_To_Melusina` (`create_ik_retargeter`) targeting
   `Mocap/Retarget/IK_Melusina_Body_Current`, and set the chain mapping **explicitly** with
   `set_retarget_chain_mapping` — do not accept auto-map silently. Arms are the risk area.
3. Retarget **one** clip first: `Cast`. Not the library.
4. **Gate 0 verification** on the retargeted `Cast` with `get_animated_bone_transform`
   (the table above). If it fails, stop and fix the mapping — do not proceed.
5. Only then retarget the bounded caster set (`Cast` + the `Ability_*` the caster actually
   needs). Keep every output in `Animations/ShinbiCast_*` — a new folder, never overwriting
   the existing `CastCandidates_20261001` clips.
6. Wire-up is a **header** change in `MelodiaWaveHarpCombatComponent.h`:
   `CastStanceAnim` / `CastShootAnim` currently point at the Lyra-derived
   `CastCandidates_20261001/A_Q_Melusina_Spell_Simple_Idle_Loop` and `..._Shoot`.
   Repoint them, keeping the current values documented as fallback.
   *(header change => requires a full closed-editor build, not Live Coding)*
7. Closed-editor build; then PIE: LMB cast in `L_MelusinaMorning`, verify no shoulder stress
   and no arm-pop on cast/recovery.
8. Aim-offset end state: once step 4 passes, retarget Shinbi's 9 `Idle_AO_*` poses and build
   an `AimOffsetBlendSpace` on `SK_Melusina_Skeleton`, then **replace** the procedural
   `ModifyBone` aim currently in `ABP_Melusina_Current` with a real RotationOffsetBlendSpace.
   The procedural node is a stand-in that works today; the AO is the correct destination.

## Already DONE tonight (for context, not part of this plan)

- Upper-body aim offset: `AimRotation` (Rotator) var + `ModifyBone` on `spine_02_x` (BMM_Additive)
  layered into the existing `UpperBody` slot of `ABP_Melusina_Current`; EventGraph chain
  `GetBaseAimRotation -> BreakRotator.Pitch -> ClampAngle(±35) -> MakeRotator -> Set AimRotation`.
  **Verified live in PIE: `AimRotation = (Pitch=-22.83, Yaw=0.0, Roll=0.0)` tracking the camera.**
- Slot discipline: `PoseSlot = TEXT("UpperBody")` in the .cpp constructor; confirmed present in
  the built DLL.
- Closed-editor build: `Result: Succeeded`, 0 errors, 0 warnings.
- ABP pre-change backup: `Saved/Audit/MelusinaWaveHarpContact_20261004/ABP_Backup/`
  sha256 `ca7b2c72…` (current `3821a8f7…`).

## Constraints carried

- No new architecture; no retarget recreation for Sparrow (owner ruling, retired).
- Do not modify the six owner-approved Sparrow clips or the authored WaveHarp shape keys.
- Preserve accepted gloves/sleeves, working locomotion, and the canonical skeleton.
- No p4 submit.