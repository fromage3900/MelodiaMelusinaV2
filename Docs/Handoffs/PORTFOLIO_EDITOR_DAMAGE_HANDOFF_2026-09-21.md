# Portfolio editor damage — 2026-09-21 17:05

The capture level was changed through Monolith and then saved. Do not run another agent pass on it. The map is dirty against git and has not been committed.

Level: `/Game/Melodia/Characters/Melusina/Portfolio/L_MelusinaPortfolioCapture`
Presenter: `BP_MelusinaSwordsman_Presentation0`
Last committed copy of this map: `13dbc182e` (`Land canonical Melusina presentation state`). Checking that file out also throws away the shirt, boots, accessories, bow attach, and beauty camera that were added after that commit and never committed. Do not revert the umap to get the hair back.

## What broke her hair

`WaterHairMesh` was not re-rigged. The mesh, the skeleton, and `ABP_Melusina_WaterHair` on disk were not edited.

On the live component, one script did all of this:

- `set_animation_mode(ANIMATION_BLUEPRINT)`
- `set_anim_instance_class` to the generated class of `/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair`
- `visibility_based_anim_tick_option = ALWAYS_TICK_POSE_AND_REFRESH_BONES`
- `update_animation_in_editor = True`
- component tick enabled

That builds a new anim instance and forces Kawaii to simulate in the editor viewport. Leader pose was not set on the hair. Hair stays on `SK_Melusina_Hair_Skeleton`. It cannot leader-pose to the body.

Undo, in the open level, on the presenter. Select `BP_MelusinaSwordsman_Presentation0`. In Details, find `WaterHairMesh`.

- Uncheck `Update Animation in Editor`.
- Set `Visibility Based Anim Tick Option` to `Always Tick Pose`.

Do not retune Kawaii. Do not leader-pose the hair. `bBoneSubdivisionCollisionOnly` was already False. Leave it. Save the level after this, or the bad tick comes back on reload.

## What removed her eyes

`Staging_R_Iris_003_L` and `Staging_R_Iris_004_R` were already in the level. The same script then:

- set both actor scales to `0.01`
- moved them onto `VFX_EyeSparkle_L` / `VFX_EyeSparkle_R` (about `(-6, 30, 155)` and `(5, 30, 155)`)
- attached both to `MelusinaPresentationMesh` with keep-world and an empty socket
- set scale `0.01` again after the attach

A disc that was visible becomes a speck at `0.01`, and attaching it to the body keeps that speck on the skeleton. No second pair was spawned. The iris materials were not cleared.

Undo, in the World Outliner:

1. Select `Staging_R_Iris_003_L`. Right click, Detach From Parent.
2. Transform scale to `1, 1, 1`.
3. Do the same for `Staging_R_Iris_004_R`.

They are already at the sparkle coordinates. Detach and scale `1` is the whole undo. Do not assign iris textures to `MI_Melusina_IRISFRONT_001` / `Gradient__Radial__002`. That slot is not an eye. Save the level.

## Sir Melodious

Eight actors, all now scale `0.01` at exactly `(150, 0, 0)`. The level was saved after this.

- `Staging_SirMelodiousBody_001`
- `Staging_sirmelodious_Retopo_PM3D_Cube3D1_001`
- `Staging_sirmelodious_Retopo_PM3D_Cube3D24_002`
- `Staging_sirmelodious_Retopo_PM3D_Cube3D25_002`
- `Staging_sirmelodious_Retopo_PM3D_Cube3D28_002`
- `Staging_sirmelodious_Retopo_PM3D_Cube3D29_002`
- `Staging_sirmelodious_Retopo_PM3D_Ring3D2_001`
- `Staging_sirmelodious_Retopo_PM3D_Sphere3D1_001`

The first scale only matched the `Staging_Sir*` prefix, so the body changed and the `Staging_sirmelodious_*` pieces stayed full size. The second call scaled all eight and stacked them on one coordinate because their relative offsets came out zero. They are static meshes. They are not his rig and they cannot play his animations.

Assets, if you replace these actors instead of rescuing them:

- Meshes and `MI_Staging_Iris` / `MI_Staging_SirMelodious`: `/Game/Melodia/Characters/Melusina/Portfolio/Staging/`
- FBX: `Saved/Audit/melodious_eyes_export_20260921/Iris_and_SirMelodious.fbx`
- Bound maps: `sirmelo_BaseColor.png`, `tie_BaseColor.png` in `Saved/Audit/melusina_lookdev/Textures_Recovered/`
- Not on disk, do not generate: `Material.021_BaseColor.png`, `Material.021_Normal.png`, `coat_BaseColor.png`
- `SirMelodiousBody` material slot 0 was empty in Blender

## Shirt and gloves

`SetLeaderPoseComponent(MelusinaPresentationMesh)` was called on:

- `WardrobeSlot_EMelodiaWardrobeSlot::Shirt`
- `WardrobeSlot_EMelodiaWardrobeSlot::Accessories`

Boots were not changed. Both slots are on `SK_Melusina_Skeleton`, same as the body, so leader pose is the correct link. It was saved with the level. If they are still in a T-pose, the body pose they are copying is the reference pose, and the leader link is not the thing to remove.

## Blender, already saved, do not redo

`C:\EnvironmentPortfolio\harp_bow_pipeline\Melusina_Harp_HERO01_ArcherPoseV09_ARP_R08_WIP_20260912.blend` was saved in place earlier.

- `eyesCloseL` and `eyesCloseR` on `Melusina_Base` move together (frame 1 = 0, frame 14 = 0.8333). Two blinks per 7 seconds, 0.12 seconds, close faster than open.
- The `eye_ctrl` world-Y driver on `Key 120` is muted. It was stuck near `0.68789`.
- `eyeBlinkLeft` / `eyeBlinkRight` stay empty and muted. Unreal drops those on import.
- Cornea: 50 verts `DEF_eye.L`, 50 verts `DEF_eye.R`, 0 on `eyes`. Weights only. No skeleton change.
- `Material.015` already had the packed `Material.020` images from `Material.023` / `Iris.002`.

## Ctrl-click, not this level

`Content/MelodiaIntegration/Party/BP_SirMelodiousPlayerUnit.uasset` exists. `SwitchToNext` returns while `bSirMelodiousExplorationUnlocked` is false. The only set-true path is `RecruitSirMelodiousThroughStockParty`. `NotifySirRescued` only advances from `FirstDungeonUnlocked`. A mesh in the capture level does not flip that flag. Do not add a second input.

## Leave alone

- Do not play `AM_Melusina_BowAttack_Bound`, `A_Melusina_BowAttackV2_A_RangeAttack`, or `A_Melusina_BowAttackV2_PortfolioShoulders`.
- Do not hide `Portfolio_WaveHarp_Harp`.
- Do not move `CAM_Melusina_BeautyFront34`.
- Do not start PIE to inspect.
- Do not open a second editor or a second Blender.
- Do not touch `Config/DefaultEngine.ini`.
