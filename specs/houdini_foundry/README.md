# specs/houdini_foundry — Houdini Foundry data contracts

| | |
|---|---|
| **Purpose** | Schemas for deterministic Houdini bakes: recipe, bake manifest, BakeFarm request, and the proposed FieldAtlas channel vocabulary. |
| **Authority** | Additive to World Compiler v1. Nothing here edits `specs/schemas/world_recipe.v1*` or `world_compiler_point_row.v1`; a channel reaches World Compiler only through a new additive schema version. `CURRENT_STATE.md` stays the only status authority. |
| **Inputs / outputs** | Consumed by `Tools/Houdini/foundry/houdini_foundry.py`; recipes live in `recipes/houdini_foundry/`. |
| **Status** | STAGED 2026-09-24 — schemas + offline tests; no bake has produced a manifest against them yet. |
| **At college** | Each baking tool writes `melodia.houdini_foundry_bake_manifest.v1`; the UE gate fills its `ue` block. |

| File | Role |
|---|---|
| `houdini_foundry_recipe.v1.schema.json` | one bake: product, seed, source, params, region/tiles, outputs, UE target, authority |
| `houdini_foundry_bake_manifest.v1.schema.json` | what a cook actually wrote (hashes, Houdini version, UE bake/save/reload) |
| `houdini_foundry_bake_request.v1.schema.json` | minimal TOP_Foundry_BakeFarm input, optionally bound to one Universe Foundry mission task |
| `field_atlas_channels.v1.json` | channel vocabulary; `existing` rows reuse current names (`Resonance`, `hero_weight`, `sparkle_response`, `WorldField.*`) |
