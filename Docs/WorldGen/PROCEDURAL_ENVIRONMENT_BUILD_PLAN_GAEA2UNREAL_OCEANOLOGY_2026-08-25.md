# Melodia Procedural Environment Build Plan

## Scope and non-negotiables

This is the replacement plan for the Gaea/MeshTerrain/Oceanology pass. The
runtime substrate is **UE 5.8 MeshTerrain only**. No classic Landscape actor,
placeholder plane, or water mesh baked into terrain collision is part of P0.

The required authoring toolchain is **Gaea 2.2.3.2** at
`C:\Program Files\QuadSpinner\Gaea 2\Gaea.exe`. Gaea application version and
Gaea2Unreal plugin version are recorded separately; a graph exported by another
Gaea version does not satisfy the source gate.

The first production-shaped proof is one isolated **Liquid Cathedral** slice:
real terrain source -> Gaea erosion/material channels -> Gaea2Unreal import
when the plugin package is valid -> MeshTerrain partition -> Substrate surface
-> Oceanology water -> musical PCG dressing -> UDS sky -> clean PIE evidence.

The other three worlds remain named recipes until that slice is proven:

| World | Gaea identity | P0 role |
|---|---|---|
| Sakura Terrace | Directional Erosion | second water/shore and blossom route slice |
| Liquid Cathedral | Canyon River with Sea | integration anchor for Gaea2Unreal + Oceanology |
| Cadence Crystal Ridge | Creative - Stylized Mountain | dry ridge, crystal landmark, no Oceanology dependency |
| Fugue Grotto | Collapsed Gullies | dry route/grotto, flow and exclusion masks |

## Current evidence and blockers — 2026-08-25

| Area | Current evidence | Status |
|---|---|---|
| Real source | Yoshino ASTER OBJ, 12 km x 12 km, 129 x 129, SHA-256 `8042fe736e349f93399000222a5240de3ebe0e30500382101e30ad73fe0f534b` | ready |
| Gaea recipes | Four native example `.terrain` graphs from the installed Gaea 2.2.3.2 distribution parse and validate locally | reference-ready |
| Gaea MeshTerrain adapter | `Tools/WorldGen/ingest_gaea2unreal_mesh_terrain_handoff.py` converts Gaea-style 16-bit heightmap + JSON + masks into the existing MeshTerrain handoff contract; 33 x 33 smoke passed | adapter smoke pass; native export pending |
| High-resolution handoff | Four 1025 x 1025 16-bit packages, 2,097,152 triangles each, metric manifests | ready fallback |
| MeshTerrain bridge | Four isolated World Partition maps were saved through the MeshPartition bridge; classic Landscape was not created | ready with evidence caveat |
| Substrate instances | Four isolated MIs use the existing toon/Substrate master with world-aligned triplanar settings; apply report is all `OK` | ready for map validation |
| Gaea2Unreal | Upstream source `main` compiled 20/20 actions against UE 5.8; packaged 5.8 plugin is staged under `Plugins/GaeaUnrealTools` with `EngineVersion: 5.8.0` | port/build pass; runtime smoke pending |
| Oceanology | NextGen purchase is now confirmed, but the current project copy still lacks a complete descriptor/package; Oceanology work is deferred until the purchased NextGen package is installed | deferred |
| Runtime proof | Prior isolated PIE smoke was not accepted as clean final evidence; direct screenshot automation also crashed once | pending |
| Lookdev/webfront | No rejected or reference-only PNG is promotable | gated |

The current MeshTerrain report's direct component query is empty even though
the reflected MeshPartition bridge returned `OK` with the expected triangle
count, bounds, material, and saved map. That mismatch is a validation debt to
resolve with an asset-registry/partition query before calling the runtime gate
complete.

### Gaea2Unreal port result

The upstream QuadSpinner source was built with UE 5.8's `RunUAT BuildPlugin`,
while all terrain authoring remains pinned to Gaea 2.2.3.2:

`Saved/Audit/Gaea2Unreal-UE5.8-package-20260825/`

The compiled package was staged into:

`Plugins/GaeaUnrealTools/`

This proves the plugin can compile for the installed UE 5.8 toolchain. It does
not prove the importer is compatible with Melodia's runtime substrate. The
plugin's own importer is implemented around `ALandscape` and Landscape layer
imports, so its Create Landscape action is explicitly out of bounds for this
project. The accepted integration seam is:

```text
Gaea Unreal workflow output (height + JSON + masks)
        -> Gaea2Unreal 5.8 scale/metadata reader
        -> MeshTerrain handoff adapter
        -> MeshPartition build
```

The next Gaea task is a small adapter smoke test that consumes one native Gaea
heightmap/JSON export and writes a MeshTerrain handoff manifest. Until that
test exists, the staged plugin is a valid 5.8 build but not yet a validated
MeshTerrain import path.

The adapter now exists at
`Tools/WorldGen/ingest_gaea2unreal_mesh_terrain_handoff.py`. Its smoke output
is at `Saved/Audit/gaea2unreal_adapter_smoke_20260825/`; the fixture is clearly
labelled as DEM-derived and is not native Gaea evidence. The remaining proof is
to run the same adapter on an actual Gaea 2.2.3.2 Unreal-workflow export.

## Target architecture

```text
real DEM or authored source
        |
        v
Gaea graph + deterministic build settings
        |
        +--> height/displacement, flow, slope, curvature, albedo/sat,
        |    normal, roughness, water/shore masks
        |
        v
Gaea2Unreal 5.8 import adapter (only after package/build gate)
        |
        v
isolated UE handoff + manifest + hashes
        |
        +--> MeshTerrain partition (solid ground and collision)
        +--> Substrate MI (world-aligned terrain surface)
        +--> Oceanology binding (water surface, waves, shoreline effects)
        +--> PCG profile (musical dressing, mask-aware, partition-aware)
        +--> UDS sky and lighting
        |
        v
PIE / save-restart / performance / clean capture / lookdev review
```

Ownership is deliberately split:

- **Gaea** owns terrain authoring, erosion, and derived terrain channels.
- **Gaea2Unreal** owns the editor-side conversion/import when its complete
  5.8 package is restored. It does not own runtime terrain policy.
- **MeshTerrain** owns the solid world substrate and terrain collision.
- **Substrate** owns the terrain appearance and musical palette response.
- **Oceanology** owns water surface simulation, wave response, and water-only
  effects. It must not replace the MeshTerrain ground.
- **PCG** owns musical dressing and route-readable landmarks. It consumes
  imported masks and partition data; it must not generate a substitute plane.
- **UDS** owns the sky and broad lighting context.
- **Lookdev** owns clean beauty captures and webfront intake.

## Phase 0 — recover and prove the toolchain

Do this before changing the four maps or attempting another broad build.

### Gaea2Unreal recovery gate

1. Launch/use **Gaea 2.2.3.2** and keep the source-built 5.8 package at `Plugins/GaeaUnrealTools`; verify the
   editor loads it without an incompatible/missing-module warning.
2. Do not use its Landscape creation action. Run one export/import smoke test
   into a new scratch folder under
   `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/ToolchainSmoke/`.
3. Record plugin version, engine build, source graph hash, exported channel
   hashes, world scale, and import result in a manifest.
4. If native Gaea export is unavailable, keep using the existing deterministic
   DEM-derived handoff as a documented fallback.
   Native Gaea export remains `false`; P0 does not become AAA-complete by
   renaming the fallback.

The installed `Gaea.BuildManager.exe` is not currently an automation route: it
expects a missing `Gaea.BuildManager.dll`. Use the Gaea UI or a verified
Gaea2Unreal import path until a real native batch entry point is proven.

### Oceanology recovery gate

1. Restore the complete Oceanology plugin package, including its `.uplugin`
   descriptor and source or a supported prebuilt package. The current DLLs are
   evidence of a prior build, not a reproducible integration.
2. Confirm the descriptor's engine/build compatibility, module names, plugin
   dependencies, and content mount point.
3. Keep the project entry disabled until the descriptor and module load cleanly.
4. After load, inspect the actual registered actor/Blueprint classes and
   water-material assets through the UE asset registry. Do not invent class or
   parameter names from memory.
5. Create a read-only inventory report before placing any water actor. The
   report must include the plugin version, class paths, required textures/data
   assets, collision mode, world-partition behavior, and any runtime warnings.

Oceanology is intentionally out of this Gaea pass. Once the purchased NextGen
package is installed, restart this gate from its own descriptor and package;
do not use the archived legacy 5.7.0/UE 5.4 source as a substitute.

## Phase 1 — deterministic Gaea output contract

For each world, the source package must produce the same named channels and a
manifest. The Gaea graph is the creative authoring layer; the manifest is the
handoff authority.

Required fields:

```text
schema: melodia.gaea_output_manifest.v2
world_id
source_uri_or_path
source_sha256
terrain_graph_path
terrain_graph_sha256
gaea_version
gaea2unreal_version_or_fallback
engine_version
width_m / depth_m / vertical_range_m
resolution_x / resolution_y
channels: height, flow, slope, curvature, albedo, normal, roughness,
          water_mask, shore_mask
channel_paths_and_sha256
ue_import_scale_cm_per_m
target_runtime: MeshTerrain
classic_landscape_used: false
native_gaea_export_verified
```

The Gaea setup contracts remain the creative starting points. For Liquid
Cathedral, preserve the 5000 m x 3000 m basin and the recorded waterline value
of 36 m, but treat the meaning of that waterline as a coordinate contract to
verify during import rather than assuming it is already a UE world Z.

The existing package at
`Saved/Audit/gaea_setups_highres_20260825_1025/` is the fallback smoke-test
source. It is real ASTER-derived metric geometry, but it is not a native Gaea
export and must remain labelled that way.

## Phase 2 — MeshTerrain and Substrate integration

1. Import or stage the metric mesh only under
   `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/<World>/`.
2. Build a UE 5.8 MeshTerrain/MeshPartition partition. Never create a classic
   Landscape actor as an adapter for a plugin limitation.
3. Attach the isolated world MI. The current material parent is
   `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend`;
   the four applied MIs and their report are the current baseline.
4. Keep world-aligned triplanar sampling active for mesh terrain. Do not depend
   on painted Landscape layers or Landscape UVs.
5. Map Gaea channels as follows:

   | Gaea channel | UE consumer |
   |---|---|
   | height/displacement | MeshTerrain geometry/import data |
   | slope/curvature | Substrate blend and PCG density/biome masks |
   | flow | wetness, river/shore dressing, route readability |
   | albedo/sat | isolated MI texture input when native export is verified |
   | normal/roughness | Substrate surface detail |
   | water/shore mask | Oceanology placement/blend and PCG exclusion |

6. Resolve the direct-component-query mismatch through a deterministic
   partition/asset query. A bridge return string alone is not the final runtime
   proof.
7. Treat the master material's existing validation issues as separate P1
   material-health debt. Do not rewrite the shared master during this P0 slice;
   repair only isolated MIs and prove their compile/runtime use on the actual
   map surface.

## Phase 3 — Oceanology vertical slice

Liquid Cathedral is the only water integration target until it passes.

1. Place the verified Oceanology water actor/Blueprint in the isolated Liquid
   Cathedral map only.
2. Drive its placement from the Gaea water/shore mask and the verified metric
   waterline. Keep the water actor separate from MeshTerrain geometry and
   collision.
3. Bind the terrain shore blend to the water state through isolated MI values:
   shore wetness, water-palette alignment, foam/flow response, and any
   Oceanology-provided shoreline mask. Use actual exposed parameter names from
   the recovered plugin inventory.
4. Add a small Liquid Cathedral PCG exclusion volume/data layer so rocks,
   flowers, and route markers do not spawn below the water surface unless the
   profile explicitly calls for submerged dressing.
5. Verify in PIE: water surface appears, waves/animation update, shoreline
   meets terrain, collision is not duplicated, World Partition streaming does
   not orphan the actor, and there are no plugin Blueprint errors or ensures.
6. Save, close, reopen, and rerun the same map. A water actor that works only
   in the unsaved editor state does not pass P0.

After Liquid Cathedral passes, reuse the adapter for Sakura ponds/rivers. Do
not force Oceanology into Cadence or Fugue, which are dry-world slices.

## Phase 4 — musical PCG and presentation

PCG is downstream of geometry and water, not a replacement for either.

- Read MeshTerrain partition data and Gaea slope/flow/shore masks.
- Use a stable world seed plus the musical phrase/profile seed so regeneration
  is repeatable while different worlds remain distinct.
- Spawn biome dressing, route markers, blossom/rose-window accents, rocks, and
  hero landmarks only on valid ground.
- Record generated counts, rejected water points, seed, and profile hash.
- Add the installed UDS Blueprint after the terrain/water slice is stable; UDS
  is presentation context, not evidence that the world is built.
- Run traversal and landmark-grounding checks before any capture request.

## P0 gate matrix

| Gate | Pass condition | Current state |
|---|---|---|
| A — source provenance | real source, graph, extents, and hashes recorded | pass for ASTER/fallback; native Gaea pending |
| B — Gaea2Unreal build/import | complete 5.8 package loads and imports one graph/channel set | blocked by missing/incompatible package |
| C — MeshTerrain | partition builds, saves, streams, and is queryable; no Landscape | bridge saved; query/runtime proof pending |
| D — Substrate | isolated MI compiles and renders on actual MeshTerrain | parameter apply verified; map visual proof pending |
| E — Oceanology | complete plugin loads and Liquid Cathedral water survives PIE/save/reopen | blocked by missing descriptor/source |
| F — PCG | points read partition/masks and water exclusion is evidenced | pending |
| G — runtime | clean PIE logs, collision, streaming, performance, save/restart | pending |
| H — lookdev | standalone clean PNG is visually accepted | pending; webfront gated |

P0 is complete only when A-H pass for the Liquid Cathedral slice. Four
recipe contracts, source meshes, imported assets, material reports, or editor
screenshots are preparation evidence, not completion.

## Execution order after package recovery

1. Recover and prove the two plugin packages without touching production maps.
2. Run the Gaea2Unreal toolchain smoke test and publish its manifest.
3. Build Liquid Cathedral from native channels; retain the fallback package for
   comparison, not silent substitution.
4. Bind Oceanology water and prove PIE/save/reopen.
5. Attach the Substrate MI and mask-aware musical PCG; verify actual counts and
   grounding.
6. Add UDS, run the clean runtime/evidence gates, and hand the first valid PNG
   to lookdev with an absolute path and material/lighting state.
7. Fan out the proven adapters to Sakura, then dry Cadence and Fugue.
8. Promote nothing to the webfront until lookdev accepts the standalone render.

## Ownership and safety boundaries

- Source-only outputs and manifests: `Saved/Audit/`.
- UE staging: `/Game/_PROJECT/ResonantWorld/Offline/GaeaSetups/` only.
- Lookdev owns `RenderTests` maps and capture promotion.
- Gameplay/save lanes own gameplay maps and persistence state.
- Use one serialized UE writer and an explicit editor lease for live asset/map
  changes.
- Never repair a failed plugin build by editing shared production assets,
  renaming an engine version in a vendor descriptor, or hiding build warnings.
- No commit, push, or webfront ingestion is implied by this plan.

## Definition of AAA-ready

The system is ready for long-term creative world generation when a new world
can be produced by changing a source graph/profile and seed, while the same
validated contracts generate metric MeshTerrain geometry, Substrate channels,
optional Oceanology water, musical PCG dressing, UDS presentation, and
reproducible evidence. The first Liquid Cathedral pass must prove that whole
chain before the project calls the four-world system finalized.
