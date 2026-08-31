# Houdini ↔ Unreal PCG Bridge Architecture — Melodia 2026

**Date:** 2026-08-31  
**Project:** Melodia Melusina / Unreal Engine 5.8  
**Status:** HIGH-PRIORITY integration architecture discovered during deeper H22/UE5.8 research  
**Primary source:** SideFX Houdini-PCG plug-in documentation  

> This is potentially more important than adding another worldbuilding application because it removes a boundary between two systems Melodia already treats as core.

---

# 1. Discovery

SideFX now ships a dedicated **Houdini Engine for Unreal PCG plug-in** that allows a Houdini Digital Asset to exist directly as a node inside an Unreal PCG graph.

Primary docs:

- PCG overview: https://www.sidefx.com/docs/houdini/unreal/pcg/overview.html
- PCG installation: https://www.sidefx.com/docs/houdini/unreal/pcg.html
- PCG workflows: https://www.sidefx.com/docs/houdini/unreal/pcg/workflows.html
- H22 Engine changes: https://www.sidefx.com/docs/houdini/news/22/engine.html
- Houdini Engine licensing: https://www.sidefx.com/products/houdini-engine/

The integration supports:

- HDA nodes inside PCG graphs;
- PCG data/attributes flowing into Houdini;
- PCG-native data flowing back out of Houdini;
- mesh/spline/landscape/world-object inputs;
- HDA parameter overrides from PCG attributes/graph parameters;
- Houdini-generated meshes, curves, landscapes and skeletal meshes;
- cooking or baking outputs;
- Session Sync;
- PCG Editor Mode;
- PCG loops;
- PCG caching;
- raw point/attribute data without requiring creation of intermediate Unreal actors/assets.

Houdini 22 specifically improves this integration with faster PCG generation, named HDA inputs, customizable input-object attribute names and **Force PCG Outputs**.

No existing checked-in Melodia document or code path was found using the Houdini-PCG plug-in directly at the time of this audit.

---

# 2. Why this changes the super-pipeline

The previous architecture implied a relatively explicit handoff:

```text
Houdini
    -> export/bake fields/assets
    -> Unreal import
    -> PCG consumes them
```

The new architecture can be:

```text
UE PCG graph
    |
    | PCG points / splines / attributes / world objects
    v
Houdini HDA node
    |
    | procedural geometry + transformed semantic data
    v
UE PCG graph
    |
    | further filtering / biome rules / artist overrides
    v
native Unreal outputs
```

This can make Houdini part of the **world-compiler graph** rather than a disconnected upstream application.

That is a major architectural simplification if it proves stable.

---

# 3. Proposed ownership model

The bridge must not blur authority.

```text
Houdini HDA inside PCG
    = deep procedural transformation node

UE PCG
    = orchestration / distribution / Unreal world context

SpeedTree
    = botanical source assets

PCG Manual Editing / Editor Mode
    = local artist-authored exceptions

Unreal runtime
    = shipping state and gameplay authority
```

The HDA PCG node should behave like a powerful deterministic compiler stage, not like a hidden second world runtime.

---

# 4. Best first Melodia use: semantic-field transform, not mesh generation

Do not begin by generating a mountain.

Start with the smallest data-only test because it directly validates the new `melodia.semantic-fields.v1` contract.

## Benchmark — P3 PCG → Houdini → PCG semantic round-trip

**Map:** `LV_RND_HoudiniPCG_SemanticRoundTrip`

**Timebox:** 90 minutes after plugin/version/license setup.

### PCG input

Create 256–1024 deterministic PCG points with:

```text
melodia_moisture
melodia_monolith_proximity
melodia_ecological_density
melodia_filter_flow_strength
```

Plus one spline defining the broad P3 horizon-current direction.

### HDA operation

The HDA should:

1. ingest the raw PCG point data;
2. preserve a stable source ID;
3. calculate distance to the input spline;
4. remap ecology density from distance/proximity;
5. calculate or modify a P3 filter-flow strength field;
6. return **PCG-native data**, not meshes.

### PCG output

Use the returned values to:

- filter points;
- orient one harmless debug mesh/arrow;
- change density;
- display attributes in PCG inspection.

### Required proof

```text
PCG -> HDA -> PCG
```

must preserve:

- point count when expected;
- stable IDs;
- scalar values within tolerance;
- transform positions;
- spline meaning;
- canonical attribute names or an explicitly documented mapping.

---

# 5. Important technical trap: generic vectors are not automatically coordinate-converted

SideFX explicitly documents an interoperability trap:

> PCG point positions are transformed between Unreal and Houdini, but generic Vector attributes are not automatically converted because the bridge cannot know whether a vector represents a point, direction or arbitrary data.

This directly affects:

```text
melodia_filter_flow_dir_ws
melodia_wind_dir_ws
melodia_tension_dir_ws
```

## Consequence

The data contract must not assume `_ws` vector attributes survive the bridge correctly without explicit conversion.

### Required HDA convention

Define one helper layer inside all Melodia PCG HDAs:

```text
IN_UNREAL_WORLD_VECTOR
    -> explicit UE ↔ Houdini axis/handedness transform
    -> HOUDINI_WORLD_VECTOR
```

and the reverse on output.

Do not hand-write the conversion independently in each HDA.

### Canary vector

Input known axis values:

```text
(1,0,0)
(0,1,0)
(0,0,1)
```

Round-trip them and record exact Unreal results.

The bridge is not approved for semantic vectors until this passes.

---

# 6. Raw PCG output contract

SideFX provides two ways to emit PCG-native data:

1. author `unreal_pcg_params` on the HDA output;
2. enable **Force PCG Outputs** on the PCG HDA node.

## Melodia rule

During initial R&D, prefer **explicit output intent** in the HDA rather than globally forcing every HDA output into PCG data.

Use Force PCG Outputs as a debugging/rapid-prototyping option.

### Cleanup trap

SideFX notes that `unreal_pcg_params` can pass through downstream HDA nodes and unintentionally cause later outputs to be treated as PCG data.

Therefore every HDA must explicitly decide whether to:

- preserve;
- replace;
- delete

`unreal_pcg_params` before output.

Add this to HDA validation.

---

# 7. Output tagging contract

Multiple HDA outputs are merged into one PCG data stream and tagged internally such as:

```text
output_0
output_1
```

Downstream PCG nodes must filter by tag to recover separate outputs.

## Melodia recommendation

Every multi-output PCG HDA should define an explicit tag map in its manifest:

```yaml
outputs:
  output_0: semantic_points
  output_1: diagnostic_splines
  output_2: generated_geometry
```

Do not make downstream graphs rely on positional output meaning without documentation.

Where SideFX allows customized semantic tags, prefer them; otherwise keep the manifest mapping stable.

---

# 8. Parameter override architecture

PCG graph parameters and attribute sets can override HDA parameters when names match the HDA's **internal parameter name**, not the visible label.

This is a hidden source of silent failure.

## Melodia rule

HDA specs must record:

```text
ui_label
internal_name
expected_type
default
PCG_override_allowed
```

Example:

```yaml
- label: Filter Flow Radius
  internal_name: filter_flow_radius_m
  type: float
  default: 25.0
  pcg_override_allowed: true
```

Do not rename internal HDA parameters casually after a PCG graph depends on them.

Treat internal names as API.

---

# 9. Caching is dangerous when Houdini reads external files

SideFX notes that PCG cache invalidation does not automatically know when an HDA has changed external data such as a `.bgeo` file.

If the external source changes, the PCG graph may reuse stale output.

## Rule

For HDAs that read outside Unreal:

```text
Use PCG Cache = OFF
```

unless the external input hash/version is explicitly incorporated into a PCG-visible dependency.

For self-contained HDAs driven entirely by PCG/HDA parameters, caching may be enabled after determinism testing.

### Evidence field

Every result records:

```text
pcg_cache = on/off
external_file_dependencies = [...]
force_generate_required = yes/no
```

---

# 10. Cook vs Bake vs Clear PCG Link

The Houdini-PCG node can cook temporary content or cook+bake permanent Unreal content.

Baked content is still associated with the PCG graph and can be deleted/regenerated by PCG cleanup unless the link is explicitly cleared.

## Recommended phases

### R&D

`Cook` only.

### Approved authoring tool

`Cook` while editing → `Cook and Bake` for promotion.

### Frozen artifact

Bake → validate → `Clear PCG Link` only when deliberately converting the result into independently-owned Unreal content.

Never clear the link simply to hide a broken regeneration path.

---

# 11. HoudiniPCGActor source-control rule

Cooking/baking can generate a `HoudiniPCGActor` container and temporary/baked content.

This could create source-control churn if agent workflows repeatedly generate/rebuild it in shared maps.

## Initial policy

- HDA PCG tests live in isolated R&D maps.
- Generated temporary content is not committed.
- Permanent baked assets need deterministic naming and a manifest before commit.
- No shared chapter map receives a HoudiniPCGActor until the round-trip and source-control tests pass.

---

# 12. PCG Editor Mode + Houdini is the particularly interesting combination

SideFX explicitly supports PCG Editor Mode.

That creates a possible artist-facing Melodia workflow:

```text
artist paints/splines in UE
        ↓
PCG Editor Mode data
        ↓
Houdini HDA transforms deep procedural meaning
        ↓
PCG responds immediately
        ↓
artist manually overrides final exceptions
```

## Candidate P3 workflow

`P3_FilterFlow_Spline`

```text
UE spline gesture
 -> PCG attributes
 -> HDA generates curvature-aware field/distance data
 -> PCG orients/densifies ecology
 -> Niagara/materials consume field
 -> Manual Editing fixes hero composition
```

This is potentially a much stronger artist workflow than opening Houdini for every P3 field adjustment.

Houdini still supplies the algorithm; Unreal supplies the interaction surface.

---

# 13. PCG loops — do not casually instantiate an HDA per point cluster

SideFX states that PCG loops instantiate one HDA per loop iteration and does not impose a hard count, but warns about complex HDAs iterating many times.

## Rule

Do not build:

```text
1000 PCG clusters
 -> loop
 -> 1000 HDA sessions/cooks
```

unless profiling proves it is appropriate.

Prefer batching point sets into one HDA cook where possible.

### Performance benchmark

After the semantic round-trip succeeds, test:

```text
1 HDA x 10,000 points
vs
10 HDA iterations x 1,000 points
```

Measure:

- editor cook time;
- memory;
- session responsiveness;
- cache behavior.

Use the result to establish a maximum recommended HDA loop granularity.

---

# 14. Landscape support is not the first target

Houdini-PCG supports landscape creation and landscape modification with caveats.

Melodia's world R&D is already exploring Mesh Terrain and non-heightfield anatomy, so landscape integration is useful but not strategically urgent.

Use the bridge first for:

1. semantic fields;
2. curves/splines;
3. point clouds;
4. local mesh generation;
5. only then landscapes.

---

# 15. Licensing nuance

SideFX currently offers Houdini Engine for Unreal commercial licenses for free, but the plugin still requires a compatible Houdini Engine license and a full Houdini installation under the surface.

Important distinctions:

- Houdini Engine for Unreal can run compatible commercial `.hda` assets in UE;
- Houdini Engine Indie is compatible with Indie asset formats and has separate restrictions;
- Houdini Apprentice assets do **not** work with normal Houdini Engine plug-ins;
- an Engine license does not provide the interactive Houdini GUI;
- interactive authoring still requires the appropriate Core/FX/Indie/Education license.

### Project action

Do not let earlier `hserver` failures blur these separate questions:

```text
Can Brennan author/edit the HDA interactively?
Can Unreal cook the already-authored HDA through Houdini Engine?
Can batch/hython run outside the UE plugin?
```

Record each license capability independently.

---

# 16. Concrete first implementation plan

## Spike 0 — installation canary

- [ ] Record exact Houdini 22 build.
- [ ] Record exact UE 5.8 patch.
- [ ] Install the `5.8-PCG` Houdini Engine plugin variant rather than assuming the normal plugin includes PCG support.
- [ ] Confirm PCG HDA node appears.
- [ ] Confirm a trivial HDA cooks.
- [ ] Confirm free/appropriate Engine license checkout.

Stop here if plugin/build mismatch exists.

## Spike 1 — scalar semantic round-trip

- [ ] 256 PCG points.
- [ ] `melodia_moisture` and `melodia_monolith_proximity` in.
- [ ] HDA computes `melodia_ecological_density` out.
- [ ] Validate value tolerance and point count.

## Spike 2 — vector-space canary

- [ ] axis test vectors;
- [ ] explicit conversion helper;
- [ ] `melodia_filter_flow_dir_ws` round-trip;
- [ ] capture manifest.

## Spike 3 — UE spline → HDA P3 field

- [ ] author spline through PCG Editor Mode;
- [ ] HDA derives field strength/distance;
- [ ] return PCG point attributes;
- [ ] orient debug ecology;
- [ ] measure cook latency while spline is edited.

## Spike 4 — SpeedTree ecology consumer

- [ ] use HDA-generated PCG field to select/orient existing SpeedTree assets;
- [ ] no new plant authoring;
- [ ] verify recook and artist override behavior.

## Spike 5 — source-control/bake test

- [ ] cook;
- [ ] bake;
- [ ] reopen editor;
- [ ] regenerate;
- [ ] inspect temp/baked folders;
- [ ] inspect Git diff;
- [ ] validate Clear PCG Link behavior in duplicate test asset only.

---

# 17. Promotion criteria

Promote Houdini-PCG from R&D to **CORE BRIDGE** only if:

- scalar and vector semantic round-trips are understood;
- cook latency supports interactive artist use for at least one real HDA;
- source-control behavior is predictable;
- no stale-cache hazards remain undocumented;
- plugin/build pinning is reproducible on a second machine;
- baking leaves native UE assets when needed;
- PCG graph ownership remains readable;
- losing Houdini Engine temporarily does not make already-baked shipping content unusable.

If it passes, this bridge should likely outrank several external worldbuilding tools because it directly joins the two systems Melodia already intends to own.

---

# 18. New super-pipeline hypothesis

```text
                    SPEEDTREE
                   botanical truth
                        |
                        v
UE PCG Editor Mode --> UE PCG GRAPH <-------------------+
 artist gestures         |                              |
                         | points/splines/attrs          |
                         v                              |
                    HOUDINI HDA                         |
                deep procedural transform               |
                         |                              |
                         | PCG-native semantic data      |
                         v                              |
                    UE PCG GRAPH                         |
               biome/distribution logic                 |
                         |                              |
              +----------+-----------+                  |
              |                      |                  |
         BIOME CORE             MANUAL EDITING          |
       scalable ecology         hero exceptions         |
              |                      |                  |
              +----------+-----------+                  |
                         |                              |
                  SPEEDTREE ASSETS                      |
                         |                              |
                  NIAGARA/MATERIALS <---- semantic fields
                         |
                 WORLD PARTITION
                         |
                    SHIPPING UE
```

This is more than a software bridge.

It is a plausible way to make Houdini algorithms **feel native to the Unreal environment artist** while preserving procedural rigor.