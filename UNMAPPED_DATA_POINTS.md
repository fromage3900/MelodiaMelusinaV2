# System Gap Analysis — Unmapped Data Points

This document identifies metadata fields, parameter values, and system configurations that exist within the **Blender 5.1** and **Unreal Engine 5.8** workspace but are currently missing from the portfolio manifest files and Figma templates.

---

## 1. Missing Architectural & Geometry Metadata

*   **Style Genome Snap Vectors**: The snap positions, bounding ranges, and kit constraints defined in [architectural_atoms.yaml](file:///g:/EnvironmentPortfolio/BS_GodFile/deploy/surreal_os/schema/architectural_atoms.yaml) are not exported to the `{WorldRoot}.world.json` manifest. As a result, Figma templates cannot display snap-connection details.
*   **Static Mesh LOD Configurations**: Polygon and vertex counts are analyzed at LOD 0, but LOD 1/2/3 vertex counts and transition screen sizes are not captured by `portfolio_stats_manifest.json`, leaving mesh optimization metrics unmapped in Figma.
*   **Vertex Attribute Channels**: The presence of the `trim_id` vertex color attribute is baked, but details regarding vertex color bit depth and face-mapping distributions are not exported.

---

## 2. Missing Material & Shader Metadata

*   **Parameter Descriptions & Descriptions**: Tooltips and descriptions defined programmatically in [setup_master_universal.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_master_universal.py) (e.g., `PastelLift` or `StarMap`) are not serialized to the material audit JSON files. Consequently, Figma swatch cards cannot display descriptions for parameter dials.
*   **Substrate Node Properties**: The active toon profile preset parameters (shadow steps, ramps) are set inside `/Game/EnvSandbox/Materials/ToonProfiles/` but are omitted from the export, leaving the Figma specifications table without toon profile data.
*   **Texture Resolution & Memory Footprints**: Material audit scripts list texture paths but do not query texture resolution ($512$, $1024$, $2048$) or VRAM footprints, leaving texture optimization stats unmapped.

---

## 3. Missing Scene & Environment Metadata

*   **Ultra Dynamic Sky Parameters**: Lighting attributes (time of day, solar angle, cloud density, light intensity) are configured by `ensure_uds_actors` but are not captured in level reports, leaving environment cards without setup metrics.
*   **Post-Process Settings**: Blend weights, outline thicknesses, and dither settings for `M_PP_ToonOutline` are not serialized, preventing Figma from displaying the post-process configuration.
*   **PCG Seed Profiles**: Spacing radius parameters and random seeds are defined in [pcg_portfolio_standards.py](file:///g:/EnvironmentPortfolio/BS_GodFile/Content/Python/pcg_portfolio_standards.py) but are not recorded in the layout output files.
