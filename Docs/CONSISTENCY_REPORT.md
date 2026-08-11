# Export System Consistency Report

**Date:** 2025-06-25  
**Scope:** All JSON export outputs in `Content/Python/` and `pipeline/inspector/`  
**Goal:** Identify schema inconsistencies before aggregation system implementation.

---

## 1. Inventory of Export Outputs

| Script | Output Path | Top-Level Keys | Timestamp Field | Success Field |
|--------|------------|----------------|-----------------|---------------|
| `capture_scene_metadata.py` | `Saved/Portfolio/SceneMetadata/scene_metadata.json` | `ok`, `world`, `actor_count`, `pcg_volume_count`, `material_instance_counts`, `actors`, `pcg_volumes` | **None** | `ok` |
| `capture_material_previews.py` | `Saved/Portfolio/MaterialPreviews/previews_manifest.json` | `ok`, `count`, `materials` | **None** | `ok` |
| `export_screenshot.py` | `Saved/Portfolio/Screenshots/` (PNG only, no JSON) | Returns dict but does not persist | **None** | `ok` |
| `import_world_manifest.py` | `Saved/Audit/import_world_manifest.json` | `ok`, `error?`, `errors?`, `actors`, `manifest` | **None** | `ok` |
| `setup_pcg_universal.py` | `Saved/Audit/pcg_universal_build.json` | `timestamp`, `graphs`, `collections`, `greybox_presets`, `passed` | `timestamp` (ISO8601) | `passed` |
| `apply_starter_instances.py` | `Saved/Audit/starter_instances.json` | `timestamp?`, `starter_count`, `instances`, `texture_refresh` | `timestamp` (ISO8601) | implicit |
| `portfolio_texture_catalog.py` | `Saved/Audit/compositing_texture_catalog.json` | `generated_at?`, `master_defaults?`, `instance_defaults?` | `generated_at?` | implicit |
| `pipeline/inspector/scan_scripts.py` | `pipeline/inspector/scan_report.json` | `scan_time`, `project_root`, `total_scripts`, `orphan_count`, `scripts`, `orphan_scripts` | `scan_time` (ISO8601) | implicit |
| `setup_pcg_greybox.py` | `Saved/Audit/pcg_greybox_apply.json` | `timestamp?`, `level`, `preset`, `passed`, `ism_*` | `timestamp` (ISO8601) | `passed` |

---

## 2. Schema Conflicts & Gaps

### 2.1 Timestamp Fields
- **Conflict:** `timestamp` vs `scan_time` vs no timestamp
- **Impact:** Aggregator cannot reliably sort or correlate outputs
- **Fix:** Standardize on `generated_at` (ISO8601) across all files

### 2.2 Success/Completion Flags
- **Conflict:** `ok` (truthy) vs `passed` (truthy) vs no flag
- **Impact:** Aggregator cannot determine overall system health
- **Fix:** Standardize on `ok` (boolean) for all outputs

### 2.3 Asset Path Representation
- **Inconsistency:** 
  - Full UE asset paths: `/Game/EnvSandbox/Materials/...`
  - Relative paths: `Content/Python/...`
  - Names only: asset.get_name()
- **Impact:** Aggregator cannot merge references without normalization
- **Fix:** Define canonical path format per domain (see Alignment Map)

### 2.4 Material Data Ownership
| File | Material Data | Format |
|------|--------------|--------|
| `capture_scene_metadata.py` | `material_instance_counts` | `{"MaterialName": count}` |
| `capture_material_previews.py` | `materials` | `{"MaterialName": {"path":..., "label":..., "thumbnail"?}}` |
| `apply_starter_instances.py` | `instances[].textures` | `{"ParamName": "asset_path"}` |

- **Conflict:** Same concept (material inventory) in three schemas with different structures
- **Fix:** `scene_metadata` owns counts; `material_previews` owns thumbnails; instances own parameter bindings

### 2.5 Actor Data Duplication
- `capture_scene_metadata.py` → `actors[]` with `label`, `class`, `location`, `tags`
- `import_world_manifest.py` → `actors{}` (dict) with `transform_len`, `mesh`, `role`
- **Conflict:** Same world actors represented as list vs dict, different fields
- **Fix:** Scene metadata owns runtime actor list; world manifest owns authored transform/mesh definitions

### 2.6 Missing Fields for Aggregation
The following fields are absent but required for `portfolio_package.json`:
- `generated_by` (script name/version)
- `project_root` (consistent absolute path)
- `unreal_version` (editor version)
- `asset_count` (total assets touched)
- `output_version` (schema version for future migration)

### 2.7 Directory Structure Inconsistency
- Audit outputs: `Saved/Audit/`
- Portfolio outputs: `Saved/Portfolio/` (new)
- Pipeline outputs: `pipeline/inspector/`
- **Fix:** Acceptable separation; aggregator must scan all three roots

---

## 3. Canonical Field Standard (Lightweight)

### 3.1 Top-Level Fields (All JSON Exports)
```json
{
  "generated_at": "2025-06-25T01:00:00Z",  // ISO8601, replaces timestamp/scan_time
  "generated_by": "script_name.py",         // script filename
  "ok": true,                               // boolean success flag
  "project_root": "g:/EnvironmentPortfolio/BS_GodFile"
}
```

### 3.2 Field Ownership Matrix

| Domain | Primary File | Secondary References |
|--------|-------------|---------------------|
| Scene actors (runtime) | `capture_scene_metadata.py` | None |
| World actors (authored) | `import_world_manifest.py` | None |
| PCG graphs | `setup_pcg_universal.py` | `capture_scene_metadata.py` (graph path only) |
| Material instances | `apply_starter_instances.py` | `capture_scene_metadata.py` (counts only) |
| Material thumbnails | `capture_material_previews.py` | None |
| Screenshots | `export_screenshot.py` | None (binary PNG) |
| Script inventory | `pipeline/inspector/scan_scripts.py` | None |

### 3.3 Naming Conventions
- **Keys:** `snake_case` for all JSON keys (already mostly consistent)
- **Paths:** Full UE asset paths (`/Game/...`) for Unreal resources; absolute filesystem paths for exports
- **Timestamps:** ISO8601 with `Z` suffix (`2025-06-25T01:00:00Z`)

---

## 4. Immediate Fixes Required

1. **Add `generated_at` to:** `capture_scene_metadata.py`, `capture_material_previews.py`, `export_screenshot.py` (manifest), `import_world_manifest.py`
2. **Rename `timestamp` → `generated_at` in:** `setup_pcg_universal.py`, `apply_starter_instances.py`, `setup_pcg_greybox.py`
3. **Rename `scan_time` → `generated_at` in:** `pipeline/inspector/scan_scripts.py`
4. **Add `ok` boolean to:** `setup_pcg_universal.py` (`passed` → keep as alias or replace)
5. **Add `generated_by` to all outputs**
6. **Normalize `location` format in scene_metadata** (currently `[x,y,z]`, ensure consistent float precision)

---

## 5. Files NOT Requiring Changes
- `portfolio_texture_catalog.py` — internal catalog, not export
- `setup_landscape_height_blend.py` — build report, not aggregation target
- `audit_*` scripts — diagnostic only, not part of portfolio package
- `run_*_loop_tick.py` — loop state files, separate concern