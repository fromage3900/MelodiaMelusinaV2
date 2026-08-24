# Choral Sheep

The first Resonance Garden companion slice for Melusina.

This folder contains the owner-authored source contract. The runtime definition
asset will be created only in a clean isolated RenderTests editor reservation;
the current Unreal bridge is unavailable, so no `.uasset`, map, gameplay state,
or webfront capture is claimed here.

## Runtime identity

- Noncombat exploration companion.
- Follows Melusina at 180 cm with a 75 cm acceptance radius.
- Interactions: graze, harmonize, guide.
- Musical motif: `choral_wool`.
- Style genome: `ResonanceGarden`.

## Fur ladder

- 0–400 cm: Native Groom hero.
- 400–1200 cm: shell/card fallback.
- 1200 cm and beyond: impostor or animated cards.

KawaiiPhysics is reserved for ears, tail, bell, and accessory motion. Wool
strand/shell behavior belongs to the fur backend adapter boundary.

## Rig drop-in contract

The finished animal should become a **mesh replacement**, not a Blueprint or
map rewrite.

1. Import (and later reimport) the owner-approved rig at
   `/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep`.
2. Create `DA_ChoralSheepDefinition` once. Its `NPCDefinition.SkeletalMesh`
   points at that reserved mesh path; `AnimationBlueprint` is optional and
   uses `/Game/Melodia/Companions/ChoralSheep/ABP_ChoralSheep` when supplied.
3. A `UMelodiaCompanionComponent` on the companion actor applies that
   definition to its primary `SkeletalMeshComponent` at play start. Its
   definition also owns the mesh-relative alignment transform.
4. Later revisions use **Reimport** at the same skeletal-mesh path. Do not
   change the companion actor, a placed map, or gameplay code merely to swap
   the rig.

Authoring requirements are deliberately small: Unreal centimeters, Z-up,
applied scale, a stable `root` bone at the origin in reference pose, and an
FBX skeletal mesh. Groom and animation are optional enhancements; absence of
either must leave the base sheep mesh visible and functional.
