# P0 exploration → wardrobe → Glide → portal probe — 2026-08-31

Status: **source/runtime seam proven; real-input and restart/load checks completed 2026-09-01**.

## Built contract

- `FMelodiaCosmeticRecord` now declares an optional `UnlockRewardId` and
  `bAutoEquipOnUnlock`.
- `UMelodiaWardrobeSubsystem` consumes the existing narrative
  `OnRewardRequested` event, grants through the canonical narrative record, and
  auto-equips through the player's existing `UMelodiaWardrobeComponent`.
- `AMelodiaTravelInteractionPortal` queries the existing
  `UMelodiaTraversalCapabilityRegistry`; its prompt changes between locked and
  unlocked text, and `TryInteract` fails closed while the capability is absent.
- `Cos_Accessories_MelusinaV2` maps `reward.first_resonance_echo` to immediate
  equip. Its existing `form.first_resonance_echo` still owns the Glide grant and
  still requires `challenge.first_resonance_echo.completed`.

## PIE observations

Clean process, `/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap`:

1. Before exploration completion, `BP_MelodiaPortal_Hub::IsTraversalUnlocked`
   returned `false`, block reason `capability_blocked_or_locked`.
2. Stepping the single music node through the PIE probe produced
   `HitCount=1`, `PerfectCount=1`, `Score=100`, `bCompleted=True`.
3. Logs then showed, in the same frame:
   - wardrobe granted `Cos_Accessories_MelusinaV2` with grant id
     `reward.first_resonance_echo`;
   - wardrobe equipped it into Accessories;
   - world challenge and music-key bridge committed exactly once.
4. `Wardrobe::IsSlotEquipped(Accessories)` returned `true`.
5. An airborne `RequestTraversalMode(Glide)` was accepted; the grounded request
   correctly rejected with `glide_requires_airborne_state`.
6. The portal subsequently returned unlocked with block reason `None`, and its
   live `PromptText.Text` changed to `Continue exploring  [F]`.
7. Editor ended with zero dirty packages.

## Verification

- Closed-editor `BS_GodFileEditor Win64 Development` build: PASS.
- `Melodia.Wardrobe`: 6/6 PASS after replacing the invalid abstract
  `UActorComponent` companion test fixture with a concrete `USceneComponent`.
- GameplayHook, TraversalIntegration, EquipRoundtrip, and SaveLoadRoundtrip: PASS.

## Certification boundary

The exploration trigger in this run was reached with `K2_SetActorLocation`, and
the airborne Glide request used `pie_call_function`. These calls prove the live
authority/data chain, not player-input routing. Do not record `music_world_key`,
wardrobe, traversal, or portal as a new real-input ledger PASS from this report.
The next certification run must use focused viewport movement/equip/glide/
interaction input and capture a report plus frames.

## 2026-09-01 closeout checks

- Real-input-equivalent focused movement crossed the integration-map blocker and
  produced `Accessories equipped = true` after the existing music node's
  `HitCount=1`, `PerfectCount=1`, `Score=100`, `bCompleted=true` result.
- Canonical save slot `P0_Shorewake_Validation` was written, the UnrealEditor
  process was fully restarted, and `load_canonical_jrpg_slot_detailed` returned
  `LOADED_NARRATIVE_RESTORED`, and `ApplyWardrobeState` restored Accessories;
  `IsSlotEquipped(Accessories)=true` after the restart.
- `BP_Starskiff_MK2` now derives from native `AMelodiaStarskiffPawn`, owns
  floating movement and MoveForward/MoveRight input, performs capability/range
  boarding checks, possesses the player on board, supports disembark, and
  requests canonical boat traversal. It is placed in
  `LV_SeaAbove_Prototype`; PIE boarding and movement were exercised after the
  build with `TryBoardNearestPlayer=true`, `IsBoarded=true`, and movement input
  accepted.
- Focused automation: `Melodia.Wardrobe` 6/6, `Melodia.P0` 4/4,
  `Melodia.Quest.Shorewake` 1/1, and
  `Melodia.Melusina.Traversal.CapabilityContract` 1/1.

## Rebind attempt 2026-09-01

A non-destructive Blender export was produced at
`Saved/Audit/melusina_lookdev/retargeted/SK_ShorewakeDress_Melusina465.fbx`.
It uses the archived canonical `SK_Melusina_FIXED_Hair.fbx` armature (463 FBX
bones), corrects the source's 100x unit mismatch, removes the 1,705-bone cloth
armature, retains the 106 vertex groups shared with the canonical armature, and
exports the dress with the canonical armature modifier. Blender re-import
confirms one 463-bone armature plus the dress mesh. Unreal import/assignment is
pending because the editor became unavailable during the import transaction;
the original asset was not modified.

## Remaining boundary

The newest `SK_ShorewakeDress_Magical` is indeed skinned, correcting the earlier
blanket statement that all available sources were 2-bone. Its imported asset has
1,705 bones and its own `SK_ShorewakeDress_Magical_Skeleton`; Melusina's body has
465 bones and uses `SK_Melusina_Skeleton`. It is therefore skinned, but not yet
compatible with Melusina's skeleton. No destructive remap was attempted; the
next safe step is a proper 465-bone skin-bound/IK-retargeted export or an
owner-approved compatible skeleton binding.
