# Material Instance Review — project-wide (2026-09-03)

**Scope:** all MaterialInstanceConstant assets, 4,499 total, audited live via
asset registry (editor on :9316). Goal: identify the triple-A tier to build Sea
Above / cathedral dressing with, and mark what must not be touched.

## Tier ladder (how to pick a material)

| Tier | Families | Verdict |
|---|---|---|
| **AAA — use for hero dressing** | `M_Water_Oceanology_Melodia` oceans, `M_Water_Master_Grand_v10_Upgrade` (Grand water), `M_Master_Toon_Universal(_Alpha)` (Nikki-style SDF toon), `M_Master_Toon_Landscape_HeightBlend`, `M_Niagara_MelodiaFlipbook` | Real masters, verified parents |
| **AAA — library assets** | Megascans 3D_Assets (123), 3D_Plants (74), Surfaces, Decals — `MI_HugeNordicCoastalCliff`, `MI_GiganticSandstoneTerrain`, `MI_ForestRockFormation_*` | Quixel scanned, photoreal. Use for terrain/island dressing, NOT for the toon cathedral (style clash) |
| **High — post/PPV** | ArtOfShader (56 MIs: ACESTonemapping, FilmGrain, NightVision, RainGlass…) | Screen-space post only |
| **Project hero surface** | `_PROJECT/04_Materials` (178 MIs: `MI_Baroque_GildedRose`, `MI_Architecture_GothicCathedral`, `MI_CathedralFloor_Textured`, `MI_Cosmo_Master_*` GildingMax/TriplanarMax/AudioDriven) | The cathedral-grade authored tier. Verify each parent before use (2 of 3 probes returned no parent — some may be dead refs) |
| **Engine/plugin utility** | VREditor, EditorShell, CAD/Wire, UDS sky MIs (62+58), TurnBasedJRPG (18), Mannequins | Runtime/system, not dressing |
| **JUNK — do not use** | `Material_001`, `MI_Master_Simple_Universal_Inst`, quarantine copies (M_Master_Toon_Landscape_HeightBlend_*QUARANTINE*/*BACKUP*/*_OLD*), `00_Archive/*`, `gltf/MaterialInstances`, starter `Box_*`/`Material_*` | Placeholders, restores, or dead duplicates |

## Sea Above family — VERIFIED live parents (the level's own materials)

| MI | Parent master | Use |
|---|---|---|
| MI_SeaAbove_SurfaceOcean / _Clean | M_Water_Master_Grand_v10_Upgrade | main sea surface |
| MI_SeaAbove_SurfaceOcean_Oceanology | **M_Water_Oceanology_Melodia** | premium ocean variant |
| MI_SeaAbove_FalseOcean / _Clean / _Oceanology | Grand / Oceanology | distant/fake ocean |
| MI_SeaAbove_UpwardDroplet | M_Niagara_MelodiaFlipbook | droplet/foam flipbook |
| MI_SeaAbove_Water_ZenForest_Baseline | MI_GrandWater_ShorelinePond | zen pond reference |
| MI_SeaAbove_CoralSkin / _2S / Kelp / WetRock / Sand / Organ_Pipe / Leviathan_Bone | M_Master_Toon_Universal | reef + bones (toon-form language) |
| MI_SeaAbove_Cloth_Banner / Shroud, MI_Jelly_Bell / Arms | M_Master_Toon_Universal_Alpha | translucent banners/jelly |
| MI_SeaAbove_CanonicalLandscape_Substrate / LiquidCathedral_Substrate | M_Master_Toon_Landscape_HeightBlend | terrain substrate |

## Build rules (from this review)

1. **Reef/jelly/kelp/rocks: M_Master_Toon_Universal family only** — it keeps the
   Nikki-form language. Do NOT put Megascans photoreal onto toon-form assets.
2. **Water: Oceanology variants are king** (`M_Water_Oceanology_Melodia`) — surfaces
   already have `_Oceanology` twins; prefer those for hero water.
3. **Cathedral dressing: `_PROJECT/04_Materials` is the authored cathedral tier**
   (`MI_Baroque_GildedRose`, `MI_Architecture_GothicCathedral`,
   `MI_CathedralFloor_Textured`, `MI_Cosmo_Master_GildingMax`) — but VERIFY the
   parent of each before wiring; 2/3 probed had no readable parent (dead-ref risk).
4. **Never touch:** quarantines/backups, `Material_001`, gltf imports, archive
   folders. These are restores or placeholders.
5. **Megascans terrain is the island/coast tier** — use `MI_HugeNordicCoastalCliff_01`,
   `MI_GiganticSandstoneTerrain_01`, `MI_ForestRockFormation_*` for the drowned
   archipelago's rock walls where water meets stone (photoreal is correct there).

## Next step (one at a time, per agreement)
- Verify parents of the 178 `_PROJECT/04_Materials` MIs (cathedral tier) — bucket
  LIVE vs dead-ref so we know what we can actually dress with.
- Then wire the golden beat volumes with only AAA parents.

## Evidence
- Live registry census 2026-09-03: 4,499 MIs, 15 EnvSandbox masters,
  31 SeaAbove MIs in Monolith folder + 42 total under SeaAbove paths.
- Parent chain read via `get_editor_property('parent')` on each named MI.