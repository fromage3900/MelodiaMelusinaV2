# Material Pipeline Specification — Environment Portfolio Platform

This document specifies the master shader architecture, parameter schemas, Substrate Toon integrations, and automation scripts used in the **Environment Portfolio Platform**.

---

## 1. Core Master Shaders (Unreal Engine 5.8)

The project relies on four specialized master shaders under `/Game/EnvSandbox/Materials/Masters/`.

```
                        ┌─────────────────────────────────┐
                        │      SUBSTRATE TOON BSDF        │
                        └────────────────▲────────────────┘
                                         │
       ┌─────────────────────────────────┼─────────────────────────────────┐
       │                                 │                                 │
┌──────┴──────┐                   ┌──────┴──────┐                   ┌──────┴──────┐
│  UNIVERSAL  │                   │  LANDSCAPE  │                   │    WATER    │
│  M_Master   │                   │  M_Master   │                   │  M_Master   │
│  Mesh props │                   │ HeightBlend │                   │   Grand_v6  │
└─────────────┘                   └─────────────┘                   └─────────────┘
```

### 1.1 `M_Master_Toon_Universal`
The primary surface master for meshes, props, and architectural trims. It is programmatically built via [setup_master_universal.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_universal.py) and features 18 texture parameter slots.

#### Parameter Group Hierarchy
1.  **Textures / LayerA / LayerB**: Albedo, Normal, ORM (Occlusion/Roughness/Metallic), and Height.
2.  **Triplanar / Temporal**: Controls world-aligned mapping projections, ink boil frequencies, and camera smears.
3.  **Layers**: Manages height-based blending between Layer A and Layer B.
4.  **Nikki (Infinity Nikki environment style)**: Controls stylization rim light widths, dream grades, glints, fabric sheens, and sparkles.
5.  **Celestial**: Renders space parallax star fields, galaxy arms, and toon-banded nebulas.
6.  **Madoka (Ethereal Witch Barrier)**: Distorts colors using Voronoi vein noise, radial witch rings, and SSS fake glows.
7.  **Gilding**: Projects curvature-based gold leaf masks onto edges.
8.  **Itto (Mythic Carved)**: Fractures surfaces using procedural Truchet cracks, wear masks, and edge breakups.
9.  **ShadowDream**: Custom N·L grading to tint and band shadow values.
10. **FlowerShadow**: Projects animated petal shadows onto surfaces.
11. **FairyDust**: Overlays star, heart, moon, and flower motifs onto highlighted surfaces.
12. **Magical**: Handles henshin transition wipes and palette shifts.

### 1.2 `M_Master_Toon_Landscape_HeightBlend`
Built via [setup_landscape_height_blend.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_landscape_height_blend.py). It manages four painted texture layers (Rock, Grass, Mud, Path) and matches the style features of the Universal master.

*   **Height-Dot Competition**: Uses `MF_LandscapeHeightCompete` to calculate sharp, natural transitions between materials based on height maps.
*   **Procedural Fallback**: Automatically activates height-based competition across layers if manual painting weights sum to zero.
*   **Slope Cliff Blend**: Projects triplanar cliff rock textures onto vertical angles automatically.
*   **Weathering Layers**: Overlays a procedural snow cover mask on upward-facing normals.

### 1.3 `M_Water_Master_Grand_v6`
A translucent water master built via [setup_master_water.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_water.py).
*   **Displacement**: Uses multi-octave Gerstner waves for physical vertex motion.
*   **Rendering**: Project-caustics maps, shoreline depth-based color fades, and high-roughness sparkles matching the Nikki environment theme.

### 1.4 `M_Master_Impressionist_Toon`
A specialized shader built via [setup_impressionist_materials.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_impressionist_materials.py) that renders a painterly, textured oil-paint overlay onto assets.

---

## 2. Shading Accumulator Chains (Universal Master)

Parameters accumulate value down a sequence chain before outputting to the Substrate BSDF node.

### 2.1 Roughness Accumulator Chain
```
Base Roughness (Layer A/B sample)
       │
       ▼
Gilding Blend ──────► Lerp Gold Roughness by Gold Mask
       │
       ▼
Itto Breakup  ──────► Add Carved Crack Breakup delta
       │
       ▼
Wetness       ──────► Lerp Wetness Roughness by Wet Mask
       │
       ▼
Audio Pulse   ──────► Add Beat Reactivity MPC delta
       │
       ▼
[Final Substrate Toon BSDF Roughness]
```

### 2.2 Emissive Accumulator Chain
```
Emissive Sum = (Rim Emissive + Iridescence Emissive)
             + Sparkle Glow
             + Madoka Witch Barrier Emissive
             + Sheen Emissive
             + Curvature Gold Emissive
             + Fairy Dust Motifs
             + Audio Emissive Vector (MPC)
             + Animated Flower Shadows
             * (1.0 + Bloom Boost)
             │
             ▼
[Final Substrate Toon BSDF Emissive]
```

---

## 3. Substrate Toon BSDF Integration

Unreal Engine 5.8 Substrate materials provide modular rendering interfaces.

*   **Node Configuration**: Masters output to a **Substrate Toon BSDF** node, feeding the result into the **Front Material** output.
*   **Toon Profiles (`TP_*`)**: Located under `/Game/EnvSandbox/Materials/ToonProfiles/`. These assets define color banding steps and shadow ramp sharpness.
    *   `TP_Default`: Standard 3-step cell shadow.
    *   `TP_Stucco`: Soft shadow ramp for plaster walls.
    *   `TP_Gold`: High-contrast reflection band for gilding.
    *   `TP_Ornamental`: Sharp, dark shadow lines for structural trims.

---

## 4. Trim Sheet & Vertex Color Conventions

Trim sheets are utilized heavily for surreal architecture layout.

*   **Vertex Color Channel (`trim_id`)**: Blender bakes trim identifiers into the mesh vertex color.
*   **Material Masking**: The Universal master reads the `trim_id` vertex attribute to drive local texture shifts, gilding placement, and layer blending weights.
*   **Baking Pipeline**: `surreal_arch/trim_bake.py` maps Blender's face-level `trim_groups` metadata to the vertex color channel automatically during FBX export.

---

## 5. Material Maker Integration Plan (MM v2)

Material Maker graphs under `Tools/MaterialMaker/` compile procedural textures for the portfolio.

*   **3-Layer Redesign Schema**:
    *   **Layer 1 (Utility)**: Subgraphs for Noise (`SG_Noise_Library`), Masking (`SG_Mask_Shaping`), Triplanar, and Global Seeds (`SG_Seed_System`).
    *   **Layer 2 (PBR Engine)**: Albedo, Normal, Roughness, Metallic, Height, Emissive, and SSS channels.
    *   **Layer 3 (Style Trees)**: Style nodes matching Nikki, Madoka, Itto, and Celestial parameters.
*   **Parameter Normalization**: All exported Material Maker parameters are clamped to a `0.0 - 1.0` range.
*   **Unreal Importer Translator**: A planned script will parse compiled Material Maker `.ptex` parameter files and automatically construct matching material instances in Unreal Engine using `setup_trimsheet_instances.py` and `setup_sdf_materials.py`.

---

## 6. Automation Scripts Reference

| Script | Purpose | Execution Command |
| :--- | :--- | :--- |
| [setup_master_universal.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_universal.py) | Builds/rebuilds the core universal master shader. | `py setup_master_universal.py` (use `BS_MASTER_FORCE=1` to override) |
| [setup_landscape_height_blend.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_landscape_height_blend.py) | Compiles the 4-layer height-blend landscape shader. | `py setup_landscape_height_blend.py` |
| [apply_starter_instances.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_starter_instances.py) | Creates the 13 canonical showcase material instances. | `py apply_starter_instances.py --starters-only` |
| [setup_trimsheet_instances.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_trimsheet_instances.py) | Builds Layer A/B blend trimsheet instance presets. | `py setup_trimsheet_instances.py` |
| [audit_material_library.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_material_library.py) | Scans for dead references, orphans, and invalid paths. | `py audit_material_library.py` |
| [fix_migration_redirectors.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_migration_redirectors.py) | Programmatically resolves redirected uassets. | `py fix_migration_redirectors.py` |
