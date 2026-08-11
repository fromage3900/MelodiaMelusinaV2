# Figma Mapping Guide

**Purpose:** Define how Unreal Engine portfolio outputs map to Figma design system components and layouts  
**Role:** Design System Bridge Layer — mapping logic only, no engine or design system modifications

---

## 1. Unreal Output Schema Analysis

### 1.1 Scene Metadata Schema

**Source:** `scene_metadata_exporter.py` → `Saved/Portfolio/scene_metadata.json`

```json
{
  "level_name": "L_SakuraPath",
  "level_path": "/Game/EnvSandbox/Levels/L_SakuraPath",
  "engine_version": "5.8.0",
  "timestamp": "2026-06-25T05:00:00Z",
  "static_mesh_actors": [
    {
      "label": "Rock_01",
      "mesh": "/Game/EnvSandbox/Meshes/GB_ZEN_Rock_01",
      "materials": ["/Game/EnvSandbox/Materials/Instances/MI_Zen_Rock"]
    }
  ],
  "materials": ["/Game/EnvSandbox/Materials/Instances/MI_Zen_Rock"],
  "material_instances": ["/Game/EnvSandbox/Materials/Instances/MI_Zen_Rock"],
  "counts": {
    "static_mesh_actors": 42,
    "materials": 12,
    "material_instances": 12
  }
}
```

**Source:** `capture_scene_metadata.py` → `Saved/Portfolio/SceneMetadata/scene_metadata.json`

```json
{
  "ok": true,
  "world": "L_SakuraPath",
  "actor_count": 156,
  "pcg_volume_count": 8,
  "material_instance_counts": {
    "MI_Zen_Rock": 24,
    "MI_Sakura_Bark": 18
  },
  "actors": [
    {
      "label": "Rock_01",
      "class": "StaticMeshActor",
      "location": [1200.5, -450.2, 85.0],
      "tags": ["Portfolio_Hero", "Breakdown_Target"]
    }
  ],
  "pcg_volumes": [
    {
      "label": "PCG_Forest",
      "graph": "/Game/EnvSandbox/PCG/Graphs/PCG_ForestGeneration"
    }
  ]
}
```

### 1.2 Asset Metadata Schema

**Source:** Python audit scripts (`audit_pcg_portfolio.py`, `audit_material_library.py`)

```json
{
  "projectName": "Sakura Path Environment",
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
  "software": ["Blender", "ZBrush", "Substance Painter", "Houdini", "Unreal Engine"],
  "engine": "Unreal Engine 5.8",
  "date": "2026-06",
  "version": "1.2"
}
```

### 1.3 Material Data Schema

**Source:** Material audit scripts

```json
{
  "material_name": "MI_Zen_Rock",
  "parent_master": "M_Master_Toon_Universal",
  "toon_profile": "Zen",
  "texture_slots": {
    "base_color": "/Game/Textures/T_Rock_BaseColor",
    "normal": "/Game/Textures/T_Rock_Normal",
    "roughness": "/Game/Textures/T_Rock_Roughness"
  },
  "parameters": {
    "roughness_value": 0.65,
    "normal_intensity": 1.0
  }
}
```

### 1.4 PCG Data Schema

**Source:** PCG audit scripts

```json
{
  "graph_path": "/Game/EnvSandbox/PCG/Graphs/PCG_ForestGeneration",
  "node_count": 24,
  "node_types": {
    "StaticMeshSampler": 8,
    "Transform": 6,
    "AttributeMath": 4
  },
  "parameters": {
    "density": 0.75,
    "random_seed": 42
  }
}
```

---

## 2. Component Property Mapping

### 2.1 Brand/AssetPassport Mapping

**DESIGN_SYSTEM.md Schema:**
```json
{
  "projectName": "string",
  "category": "string",
  "triangleCount": "string",
  "polyCount": "string",
  "materialCount": "string",
  "textureCount": "string",
  "textureResolution": "string",
  "drawCalls": "string",
  "lod": "string",
  "nanite": "boolean",
  "platform": "string",
  "software": "array",
  "engine": "string",
  "date": "string",
  "version": "string"
}
```

**Unreal → Figma Mapping:**

| Unreal Source | Unreal Key | Figma Property | Transformation |
|----------------|------------|----------------|----------------|
| Asset metadata | `projectName` | `projectName` | Direct mapping |
| Asset metadata | `category` | `category` | Direct mapping |
| Asset metadata | `triangleCount` | `triangleCount` | Format with commas (e.g., "482,318") |
| Asset metadata | `polyCount` | `polyCount` | Format with commas (e.g., "248,110") |
| Asset metadata | `materialCount` | `materialCount` | Direct mapping |
| Asset metadata | `textureCount` | `textureCount` | Direct mapping |
| Asset metadata | `textureResolution` | `textureResolution` | Direct mapping (e.g., "4K") |
| Asset metadata | `drawCalls` | `drawCalls` | Direct mapping |
| Asset metadata | `lod` | `lod` | Direct mapping (e.g., "LOD0–LOD3") |
| Asset metadata | `nanite` | `nanite` | Boolean → string ("True"/"False") |
| Asset metadata | `platform` | `platform` | Direct mapping |
| Asset metadata | `software` | `software` | Array → Tag/Software instances |
| Scene metadata | `engine_version` | `engine` | Format (e.g., "Unreal Engine 5.8") |
| Scene metadata | `timestamp` | `date` | Extract YYYY-MM (e.g., "2026-06") |
| Asset metadata | `version` | `version` | Direct mapping |

**Mapping Rules:**
- Numeric values must be formatted with commas for readability
- Boolean values converted to human-readable strings
- Software array mapped to Tag/Software component instances via instance-swap
- Engine version prefixed with "Unreal Engine" if not present
- Date extracted from ISO timestamp to YYYY-MM format

### 2.2 Tag/Technical Mapping

**Unreal → Figma Mapping:**

| Unreal Source | Unreal Key | Figma Property | Transformation |
|----------------|------------|----------------|----------------|
| Scene metadata | `counts.static_mesh_actors` | `label` | "Static Mesh Actors" |
| Scene metadata | `counts.static_mesh_actors` | `value` | Direct mapping |
| Scene metadata | `counts.materials` | `label` | "Materials" |
| Scene metadata | `counts.materials` | `value` | Direct mapping |
| Asset metadata | `triangleCount` | `label` | "Triangle Count" |
| Asset metadata | `triangleCount` | `value` | Format with commas |
| Asset metadata | `drawCalls` | `label` | "Draw Calls" |
| Asset metadata | `drawCalls` | `value` | Direct mapping |
| Asset metadata | `nanite` | `label` | "Nanite" |
| Asset metadata | `nanite` | `value` | Boolean → "Enabled"/"Disabled" |

**Mapping Rules:**
- Labels use Title Case for readability
- Values formatted with commas for numbers
- Boolean values converted to human-readable strings
- Emphasis set to "Strong" for key metrics (triangle count, draw calls)

### 2.3 Card/Info Mapping

**Unreal → Figma Mapping:**

| Unreal Source | Unreal Key | Figma Property | Transformation |
|----------------|------------|----------------|----------------|
| Scene metadata | `static_mesh_actors` | `title` | "Asset Statistics" |
| Scene metadata | `static_mesh_actors` | `rows` | Array of Row/Spec from actor data |
| Scene metadata | `material_instance_counts` | `title` | "Material Distribution" |
| Scene metadata | `material_instance_counts` | `rows` | Array of Row/Spec from material counts |
| PCG metadata | `node_types` | `title` | "PCG Node Distribution" |
| PCG metadata | `node_types` | `rows` | Array of Row/Spec from node types |

**Mapping Rules:**
- Card title derived from data type
- Rows created by iterating over dictionary keys
- Keys formatted as Title Case labels
- Values formatted as strings

---

## 3. Template Mapping

### 3.1 Hero Render → Hero Page Template

**Unreal Output:**
- Hero render image: `Saved/Portfolio/Hero_SakuraPath.png` (1920x1080)
- Scene metadata: `scene_metadata.json`

**Figma Template:** Hero Page (Template #1)

**Mapping:**

| Unreal Output | Figma Component | Figma Property | Transformation |
|---------------|-----------------|----------------|----------------|
| Hero render PNG | `Image/Plate[Beauty]` | `imageSource` | File path or embedded image |
| Scene metadata `level_name` | Text layer | `text` | Direct mapping |
| Asset metadata `projectName` | `Display/XL` | `text` | Direct mapping |
| Asset metadata (full schema) | `Brand/AssetPassport[Banner]` | All properties | See §2.1 mapping |

**Layout Structure:**
```
Hero Page Template
├─ Image/Plate[Beauty] (full-bleed hero render)
│  └─ Overlay: Display/XL title
├─ Brand/AssetPassport[Banner] (bottom-left overlay)
└─ Scroll cue (Star/4pt + text)
```

**Population Rules:**
1. Hero render fills `Image/Plate[Beauty]` with `showFrame=false`
2. Title from `level_name` or `projectName` uses `Display/XL` style
3. Asset Passport populated with full asset metadata schema
4. Scroll cue added automatically (static component)

### 3.2 Asset Metadata → Asset Passport Component

**Unreal Output:**
- Asset metadata JSON from audit scripts
- Scene metadata for engine version and timestamp

**Figma Component:** Brand/AssetPassport

**Mapping:** See §2.1 for complete property mapping

**Population Rules:**
1. All 14 properties populated from asset metadata
2. Engine version from scene metadata if not in asset metadata
3. Date extracted from scene timestamp if not in asset metadata
4. Software array converted to Tag/Software instances
5. Format variant selected based on breakpoint (Banner/Card/Compact)

### 3.3 Material Data → Material Presentation Template

**Unreal Output:**
- Material grid render: `Saved/Portfolio/Material_Grid_SDF.png` (2048x2048)
- Material metadata JSON
- Individual channel renders (Albedo, Normal, Roughness, etc.)

**Figma Template:** Material Presentation (Template #4)

**Mapping:**

| Unreal Output | Figma Component | Figma Property | Transformation |
|---------------|-----------------|----------------|----------------|
| Material grid PNG | `Image/Plate` | `imageSource` | Hero sphere/plane render |
| Channel renders | `Image/Plate` array | `imageSource` | Channel grid (4x4) |
| Channel names | `Legend/Swatch` | `label` | Channel type (e.g., "Albedo") |
| Material metadata | `Card/Info[Material Statistics]` | `title` | "Material Statistics" |
| Material metadata | `Card/Info[Material Statistics]` | `rows` | Material parameters as Row/Spec |

**Layout Structure:**
```
Material Presentation Template
├─ Title Block (Title/Project + Tag/Technical cluster)
├─ Image/Plate (material hero sphere/plane)
├─ Channel Grid (4x4 grid)
│  ├─ Image/Plate (Albedo) + Legend/Swatch
│  ├─ Image/Plate (Normal) + Legend/Swatch
│  ├─ Image/Plate (Roughness) + Legend/Swatch
│  └─ Image/Plate (Metallic/AO) + Legend/Swatch
└─ Card/Info[Material Statistics]
```

**Population Rules:**
1. Material hero render fills top `Image/Plate`
2. Channel renders populate 4x4 grid with `Image/Plate` + `Legend/Swatch` pairs
3. Material metadata populates `Card/Info[Material Statistics]`
4. Channel names derived from texture slot names
5. Grid uses Auto Layout Wrap for responsive behavior

### 3.4 PCG Data → Technical Diagram Layout

**Unreal Output:**
- PCG graph visualization render: `Saved/Portfolio/PCG_Graph_Visualization.png`
- PCG metadata JSON (node count, node types, parameters)
- PCG volume metadata from scene metadata

**Figma Template:** Process Breakdown (Template #8)

**Mapping:**

| Unreal Output | Figma Component | Figma Property | Transformation |
|---------------|-----------------|----------------|----------------|
| PCG graph render | `Image/Plate` | `imageSource` | Graph visualization |
| PCG metadata `node_count` | `Process/Step` | `stepNumber` | Sequential numbering |
| PCG metadata `graph_path` | `Process/Step` | `title` | Graph name (extracted from path) |
| PCG metadata `node_types` | `Process/Step` | `description` | Node type distribution |
| PCG metadata `parameters` | `Card/Info` | `rows` | Parameters as Row/Spec |

**Layout Structure:**
```
Process Breakdown Template
├─ Title (Title/Project)
├─ Process/Step timeline (vertical)
│  ├─ Process/Step #1 (PCG Graph Setup)
│  ├─ Process/Step #2 (Node Configuration)
│  ├─ Process/Step #3 (Parameter Tuning)
│  └─ Process/Step #4 (Output Generation)
├─ Image/Plate (PCG graph visualization)
└─ Brand/AssetPassport
```

**Population Rules:**
1. PCG graph visualization fills `Image/Plate`
2. Each PCG stage mapped to `Process/Step` component
3. Step numbers auto-increment from 1
4. Node type distribution formatted as description text
5. Parameters populated in `Card/Info` below steps

### 3.5 Scene Metadata → Environment Breakdown Page

**Unreal Output:**
- Scene metadata JSON (actors, PCG volumes, material counts)
- Breakdown renders (wireframe, UV density, shader complexity)
- Lighting pass renders (if available)

**Figma Template:** Environment Breakdown (Template #3)

**Mapping:**

| Unreal Output | Figma Component | Figma Property | Transformation |
|---------------|-----------------|----------------|----------------|
| Beauty render | `Image/Plate[Beauty]` | `imageSource` | Full-bleed beauty shot |
| Wireframe render | `Image/Plate` | `imageSource` | Wireframe breakdown |
| UV density render | `Image/Plate` | `imageSource` | UV density breakdown |
| Scene metadata `actor_count` | `Tag/Technical` | `label` | "Actor Count" |
| Scene metadata `actor_count` | `Tag/Technical` | `value` | Direct mapping |
| Scene metadata `pcg_volume_count` | `Tag/Technical` | `label` | "PCG Volumes" |
| Scene metadata `pcg_volume_count` | `Tag/Technical` | `value` | Direct mapping |
| Scene metadata `material_instance_counts` | `Card/Info` | `rows` | Material distribution |
| Scene metadata `pcg_volumes` | `Card/Info` | `rows` | PCG volume list |

**Layout Structure:**
```
Environment Breakdown Template
├─ Title Block (Title/Project + Tag/Technical cluster)
├─ Image/Plate[Beauty] (wide beauty shot)
├─ "Composition" annotated plate (optional)
├─ Modular-kit grid (Image/Plate array)
├─ Lighting passes row (Image/Plate array)
├─ Card/Info (Environment Statistics)
└─ Tag/Technical cluster (performance metrics)
```

**Population Rules:**
1. Beauty render fills top `Image/Plate[Beauty]`
2. Breakdown renders populate modular-kit grid
3. Lighting passes populate horizontal row if available
4. Scene metadata populates `Card/Info[Environment Statistics]`
5. Tag cluster populated with actor count, PCG volume count, material counts

---

## 4. Data Transformation Rules

### 4.1 Number Formatting

**Rule:** All numeric values formatted with commas for readability

**Transformations:**
- `482318` → `"482,318"`
- `248110` → `"248,110"`
- `184` → `"184"`

**Implementation:** Apply locale-aware number formatting with comma separators

### 4.2 Boolean Formatting

**Rule:** Boolean values converted to human-readable strings

**Transformations:**
- `true` → `"True"` or `"Enabled"`
- `false` → `"False"` or `"Disabled"`

**Implementation:** Context-dependent conversion (nanite → "Enabled"/"Disabled")

### 4.3 Date Formatting

**Rule:** ISO timestamps converted to YYYY-MM format

**Transformations:**
- `"2026-06-25T05:00:00Z"` → `"2026-06"`
- `"2026-03-15T12:30:45Z"` → `"2026-03"`

**Implementation:** Extract year and month from ISO 8601 timestamp

### 4.4 Array to Instance-Swap

**Rule:** Arrays converted to component instances via instance-swap

**Transformations:**
- `["Blender", "ZBrush", "Substance Painter"]` → 3 × `Tag/Software` instances
- Each instance's `softwareName` property set to array element
- Icon instance-swapped based on software name

**Implementation:** Iterate array, create/duplicate component instance, set property, swap icon

### 4.5 Path Extraction

**Rule:** Unreal asset paths extracted to display names

**Transformations:**
- `"/Game/EnvSandbox/Levels/L_SakuraPath"` → `"L_SakuraPath"`
- `"/Game/EnvSandbox/PCG/Graphs/PCG_ForestGeneration"` → `"PCG_ForestGeneration"`

**Implementation:** Extract last path segment after last `/`

### 4.6 Engine Version Formatting

**Rule:** Engine version prefixed with "Unreal Engine"

**Transformations:**
- `"5.8.0"` → `"Unreal Engine 5.8"`
- `"5.8"` → `"Unreal Engine 5.8"`

**Implementation:** Check for prefix, add if missing

---

## 5. Missing Data Fields

### 5.1 Unreal Output Gaps

**Missing from scene_metadata.json:**
- `triangleCount` — Not captured by scene metadata exporter
- `polyCount` — Not captured by scene metadata exporter
- `textureCount` — Not captured by scene metadata exporter
- `textureResolution` — Not captured by scene metadata exporter
- `drawCalls` — Not captured by scene metadata exporter
- `lod` — Not captured by scene metadata exporter
- `nanite` — Not captured by scene metadata exporter
- `platform` — Not captured by scene metadata exporter
- `software` — Not captured by scene metadata exporter
- `version` — Not captured by scene metadata exporter

**Resolution:** These fields must come from separate audit scripts (`audit_pcg_portfolio.py`, `audit_material_library.py`) or be manually specified in project configuration.

### 5.2 Figma Component Property Gaps

**Missing from DESIGN_SYSTEM.md schema:**
- `author` — Creator name/team (not in schema)
- `client` — Client name (not in schema)
- `projectUrl` — External project URL (not in schema)
- `license` — License type (not in schema)
- `tags` — Free-form tags (not in schema)
- `description` — Short project description (not in schema)
- `thumbnail` — Thumbnail image path (not in schema)

**Resolution:** These are optional fields not currently required for automation. Can be added to schema if needed.

---

## 6. Mapping Validation

### 6.1 Completeness Check

**Required Fields for Brand/AssetPassport:**
- [x] `projectName` — Available from asset metadata
- [x] `category` — Available from asset metadata
- [x] `triangleCount` — Available from asset metadata (audit script)
- [x] `polyCount` — Available from asset metadata (audit script)
- [x] `materialCount` — Available from scene metadata `counts.materials`
- [x] `textureCount` — Available from asset metadata (audit script)
- [x] `textureResolution` — Available from asset metadata (audit script)
- [x] `drawCalls` — Available from asset metadata (audit script)
- [x] `lod` — Available from asset metadata (audit script)
- [x] `nanite` — Available from asset metadata (audit script)
- [x] `platform` — Available from asset metadata (manual config)
- [x] `software` — Available from asset metadata (manual config)
- [x] `engine` — Available from scene metadata `engine_version`
- [x] `date` — Available from scene metadata `timestamp`
- [x] `version` — Available from asset metadata (manual config)

**Status:** All required fields have Unreal sources. Some require audit scripts or manual configuration.

### 6.2 Type Compatibility Check

| Figma Property | Expected Type | Unreal Source Type | Compatible |
|----------------|---------------|-------------------|------------|
| `projectName` | string | string | ✓ |
| `category` | string | string | ✓ |
| `triangleCount` | string (formatted) | number | ✓ (with formatting) |
| `polyCount` | string (formatted) | number | ✓ (with formatting) |
| `materialCount` | string | number | ✓ (with formatting) |
| `textureCount` | string | number | ✓ (with formatting) |
| `textureResolution` | string | string | ✓ |
| `drawCalls` | string | number | ✓ (with formatting) |
| `lod` | string | string | ✓ |
| `nanite` | boolean | boolean | ✓ |
| `platform` | string | string | ✓ |
| `software` | array (instance-swap) | array | ✓ |
| `engine` | string | string | ✓ |
| `date` | string (YYYY-MM) | string (ISO) | ✓ (with transformation) |
| `version` | string | string | ✓ |

**Status:** All types compatible with appropriate transformations.

---

## 7. Automation Workflow

### 7.1 Data Collection Phase

**Step 1:** Run scene metadata export
```python
py Content/Python/scene_metadata_exporter.py
```
Output: `Saved/Portfolio/scene_metadata.json`

**Step 2:** Run PCG audit
```python
py Content/Python/audit_pcg_portfolio.py
```
Output: `Saved/Audit/pcg_portfolio_audit.json`

**Step 3:** Run material library audit
```python
py Content/Python/audit_material_library.py
```
Output: `Saved/Audit/material_library_audit.json`

**Step 4:** Run Monolith MCP captures
```python
monolith_mcp_client.call_tool("editor_query", {
    "action": "capture_scene_preview",
    "asset_path": "/Game/EnvSandbox/Levels/L_SakuraPath",
    "output_path": "g:/EnvironmentPortfolio/Saved/Portfolio/Hero_SakuraPath.png"
})
```

### 7.2 Data Transformation Phase

**Step 1:** Merge JSON sources into unified schema
- Read `scene_metadata.json`
- Read `pcg_portfolio_audit.json`
- Read `material_library_audit.json`
- Merge into canonical schema (§9.1 of DESIGN_SYSTEM.md)

**Step 2:** Apply formatting transformations
- Format numbers with commas
- Convert booleans to strings
- Extract dates from timestamps
- Format engine versions

**Step 3:** Generate Figma property mapping
- Map merged schema to component properties
- Generate instance-swap arrays for software tags
- Prepare Row/Spec arrays for cards

### 7.3 Figma Population Phase

**Step 1:** Connect to Figma API
- Authenticate with access token
- Open target Figma file
- Locate template instances

**Step 2:** Populate components
- Find `Brand/AssetPassport` instances
- Set component properties from transformed data
- Create/duplicate `Tag/Software` instances for software array
- Populate `Card/Info` rows

**Step 3:** Populate images
- Upload render images to Figma
- Set `Image/Plate` image sources
- Apply captions if available

**Step 4:** Commit changes
- Validate all properties set correctly
- Commit transaction
- Log success/failure

---

## 8. Error Handling

### 8.1 Missing Data Fields

**Error:** Required field missing from Unreal output

**Handling:**
- Log warning with field name
- Use default value if available
- Skip field if optional
- Fail transaction if critical field missing

**Defaults:**
- `triangleCount`: "0"
- `polyCount`: "0"
- `materialCount`: "0"
- `textureCount`: "0"
- `drawCalls`: "0"
- `nanite`: "False"
- `version`: "1.0"

### 8.2 Type Mismatch

**Error:** Unreal data type doesn't match Figma property type

**Handling:**
- Attempt type conversion
- Log warning if conversion fails
- Use default value if conversion fails
- Fail transaction if critical field fails conversion

**Conversions:**
- number → string: `str(value)`
- boolean → string: `"True"` if true else `"False"`
- array → instance-swap: Iterate and create instances

### 8.3 Component Not Found

**Error:** Figma component instance not found in file

**Handling:**
- Log warning with component name
- Skip component if optional
- Fail transaction if critical component missing

**Critical Components:**
- `Brand/AssetPassport`
- `Image/Plate[Beauty]` (for Hero Page)

### 8.4 Image Upload Failure

**Error:** Render image cannot be uploaded to Figma

**Handling:**
- Log warning with image path
- Use placeholder image if available
- Skip image if optional
- Fail transaction if critical image missing

**Critical Images:**
- Hero render (for Hero Page)
- Material grid (for Material Presentation)

---

## 9. Summary

**Mapping Status:**
- ✓ All 14 Brand/AssetPassport properties have Unreal sources
- ✓ All types compatible with appropriate transformations
- ✓ All 5 templates have defined mapping rules
- ✓ Data transformation rules documented
- ✓ Error handling strategies defined

**Next Steps:**
1. Implement data transformation logic in bridge layer
2. Implement Figma API integration
3. Test end-to-end mapping with sample data
4. Validate component population in Figma
5. Document any additional gaps discovered during testing
