# PCG Biome Core as Melodia Ecosystem Compiler — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready R&D spec  
**Decision:** BUILD CANARY  
**Authority rule:** Houdini/project semantics define ecological meaning; Unreal resolves assets and runtime density.

## Hypothesis

UE5.8 PCG Biome Core can become the Unreal-side ecosystem compiler that translates canonical Melodia semantic fields into actual plant/prop populations without teaching Houdini about specific `/Game/...` assets.

```text
Houdini / PCG Artist Tools
  -> canonical semantic fields
  -> Biome Core local/global regions
  -> priority + blend + AssetID resolution
  -> SpeedTree / meshes
  -> runtime PCG detail
```

## Smallest useful spike

**Map:** `LV_RND_P3_BiomeCompiler`

Use one 40–80 m test patch with:

- two overlapping local biome regions;
- one global biome rule;
- one Monolith influence source;
- three SpeedTree/mesh logical asset classes;
- one runtime ground-detail layer;
- one fixed player route.

## Assets

```text
DA_MelodiaBiomeAssetMap_RND
PCG_Biome_P3_Local_A
PCG_Biome_P3_Local_B
PCG_Biome_P3_Global
PCG_Biome_P3_RuntimeDetail
BP_RND_MonolithInfluenceSource
LV_RND_P3_BiomeCompiler
```

## Semantic mapping

| Semantic | Biome use |
| --- | --- |
| `melodia_moisture` | filter / species weighting |
| `melodia_wind_exposure` | species/variant bias |
| `melodia_monolith_proximity` | influence/priority bias |
| `melodia_molt_age` | succession stage |
| `melodia_filter_flow_strength` | density/orientation bias |
| `melodia_ecological_density` | final density multiplier |
| `melodia_biome_id` | logical region identity |

Do not push full Unreal asset paths through Houdini if `AssetID` or another Unreal-owned resolver can maintain indirection.

## Overlap test

Construct a deliberate conflict:

- Local A = moist pearl-coral ecology;
- Local B = dry exposed steppe ecology;
- Monolith influence = invasive impossible growth;
- Global = chapter-level fallback.

Test:

1. no overlap;
2. A/B overlap;
3. A/B + Monolith influence;
4. priority swap;
5. blend-width edit;
6. asset-table change without changing Houdini fields.

The same semantic input should produce predictable, explainable ecological output.

## Runtime boundary

Houdini may compile fields offline/editor-time. Shipping runtime must not require Houdini.

Target:

```text
pre-generated semantics
 -> Unreal-owned resolver
 -> runtime hierarchical/GPU detail where justified
```

Dense GPU detail belongs after semantic resolution to avoid CPU/GPU ping-pong.

## SpeedTree boundary

SpeedTree remains botanical authoring truth. Biome Core selects logical species/variant IDs; the representation layer may later choose standard SpeedTree or an experimental Nanite representation without changing ecology semantics.

## Metrics

- author minutes to new biome rule;
- minutes to change one species mapping;
- overlap predictability;
- number of fields duplicated/reinterpreted;
- graph complexity;
- runtime generation CPU/GPU ms;
- visible pop on fixed route;
- memory/streaming footprint;
- reopen/regeneration repeatability;
- package/cook result;
- source-control churn.

## Hard gates

**ADOPT** if the resolver cleanly separates semantic meaning from asset choice, overlap/priority behavior is understandable, runtime detail is stable, and a species-map change requires no Houdini recook.

**PARK** if architecture is good but Experimental plugin behavior, runtime cost, or graph complexity is not yet production-safe.

**REJECT** if ecological truth becomes duplicated across Houdini and Biome graphs, asset mappings are too opaque to maintain, or package/reopen behavior is unreliable.

## Evidence

```text
Docs/Research/Evidence/BiomeCompiler/
  README.md
  semantic_input_manifest.json
  asset_map_manifest.json
  overlap_matrix.md
  fixed_route_capture.md
  perf_summary.csv
  package_result.md
  git_diff_summary.txt
```

## Promotion path

After a successful P3 canary:

1. connect `P3_FilterFlow_Brush` and `P3_EcologyBias_Spline`;
2. drive one real SpeedTree selection family;
3. add short-lived Cymatic Ecological Memory as a non-authoritative bias layer;
4. profile with World Streaming Insights;
5. only then consider chapter-scale migration.