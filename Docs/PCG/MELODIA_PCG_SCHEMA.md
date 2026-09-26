# Melodia PCG Schema — corridors, passages, houses, dioramas (v0.1, 2026-09-24)

Working schema for reusable content generation. Decisions come from the live Jev audit
(`Prototypes/JevPCGConvergenceAudit/audit_log.json`, `jev-1.13.0`, 2026-09-24) and the convergence
plan (`.hermes/plans/2026-09-24_184500-pcg-convergence-plan.md`). Jev probabilities in brackets.

## 1. Four layers

| Layer | What | Where |
|---|---|---|
| **L0 Primitives** | subgraphs with one job each | `/Game/Melodia/PCG/Core/` |
| **L1 Data** | meshes, densities, dimensions | PCGEx mesh collections + recipe data |
| **L2 Recipes** | thin wrapper graphs, no logic | `/Game/Melodia/PCG/Recipes/<Kind>/` |
| **L3 Hosts** | where/when it runs | `PCGVolume`, BP hosts, World Compiler |

Rules: logic lives once in L0; variation lives only in L1 data; L2 wires data to L0; L3 never duplicates a graph.

## 2. Authorities (locked)

| Concern | Authority | Jev |
|---|---|---|
| Paths / passages / corridors | **Placed spline spines** — `Actor + SplineComponent`, tags `PCG_Spline` + `PathSpline` (existing convention), label `WC_Corridor_*`. Everything samples them; nothing else invents a path. | 0.62 (spline + PCGEx refine 0.38 — refine allowed as an L0 step, never as authority) |
| Structure (houses, rooms, dioramas) | **PCGEx cluster layout** decides rooms/doors/corridor edges; a grammar pass (PCGPrimitives) skins walls/floors/facades per room. | 0.39 (low confidence; PCGPrimitives-only 0.29) — revisit after the first house |
| Meshes | **`PCGExMeshCollection`** (per-entry material overrides, weights). Massive `PDA_Vegetation` DAs migrate to collections. | 0.84 |
| BP hosts | BP owns a `PCGComponent` + one `PCGGraphInstance`; BP inputs flow as **graph parameters**. | 0.88 |
| Scatter | `PCG_Melodia_MassiveBiome` core (BiomeData pin: DA + `Cell_/Thin_` per category) | live |

Riskiest (Jev 0.80): **scripting gaps** — graph parameters and new input pins can't be created
from script in this build (pins need save + `reload_packages`; graph params need one manual
editor pass per recipe graph). Budget an owner/editor session for C4.

## 3. Tags and attributes (the contract)

Actor tags (L3 → L0):
- `PCG_Spline` (+ `PathSpline`) — spline spine; carves passages, drives corridor dressing. Existing tag, already on `WC_Corridor_A_to_B/B_to_C/C_to_D`.
- `PCG_Exclude` — any actor whose bounds must stay clear (hero footprints, lake edge, doors).
- `PCG_Ground` — optional: restrict projection to these actors (default: any blocking static mesh).
- `PCG_HouseLot` — volume or spline enclosing a house layout.

Point/param attributes (L1/L2 → L0):
| Attribute | Type | Meaning |
|---|---|---|
| `BiomeData` | soft object path | scatter recipe DA |
| `Cell_<Cat>` / `Thin_<Cat>` | vector / double | per-category grid cell and density-filter lower bound |
| `PathDist` | double | distance to nearest `PCG_Spline` spine (PCGEx `SampleNearestSpline`); carve keeps `PathDist > 700` (existing convention from `PCG_Nikki_PhyllotaxisGarden_Walkable` / `PCG_HeroCorner_WestRim`) |
| `PathEdgeWidth` | double | dressing band outside the carve (default 150 cm) |
| `RoomId`, `RoomKind` | int, name | house cluster node identity / purpose |
| `DoorEdge` | bool | cluster edge is a doorway/passage |
| `Collection` | soft object path | PCGExMeshCollection per kind/category |

## 4. L0 primitives (target set)

| Subgraph | In → Out | Status |
|---|---|---|
| `PCG_Core_GroundProject` | points → points on `PCG_Ground`/blocking surfaces (world ray) | inside biome core; extract (C1) |
| `PCG_Core_DensityFromData` | points + `Cell_/Thin_` → thinned points | inside biome core; extract |
| `PCG_Core_TransformFromData` | points + DA entry → transformed points (vendor `PCG_VegetationTransform`) | inside biome core; extract |
| `PCG_Core_SpawnByAttribute` | points + `Mesh`/`Collection` → instances | inside biome core; extract; switch to PCGEx collection |
| `PCG_Core_PathCarve` | points + `PCG_Spline` spines → points with `PathDist > 700` | **built** — extracted from the existing inline carve (GetSpline → PCGExSampleNearestSpline → AttributeFiltering); wired into the biome core |
| `PCG_Core_PathEdge` | spines → points in the edge band (for borders, lanterns, stepping stones) | next |
| `PCG_Core_Exclude` | points + `PCG_Exclude` actors → points | next |
| `PCG_Core_HouseLayout` | lot → PCGEx cluster (rooms = nodes, `DoorEdge` edges) | prototype (sandbox) |
| `PCG_Core_HouseSkin` | cluster → walls/floors/openings via grammar + collections | prototype (sandbox) |

## 5. Recipe kinds (L2)

- `Biome/` — scatter (live: MorningMeadow, RockScatter, CrystalGarden).
- `Passage/` — spine → carve + floor/edge dressing (stepping stones, arches, lanterns).
- `House/` — lot → layout → skin (cottage, salon, tower).
- `Diorama/` — house + passage + biome composed in one recipe (a scene tile).

## 6. Hosts (L3)

- `PCGVolume` in art levels (recipe by graph).
- BP hosts: `BP_MelusinaRoomShell` becomes the House host (today it is an empty Actor with one
  PCGComponent and its graph has 0 nodes). `BP_Morning_GoldenSpiral` converts to the pattern.
  `BP_PCG_Large/SmallAssembly` are engine-demo derived: retire unless used.
- World Compiler: manifest names a recipe + seed per chunk.

## 7. Proof gates (every recipe)

Counts by mesh; scale/rotation ranges (not just counts); grounded check (trace under each sample);
carve check (no instance within 700 cm of a `PCG_Spline` spine); lit PIE still; 0 PCG errors;
save + `reload_packages` before regenerate.
