# Figma Design System — Component Specifications

**Version:** 1.0 · 2026-06-30  
**System:** melodia-design-system  
**Data contract:** [figma_token_bridge.schema.json](figma_token_bridge.schema.json)

This document is the canonical spec for every component in the portfolio design system. Build or verify each component in Figma against these specs. All variable bindings reference token names defined in [figma_token_bridge_extension.json](figma_token_bridge_extension.json).

> [!NOTE]
> **Grid system:** 12-column, 1440px canvas, 24px gutters, 80px outer margins.  
> **Spacing:** 8px base grid (8 / 16 / 24 / 32 / 48px increments).  
> **Typography:** Outfit for H1, Inter for all other text, JetBrains Mono for metric values.

---

## Page Templates

### `Page_EnvironmentShowcase`
Primary portfolio artboard — one per environment.

```
┌─────────────────────────────────────────────────────── 1440px ──┐
│  [HeroShowcase ─────────────────────────── cols 1-12 ──────────] │  row 1
│  [BreakdownGrid ── cols 1-6] [MaterialSwatchCard 7-9] [Spec 10-12]  row 2
│  [StyleGenomeAxisDiagram ─ cols 1-9] [NiagaraPreviewSlot 10-12] │  row 3
└─────────────────────────────────────────────────────────────────┘
```

### `Page_MaterialLibrary`
Material-only deep-dive page.

```
┌─────────────────────────────────────────────────────── 1440px ──┐
│  [HeroShowcase — sphere on neutral bg ─── cols 1-12 ───────────] │
│  [SwatchCard cols 1-3] [SwatchCard 4-6] [SwatchCard 7-9] [SwatchCard 10-12]│
│  [TrimLayoutCard ─────────────── cols 1-8] [AudioReactivitySpec 9-12] │
└─────────────────────────────────────────────────────────────────┘
```

### `Page_PCGSystem`
Procedural scatter showcase.

```
┌─────────────────────────────────────────────────────── 1440px ──┐
│  [HeroShowcase — top-down ortho PCG screenshot ─── cols 1-12 ──] │
│  [PCGDensityHeatmap ─── cols 1-6] [LandscapeSplatCard 7-9] [Spec 10-12] │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

---

### `HeroShowcase`
**Status:** Verify exists  
**Grid:** Cols 1–12 · Width: 1280px · Height: 720px  
**Layer structure:**
- `[bg_fill]` — Rectangle, `fills: slot/hero_image`, mode: Fill (crop to aspect ratio)
- `[overlay_gradient]` — Rectangle overlaid, height 30% from bottom, linear gradient black→transparent
- `[title_lockup]` — Auto-layout frame, bottom-left, 24px from edges
  - `[H1_scene_title]` — Outfit 48px Bold, white, text: `token/scene_title`
  - `[subtitle_style]` — Inter 20px Regular, white 70% opacity, text: `token/style_family`
- `[engine_badge]` — Chip top-right: Inter 12px, text: `token/engine_version`

**States:** `empty` (gradient placeholder, italic hint text), `loaded` (real render)  
**Variable bindings:**

| Token | Layer | Property |
|-------|-------|----------|
| `slot/hero_image` | `[bg_fill]` | Fill image |
| `token/scene_title` | `[H1_scene_title]` | Text content |
| `token/style_family` | `[subtitle_style]` | Text content |
| `token/engine_version` | `[engine_badge]` | Text content |

---

### `BreakdownGrid`
**Status:** Verify exists  
**Grid:** Cols 1–6 · Width: 628px · Height: 360px  
**Layer structure:**
- `[lit_cell]` — 302×360px, fills: `slot/breakdown_lit`
- `[wire_cell]` — 302×360px, fills: `slot/breakdown_wire`
- `[label_lit]` — Inter 12px, top-left: "Lit Pass"
- `[label_wire]` — Inter 12px, top-left: "Wireframe"
- `[vc_badge_group]` — Auto-layout overlay for vertex color badges (see §Vertex Color Extension)

**Variable bindings:**

| Token | Layer | Property |
|-------|-------|----------|
| `slot/breakdown_lit` | `[lit_cell]` | Fill image |
| `slot/breakdown_wire` | `[wire_cell]` | Fill image |

**Vertex Color Extension:** A `vc_badge` chip component (20×20px circle, color-coded per trim_id, number label, JetBrains Mono 10px). Positioned absolutely over the lit_cell. Populated manually from `trim_id` vertex masking data.

---

### `MaterialSwatchCard`
**Status:** Verify exists  
**Grid:** Cols 7–9 · Width: 302px · Auto-height  
**Layer structure (auto-layout vertical, 16px gap):**
- `[preview_circle]` — 150×150px ellipse clip, fill: `list/swatch_images[n]`
- `[material_name]` — Inter 16px SemiBold, text: `list/swatch_labels[n]`
- `[param_tags]` — Horizontal wrap of `Tag` chip components (text: parameter key names)
- `[shadow_step_desc]` — Inter 12px Regular, muted: SSS or toon shadow description
- `[card_bg]` — Rounded rectangle, 8px radius, bg color: surface-card token

**States:** `empty`, `loaded`, `highlight` (hover: border stroke 1.5px accent)  
**Variable bindings:** Repeat component via instance swap for each material in `list/swatch_images`.

---

### `SpecCardTable`
**Status:** Verify exists  
**Grid:** Cols 10–12 · Width: 302px · Auto-height  
**Layer structure (auto-layout vertical, 0px gap, dividers):**
- Header row: Inter 14px Bold "Engine Stats"
- 5 data rows (fixed), each: `[row_label]` Inter 14px Regular + `[row_value]` JetBrains Mono 14px

**Fixed rows:**

| Row Label | Token Binding |
|-----------|--------------|
| Triangle Count | `spec/tris` |
| Draw Calls | `spec/draw_calls` |
| HISM Instances | `spec/hism_instances` |
| PCG Graphs | `spec/pcg_graphs` |
| Shader Complexity | `spec/shader_complexity` |

---

### `StyleGenomeAxisDiagram` ⭐ NEW
**Status:** Build  
**Grid:** Cols 1–9 · Width: 942px · Height: 160px  
**Purpose:** Displays the procedural architectural axis as a horizontal node sequence (addresses [FIGMA_LAYOUT_GAPS.md §3](file:///C:/EnvironmentPortfolio/BS_GodFile/FIGMA_LAYOUT_GAPS.md))

**Layer structure:**
- `[axis_track]` — Horizontal auto-layout, 24px gap between nodes
- `[GenomeAtomCard]` × N — Repeating node component:
  - `[atom_icon]` — 48×48px placeholder rectangle (fill: genome-type color token)
  - `[atom_label]` — Inter 14px SemiBold, text: `genome_axis_steps[n].label`
  - `[snap_count_badge]` — Chip, Inter 10px, text: `genome_axis_steps[n].snap_count + " snaps"`
- `[connector_arrow]` — Between each node: SVG right-arrow, stroke 1px accent color
- `[axis_label]` — Caption below track: Inter 12px, text: "Style Genome Axis"

**Populated from:** `list/genome_axis_steps` (source: `export_genome_axis.py`)

**Genome color map (atom_icon fills):**

| Genome Type | Fill Color |
|-------------|------------|
| `gate` | `#C4A882` |
| `path` | `#8BAE8A` |
| `corridor` | `#7A9BBF` |
| `platform` | `#B5846A` |
| `courtyard` | `#C2A87E` |

---

### `PCGDensityHeatmap` ⭐ NEW
**Status:** Build  
**Grid:** Cols 1–6 · Width: 512px · Height: 512px  
**Purpose:** Visualizes scatter density top-down (addresses [FIGMA_LAYOUT_GAPS.md §3](file:///C:/EnvironmentPortfolio/BS_GodFile/FIGMA_LAYOUT_GAPS.md))

**Layer structure:**
- `[heatmap_fill]` — 512×512px rectangle, fill: `slot/pcg_heatmap_image`
- `[exclusion_labels]` — Absolute-position text group:
  - `[label_path]` — Inter 11px white, positioned over path exclusion zone
  - `[label_pond]` — Inter 11px white, positioned over pond exclusion zone
  - `[label_torii]` — Inter 11px white, positioned over torii exclusion zone
- `[legend]` — Bottom-left legend strip: low→high density gradient bar + labels
- `[scale_indicator]` — Bottom-right: "N" arrow (compass) + scale text

**Populated from:** `slot/pcg_heatmap_image` (source: `audit_pcg_heatmap.py`)

---

### `TrimLayoutCard` ⭐ NEW
**Status:** Build  
**Grid:** Cols 1–8 · Width: 824px · Height: 128px  
**Purpose:** Visualizes non-uniform trim sheet zone layout (addresses [FIGMA_LAYOUT_GAPS.md §1](file:///C:/EnvironmentPortfolio/BS_GodFile/FIGMA_LAYOUT_GAPS.md))

**Layer structure:**
- `[zone_strip]` — Horizontal auto-layout, zones are variable-width children:
  - `[TrimZone]` component (width proportional to `width_m`):
    - `[zone_bg]` — Rectangle, fill: zone type color (Heavy=#8B7355, Mid=#7A9BBF, Filigree=#C2C2A3)
    - `[trim_id_label]` — JetBrains Mono 10px Bold, white, top-center: `trim_zones[n].trim_id`
    - `[width_label]` — Inter 10px, bottom-center: `trim_zones[n].width_m + "m"`
    - `[swatch_preview]` — 32×32px image inset (material swatch from `swatch_images` if available)
- `[zone_ruler]` — Thin rule above strip with cm tick marks

**Populated from:** `list/trim_zones` (source: material parameter tables)

---

### `NiagaraPreviewSlot` ⭐ NEW
**Status:** Build  
**Grid:** Cols 10–12 · Width: 302px · Height: 302px  
**Purpose:** Holds a Niagara particle still, GIF, or video reference (addresses [FIGMA_LAYOUT_GAPS.md §2](file:///C:/EnvironmentPortfolio/BS_GodFile/FIGMA_LAYOUT_GAPS.md))

**Layer structure:**
- `[preview_bg]` — 302×302px dark rectangle (#0D0D0D)
- `[preview_fill]` — 302×302px rectangle, fill: `slot/niagara_preview`
- `[play_badge]` — Optional: 32×32px circle with ▶ icon (shown when video URL detected)
- `[system_label]` — Inter 12px, bottom-left: Niagara system name (manual)
- `[fps_badge]` — Chip top-right: JetBrains Mono 10px, text: "30fps" or "static"

**Note:** Figma does not support video embeds natively. For animated previews, export as GIF from Movie Render Graph and link as image. For review sessions, embed Loom/YouTube link in a Figma prototype hotspot.

---

### `LandscapeSplatCard` ⭐ NEW
**Status:** Build  
**Grid:** Cols 7–9 · Width: 302px · Height: 302px  
**Purpose:** Displays 4-layer painted landscape weight distribution (addresses [FIGMA_LAYOUT_GAPS.md §3](file:///C:/EnvironmentPortfolio/BS_GodFile/FIGMA_LAYOUT_GAPS.md))

**Layer structure (2×2 grid, auto-layout):**
- Four `[SplatLayerCell]` components (each 143×143px with 4px gap):
  - `[texture_swatch]` — 64×64px image, fill: `splat_weights[n].texture_path`
  - `[layer_name]` — Inter 13px SemiBold, text: `splat_weights[n].layer` (e.g. "Rock")
  - `[weight_bar_bg]` — 120×6px bar background
  - `[weight_bar_fill]` — Variable width fill (0–100% of bar width = `weight_pct`)
  - `[pct_label]` — JetBrains Mono 10px: `splat_weights[n].weight_pct + "%"`

**Populated from:** `list/splat_weights` (source: `audit_landscape_layers.py`)

---

### `AudioReactivitySpec` ⭐ NEW
**Status:** Build (extends `SpecCardTable`)  
**Grid:** Cols 9–12 · Width: 302px · Auto-height  
**Purpose:** Displays material audio reactivity properties (addresses [FIGMA_LAYOUT_GAPS.md §2](file:///C:/EnvironmentPortfolio/BS_GodFile/FIGMA_LAYOUT_GAPS.md))

**Additional rows (appended after standard SpecCardTable rows):**

| Row Label | Description |
|-----------|-------------|
| MPC Channel | `MPC_Portfolio_Audio` channel index |
| Emissive Pulse Min | Min emissive multiplier |
| Emissive Pulse Max | Max emissive multiplier |

**Populated from:** Manual parameter table extracted from `MPC_Portfolio_Audio` asset (no automated path yet; add to `capture_material_previews.py` in a future pass).

---

## Typography Scale

| Style Name | Font | Size | Weight | Line Height | Use |
|-----------|------|------|--------|-------------|-----|
| H1/Title | Outfit | 48px | Bold | 1.2 | HeroShowcase title |
| H2/Heading | Inter | 24px | SemiBold | 1.3 | Section headers |
| Body | Inter | 16px | Regular | 1.5 | Genome summaries |
| Table/Label | Inter | 14px | Regular | 1.4 | Spec row labels |
| Table/Value | JetBrains Mono | 14px | Medium | 1.4 | Metric values |
| Caption | Inter | 12px | Regular | 1.4 | Sub-labels, axis captions |
| Micro | JetBrains Mono | 10px | Bold | 1.2 | Trim IDs, VC badges |

---

## Color Tokens (add to design system)

| Token Name | Hex | Use |
|-----------|-----|-----|
| `surface-bg` | `#0A0A0F` | Page background |
| `surface-card` | `#13131A` | Component card fill |
| `surface-elevated` | `#1C1C26` | Hover / active card |
| `accent-primary` | `#7EB4C8` | Arrows, highlights, progress |
| `accent-warm` | `#C4A882` | Gate atom, trim heavy |
| `text-primary` | `#F0EDE8` | H1, headings |
| `text-secondary` | `#9D9B96` | Captions, sub-labels |
| `text-value` | `#A8D8B0` | Metric values (mono) |
| `stroke-divider` | `#2A2A36` | Table row dividers |
