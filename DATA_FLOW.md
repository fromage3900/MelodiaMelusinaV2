# Technical Data Flow Specification — Environment Portfolio Platform

This document traces the data lifecycle, schema structures, and coordinate transformations across the five stages of the environment production pipeline.

---

## 1. End-to-End Data Pipeline

The diagram below traces the conversion of procedural geometry and styling data into final portfolio displays.

```
 [ Houdini Engine / HDAs ]  ──► FBX Geometries + Snap Snips
            │
            ▼ (FBX & JSON manifest export)
 [ Unreal Import Pipeline]  ──► Coordinate transformation (Z-up meters -> UE cm)
            │                  Spawns HISM actors and queries material hints
            ▼
 [ Substrate Materials  ]  ──► Samples textures, masks trim vertex colors (trim_id),
            │                  and accumulates roughness/emissive values
            ▼
 [ Active Scene Setup   ]  ──► Integrates Ultra Dynamic Sky and Post-Process outlines
            │
            ▼ (Capture Scene / Stats Audits)
 [ Portfolio Layer      ]  ──► Renders PNG images and compiles metadata JSON
            │
            ▼ (Figma Token API / Asset Upload)
 [ Figma / ArtStation   ]  ──► Populates design sheets and drafts project pages
```

---

## 2. Phase-by-Phase Technical Specifications

### Stage 1: Houdini Procedural Generation (Planned)
*   **Data Produced**:
    *   Modular mesh geometries (FBX format, meters, Z-up).
    *   Plan topologies (area coordinates, tagged vertices: `is_keep`, `is_gate`, `is_sacred`).
    *   Baked vertex colors mapping layout regions to trim indices.
*   **Data Schema**: Extends the `surreal_arch_world_v1` JSON structure:
    ```json
    {
      "format": "surreal_arch_world_v1",
      "style": "ZEN_SHRINE",
      "instance_count": 2,
      "instances": [
        {
          "role": "sacred",
          "lib": "_lib_HAIDEN",
          "transform": [ [1,0,0,0], [0,1,0,0], [0,0,1,0], [2.4, -1.2, 0.5, 1] ],
          "ue_material_hint": "sacred"
        }
      ]
    }
    ```

### Stage 2: Unreal Import Pipeline
*   **Coordinate Transformation**: Converts coordinates from Blender Z-up meters to Unreal left-handed cm:
    *   Location Translation:
        $$\begin{pmatrix} X_{ue} \\ Y_{ue} \\ Z_{ue} \end{pmatrix} = \begin{pmatrix} X_{blender} \times 100.0 \\ Y_{blender} \times 100.0 \\ Z_{blender} \times 100.0 \end{pmatrix}$$
    *   Rotation Conversion: Calculates yaw angle from Blender matrix inputs:
        $$\text{Yaw}_{ue} = \text{atan2}(M_{10}, M_{00}) \times \frac{180.0}{\pi}$$
*   **Material Matching**: Resolves `ue_material_hint` strings using the `ROLE_UE_HINTS` project settings:
    *   `sacred` $\rightarrow$ `/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_Karesansui`
    *   `wall` $\rightarrow$ `/Game/EnvSandbox/Materials/Instances/Environment/Stylized/MI_Trimsheet_HeavyWear`

### Stage 3: Substrate Toon Materials
*   **Mask Processing**: Shaders sample the mesh `trim_id` vertex color attribute to isolate trim textures.
*   **Accumulator Stack**: Accumulates albedo, normal offset, roughness additions, and emissive glints.
*   **BSDF Output**: Pipes outputs into the Substrate Toon BSDF, applying shadow ramps specified in `TP_Default` or `TP_Ornamental` profiles.

### Stage 4: Scene & Viewport Assembly
*   **Lighting Integration**: Ultra Dynamic Sky reads global time variables (e.g., `1750.0` for sunset sunset warmths).
*   **Post-Process Filters**: Scene viewports render cell outlines and storybook vine overlays onto custom depth buffers.

### Stage 5: Portfolio Output Layer
*   **Capture Engine**: Triggered by Monolith editor queries:
    *   `editor.capture_scene_preview` renders individual assets at `1920x1080`.
    *   `editor.capture_material_grid` compiles material instance swatches.
    *   `editor.capture_with_overlay` produces wireframe and UV density diagnostic sheets.
*   **Manifest Compiler**: Generates `portfolio_stats_manifest.json` collating geometric polygon metrics, HISM instance counts, and PCG density reports.
*   **Design/Publish Sync**: Transmits compiled metadata and screenshots to the Figma Token API to build portfolio layout sheets, while drafting ArtStation project uploads.
