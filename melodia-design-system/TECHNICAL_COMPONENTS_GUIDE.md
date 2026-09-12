# Technical Breakdown Components — Usage Guide

**Created:** 2026-06-25  
**Purpose:** HTML components for technical portfolio presentations  
**Location:** `wix/` folder

---

## Overview

These components are designed for technical portfolio presentations where clarity and data completeness are prioritized over decoration. They help technical directors quickly assess:

- Data availability status
- PCG graph metadata
- Performance metrics
- Process workflows
- Missing data indicators

---

## 1. Badge/DataStatus (`badge-data-status.html`)

**Purpose:** Indicates data availability for a section or dataset

**Use Cases:**
- Section headers to show if data is complete
- Asset passport to indicate missing fields
- Material breakdown to show channel availability

**Themes:**
- `present` — Green, data is complete
- `missing` — Red, data is absent
- `partial` — Amber, data is incomplete

**How to Use:**
```javascript
var DATA = {
  status: "partial",  // "present", "missing", "partial"
  label: "Data Status"
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: auto (fits content)

**Example Placement:**
- Next to section titles
- Above incomplete data cards
- In header of technical documentation

---

## 2. Placeholder/DataMissing (`placeholder-data-missing.html`)

**Purpose:** Placeholder for missing renders or images

**Use Cases:**
- Missing hero renders
- Missing breakdown images
- Missing material channel renders
- Missing PCG graph visualizations

**How to Use:**
```javascript
var DATA = {
  dataType: "Render",
  message: "No render data available"
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: Set desired dimensions (e.g., 400 × 300px)

**Customization:**
- `dataType`: Type of missing data (Render, Material, Graph, etc.)
- `message`: Specific message explaining what's missing

**Example Placement:**
- Replace Image/Plate when render data is missing
- Use in grid layouts where some images are missing
- Placeholder for future content

---

## 3. Info/GraphMetadata (`info-graph-metadata.html`)

**Purpose:** Display PCG graph technical details

**Use Cases:**
- PCG graph documentation
- Process breakdown sections
- Technical workflow explanations

**How to Use:**
```javascript
var DATA = {
  title: "PCG Graph",
  role: "foliage",
  path: "/Game/EnvSandbox/PCG/Universal/PCG_FoliageDensity",
  voxel: null,
  phase: null,
  features: {
    density_filter: true,
    surface_sampler: false,
    passthrough: false,
    pcgex_exclusion: false,
    pcgex_candidate: null
  }
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: ~ 360 × auto

**Features Displayed:**
- Graph path (shortened to filename)
- Role (foliage, rock, wall, etc.)
- Voxel size (if present)
- Phase (if present)
- Active features as tags

**Example Placement:**
- Below PCG graph visualization
- In Process Breakdown sections
- Technical documentation pages

---

## 4. Tag/PCGFeature (`tag-pcg-feature.html`)

**Purpose:** Tag for PCG-specific features

**Use Cases:**
- Feature indicators in PCG graph cards
- Process step annotations
- Technical capability tags

**How to Use:**
```javascript
var DATA = {
  feature: "Density Filter",
  active: true
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: auto (fits content)

**States:**
- `active: true` — Highlighted with gold border
- `active: false` — Neutral styling

**Common Features:**
- Density Filter
- Surface Sampler
- Passthrough
- PCGEx Exclusion
- PCGEx Candidate

**Example Placement:**
- Inside Info/GraphMetadata cards
- Clustered in process breakdowns
- Feature lists in technical docs

---

## 5. Layout/ProcessFlow (`layout-process-flow.html`)

**Purpose:** Horizontal process flow visualization

**Use Cases:**
- PCG graph sequence
- Asset pipeline stages
- Material workflow steps

**How to Use:**
```javascript
var DATA = {
  steps: [
    {num: 1, title: "Exclusion"},
    {num: 2, title: "Foliage"},
    {num: 3, title: "Rock"},
    {num: 4, title: "Wall"}
  ]
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: ~ 800 × 120px (adjust as needed)

**Customization:**
- Add/remove steps as needed
- Adjust step titles
- Step numbers auto-increment

**Example Placement:**
- Top of Process Breakdown pages
- Technical documentation headers
- Pipeline overview sections

---

## 6. Chart/Bar (`chart-bar.html`)

**Purpose:** Simple bar chart for performance metrics

**Use Cases:**
- Triangle count visualization
- Draw calls display
- Material count comparison
- Texture count breakdown

**How to Use:**
```javascript
var DATA = {
  label: "Triangle Count",
  value: 482318,
  max: 1000000,
  unit: "triangles"
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: ~ 400 × 120px

**Customization:**
- `label`: Metric name
- `value`: Current value
- `max`: Maximum value for bar calculation
- `unit`: Unit label

**Example Placement:**
- Performance sections
- Asset breakdowns
- Technical documentation

---

## 7. Card/Performance (`card-performance.html`)

**Purpose:** Performance stats card with multiple metrics

**Use Cases:**
- Scene performance overview
- Asset performance breakdown
- Material performance stats

**How to Use:**
```javascript
var DATA = {
  triangleCount: 482318,
  drawCalls: 184,
  materialCount: 12,
  textureCount: 36,
  textureResolution: "4K"
};
```

**Wix Setup:**
1. Editor → Add (+) → Embed Code → Embed HTML
2. Paste file
3. Size: ~ 360 × auto

**Metrics Displayed:**
- Triangles (formatted with commas)
- Draw Calls
- Materials
- Textures
- Resolution (if present)

**Null Handling:**
- Null values display as "TBD" in red italic

**Example Placement:**
- Hero page alongside Asset Passport
- Environment breakdown sections
- Technical documentation

---

## Integration with Portfolio Package

These components are designed to work with `portfolio_package.json`:

**Badge/DataStatus:**
```javascript
var DATA = {
  status: portfolio_package.assets.length > 0 ? "present" : "missing",
  label: "Asset Data"
};
```

**Card/Performance:**
```javascript
var DATA = {
  triangleCount: portfolio_package.stats.triangle_count,
  drawCalls: portfolio_package.stats.draw_calls,
  materialCount: portfolio_package.stats.material_count,
  textureCount: portfolio_package.stats.texture_count,
  textureResolution: portfolio_package.stats.texture_resolution
};
```

**Info/GraphMetadata:**
```javascript
var DATA = portfolio_package.pcg.graphs.foliage;
```

**Layout/ProcessFlow:**
```javascript
var DATA = {
  steps: Object.keys(portfolio_package.pcg.graphs).map((k, i) => ({
    num: i + 1,
    title: k
  }))
};
```

---

## Color Palette

All components use Melodia design system colors:

**Status Colors:**
- Present: `#5E8B7E` (sage green)
- Missing: `#A85751` (terracotta red)
- Partial: `#B8862F` (amber)

**UI Colors:**
- Surface: `#FFFFFF` (white)
- Border: `#E3DACE` (ivory border)
- Text primary: `#241B2E` (plum)
- Text secondary: `#6E6080` (slate)
- Gold accent: `#C9A86A` (champagne gold)

---

## Typography

All components use IBM Plex Mono (technical/metadata):

- Labels: 10-11px, uppercase, letter-spacing 0.08-0.12em
- Values: 11-14px, tabular figures for numbers
- Null values: Red italic, "TBD"

---

## Responsive Behavior

**Desktop (1440px):**
- Full component widths
- Process flow: horizontal
- Charts: full width

**Tablet (834px):**
- Components scale down
- Process flow: may wrap if too many steps

**Mobile (390px):**
- Components stack vertically
- Process flow: consider vertical variant
- Charts: full width

---

## File Locations

All components in: `c:\Users\froma\Downloads\melodia-design-system\wix\`

- `badge-data-status.html`
- `placeholder-data-missing.html`
- `info-graph-metadata.html`
- `tag-pcg-feature.html`
- `layout-process-flow.html`
- `chart-bar.html`
- `card-performance.html`

---

## Best Practices

1. **Use Badge/DataStatus** on every section header to show data completeness
2. **Use Placeholder/DataMissing** instead of blank spaces when data is missing
3. **Use Info/GraphMetadata** for all PCG graph documentation
4. **Use Card/Performance** for performance stats (better than generic Card/Info)
5. **Use Layout/ProcessFlow** to show workflow relationships
6. **Use Chart/Bar** for key performance metrics (triangles, draw calls)
7. **Keep data types consistent** (numbers as numbers, strings as strings)
8. **Handle null values gracefully** (show "TBD" instead of breaking)

---

## Technical Director Reading Path

These components support the recommended reading order:

1. **Hero Page** → Card/Performance + Badge/DataStatus
2. **Process Breakdown** → Layout/ProcessFlow + Info/GraphMetadata + Tag/PCGFeature
3. **Asset Breakdown** → Card/Performance + Badge/DataStatus
4. **Material Presentation** → Badge/DataStatus + Placeholder/DataMissing (if incomplete)
5. **Technical Documentation** → All components as needed

---

## Support

For questions about component usage:
- Refer to `PORTFOLIO_MAPPING_RULES.md` for mapping logic
- Refer to `DESIGN_SYSTEM.md` for design system details
- All HTML files have inline comments
