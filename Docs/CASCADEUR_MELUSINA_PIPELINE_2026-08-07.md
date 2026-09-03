# Cascadeur Melusina Pipeline

## Authority

Cascadeur is the authoring source for new Melusina animation. Lane A is the
default: animate on `updated_melusina_rig_noclothes.fbx`, preserving the real
Melusina deform skeleton and ARP bone names. Lane B, AutoRig plus retargeting,
is fallback only.

### Current staging result

The staged Quaternius source is a generic CC0 animation library and must not be
sent to the direct Melusina importer. It is reserved for the manual Cascadeur
retarget pass:

- Source: `Imports/Animations/Cascadeur/Source/Quaternius/UAL1_Standard.fbx`
- Target: `Imports/Animations/Cascadeur/Target/SK_Melusina_Cascadeur_Target.fbx`
- Provenance: `Docs/CASCADEUR_QUATERNIUS_PROVENANCE_2026-08-07.md`

The currently staged `updated_melusina_rig_noclothes.fbx` also fails direct
Lane A preflight today: it is 24 FPS with 432 bones and uses names such as
`DEF_eye.L` and `c_kilt_master.x`, while the live UE contract is 30 FPS, 465
bones, `DEF_eye_L`, and `c_kilt_master_x`. Do not import it directly. Either
export a corrected target-skeleton FBX from Cascadeur or explicitly use the
retarget fallback.

## Export Contract

- Animation only; do not export mesh or materials.
- 30 FPS.
- Bake all deform joints.
- Preserve ARP/deform bone names.
- Root motion disabled for locomotion clips unless explicitly requested.
- Keep `DEF_eye_L`, `DEF_eye_R`, `c_kilt_master_x`, `head_x`, and `root`.
- One animation clip per FBX.

## Folder Contract

Drop exports into:

`Imports/Animations/Cascadeur/Inbox/`

Use names such as:

- `CAS_Melusina_Idle_Serene.fbx`
- `CAS_Melusina_Breathing_Additive.fbx`
- `CAS_Melusina_Land_Soft.fbx`
- `CAS_Melusina_Victory_Twirl.fbx`
- `CAS_Melusina_Glide_Start.fbx`

## Offline Gate

Run `Tools/scan_cascadeur_fbx.py` with Blender before opening Unreal:

```text
blender --background --python Tools/scan_cascadeur_fbx.py -- input.fbx report.json
```

The report must show `lane_a_ready: true`, 30 FPS, an armature, and no missing
required bones.

## Unreal Import

Run inside the Unreal Editor:

```python
import import_cascadeur_anim as cascadeur
print(cascadeur.import_inbox())
```

The importer is animation-only and targets:

- Mesh: `/Game/Melodia/Characters/Melusina/SK_Melusina`
- Skeleton: `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton`
- Destination: `/Game/Melodia/Characters/Melusina/Animations/Cascadeur`

No retargeter is used in Lane A. Do not use the absent/unconfirmed
`RTG_UE4Mannequin_To_Melusina` unless Lane B is explicitly selected and the
asset is first verified.

## First Batch

1. `CAS_Melusina_Idle_Serene`
2. `CAS_Melusina_Breathing_Additive`
3. `CAS_Melusina_Land_Soft`
4. `CAS_Melusina_Victory_Twirl`
5. `CAS_Melusina_Glide_Start`

The current mocap idle remains the live idle until the new serene clip passes
verification. The first Cascadeur idle should replace only the speed-zero
sample in `BS_Melusina_Locomotion`.

## Pizzazz Layer

- Idle: breathing, weight shift, soft glance variation.
- Landing: skirt settle plus `NS_SakuraPetals_v2`.
- Glide: shawl lift, hair lag, restrained sheen.
- Victory: storybook twirl plus petal burst.
- Perfect rhythm result: brief outline/material pulse, UI confirmation, and
  optional camera emphasis.
- Good result: UI only; no camera shake.

These effects remain cosmetic. Do not delay damage, turns, battle results, or
save transitions.

## Wiring

Use `Tools/t3d_anim_injector.py` for Blend Space and AnimBP wiring. Do not use
the crashing `blueprint_query:compile_blueprint` action. Use the existing
animation-query/T3D paths and verify after each import.
