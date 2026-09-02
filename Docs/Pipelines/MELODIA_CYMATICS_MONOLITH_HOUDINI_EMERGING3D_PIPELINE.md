# Melodia: Cymatics, Monolith Architecture, Houdini Pipelines, and Emerging 3D Toolchains
**Document Version:** 1.0.0
**Date:** 2026-09-01
**Target Engine:** Unreal Engine 5.8.0 | Houdini 22.0.368 | Blender 5.2 LTS | C++20 | Python 3.11
**Classification:** Canonical Architecture & Pipeline SSOT

---

## 1. Executive Architecture & Core Governance

This document establishes the canonical cross-system engineering standards for:
1. **Cymatics & Audio-Reactive Presentation:** Mathematical formulations, C++ runtime subsystems, single-writer contracts, and Copernicus PBR texture synthesis.
2. **Monolith MCP Automation Architecture:** High-throughput JSON-RPC server on port `9316`, 18+ modular C++ subsystems, 1,400+ editor actions, and offline SQLite FTS5 reflection intelligence.
3. **Houdini Procedural Authoring Pipelines:** KineFX biharmonic skinning, World Partition streaming proxy isolation, data layer tagging (`unreal_data_layer_*`), and offline simulation baking (VAT/Chaos/VDB).
4. **Emerging 3D Toolchains & Rendering Frontiers:** SpeedTree botanical authority, 3D Gaussian Splatting (3DGS/4DGS) reference ingest, FluidNinja simulation fields, and the unified Melodia World Field Bus.

---

## 2. Cymatics & Audio-Reactive System Architecture

### 2.1 Mathematical & Physical Foundations

Cymatics transforms acoustic resonance into deterministic, physical geometric deformations and procedural surface textures.

#### Chladni 2D Standing Wave Formulation
For a 2D vibrating plate with boundary $[0, 1] \times [0, 1]$, displacement $Z(u, v)$ is solved via Helmholtz eigenvalue equations:

$$Z(u, v) = a \cos(n \pi u) \cos(m \pi v) - b \cos(m \pi u) \cos(n \pi v)$$

- **Mode Pairs $(n, m)$:** Integer harmonic frequencies mapped dynamically to melodic registers:
  - Base low registers: $(1, 2), (2, 3)$
  - Harmonic chords: $(3, 5), (4, 4)$
  - High-frequency resonance: $(5, 7), (6, 8)$
- **Interference Weights $(a, b)$:** Balance directional nodal lines, transforming orthogonal lattices into hyperbolic interference curves.

#### Circular Bessel Boundary Conditions
For circular structures (e.g. Bell mechanisms, crown motifs):

$$Z_{n,m}(r, \theta) = J_n\left(\alpha_{n,m} \frac{r}{R}\right) \cos(n \theta + \phi)$$

#### Multi-Scale Domain Warping (fBm)
To eliminate mechanical grid artifacts, UV coordinates are warped using fractional Brownian motion:

$$u' = u + \alpha \sum_{o=0}^{O-1} 2^{-o} \text{Noise}(2^o u, 2^o v)$$
$$v' = v + \alpha \sum_{o=0}^{O-1} 2^{-o} \text{Noise}(2^o u + 5.2, 2^o v + 1.3)$$

---

### 2.2 C++ Runtime Subsystem: `UMelodiaCymaticsSubsystem`

The architecture enforces a strict **Single-Writer Audio Contract**:
- **Sole Writer:** `UMelodiaAudioReactivePresentationSubsystem` writes dynamic audio telemetry (`BeatPulse`, `BassIntensity`, `BeatPhase`, `SectionEnergy`) to `MPC_Melodia_Palette`.
- **Read-Only Consumer:** `UMelodiaCymaticsSubsystem` (`UGameInstanceSubsystem`, `FTSTicker`) samples parameters via `GetParameterCollectionInstance` and evaluates standing waves without allocating heap memory per frame.
- **Contract Guard:** `IsReadOnlyByContract() const { return true; }` guarantees zero uncoordinated palette mutations.

```text
[Melodia Music Clock]
         │
         ▼
[UMelodiaAudioReactivePresentationSubsystem] (Sole Writer)
         │ writes BeatPulse, BassIntensity
         ▼
[Material Parameter Collection: MPC_Melodia_Palette]
         │ reads (GetParameterCollectionInstance)
         ▼
[UMelodiaCymaticsSubsystem] (Read-Only Consumer)
         │ publishes
         ▼
[Melodia World Field Bus: WorldField.Resonance / WorldField.Tension]
         ├──► Water & Landscape WPO Displacement
         ├──► Niagara Particle Grid Advection
         └──► Character Wardrobe Emission Shaders
```

---

### 2.3 Procedural Copernicus Texture Generation Pipeline

Automated by `Tools/Houdini/copernicus_cymatic_parallax.py`, the offline pipeline generates 9 synchronized PBR maps across 29 variants:
- **BaseColor:** Albedo with nodal line pigment deposition.
- **Normal:** 3x3 Sobel operator gradient field derived from the heightfield.
- **Roughness:** Inverse wave amplitude with high-frequency micro-roughness.
- **Metallic:** Selective antinodal conductive crystallization.
- **Height:** Combined Chladni interference field and multi-octave fBm.
- **ORM:** Packed Ambient Occlusion (R), Roughness (G), and Metallic (B).
- **Emissive:** Nodal boundary luminescence pulsed with music phase.
- **Iridescence:** Thin-film optical interference phase maps.
- **Opacity:** Alpha mask for organic membrane cutouts.

---

## 3. Monolith MCP Architecture & Automation Protocol

### 3.1 High-Throughput HTTP/JSON-RPC Bridge

Monolith embeds a native C++ HTTP server listening on port `9316` that translates Model Context Protocol (MCP) tool calls into Unreal Editor operations on the game thread.

```text
+─────────────────────────────────────────────────────────────+
|                    External Agent / Client                  |
+──────────────────────────────┬──────────────────────────────+
                               │ HTTP POST / JSON-RPC 2.0 (:9316)
                               ▼
+─────────────────────────────────────────────────────────────+
|                      FMonolithHttpServer                    |
|   - Non-blocking socket listener with backoff & retry       |
|   - Task dispatch via FMonolithTickScheduler                |
+──────────────────────────────┬──────────────────────────────+
                               │
                               ▼
+─────────────────────────────────────────────────────────────+
|                    FMonolithToolRegistry                    |
|            18 Modules / 1,400+ Granular Actions             |
+──────┬───────────────────────┼───────────────────────┬──────+
       │                       │                       │
       ▼                       ▼                       ▼
 [MonolithBlueprint]     [MonolithMaterial]      [MonolithNiagara]
 - Graph CRUD            - Substrate BSDF Nodes  - Emitter Wiring
 - Node Linking          - Expression AST        - Sim Stages
 - CDO Inspection        - Shader Compilation    - HLSL Functions
```

### 3.2 Modular Subsystem Index

1. **`MonolithCore`:** Server lifecycle, request dispatch, schema reflection, session token validation, and `Monolith.Restart`.
2. **`MonolithBlueprint` (120+ Actions):** AST mutation, node linking (`K2Node_CallFunction`, `K2Node_EnhancedInputAction`), variable CRUD, and graph compilation.
3. **`MonolithMaterial` (60+ Actions):** Material graph generation, expression node wiring (`LandscapeLayerBlend`, `TextureSampleParameter2D`), Substrate trees, and shader recompilation.
4. **`MonolithAnimation` (150+ Actions):** Control Rig graph manipulation, AnimBlueprint state machine generation, BlendSpace1D assembly, and notify injection.
5. **`MonolithNiagara` (120+ Actions):** System/emitter lifecycle, dynamic HLSL module compilation, simulation stage scheduling, and render module assignment.
6. **`MonolithReflectionIntel` (28 Actions):** Zero-LLM-cost reflection analysis (`decision_query`, `risk_query`, `cppreflect_query`, `network_query`, `pipeline_query`).
7. **`monolith_query.exe`:** Standalone C++ binary in `Plugins/Monolith/Binaries/` for instant SQLite FTS5 querying of `EngineSource.db` and `ProjectIndex.db` without starting the editor.

---

## 4. Houdini Procedural Pipelines & HDA Architecture

### 4.1 Production Governance

> **"Houdini authors the impossible evidence; Unreal decides when the player experiences it."**

All Houdini graphs must compile into deterministic, versioned `.uasset` static meshes, skeletal meshes, texture sets, or Chaos geometry collections. Live HDA cooking in shipping builds is strictly prohibited.

---

### 4.2 KineFX Character & Rigging Pipeline

1. **Skeleton Ingest:** Ingests base skeletons via `UnrealToKineFX`. Skeletons are represented as SOP point hierarchies (`P`, `rot`, `transform`, `name`, `parent`).
2. **Biharmonic Bone Capture:** Solves geodesic biharmonic weights to maintain joint volume during extreme rotational flexion.
3. **Automated Stress-Testing Suite:** Evaluates 9 canonical poses (crouch, shoulder shrug, elbow bend, high-knee step, wrist flexion) and exports a deformation strain heatmap (`f@max_stretch`) to detect clipping before mesh export.

---

### 4.3 World Partition & Landscape Streaming Proxy Workflow

To prevent source control conflicts across multi-kilometer levels:
- **Proxy Isolation:** Load only active World Partition cells before invoking HDA generation. HDAs read local heightfield tiles via `NodeSync` and output modified tiles without dirtying global landscape layers.
- **Data Layer Tagging:** HDAs assign primitives to Unreal Data Layers using primitive group conventions:
  ```text
  unreal_data_layer_P1_BaseLandscape
  unreal_data_layer_P1_FoldedFabric_Hero
  unreal_data_layer_P1_CinematicReveal
  ```
- **Material Parameter Injection:** Surface age and weathering attributes are assigned directly to primitive attributes:
  ```text
  s@unreal_material = "/Game/Materials/M_MoltMaster_Inst";
  f@unreal_material_parameter_LayerAge = f@melodia_age;
  f@unreal_material_parameter_Tension = f@melodia_tension;
  ```

---

### 4.4 Offline Simulation to Runtime Representation

| Simulation Domain | Houdini Offline Tool | Output Format / UE5.8 Target | Runtime Representation |
| :--- | :--- | :--- | :--- |
| **Continental Cloth** | Vellum XPBD solver | Vertex Animation Textures (VAT) / Skeletal LODs | Nanite Static Mesh + WPO Material |
| **Impossible Water** | FLIP Liquid Solver | Flow-map Vector Fields / Flipbooks | Oceanology + Niagara Vector Field Advection |
| **Atmospheric Volumes**| Sparse Pyro Solver | 3D Texture Volumes / OpenVDB / Flipbooks | Heterogeneous Volumes / Niagara Grid 3D |
| **Monolith Fractures** | RBD Bullet Solver | Clustered `unreal_gc_piece` Attributes | Chaos Geometry Collections (Pre-fractured) |

---

## 5. Emerging 3D Toolchains & Realtime Rendering Frontiers

### 5.1 Toolchain Classification & Ownership

```text
=========================================================================================
TIER 1: PRESENT (Core Engine Authority - Do NOT duplicate or rebuild)
-----------------------------------------------------------------------------------------
- SpeedTree 10.x        : Canonical botanical architecture & wind authority
- Houdini 22 / HDA      : Procedural geometry, ecology, biharmonic rigging, offline sim
- Copernicus (Houdini)  : Procedural PBR image generation & geometry-aware baking
- Gaea 2.x              : Geological macroterrain synthesis & erosion maps
- PCG / PCG Extended    : Unreal runtime assembly & spatial data streaming
- Unreal MCP / Monolith : 1,400+ action agentic C++ editor control server (:9316)
- NNERuntimeORT         : ONNX neural runtime inference in engine memory
- Audio Synesthesia     : Single-writer UMelodiaAudioReactivePresentationSubsystem
- Cymatics Subsystem    : Read-only UMelodiaCymaticsSubsystem (Chladni / MPC integration)

=========================================================================================
TIER 2: SCAFFOLDED (Active Native Engine Modules - Extend existing files)
-----------------------------------------------------------------------------------------
- UMelodiaCaptureRenderSubsystem        : Multi-view HDR SceneCapture & PPV gating
- UMelodiaDressingSubsystem             : Native environment set-dressing & physics settling
- UMelodiaVisualRepresentationSubsystem : Simulation vs. Presentation boundary seam
- UMelodiaVegetationGrowthSubsystem     : Dynamic PCG growth layered over SpeedTree

=========================================================================================
TIER 3: ACCELERATORS (Authoring/Ideation Only - No Shipping Engine Dependencies)
-----------------------------------------------------------------------------------------
- JangaFX IlluGen       : Rapid flow map, caustic, and distortion texture authoring
- JangaFX LiquiGen      : Real-time liquid lookdev sketching (non-authoritative)
- JangaFX EmberGen 2.x  : Large-scale atmospheric volume & cloud flow ideation
- Cascadeur 2026.x      : Physics-assisted humanoid animation & balance recovery
- Polygonflow Dash      : Interactive editor viewport composition & prop scattering

=========================================================================================
TIER 4: R&D WATCH & FRONTIER RESEARCH (Isolated Spikes Only)
-----------------------------------------------------------------------------------------
- 3D / 4D Gaussian Splatting : Radiance field scene capture as visual reference
- Neural Shaders / Materials : Compact ONNX approximations of multi-layer BSDFs
- Magpie Architecture        : Generative realtime frame rendering vs. sim authority
- NVIDIA RTX Kit / ReSTIR   : Experimental mega-geometry path tracing
=========================================================================================
```

---

### 5.2 3D Gaussian Splatting (3DGS) Production Role

3D Gaussian Splatting defines continuous radiance fields via 3D Gaussians:

$$G(x) = \exp\left(-\frac{1}{2} (x - \mu)^T \Sigma^{-1} (x - \mu)\right), \quad \Sigma = R S S^T R^T$$

**Pipeline Usage:**
- Captured splat data (`.ply`, `.spz`, `.sog`) is ingested into Houdini 22 to extract surface point density, spatial bounds, ambient occlusion estimates, and rough collision proxies.
- UE5.8 renders splats via GPU radix-sorting compute shaders for visual reference and distant atmosphere.
- Gameplay collision, traversal, and rhythm interaction remain strictly anchored to Nanite static meshes and authored collision geometry.

---

### 5.3 Unified Melodia World Field Bus

To ensure spatial coherence across disparate DCC and runtime systems, all subsystems interface through the Melodia World Field Bus:

```text
                                 [Melodia World Field Bus]
                                             │
    ┌───────────────────┬────────────────────┼────────────────────┬───────────────────┐
    │                   │                    │                    │                   │
    ▼                   ▼                    ▼                    ▼                   ▼
WorldField.FilterFlow WorldField.Tension  WorldField.Moisture  WorldField.Resonance WorldField.Residue
 (Vector Flow Dir)    (Physical Strain)    (Water/Humidity)     (Harmonic Mode)      (Molt/Secretion)
    │                   │                    │                    │                   │
    ├──► Niagara        ├──► Vellum/Cloth    ├──► SpeedTree       ├──► Cymatics       ├──► Copernicus
         Particles           WPO Strains          Foliage Growth       MPC Materials       PBR Decals
```

#### SpeedTree Semantic Bridge Attributes
SpeedTree assets read the World Field Bus through 9 standardized channels:
1. `melodia_moisture`: Modulates trunk moss density and leaf hydration shaders.
2. `melodia_slope`: Adjusts root flare morphology and ground anchoring.
3. `melodia_wind_exposure`: Drives wind response curves and branch stiffness parameters.
4. `melodia_soil_depth`: Restricts canopy scale in shallow rocky strata.
5. `melodia_monolith_proximity`: Triggers procedural leaf discoloration and crystal growth.
6. `melodia_molt_age`: Controls epiphytic vegetation density on shed Monolith skins.
7. `melodia_filter_flow`: Aligns branch growth direction along atmospheric feeding currents.
8. `melodia_tension`: Modulates hanging vine elongation and tensioned limb geometry.
9. `melodia_ecological_density`: Determines PCG cluster sizes and understory competition.

---

## 6. End-to-End Technical Workflow Summary

```text
1. ACOUSTIC / MUSICAL STIMULUS
   Melodia Music Clock Subsystem -> BeatPulse / BassIntensity -> MPC_Melodia_Palette
                               │
2. CYMATICS & FIELD EVALUATION
   UMelodiaCymaticsSubsystem (Read-Only) -> Chladni Standing Wave Formula
   -> Publishes WorldField.Resonance (Mode n, m) & WorldField.Tension
                               │
3. PROCEDURAL TEXTURE & SHADER GENERATION
   Copernicus GPU Graph / Python Batch Pipeline -> Synthesizes 9-Map PBR Suite
   -> BaseColor, Normal, ORM, Height, Iridescence -> Applied to Master Materials
                               │
4. HOUDINI PROCEDURAL COMPILATION
   Houdini 22 SOP / KineFX / Vellum -> Ingests World Fields -> Bakes Static/Skeletal Assets
   -> Injects unreal_material & unreal_data_layer_* Attributes -> Bakes to UE Content
                               │
5. ENGINE COMPOSITION & AUTOMATION
   Monolith MCP Server (:9316) -> Spawns Actors, Wires Graphs, Audits CDO Drift
   -> PCG distributes SpeedTree instances using World Field Bus parameters
                               │
6. FINAL RUNTIME PRESENTATION
   Nanite + Lumen + Substrate PBR + Niagara System + FluidNinja Reactive Local Stage
```
