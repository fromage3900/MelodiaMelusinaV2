# SeaAbove — Material Wiring Closeout + PCG Dressing Plan (2026-09-04)

Companion to `SEA_ABOVE_LANDSCAPE_EXECUTION_2026-09-04.md` (GPT Sol's execution log).
This document closes the **Gaea material intake** question and plans the **dressing** pass.
It deliberately does not duplicate Sol's material work.

---

## 1. Gaea material intake — CLOSED

`Saved/GaeaStaging/Glacier/contract.json` is the authority:

```json
layers      : ["Base", "Snow", "Water", "Rock"]
weightmaps  : ["W_Glacier_Snow.png", "W_Glacier_Water.png", "W_Glacier_Rock.png"]
scale       : { xy: 495.5401306152344, z: 244.453125 }
```

The four colour maps had been imported long ago; the three **weightmaps never had been**.
That was the entire reason `bUseGaeaMasks` was false and the mask slots held placeholder
gradients — the layer-blend data had never reached UE.

### Final state of each Gaea layer

| Contract layer | Driven by | Where |
|---|---|---|
| **Rock** | `W_Glacier_Rock` → `Gaea_SlopeMask`, weight 1.0 | `MI_Glacier_Landscape_Layered` |
| **Water** | `W_Glacier_Water` → `Gaea_WaterMask`, weight 1.0 | same |
| **Snow** | `T_Glacier_SnowEdge_SDF16` → `SnowEdgeDistanceTexture` (**signed distance field**) | master, by GPT Sol |
| **Base** | landscape base layer | — |
| *(Flow)* | **no source — inert at weight 0** | master default |

**Snow is solved by SDF, not by a weightmap slot.** An earlier note in this session
recommended adding a `Gaea_SnowMask` parameter to the master because the contract exports
a snow weightmap while the master had no matching slot. That recommendation is
**withdrawn**: `SnowEdgeDistanceTexture` + `SnowEdgeDistanceRangeCM` +
`bSnowFrostDistanceBand` give a distance-banded snow edge, which is strictly better than a
binary weight for frost banding. `W_Glacier_Snow` remains imported and unused — harmless,
and available if a hard mask is ever wanted.

**`Gaea_FlowMask` has no data source and must stay at weight 0.** The contract exports no
flow layer. The slot currently points at a *colour* map (`T_Glacier_GroundTexture`) on the
instance, which is meaningless as a mask — but `Gaea_FlowWeight` is 0, so it contributes
nothing. Do not "fix" this by binding an arbitrary texture; the correct state is inert
until Gaea exports a flow map.

### World-space mapping is correct

`GaeaLandscapeMin (-249752, -249752)` and `GaeaLandscapeSize (499504, 499504)` match the
measured Landscape extent exactly, and are consistent with the contract's `xy` scale of
495.54 over a ~1009 px heightmap. Masks land in the right place.

### Repeatability

`Content/Python/import_gaea_glacier_weightmaps.py` re-runs the whole import whenever Gaea
re-exports. It imports as **sRGB off / TC_MASKS** — imported as sRGB the weights are
gamma-curved and every layer boundary lands wrong — clears the git-lfs read-only bit before
saving, and reads every value back after writing.

---

## 2. Landscape survey — the numbers that matter for dressing

| Fact | Value |
|---|---|
| Landscape extent | `(249752, 249752, 62572)` — a real 5 km × 5 km terrain |
| Content actors | 259 StaticMeshActor, 66 PCG hero nodes, 7 jelly cathedrals |
| Budget now | 2,010,602 tris · 670 draw calls · navmesh built |
| Content X range | −140370 … 141935 |
| Content Y range | −85018 … 297296 (extends past the landscape to the north) |

**`get_scene_bounds` is useless on this level** — Ultra Dynamic Sky (9.9e9) and
OceanologyInfiniteOcean (5e7) dominate it. Query the Landscape actor's own bounds.

### Occupancy — the east is empty

3×3 cell counts over the landscape footprint:

```
north      9     8     6
mid       59   122     0     <- east column empty
south     73    55     0
        west  center  east
```

The eastern third holds effectively no content. That is where dressing has room, and it
matches Sol's independently-derived "Eastern navigation coverage repair" item.

---

## 3. The PCG volumes are not laid out

Four `PCGVolume` actors, all concentric at the origin, all far larger than the landscape:

| Volume | Location | Extent | Graph |
|---|---|---|---|
| `PCG_ResonanceCathedral` | (0, 0, −29290) | 800k | `PCG_Hero_ResonanceCathedral` |
| `PCG_Ribbon_GardenBeat_BellTree` | (0, −950, −14000) | 800k | `PCG_Hero_BellTreeGarden` |
| `PCG_Colonnade` | (0, 0, −15670) | 600k | `PCG_BaroqueColonnade` |
| `PCG_Ribbon_XylophoneTrail` | (0, 0, 0) | 300k | `PCG_Hero_XylophoneTrail` |

Landscape extent is 250k. Every graph therefore runs over the **entire** map and beyond,
stacked on the others, at negative Z. There is no spatial differentiation — no zone owns a
style, and no style is bounded by a region.

**This is the single highest-leverage level-design fix on this map**, and it is cheap:
moving and shrinking volumes is non-destructive and re-runs the graphs in place.

---

## 4. Dressing plan

### 4a. Give each hero graph a bounded zone

Re-fit the four volumes to distinct regions inside the ±250k footprint rather than four
concentric 600–800k boxes. Suggested split, derived from the occupancy grid:

| Volume | Zone | Rationale |
|---|---|---|
| `PCG_Ribbon_XylophoneTrail` | centre spine | highest existing density (122) — the de-facto main route |
| `PCG_Ribbon_GardenBeat_BellTree` | west (cx −1) | second density band (59 + 73) |
| `PCG_ResonanceCathedral` | south-west set piece | 73-count cell, reads as a destination |
| `PCG_Colonnade` | **east** | the empty third — colonnade gives structure to open ground |

Z must be re-fitted too: three of the four sit 14k–29k **below** the landscape origin.

### 4b. Reuse the existing library — do not author new graphs

`EnvSandbox/PCG/Universal/` already has 38 graphs. Ground cover `PCG_FoliageDensity`;
rock/landmark `PCG_RockScatter`, `PCG_LandmarkScatter`; anti-uniformity
`PCG_ClusteringScatter`; paths `PCG_PathScatter` + `BP_PathSplineProvider`; shoreline
`PCG_WaterEdgeScatter` (this is an ocean monolith — the signature edge).

Density should read the **same landscape layer weights** the Gaea masks now drive, so PCG
and the material agree instead of fighting. Houdini scatter already reads
`LandscapeLayerSample` weights per the documented pipeline.

`EnvSandbox/PCG/README.md` is the placement doctrine: no graphs at the PCG root; use
`Universal/`, `Greybox/`, `Collections/`, `Styles/<Style>/`. Sol has already begun
`Styles/SeaAbove/`.

### 4c. Cute biomes and Nikki corridors

Style kits exist for Sakura, Grotto, Cosmic, Baroque and now SeaAbove. Sakura already
contains `PCG_Nikki_DreamStones`, `PCG_Nikki_MandalaBloom`,
`PCG_Nikki_PhyllotaxisGarden(_Walkable)` — promote those into a `Styles/Nikki/` kit rather
than authoring new ones.

Cute-biome material identity is **already in the master** and merely switched off:
`bNikkiGlitterHalo_Active`, `bNikkiPetalShadow_Active`, `bNikkiStickerEdge_Active`,
`bNikkiDreamWatercolor_Active`, `bNikkiPearlSheen_Active`, `bNikkiSDFRibbon_Active`,
`bKawaiiSquish_Active` are all `false`. Enabling them per-zone through material instances
is the cheapest possible route to a cute read — the shader work is done.

Corridors use the existing modular kit at `EnvSandbox/Meshes/Environment/`:
`corridor`, `corridor-corner`, `corridor-end`, `corridor-intersection`,
`corridor-junction`. Corridors are also where beat reactivity reads best — enclosed space
makes `Cymatic_BeatPulse` emissive legible in a way open terrain does not.

### 4d. Secret passages — last

`mesh_query` has the analysis to place these defensibly: `find_hiding_spots` and
`analyze_sightlines` for genuine concealment, `find_dead_ends` for candidates,
`analyze_choke_points` for where a hidden route should rejoin the spine to be a real
shortcut. Do this **after** 4a, because "secret" is defined relative to a main route that
does not yet exist.

---

## 5. Coordination

GPT Sol owns the landscape **material** lane (Gaea, snow SDF, triplanar, cymatics response)
and has begun `PCG/Styles/SeaAbove/`. The volume layout in §3–4a is not covered by that
plan and is the natural split.

Two agents were writing this level's materials through one editor today. Whoever picks up
§4 should check `git status` first — 92 files were modified in-flight at the time of
writing.
