# Schema Alignment Map

**Purpose:** Defines which JSON file owns each data field to prevent duplication and conflicts in the portfolio aggregation system.

---

## 1. Top-Level Aggregation Fields

Every JSON export intended for `portfolio_package.json` merger must include:

| Field | Type | Owner | Description |
|-------|------|-------|-------------|
| `generated_at` | ISO8601 string | Exporter | When the export was created |
| `generated_by` | string | Exporter | Script filename (e.g., `capture_scene_metadata.py`) |
| `ok` | boolean | Exporter | Whether export succeeded |
| `project_root` | string | Exporter | Absolute path to project root |

---

## 2. Domain Field Ownership

### 2.1 Scene & World Data

| Field | Primary File | Secondary | Notes |
|-------|-------------|-----------|-------|
| `actors` (runtime list) | `capture_scene_metadata.py` | None | Live editor state |
| `actors` (authored dict) | `import_world_manifest.py` | None | Blender-authored transforms |
| `world` | `capture_scene_metadata.py` | None | Current world name |
| `actor_count` | `capture_scene_metadata.py` | None | Derived from runtime actors |
| `pcg_volume_count` | `capture_scene_metadata.py` | None | Derived from runtime actors |

### 2.2 PCG Data

| Field | Primary File | Secondary | Notes |
|-------|-------------|-----------|-------|
| `graphs.*` | `setup_pcg_universal.py` | `capture_scene_metadata.py` | Graph paths only |
| `collections` | `setup_pcg_universal.py` | None | Scatter kit duplication status |
| `greybox_presets` | `setup_pcg_universal.py` | None | Preset build results |
| `level` | `setup_pcg_greybox.py` | None | Target level path |
| `preset` | `setup_pcg_greybox.py` | None | Preset name |
| `ism_*` | `setup_pcg_greybox.py` | None | ISM counts and bands |

### 2.3 Material Data

| Field | Primary File | Secondary | Notes |
|-------|-------------|-----------|-------|
| `material_instance_counts` | `capture_scene_metadata.py` | None | Usage counts by name |
| `materials.*.path` | `capture_material_previews.py` | None | Asset path |
| `materials.*.label` | `capture_material_previews.py` | None | Display label |
| `materials.*.thumbnail` | `capture_material_previews.py` | None | PNG path |
| `instances[].textures` | `apply_starter_instances.py` | None | Parameter bindings |
| `master_defaults` | `portfolio_texture_catalog.py` | None | Catalog defaults |
| `instance_defaults` | `portfolio_texture_catalog.py` | None | Catalog defaults |

### 2.4 Screenshots & Media

| Field | Primary File | Secondary | Notes |
|-------|-------------|-----------|-------|
| Screenshot PNG | `export_screenshot.py` | None | Binary file, no JSON schema |

### 2.5 Pipeline Inventory

| Field | Primary File | Secondary | Notes |
|-------|-------------|-----------|-------|
| `scripts[]` | `pipeline/inspector/scan_scripts.py` | None | Full script inventory |
| `orphan_scripts` | `pipeline/inspector/scan_scripts.py` | None | Scripts without entry points |

---

## 3. Conflict Resolution Rules

### 3.1 Actor Data Conflict
- **Scenario:** Both `capture_scene_metadata.py` and `import_world_manifest.py` export actor data
- **Resolution:** 
  - `capture_scene_metadata.actors` is the authoritative runtime state
  - `import_world_manifest.actors` is the authored definition (transform, mesh, role)
  - Aggregator merges them by matching `label` or `name` fields
  - If name collision occurs, prefix authored actors with `world_`

### 3.2 Material Path Conflicts
- **Scenario:** Same material referenced by name in one file and full path in another
- **Resolution:**
  - All Unreal asset references use full `/Game/...` paths
  - Count-based keys use `asset.get_name()` only
  - Aggregator normalizes by stripping paths to names for count merging

### 3.3 Timestamp Conflicts
- **Scenario:** Different timestamp formats and field names
- **Resolution:**
  - All exporters use `generated_at` (ISO8601 with `Z`)
  - Aggregator sorts by `generated_at`
  - Legacy `timestamp` and `scan_time` are normalized on read

---

## 4. Data Flow for Aggregation

```
pipeline/inspector/scan_report.json
    └── scripts[], orphan_scripts

Saved/Portfolio/SceneMetadata/scene_metadata.json
    └── actors[], pcg_volumes[], material_instance_counts

Saved/Portfolio/MaterialPreviews/previews_manifest.json
    └── materials[] (with thumbnails)

Saved/Audit/pcg_universal_build.json
    └── graphs{}, collections{}, greybox_presets

Saved/Audit/import_world_manifest.json
    └── actors{} (authored transforms)

All merge into:
portfolio_package.json
    ├── generated_at (max of all inputs)
    ├── generated_by ("portfolio_aggregator")
    ├── ok (all ok && no errors)
    ├── project_root
    ├── scripts (from scan_report)
    ├── scene (from scene_metadata)
    ├── materials (from material_previews)
    ├── pcg (from pcg_universal_build)
    └── world (from import_world_manifest)
```

---

## 5. Field Normalization Rules

| Domain | Format | Example |
|--------|--------|---------|
| UE Asset Paths | `/Game/<folder>/<name>.<name>` | `/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal` |
| Filesystem Paths | Absolute with forward slashes | `g:/EnvironmentPortfolio/BS_GodFile/Saved/...` |
| Actor Locations | `[x, y, z]` floats, 2 decimal places | `[100.50, -200.25, 50.00]` |
| Material Names | `asset.get_name()` only | `M_Master_Toon_Universal` |
| Booleans | JSON `true`/`false` | `true` |
| Timestamps | ISO8601 with `Z` | `2025-06-25T01:00:00Z` |

---

## 6. Extensibility Rules

1. **New export fields:** Add to primary file first; secondary references must be derived, not duplicated
2. **New exporter:** Must include all four top-level fields (`generated_at`, `generated_by`, `ok`, `project_root`)
3. **New domain:** Create new section in this document before implementing
4. **Breaking changes:** Increment `output_version` and update aggregator compatibility check