# Export Standardization Notes

**Date:** 2025-06-25  
**Purpose:** Record every schema alignment change made to portfolio JSON exporters so they are merge-ready for `portfolio_aggregator.py`.

---

## 1. Changes Applied

### 1.1 `setup_pcg_universal.py`
- **Added:** `generated_at`, `generated_by`, `ok`
- **Removed:** `passed` (replaced by `ok`)
- **Impact:** Aggregator can now validate this source; timestamp normalized

### 1.2 `apply_starter_instances.py`
- **Added:** `generated_at`, `generated_by`, `ok`
- **Impact:** Consistent top-level schema with other audit exports

### 1.3 `setup_pcg_greybox.py`
- **Added:** `generated_at`, `generated_by`, `ok`
- **Removed:** `timestamp` (replaced by `generated_at`)
- **Note:** `passed` retained in payload for backward compat but `ok` is canonical

### 1.4 `pipeline/inspector/scan_scripts.py`
- **Added:** `generated_at`, `generated_by`, `ok`
- **Renamed:** `scan_time` → `generated_at`
- **Impact:** Aggregator receives consistent timestamp field

### 1.5 `capture_scene_metadata.py`
- **Added:** `generated_at`, `generated_by`, `ok`
- **Impact:** Scene metadata now mergeable; success flag explicit

### 1.6 `capture_material_previews.py`
- **Added:** `generated_at`, `generated_by`, `ok`
- **Impact:** Material preview manifest now mergeable

### 1.7 `import_world_manifest.py`
- **Added:** `generated_at`, `generated_by`
- **Impact:** World manifest now includes standard metadata; `ok` already present

### 1.8 `portfolio_aggregator.py` (new)
- **Created:** Single compiler that reads 5 sources, validates, merges
- **Output:** `Saved/Portfolio/portfolio_package.json`

---

## 2. Rationale

### 2.1 Timestamp Chaos
- **Before:** `timestamp`, `scan_time`, or absent
- **After:** `generated_at` (ISO8601 UTC) everywhere
- **Why:** Aggregator needs single sortable field

### 2.2 Success Flag Inconsistency
- **Before:** `ok`, `passed`, or absent
- **After:** `ok` (boolean) everywhere
- **Why:** Aggregator can compute overall health with uniform key

### 2.3 Missing Provenance
- **Before:** No way to trace which script produced a JSON file
- **After:** `generated_by` (script filename) in every export
- **Why:** Debugging and audit trails require source attribution

---

## 3. Migration Guide

### 3.1 Existing JSON Files
Old exports lacking `generated_at`/`generated_by` will produce validation warnings but will not fail aggregation. The aggregator logs missing fields and uses sensible defaults.

### 3.2 Re-running Exporters
Simply re-run any affected script to generate a new compliant JSON file:
```bash
py Content/Python/setup_pcg_universal.py
py Content/Python/apply_starter_instances.py
py Content/Python/setup_pcg_greybox.py
py pipeline/inspector/scan_scripts.py
py Content/Python/capture_scene_metadata.py
py Content/Python/capture_material_previews.py
py Content/Python/import_world_manifest.py
```

### 3.3 Aggregator Invocation
```bash
py Content/Python/portfolio_aggregator.py
```
Output: `Saved/Portfolio/portfolio_package.json`

---

## 4. Validation Behavior

The aggregator:
1. Loads each source; returns `None` if missing/unreadable
2. Checks for the 3 canonical top-level fields
3. Logs issues into `validation_issues` array
4. Computes `ok` as `True` only if all sources report `ok: true` AND no missing canonical fields
5. Never modifies source files

---

## 5. Path Standards

All exporters follow these conventions:
- **UE Asset Paths:** `/Game/EnvSandbox/...`
- **Filesystem Paths:** Absolute with forward slashes (`g:/...`)
- **Output Dirs:**
  - `Saved/Portfolio/` — capture outputs
  - `Saved/Audit/` — build/audit outputs
  - `pipeline/inspector/` — pipeline inventory

---

## 6. Extensibility

New exporters must:
1. Include `generated_at`, `generated_by`, `ok` at top level
2. Write JSON with `indent=2` and `ensure_ascii=False`
3. Place outputs in existing directory structure (no new roots)
4. Not modify any source JSON files of other exporters

Breaking changes to existing schema require incrementing `output_version` in the aggregator.