# Poitou Sanctuary: Production Geometry Nodes System Overhaul Plan
**Document Version:** 2.0 (Post-Audit Overhaul)  
**Target Milestone:** AAA Stylized Environment Convergence (Marais Poitevin / "Melusina's Morning")  
**Target Rigs:** Blender 5.2 Geometry Nodes $\rightarrow$ Unreal Engine 5.8 Nanite  
**Reference Canon:** [`Docs/Poitou/style_contract.md`](style_contract.md), [`Docs/Poitou/SOURCES.md`](SOURCES.md), [`Docs/Poitou/gn_parisian_audit.md`](gn_parisian_audit.md)

---

## 1. Executive Summary & Core Pivot

### 1.1 The Failure Mode of the Initial Pass
The preliminary asset generation pass relied on automated headless Python scripts applying mathematical vertex displacement via raw Perlin noise (`TexNoise` $\rightarrow$ `Normal` $\rightarrow$ `Set Position`) and automated OpenVDB voxel remeshing. This produced:
- Lumpy, marshmallow-like architectural silhouettes lacking planar definition.
- Destroyed voussoir/archivolt definition in Romanesque arches.
- Chaotic, un-stylized surface noise that read as corrupted digital geometry rather than dressed limestone or hand-adzed French timber.

### 1.2 The Architectural Mandate: "Silhouette is French. Music lives in rhythm and ornament."
Per the Poitou Style Contract:
- **Far View ($>50\,\text{m}$):** Every structure must read strictly as authentic Poitevin vernacular or Romanesque architecture (limestone rubble, lime-washed render, terracotta canal roofs, pollard ash tunnels, flat wooden barques). No giant clefs, no floating islands, no musical-instrument buildings.
- **Mid View ($20\text{--}50\,\text{m}$):** Music is expressed strictly through structural rhythm (bay spacing = 4 beats = $2.4\,\text{m}$; opening bar patterns; voussoir counts; plank spacing).
- **Near View ($<20\,\text{m}$):** Fine ornament (carved Romanesque capital corbels, ironwork hinges styled as subtle scrolls, water-whip shoots on pollard calluses).

---

## 2. Canonical Module Grid & Proportions

All Geometry Nodes generators must strictly bind to the global metric coordinate system:

| Architectural Metric | Metric Dimension | Musical Meter Analogue | Functional Constraint |
| :--- | :--- | :--- | :--- |
| **Base Module ($M$)** | $0.6\,\text{m}$ | Single Beat ($1/4$ note) | Base unit for all wall steps and openings. |
| **Bay Width ($4M$)** | $2.4\,\text{m}$ | Full Bar ($4/4$ measure) | Structural column / pier spacing. |
| **Storey Height ($5M$)** | $3.0\,\text{m}$ | Vertical Octave | Ground floor $3.0\,\text{m}$; upper floor $2.7\,\text{m}$. |
| **Wall Thickness** | $0.5\text{--}0.7\,\text{m}$ | Solid Cavity | Double-wythe limestone rubble core. |
| **Plinth Height** | $0.4\text{--}0.6\,\text{m}$ | Damp Plinth | Flood defense above Marais canal bank. |
| **Opening Width** | $0.6\,\text{m} \text{ or } 1.2\,\text{m}$ | Half-bar / Full-bar | Openings never exceed 40% of wall face. |
| **Arch Proportions** | Semicircular only | $\text{Rise} = \text{Span} / 2$ | Pointed ogives strictly banned on village assets. |

---

## 3. The 5 Core Geometry Nodes Architectural Engines

Rather than applying displacement shaders, the overhauled system constructs real geometric components using modular GN subgraphs:

```
                          ┌────────────────────────┐
                          │   Input Guide Curve/   │
                          │     Bounding Volume    │
                          └───────────┬────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         ▼                         ▼
  [Engine 1: Masonry]       [Engine 2: Arches]       [Engine 3: Pollard]
   • Ashlar Block Coursing   • Radial Voussoir Wedges  • Fluted Sinus Trunk
   • Stretcher/Header Bond   • Keystones & Imposts     • Swollen Callus Head
   • Recessed Mortar Gaps    • Stepped Archivolts      • Water-Whip Branches
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      │
                                      ▼
                        [Engine 5: Boolean Ruin]
                         • Stepped Joint Fractures
                         • Horizontal Bed Dropouts
                         • Crevice Ivy Distribution
                                      │
                                      ▼
                        [Clean Planar Output Mesh]
                         (Ready for Nanite / UE5)
```

---

### Engine 1: `GN_Poitou_AshlarMasonry` (Dressed Limestone & Rubble)
Generates authentic Poitevin dressed ashlar quoins and rubble curtain walls.

- **Node Graph Topology**:
  1. **Bounding Volume Slicing**: Uses `Mesh to Points` on bounding vertices along vertical intervals of $0.3\,\text{m}$ (stone course height).
  2. **Alternating Bond Pattern**: Shifts horizontal block offsets by half-block width ($0.3\,\text{m}$) on alternating tiers (stretcher bond).
  3. **Individual Block Instancing**: Instances pre-authored, chamfered limestone block templates ($0.6 \times 0.3 \times 0.4\,\text{m}$) with random scale jitter ($\pm 3\%$) and micro-rotation ($\pm 1.2^\circ$).
  4. **Recessed Mortar Inset**: Insets the mortar background plane by $2.0\,\text{cm}$ behind the stone face, creating crisp real geometry shadow lines instead of blurry normal maps.
  5. **Exposed Sliders**:
     - `Course Height`: Default $0.30\,\text{m}$ (Min: $0.20\,\text{m}$, Max: $0.45\,\text{m}$).
     - `Block Length`: Default $0.60\,\text{m}$ (Snap: $0.30\,\text{m}$).
     - `Joint Gap`: Default $0.02\,\text{m}$ ($2\,\text{cm}$ lime mortar).
     - `Block Jitter`: Default $0.015\,\text{m}$ (surface settling).

---

### Engine 2: `GN_Poitou_RomanesqueArch` (Voussoir & Archivolt Generator)
Constructs structurally sound Romanesque portal arches and blind arcades.

- **Node Graph Topology**:
  1. **Parametric Arc Spline**: Generates a 180-degree semicircular curve from span input ($2.4\,\text{m}$ bay default, radius $1.2\,\text{m}$).
  2. **Radial Angle Resampling**: Resamples curve into an **odd number of segments** ($13, 15, \text{ or } 17$) to guarantee a central vertical **keystone**.
  3. **Radial Voussoir Extrusion**: At each point, aligns instance coordinate frames radially toward the arc center point. Extrudes wedge blocks with wider outer rim and tapered inner intrados.
  4. **Concentric Archivolt Stepping**: Offsets outer rings forward by $+12\,\text{cm}$ and inward by $-8\,\text{cm}$, replicating the recessed French portal "chord".
  5. **Exposed Sliders**:
     - `Arch Span`: Default $2.4\,\text{m}$ (1 bay).
     - `Voussoir Count`: Default 15 (Must be odd).
     - `Archivolt Depth Tiers`: Default 3 tiers.
     - `Keystone Protrusion`: Default $0.04\,\text{m}$ ($4\,\text{cm}$).

---

### Engine 3: `GN_Poitou_PollardAsh_Trunk` (Frêne Têtard Organic Node)
Recreates the signature Marais Poitevin pollard ash trees.

- **Node Graph Topology**:
  1. **Fluted Trunk Profile**: Uses `Curve Circle` deformed by a 5-lobed sine wave to generate the deep sinus trunk ridges characteristic of ancient pollard ash.
  2. **Taper & Callus Swelling**: Sweeps profile along vertical spline up to $2.4\,\text{m}$ (the traditional Marais cutting height). Between $1.8\,\text{m}$ and $2.4\,\text{m}$, applies smoothstep radial expansion ($+45\%$) to form the bulbous callus head.
  3. **Hollow Heartwood Cavity**: Performs a boolean difference using an inverted cone at the top center of the head, representing aged rotted heartwood where water collects.
  4. **Branch Shoot Instancing**: Uses `Distribute Points on Faces` restricted to the outer callus rim (masked by normal pointing upward and radial distance $>0.8R$). Instances slender $2\text{--}3\,\text{m}$ vertical whip shoots.
  5. **Exposed Sliders**:
     - `Trunk Height`: Default $2.4\,\text{m}$ (Cutting level).
     - `Trunk Base Radius`: Default $0.55\,\text{m}$.
     - `Callus Head Flare`: Default $1.45\times$.
     - `Hollow Depth`: Default $0.65\,\text{m}$.
     - `Shoot Density`: Default 35 shoots/rim.

---

### Engine 4: `GN_Poitou_MaraisPlanking` (Oak Decking, Jetties & Lock Gates)
Constructs timber lock gates, flat barques (*plates*), and landing jetties.

- **Node Graph Topology**:
  1. **Plank Array Distribution**: Distributes planks along guide paths at strict $0.24\,\text{m}$ spacing ($10 \text{ planks} = 2.4\,\text{m} = 1 \text{ bar}$).
  2. **Board Realization**: Instances beveled oak boards ($0.23\,\text{m} \times 0.05\,\text{m} \times \text{Length}$) leaving an authentic $1.0\,\text{cm}$ drain expansion gap.
  3. **Subtle Adze Profile**: Deforms top face using a low-frequency scalloped wave ($0.5\,\text{cm}$ amplitude across $1.2\,\text{m}$) to mimic traditional hand-adze woodworking without bloated vertex noise.
  4. **Hardware Sockets**: Spawns forged iron spike heads and strap-hinge plates at plank ends.
  5. **Exposed Sliders**:
     - `Plank Width`: Fixed at $0.24\,\text{m}$ (Musical module).
     - `Expansion Gap`: Default $0.008\,\text{m}$ ($8\,\text{mm}$).
     - `Adze Hand-Hewn Depth`: Default $0.004\,\text{m}$ ($4\,\text{mm}$).
     - `Tarred Waterline Z`: Default $0.40\,\text{m}$.

---

### Engine 5: `GN_Poitou_AbbeyDecay` (Maillezais Ruin Fracture Engine)
Generates authentic collapsed cathedral ruins without voxel melting.

- **Node Graph Topology**:
  1. **Course-Aligned Slicing**: Slices walls strictly along horizontal stone bed joints and vertical voussoir planes using procedural bisect planes, ensuring breaks follow masonry blocks.
  2. **Dropout Probability Mask**: Randomly deletes individual stone instances along the top broken edge using a noise threshold weighted by height ($Z$).
  3. **Faceted Rubble Scatter**: Instanced detached stone blocks accumulate at the base on the ground plane ($Z = 0$).
  4. **Ivy Crevice Mask**: Distributes climbing ivy vine curves strictly within deep concave crevices and upward-facing horizontal ledges (via AO and Dot-Product normals).
  5. **Exposed Sliders**:
     - `Ruin Collapse Height`: Default $6.5\,\text{m}$.
     - `Block Dropout Ratio`: Default 0.35 (35% stones missing along crest).
     - `Rubble Heap Radius`: Default $3.5\,\text{m}$.

---

## 4. Integration with Existing Project Builders

To avoid redundant development, the overhauled GN suite directly integrates with the canonical builders already established in the repository:

| Existing Builder in Repo | Source File | Overhaul Integration Role | Parameter Overrides for Poitou |
| :--- | :--- | :--- | :--- |
| **`MEL_nikki_quarter`** (Mode 0) | `src/p/nikki_quarter.py` | Village Townhouses & Barns | `Floors`: 1–2; `FloorHeight`: 2.7–3.0; `Width`: 7.2–14.4; `RoofPitch`: 0.5 (~27° terracotta); `BayWindow/Balcony`: OFF; `FlowerBoxes`: ON. |
| **`MEL_wall_*` Family** | `src/p/walls_kit.py` | Quéreux Enclosure Walls | `Thickness`: 0.5–0.7m; `Height`: 1.8–2.4m; `Openings`: Driven by musical bar rhythm (`– W – W`). |
| **`GN_PARIS_WallDetail`** | `src/p/paris_wall_detail.py` | Baseboard & Quoin Trims | `ShowCornice/String`: OFF; `ShowBaseboard`: ON (as 0.5m damp plinth); `ApplyTrimUV`: ON. |
| **`MEL_half_timber_wall`** | `src/p/walls_kit.py` | Jetty Sheds & Barn Balais | `StepDrop`: 0.6–1.2m toward canal waterline; `TimberWidth`: 0.24m. |
| **`MEL_math_gothic_cathedral`** | `src/p/recursive_castle.py` | Maillezais Abbey Ruin | Lowered to squat Romanesque: `VaultHeight`: 7–9m; `ButtressReach`: 0.6–0.9m; `RoseRadius`: 0; Semicircular arches only. |
| **`MEL_music_piano_roll`** | `src/p/music_heroes.py` | Canal Jetties & Walkways | `KeyWidth`: 0.24m (Oak plank); `KeyLength`: 1.2–1.5m; Black keys limited to 1 octave per span. |

---

## 5. Staged Blockout Proxies Delivery (Phase 1 Complete)

All bloated and lumpy geometry in [`Poitou_Sanctuary_Ultimate_Staging.blend`](file:///C:/EnvironmentPortfolio/BS_GodFile/Poitou_Sanctuary_Ultimate_Staging.blend) has been purged. The scene now contains 100% clean, planar blockout proxies:

```
Poitou_Sanctuary_Ultimate_Staging.blend (0.18 MB)
├── 01_Architecture_Monumental
│   ├── SM_Maillezais_BrokenArch_Proxy      (13.2m Romanesque lancet arch)
│   ├── SM_Maillezais_CrumbledWall_Proxy     (7.4m planar rubble wall)
│   ├── SM_Maillezais_ButtressStub_Proxy     (Chamfered pilaster buttress)
│   ├── SM_Poitou_Acoustic_OrganChimney_Proxy(Resonance chimney)
│   └── SM_Poitou_Viaduct_AcousticRail_Proxy (Arched viaduct balustrade)
├── 02_Vernacular_Props
│   ├── SM_Poitou_VillageWell_Proxy          (Limestone well + timber beam)
│   ├── SM_Poitou_CalvaryCross_Proxy         (Stepped plinth + cross)
│   ├── SM_Poitou_StoneBench_Proxy           (Monolithic limestone bench)
│   ├── SM_Poitou_LockGate_Pair_Proxy        (Diagonal braced timber gates)
│   ├── SM_Poitou_Barque_Proxy               (4.6m flat-bottom plate)
│   ├── SM_Poitou_Pigouille_Proxy            (4.5m ash push-pole)
│   └── SM_Poitou_BridgeParapet_Proxy        (Canal bridge coping)
├── 03_Pollard_Vegetation
│   ├── SM_AshTetard_Ancient_01_Proxy        (Swelled callus head trunk)
│   ├── SM_AshTetard_Twisted_02_Proxy        (Curved bank-leaning trunk)
│   └── SM_AshTetard_Canal_03_Proxy          (Waterline hollow trunk)
└── 04_Studio_Lighting_Backdrop
    ├── Studio_Cyclorama_Ground              (Curved neutral studio cyclorama)
    └── Lighting Rig & Hero Camera           (3-point softbox studio lighting)
```

---

## 6. Execution Roadmap

| Phase | Milestone | Deliverable | Status |
| :---: | :--- | :--- | :---: |
| **1** | **Blockout Clean Sweep** | Purge noise/VDB; stage pure planar proxies in `Poitou_Sanctuary_Ultimate_Staging.blend`. | **COMPLETED** |
| **2** | **Core GN Subgraphs** | Author `GN_Poitou_AshlarMasonry`, `GN_Poitou_RomanesqueArch`, `GN_Poitou_PollardAsh_Trunk`. | **READY FOR DEV** |
| **3** | **Vernacular Timber Nodes** | Author `GN_Poitou_MaraisPlanking` for lock gates, quays, and barque decks. | **PENDING** |
| **4** | **Maillezais Ruin Fracture** | Implement `GN_Poitou_AbbeyDecay` block-slicing boolean pass. | **PENDING** |
| **5** | **Nanite Export Pipeline** | Export clean Nanite FBXs with custom vertex-color masks for UE 5.8 ingestion. | **PENDING** |
