# World Streaming + Perceptual QA Harness — 2026-08-31

**Project:** Melodia Melusina / UE5.8  
**Status:** implementation-ready measurement infrastructure  
**Decision:** BUILD ONCE, REUSE EVERYWHERE

## Goal

Make streaming/HLOD/world-partition tests answer two questions at the same time:

1. did memory/streaming performance improve?
2. did the scene composition visibly get worse?

World Streaming Insights should become evidence infrastructure rather than another feature to casually adopt.

## Harness map

Use one representative chapter-shaped slice or dedicated test map:

`LV_RND_WorldStreaming_PerceptualRoute`

## Fixed route

Create one deterministic 60–120 second route with:

- wide horizon reveal;
- dense foliage approach;
- hero architecture approach;
- fast lateral camera move;
- one elevated vista;
- one turn that forces aggressive cell/HLOD transitions.

Record player/camera transform samples so the route can be replayed.

## Capture set

For every major world-representation test, collect:

```text
World Partition cell state
cell priority
estimated total/unique/shared package memory
streaming source timeline
World Streaming Insights minimap
Memory Profiler drilldown where useful
GPU/CPU frame timing
fixed-camera screenshots at checkpoints
video or frame sequence of visible transitions
```

Large traces stay outside Git; commit small summaries and manifests.

## Perceptual scorecard

At 8–12 fixed checkpoints score 1–5:

```text
horizon silhouette stability
hero landmark continuity
foliage canopy continuity
lighting/material continuity
HLOD pop severity
PCG density pop
shadow/VSM transition quality
animation/wind continuity
```

A technical win that produces obvious horizon collapse is not a production win.

## Comparators

Use this harness for:

- PCG/Biome Core runtime generation;
- SpeedTree vs experimental Nanite representation;
- HLOD changes;
- Fast Geometry Streaming WATCH canary;
- Mesh Terrain/world-representation experiments;
- Dash/procedural actor-count cleanup;
- chapter-scale density changes.

## Source-control contract

Commit:

```text
route manifest
engine/project settings delta
small CSV/JSON summary
checkpoint stills where lightweight
perceptual scorecard
final decision
```

Do not commit giant `.utrace` captures by default.

## Metrics

- peak/average cell memory estimates;
- streaming stalls or spikes;
- game-thread/render-thread/GPU frame times;
- actor/component counts where relevant;
- HLOD transition count;
- perceptual score average and worst checkpoint;
- package/cook result;
- repeatability across two runs.

## Decision gate

A streaming optimization is **ADOPT** only if it improves the targeted performance/memory problem and does not materially reduce the fixed-route perceptual score.

**PARK** if technically promising but Experimental instability or visual regressions remain.

**REJECT** any optimization that merely moves cost into authoring complexity or destroys camera-critical composition.

## Evidence path

```text
Docs/Research/Evidence/WorldStreamingQA/
  README.md
  route_manifest.json
  checkpoint_scorecard.csv
  streaming_summary.csv
  perf_summary.csv
  package_result.md
  decision.md
```

## Rule

Every future chapter-scale R&D lane that changes representation, density, actor count, HLOD, or world streaming should reference this harness instead of inventing its own performance story.