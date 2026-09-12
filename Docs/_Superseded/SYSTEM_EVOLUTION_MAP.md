# System Evolution Map — Portfolio Package v2 Architecture

This document maps out the system evolution path from the minimal MVP prototype to the comprehensive **Portfolio Package v2 Architecture**, outlining the system changes and structural layers.

---

## 1. Architectural Evolution: MVP vs. v2

The v2 architecture introduces a higher layer of abstraction above the minimal MVP rendering output, translating raw engine data into semantic design tokens.

| System Layer | MVP State (Working Prototype) | v2 State (Next Abstraction Layer) |
| :--- | :--- | :--- |
| **Asset Tagging** | Basic file names and static folder paths. | Expanded taxonomic tags (Semantic Groups, LOD limits, Style taxonomy). |
| **PCG Scatter** | Point counts and volume boundary scale. | PCG graph metadata serialization (Voxel grids, clusters, density inputs). |
| **Material Registry** | Raw parameter lists and instance overrides. | **Material Passport System** (VRAM size, Substrate Toon curves, descriptions). |
| **Scene Documentation** | Level name and Camera transforms. | **Scene Breakdown Generator** (UDS parameters, Post-process outline stack). |
| **Figma Sync** | Drag-and-drop manual image importing. | **Figma Mapping Layer** (Automated JSON-to-template layout tokens mapping). |
| **Portfolio Output** | Uncompressed PNG screenshots. | **ArtStation Output Package** (Asset compile, narrative text, markup specs). |

---

## 2. Evolutionary Framework

```
   ┌────────────────────────────────────────┐
   │             MVP CORE LAYER             │
   │    Scene Metadata, Renders, Folders    │
   └───────────────────┬────────────────────┘
                       │
                       ▼ (System Evolution)
   ┌────────────────────────────────────────┐
   │             v2 SPEC LAYER              │
   ├────────────────────────────────────────┤
   │  - Asset Taxonomic Tagging             │
   │  - Material Passports & VRAM Stats     │
   │  - PCG Graph Scatter Configurations   │
   │  - Scene Documentation Generators      │
   └───────────────────┬────────────────────┘
                       │
                       ▼ (Sync & Publish)
   ┌────────────────────────────────────────┐
   │         DESIGN PRESENTATION LAYER      │
   │      Figma Token Sync / ArtStation     │
   └────────────────────────────────────────┘
```

## 3. Key Subsystem Progressions

1.  **From Raw Metadata to Material Passports**: Rather than dumping simple floats, the Material Passport compiles complete shader histories, tracking master parentage, parameter groups, VRAM resolutions, and Substrate Toon profile bounds into a design-ready specification sheet.
2.  **From Point Counts to PCG Graph Schemas**: v2 serializes the actual rules of the PCG scatter system, exporting spacing constraints, density thresholds, and static mesh collections to explain the procedural logic in the portfolio.
3.  **From Image Exports to Figma Layout Tokens**: Translates renders and metrics into JSON-based tokens that drive auto-layouts, font headings, margins, and component configurations directly inside the design templates.
