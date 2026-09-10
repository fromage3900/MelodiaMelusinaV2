# Choral Sheep — UE Retarget Prep

**Date:** 2026-08-25 · **Status:** Blender-side export verified; quick-animation retarget pass active; UE-side proof pending
**Mesh:** `Skin_Sheep_ZSpheres2` (5918 verts) · **Rig:** `rig` (474 bones = 106 deform + 368 control)

## 2026-09-08 owner update

**Supersedes the stale weight-paint caveat below for the current source asset.**

The project owner confirms that the current Choral Sheep source is **fully rigged**. The August audit that reported zero vertex groups described an earlier source state and must not be used to trigger a re-rig.

Current uncertainty is narrower:
- the sheep may need a fresh **Auto-Rig Pro (ARP) export/re-export** for the current UE path;
- the repository's deform-only exporter remains a useful fallback/comparison tool;
- fresh FBX deformation and UE import/reimport still need to be verified before claiming runtime proof.

Current execution authority:
`Docs/Semester/CHORAL_SHEEP_DAY1_EXECUTION_PLAN_2026-09-08.md`

## 2026-09-10 final presentation feature — quick Blender animation retarget

The owner is actively retargeting a small set of quick animations onto the current Choral Sheep rig in Blender as the final bounded presentation feature of the current sheep pass. This is an **animation proof/polish lane**, not permission to reopen the rig, locomotion architecture, companion AI, or unrelated gameplay systems.

### Minimum acceptance gate

Call the Blender retarget pass complete when:
- at least one useful action plays on the current sheep rig without catastrophic limb twist, inverted feet, broken spine orientation, or visible mesh separation;
- the action has an explicit root-motion choice (prefer in-place for quick presentation/companion loops unless root motion is intentionally required);
- action names and source/provenance are retained so the animation can be traced later;
- any UE-bound export contains the intended deform skeleton rather than the full control rig, using the verified deform-only exporter or a freshly verified ARP export;
- one clean viewport/playback proof is captured before further cleanup;
- the resulting FBX is treated as **Blender/export proof only** until a fresh Unreal import/reimport is actually tested.

### Stop condition for this pass

Do **not** turn this final feature into a full animation-system rebuild tonight. A successful Blender retarget + clean export + proof capture is enough to close the art-side milestone. `IK_ChoralSheep`, the UE retargeter, `ABP_ChoralSheep`, blendspace wiring, and runtime locomotion remain separate UE-side evidence gates below unless they are deliberately tested.

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

> **Historical caveat — superseded 2026-09-08:** this August source snapshot reported 0 vertex groups. The owner has since confirmed the current Choral Sheep source is fully rigged. Do not re-rig based on this historical note; verify the current ARP/FBX export instead.

## UE-side steps (editor, after fresh current-source export is verified)

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
