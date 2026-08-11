# System Architecture Map — Environment Portfolio Production Platform

This document describes the high-level system architecture of the **Environment Portfolio Production Platform**, detailing the six core components that enable automated asset layout, shading, composition, and presentation.

---

## 1. Core Subsystems

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      MCP INTEGRATION LAYER (:55557)                     │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ (RPC Controls)
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │                            IMPORT PIPELINE                             │
 │           Parses manifests, auto-imports FBXs, spawns HISMs            │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ (Placed Actor Hierarchy)
 ┌───────────────────────────────────┼────────────────────────────────────┐
 │  ┌─────────────────────────────┐  │  ┌──────────────────────────────┐  │
 │  │       MATERIAL SYSTEM       │◄─┼─►│          PCG SYSTEM          │  │
 │  │ Masters, instances, functions│  │  │ Universal scatters, falloffs │  │
 │  └─────────────────────────────┘  │  └──────────────────────────────┘  │
 └───────────────────────────────────┼────────────────────────────────────┘
                                     │ (Configured Scene Data)
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │                              SCENE SYSTEM                              │
 │            Ultra Dynamic Sky, Post-Process, templates, MPC             │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │ (Studio Rendering & Audits)
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │                         PORTFOLIO OUTPUT LAYER                         │
 │      Monolith rendering, screenshot overlays, JSON stats metadata     │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Subsystem Definitions

### 2.1 Material System
*   **Purpose**: Compiles layered Substrate Toon master shaders and automates the creation of material instances.
*   **Scope**:
    *   Masters: Opaque surfaces (`M_Master_Toon_Universal`), landscapes (`M_Master_Toon_Landscape_HeightBlend`), water (`M_Water_Master_Grand_v6`), and painterly overlays (`M_Master_Impressionist_Toon`).
    *   Helper API: [material_lib.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/material_lib.py) constructs graphs programmatically using Unreal's `unreal.MaterialEditingLibrary`.
    *   Functions: Programmatic subgraphs like `MF_LandscapeHeightCompete` and `MF_WaterShorelineFade`.
*   **Primary Entry Points**:
    *   [setup_master_universal.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_universal.py)
    *   [setup_landscape_height_blend.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_landscape_height_blend.py)
    *   [setup_master_water.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_water.py)

### 2.2 PCG System
*   **Purpose**: Automatically scatters foliage, rocks, and debris onto environment geometry.
*   **Scope**:
    *   Scatters: Universal graphs (`PCG_FoliageDensity`, `PCG_RockScatter`) and style-specific wrappers (`PCG_Sakura_GroundCover`).
    *   Libraries: [pcg_graph_builder.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/pcg_graph_builder.py) programmatically wires density filters, voxel grids, and static mesh spawners.
    *   Standards: [pcg_portfolio_standards.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/pcg_portfolio_standards.py) sets path parameters, volumes, and exclusion tags (`PCG_Ground`, `PCG_Volume`).

### 2.3 Scene System
*   **Purpose**: Manages global environment setups, lighting setups, post-processing stacks, and showcase layouts.
*   **Scope**:
    *   Lighting: Dynamically spawns and configures **Ultra Dynamic Sky** and Dynamic Weather actors.
    *   Post-Processing: Integrates cell outlines (`M_PP_ToonOutline`) and organic vine filters (`M_PP_StorybookVines`).
    *   Showcases: Generates showcase scene spheres and preview cards.
*   **Primary Entry Points**:
    *   [setup_sakura_scene.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_sakura_scene.py)
    *   [setup_template_showcase.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_template_showcase.py)
    *   [portfolio_scene_integration.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/portfolio_scene_integration.py)

### 2.4 Import Pipeline
*   **Purpose**: Converts layout plans into Unreal Engine outliner actor hierarchies.
*   **Scope**:
    *   Importer: [import_world_manifest.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_world_manifest.py) reads `{WorldRoot}.world.json` files using the `surreal_arch_world_v1` schema.
    *   HISM Spawner: Instantiates Hierarchical Instanced Static Mesh components grouped by role and handles coordinate space transformation (Blender Z-up meters to UE Left-handed cm).
    *   Mesh Resolver: Automatically handles FBX imports and maps roles to material instances using `ROLE_UE_HINTS` mappings.

### 2.5 MCP Integration Layer
*   **Purpose**: Exposes engine RPC actions over local sockets, enabling external agents to control the editor.
*   **Scope**:
    *   Plugin: The `UnrealMCP` plugin listens on Port `55557` and maps incoming JSON requests to command executors.
    *   Commands: Programmatic graph manipulation and variable editing (`BPConnector.cpp`, `BPVariables.cpp`).
    *   Client API: [monolith_mcp_client.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/monolith_mcp_client.py) allows python processes to trigger editor actions.

### 2.6 Portfolio Output Layer
*   **Purpose**: Automatically renders portfolio-ready images and extracts technical metrics from active levels.
*   **Scope**:
    *   Rendering: Captures asset previews (`editor.capture_scene_preview`), material grids (`editor.capture_material_grid`), and diagnostic views (`editor.capture_with_overlay` in wireframe/UV modes).
    *   Metadata: Audits memory usages and asset metrics, compiling them into a central `portfolio_manifest.json` report.
