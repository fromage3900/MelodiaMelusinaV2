# Portfolio Presentation System — Mapping Rules

**Generated:** 2026-06-25  
**Schema Version:** 1.0  
**Design System:** Melodia (DESIGN_SYSTEM.md)

---

# 1. Portfolio Package Schema Analysis

## 1.1 Current State (Incomplete)

```json
{
  "assets": [],                    // EMPTY - No asset data
  "materials": [],                 // EMPTY - No material data
  "pcg": {                         // PRESENT - 4 graphs
    "graphs": {
      "exclusion": { ... },
      "foliage": { ... },
      "rock": { ... },
      "wall": { ... }
    }
  },
  "renders": {                     // EMPTY - All arrays empty
    "breakdown": [],
    "hero": [],
    "materials": [],
    "pcg": []
  },
  "scene": {                       // INCOMPLETE - Missing required fields
    "engine": null,
    "level_path": null,
    "scene_name": null,
    "timestamp": "2026-06-25T05:53:43.475148+00:00"
  },
  "stats": {                       // NULL - No performance data
    "draw_calls": null,
    "triangle_count": null
  }
}
```

## 1.2 Intended Complete Schema

```json
{
  "assets": [
    {
      "name": "string",
      "type": "static_mesh|skeletal_mesh",
      "path": "/Game/...",
      "triangle_count": number,
      "material_count": number,
      "lod_levels": number,
      "nanite": boolean
    }
  ],
  "materials": [
    {
      "name": "string",
      "path": "/Game/...",
      "type": "material_instance|master_material",
      "domain": "opaque|masked|translucent",
      "texture_count": number,
      "parameter_count": number,
      "preview_image": "path/to/image.png"
    }
  ],
  "pcg": {
    "graphs": {
      "graph_name": {
        "path": "/Game/...",
        "role": "foliage|rock|wall|...",
        "voxel_cm": number,
        "phase": number,
        "features": {
          "density_filter": boolean,
          "surface_sampler": boolean,
          "passthrough": boolean,
          "pcgex_exclusion": boolean,
          "pcgex_candidate": "string"
        }
      }
    }
  },
  "renders": {
    "hero": [
      {
        "type": "beauty|wireframe|lighting",
        "path": "path/to/image.png",
        "caption": "string"
      }
    ],
    "breakdown": [
      {
        "type": "composition|modular|lighting",
        "path": "path/to/image.png",
        "caption": "string"
      }
    ],
    "materials": [
      {
        "material_name": "string",
        "channels": [
          {"type": "albedo", "path": "..."},
          {"type": "normal", "path": "..."},
          {"type": "roughness", "path": "..."}
        ]
      }
    ],
    "pcg": [
      {
        "graph_name": "string",
        "path": "path/to/image.png",
        "caption": "string"
      }
    ]
  },
  "scene": {
    "scene_name": "string",
    "level_path": "/Game/...",
    "engine": "Unreal Engine 5.x",
    "timestamp": "ISO-8601"
  },
  "stats": {
    "triangle_count": number,
    "draw_calls": number,
    "material_count": number,
    "texture_count": number,
    "texture_resolution": "string"
  }
}
```

---

# 2. Figma Layout Mapping Rules

## 2.1 Scene Data → Asset Passport Component

**Source:** `portfolio_package.json` → `scene` + `stats`

**Target:** `Brand/AssetPassport` component

| Figma Property | Source Field | Transformation | Current Status |
|----------------|--------------|----------------|----------------|
| `projectName` | `scene.scene_name` | Direct mapping | MISSING (null) |
| `category` | Derived from `assets` | "Environment" if assets present | MISSING (no assets) |
| `triangleCount` | `stats.triangle_count` | Number → formatted string | MISSING (null) |
| `polyCount` | `stats.triangle_count` / 2 | Approximation | MISSING (null) |
| `materialCount` | `stats.material_count` | Number → formatted string | MISSING (null) |
| `textureCount` | `stats.texture_count` | Number → formatted string | MISSING (null) |
| `textureResolution` | `stats.texture_resolution` | Direct mapping | MISSING (null) |
| `drawCalls` | `stats.draw_calls` | Number → formatted string | MISSING (null) |
| `lod` | Derived from `assets` | "LOD0–LOD{max}" | MISSING (no assets) |
| `nanite` | Derived from `assets` | Boolean → string | MISSING (no assets) |
| `platform` | Static | "PC / Console" | N/A (static) |
| `software` | Static | ["Blender", "Unreal Engine"] | N/A (static) |
| `engine` | `scene.engine` | Format with prefix | MISSING (null) |
| `date` | `scene.timestamp` | ISO → YYYY-MM | PRESENT |
| `version` | Static | "v1.0" | N/A (static) |

**Layout Rule:**
- If `scene.scene_name` is null → Use placeholder "Project Name"
- If stats are null → Show "TBD" in numeric fields
- If assets are empty → Default category to "Environment"

**Template Selection:**
- Desktop: `Format=Banner`
- Tablet: `Format=Card`
- Mobile: `Format=Compact`

---

## 2.2 PCG Graphs → Process Breakdown Template

**Source:** `portfolio_package.json` → `pcg.graphs`

**Target:** `Process Breakdown` template (06 Templates)

**Mapping Logic:**

For each PCG graph in `pcg.graphs`:

1. **Create Process/Step component**
   - Step number: Sequential (1, 2, 3, 4)
   - Title: Graph key (e.g., "exclusion", "foliage", "rock", "wall")
   - Description: Graph path + role

2. **Populate Step Content:**
   - `Tag/Technical` cluster for graph features:
     - If `density_filter: true` → Tag "Density Filter"
     - If `surface_sampler: true` → Tag "Surface Sampler"
     - If `passthrough: true` → Tag "Passthrough"
     - If `pcgex_exclusion: true` → Tag "PCGEx Exclusion"
     - If `pcgex_candidate` present → Tag "PCGEx: {value}"
   - `Card/Info` for graph metadata:
     - Row: "Path" → graph path
     - Row: "Role" → role (if present)
     - Row: "Voxel" → voxel_cm (if present)
     - Row: "Phase" → phase (if present)

3. **Image Plate:**
   - If `renders.pcg` has matching graph_name → Display image
   - Else → Show placeholder with "PCG Graph Visualization"

**Layout Structure:**
```
┌─────────────────────────────────────────────────┐
│ Process Breakdown Header                        │
├─────────────────────────────────────────────────┤
│ Process/Step[1]                                 │
│   Title: Exclusion                              │
│   Tags: [Passthrough] [PCGEx: DistanceFilter]  │
│   Card/Info: Path, PCGEx Candidate             │
│   Image/Plate: renders.pcg[exclusion]           │
├─────────────────────────────────────────────────┤
│ Process/Step[2]                                 │
│   Title: Foliage                                │
│   Tags: [Density Filter]                        │
│   Card/Info: Path                               │
│   Image/Plate: renders.pcg[foliage]             │
├─────────────────────────────────────────────────┤
│ Process/Step[3]                                 │
│   Title: Rock                                   │
│   Tags: [Role: Rock] [Voxel: 210cm]             │
│   Card/Info: Path, Voxel                        │
│   Image/Plate: renders.pcg[rock]                │
├─────────────────────────────────────────────────┤
│ Process/Step[4]                                 │
│   Title: Wall                                   │
│   Tags: [Phase 3] [Note: Spline Deferred]      │
│   Card/Info: Path, Phase, Note                  │
│   Image/Plate: renders.pcg[wall]                │
└─────────────────────────────────────────────────┘
```

**Current State:**
- 4 PCG graphs present → 4 Process/Step components
- No PCG renders → All Image/Plate placeholders

---

## 2.3 Asset List → Asset Breakdown Template

**Source:** `portfolio_package.json` → `assets`

**Target:** `Asset Breakdown` template

**Mapping Logic:**

For each asset in `assets`:

1. **Create Card/Info[Asset Statistics]**
   - Title: asset name
   - Row/Spec rows:
     - "Type" → asset type
     - "Triangles" → formatted triangle_count
     - "Materials" → material_count
     - "LOD Levels" → lod_levels
     - "Nanite" → boolean → "Yes/No"

2. **Image Plate:**
   - If `renders.breakdown` has matching asset → Display image
   - Else → Show placeholder

3. **Tag/Technical Cluster:**
   - Tag for asset type
   - Tag for Nanite (if true)
   - Tag for LOD count

**Layout Structure:**
```
┌─────────────────────────────────────────────────┐
│ Asset Breakdown Header                          │
├─────────────────────────────────────────────────┤
│ Grid of Card/Info + Image/Plate pairs          │
│                                                 │
│ [Card/Info]    [Image/Plate]                   │
│ Asset Name     Asset Render                    │
│ Type: Mesh     (or placeholder)                 │
│ Triangles: X                                   │
│ Materials: N                                   │
│                                                 │
│ [Card/Info]    [Image/Plate]                   │
│ ...                                            │
└─────────────────────────────────────────────────┘
```

**Current State:**
- `assets` array empty → No cards generated
- Fallback: Show "No asset data available" message

---

## 2.4 Material List → Material Presentation Template

**Source:** `portfolio_package.json` → `materials`

**Target:** `Material Presentation` template

**Mapping Logic:**

For each material in `materials`:

1. **Create Material Hero**
   - `Image/Plate[WithCaption]` with preview_image
   - Caption: material name

2. **Create Channel Grid**
   - For each channel in material:
     - `Image/Plate` with channel image
     - `Legend/Swatch` with channel type (Albedo, Normal, etc.)

3. **Create Card/Info[Material Statistics]**
   - Row/Spec rows:
     - "Type" → material type
     - "Domain" → domain
     - "Textures" → texture_count
     - "Parameters" → parameter_count

**Layout Structure:**
```
┌─────────────────────────────────────────────────┐
│ Material Presentation Header                     │
├─────────────────────────────────────────────────┤
│ Material Hero                                    │
│ [Image/Plate] Material Preview                  │
├─────────────────────────────────────────────────┤
│ Channel Grid                                     │
│ [Image/Plate] [Legend/Swatch: Albedo]          │
│ [Image/Plate] [Legend/Swatch: Normal]          │
│ [Image/Plate] [Legend/Swatch: Roughness]       │
├─────────────────────────────────────────────────┤
│ Card/Info[Material Statistics]                   │
│ Type, Domain, Textures, Parameters             │
└─────────────────────────────────────────────────┘
```

**Current State:**
- `materials` array empty → No material sections generated
- Fallback: Show "No material data available" message

---

## 2.5 Renders → Hero Page Template

**Source:** `portfolio_package.json` → `renders.hero`

**Target:** `Hero Page` template

**Mapping Logic:**

1. **Primary Hero Image:**
   - First item in `renders.hero` array
   - `Image/Plate[Beauty]` full-bleed

2. **Title Overlay:**
   - `Display/XL` with `scene.scene_name`
   - If null → Use "Environment Portfolio"

3. **Asset Passport:**
   - `Brand/AssetPassport[Banner]` overlaid bottom-left

**Layout Structure:**
```
┌─────────────────────────────────────────────────┐
│ [Image/Plate[Beauty]] Full-bleed hero render   │
│                                                 │
│ ┌───────────────────────────────────────────┐  │
│ │ Display/XL: Scene Name                   │  │
│ │ Asset Passport[Banner]                   │  │
│ └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Current State:**
- `renders.hero` empty → Use placeholder gradient background
- `scene.scene_name` null → Use "Environment Portfolio" title

---

# 3. Data Validation Rules

## 3.1 Required Fields for Complete Presentation

| Section | Required Fields | Current Status |
|---------|----------------|----------------|
| Asset Passport | `scene.scene_name`, `scene.engine`, `stats.triangle_count`, `stats.draw_calls` | MISSING |
| Asset Breakdown | `assets` array with name, type, triangle_count | MISSING |
| Material Presentation | `materials` array with name, type, channels | MISSING |
| Process Breakdown | `pcg.graphs` (PRESENT) | COMPLETE |
| Hero Page | `renders.hero` array, `scene.scene_name` | MISSING |

## 3.2 Fallback Rules

**When data is missing:**

1. **Asset Passport:**
   - `projectName` null → "Project Name"
   - Numeric stats null → "TBD"
   - `engine` null → "Unreal Engine 5.x"
   - `date` present → Use timestamp

2. **Asset/Material Sections:**
   - Empty arrays → Show "No data available" message in Card/Info
   - No renders → Use placeholder Image/Plate with gray background

3. **Hero Page:**
   - No hero render → Use editorial gradient background
   - No scene name → Use "Environment Portfolio"

4. **Process Breakdown:**
   - No PCG renders → Use placeholder Image/Plate with graph name
   - Graph metadata present → Always display

---

# 4. Missing UI Components

## 4.1 Components Needed for Technical Breakdowns

**Missing from DESIGN_SYSTEM.md:**

1. **`Badge/DataStatus`** — Indicates data availability
   - Properties: `status` (enum: present, missing, partial)
   - Use: Show which sections have complete vs missing data
   - Impact: Technical director can quickly identify incomplete documentation

2. **`Placeholder/DataMissing`** — Placeholder for missing renders
   - Properties: `dataType` (string), `message` (string)
   - Use: Replace Image/Plate when render data is missing
   - Impact: Clear indication of missing visual documentation

3. **`Info/GraphMetadata`** — Specialized card for PCG graph metadata
   - Properties: `graphPath`, `role`, `voxel`, `phase`, `features`
   - Use: Display PCG graph technical details in structured format
   - Impact: Better than generic Card/Info for graph-specific data

4. **`Tag/PCGFeature`** — Specialized tag for PCG graph features
   - Properties: `feature` (enum: density_filter, surface_sampler, passthrough, pcgex)
   - Use: Consistent styling for PCG-specific feature tags
   - Impact: Visual distinction from generic Tag/Technical

5. **`Layout/ProcessFlow`** — Horizontal process flow layout
   - Properties: `direction` (enum: horizontal, vertical), `stepCount`
   - Use: Display PCG graph sequence as connected steps
   - Impact: Shows workflow relationships between graphs

## 4.2 Components Needed for Performance Visualization

**Missing from DESIGN_SYSTEM.md:**

1. **`Chart/Bar`** — Simple bar chart for performance metrics
   - Properties: `label` (string), `value` (number), `max` (number), `unit` (string)
   - Use: Visualize triangle count, draw calls, material count
   - Impact: Technical director can quickly assess performance profile

2. **`Card/Performance`** — Specialized card for performance stats
   - Properties: `triangleCount`, `drawCalls`, `materialCount`, `textureCount`
   - Use: Display performance metrics with visual indicators
   - Impact: Better than generic Card/Info for performance data

---

# 5. Hierarchy Rules for Presentation

## 5.1 Page-Level Hierarchy

**Priority Order (for technical director reading):**

1. **Hero Page** — Project overview + key stats (Asset Passport)
2. **Process Breakdown** — PCG workflow (procedural generation competence)
3. **Asset Breakdown** — Modular construction (asset library)
4. **Material Presentation** — Material systems (shader competence)
5. **Technical Documentation** — Deep technical details

**Rationale:** Technical directors want to see:
1. What is this? (Hero)
2. How was it built procedurally? (PCG)
3. What assets were used? (Assets)
4. What materials? (Materials)
5. How does it work technically? (Documentation)

## 5.2 Section-Level Hierarchy

**Within each section:**

1. **Header** → Section title + Badge/DataStatus
2. **Summary** → Card/Info with key metrics
3. **Detail Grid** → Repeated components (cards, plates)
4. **Footer** → Asset Passport or Footer/Signature

**Rationale:** Summary first → Details second. Technical directors scan for key metrics before diving into details.

## 5.3 Component-Level Hierarchy

**Within Card/Info:**

1. **Title** → Bold, primary
2. **Key Metrics** → Top rows (triangles, materials)
3. **Secondary Metrics** → Middle rows (LOD, Nanite)
4. **Metadata** → Bottom rows (path, timestamp)

**Rationale:** Most important technical data first.

---

# 6. Layout Structure Logic

## 6.1 Desktop (1440px)

**Hero Page:**
- Full-bleed Image/Plate[Beauty]
- Overlay: Display/XL + Asset Passport[Banner]
- Scroll cue at bottom

**Process Breakdown:**
- Vertical stack of Process/Step components
- Each step: Title + Tag/Technical cluster + Card/Info + Image/Plate
- 24px spacing between steps

**Asset Breakdown:**
- 12-column grid
- Card/Info + Image/Plate pairs in 3-column layout
- 24px grid gaps

**Material Presentation:**
- Material hero (full-width Image/Plate)
- Channel grid (4 columns)
- Card/Info[Material Statistics] below

## 6.2 Tablet (834px)

**Hero Page:**
- Same structure, Asset Passport switches to Card format

**Process Breakdown:**
- Same structure, Image/Plate width constrained

**Asset Breakdown:**
- 2-column grid (Card/Info + Image/Plate pairs)

**Material Presentation:**
- Channel grid: 2 columns

## 6.3 Mobile (390px)

**Hero Page:**
- Asset Passport switches to Compact format

**Process Breakdown:**
- Process/Step components stack vertically
- Image/Plate full-width

**Asset Breakdown:**
- 1-column stack (Card/Info above Image/Plate)

**Material Presentation:**
- Channel grid: 1 column

---

# 7. Current Implementation Status

## 7.1 What Can Be Generated Now

**Complete Data:**
- PCG Process Breakdown (4 graphs with metadata)
- Asset Passport (partial - missing most fields)

**Partial Data:**
- Hero Page (no hero render, no scene name)
- Asset Breakdown (no assets)
- Material Presentation (no materials)

## 7.2 What Cannot Be Generated Yet

**Missing Data Sources:**
- Asset list (assets array empty)
- Material list (materials array empty)
- Render outputs (all render arrays empty)
- Performance stats (stats object null)
- Scene metadata (scene object incomplete)

**Required Pipeline Updates:**
1. Run asset audit to populate `assets` array
2. Run material audit to populate `materials` array
3. Run render capture to populate `renders` arrays
4. Run performance profiling to populate `stats` object
5. Fix scene_metadata export to include required fields

---

# 8. Recommendations

## 8.1 Immediate Actions

1. **Fix scene_metadata export** to include:
   - `scene_name`
   - `level_path`
   - `engine`

2. **Run asset audit** to populate `assets` array with:
   - Static mesh actors from scene
   - Triangle counts
   - Material assignments
   - LOD information

3. **Run material audit** to populate `materials` array with:
   - Material instances used in scene
   - Texture counts
   - Parameter counts
   - Preview images

4. **Run render capture** to populate `renders` arrays:
   - Hero beauty shot
   - Breakdown renders (composition, modular, lighting)
   - Material channel renders
   - PCG graph visualizations

5. **Run performance profiling** to populate `stats` object:
   - Triangle count
   - Draw calls
   - Material count
   - Texture count

## 8.2 Design System Updates

1. **Add missing UI components** (Section 4):
   - Badge/DataStatus
   - Placeholder/DataMissing
   - Info/GraphMetadata
   - Tag/PCGFeature
   - Layout/ProcessFlow
   - Chart/Bar
   - Card/Performance

2. **Update Asset Passport schema** to handle missing data gracefully

3. **Create fallback patterns** for incomplete data

---

# 9. Technical Director Reading Path

**Recommended page order for technical director review:**

1. **Hero Page** → Quick overview: What is this? Key stats?
2. **Process Breakdown** → How was it built procedurally? PCG competence?
3. **Asset Breakdown** → What assets? Modular construction?
4. **Material Presentation** → Material systems? Shader competence?
5. **Technical Documentation** → Deep technical details

**Each page should answer:**
- What technical decisions were made?
- What tools/workflows were used?
- What are the performance implications?
- What is reusable/scalable?

---

# 10. Appendix: Component Property Mapping Reference

## 10.1 Brand/AssetPassport

| Property | Source | Type | Transformation |
|----------|--------|------|----------------|
| projectName | scene.scene_name | string | Direct |
| category | Derived | string | "Environment" (default) |
| triangleCount | stats.triangle_count | number | Format: "X,XXX" |
| polyCount | stats.triangle_count | number | Format: "X,XXX" (÷2 approx) |
| materialCount | stats.material_count | number | Format: "X" |
| textureCount | stats.texture_count | number | Format: "X" |
| textureResolution | stats.texture_resolution | string | Direct |
| drawCalls | stats.draw_calls | number | Format: "X" |
| lod | Derived | string | "LOD0–LOD{max}" |
| nanite | Derived | string | "Yes" / "No" |
| platform | Static | string | "PC / Console" |
| software | Static | array | ["Blender", "Unreal Engine"] |
| engine | scene.engine | string | Format: "Unreal Engine {version}" |
| date | scene.timestamp | string | ISO → YYYY-MM |
| version | Static | string | "v1.0" |

## 10.2 Tag/Technical

| Property | Source | Type | Transformation |
|----------|--------|------|----------------|
| Type | Derived | enum | Poly Count, Material Count, etc. |
| Value | stats.* | number/string | Format per type |
| showIcon | Static | boolean | true |

## 10.3 Card/Info

| Property | Source | Type | Transformation |
|----------|--------|------|----------------|
| Type | Derived | enum | Project Information,Asset Statistics, etc. |
| Header | Static | enum | WithRule |
| Title | Derived | string | Asset name, material name, etc. |
| Rows | Derived | array | Row/Spec components |

## 10.4 Image/Plate

| Property | Source | Type | Transformation |
|----------|--------|------|----------------|
| imageSource | renders.* | string | File path |
| caption | Derived | string | Render type, asset name, etc. |
| showFrame | Static | boolean | true |
