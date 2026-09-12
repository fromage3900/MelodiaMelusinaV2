# Kawaii Physics Placement Probe — Live Evidence

**Date:** 2026-08-14  
**Asset:** `/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe`  
**Purpose:** disposable presentation/physics fixture; no gameplay, save, travel, or GameMode ownership.

## Evidence captured

- Monolith was live on Unreal Engine 5.8, server version `0.20.3`.
- The original disk asset loaded as an empty Actor. The live contract was repaired in place; the asset was not deleted or recreated.
- Components now queried live:
  - `PreviewMesh` — `SkeletalMeshComponent`
  - `PreviewCamera` — `CameraComponent`
  - `ResetAnchor` — `SceneComponent`
- Compatible hair presentation pair:
  - mesh: `/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair`
  - AnimBP: `/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair`
  - physics override: `/Game/Melodia/Characters/Melusina/SK_Melusina_FIXED_Hair_PhysicsAsset`
- Variables queried live:
  - `InitialTransform:Transform`
  - `bKawaiiDebug:bool`
- Custom events queried in the graph:
  - `ResetSimulation`
  - `ToggleKawaiiDebug`
- Compile result: `UpToDate`, zero errors, zero warnings.
- EventGraph export result: 12 nodes, 6 connections; both custom events present.
- EventGraph fingerprint (`topology+defaults`): `75193c2ad364e7629bc88c4995f563ef02062d42`.
- Targeted `save_packages` succeeded for the probe package.
- The probe was also spawned live at `[-481.9538, 160.4159, 20]` in
  `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap` as
  `KawaiiPhysicsPlacementProbe_L3`.

## Important correction

`ABP_Melusina_WaterHair` is authored against the 148-bone hair skeleton. It must not be assigned to the 465-bone `SK_Melusina` body mesh. The probe now uses the compatible `SK_MelusinaHair` asset.

## Still open

The editor entered an unrelated bulk material cleanup/save modal loop immediately after the probe save. Monolith disconnected before the integration map could be loaded. The following are therefore not claimed:

1. probe actor placement/reachability from `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`;
2. runtime AnimBP/Kawaii playback;
3. two-run deterministic `ResetSimulation` PIE result;
4. live T3D mutation evidence.

The later map-save attempt exposed a separate file-state defect: the map package had
the Windows read-only attribute set. The attribute is now cleared, but the attempted
save crashed before the map package was written, so the spawned actor is **not yet
proven persisted**. The log also reported `Could not find root physics body` for the
probe's physics-asset override; verify the hair physics asset in a clean session and
remove or replace the override if the Kawaii AnimBP's limits data asset is the intended
runtime authority.

The probe is safely persisted on disk. Reopen the editor cleanly, verify the Monolith port, load the integration map, place the probe, and capture PIE evidence before marking the fixture L4-ready.
