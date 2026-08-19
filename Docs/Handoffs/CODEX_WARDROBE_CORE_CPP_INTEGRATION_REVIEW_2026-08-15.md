# Wardrobe and core gameplay integration review — 2026-08-15

## Result

The closed-editor reflected build is green. The current blocker is not compilation: the runtime wardrobe contract has no catalog DataAsset to load, the Melusina pawn-side component/default map still needs editor-lane verification, and several C++ paths are not transactional enough for a save-safe Nikki-style collection loop.

This review changed no C++, `.uasset`, V2, ABP, BlendSpace, KawaiiPhysics, material, or `_TASK_QUEUE.md` files.

Evidence: [machine-readable audit](C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melodia_wardrobe_core_cpp_integration_review_2026-08-15.json).

## Build evidence

`BS_GodFileEditor Win64 Development` passed UHT, compile, and link with the editor closed. The build linked the current wardrobe and game integration modules. `git diff --check` passed with only CRLF normalization warnings.

Binary timestamps:

- `Plugins/MelodiaCore/Binaries/Win64/UnrealEditor-MelodiaCore.dll` — `2026-08-14T23:53:03.3029867Z`
- `Plugins/MelodiaWardrobe/Binaries/Win64/UnrealEditor-MelodiaWardrobe.dll` — `2026-08-15T03:41:23.6936434Z`
- `Binaries/Win64/UnrealEditor-BS_GodFile.dll` — `2026-08-15T03:41:23.6936434Z`

## C++ changes Claude should take next

P0:

1. Make `GrantCosmetic` and `EquipCosmetic` catalog-first and fail closed. Unknown IDs, missing meshes, missing catalog, and incompatible garment skeletons must not write the narrative record.
2. Broadcast the actual catalog slot from `GrantCosmetic`; the current implementation always broadcasts `Body`.
3. Register dynamically created garment components with the owning actor, disable collision/overlap, set the mesh before leader-pose setup, and validate the canonical body skeleton.
4. Add a canonical refresh path after narrative save restore. Wardrobe state already belongs in `FMelodiaNarrativeRecord`; do not create another save authority.

P1:

5. Move purchase cost authority into catalog/offer data. Remove caller-supplied prices from the shipping purchase path, resolve art-token variants through `UMelodiaTokenCatalog`, and make wallet refunds receipt/idempotency guarded.
6. Fix gacha’s false-success equip result. Prefer grant → preview → player-confirmed equip; keep auto-equip only for a deliberate first-demo policy.
7. Fix the plugin draft path contract and validate malformed JSON, duplicate IDs, invalid slots, rarity drift, and missing meshes before cooking.
8. Expose read-only catalog/form APIs for a thin Blueprint wardrobe browser.

The source already builds; these are runtime correctness and integration-contract changes, not a request to rework the Melusina animation/material lane.

## Editor/content lane prerequisites

The following are not solved by C++:

- Create `/MelodiaWardrobe/Catalog/DA_MelodiaCosmeticCatalog` with one approved demo record.
- Confirm exactly one `UMelodiaWardrobeComponent` on `BP_MelusinaJRPGCharacter`.
- Fill `DefaultGarmentMeshes` with the four staged V2 pieces: Shirt, Skirt, Boots, Accessories.
- Leave `bEnableBattleWardrobe=false`.
- Compile/save the pawn and leave a `Saved/Audit` readback containing the component count, default map, battle gate, body skeleton, and runtime asset identities.

The current V2 mesh inventory is present under `/Game/Melodia/Characters/Melusina/Outfits/V2/`, but the catalog asset and wardrobe widget were not found by the repository inventory.

## Infinity Nikki lens: what is in scope next

The strong translation is not “add more outfit meshes.” It is a durable loop:

`ability outfit / capability -> traversal or interaction gate -> gather -> material inventory -> craft/evolve -> save -> new outfit/form -> new route`

Already represented but not live-proven:

- `FMelodiaResonantForm` and the wardrobe capability provider.
- Glide movement with stamina and the module-neutral capability registry.
- Owned/equipped cosmetic fields in the canonical narrative record.
- Stock battle/shop/craft/boss/photo assets that still need Melodia authority adapters and fixture evidence.

Missing or not first-class:

- A stable-ID gathering node with capability checks, respawn policy, idempotent rewards, and save-backed state.
- A durable material inventory; actor-local progression inventory is not sufficient for crafting.
- Shop offers with catalog-owned prices, receipts, preview, and replay-safe refunds.
- Recipe/crafting/evolution transactions.
- Completion of the capability contract beyond the current Grounded/Glide request API; Dash/Swim/Dive need explicit unified state/capability coverage.
- Typed gameplay impact events that Niagara, materials, animation, and audio observe without becoming authority.
- Later P2 systems: dyes/variants, collection packs, style scoring, photo challenges, home/realm progression, NPC affinity/schedules, and social cards.

The wider integration map also exposes four adjacent authority gaps that should stay on the long-term ledger rather than being hidden inside wardrobe code:

- The canonical item transaction/save seam is not complete: `melodia:item:give` still logs a grant, and actor-local progression inventory is not a durable material inventory.
- The skill-definition bridge still needs one lookup, request-ID, cooldown, SP/mana-cost, cancellation/reset, and presentation-reference authority.
- `AMelodiaTravelInteractionPortal::TryInteract` currently routes travel without a shared capability/narrative `CanEnter` evaluation before travel or spawn-context mutation.
- Boss metadata and normal battle flow exist, but boss phase transitions, retry state, context locks, and reward-once completion are not first-class.

## Next integration slice

1. Claude applies the four P0 C++ fixes above.
2. The editor lane materializes the catalog and pawn defaults.
3. Rebuild with the editor closed.
4. On `MelodiaIntegrationMap`, prove demo grant/equip/unequip, save, full restart/load, and visual reapply.
5. Prove one authored Resonant Form through registry → Glide gate.
6. Add one gathering node and one recipe on the canonical inventory/save boundary.

The broader order after the wardrobe proof is: canonical item transaction/save seam → skill bridge → Core encounter fixture proof → unified traversal/portal gate → gathering/crafting → shop/boss/challenge transactions → photo/home → co-op.

Battle wardrobe remains disabled. Bulk gacha, photo/home/co-op, and new VFX/material authoring stay outside this slice.
