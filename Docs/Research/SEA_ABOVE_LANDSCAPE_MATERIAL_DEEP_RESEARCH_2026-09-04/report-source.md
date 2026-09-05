# SeaAbove landscape material and curated biome research

**Audience:** technical art and level design owners of `LV_SeaAbove_Prototype`  
**Date:** 2026-09-04  
**Scope:** Gaea landscape intake, reusable UE5.8 landscape shading, triplanar normals, snow breakup, cymatics, and golden-ratio PCG biome dressing. Houdini Engine and VDM authoring remain a later input lane.

## Executive answer

The authored 5 km landscape should remain at its source scale. The durable path is one normalized world-space Gaea projection for exported whole-landscape data, independent tiled material lanes for close detail, and a measured triplanar option for steep or damaged rock. The current master already has the right high-level separation, but the Glacier instance needs an explicit semantic Snow mask and a dedicated whole-landscape color parameter so a source color map cannot be mistaken for a tilable layer texture. Weight values must be clamped to 0–1 and every normalized coordinate must be saturated before sampling.

For PCG, keep the existing Fiblat node and golden-ratio constant as the macro layout, project the result with a landscape-only raycast, then shape the density with slope, elevation, distance-to-landmark, and sightline masks. Use large world-partition cells for hero meshes and smaller cells for flowers, motes, and ground cover. Epic's PCG documentation confirms that points carry density, bounds, transforms, and custom attributes, and that partition and hierarchical generation are intended for large worlds and multi-scale content ([PCG overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-overview), [PCG generation modes](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-generation-modes-in-unreal-engine?lang=en-US)).

## Implemented evidence

- `contract.json` exports `Base/Snow/Water/Rock`, three 1009² weightmaps, XY scale 495.5401 cm/vertex, and Z scale 244.4531 cm/height unit.
- The active Glacier instance is parented to `M_Master_Nikki_Landscape`, carries `GaeaLandscapeMin=(-249752.21875,-249752.21875)` and `GaeaLandscapeSize=(499504.4375,499504.4375)`, and compiles with Gaea switches enabled.
- Four eastern PCG cells are grounded by downward landscape-only raycasts. The new Fiblat cell uses 140 points, `GoldenRatio`, an 18 m local shape, and a measured ~40 m generated footprint.
- `MF_Triplanar_LandscapePro` already supports scale, rotation, offset, axis weights, decorrelated breakup, explicit gradients, and a separate normal output. Its normal implementation is being tightened against the published surface-gradient formulation before any high-cost optional tier is enabled.

## Source-backed analysis

### Landscape and Gaea coordinates

UE landscape paint layers are material-defined and can have different textures, scaling, rotation, and panning ([Landscape Paint Mode](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-paint-mode-in-unreal-engine)). A Gaea color or mask export that represents the entire terrain therefore needs a single world-to-0..1 mapping; it must not inherit a tilable layer's UV scale. The implementation uses `(AbsoluteWorldPosition.xy - GaeaLandscapeMin.xy) / GaeaLandscapeSize.xy`, then `saturate` before sampling. This gives one map traversal over the authored landscape and a predictable edge when the camera or ocean is outside it.

### Triplanar normals

Mikkelsen's *Surface Gradient–Based Bump Mapping Framework* gives a published treatment of volume bump maps, including triplanar projection, explicit derivatives, and normalized axis weights ([JCGT paper](https://jcgt.org/published/0009/03/04/)). The practical consequence is that tangent-space samples cannot be added as if all three planes share one tangent frame. Each plane must be reoriented into the same surface frame (or converted to a surface gradient) before blending. The updated function keeps explicit `SampleGrad` derivatives and uses axis signs/swizzles with a reoriented blend, then normalizes once in world space.

### Snow breakup and macro variation

Snow coverage is a field, not a binary material switch. A stable reusable mask is the product of painted/Gaea coverage, an up-facing term, a slope term, and bounded multi-scale noise. The close layer uses a 0.6–6 m noise band; the far layer uses a 20–80 m macro band. A signed-distance or edge band is useful only when its encoding and range are known; otherwise it stays behind a static switch. The current SDF frost lane remains disabled until its encoded range is validated against source pixels.

### Cymatics

The landscape consumes the existing cymatics collection parameter and clamps its contribution by `CymaticsLandscapeAmount` and `CymaticsLandscapeMaxEmission`. Keeping one writer and many bounded consumers prevents material instances from inventing independent audio time bases. A separate quiet and active PIE capture is the acceptance test.

### Curated biomes

The PCG framework exposes point density, transforms, bounds, and user attributes, and its `Transform Points` node is specifically intended to introduce controlled natural variation ([PCG node reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-node-reference-in-unreal-engine)). The project therefore uses Fiblat/golden-angle spacing for the readable macro rhythm, then applies local biome masks for slope, elevation, landmark distance, and sightline clearance. This is deterministic and art-directable: changing the anchor or scale changes the district without rewriting the distribution.

## Proposed reusable controls

1. `Gaea_WholeLandscapeColor` (clamped sampler) owns the once-over source color. `Ground_Albedo`, `Grass_Albedo`, `Rock_Albedo`, `Snow_Albedo`, and `Water_Albedo` remain independently tiled close-detail lanes.
2. `Gaea_SnowMask`, `Gaea_WaterMask`, and `Gaea_RockMask` are semantic slots. `Gaea_SlopeMask` is reserved for a true slope or procedural mask; the Rock export must not silently gate Snow.
3. `TriplanarPro_BlendStrength` is a runtime scalar blend into the landscape layer result; `bRockTriplanarNormals` is a static permutation gate. Keep it off in the standard tier and enable it for steep rock or hero captures.
4. `Snow_BreakupWorldSizeCM`, `Snow_BreakupStrength`, `TriplanarPro_BreakupScale`, and `TriplanarPro_BreakupContrast` are bounded controls. All instance overrides are validated against `[0,1]` where they represent weights.
5. PCG cells use 25.6 km partition semantics for streaming, 2.5–8 km macro cells for terrain dressing, 40–120 m Fiblat gardens for hero pockets, and 4–20 m detail cells for flowers and motes.

## Acceptance and limits

- Baseline and repaired landscape captures must show one full Gaea traversal without repeating seams at both close and far distances.
- A triplanar normal test must show no axis inversion on a six-face primitive and no seam at a 45° slope. Compare instruction counts before and after enabling the permutation.
- A quiet/active PIE pair must show cymatics changing the bounded emissive response while leaving base color and roughness stable.
- `W_Glacier_Rock` is currently near-black (max 31/255), so it cannot produce a strong rock biome until Gaea re-exports a normalized rock layer. `W_Glacier_Water` is sparse by design. These are source-data limits, not shader controls.
- Runtime SDF, Houdini VDMs, and high-cost tessellation stay deferred until the measured standard tier reads correctly.

## Claim → source ledger

| Claim | Source |
|---|---|
| PCG points expose density, bounds, transforms, and custom attributes | [Epic PCG overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-overview) |
| Partitioning and hierarchical generation support large worlds and multi-scale meshes | [Epic PCG generation modes](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-generation-modes-in-unreal-engine?lang=en-US) |
| Transform Points provides controlled rotation/scale variation | [Epic PCG node reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-node-reference-in-unreal-engine) |
| Landscape material layers own texture scaling/rotation/panning | [Epic Landscape Paint Mode](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-paint-mode-in-unreal-engine) |
| Surface-gradient composition is a principled triplanar bump-map method | [Mikkelsen, JCGT 9(3)](https://jcgt.org/published/0009/03/04/) |
| Infinity Nikki presents an open-world styling fantasy visual target | [Infinity Nikki official site](https://infinitynikki.infoldgames.com/en/home) |

