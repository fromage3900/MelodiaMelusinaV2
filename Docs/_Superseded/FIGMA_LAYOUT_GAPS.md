# System Gap Analysis — Figma Layout Gaps

This document identifies missing component templates, layout structures, and design representations within the **Figma Design System** required to display the outputs of the production pipeline.

---

## 1. Missing Trim Sheet Representations

*   **Non-Uniform Trim Layout Guides**: The Figma Design System lacks responsive layout containers to represent non-uniform trimsheets. It cannot map a mixed trim layout (e.g., $4\text{m}$ heavy wear borders next to $1\text{m}$ filigree trims) onto a visual grid.
*   **Vertex Color Identifier Indicators**: There are no design elements to overlay `trim_id` vertex index indicators onto mesh breakdown cards, making it difficult to show how geometries map to trim zones.

---

## 2. Missing Particle & Dynamic Visualizers

*   **Niagara Animation Support**: Figma components only support static 1:1 image slots. It lacks layout frames or components for animated preview loops (like Sakura leaf shimmer or waterfall sheets) or flipbook atlas sheets.
*   **Audio Reactivity Bands**: The Figma specification cards have no visual design components to display material audio reactivity properties, such as emissive pulse ranges linked to `MPC_Portfolio_Audio` channels.

---

## 3. Missing Procedural & System Layouts

*   **Structural Axis Trees**: There are no Figma component structures designed to represent sequential room plans (e.g., the layout path: Torii gate $\rightarrow$ Sando $\rightarrow$ Kairo $\rightarrow$ Haiden). This makes it difficult to show the output of Style Genomes.
*   **Landscape paint Layer Splat Cards**: Figma lacks components to visualize 4-layer painted landscape splat weights (Rock, Grass, Mud, Path), preventing the display of paint coverage statistics.
*   **PCG Density Heatmaps**: The spec cards lack components to show PCG scatter distributions and density profiles visually.
