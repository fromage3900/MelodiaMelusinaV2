# Wix Integration Guide — Technical Breakdown Components

**Created:** 2026-06-25  
**Purpose:** Step-by-step instructions for adding technical components to Wix  
**Components:** 7 HTML embeds for portfolio technical presentations

---

## Prerequisites

1. **Wix Editor Access** — You must be logged into your Wix site editor
2. **Component Files** — All HTML files in `wix/` folder
3. **Fonts Setup** — Fonts should already be configured from WIX-GUIDE.md

---

## General Embed Process (Same for All Components)

### Step 1: Open Wix Editor
1. Go to your Wix site dashboard
2. Click **Edit Site** to open the Wix Editor

### Step 2: Navigate to Target Page
1. In the left sidebar, click **Pages**
2. Select the page where you want to add the component
3. Scroll to the section where you want it

### Step 3: Add HTML Embed
1. Click the **+** button (Add Elements) in the left sidebar
2. Scroll down to **Embeds**
3. Click **Embed Code**
4. Select **Embed HTML**

### Step 4: Paste Component Code
1. Open the component HTML file in a text editor (Notepad, VS Code, etc.)
2. Copy the entire file contents (from `<!DOCTYPE html>` to `</html>`)
3. Paste into the Wix HTML embed box
4. Click **Update**

### Step 5: Size and Position
1. Drag the embed box to your desired location
2. Resize to recommended dimensions (see component-specific sections below)
3. Use the **Align** tools if needed (center, left, right)

### Step 6: Customize Data (Optional)
1. Click the embed box to select it
2. Click **Settings** (gear icon)
3. Click **Edit Code**
4. Find the `var DATA = { ... }` block
5. Modify values as needed
6. Click **Update**

---

## Component-Specific Instructions

### 1. Badge/DataStatus (`badge-data-status.html`)

**Purpose:** Show data availability status

**Recommended Size:** Auto (no resizing needed)

**Where to Use:**
- Section headers (next to titles)
- Above incomplete data cards
- In technical documentation headers

**Customization Example:**
```javascript
var DATA = {
  status: "partial",  // "present", "missing", "partial"
  label: "Asset Data"
};
```

**Status Colors:**
- `present` → Green (data complete)
- `missing` → Red (data absent)
- `partial` → Amber (data incomplete)

**Placement Tips:**
- Place immediately after section titles
- Use consistent positioning (always right-aligned or left-aligned)
- Don't overuse — only for sections with variable data completeness

---

### 2. Placeholder/DataMissing (`placeholder-data-missing.html`)

**Purpose:** Placeholder for missing renders/images

**Recommended Size:** 
- Small: 200 × 150px
- Medium: 400 × 300px
- Large: 600 × 400px

**Where to Use:**
- Where hero renders should be
- In breakdown image grids
- Material channel slots
- PCG graph visualization areas

**Customization Example:**
```javascript
var DATA = {
  dataType: "Hero Render",
  message: "No render data available yet"
};
```

**Placement Tips:**
- Size to match expected image dimensions
- Use consistent sizing within grids
- Replace with actual images when available

---

### 3. Info/GraphMetadata (`info-graph-metadata.html`)

**Purpose:** Display PCG graph technical details

**Recommended Size:** ~360px width, auto height

**Where to Use:**
- Below PCG graph visualizations
- In Process Breakdown sections
- Technical documentation pages

**Customization Example:**
```javascript
var DATA = {
  title: "PCG_FoliageDensity",
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

**Placement Tips:**
- Place below corresponding graph visualization
- Use in vertical stacks for multiple graphs
- Keep consistent spacing between graph and metadata

---

### 4. Tag/PCGFeature (`tag-pcg-feature.html`)

**Purpose:** Tag for PCG-specific features

**Recommended Size:** Auto (no resizing needed)

**Where to Use:**
- Inside Info/GraphMetadata cards
- Clustered in process breakdowns
- Feature lists in technical docs

**Customization Example:**
```javascript
var DATA = {
  feature: "Density Filter",
  active: true
};
```

**Placement Tips:**
- Use multiple copies for multiple features
- Cluster horizontally when possible
- Use `active: true` for primary features, `false` for secondary

**Creating Feature Clusters:**
1. Add first Tag/PCGFeature embed
2. Copy and paste for additional features
3. Arrange horizontally with small gaps
4. Use Wix's **Distribute** tool for even spacing

---

### 5. Layout/ProcessFlow (`layout-process-flow.html`)

**Purpose:** Horizontal process flow visualization

**Recommended Size:** ~800px width, 120px height

**Where to Use:**
- Top of Process Breakdown pages
- Technical documentation headers
- Pipeline overview sections

**Customization Example:**
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

**Placement Tips:**
- Center-align at top of section
- Use as section divider
- Ensure enough width for all steps (consider mobile)

**Mobile Consideration:**
- On mobile (390px), consider using vertical layout
- Or reduce step titles to shorter text

---

### 6. Chart/Bar (`chart-bar.html`)

**Purpose:** Simple bar chart for performance metrics

**Recommended Size:** ~400px width, 120px height

**Where to Use:**
- Performance sections
- Asset breakdowns
- Technical documentation

**Customization Example:**
```javascript
var DATA = {
  label: "Triangle Count",
  value: 482318,
  max: 1000000,
  unit: "triangles"
};
```

**Placement Tips:**
- Use for key metrics only (triangles, draw calls)
- Place near related data (e.g., next to Asset Passport)
- Keep consistent `max` values for comparison

**Common Metrics:**
- Triangle Count (max: 1,000,000)
- Draw Calls (max: 500)
- Material Count (max: 50)
- Texture Count (max: 100)

---

### 7. Card/Performance (`card-performance.html`)

**Purpose:** Performance stats card with multiple metrics

**Recommended Size:** ~360px width, auto height

**Where to Use:**
- Hero page alongside Asset Passport
- Environment breakdown sections
- Technical documentation

**Customization Example:**
```javascript
var DATA = {
  triangleCount: 482318,
  drawCalls: 184,
  materialCount: 12,
  textureCount: 36,
  textureResolution: "4K"
};
```

**Placement Tips:**
- Place next to Asset Passport for complete overview
- Use in performance-focused sections
- Keep null values as null (will display "TBD")

**Null Handling:**
- If data not available, set to `null`
- Will display as red italic "TBD"
- Indicates data needs to be collected

---

## Page Layout Examples

### Hero Page Layout

```
┌─────────────────────────────────────────────────┐
│ Hero Image (or Placeholder/DataMissing)         │
│                                                 │
│ ┌───────────────────────────────────────────┐  │
│ │ Asset Passport                          │  │
│ │ Card/Performance                        │  │
│ │ Badge/DataStatus (partial)               │  │
│ └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Steps:**
1. Add hero image (or Placeholder/DataMissing)
2. Add Asset Passport (from brennan-passport-embed.html)
3. Add Card/Performance below passport
4. Add Badge/DataStatus to show data completeness

---

### Process Breakdown Page Layout

```
┌─────────────────────────────────────────────────┐
│ Layout/ProcessFlow (horizontal steps)           │
├─────────────────────────────────────────────────┤
│ Badge/DataStatus (present)                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌───────────────────────────────────────────┐  │
│ │ Graph Visualization (or Placeholder)      │  │
│ │ Info/GraphMetadata                        │  │
│ │ Tag/PCGFeature cluster                    │  │
│ └───────────────────────────────────────────┘  │
│                                                 │
│ ┌───────────────────────────────────────────┐  │
│ │ Graph Visualization (or Placeholder)      │  │
│ │ Info/GraphMetadata                        │  │
│ │ Tag/PCGFeature cluster                    │  │
│ └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Steps:**
1. Add Layout/ProcessFlow at top
2. Add Badge/DataStatus below
3. For each PCG graph:
   - Add graph image (or Placeholder/DataMissing)
   - Add Info/GraphMetadata below
   - Add Tag/PCGFeature cluster for features

---

### Asset Breakdown Page Layout

```
┌─────────────────────────────────────────────────┐
│ Badge/DataStatus (missing)                      │
├─────────────────────────────────────────────────┤
│ Card/Performance                                │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌──────────────────┐  ┌──────────────────┐     │
│ │ Asset Image      │  │ Asset Image      │     │
│ │ (or Placeholder) │  │ (or Placeholder) │     │
│ └──────────────────┘  └──────────────────┘     │
│                                                 │
│ ┌──────────────────┐  ┌──────────────────┐     │
│ │ Asset Image      │  │ Asset Image      │     │
│ │ (or Placeholder) │  │ (or Placeholder) │     │
│ └──────────────────┘  └──────────────────┘     │
└─────────────────────────────────────────────────┘
```

**Steps:**
1. Add Badge/DataStatus at top
2. Add Card/Performance below
3. Add grid of asset images (or Placeholder/DataMissing)

---

## Responsive Testing

### Desktop (1440px)
- Test all components at full width
- Ensure ProcessFlow fits horizontally
- Check Chart/Bar proportions

### Tablet (834px)
- Test components at reduced width
- ProcessFlow may need to wrap
- Card grids: 2-up instead of 3-up

### Mobile (390px)
- Test components stacked vertically
- ProcessFlow: consider vertical variant
- Card grids: 1-up stack
- Chart/Bar: full width

**How to Test:**
1. In Wix Editor, click **Mobile View** icon (bottom)
2. Adjust component sizes if needed
3. Click **Desktop View** to return
4. Repeat for **Tablet View**

---

## Common Issues and Solutions

### Issue: Component not displaying
**Solution:**
- Ensure you copied the entire HTML file (from `<!DOCTYPE` to `</html>`)
- Check that you clicked **Update** after pasting
- Try refreshing the editor page

### Issue: Component looks wrong size
**Solution:**
- Drag the embed box to resize
- Check recommended dimensions in this guide
- Use **Lock Aspect Ratio** if needed

### Issue: Data not updating after editing
**Solution:**
- Click **Settings** → **Edit Code**
- Make changes to `var DATA` block
- Click **Update**
- Refresh the page if needed

### Issue: Fonts not loading
**Solution:**
- Ensure fonts are set up per WIX-GUIDE.md
- Check that Google Fonts link is in the HTML
- Try clearing browser cache

### Issue: Components overlapping on mobile
**Solution:**
- Switch to mobile view in Wix Editor
- Adjust spacing between components
- Consider stacking vertically instead of horizontally

---

## Best Practices

1. **Test on all devices** — Desktop, tablet, mobile
2. **Keep data consistent** — Use same formatting across components
3. **Use placeholders** — Don't leave blank spaces when data is missing
4. **Show status badges** — Always indicate data completeness
5. **Keep spacing consistent** — Use Wix's spacing tools
6. **Preview before publishing** — Check all pages in preview mode
7. **Backup your work** — Save frequently

---

## File Reference

All component files in: `c:\Users\froma\Downloads\melodia-design-system\wix\`

- `badge-data-status.html`
- `placeholder-data-missing.html`
- `info-graph-metadata.html`
- `tag-pcg-feature.html`
- `layout-process-flow.html`
- `chart-bar.html`
- `card-performance.html`

---

## Next Steps

1. **Set up fonts** per WIX-GUIDE.md (if not already done)
2. **Add Hero Page components** (Asset Passport, Card/Performance, Badge)
3. **Add Process Breakdown components** (ProcessFlow, Info/GraphMetadata, Tags)
4. **Add Asset Breakdown components** (Badge, Card/Performance, Placeholders)
5. **Test on all devices** (Desktop, Tablet, Mobile)
6. **Preview and publish** when satisfied

---

## Support

For questions:
- Refer to `TECHNICAL_COMPONENTS_GUIDE.md` for component details
- Refer to `PORTFOLIO_MAPPING_RULES.md` for data mapping
- Refer to `DESIGN_SYSTEM.md` for design system details
