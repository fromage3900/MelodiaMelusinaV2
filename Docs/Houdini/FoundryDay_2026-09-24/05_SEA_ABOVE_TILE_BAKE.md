# 05 — Gates 4–5 (P0): one Sea Above tile → UE, then the tiled bake

| | |
|---|---|
| **Purpose** | Prove FieldAtlas as supplemental world intelligence on the real Sea Above level, test-first, before any expensive tiling. |
| **Authority** | `LV_SeaAbove_Prototype` is owner-authored: its Landscape and cathedral placement (`00_CANON/*`) are canonical and **read-only** here. Existing PCG graphs keep placement authority. The `TERRAIN_HANDOFF_CONTRACT` Mesh-Terrain rule governs *new* terrain; FieldAtlas is not a terrain handoff. |
| **Inputs** | `recipes/houdini_foundry/field_atlas_sea_above_test_tile.v1.json`; tile plan from `houdini_foundry.py plan`; a height/geometry export of the tile region. |
| **Outputs** | Tile EXRs + manifest (Gate 3 format); UE textures under `/Game/Melodia/HoudiniFoundry/FieldAtlas/`; one consumer reading them. |
| **Evidence** | `Saved/Audit/houdini_foundry/field_atlas_sea_above_test_tile/` |
| **Status** | STAGED. |

## Scale reality check (read before planning tiles)

"8 km" in the repo is **Faraway Mother** (`LV_FarawayMother_Prototype`, 8 × 8 km), not Sea Above. What is measured for Sea Above:

- NavMeshBoundsVolume centre (−450, 100, 7000) cm, half-extent (3000, 4000, 8000) cm → route region **60 × 80 m** (`Docs/Evidence/SEA_ABOVE_LEVEL_ORGANIZATION_2026-09-01.json`).
- 11 bounded PCG volumes, the largest 83 × 15 × 17 m (`CURRENT_STATE.md`, 2026-09-12).
- The landscape extent is **not recorded anywhere tracked.** Gate 4 step 1 measures it.

The staged recipe uses the nav bounds with `tile_size_cm` 12800 (the finest level of the World Compiler hierarchy 51200 / 25600 / 12800) and a 1280 cm gutter. `only_tiles` restricts the plan to **one** tile, `tx-001_ty+000`. If the measured landscape is much larger, update `region.bounds_cm` + `bounds_source` in the recipe and commit that before Gate 5. **Tile ids and seeds never change** for a tile that keeps the same grid coordinates.

## Deterministic tiling contract (implemented in `Tools/Houdini/foundry/houdini_foundry.py plan`)

| Item | Rule |
|---|---|
| Grid | `ix = floor(x / tile_size)`, `iy = floor(y / tile_size)`, level space, origin (0, 0) |
| Tile id | `tx{ix:+04d}_ty{iy:+04d}` (e.g. `tx-001_ty+000`) |
| Seed | `stable_int(recipe.seed, "houdini_foundry", recipe_id, "tile", ix, iy) % 2^31` |
| Core / bake bounds | core = the grid cell; bake = core ± `gutter_cm` |
| Output path | `Saved/HoudiniFoundry/<recipe_id>_<seed>/tiles/<tile_id>/` |
| Manifest | one `bake_manifest.json` per tile (`tile_id` set) + one index manifest listing all tiles |
| Hash | sha256 per output file; the recipe hash is `universe_foundry.content_hash(recipe)` |

## Gate 4 — one tile → UE (interactive)

1. **Measure (read-only, UE):** Landscape actor bounds and the landscape's world-to-height scale. Write `sea_above_bounds_2026-09-24.json` into evidence. Do not modify anything.
2. **Export tile geometry (read-only):** export the tile's bake-bounds region of the landscape as a heightfield or mesh (UE export or Houdini Engine *input* node reading the landscape; either is fine because both are read-only). Record the method.
3. **Cook** `HDA_Foundry_FieldAtlas` with the tile's `Seed`/bounds from `plan` (ErosionIterations 0 first). Then `verify`.
4. **Validate** channels: value ranges within the vocabulary, no NaNs, preview reviewed by Brennan.
5. **Import** EXRs into `/Game/Melodia/HoudiniFoundry/FieldAtlas/` (linear, no sRGB, compression HDR or BC6H). Record import settings.
6. **Consume with one existing reader, read-only.** The cheapest honest consumer is a debug material instance on a plane/decal over the tile, sampling one channel in world XY (bounds from the manifest). Or sample the texture as a point attribute in **one existing** Sea Above PCG graph via a Texture Sampler, **only** if that graph's owner agrees. **No new PCG graph, no graph rewrite, no MPC.**
7. **Save → reload → re-check** that the texture and consumer are still bound. Fill the manifest's `ue` block.

## Gate 5 — tiled expensive bake (heavy lane)

Only after Gate 4 is green:

1. Remove `only_tiles` (or list the chosen tiles) and set the real bounds. Validate, then run `plan --out Saved/Audit/houdini_foundry/field_atlas_sea_above_test_tile/plan.json`.
2. Raise `ErosionIterations` to the Brennan-approved look from Gate 4.
3. Launch (heavy lane) either as a hython loop over the plan's tiles or as `TOP_Foundry_BakeFarm` if Gate 10 is ready. Log per tile.
4. After completion, run a seam check across adjacent tiles (Gate 3 rule) and `verify` on every tile manifest.
5. Do not import every tile into UE today. Import the tiles that the route crosses.

Candidate channels for this recipe: flow, sediment, debris, slope, curvature, cliff, exposure, wetness, shore_influence, biome eligibility (`biome_id`). Keep the tile test to the recipe's list; add channels in a new recipe version rather than editing a baked one.

## Done when

Gate 4: one tile's texture is read by one existing consumer, and the result survives save/reload, with evidence. Gate 5: every planned tile has a verifying manifest and the seam check passes.
