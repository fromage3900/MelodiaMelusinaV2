# Emerging 3D Toolchain — Trench Sweep VI

**Date:** 2026-08-31  
**Project:** Melodia Melusina / Unreal Engine 5.8 / Houdini 22  
**Status:** deep architecture correction + integration evidence pass  
**Rule:** one real Melodia benchmark per tool; native UE/Houdini baselines must be beaten, not ignored.

---

# 0. What changed in this pass

This pass is deliberately less about discovering another application and more about identifying the **second-order failure modes** that appear once Houdini 22, Unreal PCG, Biome Core, Mesh Terrain, Unreal MCP, MaterialX/OpenPBR, SpeedTree, JangaFX, and editor-side authoring start to touch the same data.

The strongest new conclusion is:

> Melodia should treat procedural worldbuilding as a compiler problem with explicit data contracts, not as a chain of interchangeable DCC exports.

The practical architecture is now:

```text
artist gesture / authored asset
        |
        v
UE PCG Editor Mode / Manual Editing
        |
        v
PCG semantic data
        |
        +------> Houdini HDA transform stage
        |             |
        |             v
        |       PCG-native semantic output
        |             |
        +-------------+
        |
        v
PCG / Biome Core / terminal GPU PCG
        |
        +--> SpeedTree assets
        +--> Niagara/material response
        +--> optional Mesh Terrain / Nanite representation
        |
        v
shipping Unreal assets/runtime
```

Houdini is not runtime authority. PCG is not botanical truth. SpeedTree is not world logic. Dash is not the world compiler. Unreal MCP is not a second uncontrolled editor writer.

---

# 1. VERIFIED: SideFX documentation currently disagrees about PCG plug-in packaging

Two current SideFX documentation pages give different packaging guidance:

- The Houdini Engine for Unreal introduction says that the plug-in came in separate `UE5.X` and `UE5.X-PCG` variants in Houdini 21.0, but because PCG is no longer Experimental in Unreal as of UE5.7, SideFX no longer provides a separate PCG-support plug-in.
- The dedicated PCG installation page still describes a separate `5.Z-PCG` plug-in directory and instructs users to copy that version.

Sources:

- https://www.sidefx.com/docs/houdini/unreal/intro.html
- https://www.sidefx.com/docs/houdini/unreal/pcg.html

## Consequence

Do **not** hard-code installation instructions in Melodia docs based on one SideFX page.

### New install gate

For the exact Houdini 22 production build and exact UE5.8 patch used on the workstation:

1. record Houdini build number;
2. record UE build/patch;
3. inspect the installed Houdini Unreal plug-in directories;
4. record whether the PCG-capable build is integrated or separate;
5. confirm the Houdini Digital Asset node appears in a PCG graph;
6. record the actual plug-in descriptor/version committed or installed;
7. only then write the local setup instructions.

**Decision:** vendor documentation inconsistency becomes a reproducibility test, not a reason to guess.

---

# 2. VERIFIED: UE5.8 PCG metadata domains should become part of the semantic contract

UE5.8 PCG distinguishes metadata domains including:

- `@Data` — one value for the data object;
- `@Points` — per-point metadata;
- `@Elements` — attribute-set elements.

Source:

- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview

UE5.8 also adds support for complex metadata values such as arrays, structures, sets, and maps.

Source:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes

## Melodia implication

`melodia.semantic-fields.v1` needs **domain** in addition to name/type/unit/space.

Recommended mapping:

```text
@Data
  melodia_schema_version
  melodia_source_asset
  melodia_source_revision
  melodia_generator_id
  melodia_seed
  melodia_space_contract

@Points
  melodia_moisture
  melodia_wind_exposure
  melodia_monolith_proximity
  melodia_molt_age
  melodia_filter_flow_strength
  melodia_filter_flow_dir_ws
  melodia_tension
  melodia_ecological_density
  melodia_asset_id

@Elements
  root asset lookup rows
  biome asset table rows
  material/profile lookup rows
```

### Compatibility rule

Even though UE5.8 supports arrays/structs/sets/maps, **do not put complex types into the cross-DCC v1 contract yet**.

The Houdini-PCG bridge must first prove preservation of:

- float;
- int;
- bool;
- string/name-like identifiers;
- point transform;
- explicitly-converted vector.

Only then should a `v2` experiment evaluate complex values.

This avoids an elegant Unreal-only schema becoming a fragile cross-tool schema.

---

# 3. VERIFIED: Houdini-PCG should be a CPU semantic stage, not interleaved with GPU PCG repeatedly

UE5.8 GPU PCG is Beta. Epic recommends grouping GPU nodes into compute graphs and minimizing CPU↔GPU transfers because uploads/downloads have cost.

Source:

- https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-with-gpu-processing-in-unreal-engine

Houdini Engine cooking is inherently an external/CPU authoring stage from PCG's point of view.

## Bad graph pattern

```text
CPU PCG
 -> GPU PCG
 -> download
 -> Houdini HDA
 -> upload
 -> GPU PCG
 -> download
 -> another HDA
 -> upload
```

This creates both performance and debugging complexity.

## Preferred graph pattern

```text
CPU PCG authoring / attributes
 -> one Houdini HDA semantic transform stage
 -> CPU validation / merge
 -> one terminal GPU compute block for dense point work/spawning
```

### Adoption gate

Any PCG graph that introduces Houdini must show:

- number of CPU→GPU transfers;
- number of GPU→CPU transfers;
- HDA cook count;
- HDA loop iteration count;
- total regeneration time.

No HDA is approved inside a dense runtime generation loop.

---

# 4. VERIFIED: Biome Core gives Melodia a strong asset-identity architecture

UE5.8 PCG Biome Core uses a local/global architecture and a root asset table. Generated points carry an `AssetID` that references properties stored in the table rather than duplicating full asset configuration on every point.

Sources:

- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-reference-guide-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-quick-start-guide-in-unreal-engine

## Melodia implication

This is a better fit for SpeedTree than making Houdini output direct Unreal asset references everywhere.

Preferred contract:

```text
Houdini HDA
 -> emits semantic points + stable asset-family intent
 -> PCG/Biome Core resolves AssetID
 -> root asset table owns SpeedTree mesh/render/collision configuration
```

### Why

- Houdini remains asset-library agnostic where possible;
- Unreal owns Unreal-specific rendering/collision references;
- SpeedTree assets remain canonical plant assets;
- semantic point data stays small and portable;
- one root table can retarget representations later.

## New benchmark

`LV_RND_P3_BiomeCore_AssetIDBridge`

Input:

- 3 SpeedTree species families;
- 4 semantic fields;
- one Houdini semantic transform;
- one Biome Core root asset table.

Pass if changing the root-table representation does **not** require changing the HDA.

---

# 5. VERIFIED: Biome Core runtime is a downstream consumer, not where Houdini should cook

Biome Core runtime can consume pre-generated graph data and use Runtime Hierarchical Generation and GPU nodes around the camera/player.

Source:

- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-reference-guide-in-unreal-engine

## Melodia rule

Houdini is authoring-time/compiler-time only.

```text
Houdini authoring pass
 -> bake/serialize semantic world data
 -> Biome Core runtime consumes it
 -> runtime GPU generation handles dense local detail
```

Do not design shipping gameplay that needs a Houdini Engine cook.

This provides a clean degradation path: if Houdini is unavailable on a build machine or artist machine, already-baked shipping content still works.

---

# 6. VERIFIED: Mesh Terrain PCG requires explicit read/write layer discipline

Epic's Mesh Terrain PCG guidance allows PCG to query and write mesh partition data, but warns against feedback loops. Epic recommends matching priority layer/sub-priority and avoiding inclusive queries by default.

Source:

- https://dev.epicgames.com/documentation/unreal-engine/pcg-and-mesh-terrain-in-unreal-engine

## Melodia terrain rule

Every Mesh Terrain graph must declare:

```yaml
reads:
  priority_layer:
  sub_priority:
  inclusive: false
writes:
  priority_layer:
  sub_priority:
```

### Proposed layer ownership

```text
L00_SOURCE        authored/Houdini base
L10_PRIMARY_FORM  folds / shelves / cavities
L20_EROSION       procedural erosion / smoothing
L30_MATERIAL      weights / wetness / biological masks
L40_ARTIST        final manual hero corrections
L90_DEBUG         temporary diagnostics only
```

No graph may read its own output layer inclusively without an explicit feedback-loop test.

---

# 7. VERIFIED: Unreal MCP has properties that make Melodia's existing policy layer more important, not less

Epic's UE5.8 Unreal MCP documentation states:

- Unreal MCP is Experimental;
- it embeds an MCP server inside the Unreal Editor process;
- it exposes editor functionality through tools;
- by default it accepts local-machine connections;
- it has no authentication layer;
- it is not designed for remote use;
- tool invocations are synchronized to the game thread and executed serially;
- APIs/data formats are incomplete and subject to change.

Sources:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- https://dev.epicgames.com/documentation/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine

## Repository finding

Melodia already has:

- `deploy/melodia_mcp_server.py`
- `Tools/mcp_policy.py`
- `specs/mcp_tool_policy.v1.json`

The existing policy is deny-by-default and distinguishes read/verify/mutate operations plus approval levels.

## Architectural conclusion

Do **not** replace the Melodia policy layer with direct unrestricted Unreal MCP exposure.

Preferred path:

```text
agent
 -> Melodia policy / allowlist
 -> exactly one editor mutation surface
 -> official Unreal MCP OR Monolith/T3D
 -> editor
```

Never:

```text
agent A -> Monolith write
agent B -> Unreal MCP write
agent C -> T3D injector
```

against the same editor state concurrently.

---

# 8. VERIFIED: Epic now ships PCG-specific MCP skills that are directly relevant

Epic documents dedicated PCG-oriented skills/toolsets for LLM work, including guidance for:

- PCG graph generation;
- Mesh Partition / Mesh Terrain;
- PCG Biome Core;
- mesh-surface instancing;
- shape grammar.

Source:

- https://dev.epicgames.com/documentation/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine

## Melodia implication

The first MCP benchmark should not be "spawn cubes because MCP can spawn cubes."

A better benchmark is:

1. load only the PCG toolset/skill context;
2. inspect one sandbox PCG graph;
3. add or modify one harmless debug branch;
4. inspect point attributes through Data View;
5. run a known validation/automation test;
6. compare the result to the equivalent Monolith/T3D operation.

### Safety rule

Day-one official MCP remains sandbox-only with:

- no production map writes;
- no deletion;
- no bulk rename;
- no plugin toggles;
- no source-control operations;
- no arbitrary shell bridge;
- full command transcript.

---

# 9. VERIFIED: MaterialX/OpenPBR is useful as a constrained interchange layer, not a replacement for Unreal master materials

UE5.8 supports MaterialX import through:

- direct `.mtlx` import;
- MaterialX referenced by USD;
- MaterialX embedded in USD stages.

In Substrate projects, MaterialX can be translated into native Substrate material nodes/functions, including OpenPBR surface mappings.

Sources:

- https://dev.epicgames.com/documentation/unreal-engine/importing-materialx-files-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/InterchangeCommon/EInterchangeMaterialXShaders

Houdini/Solaris supports MaterialX through USD/UsdMaterialX and Karma workflows.

Source:

- https://www.sidefx.com/docs/houdini/solaris/materialx

## Important boundary

This is strongest as a **look-transfer contract**, not as a guarantee that arbitrary production shader graphs round-trip losslessly.

### First benchmark

`MEL_Petal_OpenPBR_Canary`

Author one restrained material with:

- base color;
- roughness;
- metallic = 0;
- normal;
- opacity/transmission variant if needed;
- one emissive parameter if supported cleanly.

Path:

```text
Houdini MaterialX/OpenPBR
 -> .mtlx or USD MaterialX
 -> UE5.8 Interchange import
 -> native Substrate material
```

Measure:

- parameter preservation;
- texture path resolution;
- color-space handling;
- normal orientation;
- roughness parity;
- shader compile cost;
- reimport behavior.

### Rule

Game-specific dynamic logic remains in project-owned Unreal master materials unless a narrower interchange subset proves reliable.

---

# 10. VERIFIED: UE5.8 USD asset import is stronger than level import

UE5.8 release notes state USD through Interchange is production-ready for **asset import** and Experimental for **level import**.

Source:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes

## Melodia rule

Use USD for:

- asset packaging;
- variant/reference exchange;
- geometry/lookdev handoff;
- controlled import pipelines.

Do not make a USD stage the production world-authority layer for Melodia's shipping chapters yet.

World Partition + Unreal assets remain shipping authority.

---

# 11. VERIFIED: UE5.8 PCG Manual Editing makes native Unreal a much stronger Dash comparator

UE5.8 adds non-destructive Manual Editing/Data Overrides for PCG and a first-generation PCG Editor Mode with spline, surface, paint, and volume tools.

Sources:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- https://dev.epicgames.com/documentation/unreal-engine/pcg-editor-mode-in-unreal-engine

## Updated Dash rule

Dash must beat:

```text
PCG Editor Mode + Manual Editing + native placement tools
```

not merely drag-and-drop actor placement.

If native PCG artist tooling gets within ~10–15% of Dash's speed while remaining easier to version, automate, and maintain, prefer native UE.

The threshold is a project proposal, not a vendor fact.

---

# 12. VERIFIED: Nanite Foliage / Assemblies are representation R&D, not authoring truth

UE5.8 Nanite Foliage is Experimental. Nanite Assemblies can micro-instance repeated geometry and work with static or skeletal mesh assets.

Source:

- https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-foliage

## Melodia role

SpeedTree remains botanical authoring truth.

Nanite Foliage / Assemblies may become a **representation target** for selected hero ecology if they demonstrate:

- better dense-canopy quality;
- acceptable wind/deformation behavior;
- lower streaming/disk burden;
- acceptable build times;
- stable packaging.

Do not convert the whole vegetation library during the first canary.

---

# 13. NEW CROSS-SYSTEM FAILURE MODE: semantic meaning can survive while data representation silently changes

Potential example:

```text
Houdini vector
 -> PCG vector attribute
 -> GPU HLSL
 -> Niagara vector
```

The field name may remain `melodia_filter_flow_dir_ws` while one stage silently changes:

- axis convention;
- normalization;
- unit scale;
- metadata domain;
- local/world space;
- precision.

## New invariant

Every semantic-field consumer must be able to answer:

```text
name
meaning
unit
space
domain
normalization rule
valid range
source revision
```

If any answer is implicit, the field is not production-ready.

---

# 14. NEW PIPELINE RULE: authoring dependency != shipping dependency

Every tool must be classified on two independent axes.

## Authoring dependency

Does an artist need the tool to regenerate/edit the source?

## Shipping dependency

Does the packaged game need the tool/plugin/runtime to render or function?

Preferred Melodia pattern:

```text
Houdini / Copernicus / IlluGen / Toolbag / Cascadeur
  = authoring dependency possible
  = shipping dependency NO

SpeedTree-authored assets
  = authoring dependency possible
  = shipping dependency NO beyond normal UE assets/shaders

UE PCG / Niagara / native materials
  = shipping-native systems when used at runtime
```

Any external tool that becomes a shipping runtime dependency needs a much higher adoption bar.

---

# 15. NEW BENCHMARK ORDER — corrected after this research

The previous tool-first order is now superseded by a **contract-first** order.

## Tier 0 — establish the compiler contract

1. H22/UE5.8 Houdini-PCG installation canary, including vendor-doc discrepancy.
2. Scalar semantic round-trip.
3. Vector conversion canary.
4. PCG domain mapping (`@Data`, `@Points`, `@Elements`).
5. Source-control/cook/bake/reopen test.

## Tier 1 — prove world orchestration

6. P3 spline → HDA semantic field → PCG.
7. Biome Core AssetID → SpeedTree representation.
8. Manual Editing hero exceptions.
9. GPU terminal detail pass.
10. World Partition / runtime generation performance capture.

## Tier 2 — compare external accelerators

11. IlluGen vs H22 Copernicus for Sea Above/P3 texture motion.
12. Dash vs PCG Editor Mode + Manual Editing.
13. Cascadeur Mara Anchor round-trip.
14. Toolbag hero bake/lookdev QA.
15. LiquiGen / EmberGen shot-specific bake workflows.

## Tier 3 — experimental engine representations

16. Mesh Terrain folded patch.
17. Nanite Foliage/Assemblies canary.
18. PVE package canary.

## Tier 4 — frontier/watch

19. RTX/neural materials.
20. Procedura.
21. Magpie.

This sequencing reduces the chance of selecting a third-party tool to solve a problem the native compiler stack already solves.

---

# 16. Promotion gates that now apply to every procedural tool

A tool may only move to ADOPT if all relevant gates are green:

### Visual gate
- visibly better Melodia result;
- fixed cameras / same brief;
- not judged on vendor demo content.

### Time gate
- setup time recorded;
- hands-on time recorded;
- comparator workflow recorded;
- repeat run performed after first-learning run where practical.

### Reproducibility gate
- version/build recorded;
- license state recorded;
- seed/input manifest recorded;
- source graph/HDA/settings preserved where license allows;
- second-machine or clean-reopen test where practical.

### Data gate
- semantic field names/types/domains/units recorded;
- coordinate conversions explicit;
- no silent attribute loss.

### Source-control gate
- temporary/generated outputs identified;
- deterministic names;
- no large mystery binary churn;
- bake/freeze behavior documented.

### Runtime gate
- shipping dependency identified;
- GPU/CPU cost measured if runtime;
- package/cook attempt for Experimental engine features.

### Maintainability gate
- owner declared;
- rollback path declared;
- no duplicate authority created.

---

# 17. Priority decisions after Trench Sweep VI

| Lane | Decision now | Reason |
| --- | --- | --- |
| SpeedTree | CORE | botanical authoring truth |
| Houdini 22 + Copernicus | CORE / ACTIVE | already live; increasingly central |
| Houdini-PCG | **TIER-0 VALIDATE** | could unify two core systems |
| UE PCG Manual Editing / Editor Mode | NATIVE BASELINE | every dressing tool must beat it |
| PCG Biome Core | HIGH-PRIORITY R&D | strong fit for semantic ecology + SpeedTree |
| IlluGen | TEST | must beat H22 Copernicus on one real VFX texture family |
| Cascadeur | TEST | clear Mara benchmark |
| Unreal MCP | TEST BEHIND POLICY | useful, but Experimental and unauthenticated locally |
| Dash | OPTIONAL TEST | now has a stronger native comparator |
| Mesh Terrain | R&D | powerful but Experimental and feedback-sensitive |
| Nanite Foliage | R&D REPRESENTATION | not an authoring replacement |
| PVE | WATCH / PACKAGE-CANARY | secondary growth only |
| MaterialX/OpenPBR | TIER-A INTERCHANGE TEST | useful constrained look transfer |
| USD | ASSET INTERCHANGE | do not make world authority |
| RTX/neural | WATCH | branch-heavy/runtime-specific |
| Procedura | WATCH | architecture inspiration until concrete fit proven |
| Magpie | WATCH / RESEARCH ONLY | simulation-vs-visual-truth research signal |

---

# 18. Immediate actions

- [ ] Create a dedicated Houdini-PCG validation issue.
- [ ] Add PCG metadata domain mapping to the semantic-field contract.
- [ ] Add vendor-documentation discrepancy to the H22 install checklist.
- [ ] Add a CPU/GPU transfer count to every PCG benchmark result.
- [ ] Add authoring-dependency vs shipping-dependency fields to every tool result.
- [ ] Add MaterialX/OpenPBR canary after semantic bridge Tier 0.
- [ ] Update Issue #29 so Houdini-PCG and native UE baselines precede third-party tools.
- [ ] Keep Issue #36 focused on consolidation/discovery and missing board recovery.

---

# 19. Primary evidence sources

SideFX:

- https://www.sidefx.com/docs/houdini/unreal/intro.html
- https://www.sidefx.com/docs/houdini/unreal/pcg.html
- https://www.sidefx.com/docs/houdini/unreal/pcg/overview.html
- https://www.sidefx.com/docs/houdini/unreal/pcg/workflows.html
- https://www.sidefx.com/docs/houdini/news/22/engine.html
- https://www.sidefx.com/docs/houdini/unreal/copernicus.html
- https://www.sidefx.com/docs/houdini/solaris/materialx

Epic:

- https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-overview
- https://dev.epicgames.com/documentation/en-us/unreal-engine/using-pcg-with-gpu-processing-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/pcg-editor-mode-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/procedural-content-generation-pcg-biome-core-and-sample-plugins-reference-guide-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/pcg-and-mesh-terrain-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor
- https://dev.epicgames.com/documentation/unreal-engine/working-with-pcg-and-llms-using-unreal-mcp-in-unreal-engine
- https://dev.epicgames.com/documentation/unreal-engine/importing-materialx-files-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-foliage

---

## Bottom line

The next major Melodia toolchain win is probably **not another application**. It is proving that one semantic world description can move predictably through UE PCG, Houdini, Biome Core, SpeedTree, Niagara/materials, and experimental representation layers without changing meaning or creating a second runtime authority.
