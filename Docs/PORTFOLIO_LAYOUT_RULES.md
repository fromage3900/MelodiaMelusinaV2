# Portfolio Layout Rules

**Purpose:** Define rules for automatic layout population in Figma based on Unreal Engine outputs  
**Role:** Design System Bridge Layer — layout population logic only, no engine or design system modifications

---

## 1. Layout Population Overview

### 1.1 Core Principle

**Rule:** Unreal Engine outputs (renders + JSON metadata) automatically populate Figma layouts via a bridge layer that:
1. Collects structured data from Unreal (JSON + images)
2. Transforms data to match Figma component property schemas
3. Maps transformed data to specific Figma components and templates
4. Executes Figma API calls to populate components

### 1.2 Population Hierarchy

```
Unreal Output
    ↓
Data Collection (JSON + Images)
    ↓
Data Transformation (formatting, type conversion)
    ↓
Component Mapping (property assignment)
    ↓
Layout Population (Figma API)
    ↓
Figma Layout (populated template)
```

### 1.3 Population Modes

**Mode 1: Full Auto-Population**
- Trigger: New scene export from Unreal
- Action: Create new page from template, populate all components
- Use case: Initial portfolio page creation

**Mode 2: Update-Only**
- Trigger: Updated metadata from Unreal
- Action: Update existing page components, preserve layout
- Use case: Iterative refinement, data corrections

**Mode 3: Append-Only**
- Trigger: New asset/material added to scene
- Action: Append new component instances to existing layout
- Use case: Expanding existing breakdown pages

---

## 2. Template Selection Rules

### 2.1 Template Selection Logic

**Rule:** Template selected based on Unreal output type and content

| Unreal Output Type | Template Selection Criteria | Figma Template |
|-------------------|----------------------------|----------------|
| Hero render + scene metadata | Single beauty shot + full scene data | Hero Page (Template #1) |
| Multiple breakdown renders | 3+ breakdown images + composition data | Environment Breakdown (Template #3) |
| Material grid + channel renders | 4+ channel images + material data | Material Presentation (Template #4) |
| PCG graph + node data | Graph visualization + node metadata | Process Breakdown (Template #8) |
| Asset metadata only | No renders, metadata only | Asset Passport (component only) |

### 2.2 Template Fallback Rules

**Rule:** If primary template criteria not met, fallback to simpler template

**Fallback Chain:**
1. Hero Page → Environment Breakdown (if multiple renders available)
2. Environment Breakdown → Asset Passport (if no renders available)
3. Material Presentation → Asset Passport (if no channel renders available)
4. Process Breakdown → Asset Passport (if no graph visualization available)

### 2.3 Template Instance Creation

**Rule:** Templates are instantiated from Figma component library, not duplicated from existing pages

**Process:**
1. Locate template component in Figma library
2. Create new instance on target page
3. Detach instance if customization required
4. Populate component properties via API

---

## 3. Component Population Rules

### 3.1 Brand/AssetPassport Population

**Rule:** Asset Passport populated with all 14 properties from merged Unreal data

**Population Order:**
1. Text properties (projectName, category, engine, date, version)
2. Numeric properties (triangleCount, polyCount, materialCount, textureCount, drawCalls)
3. Boolean properties (nanite)
4. String properties (textureResolution, lod, platform)
5. Array properties (software → Tag/Software instances)

**Software Array Population:**
```
For each software in software array:
    1. Create Tag/Software component instance
    2. Set softwareName property to software string
    3. Instance-swap icon based on software name:
       - "Blender" → Blender icon
       - "ZBrush" → ZBrush icon
       - "Substance Painter" → Substance icon
       - "Houdini" → Houdini icon
       - "Unreal Engine" → Unreal icon
       - Default → Generic software icon
    4. Position instance in Auto Layout container
```

**Format Variant Selection:**
- Hero Page: Banner format (bottom-left overlay)
- Environment Breakdown: Card format (sidebar)
- Material Presentation: Card format (sidebar)
- Process Breakdown: Card format (sidebar)

### 3.2 Tag/Technical Population

**Rule:** Tag/Technical instances created for each key metric from scene metadata

**Population Order:**
1. Static mesh actor count
2. Material count
3. Triangle count
4. Draw calls
5. Nanite status
6. PCG volume count

**Emphasis Rules:**
- Key metrics (triangle count, draw calls): Emphasis = "Strong"
- Secondary metrics (material count, actor count): Emphasis = "Default"
- Tertiary metrics (PCG volume count): Emphasis = "Subtle"

**Cluster Layout:**
```
Tag/Technical Cluster (Auto Layout Horizontal, gap: 8px)
├─ Tag/Technical (Static Mesh Actors)
├─ Tag/Technical (Materials)
├─ Tag/Technical (Triangle Count) [Strong]
├─ Tag/Technical (Draw Calls) [Strong]
└─ Tag/Technical (Nanite)
```

### 3.3 Card/Info Population

**Rule:** Card/Info populated with Row/Spec arrays derived from dictionary data

**Row/Spec Generation:**
```
For each key-value pair in dictionary:
    1. Create Row/Spec instance
    2. Set label to key (Title Case)
    3. Set value to value (formatted as string)
    4. Add to Card/Info rows array
```

**Card Title Assignment:**
- Material distribution → "Material Distribution"
- PCG node types → "PCG Node Distribution"
- Environment statistics → "Environment Statistics"
- Asset statistics → "Asset Statistics"

**Row Sorting:**
- Numeric values: Sort descending (highest first)
- String values: Sort alphabetically
- Mixed types: Numeric first, then alphabetical

### 3.4 Image/Plate Population

**Rule:** Image/Plate populated with render images from Unreal output directory

**Image Source Resolution:**
1. Check if image already uploaded to Figma (by file hash)
2. If uploaded, reuse existing Figma image node
3. If not uploaded, upload image to Figma
4. Set Image/Plate imageSource to uploaded image node

**Frame Assignment:**
- Hero render: `showFrame = false` (full-bleed)
- Breakdown renders: `showFrame = true` (framed)
- Channel renders: `showFrame = true` (framed, square aspect)
- Graph visualization: `showFrame = true` (framed)

**Aspect Ratio Rules:**
- Hero render: 16:9 (1920x1080)
- Breakdown renders: 16:9 or 4:3 (match source)
- Channel renders: 1:1 (square, 512x512 or 1024x1024)
- Graph visualization: 16:9 or 4:3 (match source)

**Caption Assignment:**
- If caption metadata available, set caption property
- If no caption, use filename (without extension) as caption
- If caption empty, hide caption layer

---

## 4. Layout Structure Rules

### 4.1 Hero Page Layout

**Layout Structure:**
```
Hero Page (Frame: 1920x1080)
├─ Image/Plate[Beauty] (full-bleed, z-index: 0)
│  └─ imageSource: Hero render PNG
├─ Title Block (z-index: 10)
│  ├─ Display/XL (title text)
│  │  └─ text: level_name or projectName
│  └─ Tag/Technical cluster (optional)
├─ Brand/AssetPassport[Banner] (z-index: 20)
│  └─ position: bottom-left (x: 64, y: 920)
└─ Scroll Cue (z-index: 30)
   ├─ Star/4pt
   └─ text: "Scroll to explore"
```

**Positioning Rules:**
- Hero render: Full-bleed (x: 0, y: 0, width: 1920, height: 1080)
- Title block: Top-left (x: 64, y: 64)
- Asset Passport: Bottom-left (x: 64, y: 920)
- Scroll cue: Bottom-right (x: 1856, y: 920)

**Spacing Rules:**
- Title to passport: Auto-fill (passport fixed at bottom)
- Passport to edge: 64px margin
- Scroll cue to edge: 64px margin

### 4.2 Environment Breakdown Layout

**Layout Structure:**
```
Environment Breakdown (Frame: 1920x1080+)
├─ Title Block (height: 128)
│  ├─ Title/Project (x: 64, y: 48)
│  └─ Tag/Technical cluster (x: 64, y: 88)
├─ Image/Plate[Beauty] (height: 600)
│  └─ imageSource: Beauty render
├─ "Composition" Annotated Plate (height: 400, optional)
│  └─ imageSource: Composition render
├─ Modular-Kit Grid (Auto Layout Wrap, gap: 32)
│  ├─ Image/Plate (Breakdown #1)
│  ├─ Image/Plate (Breakdown #2)
│  ├─ Image/Plate (Breakdown #3)
│  └─ Image/Plate (Breakdown #N)
├─ Lighting Passes Row (Auto Layout Horizontal, gap: 32, optional)
│  ├─ Image/Plate (Lighting #1)
│  ├─ Image/Plate (Lighting #2)
│  └─ Image/Plate (Lighting #N)
└─ Card/Info (Environment Statistics)
   └─ rows: Actor count, PCG volumes, material distribution
```

**Grid Population Rules:**
- Grid uses Auto Layout with Wrap
- Grid gap: 32px
- Grid padding: 64px
- Item width: Auto (min-width: 400px)
- Item height: Auto (aspect-ratio: 16:9)

**Row Population Rules:**
- Row uses Auto Layout Horizontal
- Row gap: 32px
- Row padding: 64px
- Item width: Auto (aspect-ratio: 16:9)
- Item height: 300px

**Card Positioning:**
- Card placed after all image grids
- Card width: 400px
- Card position: Left-aligned with 64px margin

### 4.3 Material Presentation Layout

**Layout Structure:**
```
Material Presentation (Frame: 1920x1080+)
├─ Title Block (height: 128)
│  ├─ Title/Project (x: 64, y: 48)
│  └─ Tag/Technical cluster (x: 64, y: 88)
├─ Image/Plate (Material Hero, height: 600)
│  └─ imageSource: Material sphere/plane render
├─ Channel Grid (Auto Layout Grid, 4 columns, gap: 32)
│  ├─ Image/Plate (Albedo) + Legend/Swatch
│  ├─ Image/Plate (Normal) + Legend/Swatch
│  ├─ Image/Plate (Roughness) + Legend/Swatch
│  ├─ Image/Plate (Metallic) + Legend/Swatch
│  ├─ Image/Plate (AO) + Legend/Swatch
│  ├─ Image/Plate (Height) + Legend/Swatch
│  ├─ Image/Plate (Thickness) + Legend/Swatch
│  └─ Image/Plate (Subsurface) + Legend/Swatch
└─ Card/Info (Material Statistics)
   └─ rows: Material parameters, texture slots
```

**Channel Grid Rules:**
- Grid: 4 columns, 2 rows (8 channels max)
- Grid gap: 32px
- Grid padding: 64px
- Item aspect-ratio: 1:1 (square)
- Legend/Swatch positioned below each Image/Plate

**Legend/Swatch Population:**
- Label: Channel name (e.g., "Albedo", "Normal")
- Swatch color: Extracted from channel render (average color)
- Swatch size: 16x16px

### 4.4 Process Breakdown Layout

**Layout Structure:**
```
Process Breakdown (Frame: 1920x1080+)
├─ Title Block (height: 128)
│  ├─ Title/Project (x: 64, y: 48)
│  └─ Tag/Technical cluster (x: 64, y: 88)
├─ Process/Step Timeline (Auto Layout Vertical, gap: 48)
│  ├─ Process/Step #1
│  │  ├─ stepNumber: 1
│  │  ├─ title: "PCG Graph Setup"
│  │  └─ description: Node type distribution
│  ├─ Process/Step #2
│  │  ├─ stepNumber: 2
│  │  ├─ title: "Node Configuration"
│  │  └─ description: Parameter tuning
│  ├─ Process/Step #3
│  │  ├─ stepNumber: 3
│  │  ├─ title: "Output Generation"
│  │  └─ description: Asset instantiation
│  └─ Process/Step #N
├─ Image/Plate (PCG Graph Visualization, height: 600)
│  └─ imageSource: Graph render
└─ Brand/AssetPassport (Card format)
   └─ position: Right sidebar
```

**Timeline Population Rules:**
- Timeline uses Auto Layout Vertical
- Timeline gap: 48px
- Timeline padding: 64px
- Step numbering: Auto-increment from 1
- Step content: Derived from PCG metadata stages

**Step Content Mapping:**
- Stage 1: Graph setup (node count, graph path)
- Stage 2: Node configuration (node types)
- Stage 3: Parameter tuning (parameters)
- Stage 4: Output generation (output stats)

---

## 5. Auto Layout Rules

### 5.1 Auto Layout Container Rules

**Rule:** All dynamic content containers use Auto Layout for responsive behavior

**Container Types:**
- Horizontal: Tag clusters, lighting pass rows
- Vertical: Timelines, card stacks
- Wrap: Modular-kit grids, channel grids

**Auto Layout Properties:**
- Gap: 32px (standard), 48px (timeline), 64px (sections)
- Padding: 64px (page margins), 32px (component margins)
- Alignment: Top-left (default), Center (hero title)
- Distribution: Space-between (headers), Packed (grids)

### 5.2 Responsive Breakpoint Rules

**Rule:** Layout adapts to viewport width using breakpoints

**Breakpoints:**
- Desktop: ≥ 1440px (full layout)
- Tablet: 768px - 1439px (2-column grid)
- Mobile: < 768px (1-column stack)

**Breakpoint Adaptations:**
- Desktop: 4-column channel grid, 3-column modular grid
- Tablet: 2-column channel grid, 2-column modular grid
- Mobile: 1-column channel grid, 1-column modular grid

**Asset Passport Format by Breakpoint:**
- Desktop: Banner format (full width)
- Tablet: Card format (sidebar)
- Mobile: Compact format (stacked)

### 5.3 Overflow Rules

**Rule:** Content that exceeds viewport height triggers scroll behavior

**Overflow Triggers:**
- Hero Page: Never overflows (fixed 1920x1080)
- Environment Breakdown: Scroll if > 3 breakdown renders
- Material Presentation: Scroll if > 8 channels
- Process Breakdown: Scroll if > 5 steps

**Scroll Behavior:**
- Scroll container: Page frame
- Scroll indicator: Scroll cue (Star/4pt + text)
- Scroll position: Top (initial), Bottom (after population)

---

## 6. Data Validation Rules

### 6.1 Required Field Validation

**Rule:** Transaction fails if required fields missing

**Critical Fields:**
- Hero Page: Hero render image, projectName
- Environment Breakdown: Beauty render, scene metadata
- Material Presentation: Material hero render, material metadata
- Process Breakdown: PCG graph render, PCG metadata

**Validation Order:**
1. Check JSON file exists and is valid
2. Check required fields present in JSON
3. Check render images exist and are readable
4. Check Figma file is accessible
5. Check template component exists in library

**Failure Handling:**
- Log specific missing field
- Abort transaction
- Return error code with details

### 6.2 Type Validation

**Rule:** Field types validated before transformation

**Type Checks:**
- projectName: string
- triangleCount: number (convert to string)
- nanite: boolean
- software: array
- timestamp: string (ISO 8601)

**Conversion Rules:**
- number → string: `str(value)`
- boolean → string: `"True"` if true else `"False"`
- array → instance-swap: Iterate and create instances
- ISO timestamp → YYYY-MM: Extract year and month

### 6.3 Range Validation

**Rule:** Numeric values validated against expected ranges

**Range Checks:**
- triangleCount: 0 - 10,000,000
- polyCount: 0 - 10,000,000
- materialCount: 0 - 1000
- textureCount: 0 - 1000
- drawCalls: 0 - 10,000

**Out-of-Range Handling:**
- Log warning with value and expected range
- Clamp to range if reasonable
- Fail transaction if extreme outlier (e.g., negative values)

---

## 7. Image Handling Rules

### 7.1 Image Upload Rules

**Rule:** Images uploaded to Figma only if not already present

**Upload Process:**
1. Calculate file hash (SHA-256)
2. Check if hash exists in Figma file
3. If exists, reuse existing image node
4. If not exists, upload image to Figma
5. Store hash-to-node mapping for future reuse

**Image Compression:**
- Hero renders: Max 5MB (PNG or JPG)
- Breakdown renders: Max 2MB (PNG or JPG)
- Channel renders: Max 1MB (PNG)
- Graph visualizations: Max 2MB (PNG or JPG)

**Image Format Preference:**
- Photos with gradients: PNG (lossless)
- Photos with solid colors: JPG (lossy, smaller)
- Technical diagrams: PNG (lossless, sharp edges)

### 7.2 Image Placement Rules

**Rule:** Images placed according to layout structure and aspect ratio

**Placement Order:**
1. Hero render (if Hero Page)
2. Beauty render (if Environment Breakdown)
3. Material hero render (if Material Presentation)
4. Channel renders (if Material Presentation)
5. Breakdown renders (if Environment Breakdown)
6. PCG graph render (if Process Breakdown)

**Aspect Ratio Enforcement:**
- If image aspect ratio doesn't match target:
  - Crop to target aspect ratio (center crop)
  - Add letterboxing (if preserving full image)
  - Stretch (not recommended, only if explicitly requested)

**Image Quality Rules:**
- Hero renders: 1920x1080 minimum
- Breakdown renders: 1280x720 minimum
- Channel renders: 512x512 minimum
- Graph visualizations: 1280x720 minimum

---

## 8. Text Handling Rules

### 8.1 Text Truncation Rules

**Rule:** Long text truncated with ellipsis if exceeds component bounds

**Truncation Thresholds:**
- projectName: 50 characters
- category: 30 characters
- Tag/Technical label: 20 characters
- Tag/Technical value: 15 characters
- Card/Info label: 25 characters
- Card/Info value: 30 characters

**Truncation Behavior:**
- Truncate at threshold
- Add ellipsis ("...")
- Show full text on hover (tooltip)

### 8.2 Text Formatting Rules

**Rule:** Text formatted according to design system typography

**Typography Mapping:**
- projectName: `title-project` (40px, Fraunces Regular)
- category: `header-sub` (20px, Inter SemiBold)
- Tag/Technical: `label-technical` (12px, IBM Plex Mono Medium)
- Card/Info: `body-default` (16px, Inter Regular)
- Metadata: `metadata` (11px, IBM Plex Mono Regular)

**Text Case Rules:**
- projectName: Title Case
- category: Title Case
- Tag/Technical label: Title Case
- Tag/Technical value: Uppercase (if technical)
- Card/Info label: Title Case
- Card/Info value: As-is (preserve original case)

---

## 9. Conditional Population Rules

### 9.1 Optional Component Rules

**Rule:** Optional components only populated if data available

**Optional Components:**
- "Composition" annotated plate (Environment Breakdown)
- Lighting passes row (Environment Breakdown)
- PCG graph visualization (Process Breakdown)
- Channel grid beyond 4 channels (Material Presentation)

**Population Logic:**
```
If data available:
    Create component instance
    Populate with data
    Position in layout
Else:
    Skip component
    Adjust layout (remove gap, reflow)
```

### 9.2 Conditional Variant Rules

**Rule:** Component variant selected based on data characteristics

**Variant Selection:**
- Asset Passport: Banner (Hero Page), Card (Breakdown), Compact (Mobile)
- Tag/Technical: Strong (key metrics), Default (secondary), Subtle (tertiary)
- Image/Plate: Framed (breakdowns), Full-bleed (hero), Square (channels)

**Variant Logic:**
```
If metric is key (triangle count, draw calls):
    Use Strong variant
Else if metric is secondary (material count, actor count):
    Use Default variant
Else:
    Use Subtle variant
```

### 9.3 Conditional Layout Rules

**Rule:** Layout structure adapts based on content volume

**Content Volume Thresholds:**
- Breakdown renders: 1-3 (single row), 4-6 (2 rows), 7+ (grid)
- Channel renders: 1-4 (single row), 5-8 (2 rows), 9+ (scroll)
- Process steps: 1-3 (vertical stack), 4+ (scroll)

**Layout Adaptation:**
```
If content count ≤ threshold:
    Use compact layout (single row/stack)
Else if content count > threshold:
    Use expanded layout (grid/scroll)
```

---

## 10. Error Recovery Rules

### 10.1 Partial Population Recovery

**Rule:** If component population fails, continue with remaining components

**Failure Isolation:**
- Log specific component failure
- Skip failed component
- Continue with next component
- Mark transaction as partial success

**Partial Success Handling:**
- Return list of successfully populated components
- Return list of failed components with error details
- Allow retry of failed components individually

### 10.2 Rollback Rules

**Rule:** If critical component fails, rollback entire transaction

**Critical Components:**
- Hero render (Hero Page)
- Beauty render (Environment Breakdown)
- Material hero render (Material Presentation)
- Brand/AssetPassport (all templates)

**Rollback Process:**
1. Revert all component property changes
2. Delete newly created component instances
3. Delete newly uploaded images
4. Restore original layout state
5. Log rollback with reason

### 10.3 Retry Rules

**Rule:** Failed transactions can be retried with exponential backoff

**Retry Strategy:**
- Retry 1: Immediate (network glitch)
- Retry 2: 1 second delay (temporary API issue)
- Retry 3: 5 second delay (rate limit)
- Retry 4: 30 second delay (service unavailable)
- Retry 5+: Abort (persistent error)

**Retry Conditions:**
- Network timeout
- API rate limit (429)
- Service unavailable (503)
- Temporary authentication failure (401)

**No-Retry Conditions:**
- Invalid data (400)
- Component not found (404)
- Permission denied (403)
- Persistent authentication failure (401 after retry)

---

## 11. Performance Rules

### 11.1 Batch Operation Rules

**Rule:** Multiple component updates batched into single API call

**Batch Size:**
- Component property updates: 100 per batch
- Image uploads: 10 per batch
- Instance creations: 50 per batch

**Batch Processing:**
```
For each batch of components:
    1. Collect component updates
    2. Send single API call with batch
    3. Wait for response
    4. Process next batch
```

### 11.2 Caching Rules

**Rule:** Figma API responses cached to reduce redundant calls

**Cache Duration:**
- Component library metadata: 1 hour
- File metadata: 5 minutes
- Image node mapping: 1 hour
- Component property schema: 1 hour

**Cache Invalidation:**
- File modified: Invalidate file metadata cache
- Component library updated: Invalidate component metadata cache
- Manual cache clear: Invalidate all caches

### 11.3 Parallel Processing Rules

**Rule:** Independent operations processed in parallel

**Parallelizable Operations:**
- Image uploads (different images)
- Component property updates (different components)
- Instance creations (different components)

**Parallel Limits:**
- Max concurrent API.calls: 5
- Max concurrent image uploads: 3
- Max concurrent component updates: 10

---

## 12. Logging and Monitoring Rules

### 12.1 Event Logging Rules

**Rule:** All population events logged for debugging and monitoring

**Log Levels:**
- Info: Normal operations (component created, property set)
- Warning: Non-critical issues (missing optional field, type conversion)
- Error: Critical failures (missing required field, API failure)

**Log Content:**
- Timestamp
- Operation type
- Component/template name
- Property name (if applicable)
- Value (if applicable)
- Error message (if error)

### 12.2 Success Metrics

**Rule:** Transaction success tracked with metrics

**Metrics Tracked:**
- Transaction success rate (percentage)
- Average transaction duration
- Components populated per transaction
- Images uploaded per transaction
- API calls per transaction

**Metric Thresholds:**
- Success rate: ≥ 95%
- Average duration: ≤ 30 seconds
- API calls: ≤ 50 per transaction

### 12.3 Failure Analysis

**Rule:** Failures analyzed to identify patterns

**Failure Categories:**
- Missing data (field not in Unreal output)
- Type mismatch (field type doesn't match Figma property)
- API failure (Figma API error)
- Network failure (connection timeout)
- Validation failure (data out of range)

**Failure Reporting:**
- Aggregate failure counts by category
- Identify top failure reasons
- Recommend fixes for common failures

---

## 13. Summary

**Population Rules Status:**
- ✓ Template selection rules defined
- ✓ Component population rules defined
- ✓ Layout structure rules defined
- ✓ Auto layout rules defined
- ✓ Data validation rules defined
- ✓ Image handling rules defined
- ✓ Text handling rules defined
- ✓ Conditional population rules defined
- ✓ Error recovery rules defined
- ✓ Performance rules defined
- ✓ Logging and monitoring rules defined

**Implementation Priority:**
1. High: Template selection, component population, data validation
2. Medium: Layout structure, auto layout, image handling
3. Low: Performance optimization, logging, monitoring

**Next Steps:**
1. Implement bridge layer with population rules
2. Test with sample Unreal outputs
3. Validate Figma API integration
4. Monitor success metrics
5. Refine rules based on testing results
