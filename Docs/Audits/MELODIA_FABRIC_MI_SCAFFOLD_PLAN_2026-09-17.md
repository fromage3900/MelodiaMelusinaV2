# Melodia fabric MI scaffold plan ΓÇö 2026-09-17

**Package:** A ΓÇö Materials org (plan only; no mass MI create in this stamp)  
**Stamp:** 2026-09-17 ~18:25 EDT (America/Toronto)  
**Parent master:** `/Game/Melodia/Materials/Masters/M_SurrealFabric_Flipbook`  
**Template MI:** `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_CelestialSilk`  
**Destination (proposed):** `/Game/Melodia/Materials/Lookdev/` or `/Game/Melodia/Materials/Instances/SurrealFabric/` (owner pick folder; keep Melodia naming)

## Already instanced (lookdev ├ù3)

| MI | Soft path | Status |
|----|-----------|--------|
| CelestialSilk | `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_CelestialSilk` | Template ΓÇö **Ctrl+S owed** |
| CymaticPulse | `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_CymaticPulse` | **Ctrl+S owed** |
| BrassPatina | `/Game/Melodia/Materials/Lookdev/MI_SurrealFabric_BrassPatina` | **Ctrl+S owed** |

## Remaining Melodia* fabric folders (no MI hint yet)

From MATERIALS_CLEAN_LOOP fold-in 1745 (12 Copernicus Melodia* tex folders):

| # | Folder / family hint | Proposed MI name |
|---|----------------------|------------------|
| 1 | AmethystVein | `MI_SurrealFabric_AmethystVein` |
| 2 | AuroraGlass | `MI_SurrealFabric_AuroraGlass` |
| 3 | ForestEmerald | `MI_SurrealFabric_ForestEmerald` |
| 4 | GoldSilk | `MI_SurrealFabric_GoldSilk` |
| 5 | Moonlace | `MI_SurrealFabric_Moonlace` |
| 6 | MotherPearl | `MI_SurrealFabric_MotherPearl` |
| 7 | SapphireGlass | `MI_SurrealFabric_SapphireGlass` |
| 8 | MoonlitMoss | `MI_SurrealFabric_MoonlitMoss` |
| 9 | PrismaticObsidian | `MI_SurrealFabric_PrismaticObsidian` |
| 10 | RoyalVelvetBrocade | `MI_SurrealFabric_RoyalVelvetBrocade` |
| 11 | SingingDune | `MI_SurrealFabric_SingingDune` |
| 12 | WeepingWillow | `MI_SurrealFabric_WeepingWillow` |

## Clone recipe (from CelestialSilk)

| Param | Value |
|-------|-------|
| Parent | `M_SurrealFabric_Flipbook` |
| AtlasCols / AtlasRows | **6 / 5** |
| FlipFPS / FrameRate | **12** |
| FrameCount | **30** |
| BaseColor | family `*_Atlas_6x5` or `*_AtlasCompact_6x5` if present |
| Normal / ORM | **still** until atlas exists (see Normal/ORM inventory) |
| Iridescence / Roughness | atlas if present; else still |

### Steps (editor; owner Ctrl+S)

1. Duplicate `MI_SurrealFabric_CelestialSilk` ΓåÆ rename per table.
2. Swap BaseColor (and other HAVE atlases) to that familyΓÇÖs textures.
3. Leave Normal/ORM on still if GAP.
4. Validate; **owner Ctrl+S**. Never agent `save_packages` / `recompile_material`.
5. Do not invent a second flipbook master.

## Batch order (suggested)

1. GoldSilk, RoyalVelvetBrocade, MotherPearl (wardrobe-adjacent)
2. AmethystVein, SapphireGlass, AuroraGlass (jewel/glass reads)
3. ForestEmerald, MoonlitMoss, WeepingWillow (nature)
4. Moonlace, PrismaticObsidian, SingingDune

## Out of scope

- Inventing missing atlases
- Reopening Universal Cymatic bus
- Pushing Content from docs branch

## Related

- `Docs/VFX/Playbooks/PLAYBOOK_SURREALFABRIC_FLIPBOOK_MASTER.md`
- `Docs/Audits/SURREALFABRIC_NORMAL_ORM_INVENTORY_2026-09-17.md`
