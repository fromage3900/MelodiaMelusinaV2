# Automated Portfolio & Figma Production Pipeline Specification

This document details the pipeline design for automatically extracting visual assets, technical statistics, and narrative metadata from **Unreal Engine 5.8** and mapping them directly to a **Figma Design System** template for automated portfolio assembly and ArtStation publishing.

---

## 1. Automated Scene Outputs

The pipeline uses the C++ editor preview hooks of the **Monolith** plugin and **Python metadata scanners** to automatically render and package content during Loop verification cycles.

```
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│           UNREAL WORKSPACE           │          │          PORTFOLIO ARTIFACTS         │
├──────────────────────────────────────┤          ├──────────────────────────────────────┤
│  - Monolith Preview Render Engine   │          │  - PNG Renders (Hero, Breakdown)    │
│  - Python Asset Metadata Scanners    │ ───────► │  - JPG Swatches (Material, Trim)     │
│  - Level Viewport Camera Capture     │          │  - JSON Stats & Narrative Manifests  │
└──────────────────────────────────────┘          └──────────────────┬───────────────────┘
                                                                     │
                                                                     ▼ (Figma Sync & ArtStation Publish)
                                                  ┌──────────────────────────────────────┐
                                                  │       PORTFOLIO DESTINATIONS         │
                                                  ├──────────────────────────────────────┤
                                                  │  - Figma Design System Templates     │
                                                  │  - ArtStation Project Drafts         │
                                                  └──────────────────────────────────────┘
```

### 1.1 Hero Renders
*   **Source**: Active environment levels (`L_SakuraPath`, `L_Template`).
*   **Extraction Method**: cine camera actors are marked with `Portfolio_Hero` tags. The pipeline queries the world context, binds the view target to the tagged camera, and triggers viewport frame capture with a 60-frame temporal AA warm-up.
*   **Target Resolutions**:
    *   Figma Desktop Frame: `1920 x 1080` (16:9, sRGB, PNG).
    *   Mobile/Instagram Frame: `1080 x 1350` (4:5 vertical, sRGB, PNG).

### 1.2 Breakdown Sheets
*   **Source**: Generated greybox static meshes (`GB_ZEN_*`).
*   **Extraction Method**: Executes the Monolith editor action `editor.capture_with_overlay`.
    *   `asset_path`: Target static mesh path.
    *   `mode`: `wireframe` (mesh edges), `uv_density` (tiling density), or `shader_complexity`.
    *   `resolution`: `1024 x 1024` (PNG, transparent background).

### 1.3 Material Sheets
*   **Source**: Active material instances (`MI_Show_*`, `MI_Zen_*`).
*   **Extraction Method**: Executes `editor.capture_material_grid` to render up to 16 materials in a single preview scene under identical lighting and HDRI reflections.
    *   `material_paths`: Array of material instance references.
    *   `preview_mesh`: `sphere` (standard surfaces) or `plane` (displacement/parallax).
    *   `resolution`: `2048 x 2048` grid (producing `512 x 512` individual cell swatches).

### 1.4 Trim Sheet Sheets
*   **Source**: Blended trimsheet instances (`MI_Trimsheet_*`).
*   **Extraction Method**: Spawns a flat trim-panel static mesh configured with `trim_id` vertex color masking. Captures:
    1.  A fully lit pass under neutral studio HDRI.
    2.  An overlay pass using `wireframe` or `uv_density` modes to expose the UV layout tiling across the trim layout.

### 1.5 Asset Statistics Manifest
*   **Source**: Static mesh assets, HISM outliner components, and PCG volumes.
*   **Extraction Method**: Python metadata queries (`audit_pcg_portfolio.py` and `audit_material_library.py`) outputting a `portfolio_stats_manifest.json` file.
*   **Captured Metrics**:
    *   Geometry: Vertex count, polygon count, UV channel count, and bounding box volume.
    *   Instancing: HISM instance counts per actor, total draw calls, and vertex memory sizes.
    *   PCG Density: Point counts, voxel dimensions, and scatter bounding scopes.

---

## 2. Design System Integration (Figma Mapping)

To automate page layout, the pipeline output files are mapped directly to components within the Figma Design System.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FIGMA DESKTOP ARTBOARD                          │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     HERO SHOWCASE (16:9 Frame)                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────┐  │
│  │      BREAKDOWN       │  │    MATERIAL SWATCH   │  │  SPEC TABLE  │  │
│  │   (Wireframe/UV)     │  │     (Sphere Grid)    │  │ (Stats JSON) │  │
│  └──────────────────────┘  └──────────────────────┘  └──────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.1 Grid System Mapping
*   **Desktop Canvas Grid**: Standard 12-column grid.
    *   Total Canvas Width: `1440px` (or `1920px` for high-res showcases).
    *   Gutters: `24px`.
    *   Margins: `80px` (outer padding).
*   **Responsive Spacing Grid**: 8px grid system for layout padding and margins:
    *   Outer Component Padding: `24px` (3 grid steps).
    *   Inner Element Spacing: `8px` (1 grid step) or `16px` (2 grid steps).

### 2.2 Typography Usage Mapping
Metadata variables from `docs.json` are synced directly to Figma Text Styles:

| Figma Text Style | Font Family | Size / Weight | Line Height | Target Metadata Key |
| :--- | :--- | :--- | :--- | :--- |
| **H1: Title** | *Outfit* | 48px / Bold | 1.2 (58px) | `{style_theme}` (e.g., "Zen Shrine Axis") |
| **H2: Heading** | *Inter* | 24px / Semi-Bold | 1.3 (32px) | `{world_root}` (e.g., "SurrealPlan_ZenRoji") |
| **Body: Text** | *Inter* | 16px / Regular | 1.5 (24px) | `{genome_summary}` (procedural description) |
| **Table: Label** | *Inter* | 14px / Regular | 1.4 (20px) | Metric Names (e.g., "Vertex Count") |
| **Table: Value** | *JetBrains Mono* | 14px / Medium | 1.4 (20px) | `{vertex_count}`, `{instances}`, etc. |

### 2.3 Component Mapping
Unreal Engine outputs map to Figma Component Library items:

*   **Hero Component (`HeroShowcase`)**:
    *   Figma Layout: Spans columns 1–12 (`1280px` width, `720px` height).
    *   Input: `Hero_*.png`. Fill mode: Aspect Ratio Crop.
*   **Breakdown Grid Component (`BreakdownGrid`)**:
    *   Figma Layout: Spans columns 1–6 (`628px` width).
    *   Inputs: Spawns two square sub-cards showing Lit vs. Wireframe side-by-side (`302px` each).
*   **Material Swatch Component (`MaterialSwatchCard`)**:
    *   Figma Layout: Spans columns 7–9 (`302px` width). Spawns an auto-layout card with a `150px` preview circle, parameter tags, and shadow-step descriptions.
    *   Inputs: Cell images extracted from `Swatch_*.png`.
*   **Specification Card (`SpecCardTable`)**:
    *   Figma Layout: Spans columns 10–12 (`302px` width). An auto-layout vertical table displaying engine metrics.
    *   Inputs: Values parsed from `stats.json`.

---

## 3. ArtStation Publishing Package

The final pipeline stage compiles a project zip folder prepared for ArtStation uploads:

1.  **Image Stack**:
    *   `01_Hero.jpg`: High-res, sRGB, Cine Camera render.
    *   `02_Breakdown_Wireframe.jpg`: Edge-visualizer render.
    *   `03_Breakdown_UVDensity.jpg`: Mapped UV density pass.
    *   `04_Material_Grid.jpg`: Spheres compilation.
2.  **Narrative Details**: A text file (`ArtStation_Draft.txt`) containing:
    *   Title: `Stylized Surreal Architecture — {style_theme} axis`
    *   Description: "Procedural geometry layout generated in Blender 5.1 using Style Genomes and snap taxonomies. Rendered in Unreal Engine 5.8 using Substrate Toon shaders and custom cell shading profiles. Foliage and rock distributions driven by programmatically built PCG graphs."
    *   Technical Stats: Polycounts, instance counts, and PCG density metrics.
