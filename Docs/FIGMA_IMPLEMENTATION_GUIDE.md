# Figma Implementation Guide

**Purpose:** Practical guidance for implementing the Environment Portfolio Design System in Figma  
**Target Audience:** Figma designers, design system maintainers  
**Constraint:** Presentation-layer implementation only — no engine changes

---

## Table of Contents

1. [File Setup](#1-file-setup)
2. [Foundations Implementation](#2-foundations-implementation)
3. [Component Implementation](#3-component-implementation)
4. [Template Implementation](#4-template-implementation)
5. [Automation Setup](#5-automation-setup)
6. [Responsive Implementation](#6-responsive-implementation)
7. [Dark Mode Implementation](#7-dark-mode-implementation)
8. [Accessibility Implementation](#8-accessibility-implementation)
9. [Publishing & Distribution](#9-publishing--distribution)
10. [Maintenance Workflow](#10-maintenance-workflow)

---

## 1. File Setup

### 1.1 Create File Structure

Create a new Figma file with the following pages (order matters):

```
00 Cover              (optional, for file thumbnail)
01 Foundations        (brand intro, color/type/spacing specimens)
02 Tokens             (variable collections — source of truth)
03 Components         (component library, organized by hierarchy)
04 Patterns           (recurring composites)
05 Layouts            (grid systems, spacing/elevation references)
06 Templates          (10 production templates × 3 breakpoints)
07 Archive            (deprecated components/versions)
```

**Naming Convention:** Use exact page names above. Do not rename.

### 1.2 Import Fonts

Install these fonts in Figma before beginning:

| Font | Source | Required Weights |
|------|--------|------------------|
| Fraunces | Google Fonts | 300, 400, 500 |
| Cinzel | Google Fonts | 400, 700 |
| Inter | Google Fonts | 400, 500, 600 |
| IBM Plex Mono | Google Fonts | 400, 500 |

**Note:** Use variable font versions where available (Fraunces Variable).

### 1.3 Create Color Variables

Create variable collections in the **02 Tokens** page:

**Collection: Color**
- Modes: `Light`, `Dark`
- Groups: `color/surface`, `color/text`, `color/border`, `color/accent`, `color/feedback`, `color/rule`

**Primitive Variables (Light Mode):**
```
ivory/50: #FCFBF8
ivory/100: #F7F4EF
ivory/200: #EFEAE1
ivory/300: #E3DACE
plum/500: #6E6080
plum/600: #463A54
plum/700: #2E2438
plum/800: #241B2E
plum/900: #1C1426
gold/100: #F0E6D2
gold/300: #DDC79B
gold/500: #C9A86A
gold/700: #A7884E
lavender/100: #E8E4F2
lavender/300: #C2BAE0
lavender/500: #9F94C6
sakura/100: #F5E8EA
sakura/300: #E7C9CE
sakura/500: #D6A9B0
slate/200: #D5D8DE
slate/300: #AEB4BF
slate/400: #828A98
slate/500: #5A6170
slate/700: #3C414B
astral/100: #E5EAF5
astral/300: #8AA9D6
astral/500: #3C5C9E
astral/700: #26365E
astral/900: #141A30
iris/100: #ECE6F4
iris/300: #A99AD0
iris/500: #6E5AA6
status/success: #5E8B7E
status/warning: #B8862F
status/error: #A85751
status/info: #6B7CA8
```

**Semantic Variables (Light Mode):**
```
color/surface/base: ivory/100
color/surface/raised: ivory/50
color/surface/sunken: ivory/200
color/surface/inverse: plum/800
color/text/primary: plum/800
color/text/secondary: slate/500
color/text/tertiary: slate/400
color/text/inverse: ivory/50
color/text/accent: gold/700
color/border/subtle: ivory/300
color/border/default: slate/200
color/border/strong: slate/300
color/accent/primary: gold/500
color/accent/secondary: lavender/500
color/accent/tertiary: sakura/300
color/accent/astral: astral/500
color/accent/iris: iris/500
color/rule/gold: gold/500
color/feedback/success: status/success
color/feedback/warning: status/warning
color/feedback/error: status/error
color/feedback/info: status/info
```

**Semantic Variables (Dark Mode):**
```
color/surface/base: astral/900
color/surface/raised: astral/700
color/surface/sunken: plum/900
color/surface/inverse: ivory/100
color/text/primary: ivory/50
color/text/secondary: slate/300
color/text/tertiary: slate/400
color/text/inverse: astral/900
color/text/accent: gold/300
color/border/subtle: astral/700
color/border/default: astral/500
color/border/strong: iris/500
color/accent/primary: gold/500
color/accent/secondary: lavender/300
color/accent/tertiary: sakura/300
color/accent/astral: astral/300
color/accent/iris: iris/300
color/rule/gold: gold/500
color/feedback/success: status/success
color/feedback/warning: status/warning
color/feedback/error: status/error
color/feedback/info: status/info
```

**Implementation Tip:** Use Tokens Studio plugin to import `tokens.json` from `_staging/design-system/` for automated variable creation.

### 1.4 Create Spacing Variables

**Collection: Spacing**
```
space/4: 4
space/8: 8
space/16: 16
space/24: 24
space/32: 32
space/48: 48
space/64: 64
space/96: 96
space/128: 128
```

### 1.5 Create Radius Variables

**Collection: Radius**
```
radius/none: 0
radius/sm: 2
radius/md: 4
radius/lg: 8
radius/pill: 999
```

### 1.6 Create Text Styles

Create text styles in the **02 Tokens** page:

| Style Name | Font | Size | Weight | Line Height | Letter Spacing | Case |
|------------|------|------|--------|-------------|----------------|------|
| `Display/XL` | Fraunces | 72 | 300 | 76 | -0.02em | — |
| `Display/Large` | Fraunces | 56 | 300 | 60 | -0.02em | — |
| `Title/Project` | Fraunces | 40 | 400 | 44 | -0.01em | — |
| `Header/Section` | Fraunces | 28 | 500 | 34 | 0 | — |
| `Header/Sub` | Inter | 20 | 600 | 28 | 0 | — |
| `Body/Large` | Inter | 18 | 400 | 30 | 0 | — |
| `Body/Default` | Inter | 16 | 400 | 26 | 0 | — |
| `Caption` | Inter | 13 | 400 | 18 | 0.01em | — |
| `Label/Technical` | IBM Plex Mono | 12 | 500 | 16 | 0.08em | UPPER |
| `Metadata` | IBM Plex Mono | 11 | 400 | 14 | 0.06em | UPPER |

**Implementation Tip:** Use tabular figures for IBM Plex Mono styles (OpenType feature `tnum`).

### 1.7 Create Effects

Create local styles in the **02 Tokens** page:

**Shadows:**
```
shadow/sm: 0, 1, 2, 0, rgba(36,27,46,0.06)
shadow/md: 0, 8, 24, 0, rgba(36,27,46,0.10)
```

**Glows:**
```
glow/gold: 0, 0, 16, 0, rgba(201,168,106,0.45)
glow/astral: 0, 0, 20, 0, rgba(60,92,158,0.50)
```

---

## 2. Foundations Implementation

### 2.1 Brand Mark System

Create **Brand/Mark** component set in **03 Components** page:

**Variants:**
- `Type=Star` — 8-point star (✸)
- `Type=Wordmark` — MELODIA wordmark in Fraunces Display/Large
- `Type=Lockup` — Star + Wordmark horizontal lockup

**Component Properties:**
- `showGlow: boolean` — Apply glow/gold effect
- `color: variable` — Default to color/text/accent

**Implementation:**
- Star: Draw using vector pen tool. Use gold/500 stroke, 1px weight.
- Wordmark: Text layer using Fraunces Display/Large, tracking -0.02em.
- Lockup: Auto Layout horizontal, 8px gap, center alignment.

### 2.2 Motif Primitives

Create these primitive components in **03 Components** page:

**Star/8pt** (`Star/*` component set)
- 8-point star vector
- Variants: `Opacity=100`, `Opacity=50`, `Opacity=25`
- Default color: gold/500

**Star/4pt** (`Star/*` component set)
- 4-point star vector
- Variants: `Opacity=100`, `Opacity=50`, `Opacity=25`
- Default color: gold/500

**Constellation** (`Star/*` component set)
- Connected-dot starfield pattern
- Opacity ≤ 12%
- Use as background fill, not standalone

**Frame/Corner** component set
- Variants: `Style=Filigree`, `Style=Astral`
- Properties: `lineWeight: number`, `color: variable`
- Line weight: 1px default

**Implementation Tip:** Use vector networks for constellation patterns. Keep stroke weight consistent at 1px.

---

## 3. Component Implementation

### 3.1 Implementation Order

Follow this order to ensure dependencies are resolved:

1. **Primitives** — Star, Brand/Mark, Row/Spec, Divider/Section
2. **Atoms** — Icon/Software/* (create all software icons)
3. **Elements** — Tag/Technical, Tag/Software, Button, Callout, Image/Plate, Legend/Swatch
4. **Composites** — Card/Info, Process/Step, Breadcrumb/Pager, Footer/Signature, Summary/QuickScan
5. **Layouts** — Grid/Image
6. **Signature** — Brand/AssetPassport (all formats + themes)

### 3.2 Row/Spec Component

**Purpose:** Key-value spec rows in cards

**Structure:**
```
Auto Layout (Horizontal, 8px gap)
├─ Text Layer (Label/Technical) — Key
└─ Text Layer (Metadata) — Value
```

**Component Properties:**
- `key: text` — Spec key (e.g., "Triangle Count")
- `value: text` — Spec value (e.g., "482,318")

**Implementation:**
- Use Auto Layout with `space/8` gap
- Key uses `Label/Technical` style
- Value uses `Metadata` style
- No background, no border

### 3.3 Divider/Section Component

**Purpose:** Section separators with optional labels

**Variants:**
- `Style=Gold Rule` — 1px gold/500 line
- `Style=Hairline` — 1px ivory/300 line
- `Style=Constellation` — Faint constellation pattern
- `Weight=Strong` — 2px color/rule/gold with Star/4pt
- `Weight=Medium` — 1px color/rule/gold, no star
- `Weight=Subtle` — 1px color/border/subtle, no star

**Component Properties:**
- `showStar: boolean` — Show 4pt star at center
- `label: text` — Section label text
- `showIcon: boolean` — Show icon indicator

**Implementation:**
- Gold Rule: 1px height rectangle, fill color/rule/gold
- Hairline: 1px height rectangle, fill color/border/subtle
- Constellation: Pattern fill using Star/Constellation component
- Strong weight: 2px height rectangle, fill color/rule/gold, centered Star/4pt
- Label: Label/Technical style, positioned 8px above divider when present
- Star: Centered Star/4pt when showStar=true

### 3.4 Tag/Technical Component

**Purpose:** Spec labels in Asset Passport and Info Cards with priority-based visual hierarchy

**Variants:**
- `Type=Triangle Count`
- `Type=Poly Count`
- `Type=Material Count`
- `Type=Texture Resolution`
- `Type=Draw Calls`
- `Type=LOD`
- `Type=Nanite`
- `Type=Platform`
- `Type=Engine`
- `Type=Date`
- `Type=Version`
- `Priority=Critical` — Background color/accent/primary, text color/text/inverse
- `Priority=High` — Background color/surface/sunken, border color/accent/primary
- `Priority=Medium` — Background color/surface/sunken, border color/border/default
- `Priority=Low` — Background transparent, border color/border/subtle

**Component Properties:**
- `label: text` — Label text
- `value: text` — Value text
- `emphasis: enum` — Strong, Default
- `priority: enum` — Critical, High, Medium, Low

**Implementation:**
- Auto Layout (Horizontal, 4px gap)
- Minimum width: 120px
- Padding: space/4 horizontal, space/4 vertical
- Radius: radius/sm
- Label: Label/Technical style, color/text/tertiary
- Value: Metadata style, color/text/primary
- Colon separator between label and value
- Truncate behavior with tooltip for long values
- Emphasis=Strong: Value uses color/text/accent
- Priority variants override emphasis for visual treatment

### 3.5 Tag/Software Component

**Purpose:** Software stack display

**Variants:**
- `softwareName: enum` — Blender, ZBrush, Substance Painter, Houdini, Unreal Engine, Maya, 3ds Max

**Component Properties:**
- `softwareName: enum` — Software type
- `icon: instance-swap` — Icon/Software/* instance

**Implementation:**
- Auto Layout (Horizontal, 4px gap)
- Background: color/surface/sunken
- Border: 1px color/border/subtle
- Radius: radius/sm
- Padding: space/4 horizontal, space/4 vertical
- Icon: 16x16 instance-swap
- Label: Label/Technical style

### 3.6 Card/Info Component

**Purpose:** Information cards in breakdown layouts with priority-based visual hierarchy

**Variants:**
- `Type=Asset Statistics`
- `Type=Material Statistics`
- `Type=Shader Statistics`
- `Type=Environment Statistics`
- `Priority=High` — Shadow/md, border color/accent/primary
- `Priority=Medium` — Shadow/sm, border color/border/default
- `Priority=Low` — No shadow, border color/border/subtle

**Component Properties:**
- `title: text` — Card title
- `rows: array` — Array of Row/Spec instances
- `showIcon: boolean` — Show type icon
- `priority: enum` — High, Medium, Low
- `groupedRows: boolean` — Enable row grouping

**Implementation:**
- Auto Layout (Vertical, space/16 gap)
- Background: color/surface/base
- Radius: radius/md
- Padding: space/24
- Title: Header/Sub style
- Rows: Vertical stack of Row/Spec instances
- Icon: 24x24 icon when showIcon=true
- Priority=High: Apply shadow/md, border color/accent/primary
- Priority=Medium: Apply shadow/sm, border color/border/default
- Priority=Low: No shadow, border color/border/subtle
- Row grouping: Add subtle background (color/surface/raised) for grouped rows with Label/Technical headers

### 3.7 Image/Plate Component

**Purpose:** Image frames with optional captions

**Variants:**
- `Type=Default` — Standard image frame
- `Type=WithCaption` — Image with caption below
- `Type=Beauty` — Full-bleed hero image

**Component Properties:**
- `imageSource: image` — Image fill
- `caption: text` — Caption text
- `showFrame: boolean` — Show decorative frame

**Implementation:**
- Auto Layout (Vertical, space/8 gap for WithCaption)
- Image: Rectangle with image fill, aspect ratio preserve
- Frame: 1px color/border/subtle when showFrame=true
- Radius: radius/lg
- Caption: Caption style, color/text/secondary
- Beauty variant: No frame, no radius, full-bleed

### 3.8 Grid/Image Component

**Purpose:** Standardized image grid layouts across templates

**Variants:**
- `Columns=2` — 2-column grid
- `Columns=3` — 3-column grid
- `Columns=4` — 4-column grid
- `Gap=16` — 16px gap (mobile)
- `Gap=24` — 24px gap (tablet)
- `Gap=32` — 32px gap (desktop)

**Component Properties:**
- `items: array` — Array of Image/Plate instances
- `columns: number` — Number of columns
- `gap: number` — Gap between items
- `minWidth: number` — Minimum item width

**Implementation:**
- Auto Layout (Horizontal, Wrap)
- Gap: 32px (desktop), 24px (tablet), 16px (mobile)
- Padding: space/24
- Min-width constraints: 280px (cards), 400px (images)
- Responsive reflow: Use variant swaps by breakpoint
- Alignment: Top-left for consistent grid alignment

### 3.9 Summary/QuickScan Component

**Purpose:** Quick-scan summary for recruiter-friendly metric visibility at top of breakdown pages

**Variants:** None

**Component Properties:**
- `triangleCount: text` — Triangle count (formatted with commas)
- `polyCount: text` — Polygon count (formatted with commas)
- `materialCount: text` — Number of materials
- `engine: text` — Engine version
- `platform: text` — Platform
- `category: text` — Project category

**Implementation:**
- Auto Layout (Horizontal, space/16 gap)
- Background: color/surface/raised
- Border: 1px color/border/subtle
- Radius: radius/md
- Padding: space/16
- Icon indicators for each metric (16x16)
- Triangle count emphasized with color/text/accent
- Horizontal wrap for mobile responsiveness
- Position: Below title block, above content sections

### 3.10 Legend/Swatch Component

**Purpose:** Material/color legend rows

**Component Properties:**
- `label: text` — Label text
- `colorSwatch: color` — Swatch color
- `description: text` — Description text

**Implementation:**
- Auto Layout (Horizontal, space/8 gap)
- Swatch: 16x16 rectangle, radius/sm
- Label: Label/Technical style
- Description: Caption style, color/text/tertiary

### 3.9 Process/Step Component

**Purpose:** Numbered steps in process breakdowns

**Component Properties:**
- `stepNumber: number` — Step number
- `title: text` — Step title
- `description: text` — Step description
- `imagePlate: instance` — Image/Plate instance

**Implementation:**
- Auto Layout (Vertical, space/16 gap)
- Number: Circle with stepNumber, background color/accent/primary
- Title: Header/Sub style
- Description: Body/Default style
- Image: Image/Plate instance

### 3.10 Brand/AssetPassport Component

**Purpose:** Signature spec plate for every portfolio artifact

**Variants:**
- `Format=Banner` — Wide horizontal banner
- `Format=Card` — Compact card
- `Format=Compact` — Minimal version
- `Theme=Light` — Light mode colors
- `Theme=Dark` — Dark mode colors

**Component Properties (Automation Schema):**
- `projectName: text` — Project name
- `category: text` — Environment / Character / Prop / VFX
- `triangleCount: text` — Triangle count (formatted with commas)
- `polyCount: text` — Polygon count (formatted with commas)
- `materialCount: text` — Number of materials
- `textureCount: text` — Number of textures
- `textureResolution: text` — Texture resolution (e.g., "4K")
- `drawCalls: text` — Draw call count
- `lod: text` — LOD levels (e.g., "LOD0–LOD3")
- `nanite: boolean` — Nanite support
- `platform: text` — Platform (e.g., "PC / Console")
- `software: array` — Array of Tag/Software instances
- `engine: text` — Engine version (e.g., "Unreal Engine 5.8")
- `date: text` — Date (e.g., "2026-03")
- `version: text` — Version number (e.g., "1.2")

**Implementation (Banner Format):**
- Auto Layout (Vertical, space/16 gap)
- Background: color/surface/inverse
- Radius: radius/md
- Padding: space/24
- Title: Title/Project style, color/text/inverse
- Tag Cluster: Horizontal wrap of Tag/Technical instances
- Software Stack: Horizontal wrap of Tag/Software instances
- Footer: Metadata style, color/text/tertiary

**Implementation (Card Format):**
- Auto Layout (Vertical, space/12 gap)
- Background: color/surface/base
- Border: 1px color/border/subtle
- Radius: radius/md
- Padding: space/16
- Title: Header/Sub style
- Tag Cluster: Vertical stack of Tag/Technical instances
- Software Stack: Horizontal wrap of Tag/Software instances

**Implementation (Compact Format):**
- Auto Layout (Horizontal, space/8 gap)
- Background: transparent
- Title: Body/Large style
- Tags: Single row of key tags only

**Critical:** Component property names must match automation schema exactly (see §9.1 of DESIGN_SYSTEM.md).

---

## 4. Template Implementation

### 4.1 Template Structure

All templates follow this structure:

```
Auto Layout (Vertical, space/64 gap)
├─ Header (Title + Breadcrumb/Pager)
├─ Content Section(s)
└─ Footer/Signature
```

### 4.2 Hero Page Template

**Structure:**
```
Auto Layout (Vertical, space/96 gap)
├─ Image/Plate[Beauty] (Full-bleed, 1920x1080)
│  └─ Overlay: Display/XL title + Asset Passport[Banner]
└─ Scroll cue (Star/4pt + "Scroll" text)
```

**Breakpoints:**
- Desktop: 1440 width, 96 margin
- Tablet: 834 width, 48 margin
- Mobile: 390 width, 24 margin

**Responsive Behavior:**
- Image/Plate: Full-width at all breakpoints
- Display/XL: 72px → 56px → 40px
- Asset Passport: Banner → Card → Compact

### 4.3 Asset Breakdown Template

**Structure:**
```
Auto Layout (Vertical, space/64 gap)
├─ Title Block (Title/Project + Tag/Technical cluster)
├─ Image/Plate[Beauty] (Beauty shot)
├─ 12-col Grid
│  ├─ Card/Info[Asset Statistics] (4 cols)
│  ├─ Image/Plate (Wireframe, 4 cols)
│  ├─ Image/Plate (UV Density, 4 cols)
│  └─ Image/Plate (Shader Complexity, 4 cols)
└─ Tag/Technical cluster (Performance metrics)
```

**Breakpoints:**
- Desktop: 12 col grid, 3-4 cards per row
- Tablet: 8 col grid, 2 cards per row
- Mobile: 4 col grid, 1 card per row (stack)

**Responsive Behavior:**
- Card grids: Use Auto Layout Wrap
- Image plates: Side-by-side → 2-up → Full-width stacked

### 4.4 Material Presentation Template

**Structure:**
```
Auto Layout (Vertical, space/64 gap)
├─ Title Block (Title/Project + Tag/Technical cluster)
├─ Image/Plate (Material hero sphere/plane)
├─ Channel Grid (4x4 grid of Image/Plate + Legend/Swatch)
│  ├─ Albedo + Legend/Swatch
│  ├─ Normal + Legend/Swatch
│  ├─ Roughness + Legend/Swatch
│  └─ Metallic/AO + Legend/Swatch
└─ Card/Info[Material Statistics]
```

**Breakpoints:**
- Desktop: 4x4 grid
- Tablet: 2x4 grid
- Mobile: 1x4 grid (stack)

**Responsive Behavior:**
- Channel Grid: Use Auto Layout Wrap with min-width constraints

### 4.5 Technical Documentation Template

**Structure:**
```
Auto Layout (Vertical, space/64 gap)
├─ Doc Header (Header/Section + Breadcrumb/Pager)
├─ TOC (Auto Layout vertical list)
├─ Body Sections (Auto Layout vertical, space/48 gap)
│  ├─ Header/Section
│  ├─ Divider/Section
│  ├─ Body/Default text
│  ├─ Callout (Code/Spec)
│  └─ Image/Plate
└─ Footer/Signature
```

**Breakpoints:**
- Desktop: 2-column layout (TOC left, content right)
- Tablet: Single column, TOC collapsed
- Mobile: Single column, TOC in accordion

**Responsive Behavior:**
- TOC: Desktop sidebar → Tablet top bar → Mobile accordion
- Content: Full-width at all breakpoints

### 4.6 Template Implementation Checklist

For each template:

- [ ] Create Desktop version first (1440px frame)
- [ ] Use Auto Layout for all containers
- [ ] Apply spacing from variables (space/8, space/16, etc.)
- [ ] Use component instances, never detached copies
- [ ] Apply text styles from token set
- [ ] Apply color variables from token set
- [ ] Test responsive reflow at Tablet (834px)
- [ ] Test responsive reflow at Mobile (390px)
- [ ] Add Footer/Signature to every template
- [ ] Add at least one Brand/AssetPassport to every template

---

## 5. Automation Setup

### 5.1 Component Property Naming

**Critical:** Component text properties must use exact names from automation schema:

| Schema Key | Component Property | Component |
|------------|-------------------|------------|
| `projectName` | `projectName` | Brand/AssetPassport |
| `category` | `category` | Brand/AssetPassport |
| `triangleCount` | `triangleCount` | Brand/AssetPassport, Tag/Technical |
| `polyCount` | `polyCount` | Brand/AssetPassport, Tag/Technical |
| `materialCount` | `materialCount` | Brand/AssetPassport, Tag/Technical |
| `textureCount` | `textureCount` | Brand/AssetPassport, Tag/Technical |
| `textureResolution` | `textureResolution` | Brand/AssetPassport, Tag/Technical |
| `drawCalls` | `drawCalls` | Brand/AssetPassport, Tag/Technical |
| `lod` | `lod` | Brand/AssetPassport, Tag/Technical |
| `nanite` | `nanite` | Brand/AssetPassport, Tag/Technical |
| `platform` | `platform` | Brand/AssetPassport, Tag/Technical |
| `software` | `software` | Brand/AssetPassport (array of Tag/Software) |
| `engine` | `engine` | Brand/AssetPassport, Tag/Technical |
| `date` | `date` | Brand/AssetPassport, Tag/Technical |
| `version` | `version` | Brand/AssetPassport, Tag/Technical |

**Do not** rename these properties. Automation depends on exact string matches.

### 5.2 Instance-Swap Properties

Lists (e.g., `software`) use instance-swap:

**Tag/Software Component:**
- Property: `softwareName: enum`
- Values: Blender, ZBrush, Substance Painter, Houdini, Unreal Engine, Maya, 3ds Max
- Icon: Instance-swap to Icon/Software/* based on softwareName

**Automation Behavior:**
- Plugin reads `software: ["Blender", "ZBrush"]` from JSON
- Plugin creates/duplicates Tag/Software instances
- Plugin sets `softwareName` property on each instance
- Plugin swaps icon based on softwareName

### 5.3 Figma Plugin Integration

**Required Plugin:**
- Custom plugin or Figma API integration for JSON → Component property mapping

**Plugin Workflow:**
1. Read `portfolio_manifest.json` from Unreal pipeline
2. Find all instances of `Brand/AssetPassport` in file
3. For each instance, set component properties from JSON
4. Find all instances of `Card/Info` in file
5. For each card, populate `Row/Spec` rows from JSON
6. Find all instances of `Tag/Technical` in file
7. For each tag, set label/value from JSON
8. Commit changes with transaction (rollback on error)

**Error Handling:**
- If component property not found: Log warning, skip property
- If component instance not found: Log warning, skip instance
- If data type mismatch: Log error, rollback transaction
- If file not writable: Log error, abort

### 5.4 MCP Server Integration

**MCP Action:**
```
populate_passport(fileKey, nodeId, data)
```

**Parameters:**
- `fileKey: string` — Figma file key
- `nodeId: string` — Target node ID (Brand/AssetPassport instance)
- `data: object` — JSON object matching §9.1 schema

**Response:**
```json
{
  "success": true,
  "updatedProperties": ["projectName", "triangleCount", "engine"],
  "errors": []
}
```

**Implementation:**
- MCP server wraps Figma REST API calls
- Handles authentication via Figma access token
- Implements rate limiting (100 requests/minute)
- Caches component property schemas for performance

---

## 6. Responsive Implementation

### 6.1 Breakpoint Frames

Create three frames for each template in **06 Templates** page:

```
TemplateName/Desktop (1440x1080)
TemplateName/Tablet (834x1194)
TemplateName/Mobile (390x844)
```

**Naming Convention:** Use exact format above.

### 6.2 Auto Layout Settings

**Container Auto Layout:**
- Direction: Vertical (page), Horizontal (sections)
- Padding: space/24 (mobile), space/48 (tablet), space/96 (desktop)
- Gap: space/16 (components), space/32 (sections), space/64 (major)
- Alignment: Left (text), Center (hero), Top (stacks)

**Grid Auto Layout:**
- Direction: Horizontal
- Gap: space/24 (desktop), space/16 (tablet), space/8 (mobile)
- Wrap: Yes (for card grids)
- Min Width: 280px (cards), 1fr (images)

**Component Auto Layout:**
- Direction: Horizontal (tags), Vertical (cards)
- Gap: space/8 (tight), space/16 (default)
- Padding: space/8 (chips), space/16 (controls), space/24 (cards)

### 6.3 Responsive Variant Swaps

**Type Scale Swaps:**
- Display/XL → Display/Large → Title/Project
- Title/Project → Header/Section → Header/Sub
- Header/Section → Header/Sub → Body/Large

**Passport Format Swaps:**
- Banner → Card → Compact

**Card Grid Swaps:**
- 4-up → 2-up → 1-up (stack)

**Image Plate Swaps:**
- Side-by-side → 2-up → Full-width stacked

**Implementation:**
- Use component variants for breakpoint-specific styles
- Swap variants manually or via responsive plugin
- Do not free-scale text sizes

### 6.4 Responsive Testing Checklist

For each template:

- [ ] Test at 1440px (Desktop)
- [ ] Test at 834px (Tablet)
- [ ] Test at 390px (Mobile)
- [ ] Test at 1920px (Large Desktop)
- [ ] Test at 768px (Small Tablet)
- [ ] Test at 428px (Large Mobile)
- [ ] Verify text remains legible at all breakpoints
- [ ] Verify images maintain aspect ratio
- [ ] Verify Auto Layout wraps correctly
- [ ] Verify no horizontal scroll at mobile
- [ ] Verify touch targets ≥ 44px on mobile

---

## 7. Dark Mode Implementation

### 7.1 Variable Mode Switching

**Collection: Color**
- Modes: `Light`, `Dark`
- Default Mode: `Light`

**Switching Method:**
1. Select all frames in file
2. Use "Variables" panel → "Mode" dropdown
3. Switch from `Light` to `Dark`
4. All color variables update automatically

**Implementation Tip:** Create a "Dark Mode Preview" frame to test dark mode without switching entire file.

### 7.2 Component Dark Mode Variants

**Components Requiring Dark Mode Variants:**
- Brand/AssetPassport (`Theme=Dark`)
- Card/Info (background color variable)
- Image/Plate (frame color variable)
- Divider/Section (line color variable)
- Star/* (opacity adjustment)
- Frame/Corner (color adjustment)

**Implementation:**
- Add `Theme` property to components
- Create `Theme=Light` and `Theme=Dark` variants
- Bind colors to semantic variables (color/surface/base, etc.)
- Variables automatically switch based on mode

### 7.3 Dark Mode Motif Adjustments

**Star/8pt:**
- Light Mode: gold/500, opacity 100%
- Dark Mode: gold/300, opacity 75%

**Star/4pt:**
- Light Mode: gold/500, opacity 100%
- Dark Mode: gold/300, opacity 50%

**Constellation:**
- Light Mode: ivory/300, opacity 12%
- Dark Mode: astral/500, opacity 8%

**Frame/Corner:**
- Light Mode: gold/500 stroke
- Dark Mode: gold/300 stroke

**Glow Effects:**
- Light Mode: glow/gold
- Dark Mode: glow/astral

**Implementation Tip:** Use variable opacity for motif components to enable mode switching.

### 7.4 Dark Mode Testing Checklist

- [ ] Switch all variables to Dark mode
- [ ] Verify all components update correctly
- [ ] Verify text contrast ratios ≥ 4.5:1
- [ ] Verify gold accents remain visible
- [ ] Verify glow effects read well on dark backgrounds
- [ ] Verify image frames have appropriate contrast
- [ ] Verify decorative elements don't compete with content
- [ ] Test on actual dark background (not just in Figma)

---

## 8. Accessibility Implementation

### 8.1 Color Contrast Validation

**Target Contrast Ratios:**
- Body text on surface base: ≥ 7:1 (AAA)
- Secondary text on surface base: ≥ 4.5:1 (AA)
- Gold accent text: ≥ 4.5:1 (AA)

**Validation Tools:**
- Figma "Stark" plugin for contrast checking
- WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/)

**Known Valid Combinations (Light Mode):**
- plum/800 on ivory/100: 12.5:1 (AAA)
- slate/500 on ivory/100: 7.2:1 (AAA)
- gold/700 on ivory/100: 4.8:1 (AA)
- slate/400 on ivory/100: 4.2:1 (AA)

**Known Valid Combinations (Dark Mode):**
- ivory/50 on astral/900: 14.1:1 (AAA)
- slate/300 on astral/900: 8.3:1 (AAA)
- gold/300 on astral/900: 5.1:1 (AA)
- slate/400 on astral/900: 4.7:1 (AA)

**Implementation Tip:** Document contrast ratios for all color combinations in component descriptions.

### 8.2 Typography Accessibility

**Minimum Font Size:**
- Body text: 16px (Body/Default)
- Metadata: 12px (Label/Technical) — minimum acceptable
- Captions: 13px (Caption)

**Line Height Ratios:**
- Body text: 1.6–1.8 (26px for 16px)
- Headings: 1.2–1.4
- Mono: 1.3–1.5

**Letter Spacing:**
- Body text: 0em (default)
- Mono labels: 0.06–0.08em (uppercase)
- Display text: -0.01 to -0.02em (negative tracking)

**Implementation Tip:** Use relative units (em) for letter spacing to scale with font size.

### 8.3 Component Accessibility

**Focus States:**
- Add `Focus` variant to all interactive components
- Focus ring: 2px solid color/accent/astral
- Focus offset: 2px outside component
- Focus radius: Match component radius

**ARIA Labels:**
- Add `ariaLabel` property to all interactive components
- Use descriptive labels (e.g., "Download project files" not "Download")
- Include context in labels (e.g., "Close modal" not "Close")

**Keyboard Navigation:**
- Define tab order for interactive elements
- Ensure all interactive elements are keyboard-accessible
- Provide keyboard shortcuts for common actions (Escape to close modal)

**Screen Reader Support:**
- Add `srText` property for screen-reader-only text
- Use semantic HTML structure when exporting
- Provide alt text for all images

**Implementation Tip:** Create an "Accessibility" variant set for components with focus states and ARIA labels.

### 8.4 Reduced Motion Support

**Animation Variants:**
- Add `ReducedMotion` variant to animated components
- Reduced Motion: Disable all animations, use instant transitions
- Default: Use smooth transitions (150–300ms)

**Implementation:**
- Use Figma "Smart Animate" for transitions
- Set duration to 0ms for Reduced Motion variant
- Respect user's OS reduced-motion preference when exporting

---

## 9. Publishing & Distribution

### 9.1 Publish as Figma Library

**Steps:**
1. Complete all components and templates
2. Run accessibility validation
3. Test responsive behavior at all breakpoints
4. Test dark mode switching
5. Test automation with sample JSON
6. Publish file as team library
7. Enable library for all team members
8. Document library URL in DESIGN_SYSTEM.md

**Library Settings:**
- Name: "Environment Portfolio Design System"
- Description: "Design system for Environment Portfolio Platform"
- Version: 1.0 (increment on major changes)
- Access: Team (or Organization if available)

### 9.2 Component Publishing

**Publish Checklist:**
- [ ] All components have descriptions
- [ ] All component properties have descriptions
- [ ] All variants have descriptive names
- [ ] All components use variables for colors/spacing
- [ ] All components use text styles
- [ ] All components are properly named (Category/Component)
- [ ] No default names (Frame 12, Group 3)
- [ ] No detached instances in library
- [ ] All components are responsive
- [ ] All components have dark mode variants

### 9.3 Template Distribution

**Template Access:**
- Publish templates as separate pages in library file
- Or create separate "Templates" file linked to library
- Document template usage in guide

**Template Versioning:**
- Version templates separately from components
- Use semantic versioning (1.0, 1.1, 2.0)
- Document breaking changes in changelog

### 9.4 Export for ArtStation/Web

**Export Settings:**
- Format: PNG (for images), SVG (for icons)
- Scale: 1x, 2x (for retina)
- Color Profile: sRGB
- Compression: PNG-24 (lossless)

**Export Workflow:**
1. Create export variants on Image/Plate components
2. Set export settings: PNG @ 2x
3. Batch export all plates from templates
4. Organize exports by project/template
5. Upload to ArtStation or web platform

**Implementation Tip:** Use Figma "Batch Export" plugin for efficient bulk exports.

---

## 10. Maintenance Workflow

### 10.1 Version Control

**File Versioning:**
- Use Figma's version history for major changes
- Document version changes in changelog
- Tag versions in DESIGN_SYSTEM.md

**Component Versioning:**
- When changing component structure: increment major version (1.0 → 2.0)
- When adding new variants: increment minor version (1.0 → 1.1)
- When fixing bugs: increment patch version (1.0 → 1.0.1)

**Breaking Changes:**
- Document breaking changes in changelog
- Notify team members of breaking changes
- Provide migration guide for breaking changes
- Deprecate old components before removing (move to Archive page)

### 10.2 Update Process

**When Updating Design System:**

1. **Update DESIGN_SYSTEM.md** with design changes
2. **Regenerate tokens.json** if color/spacing/type changes
3. **Update Figma variables** to match new tokens
4. **Update Figma components** to match new spec
5. **Update Unreal Python scripts** if schema changes
6. **Test pipeline end-to-end** with sample data
7. **Publish library update** with new version
8. **Notify team** of changes

**Update Checklist:**
- [ ] DESIGN_SYSTEM.md updated
- [ ] tokens.json regenerated
- [ ] Figma variables updated
- [ ] Figma components updated
- [ ] Unreal scripts updated (if needed)
- [ ] Pipeline tested
- [ ] Library published
- [ ] Team notified

### 10.3 Validation

**Pre-Publish Validation:**
- [ ] All templates pass responsive testing (Desktop/Tablet/Mobile)
- [ ] All automation schemas match component property names exactly
- [ ] All Unreal extraction scripts produce valid JSON per schema
- [ ] Accessibility compliance checked on each update
- [ ] Dark mode tested on all components
- [ ] Contrast ratios validated for all color combinations
- [ ] No console errors in Figma
- [ ] No detached instances in library

**Post-Publish Validation:**
- [ ] Library accessible to all team members
- [ ] Components appear in component panel
- [ ] Templates can be instantiated from library
- [ ] Automation plugin works with published library
- [ ] Export settings work correctly

### 10.4 Changelog

**Changelog Format:**
```markdown
## [1.1.0] - 2026-06-25

### Added
- Layout/SplitView component for LOD comparisons
- Chart/Bar component for performance visualization
- Text/CodeBlock component for shader code display

### Changed
- Asset Passport schema: Added author, client, license fields
- Card/Info: Added collapsible variant
- Image/Plate: Added zoomable property

### Fixed
- Dark mode contrast ratio for gold text on ivory
- Mobile responsive behavior for Tag/Technical clusters

### Deprecated
- Tag/Software (old variant) — use Tag/Software v2
```

**Changelog Location:**
- Add changelog section to DESIGN_SYSTEM.md
- Or create separate CHANGELOG.md file
- Link to changelog from DESIGN_SYSTEM.md

---

## Appendix A: Quick Reference

### A.1 Component Property Names

**Brand/AssetPassport:**
```
projectName, category, triangleCount, polyCount, materialCount, 
textureCount, textureResolution, drawCalls, lod, nanite, 
platform, software, engine, date, version
```

**Tag/Technical:**
```
label, value, emphasis
```

**Tag/Software:**
```
softwareName, icon
```

**Card/Info:**
```
title, rows, showIcon
```

**Row/Spec:**
```
key, value
```

**Image/Plate:**
```
imageSource, caption, showFrame
```

### A.2 Variable Names

**Colors:**
```
color/surface/base, color/surface/raised, color/surface/sunken, 
color/surface/inverse, color/text/primary, color/text/secondary, 
color/text/tertiary, color/text/inverse, color/text/accent, 
color/border/subtle, color/border/default, color/border/strong, 
color/accent/primary, color/accent/secondary, color/accent/tertiary, 
color/accent/astral, color/accent/iris, color/rule/gold, 
color/feedback/success, color/feedback/warning, 
color/feedback/error, color/feedback/info
```

**Spacing:**
```
space/4, space/8, space/16, space/24, space/32, 
space/48, space/64, space/96, space/128
```

**Radius:**
```
radius/none, radius/sm, radius/md, radius/lg, radius/pill
```

### A.3 Text Style Names

```
Display/XL, Display/Large, Title/Project, Header/Section, 
Header/Sub, Body/Large, Body/Default, Caption, 
Label/Technical, Metadata
```

### A.4 Effect Names

```
shadow/sm, shadow/md, glow/gold, glow/astral
```

---

## Appendix B: Troubleshooting

### B.1 Component Not Updating from Automation

**Symptom:** Component properties not changing after plugin runs.

**Possible Causes:**
1. Component property name doesn't match schema
2. Component instance is detached
3. Plugin doesn't have write permissions
4. JSON data type mismatch (string vs number)

**Solutions:**
1. Verify property names match schema exactly (case-sensitive)
2. Re-instantiate component from library
3. Check plugin permissions in Figma
4. Verify JSON data types match property types

### B.2 Dark Mode Not Switching

**Symptom:** Colors not updating when switching to Dark mode.

**Possible Causes:**
1. Component uses hard-coded colors instead of variables
2. Variable mode not switched
3. Component doesn't have dark mode variant

**Solutions:**
1. Replace hard-coded colors with variable bindings
2. Switch variable mode in Variables panel
3. Add Theme=Dark variant to component

### B.3 Responsive Layout Breaking

**Symptom:** Layout breaks at certain breakpoints.

**Possible Causes:**
1. Auto Layout not set to Wrap
2. Min/max width constraints not set
3. Text not using variant swaps

**Solutions:**
1. Set Auto Layout to Wrap for card/tag grids
2. Set min-width constraints on cards (min 280px)
3. Use component variant swaps for text size changes

### B.4 Contrast Ratio Failing

**Symptom:** Contrast checker fails for color combination.

**Possible Causes:**
1. Color combination not in valid palette
2. Using gold for body text
3. Dark mode colors not optimized

**Solutions:**
1. Use only documented color combinations
2. Never use gold for body text (only accents)
3. Adjust dark mode colors for better contrast

---

**End of Figma Implementation Guide**
