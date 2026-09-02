# Melodia PCG Artist Tool Shelf / World-Brush Language — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready R&D spec  
**Decision:** BUILD SPIKE  
**Depends on:** `melodia.semantic-fields.v1`, `PCG_SEMANTIC_FIELD_DOMAIN_MAPPING_2026-08-31.md`, `UE58_NATIVE_WORLD_AUTHORING_BASELINE_2026-08-31.md`

## Goal

Turn UE5.8 PCG Editor Mode + Manual Editing into a Melodia-specific world-authoring language rather than a generic scatter workflow.

The shelf writes semantic intent. It does not directly own final species, materials, gameplay, or runtime truth.

```text
artist gesture
 -> semantic field / tagged region
 -> Houdini or native PCG interpretation
 -> Biome Core / PCG asset resolution
 -> SpeedTree / meshes / Niagara / materials
 -> optional Dash hero composition
```

## First tool set

| Tool | Authoring primitive | Writes | Typical consumer |
| --- | --- | --- | --- |
| `P3_FilterFlow_Brush` | paint | `melodia_filter_flow_strength` + explicit direction source | Houdini / PCG / Niagara |
| `P3_EcologyBias_Spline` | spline | `melodia_ecological_density` bias | Biome Core / PCG |
| `P2_MoltSuccession_Brush` | paint | `melodia_molt_age` | materials / ecology |
| `P2_ExclusionScar_Paint` | paint | project-local exclusion tag, never new ecology authority | PCG filters |
| `P1_TensionFiber_Spline` | spline | `melodia_tension_strength`, `melodia_tension_dir_ws` | Houdini / materials / VFX |
| `Monolith_Proximity_Volume` | volume | source volume from which proximity is derived | Houdini / PCG |
| `HeroDebris_Composition_Paint` | paint | hero-placement intent layer | PCG / optional Dash |
| `SpeedTree_Override_Paint` | paint | species/variant bias, not direct hard reference where avoidable | Biome asset resolver |

## Smallest useful spike

**Map:** `LV_RND_P3_PCGArtistTools`

Build only:

1. `P3_FilterFlow_Brush`
2. `P3_EcologyBias_Spline`
3. one downstream PCG graph that visualizes both as debug color + point density
4. save, close editor, reopen, regenerate
5. compare with one equivalent Dash-assisted hero pass

## Asset naming

```text
PCGAT_P3_FilterFlow_Brush
PCGAT_P3_EcologyBias_Spline
PCG_P3_SemanticPreview
DA_MelodiaBiomeAssetMap_RND
LV_RND_P3_PCGArtistTools
```

## Layering rules

1. **Semantic layer** — paint/spline/volume writes meaning.
2. **Compiler layer** — Houdini/native PCG derives secondary fields.
3. **Resolver layer** — Biome Core/PCG maps meaning to assets.
4. **Manual Editing layer** — durable native exceptions.
5. **Dash layer** — optional last-mile composition only.

Dash may move or finalize hero objects; it must not become the only store for biome density, Monolith influence, or species-selection logic.

## Regeneration and undo tests

Run these in order:

- create brush stroke, undo, redo;
- edit exposed tool parameters and regenerate;
- move source spline and confirm dependent output updates;
- Manual Edit one generated point, regenerate source graph, verify exception behavior;
- perform a Dash hero pass, regenerate base system, inspect duplicates/loss;
- close/reopen editor and repeat;
- inspect Git diff for opaque/generated churn.

## Semantic contract rules

- all cross-system scalars use `melodia.semantic-fields.v1` names;
- world-space vectors require the centralized UE↔Houdini conversion helper;
- tool assets may expose friendly labels, but machine-facing attribute names are versioned API;
- do not introduce complex UE-only metadata types into the cross-DCC contract until scalar/vector v1 is proven stable;
- tool presets may write source controls, but derived values such as distance/proximity should be recomputed by one owner.

## Evidence bundle

```text
Docs/Research/Evidence/PCGArtistTools/
  README.md
  settings_manifest.json
  fixed_camera_before.png
  fixed_camera_after.png
  reopen_result.md
  regeneration_result.md
  git_diff_summary.txt
```

Large traces/caches stay outside Git.

## Metrics

- minutes from blank map to useful authored result;
- second-revision time;
- number of opaque/generated assets;
- regeneration survival rate;
- Manual Editing survival;
- Dash survival;
- source-control churn;
- downstream semantic correctness;
- artist rating: can the result be art-directed without opening the graph?

## Decision gates

**ADOPT** if two artist-facing tools survive reopen/regeneration, preserve semantic meaning, produce understandable diffs, and beat raw graph editing for iteration.

**PARK** if useful but fragile, Experimental-editor UX becomes blocking, or Dash/native transforms remain faster for the intended task.

**REJECT** any tool preset that silently creates a second ecology/gameplay authority or stores critical intent only in opaque plugin state.

## Next build after pass

Expand the shelf in this order:

```text
P3_FilterFlow_Brush
P3_EcologyBias_Spline
Monolith_Proximity_Volume
P2_MoltSuccession_Brush
P1_TensionFiber_Spline
SpeedTree_Override_Paint
HeroDebris_Composition_Paint
```

The goal is not a large tool catalog. The goal is a small vocabulary that maps directly to Melodia's world semantics.