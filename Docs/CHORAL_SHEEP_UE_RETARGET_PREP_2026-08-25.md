# Choral Sheep — UE Retarget Prep

**Date:** 2026-08-25 · **Status:** Blender-side export verified; UE-side steps ready
**Mesh:** `Skin_Sheep_ZSpheres2` (5918 verts) · **Rig:** `rig` (474 bones = 106 deform + 368 control)

## Goal

Make `SK_ChoralSheep` a clean UE skeletal mesh that accepts retargeted quadruped
locomotion (walk/trot/run) so the companion can move, follow, and lead in-game.

## Blender export — DONE and verified

`Tools/BlenderAddons/melodia_studio/export_choral_sheep.py` now exports with
**`use_armature_deform_only=True`**, so the FBX carries only the **106 deform bones**
(not the 368 Rigify-style `c_*` FK/IK control bones — those are unusable in UE and
would bloat/bloat `SK_ChoralSheep`).

Verified headless on a copy of `choralsheep.blend`:
- mesh `Skin_Sheep_ZSpheres2`, armature `rig`
- **exported deform bones: 106 / total rig bones: 474**
- sample bones: `root.x`, `c_thigh_b.r/.l`, `thigh_twist.r/.l`, `foot.r/.l`,
  `toes_01.r/.l`, `c_tail_00.x … c_tail_03.x`, head/spine chains
- FBX ~455 KB, axis `-Z` forward / `Y` up, 100× scale (meters→cm)

The deform skeleton is **quadruped-friendly**: root → spine → neck → head + ears,
4 leg chains (`thigh/foot/toes`), and a 4-bone tail. This maps cleanly to a
horse/deer/goat source skeleton.

> **Known caveat:** the body mesh currently has **0 vertex groups** (not yet weight
> painted to the rig). Export succeeds regardless, but the FBX is not a true skinned
> skeletal mesh until skinning lands. Finish weight painting before the final import.

## UE-side steps (editor, once mesh is skinned)

1. **Import** `SK_ChoralSheep.fbx` → `/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep`.
   - Skeleton Type: **Create new** (`SK_ChoralSheep_Skeleton`). Do not reuse Sir/Melusina's.
   - Confirm only the 106 deform bones appear in the Skeleton asset (no `c_*` controls).
2. **Set the mesh on the definition** (NOT the Blueprint — per runbook):
   - `DA_ChoralSheepDefinition` → `NPCDefinition.SkeletalMesh` = `SK_ChoralSheep`.
3. **Author the sheep IK Rig** (`IK_ChoralSheep`) — Control Rig asset. This is the
   retarget source/target skeleton. Define the quadruped chains you need:
   - `pelvis`/root, `spine`, `neck`, `head`
   - `thigh.l/r` → `foot.l/r` → `toes.l/r` (4 leg chains, IK)
   - `tail` (4-bone chain)
   - `ear.l/r` if you want ear reactions
   **Never reuse `IK_Melusina_Body_Current`** — the sheep needs its own rig.
4. **Retargeter** (`RT_QuadrupedMocap_To_ChoralSheep`):
   - Source: a horse/deer/goat skeleton (imported mocap, or a free UE quadruped).
   - Target: `IK_ChoralSheep` chains above.
   - Author the bone-chain mapping, then auto-generate the retarget pose.
5. **Animations** — retarget quadruped walk/trot/run onto the sheep's skeleton, then
   wire into an `ABP_ChoralSheep` locomotion blendspace over `GroundSpeed`
   (reuse the `BS_Melusina_Locomotion_Hybrid` pattern; sheep needs its own blendspace).
6. **Set `ABP_ChoralSheep`** on `DA_ChoralSheepDefinition` → `AnimationBlueprint`.

## Retarget-friendly bone list (deform, for mapping)

`root.x`, spine chain, `c_neck`, `c_head.x`, `c_skull_*`, `c_ear_01/02.l/.r`,
`c_thigh_b.l/.r`, `thigh_twist.l/.r`, `foot.l/.r`, `toes_01.l/.r`, `c_tail_00…03.x`,
plus facial `c_eye`, `c_jaw`, `c_lips`, `c_cheek` (great for Harmonize/Guide emotes).

## Files
- `Tools/BlenderAddons/melodia_studio/export_choral_sheep.py` — deform-only FBX export (verified)
- `Tools/BlenderAddons/melodia_studio/sheep_shine.py` — 10 color/shader variations
- `Tools/BlenderAddons/melodia_studio/sheep_shapekeys.py` — expression shape-key panel
- Source of truth: `ChoralSheepDefinition.json` (drop-in contract, `reimport_policy`)
