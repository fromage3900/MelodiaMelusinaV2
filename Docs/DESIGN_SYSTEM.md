# Environment Portfolio Design System

**Source of Truth for Portfolio Generation**

This document is the single source of truth for the Environment Portfolio Platform design system. It defines the typography, grid, spacing, components, and layouts that all portfolio artifacts must follow. The system is designed to be populated automatically by the Unreal Engine project via the pipeline defined in `PORTFOLIO_PIPELINE.md`.

---

## 1. Brand Foundations

### 1.1 Design Philosophy
**North Star:** Premium fantasy artbook meets professional technical documentation.

**Inspiration:** HoYoverse celestial UI (Genshin Impact / Honkai: Star Rail) fused with luxury editorial layout. The system balances:
- HoYoverse: Astral starfields, luminous gold filigree, ornate-but-restrained framing, constellation systems
- Luxury Editorial: Fashion-book grids, high-contrast serifs, generous whitespace

### 1.2 Pillars (Priority Order)
1. **Clarity** — Information legibility is never sacrificed for atmosphere
2. **Technical expertise** — Numbers, specs, and process read as authoritative
3. **Craftsmanship** — Every edge, rule line, and margin is intentional
4. **Elegance** — Restraint, generous whitespace, high typographic contrast
5. **Premium quality** — Print-grade finish; feels like a collector artbook
6. **Magical atmosphere** — Celestial accents, never costume fantasy
7. **Professionalism** — A studio could ship documentation in this system

**Governing Rule:** Ornamentation enhances information; it never competes with it.

### 1.3 Visual Motifs (Use Sparingly)
All motifs rendered as **thin gold or plum linework**, never filled blobs:

- **Eight-point star** (✸) — Signature mark (HoYoverse-leaning astral burst)
- **Four-point star** (✦) — Secondary sparkle: list bullets, divider centers, spec markers
- **Constellation / star-chart patterns** — Faint connected-dot lines as page-corner accents, title backplates (opacity ≤ 12%)
- **Ornate gold corner frames** — HoYoverse-style filigree brackets framing hero plates only
- **Thin celestial linework** — 1px hairlines, often with a single star node
- **Gold rule lines** — 1px champagne-gold rules separate content and frame headers
- **Luminous glow** — Soft outer glow (gold or astral) reserved for brand mark and one hero element per view

**Density Budget:** No more than **3 motif instances** on working documentation pages; up to 6 on hero/cover pages.

---

## 2. Color System

### 2.1 Primitive Palette
Base colors never used directly in designs.

| Token | Hex | Note |
|-------|-----|------|
| `ivory/50` | `#FCFBF8` | Moonlight White — purest surface |
| `ivory/100` | `#F7F4EF` | Ivory — default paper |
| `ivory/200` | `#EFEAE1` | Sunken / subtle fill |
| `ivory/300` | `#E3DACE` | Hairline on ivory |
| `plum/500` | `#6E6080` | Muted plum (disabled, faint) |
| `plum/600` | `#463A54` | Plum mid |
| `plum/700` | `#2E2438` | Plum deep |
| `plum/800` | `#241B2E` | Midnight Plum — primary dark |
| `plum/900` | `#1C1426` | Darkest, dark-mode base |
| `gold/100` | `#F0E6D2` | Gold tint fill |
| `gold/300` | `#DDC79B` | Gold light |
| `gold/500` | `#C9A86A` | Champagne Gold — accent / rules |
| `gold/700` | `#A7884E` | Gold text (AA on ivory) |
| `lavender/100` | `#E8E4F2` | Lavender tint |
| `lavender/300` | `#C2BAE0` | Lavender light |
| `lavender/500` | `#9F94C6` | Lavender — secondary accent |
| `sakura/100` | `#F5E8EA` | Sakura tint |
| `sakura/300` | `#E7C9CE` | Dusty Sakura — tertiary accent |
| `sakura/500` | `#D6A9B0` | Sakura saturated (rare) |
| `slate/200` | `#D5D8DE` | Border default |
| `slate/300` | `#AEB4BF` | Border strong |
| `slate/400` | `#828A98` | Text tertiary |
| `slate/500` | `#5A6170` | Slate Grey — text secondary |
| `slate/700` | `#3C414B` | Slate deep |
| `astral/100` | `#E5EAF5` | Astral tint (light) |
| `astral/300` | `#8AA9D6` | Astral light |
| `astral/500` | `#3C5C9E` | Astral Blue — HoYoverse night accent |
| `astral/700` | `#26365E` | Deep astral (dark surface tone) |
| `astral/900` | `#141A30` | Astral Night — dark-mode base |
| `iris/100` | `#ECE6F4` | Iris tint |
| `iris/300` | `#A99AD0` | Iris light |
| `iris/500` | `#6E5AA6` | Iris/Amethyst — Honkai-leaning violet accent |
| `status/success` | `#5E8B7E` | Muted sage |
| `status/warning` | `#B8862F` | Aged amber |
| `status/error` | `#A85751` | Muted terracotta |
| `status/info` | `#6B7CA8` | Muted slate-blue |

### 2.2 Semantic Tokens (Light Mode — Ivory Editorial)
| Semantic Token | Primitive |
|----------------|-----------|
| `color/surface/base` | `ivory/100` |
| `color/surface/raised` | `ivory/50` |
| `color/surface/sunken` | `ivory/200` |
| `color/surface/inverse` | `plum/800` |
| `color/text/primary` | `plum/800` |
| `color/text/secondary` | `slate/500` |
| `color/text/tertiary` | `slate/400` |
| `color/text/inverse` | `ivory/50` |
| `color/text/accent` | `gold/700` |
| `color/border/subtle` | `ivory/300` |
| `color/border/default` | `slate/200` |
| `color/border/strong` | `slate/300` |
| `color/accent/primary` | `gold/500` |
| `color/accent/secondary` | `lavender/500` |
| `color/accent/tertiary` | `sakura/300` |
| `color/accent/astral` | `astral/500` |
| `color/accent/iris` | `iris/500` |
| `color/rule/gold` | `gold/500` |
| `color/feedback/success` | `status/success` |
| `color/feedback/warning` | `status/warning` |
| `color/feedback/error` | `status/error` |
| `color/feedback/info` | `status/info` |

### 2.3 Semantic Tokens (Dark Mode — Astral Night)
| Semantic Token | Primitive |
|----------------|-----------|
| `color/surface/base` | `astral/900` |
| `color/surface/raised` | `astral/700` |
| `color/surface/sunken` | `plum/900` |
| `color/surface/inverse` | `ivory/100` |
| `color/text/primary` | `ivory/50` |
| `color/text/secondary` | `slate/300` |
| `color/text/tertiary` | `slate/400` |
| `color/text/inverse` | `astral/900` |
| `color/text/accent` | `gold/300` |
| `color/border/subtle` | `astral/700` |
| `color/border/default` | `astral/500` |
| `color/border/strong` | `iris/500` |
| `color/accent/primary` | `gold/500` |
| `color/accent/secondary` | `lavender/300` |
| `color/accent/tertiary` | `sakura/300` |
| `color/accent/astral` | `astral/300` |
| `color/accent/iris` | `iris/300` |
| `color/rule/gold` | `gold/500` |
| `color/feedback/success` | `status/success` |
| `color/feedback/warning` | `status/warning` |
| `color/feedback/error` | `status/error` |
| `color/feedback/info` | `status/info` |

### 2.4 Accessibility Floor
- Body text on surface base: target ≥ 7:1 (AAA)
- Secondary text on surface base: ≥ 4.5:1
- Gold is never used for body text — only for short accent text and rules
- Status colors paired with icon/label, never color-only

---

## 3. Typography System

### 3.1 Font Pairing
| Role | Font | Why |
|------|------|-----|
| **Display / Titles** | Fraunces (variable) | Editorial serif with literary, artbook feel; variable axes give XL drama |
| **Cover / Hero caps** | Cinzel (optional) | Engraved Roman capitals — HoYoverse celestial title feel |
| **Body / UI** | Inter | Neutral neo-grotesque; superb legibility at all sizes |
| **Technical / Metadata** | IBM Plex Mono | Monospace signals engineering credibility; aligns numeric specs |

### 3.2 Type Scale
All sizes in px, tracking in em.

| Style | Font | Size / Line | Weight | Tracking | Case | Use |
|-------|------|-------------|--------|----------|------|-----|
| `Display/XL` | Fraunces | 72 / 76 | 300 | -0.02 | — | Cover titles, hero |
| `Display/Large` | Fraunces | 56 / 60 | 300 | -0.02 | — | Section openers, artbook |
| `Title/Project` | Fraunces | 40 / 44 | 400 | -0.01 | — | Project name on breakdowns |
| `Header/Section` | Fraunces | 28 / 34 | 500 | 0 | — | In-page section headers |
| `Header/Sub` | Inter | 20 / 28 | 600 | 0 | — | Subheaders, card titles |
| `Body/Large` | Inter | 18 / 30 | 400 | 0 | — | Lead paragraphs, intros |
| `Body/Default` | Inter | 16 / 26 | 400 | 0 | — | Standard body copy |
| `Caption` | Inter | 13 / 18 | 400 | 0.01 | — | Image captions, footnotes |
| `Label/Technical` | IBM Plex Mono | 12 / 16 | 500 | 0.08 | UPPER | Tag labels, spec keys |
| `Metadata` | IBM Plex Mono | 11 / 14 | 400 | 0.06 | UPPER | Passport fields, fine print |

### 3.3 Type Rules
- **One serif moment per view** — Don't stack Display XL and Display Large
- **Numbers are mono** — Spec values (poly count, resolution, version) in IBM Plex Mono with tabular figures
- **Measure** — Body line length 60–75 characters
- **Tracking** — Only mono labels/metadata get positive tracking; serif display gets negative tracking

---

## 4. Spacing, Grid, Radius, Elevation

### 4.1 8pt Spacing Scale
Base unit **8** (with **4** micro-unit for icon/optical nudges only).

| Token | Value | Primary Usage |
|-------|-------|---------------|
| `space/4` | 4 | Micro: icon-to-label gap, optical nudge |
| `space/8` | 8 | Tight: chip padding, inline gaps |
| `space/16` | 16 | Default: control padding, small stacks |
| `space/24` | 24 | Card padding, paragraph rhythm |
| `space/32` | 32 | Block separation within section |
| `space/48` | 48 | Section padding, card grid gaps |
| `space/64` | 64 | Major section separation |
| `space/96` | 96 | Page top/bottom margins (desktop) |
| `space/128` | 128 | Hero whitespace, artbook spread margins |

**Usage Rules**
- Inside components: 8 / 16 / 24 only
- Between components: 24 / 32 / 48
- Between sections: 64 / 96
- Page-frame margins: 96 (desktop), 48 (tablet), 24 (mobile)

### 4.2 Layout Grids
| Breakpoint | Frame Width | Columns | Gutter | Margin |
|------------|-------------|---------|--------|--------|
| Desktop | 1440 | 12 | 24 | 96 |
| Tablet | 834 | 8 | 24 | 48 |
| Mobile | 390 | 4 | 16 | 24 |

Artbook spreads use a **2-page** frame (2880 wide) with center gutter of 128 and mirrored margins.

### 4.3 Radius
Editorial = near-sharp. Soft corners read as "app," not "print."

| Token | Value | Use |
|-------|-------|-----|
| `radius/none` | 0 | Dividers, rule frames, technical plates |
| `radius/sm` | 2 | Chips, tags, buttons (near-sharp) |
| `radius/md` | 4 | Cards, small containers |
| `radius/lg` | 8 | Large cards, image plates |
| `radius/pill` | 999 | Pills, badges (rare) |

### 4.4 Elevation (Shadows)
| Token | Value | Use |
|-------|-------|-----|
| `shadow/sm` | 0, 1, 2, 0, rgba(36,27,46,0.06) | Subtle lift on cards |
| `shadow/md` | 0, 8, 24, 0, rgba(36,27,46,0.10) | Raised elements, modals |
| `glow/gold` | 0, 0, 16, 0, rgba(201,168,106,0.45) | Brand mark + one hero element only |
| `glow/astral` | 0, 0, 20, 0, rgba(60,92,158,0.50) | Dark-night hero plates |

---

## 5. Component Library

### 5.1 Signature Component: Brand/AssetPassport
The signature spec plate that appears on every portfolio artifact. Contains project metadata in a standardized format.

**Variants:**
- `Format`: Banner, Card, Compact
- `Theme`: Light, Dark

**Component Properties (Automation Schema):**
- `projectName` — Project name
- `category` — Environment / Character / Prop / VFX
- `triangleCount` — Triangle count (formatted with commas)
- `polyCount` — Polygon count (formatted with commas)
- `materialCount` — Number of materials
- `textureCount` — Number of textures
- `textureResolution` — Texture resolution (e.g., "4K")
- `drawCalls` — Draw call count
- `lod` — LOD levels (e.g., "LOD0–LOD3")
- `nanite` — Boolean for Nanite support
- `platform` — Platform (e.g., "PC / Console")
- `software` — Array of software tags (instance-swap)
- `engine` — Engine version (e.g., "Unreal Engine 5.8")
- `date` — Date (e.g., "2026-03")
- `version` — Version number (e.g., "1.2")

### 5.2 Core Components

#### Summary/QuickScan
- **Variants:** None
- **Properties:** `triangleCount`, `polyCount`, `materialCount`, `engine`, `platform`, `category`
- **Use:** Quick-scan summary for recruiter-friendly metric visibility at top of breakdown pages
- **Layout:** Horizontal layout with icon indicators, emphasis on triangle count
- **Styling:** Background: color/surface/raised, Border: 1px color/border/subtle, Padding: space/16

#### Tag/Technical
- **Variants:** Type (Triangle Count, Poly Count, Material Count, Texture Resolution, Draw Calls, LOD, Nanite, Platform, Engine, Date, Version)
- **Properties:** `label`, `value`, `emphasis` (Strong, Default), `priority` (Critical, High, Medium, Low)
- **Use:** Spec labels in Asset Passport and Info Cards
- **Priority Visual Treatment:**
  - Critical: Background color/accent/primary, text color/text/inverse
  - High: Background color/surface/sunken, border color/accent/primary
  - Medium: Background color/surface/sunken, border color/border/default
  - Low: Background transparent, border color/border/subtle
- **Minimum Width:** 120px with truncate behavior

#### Tag/Software
- **Variants:** Software type (Blender, ZBrush, Substance Painter, Houdini, Unreal Engine, Maya, 3ds Max)
- **Properties:** `softwareName`, `icon` (instance-swap)
- **Use:** Software stack display

#### Card/Info
- **Variants:** Type (Asset Statistics, Material Statistics, Shader Statistics, Environment Statistics)
- **Properties:** `title`, `rows` (array of Row/Spec), `showIcon`, `priority` (High, Medium, Low), `groupedRows` (boolean)
- **Use:** Information cards in breakdown layouts
- **Priority Visual Treatment:**
  - High: Shadow/md, border color/accent/primary
  - Medium: Shadow/sm, border color/border/default
  - Low: No shadow, border color/border/subtle
- **Row Grouping:** Visual grouping (subtle background) for related rows with optional group headers

#### Row/Spec
- **Variants:** None (atomic component)
- **Properties:** `key`, `value`
- **Use:** Key-value spec rows in cards

#### Divider/Section
- **Variants:** Style (Gold Rule, Hairline, Constellation), Weight (Strong, Medium, Subtle)
- **Properties:** `showStar` (boolean), `label` (text), `showIcon` (boolean)
- **Use:** Section separators with optional labels for content progression
- **Weight Visual Treatment:**
  - Strong: 2px color/rule/gold, with Star/4pt
  - Medium: 1px color/rule/gold, no star
  - Subtle: 1px color/border/subtle, no star
- **Label Treatment:** Label/Technical style, positioned above divider when present

#### Image/Plate
- **Variants:** Type (Default, WithCaption, Beauty)
- **Properties:** `imageSource`, `caption`, `showFrame`
- **Use:** Image frames with optional captions

#### Grid/Image
- **Variants:** Columns (2, 3, 4), Gap (16, 24, 32)
- **Properties:** `items` (array of Image/Plate instances), `columns` (number), `gap` (number), `minWidth` (number)
- **Use:** Standardized image grid layouts across templates
- **Responsive Behavior:** Gap: 32px (desktop), 24px (tablet), 16px (mobile)
- **Constraints:** Min-width: 280px (cards), 400px (images)
- **Layout:** Auto Layout Wrap with responsive reflow

#### Icon/Software/*
- **Variants:** Software-specific icons
- **Properties:** None (visual only)
- **Use:** Software tags

#### Button
- **Variants:** Type (Primary, Secondary, Ghost), Size (sm, md)
- **Properties:** `label`, `showIcon`
- **Use:** Call-to-action buttons

#### Callout
- **Variants:** Type (Note, Tip, Warning)
- **Properties:** `message`, `type`
- **Use:** Feedback and informational callouts

#### Legend/Swatch
- **Variants:** None
- **Properties:** `label`, `colorSwatch`, `description`
- **Use:** Material/color legend rows

#### Process/Step
- **Variants:** None
- **Properties:** `stepNumber`, `title`, `description`, `imagePlate`
- **Use:** Numbered steps in process breakdowns

#### Breadcrumb/Pager
- **Variants:** None
- **Properties:** `sectionPath`, `pageNumber`
- **Use:** Page navigation and section breadcrumbs

#### Footer/Signature
- **Variants:** None
- **Properties:** `brandMark`, `handle`, `contact`
- **Use:** Brand signature on every template

#### Star/*
- **Variants:** 4pt (✦), 8pt (✸), Constellation, StarChart
- **Properties:** `opacity`, `color`
- **Use:** Motif primitives

#### Frame/Corner
- **Variants:** Filigree, Astral
- **Properties:** `lineWeight`, `color`
- **Use:** Ornate corner frames for hero/cover plates

#### Brand/Mark
- **Variants:** Star (✸), Wordmark (MELODIA), Lockup (✸ + MELODIA)
- **Properties:** `showGlow` (boolean)
- **Use:** Logo system

### 5.3 Component Hierarchy
```
Primitives:    Star, Brand/Mark, Icon/Software/*, Row/Spec, Divider/Section
Elements:      Tag/Technical, Tag/Software, Button, Callout, Legend/Swatch, Image/Plate
Composites:    Card/Info, Process/Step, Breadcrumb/Pager, Footer/Signature, Summary/QuickScan
Layouts:       Grid/Image
Signature:     Brand/AssetPassport
Patterns:      Stat Cluster, Spec Sheet, Beauty + Passport pairing
```

---

## 6. Layout Templates

All templates are Auto Layout, built from components, use the §4.2 grids, and ship in Desktop/Tablet/Mobile sizes. Each carries a `Footer/Signature` and at least one `Brand/AssetPassport`.

### 6.1 Template Inventory

| # | Template | Structure (top → bottom) | Key Components |
|---|----------|---------------------------|----------------|
| 1 | **Hero Page** | Full-bleed beauty `Image/Plate[Beauty]` → `Display/XL` title overlay → `Asset Passport[Banner]` → scroll cue | Mark, Passport, Plate |
| 2 | **Asset Breakdown** | Title block → `Summary/QuickScan` → beauty shot → `Grid/Image` of `Card/Info[Asset Statistics]` + wireframe/UV plates → `Divider/Section[Strong]` → `Tag/Technical` cluster | Summary, Grid, Cards, Tags, Plates, Dividers |
| 3 | **Environment Breakdown** | Title block → `Summary/QuickScan` → wide beauty → `Divider/Section[Strong]` label="Composition" → annotated plate → `Divider/Section[Medium]` label="Modular Kit" → `Grid/Image` modular-kit grid → `Divider/Section[Medium]` label="Lighting" → lighting passes row → `Card/Info[Priority=High]` stats | Summary, Grid, Plates, Cards, Dividers |
| 4 | **Material Presentation** | Title block → `Summary/QuickScan` → material hero sphere/plane → `Divider/Section[Strong]` label="Channels" → `Grid/Image` channel grid (Albedo/Normal/Roughness/etc. `Image/Plate` + `Legend/Swatch`) → `Divider/Section[Medium]` → `Card/Info[Priority=High]` stats | Summary, Grid, Plates, Legend, Cards, Dividers |
| 5 | **Shader Breakdown** | Title block → `Summary/QuickScan` → result beauty → `Divider/Section[Strong]` label="Node Graph" → node-graph plate → `Divider/Section[Medium]` label="Parameters" → parameter table (`Row/Spec`) → `Card/Info[Shader Statistics]` → math/notes `Callout` | Summary, Cards, Rows, Callout, Dividers |
| 6 | **Trim Sheet Presentation** | Title block → `Summary/QuickScan` → trim sheet flat → `Divider/Section[Medium]` label="Usage Examples" → `Grid/Image` usage examples grid → density/texel `Tag/Technical` cluster → application beauty | Summary, Grid, Plates, Tags, Dividers |
| 7 | **Technical Documentation** | Doc header + `Breadcrumb/Pager` → TOC → body sections w/ `Header/Section` + `Divider/Section[Weight=Strong]` with labels → code/spec `Callout` | Dividers, Callout, Pager |
| 8 | **Process Breakdown** | Title block → `Summary/QuickScan` → numbered `Process/Step` timeline (✦ markers) → `Divider/Section[Medium]` between steps → stage plates → final beauty + Passport | Summary, Process/Step, Plates, Dividers |
| 9 | **Commission Sheet** | Brand lockup header → service tiers as `Card/Info[Priority=High]` → pricing `Row/Spec` → ToS fine print → contact `Footer/Signature` | Cards, Rows, Mark |
| 10 | **Artbook Spread** | 2-page frame → full-bleed art left, editorial text + `Display/Large` right → constellation corner accents → page numbers | Plate, Star, Pager |

### 6.2 Recurring Patterns

#### Stat Cluster
Responsive wrap of `Tag/Technical` components. Used for displaying key metrics (triangle count, poly count, material count, etc.).

#### Spec Sheet
`Card/Info` component containing repeated `Row/Spec` components. Used for detailed technical specifications.

#### Beauty + Passport
Full-bleed `Image/Plate[Beauty]` with `Brand/AssetPassport` overlaid bottom-left. The hero signature pattern.

#### Channel Grid
Uniform grid of `Image/Plate` components with mono captions. Used for material/shader channel breakdowns (Albedo, Normal, Roughness, etc.).

---

## 7. Responsive Rules

Single source design at Desktop, then adapt. Components are built to **reflow**, not rescale.

| Concern | Desktop (1440) | Tablet (834) | Mobile (390) |
|---------|----------------|--------------|--------------|
| Grid | 12 col / 96 margin | 8 col / 48 margin | 4 col / 24 margin |
| Section spacing | 96 | 64 | 48 |
| Card grids | 3–4 up | 2 up | 1 up (stack) |
| `Display/XL` | 72 | 56 | 40 |
| `Title/Project` | 40 | 32 | 28 |
| Asset Passport | Banner or Card | Card | Compact |
| Tag clusters | Single row | Wrap | Wrap, full-width chips |
| Image plates | Side-by-side | 2-up | Full-width stacked |
| Artbook spread | 2-page | Single page, stacked | Single page, stacked |

**Mechanics**
- Use Auto Layout `Wrap` for tag/card clusters
- Use min/max width constraints on cards (`min 280`, `max 1fr`)
- Type steps are variant-swapped by breakpoint (don't free-scale text)
- Passport switches `Format` variant by breakpoint
- Test each template at all three widths before publishing

---

## 8. Figma File Organization

### 8.1 Page Structure
```
01 Foundations   → Brand intro, motifs, color/type/spacing specimens, logo system, do/don't
02 Tokens        → Variable collections rendered as swatches/specimens (source of truth)
03 Components    → Component library, organized by hierarchy, with usage notes
04 Patterns      → Recurring composites (Stat Cluster, Spec Sheet, Beauty+Passport, Channel Grid)
05 Layouts       → Grid systems, responsive frames, spacing/elevation references
06 Templates     → 10 production templates × {Desktop, Tablet, Mobile}
07 Archive       → Deprecated components/versions; never delete, move here
```

Optional `00 Cover` page with brand lockup for file thumbnail.

### 8.2 Naming Conventions

**Layers**
- Frames: `PascalCase` descriptive (`HeroPage/Desktop`)
- No default names (`Frame 12`, `Group 3`) — ever
- Prefix utility layers with `_` (`_grid`, `_bg`, `_spacer`)

**Components** — `Category/Component`
- Examples: `Tag/Technical`, `Card/Info`, `Brand/AssetPassport`, `Divider/Section`
- Categories: `Brand`, `Tag`, `Card`, `Divider`, `Row`, `Image`, `Button`, `Icon`, `Process`, `Footer`, `Legend`, `Breadcrumb`, `Star`
- Component sets (multi-variant) use bare name; variants live inside

**Variant Properties** — `Property=Value`
- Properties: `PascalCase`
- Values: `PascalCase` or human strings
- Examples: `Type=Triangle Count`, `Emphasis=Strong`, `Format=Banner`, `Theme=Dark`
- Booleans named with verb/state: `showIcon`, `hasDivider`
- Order: `Type` → `Style/Emphasis/Format` → `Theme` → `Size` → booleans

**Component (Data) Properties**
- Text props use automation field name verbatim (see §9): `projectName`, `triangleCount`, `textureResolution`, `materialCount`, `engine`, `version`, `date`, `category`
- Instance-swap props: `softwareTag`, `dividerNode`, `softwareIcon`

**Variables / Tokens** — `group/subgroup/name`
- Color: `color/surface/base`, `color/text/primary`, `color/accent/primary`
- Spacing: `space/8` … `space/128`
- Radius: `radius/sm`
- Collections: `Color` (modes: Light, Dark), `Spacing`, `Radius`

**Text Styles** — `Group/Name`
- Examples: `Display/XL`, `Header/Section`, `Label/Technical`, `Metadata`

**Styles/Effects** — `shadow/sm`, `shadow/md`

---

## 9. Automation Support

### 9.1 Canonical Data Schema
Single contract between tooling and design. Component text-property names match these keys exactly.

```json
{
  "projectName": "Ashen Cathedral",
  "category": "Environment",
  "triangleCount": 482318,
  "polyCount": 248110,
  "materialCount": 12,
  "textureCount": 36,
  "textureResolution": "4K",
  "drawCalls": 184,
  "lod": "LOD0–LOD3",
  "nanite": true,
  "platform": "PC / Console",
  "software": ["Blender", "ZBrush", "Substance Painter", "Houdini"],
  "engine": "Unreal Engine 5.8",
  "date": "2026-03",
  "version": "1.2"
}
```

### 9.2 Automation Population Methods
- **Tokens Studio + JSON:** Import `tokens.json` → variables; tooling can regenerate token files for theme variants
- **Figma Plugin API:** Plugin reads JSON, finds instances of `Brand/AssetPassport` / `Card/Info` / `Tag/Technical`, sets component properties by name
- **MCP Automation:** MCP server exposes `populate_passport(fileKey, nodeId, data)` wrapping plugin/REST calls
- **Unreal Pipeline:** Python scripts in Unreal Engine generate the JSON schema from scene stats

### 9.3 Design Rules for Automation
1. Every dynamic value is a Component Property named per schema — never raw text
2. Stable names, stable structure — don't rename props or reorder casually
3. Formatting lives in components (tabular figures, uppercase via style) so tooling passes raw values
4. Lists via instance-swap (`software`) so adding a tool = swapping/duplicating an `Icon/Software/*`
5. One schema, many surfaces — same JSON fills Passport, Info Cards, and Tag clusters

---

## 10. Implementation Order

1. **File + pages** — Create 7 pages (§8.1). Add `00 Cover`
2. **Variables** — Create `Color` (Light+Dark modes), `Spacing`, `Radius` collections from §2/§4
3. **Text styles** — Create all §3.2 styles. Load fonts first
4. **Effects** — Create `shadow/sm`, `shadow/md`
5. **Motif primitives** — `Star/8pt`, `Star/4pt`, `Constellation`, `Frame/Corner`, `Brand/Mark` lockups
6. **Atoms** — `Row/Spec`, `Divider/Section`, `Icon/Software/*`
7. **Elements** — `Tag/Technical`, `Tag/Software`, `Button`, `Callout`, `Image/Plate`, `Legend/Swatch`
8. **Composites** — `Card/Info`, `Process/Step`, `Breadcrumb/Pager`, `Footer/Signature`
9. **Signature** — `Brand/AssetPassport` (all formats + themes) — wire component properties to §9.1 names
10. **Patterns** — Assemble Stat Cluster, Spec Sheet, Beauty+Passport, Channel Grid
11. **Layouts** — Grids + spacing/elevation reference frames
12. **Templates** — Build all 10 at Desktop, then derive Tablet + Mobile via variant swaps + reflow
13. **Documentation** — Specimens, do/don'ts, usage notes
14. **Publish** as Figma Library; enable for ArtStation/web exports
15. **Automation hookup** — Wire populate plugin/MCP to §9.1 schema; dry-run on real project

---

## 11. Hero Treatments

Four interchangeable hero/cover styles — same palette + type, different mood and sparkle level. Use one per piece; don't stack.

| Treatment | Surface | Sparkle Level | Best For |
|-----------|---------|---------------|----------|
| **Constellation** | Astral Night | Low–medium (Star/Constellation backplate + faint scatter) | Default hero, ArtStation cover |
| **Nebula (iris-forward)** | Astral Night + iris/astral bloom | Medium (glowing gold sparkles) | Dramatic hero pieces, key art |
| **Ornate Frame** | Astral Night | Low (Frame/Corner brackets) | Covers, end-cards, artbook plates |
| **Ivory Editorial + sparkle** | Ivory | Very low (a few gold Star/4pt) | Breakdowns, print, readability-first |

**Sparkle Budget:** Dark surfaces may carry faint white starfield + ≤ 1 glowing gold star per view; ivory surfaces get only a handful of low-opacity gold `Star/4pt`. Glow rationed to brand mark + one hero element.

---

## 12. Unreal Engine Data Emission Points

This section defines how the Unreal Engine 5.8 project emits data to populate the design system layouts automatically.

### 12.1 Hero Renders → Hero Page Template
**Unreal Source:** Active environment levels (`L_SakuraPath`, `L_Template`)

**Extraction Method:** 
- Monolith MCP action: `editor.capture_scene_preview`
- Cine Camera actors marked with `Portfolio_Hero` tags
- Pipeline queries Level Editor world context, sets view target to tagged camera
- Triggers viewport frame capture with temporal AA warmups

**Monolith Action Parameters:**
```python
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_scene_preview",
    "asset_type": "static_mesh",  # or "level" for full scene
    "asset_path": "/Game/EnvSandbox/Levels/L_SakuraPath",
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/Hero_SakuraPath.png",
    "width": 1920,
    "height": 1080
})
```

**Target Resolutions:**
- Desktop Container: `1920 x 1080` (16:9, PNG, sRGB)
- Mobile Showcase: `1080 x 1350` (4:5 vertical, PNG, sRGB)

**Figma Mapping:** `Image/Plate[Beauty]` in Hero Page template

**Metadata Keys:** `world_root`, `style_theme`, `camera_tag`, `resolution`

### 12.2 Breakdown Renders → Asset Breakdown / Environment Breakdown Templates
**Unreal Source:** Modular greybox static meshes generated by PGA (`GB_ZEN_*`)

**Extraction Method:** Monolith MCP action `editor.capture_with_overlay`

**Monolith Action Parameters:**
```python
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_with_overlay",
    "asset_path": "/Game/EnvSandbox/Meshes/GB_ZEN_Rock_01",
    "overlay_mode": "wireframe",  # or "uv_density", ".shader_complexity", "normals"
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/Breakdown_Rock_Wireframe.png",
    "width": 1024,
    "height": 1024
})
```

**Figma Mapping:** `Image/Plate` grid in Asset Breakdown / Environment Breakdown templates

**Metadata Keys:** `asset_path`, `overlay_mode`, `mesh_type`

### 12.3 Material Sheets → Material Presentation Template
**Unreal Source:** Showcase and theme material instances (`MI_Show_*`, `MI_Zen_*`)

**Extraction Method:** Monolith MCP action `editor.capture_material_grid`

**Monolith Action Parameters:**
```python
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_material_grid",
    "material_instances": [
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_Baroque_Default",
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_GothicArchitecture_Stone",
        "/Game/EnvSandbox/Materials/SDF/Instances/MI_SDF_OrnamentLayer_Classic"
    ],
    "preview_mesh": "sphere",  # or "plane" for displacement/parallax
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/Material_Grid_SDF.png",
    "width": 2048,
    "height": 2048
})
```

**Figma Mapping:** Channel Grid in Material Presentation template

**Metadata Keys:** `parent_master`, `toon_profile`, `material_type`

### 12.4 Trim Sheet Renders → Trim Sheet Presentation Template
**Unreal Source:** Blended trimsheet instances (`MI_Trimsheet_*`) and baked trim geometry

**Extraction Method:** Monolith MCP action `editor.capture_scene_preview` with custom trim panel setup

**Monolith Action Parameters:**
```python
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_scene_preview",
    "asset_type": "static_mesh",
    "asset_path": "/Game/EnvSandbox/Meshes/TrimPanel_01",
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/TrimSheet_Lit.png",
    "width": 2048,
    "height": 1024
})

# Second capture with overlay for UV visualization
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_with_overlay",
    "asset_path": "/Game/EnvSandbox/Meshes/TrimPanel_01",
    "overlay_mode": "uv_density",
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/TrimSheet_UV.png",
    "width": 2048,
    "height": 1024
})
```

**Figma Mapping:** `Image/Plate` in Trim Sheet Presentation template

**Metadata Keys:** `trim_id_count`, `layers`, `texel_density`

### 12.5 Asset Statistics → Asset Passport / Card/Info Components
**Unreal Source:** Static mesh assets, HISM outliner components, PCG volumes

**Extraction Method:** Python metadata queries (`audit_pcg_portfolio.py`, `audit_material_library.py`) outputting `portfolio_stats_manifest.json`

**Python Audit Scripts:**
```python
# PCG audit (from audit_pcg_portfolio.py)
import audit_pcg_portfolio
report = audit_pcg_portfolio._audit_in_ue()
# Outputs: Saved/Audit/pcg_portfolio_audit.json
# Contains: ISM counts, PCG density, volume bounds, graph references

# Material library audit (from audit_material_library.py)
import audit_material_library
materials = audit_material_library.scan_tree(MATERIALS_ROOT)
# Outputs: Saved/Audit/material_library_audit.json
# Contains: texture_count, material_count, orphan_textures, refs
```

**Captured Metrics:**
- Geometry: Vertex count, polygon count, UV channel count, bounding box volume
- Instancing: HISM instance counts per actor, total draw calls, vertex memory sizes
- PCG Density: Point counts, voxel dimensions, scatter bounding scopes

**Figma Mapping:** `Brand/AssetPassport` and `Card/Info` components

**Metadata Keys:** Maps directly to §9.1 canonical schema:
- `triangleCount` → from vertex count
- `polyCount` → from polygon count
- `materialCount` → from material slots
- `textureCount` → from texture references
- `textureResolution` → from texture size analysis
- `drawCalls` → from HISM draw call analysis
- `nanite` → from mesh Nanite flag
- `platform` → from project settings
- `software` → from plugin/dependency analysis
- `engine` → from Unreal version
- `date` → from asset modification date
- `version` → from asset version or iteration

### 12.6 Technical Documentation → Technical Documentation Template
**Unreal Source:** Style genomes (`surreal_os/genome.py`), snap rules (`architectural_atoms.yaml`), loop state changelogs

**Extraction Method:** Monolith MCP action `editor.inspect_material_pbr` for material documentation

**Monolith Action Parameters:**
```python
monolith_mcp_client.call_tool("editor_query", {
    "action": "inspect_material_pbr",
    "asset_path": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
})
# Returns: {
#   "slots": {
#     "base_color_texture": "/Game/Textures/T_BaseColor",
#     "normal_texture": "/Game/Textures/T_Normal",
#     "roughness_texture": "/Game/Textures/T_Roughness"
#   },
#   "packed_channels": [
#     {"texture": "/Game/Textures/T_ORM", "packing": "ORM"}
#   ],
#   "unmapped_parameters": []
# }
```

**Figma Mapping:** `Header/Section`, `Divider/Section`, `Callout` components in Technical Documentation template

**Metadata Keys:** `genome_summary`, `grammar_axis`, `process_steps`, `technical_notes`

### 12.7 PCG Diagrams → Process Breakdown Template
**Unreal Source:** PCG graph nodes and metadata

**Extraction Method:** Python PCG graph introspection (`pcg_graph_builder.py`) + Monolith MCP for visualization

**Python Graph Builder:**
```python
import pcg_graph_builder as gb

# Get graph package path from PCG component
graph_path = gb.graph_package_path(pcg_component)

# Inspect graph structure
graph_data = {
    "graph_path": graph_path,
    "node_count": len(gb.get_graph_nodes(graph_path)),
    "node_types": gb.get_node_type_distribution(graph_path),
    "parameters": gb.get_graph_parameters(graph_path)
}
```

**Monolith Visualization:**
```python
# Capture PCG volume visualization
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_scene_preview",
    "asset_type": "level",
    "asset_path": "/Game/EnvSandbox/Levels/L_SakuraPath",
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/PCG_Graph_Visualization.png",
    "width": 1920,
    "height": 1080
})
```

**Figma Mapping:** `Process/Step` components in Process Breakdown template

**Metadata Keys:** `pcg_graph_path`, `node_sequence`, `parameter_values`

### 12.8 Performance Captures → Asset Breakdown / Environment Breakdown Templates
**Unreal Source:** Stat system, GPU profilers, memory trackers

**Extraction Method:** Monolith MCP action `editor.csv_profile` for performance data capture

**Monolith Action Parameters:**
```python
# Start CSV profiling
monolith_mcp_client.call_tool("editor_query", {
    "action": "csv_profile",
    "operation": "start",
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/Performance_Profile.csv",
    "trace_channels": ["CPU", "GPU", "Frame", "Render"]
})

# Run PIE session
monolith_mcp_client.call_tool("editor_query", {
    "action": "start_pie",
    "level_path": "/Game/EnvSandbox/Levels/L_SakuraPath"
})

# Stop profiling after capture
monolith_mcp_client.call_tool("editor_query", {
    "action": "csv_profile",
    "operation": "stop"
})
```

**Figma Mapping:** `Tag/Technical` clusters and `Card/Info` components

**Metadata Keys:** `fps`, `frameTime`, `gpuTime`, `memoryUsage`, `drawCallCount`

---

## 13. Pipeline Execution Sequence

During loop runs, SQA sentinels coordinate extraction and packaging:

```
[ Loop Finish ]
       │
       ▼
[ Step 1: Render Sweep ]      ➔ Capture Hero, Breakdowns, and Material grids via Monolith
       │
       ▼
[ Step 2: Stats Audit ]       ➔ Run Python scripts to compile memory, vertex, and HISM metrics
       │
       ▼
[ Step 3: Package JSON ]      ➔ Write portfolio_manifest.json referencing all renders and metadata
       │
       ▼
[ Step 4: Figma Push ]        ➔ Sync JSON tokens via Figma API to instantiate layout frames
```

---

## 14. File Locations

- **Design System Spec:** `Docs/DESIGN_SYSTEM.md` (this file)
- **Design Tokens:** `_staging/design-system/tokens.json`
- **Pipeline Spec:** `BS_GodFile/PORTFOLIO_PIPELINE.md`
- **Portfolio Orchestrator:** `BS_GodFile/Docs/PORTFOLIO_ORCHESTRATOR_PLAN.md`
- **PCG Portfolio Plan:** `BS_GodFile/Docs/PCG_PORTFOLIO_PLAN.md`
- **Unreal Python Scripts:** `BS_GodFile/Content/Python/`
- **Audit Outputs:** `BS_GodFile/Saved/Audit/`

---

## 15. Maintenance

### 15.1 Version Control
- Design system changes tracked in this document
- Token changes reflected in `tokens.json`
- Component changes documented in changelog

### 15.2 Update Process
1. Update this document with design changes
2. Regenerate `tokens.json` if color/spacing/type changes
3. Update Figma components to match new spec
4. Update Unreal Python scripts if schema changes
5. Test pipeline end-to-end with sample data

### 15.3 Validation
- All templates must pass responsive testing (Desktop/Tablet/Mobile)
- All automation schemas must match component property names exactly
- All Unreal extraction scripts must produce valid JSON per §9.1 schema
- Accessibility compliance checked on each update

---

**This document is the single source of truth for the Environment Portfolio Platform design system. All portfolio generation must reference this specification.**
