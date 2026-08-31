# Natural Geology -> Impossible Anatomy Compiler — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready terrain R&D spec  
**Decision:** BUILD COMPARATIVE SPIKE

## Goal

Use Gaea or World Creator for believable macro-geology, then deliberately violate that geology in Houdini while preserving useful erosion/drainage/semantic evidence for Unreal.

```text
Gaea / World Creator
 -> height + erosion/drainage masks
 -> Houdini anatomical / impossible transform
 -> semantic fields + collision/representation prep
 -> Unreal mesh / terrain R&D representation
```

## Benchmark brief

**Horizon Eater highland / chalk steppe:** believable drainage and erosion at macro scale, then transformed into impossible folded/anatomical landforms.

## Maps and files

```text
LV_RND_ImpossibleGeology_Highland
HG_RND_HorizonEater_Base_Gaea
HG_RND_HorizonEater_Base_WorldCreator
HDA_Melodia_ImpossibleGeology
DA_RND_GeologyManifest
```

## Phase 1 — natural source shootout

Give Gaea and World Creator the same:

- target extent;
- height range;
- first-pass timebox: 30 minutes;
- required outputs: height + 3–4 useful masks;
- one revision request.

Required masks:

```text
erosion
flow/drainage
slope or deposition
material/region candidate
```

Score natural macroform quality, useful masks, revision speed, bridge predictability, source-file size, and Houdini handoff.

## Phase 2 — Houdini impossible transform

Houdini consumes source height/masks and performs one deliberately non-natural transform:

- folded escarpment/cavity;
- stretched anatomical ridge;
- tension scar network;
- suspended/undercut form where representation allows.

Houdini may derive:

```text
melodia_slope
melodia_moisture
melodia_soil_depth_m
melodia_monolith_distance_m
melodia_monolith_proximity
melodia_tension_strength
melodia_tension_dir_ws
melodia_filter_flow_strength
melodia_filter_flow_dir_ws
```

## Representation test

Do not let source terrain tool dictate Unreal representation.

Evaluate at least:

1. standard Landscape-compatible result where valid;
2. static/Nanite mesh result for impossible topology;
3. UE5.8 Mesh Terrain experiment only in an isolated map if the feature/build is available and stable enough for the canary.

## Source-control and resync test

For World Creator bridge workflows, destructive reset/sync options must be tested only in the disposable map. Record what disappears with reset ON vs OFF.

For Gaea, record bridge metadata/scale assumptions and avoid making the Unreal Landscape bridge the only path if the final topology cannot remain a Landscape.

## Metrics

- source-authoring minutes;
- revision minutes;
- mask usefulness;
- Houdini transform minutes;
- semantic-field retention;
- Unreal import/setup minutes;
- disk footprint;
- streaming/runtime cost;
- visual silhouette quality;
- collision practicality;
- re-authoring cost after source terrain edit;
- package/cook result.

## Decision

**ADOPT a front-end role** if the terrain tool gives faster/better believable geology and useful masks while remaining replaceable before Houdini.

**PARK** if bridge convenience creates destructive sync risk or handoff is too opaque.

**REJECT final-terrain ownership** for any workflow that prevents Houdini from performing the required impossible topology or makes source edits prohibitively expensive.

## Evidence

```text
Docs/Research/Evidence/ImpossibleGeology/
  README.md
  source_settings_gaea.json
  source_settings_worldcreator.json
  handoff_manifest.json
  before_after_fixed_camera.md
  semantic_field_preview.png
  resync_test.md
  perf_streaming_summary.csv
  decision.md
```

## Production doctrine

Natural terrain generators provide geological prior art. Houdini owns the violation. Unreal owns shipping representation.