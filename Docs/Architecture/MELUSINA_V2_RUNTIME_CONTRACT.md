# Melusina V2 Runtime Contract

## Mesh contract

- Target skeleton: `/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton`
- Bone count: 465
- Bone names: underscore-normalized contract names
- Units: centimetres
- Source: bound v22 wardrobe, never the unskinned `SM_*.fbx` exports
- Required output: five skeletal pieces with real deform groups, morphs where
  authored, approved material instances, and zero unresolved or zero-weight
  vertices

The Unreal skeleton pointer is not sufficient proof. The export sidecar and
import validator must inspect the actual required bone map used by the mesh and
must prevent Unreal from auto-adding bones to the canonical skeleton.

## Wardrobe contract

`EMelodiaWardrobeSlot` preserves existing values and appends `Shirt`, `Skirt`,
`Boots`, and `Accessories`. `UMelodiaWardrobeComponent` is the only V2 visual
authority. It restores saved cosmetics first, then applies configured defaults
only to slots with no saved selection. Every garment leader-poses to
`CharacterMesh0`.

`MelodiaOutfitComponent` remains compatibility-only until a separate cleanup;
it must not become a second source of mesh truth.

## Rollback contract

The old `/Game/Melodia/Characters/Melusina/SK_Melusina` body, current ABP,
hybrid locomotion BlendSpace, Quaternius clips, and hair runtime remain
untouched. Rollback requires changing the pawn body reference and clearing V2
default garment references; no animation retarget is required.
