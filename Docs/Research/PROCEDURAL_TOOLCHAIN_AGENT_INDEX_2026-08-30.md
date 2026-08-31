# Procedural Toolchain Agent Index — Houdini / Copernicus / Dash / Magpie

**Date:** 2026-08-30  
**Purpose:** stable discovery entry point for agents working on Melodia procedural-world, rendering, and emerging-toolchain R&D.  
**Read this file first when a task mentions:** Houdini, Copernicus, Dash, Magpie, IlluGen, LiquiGen, EmberGen, Cascadeur, Gaea, World Creator, Toolbag, Unreal MCP, Mesh Terrain, Procedural Vegetation, RTX Kit, neural shaders/materials, Procedura, FluidNinja, VectorayGen, GeoGen, Voxel Plugin, or toolchain integration spikes.

---

## Why this index exists

The research corpus is split across two places:

1. **current `main`** — active Copernicus implementation, live execution reports, dress-bake handoffs, and current production evaluation material;
2. **branch `docs/2026-08-29-character-p1-p2-canon-audit`** — the large Houdini / emerging-toolchain research corpus and Aug 31 spike plans.

As of 2026-08-30, `Docs/Houdini/` and the newer emerging-toolchain research files are **not present on `main`**. Agents searching only the default branch will therefore miss them. This is a branch-discoverability problem, not evidence that the research was never written.

Do not recreate research just because it is absent from `main`. Retrieve the branch source first, then reconcile it against current implementation.

---

# 1. Current implementation on `main`

These are the most important current sources when work has already begun.

## Copernicus / Houdini implementation

- `Tools/Houdini/copernicus/README.md`
- `Tools/Houdini/copernicus/copernicus_dress_bake.py`
- `Tools/Houdini/copernicus/copernicus_petal_variants.py`
- `Tools/Houdini/copernicus/copernicus_fabric_sheen.py`
- `Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py`
- `Tools/Houdini/copernicus/melodia_dress_cop.hip.template.md`
- `Tools/Houdini/copernicus/hda_melodia_lookdev_spec.json`

## Current reports / handoffs

- `Docs/Plans/COPERNICUS_AAA_LIVE_REPORT_2026-08-31.md`
- `Docs/Art/DRESS_HOUDINI_SETUP_REVIEW_2026-08-30.md`
- `Docs/Handoffs/SESSION_HANDOFF_DRESS_BAKE_2026-08-30.md`
- `Docs/TOOL_EVALUATION_SESSION_2026-08-30.md`

**Rule:** current implementation evidence outranks older speculative setup instructions where they conflict.

---

# 2. Stranded Houdini corpus

**Source branch:** `docs/2026-08-29-character-p1-p2-canon-audit`

The branch contains a `Docs/Houdini/` directory that is absent from `main`.

Read these for the intended Houdini architecture and Melodia-specific procedural systems:

- `Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md`
  - authoritative technical split between Houdini authoring and Unreal runtime;
  - HDA contracts, KineFX, World Partition/Data Layers, PCG, attributes, baking and representation ladder.
- `Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md`
  - concrete Mara + P0/P1/P2/P3 Houdini execution plan;
  - character utilities, world HDAs, P1 seams, P2 molt families, P3 mouth/filter fields.
- `Docs/Houdini/LATE_MONOLITH_VISUAL_ESCALATION_BIBLE_2026-08-29.md`
  - late-game reality-scale anatomy systems and reusable Monolith HDA families.
- `Docs/Houdini/MELODIA_WORLD_COMPILER_TOMORROW_SCAFFOLD_2026-08-30.md`
  - world-compiler scaffolding and execution framing.
- `Docs/Houdini/HOUDINI_LICENSING_CORE_FX_INDIE_TRANSITION_RESEARCH_2026-08-30.md`
  - licensing / edition transition constraints and production implications.

### Local retrieval

```bash
git fetch origin docs/2026-08-29-character-p1-p2-canon-audit

git show origin/docs/2026-08-29-character-p1-p2-canon-audit:Docs/Houdini/MELUSINA_HOUDINI_UE58_TECHNICAL_RESEARCH_2026-08-30.md
```

To inspect the whole stranded corpus without switching branches:

```bash
git ls-tree -r --name-only origin/docs/2026-08-29-character-p1-p2-canon-audit -- Docs/Houdini Docs/Research
```

---

# 3. Emerging toolchain master research — where Dash and Magpie actually live

Dash and Magpie were **not authored as standalone top-level docs**. Their primary research lives inside the broader emerging-toolchain documents on the same branch.

## Primary catalog

`Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md`

Contains the original role / integration-boundary / adoption-gate survey for:

- SpeedTree
- Houdini 22
- Copernicus
- IlluGen
- LiquiGen
- EmberGen
- Cascadeur
- **Polygonflow Dash**
- Gaea
- World Creator
- Marmoset Toolbag
- UE5.8 Mesh Terrain + PCG
- UE5.8 Procedural Vegetation Editor
- Unreal MCP
- NVIDIA RTX Kit
- neural shaders / neural materials
- Procedura
- **Magpie / generative realtime world rendering**

### Dash finding

Dash is framed as an Unreal-native **final human environment-art pass** that complements rather than replaces Houdini or PCG:

```text
Houdini = procedural systems
PCG     = scalable authored distribution
Dash    = fast final human composition pass
```

The benchmark is a short P3 Filter-Flow Biome dressing pass: rocks/logs/debris, cable/vine/road assembly, physics placement, and camera-critical composition. Adopt only if it visibly improves the authored read faster than equivalent manual UE work while leaving normal UE content behind.

### Magpie finding

Magpie is **research-only**, not a production dependency. The useful conceptual takeaway is the future separation of:

```text
gameplay / simulation authority
        !=
visual frame representation
```

This is relevant to Melodia's existing split between world truth and perceived/presentation truth, but current determinism, latency, temporal consistency, art direction, QA and platform constraints make it unsuitable for production adoption.

---

# 4. Integration spike plan

`Docs/Research/TOOLCHAIN_INTEGRATION_SPIKE_PLAN_2026-08-31.md`

This is the execution plan for testing the research against real Melodia tasks.

Core rule:

> **Does this let us produce a visibly better Melodia result per hour than the current workflow?**

Key benchmarks:

- **A — P2 Molt Material Family:** Copernicus / IlluGen / Toolbag / Substance / Houdini SOP-COP interoperability.
- **B — P3 Filter-Flow Biome:** SpeedTree / Houdini semantic masks / UE PCG / Niagara / **Dash**.
- **C — Mara Anchor Motion:** Cascadeur / UE retarget / Houdini deformation audit.
- **D — Impossible Terrain Patch:** Houdini / UE5.8 Mesh Terrain / Gaea / World Creator.
- **E — Sea Above Hero Liquid/Atmosphere Shot:** LiquiGen / EmberGen / IlluGen / Niagara.

Priority tiers in the plan:

```text
Tier A: Copernicus, IlluGen, Cascadeur, Unreal MCP, Mesh Terrain + PCG
Tier B: Dash, LiquiGen, EmberGen, Toolbag
Tier C: Gaea, World Creator, Procedural Vegetation Editor
Tier D: RTX/neural R&D, Procedura, Magpie
```

If Copernicus work is already in progress, do **not** restart Test 01 from zero. Compare current implementation against the original adoption gate and record evidence.

---

# 5. Deeper trench sweeps

Also on `docs/2026-08-29-character-p1-p2-canon-audit`:

- `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_02_2026-08-30.md`
  - FluidNinja LIVE-2
  - Advanced Environment Interaction
  - MetaTailor
  - Chaos Outfit Assets
  - Rokoko Vision -> Cascadeur -> Unreal
  - GeoGen
  - VectorayGen
  - Voxel Plugin 2
  - Errant Worlds / Biomes
  - RealityScan
  - SuperSplat / Gaussian workflows
  - InstaMAT / Material Maker / ArmorPaint
  - Style3D and other specialized candidates.
- `Docs/Research/EMERGING_3D_TOOLCHAIN_TRENCH_SWEEP_03_2026-08-30.md`
  - further niche / frontier tool research.
- `Docs/Research/TOOLCHAIN_TRENCH_SWEEP_02_TEST_PLAN_2026-08-31.md`
  - production-shaped comparison plan for trench-sweep candidates.
- `Docs/Research/TOOLCHAIN_KICKOFF_2026-08-30_CASCADEUR_ILLUGEN_BLENDER_RHYTHM.md`
  - practical kickoff around Cascadeur / IlluGen / Blender rhythm work.
- `Docs/Research/INFINITY_NIKKI_UE5_TRANSLATION_FOR_MELODIA_2026-08-30.md`
  - production-principle comparison used to judge tool adoption.
- `Docs/Research/UE58_EXPLORATION_WORLD_BUILDING_RESEARCH_2026-08-29.md`
  - native UE5.8 systems that external tools must complement rather than duplicate.

---

# 6. Visual / image-board status

## Confirmed committed boards on the stranded branch

`Docs/Art/Images/` contains:

- `sea_above_level_stack_16x9.svg`
- `sea_above_melusina_character_board_v0.svg`
- `sea_above_shader_breakdown.svg`
- `sea_above_shorelistener_concept_board_v1.svg`
- `shorewake_shader_flow_sea_above_p0_visual_target_2026-08-29.svg`
- `CharacterConcepts/`

These are useful visual references for Sea Above / character / shader work, but they are **not dedicated Dash / Magpie / Houdini tool-research boards**.

## Not found in Git

At audit time:

- no `Docs/Houdini/Images/` directory exists on the stranded branch;
- no `Docs/Research/Images/` directory exists on the stranded branch;
- no dedicated Dash/Magpie image-board file was found on current `main`;
- current-main keyword search for `Magpie` had no result before this index existed.

Therefore any dedicated Houdini/Dash/Magpie research boards remembered from chat should be treated as **chat/local artifacts until their source files are recovered and committed**. Do not fabricate paths for them.

Recommended canonical destination when recovered:

```text
Docs/Research/Images/Toolchain/
  houdini_copernicus_melodia_pipeline_*.webp|png|svg
  dash_environment_artpass_*.webp|png|svg
  magpie_simulation_vs_representation_*.webp|png|svg
  emerging_toolchain_matrix_*.webp|png|svg
```

---

# 7. Agent retrieval rules

When an agent receives a Houdini / Copernicus / Dash / Magpie task:

1. Read **this index first**.
2. Inspect current `main` implementation before proposing new systems.
3. Fetch the stranded branch research if the task concerns architecture, original adoption gates, or planned benchmarks.
4. Never infer that a missing default-branch file was deleted or never written until the branch corpus is checked.
5. Never recreate a tool pipeline that has already landed under `Tools/Houdini/copernicus/`.
6. Treat current live execution evidence as newer than speculative research where they disagree.
7. Preserve ownership boundaries:
   - Houdini = procedural geometry / fields / offline simulation / authoring;
   - Copernicus = geometry-aware textures and masks;
   - SpeedTree = authored botany;
   - Dash = optional Unreal art-pass accelerator;
   - Unreal = runtime state / streaming / interaction / rhythm / shipping presentation;
   - Magpie = research signal only, not shipping runtime architecture.
8. For visual references, use only paths proven to exist. If a remembered board is not in Git, report it as unrecovered rather than inventing a filename.

---

# 8. Consolidation recommendation

Do **not** blindly merge the entire old canon-audit branch just to recover research. It contains broader chapter/canon work and may have diverged from current production.

Preferred cleanup:

1. selectively migrate the still-authoritative Houdini/research markdown files into current `main`;
2. keep this index as the permanent discovery layer;
3. recover chat/local toolchain image boards into `Docs/Research/Images/Toolchain/`;
4. add a small agent-start pointer to this index when the next safe `AGENTS.md` consolidation pass occurs;
5. update individual docs with `Superseded by` / `Implementation status` notes instead of deleting historical research.

Until that migration is complete, this file is the stable bridge between current implementation and the stranded research corpus.
