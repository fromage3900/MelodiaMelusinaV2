# System Gap Analysis — Unreal Capture Gaps

This document identifies limitations and missing visual capture capabilities in the **Unreal Engine 5.8** rendering and preview pipeline.

---

## 1. Missing Shading & Render Pass Captures

*   **Detail Lighting Mode**: Monolith's `editor.capture_with_overlay` supports `wireframe`, `normals`, `uv_density`, and `shader_complexity` modes, but lacks a **Detail Lighting** (lit without diffuse albedo) capture mode, which is required for sculptural model showcases.
*   **Unlit / Albedo-Only Pass**: There is no direct command to capture unlit flat albedo passes, preventing the export of base texture maps for PBR breakdown sheets.
*   **Buffer Visualization Exports**: G-buffer outputs (Roughness, Metallic, Ambient Occlusion, Specular) cannot be rendered and saved to disk automatically, making it difficult to generate PBR channel breakdowns.

---

## 2. Level Viewport Framing Limitations

*   **Active Level Actor Capture**: Monolith's capture actions (like `capture_scene_preview`) render assets inside private, isolated preview worlds. There is no command to capture static meshes in their **placed level context** (e.g., framing a torii gate actor inside `L_SakuraPath` under level lighting).
*   **CineCamera Viewport Binding**: Viewport screenshots do not bind to cinematic camera aspect ratios or depth-of-field settings, leading to framing mismatches between editor screenshots and cinematic renders.

---

## 3. Specialist Preview Limitations

*   **Translucent Water Displacement**: Previewing `M_Water_Master_Grand_v6` inside a private preview scene on a simple sphere or plane ignores wave displacement and shoreline depth-based color fades, as there is no floor mesh or distance field data in the isolated world.
*   **Post-Process Material Overlay**: Capturing individual assets in private worlds ignores level-global post-process materials (like `M_PP_ToonOutline`), rendering previews without Toon outlines.
*   **Niagara Particle State Capture**: Niagara previews require arbitrary seek warmups (`seek_time`) to capture sprite layouts, which does not guarantee consistent particle distributions for loops.
