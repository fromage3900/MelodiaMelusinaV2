# SpeedTree -> Nanite Representation Compiler — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** high-value experimental canary  
**Authority rule:** SpeedTree remains botanical authoring truth. Unreal representation may change; botanical source does not.

## Research question

Can one approved SpeedTree plant be transformed into a UE5.8 Nanite-oriented shipping representation without making botanical iteration worse than the runtime/storage savings are worth?

This is not a migration plan. It is a one-asset compiler canary.

## Candidate pipeline

```text
SpeedTree source
 -> exported geometry / skeleton / part metadata
 -> Houdini or Unreal preparation
 -> optional USD interchange
 -> Nanite geometry baseline
 -> experimental Nanite Assembly / skeletal representation
 -> wind / VSM / streaming / package benchmark
```

## Map and assets

```text
LV_RND_SpeedTree_NaniteRepresentation
ST_RND_SourceTree_A
SM_RND_Tree_GeometryNanite_A
NA_RND_Tree_Assembly_A
SK_RND_Tree_NaniteSkin_A
DA_RND_TreePartManifest_A
```

Use an existing project-owned tree with an approved silhouette and wind profile. Do not invent a synthetic vendor-demo plant.

## Three-lane benchmark

### A — production source baseline

Current SpeedTree import/material/wind path.

### B — standard Nanite geometry

Geometry-rich static representation using normal Nanite guidance where feasible. Keep botanical silhouette and material intent fixed.

### C — experimental part-based representation

Attempt repeated branch/frond/leaf part decomposition suitable for Nanite Assemblies and, only if practical, skeletal/Nanite wind experimentation.

If lane C becomes a multi-day reverse-engineering exercise, stop and record the blockage. That itself is a valid PARK result.

## Compiler manifest

Every conversion run records:

```json
{
  "schema": "melodia.speedtree-representation.v1",
  "source_asset": "...",
  "source_hash": "...",
  "speedtree_build": "...",
  "ue_build": "5.8.x",
  "houdini_build": "...",
  "representation": "baseline|nanite_geometry|nanite_assembly",
  "part_count": 0,
  "bone_count": 0,
  "material_slots": 0,
  "generated_assets": []
}
```

## Re-authoring test

This is mandatory.

1. capture all three lanes;
2. make one real botanical source edit in SpeedTree: branch length, leaf scale, or crown silhouette;
3. rebuild all lanes;
4. measure minutes to visual parity;
5. inspect whether part IDs/names remain stable;
6. inspect Git churn and generated asset replacement.

A runtime representation that cannot survive ordinary plant iteration is not production-ready.

## Wind boundary

- source botanical wind intent belongs to SpeedTree/project art direction;
- any UE experimental skeletal wind representation is a shipping implementation detail;
- do not accept a cheaper representation if it loses player-local/rhythm/Monolith response required by the final game;
- experimental Dynamic Wind limitations must be documented exactly for the tested UE build.

## Metrics

```text
source edit minutes
conversion minutes
uasset disk size
streaming memory
GPU ms
VSM cost
material/shader cost
wind cost
close-leaf quality
mid-distance canopy retention
far silhouette
package/cook result
reopen/rebuild stability
source-control churn
```

Capture fixed cameras at near/mid/far distances and one wind sequence.

## Pass / park / reject

**ADOPT representation compiler** only if a non-baseline lane provides a meaningful storage/runtime win, preserves silhouette/wind/art direction, packages successfully, and can be rebuilt after a source edit without unreasonable manual repair.

**PARK** if runtime numbers are interesting but conversion is fragile, experimental APIs are unstable, or re-authoring cost is too high.

**REJECT for production** if source changes routinely invalidate hand repair, packaging fails, or the new representation reduces close/mid visual quality enough to undermine the art direction.

## Evidence

```text
Docs/Research/Evidence/SpeedTreeNanite/
  README.md
  representation_manifest.json
  baseline_near.png
  baseline_far.png
  nanite_near.png
  nanite_far.png
  assembly_near.png
  assembly_far.png
  rebuild_after_source_edit.md
  package_result.md
  metrics.csv
```

## Integration boundary

The compiler must be replaceable. No gameplay or ecology logic may depend on Nanite Assembly internals. Biome/PCG resolves a logical plant/variant; the representation layer decides how that plant is shipped.