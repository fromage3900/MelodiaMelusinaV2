# PLAN — PCG convergence: Massive biome core + PCGEx + Blueprint PCG hosts (2026-09-24)

**Goal:** one layered PCG system. Logic lives once, variation lives in data, and every host (volume, Blueprint, World Compiler) drives the same pieces. Supersedes the "G5/G6" tail of `2026-09-24_173839-massive-world-pcg-port.md`.
**Inventory (live, 2026-09-24):** `Saved/Audit/massive_morning_20260924/pcg_inventory.json`
- 191 project PCG graphs: 42 use PCGEx, 36 are placed in a level, **114 have no references at all**.
- By folder: `EnvSandbox/PCG/Styles` 97 (Baroque 35, Escher 19, WP 16, Sakura 9, SeaAbove 9, 5 stubs); `Universal` 35; `_Dev` 11; `/Game/PCG/Graphs` 16 (demo); `Musical` 6; `Melodia/PCG` + `WorldCompiler` 12.
- PCGEx data: 12 `PCGExMeshCollection`. `PCGGraphInstance`: 1 (graph parameters are essentially unused).
- Blueprint hosts that reference PCG graphs: `BP_Morning_GoldenSpiral`, `BP_MelusinaRoomShell`, `BP_PCG_LargeAssembly`, `BP_PCG_SmallAssembly`.

## What exists now (proven today)

`/Game/Melodia/PCG/MassiveBiome/`:
- **Core:** `PCG_Melodia_MassiveBiome` — input pin `BiomeData` (attribute set: soft path to a `PDA_Vegetation` DA + `Cell_<Cat>` vector + `Thin_<Cat>` double per Flowers/Bushes/SmallRocks/BigRocks) → per category: grid → jitter → noise → density filter → world-ray projection → weighted match from DA → partition by Mesh → Loop vendor `PCG_VegetationTransform` → spawn by attribute.
- **Wrappers (biome = DA + density values):** `PCG_Biome_MorningMeadow` (island scale), `PCG_Biome_RockScatter` (corner scale), `PCG_Biome_CrystalGarden` (Universe Foundry floating crystals).
- **Live in Morning:** `Massive_Biome_Meadow` 992 inst; `Massive_Biome_CrystalGarden` 205 inst on BrushifyIsland_09; `WC_HeroCorner_WestRim_PCG_Companion` 25 art rocks (was greybox). Grounded checks: 0 floaters.

## Target layering

| Layer | Owns | One authority |
|---|---|---|
| **L0 Primitives** | ground projection (static mesh + landscape), density-from-data, transform-from-data, spawn-by-attribute, exclusion (paths/water/hero footprints) | subgraphs in `/Game/Melodia/PCG/Core/` |
| **L1 Data** | what spawns and how dense | `PDA_Vegetation` biome DAs + `PCGExMeshCollection`s (see C2) |
| **L2 Recipes** | a biome, a style set-piece, a path dressing | thin wrapper graphs, no logic |
| **L3 Hosts** | where and when | `PCGVolume`, BP hosts, World Compiler manifest |

PCGEx stays the structural engine (clusters, paths, room shells, Escher/Baroque/Phyllotaxis layouts). The biome core is the scatter engine. They meet at L0: a PCGEx layout outputs points/paths; the shared spawn and exclusion primitives dress them.

## Steps (each ends in a gate; Morning edits additive and PIE-proven)

### C1 — Extract L0 primitives from the biome core
- Split `PCG_Melodia_MassiveBiome` into subgraphs: `PCG_Core_GroundProject`, `PCG_Core_DensityFromData`, `PCG_Core_TransformFromData` (wraps vendor `PCG_VegetationTransform`), `PCG_Core_SpawnByAttribute`. The core becomes a composition of them.
- Add `PCG_Core_Exclude`: difference against tagged actors (`PCGExclude`: paths, lake, hero footprints). Fixes flowers/crystals overlapping the meadow canonical and paths.
- **Gate:** the three live biome volumes regenerate to the same counts (992 / 205 / 25) with 0 PCG errors.

- **C1 DONE 2026-09-24 ~19:03:** `/Game/Melodia/PCG/Core/` `PCG_Core_DensityFromData` (Density param pin → grid/jitter/noise/thin overrides), `PCG_Core_GroundProject`, `PCG_Core_TransformFromData`, `PCG_Core_SpawnByAttribute`; biome core is now a composition (per category: rename chain → Density → Ground → DA match → Xform → Spawn). Jitter moved to wrapper data (`JitMin_/JitMax_`). Gate passed: 992 / 205 / 25 identical per mesh, grounded, DA scale/yaw, 0 PCG errors, live A/B (shard thin 0.9 → 0 shards) proves no stale cache. `PCG_Core_Exclude` not built; `PCG_Core_PathCarve` staged but carves nothing as a subgraph (open).

### C2 — One mesh-list authority — DECIDED: PCGExMeshCollection (owner 2026-09-24, Jev 0.84)
- `PDA_Vegetation` has no material field, so rainbow MIs can't be expressed. `PCGExMeshCollection` supports per-entry material overrides, weights and variations.
- **Recommendation:** make `PCGExMeshCollection` the mesh authority; the biome DA keeps category structure + transform ranges and points each category at a collection. The core reads collection entries (PCGEx asset-collection-to-set) instead of raw `Mesh` fields.
- **Gate:** meadow flowers spawn with rainbow `MI_RainbowSpeedTree`/meadow MIs through a collection; `PCG_Meadow_RainbowBloom` (canonical meadow) reproduced by a wrapper → then retire it.

### C3 — PCGEx style graphs converge on L0
- Scope: the 16 live style/musical graphs first (SeaAbove 9, Escher 3, Sakura 3, Baroque 1, Musical Hero 3). Replace each graph's private scatter/spawn tail with `PCG_Core_SpawnByAttribute` + `PCG_Core_Exclude`; keep their PCGEx layout head untouched.
- **Gate:** per graph, before/after instance counts and a still from its level; 0 errored.

### C4 — Blueprint hosts on one pattern
- Pattern: BP owns a `PCGComponent` + one `PCGGraphInstance` asset per BP recipe; BP-specific inputs (spline, dimensions, seed) reach the graph as graph parameters, not duplicated graphs.
- Graph parameters must be authored by hand once per recipe graph in the editor (scripted creation isn't exposed in this build; set values afterwards via `PCGGraphParametersHelpers`).
- Convert `BP_Morning_GoldenSpiral`, `BP_MelusinaRoomShell` first; `BP_PCG_Large/SmallAssembly` are engine-demo derived — assess, likely retire.
- **Gate:** each BP regenerates identically in Morning; changing a BP property changes output without touching the graph.

### C5 — World Compiler hosts
- Hero corners (`PCG_HeroCorner_*`, PCGEx) and `PCG_WorldCompiler_PointField` consume L2 recipes by name from the `world.json` manifest (movement/music key → biome wrapper + seed).
- Fix audit findings in the same pass: WestRim main still spawns 160 greybox rocks; `WC_morning_rainbow_bloom_Field` spawns coral/kelp; EastBank/NorthDress mains generate nothing; NorthDress companion floats over empty space (no ground under the volume).
- **Gate:** one manifest chunk generates end to end; greybox count in Morning = 0.

### C6 — Retire dead graphs (red tier — owner OK per batch)
- 114 unreferenced graphs → move to `/Game/00_Archive/PCG_<date>/` in batches by folder (`WP` 16 all dead, `_Dev`, `_Scratch`, `_Deprecated`, `Legacy_Portfolio`, dead style stubs), with a reference check immediately before each move.
- **Gate:** 0 broken references; project opens clean.

### C7 — Massive pack landscape lane (later)
- River/lake/cliff/road tools need a landscape plus the `EditorScriptableToolsFramework` and `LandscapePatch` plugins, and roads need `r.VirtualTextures` (protected `DefaultEngine.ini`). Only for a future landscape level; not Morning.

## Rules carried forward
- Materials: MIs of existing masters only. Density lives in wrapper data, never in the core.
- After any scripted graph edit: save + `reload_packages` before regenerating, or the editor runs the stale graph (see memory `pcg-scripting-traps-ue58`).
- Check instance **scale/rotation ranges**, not just counts — a broken transform still spawns.
- Commit only on owner OK; vendor files force-added only where our assets reference them; `Docs/CREDITS.md` entry first.
