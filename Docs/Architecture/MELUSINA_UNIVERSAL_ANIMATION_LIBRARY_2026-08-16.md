# Melusina Universal Animation Library — v2

## Authoritative pipeline

The portfolio stage is an ARP rig. The Blender lane therefore reuses the
existing v22 ARP operator bake and the approved in-memory remap contract:

```text
Cascadeur / Blender / foreign source
        -> canonical SK_Source_Melusina (464 bones, 30 FPS, cm)
        -> UE staging import
        -> RTG_Source_to_Melusina
        -> SK_Melusina_Skeleton / SK_Melusina
        -> audit -> optional runtime promotion
```

The authoritative stage is
`G:/EnvironmentPortfolio/BS_GodFile/Melodia_Portfolio_Stage_v22_ZenRebuild_WIP.blend`.
Automation reads it and never saves it. ARP's visual controller bake remains
the source of truth; generic Blender `nla.bake` is not a replacement for this
stage's constraint graph.

The established ARP rules are retained:

- `use_deform` wins the `thigh_stretch_l/r` collision;
- the approved ARP semantic map is combined with the contract finger map;
- inactive contract bones are completed structurally after the baked audit;
- the canonical source hierarchy is applied in memory;
- ARP's action export applies the existing metre-to-centimetre bake;
- the final artifact is animation-only and contains one clip.

## Pilot evidence

The Blender pilot is `A_BL_Source_Idle_Loop`. Its final FBX and v2 sidecar are
under `Exports/AnimationLibrary/Blender/`. Blender scanner evidence records 30
FPS, 464 bones, no meshes, underscore names, and a centimetre header. The
source stage mtime remains unchanged.

Quaternius/UAL1 Inbox clips remain `manual_required`; the Cascadeur bridge
creates a handoff report but does not pretend to perform AutoPosing, retarget,
contact cleanup, or polish. The direct Quaternius-to-Melusina retargeter is a
legacy rollback path.

The live UE pilot now has a passing staging/retarget report at
`Saved/Audit/melusina_ue_source_pilot.json`: the imported source clip is
30 FPS, centimetre-probed, loop-policy verified, saved, and retargeted through
the existing `RTG_Source_to_Melusina` chain without rebinding `SK_Melusina`.
The report also records the important project fact that
`SK_Source_Melusina` is a skeletal mesh whose existing Skeleton property
resolves to `SK_Melusina_Skeleton`; automation reuses that setup rather than
creating a second skeleton. PIE evidence passes on
`MelodiaIntegrationMap` with the expected `ABP_Melusina_Current` and zero
runtime errors.

The read-only `foot_contact_audit.py` wrapper calls the existing Monolith
`derive_foot_sync_markers` action. The ARP idle reports “static pose, no
plants”, so the sidecar is allowed to pass only for the explicit montage
consumer scope; BlendSpace still requires bilateral contact evidence. The
new pilot montage `AM_MUAL_Source_Idle` is promoted and saved with a
timestamped rollback marker. The active BlendSpace promotion remains blocked
because the idle is root-locked/in-place and cannot provide an authored
locomotion speed.

The read-only stage inventory at `Saved/Audit/melusina_stage_actions.json`
found 44 Blender actions but only the `character_rig` NLA strip
`idle_animation -> character_rigAction` is the authoritative v22 ARP character
take. No authored walk/run action was present on that rig, so the locomotion
gate remains an honest pending input rather than a synthetic speed or a direct
foreign-rig promotion.

`pipeline.py acceptance` writes the requirement-level matrix at
`Saved/Audit/mual_acceptance_matrix.json`; it remains red until live UE
staging, control-case verification, PIE evidence, and guarded promotions pass.
