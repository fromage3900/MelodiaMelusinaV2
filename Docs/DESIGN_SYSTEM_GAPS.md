# Design System Gaps Analysis

**Analysis Date:** 2026-06-25  
**Last Updated:** 2026-06-25 (Cycle 1 Implementation)  
**Scope:** Hero Pages, Breakdown Pages, Material Presentation Pages, Technical Documentation Pages  
**Constraint:** Presentation-layer analysis only — no engine changes proposed  
**Bridge Layer Context:** Unreal-to-Figma mapping validation and automation readiness

---

## Cycle 1 Resolved Gaps (2026-06-25)

### Visual Hierarchy Improvements
- ✅ **Added Summary/QuickScan component** — Provides recruiter-friendly metric visibility at top of breakdown pages
- ✅ **Enhanced Tag/Technical with priority system** — Critical/High/Medium/Low variants for visual hierarchy
- ✅ **Enhanced Divider/Section with labeled variants** — Strong/Medium/Subtle weights with optional labels
- ✅ **Enhanced Card/Info with priority system** — High/Medium/Low variants for card importance

### Layout Consistency Improvements
- ✅ **Added Grid/Image component** — Standardized image grid layouts across templates
- ✅ **Updated component hierarchy** — Added Summary/QuickScan to Composites, Grid/Image to Layouts

### Documentation Updates
- ✅ **Updated DESIGN_SYSTEM.md** — Added new components and enhanced existing ones
- ✅ **Updated FIGMA_IMPLEMENTATION_GUIDE.md** — Added implementation details for new components

**Remaining High-Priority Gaps:**
- Missing navigation components (Nav/TabBar, Nav/Sidebar, Nav/Pagination)
- Missing data visualization components (Chart/Bar, Chart/Line)
- Missing comparison layout components (Layout/SplitView, Layout/Tabs)
- Dark mode variants for decorative components incomplete

---

---

## Executive Summary

The design system provides a strong foundation with 8 mapped Unreal data emission points to Figma layouts. However, **3 of 10 templates lack Unreal data sources**, and **critical UI components are missing** for complete portfolio presentation.

**Bridge Layer Assessment:**
- ✓ All 14 Brand/AssetPassport properties have Unreal sources (some require audit scripts)
- ✓ All 5 portfolio templates have defined mapping rules
- ✓ Data transformation rules documented
- ⚠ Unreal output schema gaps: scene_metadata.json missing key asset statistics
- ⚠ Optional Figma schema fields not defined (author, client, license, etc.)

**Critical Gaps:**
- 3 templates (Shader Breakdown, Commission Sheet, Artbook Spread) have no Unreal emission mapping
- Missing navigation and interaction components
- No data visualization components for complex metrics
- Missing comparison/side-by-side layout components

---

## 1. Unreal-to-Figma Mapping Validation

### 1.1 Mapped Data Flows (8/8 Complete)

| # | Unreal Source | Monolith Action | Figma Template | Figma Component | Status |
|---|---------------|-----------------|----------------|-----------------|--------|
| 1 | Hero Renders | `capture_scene_preview` | Hero Page | `Image/Plate[Beauty]` | ✓ Complete |
| 2 | Breakdown Renders | `capture_with_overlay` | Asset/Environment Breakdown | `Image/Plate` grid | ✓ Complete |
| 3 | Material Sheets | `capture_material_grid` | Material Presentation | Channel Grid | ✓ Complete |
| 4 | Trim Sheet Renders | `capture_scene_preview` + overlay | Trim Sheet Presentation | `Image/Plate` | ✓ Complete |
| 5 | Asset Statistics | Python audit scripts | All templates | `Brand/AssetPassport`, `Card/Info` | ✓ Complete |
| 6 | Technical Documentation | `inspect_material_pbr` | Technical Documentation | `Header/Section`, `Divider/Section`, `Callout` | ✓ Complete |
| 7 | PCG Diagrams | `pcg_graph_builder.py` + captures | Process Breakdown | `Process/Step` | ✓ Complete |
| 8 | Performance Captures | `csv_profile` | Asset/Environment Breakdown | `Tag/Technical` clusters, `Card/Info` | ✓ Complete |

**Assessment:** All 8 defined emission points have clear Monolith MCP action paths and Figma component mappings. The pipeline is technically sound for these data types.

### 1.2 Bridge Layer Schema Validation

**Brand/AssetPassport Property Mapping (14/14 Complete):**

| Property | Unreal Source | Source Type | Transformation | Status |
|----------|---------------|-------------|----------------|--------|
| projectName | Asset metadata | JSON | Direct mapping | ✓ |
| category | Asset metadata | JSON | Direct mapping | ✓ |
| triangleCount | Asset metadata | JSON | Number → formatted string | ✓ |
| polyCount | Asset metadata | JSON | Number → formatted string | ✓ |
| materialCount | Scene metadata | JSON | Number → formatted string | ✓ |
| textureCount | Asset metadata | JSON | Number → formatted string | ✓ |
| textureResolution | Asset metadata | JSON | Direct mapping | ✓ |
| drawCalls | Asset metadata | JSON | Number → formatted string | ✓ |
| lod | Asset metadata | JSON | Direct mapping | ✓ |
| nanite | Asset metadata | JSON | Boolean → string | ✓ |
| platform | Asset metadata | JSON | Direct mapping | ✓ |
| software | Asset metadata | JSON | Array → instance-swap | ✓ |
| engine | Scene metadata | JSON | Format with prefix | ✓ |
| date | Scene metadata | JSON | ISO → YYYY-MM | ✓ |
| version | Asset metadata | JSON | Direct mapping | ✓ |

**Schema Gap Analysis:**
- ✓ All required properties have Unreal sources
- ⚠ Some properties require separate audit scripts (not in scene_metadata.json)
- ⚠ Optional properties (author, client, license, projectUrl) not in current schema
- ⚠ Unreal output schema lacks triangleCount, polyCount, textureCount, drawCalls in scene_metadata.json

**Resolution Required:**
- scene_metadata.json must be augmented with asset statistics, OR
- Bridge layer must merge data from multiple sources (scene_metadata.json + audit scripts)

### 1.3 Unmapped Templates (3/10 Templates)

| Template | Current Status | Gap Type | Impact |
|----------|----------------|----------|--------|
| **Shader Breakdown** | No Unreal emission defined | Data source missing | Cannot auto-populate node graphs, parameter tables, math notes |
| **Commission Sheet** | No Unreal emission defined | Data source missing | Cannot auto-populate service tiers, pricing, ToS |
| **Artbook Spread** | No Unreal emission defined | Data source missing | Cannot auto-populate editorial text, page layouts |

**Assessment:** These templates are designed for manual authoring. This may be intentional (Commission Sheet is business-facing, Artbook Spread is editorial). However, if automation is desired, Unreal emission points must be defined.

### 1.4 Unreal Output Schema Gaps (Bridge Layer Specific)

**scene_metadata.json Schema (from scene_metadata_exporter.py):**
```json
{
  "level_name": "string",
  "level_path": "string",
  "engine_version": "string",
  "timestamp": "string",
  "static_mesh_actors": [{"label": "string", "mesh": "string", "materials": ["string"]}],
  "materials": ["string"],
  "material_instances": ["string"],
  "counts": {
    "static_mesh_actors": "number",
    "materials": "number",
    "material_instances": "number"
  }
}
```

**Missing Fields for Complete Automation:**
- `triangleCount` — Not captured by scene_metadata_exporter.py
- `polyCount` — Not captured by scene_metadata_exporter.py
- `textureCount` — Not captured by scene_metadata_exporter.py
- `textureResolution` — Not captured by scene_metadata_exporter.py
- `drawCalls` — Not captured by scene_metadata_exporter.py
- `lod` — Not captured by scene_metadata_exporter.py
- `nanite` — Not captured by scene_metadata_exporter.py
- `platform` — Not captured by scene_metadata_exporter.py
- `software` — Not captured by scene_metadata_exporter.py
- `version` — Not captured by scene_metadata_exporter.py
- `projectName` — Not captured by scene_metadata_exporter.py
- `category` — Not captured by scene_metadata_exporter.py

**Bridge Layer Impact:**
- Bridge layer must merge data from multiple sources to populate Brand/AssetPassport
- Requires running separate audit scripts (audit_pcg_portfolio.py, audit_material_library.py)
- Increases complexity of data collection phase
- Requires manual configuration for fields not auto-captured (platform, software, version)

**Recommended Resolution:**
1. Augment scene_metadata_exporter.py to capture basic asset statistics
2. Create a unified portfolio_manifest.json that merges all data sources
3. Add project configuration file for manual fields (platform, software, version)

---

## 2. Bridge Layer Missing UI Components

### 2.1 Components Required for Automation

**Data Source Indicator Component:**
- **`Badge/DataSource`** — Badge indicating data origin (Unreal, Manual, Hybrid)
  - Properties: `sourceType` (enum: unreal, manual, hybrid), `sourceScript` (string)
  - Use case: Tag components to show which data came from Unreal vs manual entry
  - Impact: Without this, users cannot distinguish automated vs manual content

**Validation Status Component:**
- **`Badge/Validation`** — Badge indicating data validation status
  - Properties: `status` (enum: valid, warning, error, pending), `message` (string)
  - Use case: Show which components have valid data vs missing/invalid data
  - Impact: Without this, users cannot identify incomplete or erroneous data

**Sync Status Component:**
- **`Badge/Sync`** — Badge indicating last sync time with Unreal
  - Properties: `lastSync` (timestamp), `syncSource` (string)
  - Use case: Show when data was last pulled from Unreal
  - Impact: Without this, users cannot determine data freshness

### 2.2 Components Required for Multi-Source Data Merging

**Merge Indicator Component:**
- **`Info/MergeSource`** — Info component showing data source composition
  - Properties: `sources` (array of {name, contribution}), `primarySource` (string)
  - Use case: Show that Brand/AssetPassport data comes from scene_metadata.json + audit scripts
  - Impact: Without this, users cannot understand data provenance

**Missing Data Placeholder Component:**
- **`Placeholder/MissingData`** — Placeholder for components with missing data
  - Properties: `field` (string), `source` (string), `action` (string)
  - Use case: Show "triangleCount not available in scene_metadata.json, run audit script"
  - Impact: Without this, missing fields are silently skipped, confusing users

---

## 3. Missing UI Components

### 3.1 Critical Missing Components

#### Navigation Components
- **`Nav/TabBar`** — Tab navigation for multi-section breakdowns
- **`Nav/Sidebar`** — Left navigation for documentation pages
- **`Nav/Pagination`** — Previous/Next page controls for multi-page portfolios
- **`Nav/AnchorLink`** — In-page jump links for long documentation

**Impact:** Technical Documentation and long breakdown pages lack navigation structure. Users cannot easily jump between sections.

#### Data Visualization Components
- **`Chart/Bar`** — Bar charts for performance metrics (FPS, draw calls over time)
- **`Chart/Line`** — Line graphs for memory usage, GPU time
- **`Chart/Pie`** — Pie charts for material distribution, texture memory
- **`Table/Sortable`** — Sortable data tables for asset inventories
- **`Table/Comparison`** — Side-by-side comparison tables (LOD levels, material variants)

**Impact:** Performance data from `csv_profile` cannot be visualized effectively. Raw numbers in `Tag/Technical` clusters are insufficient for trend analysis.

#### Comparison Layout Components
- **`Layout/SplitView`** — Side-by-side comparison layout (Before/After, LOD0/LOD1)
- **`Layout/Carousel`** — Horizontal carousel for image sequences
- **`Layout/Accordion`** — Expandable sections for detailed technical notes
- **`Layout/Tabs`** — Tabbed content areas for multi-variant materials

**Impact:** Cannot present LOD comparisons, material variants, or iterative process steps effectively.

#### Interactive Components
- **`Modal/Lightbox`** — Lightbox for full-size image viewing
- **`Tooltip/Info`** — Hover tooltips for technical terms
- **`Toggle/Switch`** — Theme toggle (Light/Dark mode)
- **`Search/Filter`** — Search/filter controls for asset libraries

**Impact:** Portfolio lacks interactive depth. Users cannot zoom images, switch themes, or filter content.

#### Media Components
- **`Video/Player`** — Video player for animated breakdowns, real-time captures
- **`Gallery/Grid`** — Masonry or grid gallery for screenshot collections
- **`Carousel/Image`** — Image carousel with navigation controls

**Impact:** Cannot present animated content (Niagara systems, cloth simulation, water effects) or large screenshot galleries.

#### Annotation Components
- **`Annotation/Marker`** — Numbered markers with callout lines for image annotations
- **`Annotation/Hotspot`** — Clickable hotspots with pop-up information
- **`Annotation/Overlay`** — Transparent overlay with labeled regions

**Impact:** Cannot annotate breakdown renders with specific technical callouts (e.g., "UV seam here", "LOD transition point").

### 3.2 Secondary Missing Components

#### Typography Components
- **`Text/CodeBlock`** — Syntax-highlighted code blocks for shader graphs, Python scripts
- **`Text/Quote`** — Blockquote for testimonials, design philosophy
- **`Text/Definition`** — Definition list for glossary terms

**Impact:** Technical Documentation lacks code presentation capability. Shader breakdowns cannot show HLSL/GLSL code.

#### Feedback Components
- **`Progress/Bar`** — Progress bars for loading states, completion status
- **`Badge/Status`** — Status badges (In Progress, Completed, Deprecated)
- **`Alert/Banner`** — Alert banners for important notices

**Impact:** Cannot communicate project status or workflow state.

#### Input Components
- **`Input/TextField`** — Text input for search/filter
- **`Input/Select`** — Dropdown selects for filtering
- **`Input/Checkbox`** — Checkboxes for multi-select filters

**Impact:** Portfolio is read-only. No interactive filtering or search capability.

---

## 4. Layout Template Gaps

### 4.1 Hero Page Template

**Current Structure:**
- Full-bleed beauty `Image/Plate[Beauty]`
- `Display/XL` title overlay
- `Asset Passport[Banner]`
- Scroll cue

**Identified Gaps:**
1. **No subtitle/description field** — Hero lacks descriptive text below title
2. **No navigation preview** — No indication of sections within the portfolio
3. **No variant selector** — Cannot switch between different hero treatments (Constellation, Nebula, etc.)
4. **No download/CTA** — No call-to-action for downloading assets or viewing project files

**Recommendation:** Add optional `Text/Body` description, `Nav/AnchorLink` section preview, and `Button/Download` component.

### 4.2 Asset Breakdown Template

**Current Structure:**
- Title block
- Beauty shot
- 12-col grid of `Card/Info[Asset Statistics]` + wireframe/UV plates
- `Tag/Technical` cluster

**Identified Gaps:**
1. **No LOD comparison** — Cannot show LOD0/LOD1/LOD2 side-by-side
2. **No material variant comparison** — Cannot show material variations (day/night, wet/dry)
3. **No annotation system** — Cannot annotate specific mesh features
4. **No performance visualization** — Performance data is raw tags, not charts

**Recommendation:** Add `Layout/SplitView` for LOD comparisons, `Layout/Tabs` for material variants, `Annotation/Marker` for feature callouts, `Chart/Bar` for performance data.

### 4.3 Environment Breakdown Template

**Current Structure:**
- Wide beauty
- "Composition" annotated plate
- Modular-kit grid
- Lighting passes row
- `Card/Info` stats

**Identified Gaps:**
1. **No lighting comparison** — Cannot show time-of-day variations
2. **No PCG visualization** — PCG diagrams are mapped to Process Breakdown, not Environment Breakdown
3. **No interactive exploration** — Cannot toggle visibility of layers (foliage, water, architecture)
4. **No camera path visualization** — Cannot show camera movement paths for cinematics

**Recommendation:** Add `Layout/Tabs` for lighting variations, integrate PCG visualization, add layer toggle controls, include camera path overlays.

### 4.4 Material Presentation Template

**Current Structure:**
- Material hero sphere/plane
- Channel grid (Albedo/Normal/Roughness/etc.)
- `Card/Info[Material Statistics]`

**Identified Gaps:**
1. **No material variant comparison** — Cannot show parameter variations (roughness 0.2 vs 0.8)
2. **No shader code display** — Cannot show HLSL/GLSL shader code
3. **No material graph visualization** — Cannot show Unreal material node graph
4. **No texture breakdown** — Cannot show individual texture maps with explanations

**Recommendation:** Add `Layout/SplitView` for parameter variations, `Text/CodeBlock` for shader code, `Image/Plate` for material graph, expandable texture breakdown section.

### 4.5 Technical Documentation Template

**Current Structure:**
- Doc header + `Breadcrumb/Pager`
- TOC
- Body sections with `Header/Section` + `Divider`
- Code/spec `Callout`

**Identified Gaps:**
1. **No code syntax highlighting** — `Callout` is not designed for code
2. **No search functionality** — Cannot search within documentation
3. **No collapsible sections** — Long docs cannot collapse sections
4. **No version history** — Cannot show changelog or version differences
5. **No print/export styling** — No consideration for PDF export

**Recommendation:** Add `Text/CodeBlock` with syntax highlighting, `Search/Filter` component, `Layout/Accordion` for collapsible sections, version history component, print-specific styles.

---

## 5. Component Property Schema Gaps

### 5.1 Asset Passport Schema

**Current Schema (§9.1):**
```json
{
  "projectName": "string",
  "category": "string",
  "triangleCount": "number",
  "polyCount": "number",
  "materialCount": "number",
  "textureCount": "number",
  "textureResolution": "string",
  "drawCalls": "number",
  "lod": "string",
  "nanite": "boolean",
  "platform": "string",
  "software": ["string"],
  "engine": "string",
  "date": "string",
  "version": "string"
}
```

**Missing Properties:**
- `author` — Creator name/team
- `client` — Client name (for commissioned work)
- `projectUrl` — External project URL (ArtStation, website)
- `license` — License type (CC-BY, Commercial, etc.)
- `tags` — Free-form tags for categorization
- `description` — Short project description
- `thumbnail` — Thumbnail image path

**Impact:** Cannot attribute work, link to external portfolios, or provide licensing information.

### 5.2 Card/Info Schema

**Current Schema:**
- `title` — string
- `rows` — array of `Row/Spec`
- `showIcon` — boolean

**Missing Properties:**
- `collapsible` — boolean (for expandable cards)
- `defaultExpanded` — boolean (initial state)
- `badge` — string (status badge)
- `iconType` — string (icon variant)

**Impact:** Cannot create collapsible info cards or show status indicators.

### 5.3 Image/Plate Schema

**Current Schema:**
- `imageSource` — string
- `caption` — string
- `showFrame` — boolean

**Missing Properties:**
- `zoomable` — boolean (enable lightbox)
- `annotations` — array of annotation objects
- `altText` — string (accessibility)
- `aspectRatio` — string (force aspect ratio)
- `loadingState` — string (skeleton, placeholder)

**Impact:** Cannot add interactive zoom, annotations, or accessibility features.

---

## 6. Responsive Design Gaps

### 6.1 Breakpoint Coverage

**Current Breakpoints:**
- Desktop: 1440px (12 col)
- Tablet: 834px (8 col)
- Mobile: 390px (4 col)

**Missing Breakpoints:**
- **Large Desktop (1920px)** — For ultra-wide displays
- **Small Tablet (768px)** — For portrait tablets
- **Large Mobile (428px)** — For modern large phones

**Impact:** Layout may break on non-standard screen sizes.

### 6.2 Component Responsiveness

**Issues Identified:**
1. **`Tag/Technical` clusters** — Wrap behavior not specified for very long values
2. **`Card/Info`** — Minimum width not defined for mobile
3. **`Image/Plate`** — Aspect ratio handling not specified for different breakpoints
4. **`Process/Step`** — Timeline layout not defined for mobile (vertical vs horizontal)

**Recommendation:** Define explicit reflow rules for each component at all breakpoints.

---

## 7. Accessibility Gaps

### 7.1 Color Contrast

**Current Floor (§2.4):**
- Body text on surface base: target ≥ 7:1 (AAA)
- Secondary text on surface base: ≥ 4.5:1
- Gold never used for body text

**Missing:**
- No contrast ratios specified for gold text on ivory
- No contrast ratios for accent colors (lavender, sakura, astral, iris)
- No focus states defined for interactive components

**Recommendation:** Calculate and document contrast ratios for all color combinations. Define focus ring styles.

### 7.2 Typography Accessibility

**Current Rules (§3.3):**
- Numbers in IBM Plex Mono
- Measure: 60–75 characters

**Missing:**
- No minimum font size specified (currently 11px for Metadata)
- No line-height ratios documented
- No letter-spacing limits for accessibility

**Recommendation:** Set minimum font size to 12px. Document line-height ratios (1.5–1.8). Limit letter-spacing to ±0.05em.

### 7.3 Component Accessibility

**Missing:**
- No ARIA labels defined for components
- No keyboard navigation patterns specified
- No screen reader text alternatives
- No reduced-motion support defined

**Recommendation:** Add ARIA label properties to all interactive components. Define keyboard navigation patterns. Add reduced-motion animation variants.

---

## 8. Dark Mode Implementation Gaps

### 8.1 Token Coverage

**Current Coverage (§2.3):**
- All semantic tokens have dark mode equivalents

**Missing:**
- No dark mode variants for motif components (`Star/*`, `Frame/Corner`)
- No dark mode variants for hero treatments (Constellation, Nebula, etc.)
- No dark mode documentation images specified

**Recommendation:** Define dark mode variants for all visual components. Provide example images for dark mode hero treatments.

### 8.2 Component Dark Mode

**Issues:**
- `Image/Plate` frame color not specified for dark mode
- `Divider/Section` star visibility not defined for dark mode
- Glow effects (`glow/gold`, `glow/astral`) may need adjustment for dark backgrounds

**Recommendation:** Explicitly define dark mode styles for all decorative components.

---

## 9. Automation Implementation Gaps

### 9.1 Figma Plugin Integration

**Current Plan (§9.2):**
- Figma Plugin API reads JSON
- Finds instances of components
- Sets component properties by name

**Missing:**
- No error handling for missing components
- No validation of data types (number vs string)
- No rollback mechanism for failed updates
- No batch update optimization

**Recommendation:** Define error handling strategy. Add data type validation. Implement transactional updates with rollback.

### 9.2 MCP Server Integration

**Current Plan (§9.2):**
- MCP server exposes `populate_passport(fileKey, nodeId, data)`

**Missing:**
- No authentication mechanism
- No rate limiting
- No caching strategy
- No webhook notifications for updates

**Recommendation:** Define authentication strategy. Implement rate limiting. Add caching for frequently accessed data.

---

## 10. Priority Recommendations

### 10.1 High Priority (Blocking Automation)

1. **Define Unreal emission points for Shader Breakdown template** — Add Monolith actions for node graph capture, parameter extraction
2. **Add `Layout/SplitView` component** — Required for LOD comparisons, material variants
3. **Add `Chart/Bar` component** — Required for performance data visualization
4. **Add `Text/CodeBlock` component** — Required for shader code display
5. **Define dark mode variants for all decorative components** — Required for complete dark mode support

### 10.2 Medium Priority (User Experience)

1. **Add navigation components** (`Nav/TabBar`, `Nav/Sidebar`, `Nav/Pagination`) — Improve documentation navigation
2. **Add annotation components** (`Annotation/Marker`, `Annotation/Hotspot`) — Enable detailed breakdown calls
3. **Add `Layout/Accordion` component** — Enable collapsible sections in long docs
4. **Add `Modal/Lightbox` component** — Enable full-size image viewing
5. **Expand Asset Passport schema** — Add author, client, license, projectUrl fields

### 10.3 Low Priority (Enhancement)

1. **Add video player component** — Enable animated content presentation
2. **Add search/filter components** — Enable portfolio search
3. **Add missing breakpoints** — Improve responsive coverage
4. **Define accessibility ARIA labels** — Improve screen reader support
5. **Add print/export styles** — Enable PDF generation

---

## 11. Conclusion

The design system has a solid foundation with 8/8 mapped Unreal emission points. The bridge layer validation confirms that all 14 Brand/AssetPassport properties have Unreal sources, though some require separate audit scripts.

**Primary Gaps:**
1. **3 templates lack Unreal data sources** — Shader Breakdown, Commission Sheet, Artbook Spread
2. **Unreal output schema gaps** — scene_metadata.json missing key asset statistics (triangleCount, polyCount, textureCount, drawCalls)
3. **Missing navigation and data visualization components** — Critical for portfolio usability
4. **Missing comparison layout components** — Required for LOD and material variant presentations
5. **Missing bridge layer UI components** — No data source indicators, validation badges, or sync status components
6. **Accessibility gaps** — Contrast ratios, ARIA labels, keyboard navigation not fully defined
7. **Dark mode incomplete** — Decorative components lack dark mode variants

**Bridge Layer Assessment:**
- ✓ All 14 Brand/AssetPassport properties have Unreal sources
- ✓ All 5 portfolio templates have defined mapping rules
- ✓ Data transformation rules documented
- ⚠ Unreal output schema requires augmentation or multi-source merging
- ⚠ Optional Figma schema fields not defined (author, client, license, etc.)

**Next Steps:**
1. **Bridge Layer:** Augment scene_metadata.json or create unified portfolio_manifest.json for complete asset statistics
2. **Bridge Layer:** Add bridge layer UI components (Badge/DataSource, Badge/Validation, Badge/Sync)
3. Decide if Shader Breakdown, Commission Sheet, and Artbook Spread should be automated
4. Prioritize missing components based on portfolio use cases
5. Define Unreal emission points for any newly automated templates
6. Implement missing components in Figma
7. Update DESIGN_SYSTEM.md with new components and schemas
