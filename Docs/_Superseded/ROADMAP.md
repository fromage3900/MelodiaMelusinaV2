# Production Roadmap — Environment Portfolio Platform

This roadmap outlines the development timeline, milestones, and deliverable targets for the multi-agent production team. The platform aims to build a reusable environment-art system using Unreal Engine 5.8, Blender 5.1, Material Maker, and Houdini.

---

## Roadmap Overview

```
Phase 1: Stabilization ──► Phase 2: Zen AAA Genome ──► Phase 3: Material Maker Integration
                                                                    │
Phase 6: Portfolio Showcase ◄── Phase 5: Houdini Integration ◄──────┴── Phase 4: Specialist Landscapes
```

---

## Phase 1: Subsystem Stabilization & UE 5.8 Integration (Active)

**Goal**: Resolve compiler errors, deprecations, and ensure clean multi-agent loop operations under Unreal Engine 5.8.

*   **Milestones**:
    *   [x] Fix C2665 compilation errors in `UnrealMCP` plugin (`BPVariables.cpp` / `BPConnector.cpp`) caused by key type change in `FJsonObject::Values` (to `FSharedString`).
    *   [x] Silence C4996 JSON serialization API warnings.
    *   [x] Replace deprecated `WhitelistPlatforms` with `PlatformAllowList` in plugin descriptors.
    *   [x] Extract universal material properties (`setup_master_universal.py` and group sorting).
    *   [x] Implement legacy asset retention policy: safeguard `Content/_PROJECT/` permanently while rewiring EnvSandbox instances.
    *   [x] Establish automated verification loops (`run_verify.ps1`, `_mcp_verify_world.py`, `audit_material_library.py`).
*   **Deliverables**:
    *   Stable C++ plugins for UE 5.8.
    *   Green checkmarks across all Phase 1 QA verification scripts.

---

## Phase 2: Zen AAA / Style Genome Maturation (Active)

**Goal**: Mature the Blender procedural layout engine and Style Genome taxonomy for the pilot Japanese Zen Shrine theme.

*   **Milestones**:
    *   [x] Register `GB_ZEN_SANDO` and `GB_ZEN_KAIRO` architectural atoms.
    *   [x] Standardize snap parameters and kit constraints in `architectural_atoms.yaml`.
    *   [x] Define `ZEN_SHRINE_AXIS` room grammar (Torii → Sando → Kairo → Karesansui).
    *   [x] Register `GB_ZEN_HAIDEN` (Worship Hall platform, genkan steps, ranma, noki).
    *   [x] Hook non-Euclidean transforms (`axis_compression`) into Style Genomes.
    *   [ ] Implement Tier B and Tier C modules: Goju-no-to (five-story pagoda), Tahoto, Honden, and Sakura Torii variants.
    *   [ ] Export compiled Style Genomes directly to `.world.json` manifests.
*   **Deliverables**:
    *   Procedural Zen layout generator in Blender panel.
    *   Verified snap consistency and zero mesh intersection across generated layouts.

---

## Phase 3: Material Maker Engine Integration (Planned)

**Goal**: Replace flat-colorize nodes in Material Maker with a reusable, modular, 3-layer surreal PBR node engine.

*   **Milestones**:
    *   [ ] Build **Layer 1: Base Utility Subgraphs** (Noise library, mask shaping, triplanar coordinate systems, seed systems, and domain warp).
    *   [ ] Build **Layer 2: PBR Engine** (Albedo, normal, roughness, metallic, AO, height, emissive, opacity, and SSS channels).
    *   [ ] Build **Layer 3: Style Trees** (Nikki soft pastel, Madoka ethereal witch barrier, Itto mythic carved cracks, Celestial NASA space parallax).
    *   [ ] Compile PTEX graphs with normalized parameters (0-1 range).
    *   [ ] Write translation scripts to parse Material Maker nodes and map them directly into Unreal Engine master node parameters via `setup_material_functions.py`.
*   **Deliverables**:
    *   `MM_Master_SurrealAnimatedPBR_v2` project files.
    *   Python translator compiling Material Maker graphs into Unreal Engine Material Functions.

---

## Phase 4: Specialist Landscapes, Water, & Niagara Vistas (In Progress)

**Goal**: Build advanced environment shading systems that extend the universal master shader into specialized domains.

*   **Milestones**:
    *   [x] Implement 4-layer painted height competition on landscapes (Rock, Grass, Mud, Path).
    *   [x] Extract custom material functions (`MF_LandscapeHeightCompete`, `MF_WaterShorelineFade`).
    *   [x] Build `M_Water_Master_Grand_v6` containing Gerstner waves, caustics, and shoreline depth-based color fades.
    *   [x] Wire Infinity Nikki dream grading and shimmer options onto landscape meshes.
    *   [ ] Integrate Niagara sprite material setups (`MI_Niagara_Petals`).
    *   [ ] Set up interactive shoreline foam and water-surface ripples responding to character movement.
*   **Deliverables**:
    *   `M_Master_Toon_Landscape_HeightBlend` master shader.
    *   `M_Water_Master_Grand_v6` master shader.
    *   Specialist water instances (`MI_GrandWater_SakuraPond`).

---

## Phase 5: Houdini Procedural Generation Integration (Planned)

**Goal**: Expand environment layout options from Blender grids to Houdini-based procedural building generators.

*   **Milestones**:
    *   [ ] Set up Houdini Engine integration within the Unreal project.
    *   [ ] Build Houdini Digital Assets (HDAs) for stylized roof tiling, wall framing, and bridge arching.
    *   [ ] Wire HDA outputs to emit `surreal_arch_world_v1` metadata, ensuring they snap together using the same taxonomy rules as Blender.
    *   [ ] Enable HDA generators to sample PCG point data to place doors, windows, and decor based on local density.
*   **Deliverables**:
    *   Cathedral, Gothic, and Japanese structural HDAs.
    *   Automated geometry spawning directly inside Unreal viewport.

---

## Phase 6: Portfolio Showcase Production & Optimization (Ongoing)

**Goal**: Assemble, optimize, and document the final portfolio scenes (`L_Template`, `L_SakuraPath`) to showcase the platform's visual quality.

*   **Milestones**:
    *   [x] Build `L_Template` showcase containing sphere previews for all 13 core material instances.
    *   [ ] Assemble `L_SakuraPath` level using generated Zen Shrine elements, grand water pond, and PCG-scattered cherry blossoms.
    *   [ ] Resolve reference redirectors and compile shaders with zero errors.
    *   [ ] Profile scene frame rate, draw calls, and HISM instance counts.
    *   [ ] Implement Post-Process outline and storybook vines to frame the stylized renders.
*   **Deliverables**:
    *   Fully populated, high-performance portfolio scene levels.
    *   Visual walkthrough guides detailing frame rates and design configurations.
