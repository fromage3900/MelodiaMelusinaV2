# Receipt - Nikki leftover validate + HeightBlend reparent list - 2026-09-09

**Status:** VALIDATE PASS + parent lists FILLED (exact soft-paths)  
**Owner lane:** Melodia study bot (docs / #158) · **Live fill:** New Bot 2026-09-09  
**Index:** [Docs/Materials/README.md](README.md) · **Labels:** [LABEL_MAP_2026-09-09.md](LABEL_MAP_2026-09-09.md)  
**Authority:** `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` (**SHIP**)  
**Legacy:** `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend` (**LEGACY**)  
**Tool:** Monolith `validate_material` + `material_query list_material_instances` (Asset Registry, saved-to-disk; **NO** save_packages / **NO** recompile)

## A) Fresh validate (FILLED)

| Check | Result |
|-------|--------|
| `validate_material` `/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape` (`fix_issues=false`) | **PASS** — **hard errors: 0**; warnings: **126** (island / unused_parameter); info: 1 |
| `MI_Glacier_Landscape_Layered` parent | **Nikki** |
| Sea Above / Glacier PIE | owner smoke still open |
| Scratch master | SCRATCH — not authority |

## B) Census summary

| Parent | Count |
|--------|-------|
| `M_Master_Nikki_Landscape` | **9** |
| `M_Master_Toon_Landscape_HeightBlend` | **28** |

Prior audit "19/37" is superseded by this live registry dump.

## C) On Nikki (9) — keep

1. `/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered`
2. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CarvedRock`
3. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow`
4. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_NikkiDream`
5. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_PondBank`
6. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SnowAlpine`
7. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_UrbanCobble`
8. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_VolcanicRock`
9. `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_WetlandMud`

## D) Still on HeightBlend (28) — reparent → Nikki or defer

| # | Soft path | Suggested action |
|---|-----------|------------------|
| 1 | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend_Inst` | retire with LEGACY master |
| 2 | `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/CadenceCrystalRidge/MI_Gaea_CadenceCrystalRidge_Substrate` | owner: reparent vs Gaea defer |
| 3 | `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/FugueGrotto/MI_Gaea_FugueGrotto_Substrate` | owner: reparent vs Gaea defer |
| 4 | `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/SakuraTerrace/MI_Gaea_SakuraTerrace_Substrate` | owner: reparent vs Gaea defer |
| 5 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CliffGrass` | **reparent → Nikki** |
| 6 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_CoastalCliff` | **reparent → Nikki** |
| 7 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_DesertArid` | **reparent → Nikki** |
| 8 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_ForestFloor` | **reparent → Nikki** |
| 9 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Grass_Tilable_R090_Tile6` | **reparent → Nikki** |
| 10 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SakuraGarden` | **reparent → Nikki** |
| 11 | `/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_WitchGarden` | **reparent → Nikki** |
| 12 | `/Game/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Landscape_HeightBlend/MI_M_Master_Toon_Landscape_HeightBlend_Grass` | MelusinaReal pass / reparent |
| 13 | `/Game/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Landscape_HeightBlend/MI_M_Master_Toon_Landscape_HeightBlend_LandscapeGrayscale` | MelusinaReal pass / reparent |
| 14 | `/Game/EnvSandbox/Materials/Instances/MelusinaReal/M_Master_Toon_Landscape_HeightBlend/MI_M_Master_Toon_Landscape_HeightBlend_Soil` | MelusinaReal pass / reparent |
| 15 | `/Game/EnvSandbox/Materials/Instances/MI_Master_Toon_Landscape_HeightBlend_Inst` | retire with LEGACY |
| 16 | `/Game/EnvSandbox/Materials/Masters/MI_SakuraLandscape` | reparent → Nikki + move out of Masters/ |
| 17 | `/Game/EnvSandbox/Materials/Instances/Sakura/MI_SakuraLandscape` | **reparent → Nikki** |
| 18 | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Terrain/MI_SeaAbove_CanonicalLandscape_Substrate` | **reparent → Nikki** |
| 19 | `/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Terrain/MI_SeaAbove_LiquidCathedral_Substrate` | **reparent → Nikki** |
| 20 | `/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Landscape/MI_Showcase2_Landscape_Baseline` | **defer showcase** |
| 21 | `/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Landscape/MI_Showcase2_Landscape_MacroVariation` | **defer showcase** |
| 22 | `/Game/EnvSandbox/Materials/Instances/Showcase2026_06_27/Landscape/MI_Showcase2_Landscape_RealNormals` | **defer showcase** |
| 23 | `/Game/EnvSandbox/Materials/Instances/Terrain/MI_Terrain_BaroqueGrotto_Substrate` | owner triage |
| 24 | `/Game/EnvSandbox/Materials/Instances/Terrain/MI_Terrain_CosmicOrrery_Substrate` | owner triage |
| 25 | `/Game/EnvSandbox/Materials/Instances/Terrain/MI_Terrain_SakuraDream_Substrate` | owner triage |
| 26 | `/Game/EnvSandbox/Materials/Instances/Terrain/MI_Terrain_SpaceCathedral_Substrate` | owner triage |
| 27 | `/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_RakedSand` | owner triage |
| 28 | `/Game/EnvSandbox/Materials/_Scratch/Test_Landscape` | **SCRATCH** — ignore |

## E) Still open (owner / later batch)

- [ ] Reparent core + Sea Above rows (5–11, 17–19) then **owner Ctrl+S**
- [ ] PIE Sea Above / Glacier after reparent
- [ ] Quarantine HeightBlend master only after consumers clear

## Hard rules

- Agents: validate / list only — never `save_packages` / `recompile_material`.
- Owner Ctrl+S for intentional saves.
- One concern per PR off **main**.
