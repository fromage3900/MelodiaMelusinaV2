# Assets — Chapter 02 Shorewake Calling

Outfit rows follow the wardrobe catalog contract. Do not invent slots.
World-building contract: `Docs/WorldBuilding/WORLD_BUILDING_SOURCE_OF_TRUTH.md`.

| Need | Asset | State |
|---|---|---|
| Water outfit | `SK_ShorewakeDress_*` (retargeted Melusina465, Magical variants) + `MI_Melusina_Dress_Shorewake` | rigged; canonical usdc at `Saved/` (270k v, 28 mats) |
| Catalog row | `Cos_ShorewakeDress` | exists; dress grant belongs to `UMelodiaWardrobeSubsystem`, not `melodia:item:` |
| Animated fabric | `T_DressShorewake_ScaleMask`, `T_DressShorewake_ScaleShimmer` + PearlWoven 16-frame set | needs `MF_FlipbookScrub` (`specs/materials/MF_FlipbookScrub.v1.json`) |
| Boat | Starskiff kit: hull/brass/cushion/wake-emission MIs, regal bake, `T_Starskiff_Brass_Patina_Mask` (pair with SurrealFabric BrassPatina 6x5 atlas) | imported 09-05, dressed |
| Reef | SeaAbove/Prototype/Reef kit (kelp/coral/starfish OBJs, `MI_SeaAbove_Cloth_Banner`) | present; height-aware PCG live |
| Dressing | `PCG_SeaAbove_BellTreeGarden` | present |
| Preview reward row | `Cos_Charm_SkiffShell` | preview-only in `encounters.json`; do not apply to DA until the chapter editor lane is assigned |
