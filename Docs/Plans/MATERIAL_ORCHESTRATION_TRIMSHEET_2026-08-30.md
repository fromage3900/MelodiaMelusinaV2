# Material Orchestration — Trimsheet / Tilable / Unique + Vehicles / Oceanology / FarawayMother

> **Date:** 2026-08-30  
> **Type:** READ-REVIEW orchestrator pass (no .uasset writes)  
> **Queue:** `Saved/Audit/overnight_queue_2026-08-30.json` (11 → 15, added 4)  
> **Companion specs:** `material_catalog_2026-08-30.json`, `material_library_audit.json`, `mi_proposal_2026-08-30.json`, `Content/Python/materialize_glitter_polished.py` (15 polished MIs)  
> **Editor:** assumed down at write time — all new tasks are spec-only until live (`dry_run` / JSON audit pattern like glitter)

---

## 1. Ground truth scanned this pass

### 1.1 KitBash_EnchantedVehicles — 172 meshes, 624 files on disk

| Fact | Value |
|---|---|
| Location | `Content/KitBash_EnchantedVehicles/` (flat, no subdirs) |
| Total `.uasset` | 624 |
| `SM_` meshes | **172** (5 hero + 167 parts) — Apothecary 62, Cobbler 46, Courrier 28, Royal 18, BandWagon 13 + `SM_KB3D_ECV` 5 aggregate heroes |
| Unique PBR stems | **82** (`KB3D_ECV_*` stripped of `_basecolor` etc) — see §1.1.1 |
| Maps per stem | 4–8 (most 5: BC/Height/Metallic/Normal/Roughness; atlases 6–7 with Opacity/Emissive; Glass 6–7 with refraction pair) |
| Material sources | `M_KB3D_ECV` 72 (+ instance) — KB3D import mats to be replaced |

#### 1.1.1 82 stems by category

- **Wood (14):** WoodOldWornBrightA/BrownA/BrownB/BrownBDamaged/GrayA, WoodBarkMoss/PineWorn, WoodHeartwoodAtlas, WoodChipped, WoodOrangePolished, WoodPBeige/Blue/Green/RedWorn, WoodPaintTrim/PaintedGoldMetallic, WoodPlankA, WoodWhiteCarriage
- **Fabric (10):** FabricB/OldBright/PatternA/PatternBlue/PatternRed/TentPink/TentRed/VelvetBlueA/VelvetPurpleA/VelvetWhite/WhiteWorn
- **Metal (6):** MetalCleaner/ForgedBlackRustedA/ForgedGrayA/ForgedGrayB/PBlueWorn/PWhite, Copper, GoldCleanA/CleanDark/DirtyA/TrimB
- **Stone/Brick/Plaster (7):** BrickStoneGray/WarmBTop, CobblestoneFloorB, SandStoneWorn, SlateDB, StoneGray/GrayLight, PlasterYellow, SoilGroundD
- **Atlases (8):** AtlasFlowersA/FoodA/FruitsB/GraphicsA/GraphicsB/LeafA/LeafB/LeafC (+ EmissiveTrim 6)
- **Trim/Detail (9):** RopesTrimA, TrimLeatherWorn, ClayPotsTrimA, BoxwoodBranch, CandleWax, Ivy, LetterPaperA, LeatherWornA/TA, FirewoodA, GlassClean/Dirty, PlasticCable, WallWeaveB

> Note: task prompt said "172" — that is the **mesh** count; total files 624 includes textures. 72 `M_KB3D_ECV` are import materials to be replaced via `M_Master_Toon_Universal`.

### 1.2 Textures/FarawayMother_Suites — 6 suites, 47 PNGs (not 47 suites)

| Suite | Maps | Count | Type |
|---|---|---|---|
| `T_FarawayMother_Corset_GildedAcanthusBrocade` | AO/BC/H/M/N/ORM/R | 7 | Unique — brocade corset |
| `T_FarawayMother_Cradle_CarvedAlabasterWood` | AO/BC/H/M/N/ORM/R | 7 | Unique — carved wood cradle |
| `T_FarawayMother_Gown_CelestialSilkJacquard` | AO/BC/H/M/N/ORM/R/**Sheen** | 8 | Unique — silk jacquard gown |
| `T_FarawayMother_Mantle_NightSkyVelvet` | AO/BC/H/M/N/ORM/R/**Sheen** | 8 | Unique — velvet mantle |
| `T_FarawayMother_Ornament_NacreMusicBoxJewel` | AO/BC/H/M/N/ORM/R/**Sheen** | 8 | Unique — nacre jewel |
| `T_FarawayMother_Veil_AquaticLullabyLace` | AO/**Alpha**/BC/H/M/**Mask**/N/ORM/R | 9 | Unique — lace veil (translucent) |

Flat folder, no suite subdirs. Each PNG has a `.uasset` twin already (94 total files = 47×2). ORM may be packed or separate R/M; Sheen is velvet/silk highlight; Alpha/Mask is lace cutout.

> Previous `material_catalog_2026-08-30.json` lists `T_FarawayMother: 6` (correct — family count), confirming 6 suites.

### 1.3 EnvSandbox/Textures/PBR_Sets/Water — 4 stems, 30 uassets

| Stem | Maps | Count |
|---|---|---|
| `T_WaterBase` | AO/BC/Height/Metallic/Normal/Opacity/Roughness/Specular | 8 |
| `T_WaterHighlight` | AO/BC/Metallic/Normal/Opacity/Roughness/Specular | 7 |
| `T_WaterLayer2` | AO/BC/Metallic/Normal/Opacity/Roughness/Specular | 7 |
| `T_WaterLayerMid` | AO/BC/Height/Metallic/Normal/Opacity/Roughness/Specular | 8 |

Plus sibling sets: `GildedPea` / `PrettyRock` / `SadRock` / `Sand` each 5 maps (BC/Height/Metallic/Normal/Roughness) — tilable substances.

### 1.4 EnvSandbox/Materials/Instances — 614 MI files, sharded history

Current top-level folders (find maxdepth 4):

```
Instances/
  Atlantis/ (18 — BrickStone* etc, already tilable)
  BlingVol3/
  Character/, Melusina/, NikkiHero/, NikkiIntegrated/
  Environment/{Baroque,Cathedral,Cinematic,Escher,FlatColors,House,ImportedPacks,Magical,
               PatternsExtra,RetroTextures,Stylized,Triplanar,World,Zen} (Zen holds 7 ZenTrim)
  Foliage/ (5 orphan Niagara cards)
  Grotto/ (MI_Grotto_UnderwaterPP — orphan)
  Landscape/, Terrain/
  MelusinaReal/ (M_Master_Toon_Landscape_HeightBlend + Universal)
  Oceanology/ (1: MI_Oceanology_Melodia_Hero — orphan, needs reparent)
  Rhythm/ (4 orphan pulse MIs), Showcase/ (4 voids), Sakura/, SDFArchitecture/
  Water/{v7,v9,v10{v10/Integrated,/Preview}} (Water master v6/v7/v9/v10 sharded)
  Showcase2026_06_27/{Landscape,Universal,Water}
  Kenney/RetroFantasyKit/ (10 non-MI-prefix legacy)
  _Scratch/
```

Orphans (21, from `mi_proposal_2026-08-30.json`): Foliage 5, Grotto 1, Melusina 1, Oceanology 1, Rhythm 5, Showcase 5, Water 1, Magical 2. Plus 4 potentially broken SDF parents.

### 1.5 Glitter polished spec (today)

`Content/Python/materialize_glitter_polished.py` — 15 MIs plan: Enhanced(5 BrickStone tilables R0.65–0.78, UVScale 4/6/8), Ultimate(5 sparkle R0.28–0.45, SparkleIntensity 2.8–5.0, soft blue/pink), WorldAligned(5 triplanar R0.78–0.92, Tiling 2–8). Masters: Enhanced/Ultimate/World/Ink. Dest `/Game/EnvSandbox/Materials/Instances/Glitter/Polished`, Tex `/Game/EnvSandbox/Textures/Atlantis`. Roughness spread + tile are the naming pattern to propagate: `MI_<Stem>_Rxx_TileY`.

### 1.6 EnvSandbox/Textures top-level inventory

1210 uassets total: Atlantis 424, PackTextures 375, Melusina 101, BlingVol3 90, Melodia 43, PBR_Sets 50, Trimsheet 6, CrystalCrossroads 7, Defaults 7, etc. Catalog says 12 complete sets (ZenTrim 7 + FloralBrick + basetrim/concretetrim + landscape_grass/grayscale), 93 incomplete stems, 0 with instance.

---

## 2. Proposed organized hierarchy

### 2.1 Principle

Sort by **how it tiles**, not where it was imported from. Three buckets, then domain folders inside each.

```
Content/EnvSandbox/Materials/Instances/
  Tilable/            — seamless tiling PBR (UVScale/TileY meaningful, Rxx spread)
    Atlantis/         — BrickStone* etc (migrated from Atlantis/)
    Zen/              — ZenTrim_* (from Environment/Zen/)
    PBR_Sets/         — GildedPea, PrettyRock, SadRock, Sand
    Generic/          — concretetrim/basetrim, landscape_grass, SoIL, etc.
    PackTextures/     — PackTextures subsets that are tilable (subset migration)

  Trimsheet/          — UV atlas / trim strip (TileY = trim index or atlas page)
    Trimsheet/        — EnvSandbox/Textures/Trimsheet 6 + interiorwalltrim
    ZenTrims/         — ZenTrim_*Trim* members
    PackTrims/        — PackTextures trims
    EnchantedAtlas/   — AtlasFlowers/Food/Fruits/Graphics/Leaf from ECV (atlas link)

  Unique/             — hero / one-off (TileY always 1, no tiling)
    FarawayMother/    — P2 suites (6, see §1.2) + P1 if exists
    Props/            — FloralBrickGrayScale, CrystalCrossroads, one-off hero props
    Character/        — (keep Character/, Melusina/ but label as Unique/Character/)

  Vehicles/
    Enchanted/        — all ECV tilable+trim+unique for 5 vehicles (grouped subfolder per vehicle)
      Apothecary/ Cobbler/ Courrier/ Royal/ BandWagon/
      Shared/         — wood/metal/stone shared across vehicles
      Atlas/          — Atlas* shared

  Oceanology/         — water-as-material domain (distinct from generic Water history)
    WaterBase/ WaterHighlight/ WaterLayer2/ WaterLayerMid/
    Shoreline/        — T_SeaAbove_Sand etc when water-adjacent (cross-ref SeaAbove/)

  FarawayMother/
    P1/               — (reserved if P1 batch exists; else empty)
    P2/               — 6 suites below (Uniquetiling, Tile1)

  Water/              — keep versioned history v7/v9/v10 but consolidate active into Water/Active/
  Glitter/
    Polished/         — already correct (15 from glitter_polished)

  SeaAbove/           — from mi_proposal batch (Reef 40 stems — keep as SeaAbove/)
  _Archive/           — Kenney 10 non-MI, BlingVol3 rhinestone, orphan shims (staged delete)
```

Keep `Environment/`, `SDFArchitecture/` etc as aliases or migrate incrementally — the new top-level Tilable/Trimsheet/Unique + Vehicles + Oceanology + FarawayMother are the **canonical** labels; old paths become redirectors.

### 2.2 Decision matrix (tilable vs trimsheet vs unique)

| Signal | Tilable | Trimsheet | Unique |
|---|---|---|---|
| Name contains `Trim`/`Atlas`/`Rope`/`LeatherTrim` | — | **yes** | — |
| Maps include opacity+emissive with atlas layout | — | **yes** | — |
| hero costume/prop (FarawayMother, CrystalCrossroads) | — | — | **yes** |
| Substance-style 5-map (BC/Height/Metallic/Normal/Roughness) uniform | **yes** | — | — |
| ZenTrim_Flowers etc repeated motif | **yes** | — | — |
| TileY makes sense >1 | **yes** | yes (as trim index) | **no** (always 1) |

### 2.3 Master assignment

| Bucket | Primary master | When to use Alpha / Nikki / SDF / Water |
|---|---|---|
| Tilable opaque | `M_Master_Toon_Universal` | Landscape HeightBlend only for landscape terrain; SDF for parallax bone variants |
| Trimsheet | `M_Master_Toon_Universal` | Alpha if any opacity channel (ECV atlases have it) |
| Unique | `M_Master_Toon_Universal` | Nikki for velvet/silk sheen (Faraway Gown/Mantle), Alpha for Veil lace, SDF if hero needs parallax |
| Vehicles | `M_Master_Toon_Universal` + `Alpha` | Metal/wood opaque on Universal; Glass + 6 Fabric+Opacity on Alpha; EmissiveTrim on Universal with emissive |
| Oceanology/Water | `M_Water_Master_Grand_v10_Upgrade` | Universal fallback for shoreline cut; Substrate variant if Nanite |
| FarawayMother P2 | `M_Master_Toon_Universal` / `M_Master_Nikki` | Nikki for Sheen (Gown/Mantle/Ornament), Alpha for Veil; ORM split + AO |
| Glitter | `M_Glitter_*` (already) | — |

All new MIs enable ShadowDream soft blue #8AA0D6 / pink #E8A0BF (from glitter spec) except water where `bCelestialUsesDreamPalette` carries it.

---

## 3. Migration map (from → to)

| From (current) | To (proposed) | Items | Action |
|---|---|---|---|
| `Instances/Atlantis/MI_BrickStone* (18)` | `Instances/Tilable/Atlantis/MI_Tilable_*` | 18 | move + rename to `MI_Tilable_<Stem>_Rxx_TileY` |
| `Instances/Environment/Zen/MI_Zen*` | `Instances/Tilable/Zen/` + `Instances/Trimsheet/ZenTrims/` | ~7 ZenTrim | split by `*Trim*` |
| `EnvSandbox/Textures/PBR_Sets/{GildedPea,PrettyRock,SadRock,Sand}` (no MI yet) | `Instances/Tilable/PBR_Sets/` | 4 stems (20 files) | **new** (tilable_trimsheet_split task) |
| `EnvSandbox/Textures/Trimsheet/` (6) | `Instances/Trimsheet/Trimsheet/` | 6 | **new** |
| `Content/KitBash_EnchantedVehicles/KB3D_ECV_*` (82 stems) | `Instances/Vehicles/Enchanted/{Apothecary,Cobbler,Courrier,Royal,BandWagon,Shared,Atlas}/` | 72 PBR stems + 10 shared | **new** (enchanted_vehicles_mat task) |
| `EnvSandbox/Textures/PBR_Sets/Water` (4 stems, 30 files) | `Instances/Oceanology/WaterBase|Highlight|Layer2|LayerMid/` + `Instances/Water/Active/` | 4 stems | **new** (oceanology_water_mat task) |
| `Instances/Oceanology/MI_Oceanology_Melodia_Hero` (orphan) | `Instances/Oceanology/Hero/MI_Oceanology_*` | 1 | reparent to `M_Master_Toon_Universal` or Water master |
| `Instances/Water/v7|v9|v10` (25 water MIs) | `Instances/Water/Active/` + `Instances/Water/_Archive/v7|v9|v10` | 25 | consolidate active 4, archive versioned |
| `Content/Textures/FarawayMother_Suites` (6 suites, 47 PNGs) | `Instances/FarawayMother/P2/{Corset,Cradle,Gown,Mantle,Ornament,Veil}/` | 6 suites | **new** (faraway_p2_unique task) |
| `EnvSandbox/Textures/BlingVol3` (rhinestone 15) | `Instances/Tilable/BlingVol3/` or `_Archive` | 15 | defer — low priority |
| `Instances/Kenney/RetroFantasyKit` (10 non-MI) | `Instances/_Archive/Kenney/` | 10 | staged delete (kenney_purge_verify queue) |
| `Instances/SeaAbove/` (mi_proposal 11 candidates, 40 stems) | `Instances/SeaAbove/` (keep) + `Instances/Oceanology/Shoreline/` cross-ref | 40 | existing reef_mis task |
| `Instances/Glitter/Polished` (via glitter_polished 15) | `Instances/Glitter/Polished/` | 15 | already routed |

Total net new MIs proposed this plan: ECV ~82 + Water 4 + Faraway P2 6 + Tilable/Trimsheet ~15–20 = **~107–112** new MI specs (all `MI_<Category>_<Stem>_Rxx_TileY`).

---

## 4. Tilable / Trimsheet / Unique split table (remaining gap)

| Stem family | Source | Maps | Bucket | Proposed MI example | Priority |
|---|---|---|---|---|---|
| `ZenTrim_CrackedToHell` | Textures_Shared | 7 (Alpha/BC/Disp/Emiss/Met/N/R) | **Tilable** | `MI_Tilable_ZenTrimCrackedToHell_R072_Tile4` | P1 |
| `ZenTrim_Base4K`, `ColourShift`, `Flowers*`×3, `Wet` | Textures_Shared | 7 each | **Tilable** | `MI_Tilable_ZenTrimFlowersLots_R065_Tile6` | P2 |
| `T_GildedPea` | PBR_Sets/GildedPea | 5 | **Tilable** | `MI_Tilable_GildedPea_R028_Tile4` (gold R0.28) | P1 |
| `T_PrettyRock` | PBR_Sets/PrettyRock | 5 | **Tilable** | `MI_Tilable_PrettyRock_R082_Tile4` | P1 |
| `T_SadRock` | PBR_Sets/SadRock | 5 | **Tilable** | `MI_Tilable_SadRock_R085_Tile4` | P1 |
| `T_Sand` | PBR_Sets/Sand | 5 | **Tilable** | `MI_Tilable_Sand_R088_Tile6` | P1 |
| `concretetrim` / `basetrim` | Textures/Textures | ~5 | **Tilable** | `MI_Tilable_ConcreteTrim_R078_Tile4` | P2 |
| `landscape_grass`, `landscapegrayscale` | Textures | ~5 | **Tilable** | `MI_Tilable_LandscapeGrass_R092_Tile8` | P2 |
| `T_FloralBrickGrayScale` | Textures | 6 | **Unique** | `MI_Unique_FloralBrickGrayScale_R075_Tile1` | P3 |
| `Trimsheet` 6 | Trimsheet/ | ~3–5 | **Trimsheet** | `MI_Trimsheet_InteriorWallTrim_R068_Tile2` | P1 |
| `T_ClothTrim*` (cached-only, verify) | — | 0 on disk | skip | — | — |
| `PackTextures` tilable subset | PackTextures/ 375 | mixed | **Tilable** (audited subset) | `MI_Tilable_Pack_*` | P3 |
| `PackTextures` trim subset | PackTextures/ | mixed | **Trimsheet** | `MI_Trimsheet_Pack_*` | P3 |

Detailed per-stem audit to be written by `tilable_trimsheet_split` task to `Saved/Audit/tilable_trimsheet_split_2026-08-30.json`.

---

## 5. Instance naming `MI_<Category>_<Stem>_Rxx_TileY` — convention

```
MI_<Category>_<Stem>_R<RR>_Tile<Y>[_Variant]
       │        │      │      │      └─ Optional: Unique | Translucent | Sheen | Depth | Shimmer | Height | Trim | Atlas
       │        │      │      └─ TileY = UVScale / tiling index: 1=Unique, 2=trim/small, 4=standard, 6=large atlas, 8=macro
       │        │      └─ Rxx = roughness×100 zero-padded: R028 (0.28 gold), R078 (0.78 brick), R092 (0.92 velvet)
       │        └─ Stem = PascalCase stripped of T_/KB3D_ECV_/FarawayMother_/Water prefixes
       └─ Category = Tilable | Trimsheet | Unique | EnchantedVehicle | Oceanology | Water | FarawayMother
```

Examples (normative):

- `MI_EnchantedVehicle_WoodOldWornBrownA_R078_Tile4`
- `MI_EnchantedVehicle_GlassClean_R012_Tile2_Translucent`
- `MI_EnchantedVehicle_AtlasFlowersA_R045_Tile6`
- `MI_Oceanology_WaterBase_R035_Tile4_Depth`
- `MI_Water_WaterHighlight_R018_Tile6_Shimmer`
- `MI_FarawayMother_Corset_GildedAcanthusBrocade_R045_Tile1_Unique`
- `MI_FarawayMother_Veil_AquaticLullabyLace_R088_Tile1_Translucent`
- `MI_Tilable_ZenTrimCrackedToHell_R072_Tile4`
- `MI_Trimsheet_InteriorWallTrim_R068_Tile2`
- `MI_Unique_FloralBrickGrayScale_R075_Tile1`
- Glitter already uses `MI_Glitter_*_Rxx` — keep as `MI_Glitter_*` (exempt)

Roughness spread (from glitter_polished + water + faraway):

- Wood 0.72–0.88, Metal 0.25–0.45, Fabric 0.85–0.95, Glass 0.05–0.12, Stone 0.78–0.85, Gold 0.28, Marble 0.32, Velvet 0.92, Silk 0.32, Jewel 0.18, Water 0.18–0.35, Brocade 0.45, Lace 0.88

---

## 6. New queued tasks (4) — appended to overnight_queue

| # | id | lane | pri | Summary | Dest | Naming | Log |
|---|---|---|---|---|---|---|---|
| 1 | `enchanted_vehicles_mat` | code | 2 | 172 SM + 82 PBR stems from KitBash_EnchantedVehicles | `Instances/Vehicles/Enchanted/` (Apothecary/Cobbler/Courrier/Royal/BandWagon/Shared/Atlas) | `MI_EnchantedVehicle_<Stem>_Rxx_TileY` | `Saved/Audit/enchanted_vehicles_2026-08-30.json` |
| 2 | `oceanology_water_mat` | code | 2 | 4 Water PBR stems (30 uassets) + Oceanology reparent + Water v7/v9/v10 consolidation | `Instances/Oceanology/` + `Instances/Water/Active/` | `MI_Oceanology_<Stem>_Rxx_TileY` / `MI_Water_<Stem>_Rxx_TileY` | `Saved/Audit/oceanology_water_2026-08-30.json` |
| 3 | `faraway_p2_unique` | code | 3 | 6 suites / 47 PNGs FarawayMother P2, Unique bucket, Nikki sheen + Alpha veil | `Instances/FarawayMother/P2/` | `MI_FarawayMother_<Piece>_<Material>_Rxx_Tile1_Unique` | `Saved/Audit/faraway_p2_2026-08-30.json` |
| 4 | `tilable_trimsheet_split` | docs | 3 | Remaining gap: 1210 EnvSandbox/Textures + catalog 12 complete sets split Tilable/Trimsheet/Unique + migration map | `Instances/Tilable/` `Trimsheet/` `Unique/` | `MI_Tilable_*`, `MI_Trimsheet_*`, `MI_Unique_*` | `Saved/Audit/tilable_trimsheet_split_2026-08-30.json` |

Full prompts are in `Saved/Audit/overnight_queue_2026-08-30.json` entries 12–15. Queue went **11 → 15**, still contains `read_review_loop` recurring (pri 99) to keep refilling when <3 items.

Each task follows the glitter pattern: `ensure_mi` + `apply_params` against `M_Master_Toon_Universal` (and Alpha/Nikki/Water), ShadowDream soft blue `#8AA0D6` / pink `#E8A0BF`, spec JSON first, `.uasset` only when editor live — **no .uasset writes this pass**.

---

## 7. Risks / verification needed live

- Monolith HTTP was `000` at prior `melodia-lookdev-audit` pass — all 21 orphans / 4 broken SDF parents need `get_cdo_properties` verification live.
- `M_Master_Toon_Universal_Alpha` existence: `mi_proposal` lists it as 12 parents — confirm before ECV Glass/Fabric routing.
- `T_FarawayMother` ORM vs separate R/M — disk shows both `ORM.png` and `R.png`+`M.png` per suite; verify packing.
- Faraway suite import state: PNG + .uasset twins exist — confirm they are imported as `Texture2D` with correct compression (BC7 for BC, BC5 for Normal).
- Vehicle mesh material slots: 72 `M_KB3D_ECV` need static_materials scan to map which mesh uses which stem (deferred to enchanted_vehicles_mat task).

---

## 8. Next orchestrator actions

- When queue drains below 3, `read_review_loop` refills with next micro-tasks: per-vehicle MI batches (Apothecary first), Water Active consolidation, Faraway P2 veil translucency tuning.
- Archive `Kenney` after `kenney_purge_verify` confirms no referencers.
- Reconcile `614` vs `mi_proposal 629` MI count drift (new Glitter 15 may explain).

