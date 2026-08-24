# Choral Sheep — Direct Integration Runbook

## Purpose

Land an owner-authored Choral Sheep rig as a data-driven exploration companion
without changing protected lookdev maps, save authority, or the generic player
controller. The native home is `AMelodiaChoralSheepActor`; the rig is owned by
one `UMelodiaCompanionDefinitionAsset`.

## One-time editor integration

Perform this only in a healthy single-editor reservation after the owner has
approved the skeletal mesh.

1. Import (or reimport) the FBX at
   `/Game/Melodia/Companions/ChoralSheep/SK_ChoralSheep`.
2. Create `/Game/Melodia/Companions/ChoralSheep/DA_ChoralSheepDefinition` as
   `UMelodiaCompanionDefinitionAsset`.
3. Configure the definition:
   - `CompanionId`: `ChoralSheep`
   - `NPCDefinition.Role`: `Companion`
   - `NPCDefinition.SkeletalMesh`: `SK_ChoralSheep`
   - `AnimationBlueprint`: optional `ABP_ChoralSheep`
   - interactions: Graze, Harmonize, Guide
   - follow distance/acceptance: 180 cm / 75 cm
4. Create `BP_ChoralSheep` from `AMelodiaChoralSheepActor`; assign only the
   definition asset. Do not hard-reference the rig in the Blueprint.

The actor applies the definition to its native `SkeletalMesh` component. Its
query-only `InteractionRange` is 160 cm, and it can auto-follow Player 0 for a
standalone smoke. The definition also owns local mesh alignment, so a later
rig reimport changes no maps or Blueprint graphs.

## Gameplay binding

No global interaction or save hook is installed. An authored interaction
detector may call the explicit native Blueprint methods after its normal range
and prompt checks:

| Player action | Method | Effect |
| --- | --- | --- |
| Graze | `TryBeginGraze(Interactor)` | Requests the data-authorized graze state. |
| Harmonize | `TryBeginHarmonize(Interactor)` | Requests harmonize; existing rhythm signals drive its pulse. |
| Guide | `TryBeginGuide(Interactor, GuideTarget)` | Sets an explicit guide target and requests seek. |
| End action | `EndCompanionInteraction()` | Returns to follow/idle through the companion state contract. |

The methods fail closed if the player is outside the sphere, the target is
invalid, or the definition does not authorize that interaction. They do not
grant currency, write a save, alter the player controller, or materialize
world assets.

## First live test: `MelodiaIntegrationMap`

Use the integration map rather than a protected RenderTests beauty map.

1. Spawn one `BP_ChoralSheep` with `DA_ChoralSheepDefinition` assigned.
2. Verify base mesh and optional animation apply with no missing-asset log.
3. Move Melusina beyond and within the 180 cm follow band; confirm no
   `Accessed None`, Blueprint Runtime Error, Fatal, or Ensure.
4. Enter the 160 cm interaction range and run Graze, Harmonize, Guide, then
   end the action. Confirm only supported states occur.
5. Run a focused 30-second PIE smoke, teardown, and record the runtime log.

Groom, shell/card, and impostor layers are separate optional presentation
work. They may not block the base skeletal companion, gameplay smoke, or mesh
reimport path.
