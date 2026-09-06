# PCGEx Gallery Review — what's alive, what's hollow, how to use it wisely (2026-09-03)

## The census (live node audit via asset registry, editor on :9316)

754 PCGGraph assets exist. The "gallery" is mostly names. Verified:

### LIVE — graphs with real spawners (usable as-is)
| Graph | Nodes | Spawner | Notes |
|---|---|---|---|
| `PCG_Hero_ResonanceCathedral` | 24 | 1 `PCGSpawnActorNode` | **Proof-of-pattern.** Live in LV_SeaAbove_Prototype (24 music nodes). Chain: CreateSpline → TensorSpin → ExtrudeTensors → SplineSampler → SampleNearestSpline → 6 chord pads |
| `PCG_Hero_XylophoneTrail` | 12 | 1 `PCGSpawnActorNode` | Live spawner. The "ribbon" graph — path-following music trail |
| `PCG_Hero_BellTreeGarden` | 14 | 1 `PCGSpawnActorNode` | Live spawner. The "garden" graph — bell trees |

### HOLLOW — zero spawner nodes (scaffolds, not systems)
| Graph | Nodes | Verdict |
|---|---|---|
| `PCG_Nikki_PhyllotaxisGarden_Walkable` | 8 | **Hollow** — the golden name, no content. Do NOT wire expecting output |
| `PCG_BezierColonnadeAvenue` | 4 | Hollow |
| `PCG_BezierGardenPromenade` | 5 | Hollow |
| `PCG_BezierSplineGarden` | 4 | Hollow |
| `PCG_BezierVistaTerrace` | 5 | Hollow |
| `PCG_MeadowFalloff` | 8 | Filter/mask, not spawner — composeable but inert alone |
| `PCG_PathScatter` | 33 | Complex graph, 0 spawners at top level; subgraph spawners unknown |
| `PCG_BaroqueNaveVaultEx` | 3 | Hollow (confirmed 09-01 investigation) |
| `PCG_Baroque_Scatter` | 12 | Hollow (confirmed) |

### Composable subgraphs (filters, NOT outputs)
- `PCG_Sub_WalkabilityFilter` (3) — **the pacing gate**. Reject points the player can't stand on.
- `PCG_Sub_BaroqueAlongPath` (3) — path-relative placement helper.

## What this means

1. **The gallery's real asset is the toolkit, not the graphs.** `Plugins/PCGExtendedToolkit` ships 400+ element types (CreateSpline, BlendPath, BevelPath, DistanceFilter, NeighborSample, NoiseFilter, SortPoints, Bitmask, RecursiveGrammar, ParcelSplit). The named style graphs are mostly unfinished scaffolds from exploration; wiring them in expecting output = the silent-PCG defect class we already hit twice.

2. **One proven pattern to reuse, not reinvent:**
   `PCGSpawnActorNode → PCGExCreateSpline → PCGExTensorSpin → PCGExExtrudeTensors → SplineSampler → PCGExSampleNearestSpline`
   That's ResonanceCathedral — the only graph family that demonstrably generates. Any new walkway/garden/overlook graph should be built on this spine, not on the hollow Bezier/nikki scaffolds.

3. **Golden math lives in the manifest, not the graph.** Phyllotaxis (137.5° golden angle), φ-band falloff `(D/(d+D))^φ`, and φ-scaled beat spacing are deterministic math — compute them in Python (heatmap generator already does), emit spline/point data, feed the proven PCG graph pattern. Don't search for golden geometry inside the toolkit; author it and hand it to the graph.

## Wise use — mapping the gallery to the 5 beats

| Beat | Graph | Action |
|---|---|---|
| 1 Threshold | `PCG_Sub_WalkabilityFilter` + `PCG_Hero_ResonanceCathedral` pattern | Build entry gate as spline+spawner cluster; filter by walkability |
| 2 Ribbon | `PCG_Hero_XylophoneTrail` (LIVE) | Reuse as-is; re-spline to follow golden spiral |
| 3 Overlook | `PCG_BezierVistaTerrace` (HOLLOW) | Do NOT use. Build new from ResonanceCathedral pattern, φ-scaled terrace ring |
| 4 Garden | `PCG_Hero_BellTreeGarden` (LIVE) | Reuse; place at music-key beat, ring = phyllotaxis points from Python |
| 5 Departure | `PCG_Hero_XylophoneTrail` variant | Trail-to-dock; sparse fade = φ falloff |

Subgraphs to herald: `PCG_Sub_WalkabilityFilter` gates every static spawner so the walkway stays walkable; `PCG_PathScatter` (33 nodes) is worth ONE editor-authoring pass if the PCG UI is open — it may already encode a scatter-to-path pattern we should copy rather than rebuild.

## Anti-duplication standing rules
- Extend/populate the LIVE Hero family; never build a parallel spawner.
- Hollow scaffolds: either fill their spawners in the PCG editor (owner/UI work) or leave them; wiring them from Python produces silent zero-instance graphs.
- One PCG authority: ResonanceCathedral's spline-creating pattern is THE reusable seam.

## Evidence
- Node census run live 2026-09-03 via asset registry + `get_editor_property('nodes')` on 13 graphs.
- Live-spawner table above is the durable record; re-run the census before touching any graph.