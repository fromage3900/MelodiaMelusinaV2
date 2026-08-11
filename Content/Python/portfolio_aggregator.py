"""Aggregate all portfolio JSON exports into single portfolio_package.json.

Reads exporter fragments (read-only):
  Saved/Portfolio/Metadata/scene_metadata.json
  Saved/Portfolio/MaterialPreviews/previews_manifest.json
  Saved/Portfolio/Renders/renders_manifest.json
  Saved/Audit/pcg_universal_build.json
  Saved/Portfolio/Stats/portfolio_stats_manifest.json

Writes:
  Saved/Portfolio/portfolio_package.json

Always writes valid JSON output. Missing inputs are logged as warnings and
replaced with empty defaults; execution never aborts before the package is written.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import portfolio_output_layout as portfolio_fs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = Path(__file__).resolve().parent / "portfolio_schema.json"
OUT_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "portfolio_package.json"

SOURCE_ORDER = (
    "scene_metadata",
    "material_previews",
    "renders_manifest",
    "pcg_build",
    "stats_manifest",
    "genome_axis",
    "pcg_heatmap",
)

_FALLBACK_SCHEMA: dict[str, Any] = {
    "version": "1.0",
    "required_top_level_keys": [
        "scene",
        "assets",
        "materials",
        "renders",
        "pcg",
        "stats",
        "metadata",
    ],
    "sections": {
        "scene": {
            "required": ["scene_name", "level_path", "engine", "timestamp"],
            "optional": [],
        },
        "assets": {"type": "array", "required_fields": []},
        "materials": {"type": "array", "required_fields": []},
        "renders": {
            "required_groups": ["hero", "breakdown", "materials", "pcg"],
        },
        "pcg": {"required_fields": ["graphs"]},
        "stats": {"required_fields": ["triangle_count", "draw_calls"]},
        "metadata": {"required": []},
    },
    "source_fragments": {},
    "field_mappings": {
        "scene": {
            "scene_name": ["level_name", "world"],
            "level_path": ["level_path"],
            "engine": ["engine_version"],
            "timestamp": ["timestamp", "generated_at"],
        },
        "assets": {
            "asset_name": ["label"],
            "asset_type": ["class"],
            "materials": ["materials"],
        },
        "materials": {
            "material_name": ["_dict_key"],
        },
    },
    "legacy_aliases": {},
}


def _log_warning(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def _resolve_source_paths(*, project_root: Path | None = None) -> dict[str, Path]:
    root = project_root or PROJECT_ROOT
    paths = portfolio_fs.portfolio_paths(project_root=root)
    portfolio_root = paths["portfolio_root"]
    return {
        "scene_metadata": paths["scene_metadata"],
        "scene_metadata_fallback": portfolio_root / "SceneMetadata" / "scene_metadata.json",
        "material_previews": portfolio_root / "MaterialPreviews" / "previews_manifest.json",
        "renders_manifest": portfolio_root / "Renders" / "renders_manifest.json",
        "pcg_build": root / "Saved" / "Audit" / "pcg_universal_build.json",
        "stats_manifest": portfolio_root / "Stats" / "portfolio_stats_manifest.json",
        "genome_axis": portfolio_root / "Metadata" / "genome_axis.json",
        "pcg_heatmap": portfolio_root / "Metadata" / "pcg_heatmap.json",
    }


def _load_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        _log_warning(f"portfolio schema not found at {SCHEMA_PATH}, using built-in defaults")
        return dict(_FALLBACK_SCHEMA)
    try:
        data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        _log_warning(f"portfolio schema unreadable ({exc}), using built-in defaults")
        return dict(_FALLBACK_SCHEMA)
    if not isinstance(data, dict):
        _log_warning("portfolio schema is not a JSON object, using built-in defaults")
        return dict(_FALLBACK_SCHEMA)
    return data


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _normalize_legacy_aliases(data: dict, schema: dict) -> dict:
    """Return a shallow copy with legacy alias keys resolved (read-only transform)."""
    out = dict(data)
    aliases = schema.get("legacy_aliases") or {}
    for canonical, sources in aliases.items():
        if canonical in out:
            continue
        for alias in sources:
            if alias in out:
                out[canonical] = out[alias]
                break
    return out


def _first_present(data: dict, keys: list[str]) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _validate_fragment(
    data: dict | None,
    source_key: str,
    schema: dict,
) -> list[str]:
    warnings: list[str] = []
    if data is None:
        warnings.append(f"{source_key}: missing or unreadable")
        return warnings

    fragments = schema.get("source_fragments") or {}
    fragment = fragments.get(source_key) or {}
    section = fragment.get("section")
    if not section:
        return warnings

    section_schema = (schema.get("sections") or {}).get(section) or {}
    required = section_schema.get("required") or section_schema.get("required_fields") or []
    if section == "renders":
        required = section_schema.get("required_groups") or []

    if section == "scene":
        mappings = (schema.get("field_mappings") or {}).get("scene") or {}
        for field in required:
            source_keys = mappings.get(field) or [field]
            if _first_present(data, source_keys) is None:
                warnings.append(f"{source_key}: missing source for scene.{field}")
    elif section == "materials":
        materials = data.get("materials")
        if not isinstance(materials, dict):
            warnings.append(f"{source_key}: missing 'materials' object")
    elif section == "pcg":
        if "graphs" not in data:
            warnings.append(f"{source_key}: missing 'graphs'")
    elif section == "stats":
        for field in required:
            if field not in data:
                warnings.append(f"{source_key}: missing stats.{field}")
    elif section == "renders":
        for group in required:
            if group not in data:
                warnings.append(f"{source_key}: missing renders.{group}")

    return warnings


def _default_scene_section(schema: dict) -> dict[str, Any]:
    required = (schema.get("sections") or {}).get("scene", {}).get("required") or []
    return {field: None for field in required}


def _default_renders_section(schema: dict) -> dict[str, list]:
    groups = (schema.get("sections") or {}).get("renders", {}).get("required_groups") or []
    return {group: [] for group in groups}


def _default_pcg_section(schema: dict) -> dict[str, list]:
    required = (schema.get("sections") or {}).get("pcg", {}).get("required_fields") or ["graphs"]
    section: dict[str, Any] = {}
    for field in required:
        section[field] = [] if field == "graphs" else None
    return section


def _default_stats_section(schema: dict) -> dict[str, Any]:
    required = (schema.get("sections") or {}).get("stats", {}).get("required_fields") or []
    return {field: None for field in required}


def _map_scene(data: dict | None, schema: dict, warnings: list[str]) -> dict:
    mappings = (schema.get("field_mappings") or {}).get("scene") or {}
    section_schema = (schema.get("sections") or {}).get("scene") or {}
    required = section_schema.get("required") or []
    section = _default_scene_section(schema)

    if not data:
        warnings.append("scene: no scene_metadata source, using null defaults")
        return section

    for field in required:
        source_keys = mappings.get(field) or [field]
        value = _first_present(data, source_keys)
        if value is None:
            warnings.append(f"scene: missing required field '{field}'")
        else:
            section[field] = value
    for field in section_schema.get("optional") or []:
        source_keys = mappings.get(field) or [field]
        value = _first_present(data, source_keys)
        if value is not None:
            section[field] = value
    return section


def _map_assets(data: dict | None, schema: dict, warnings: list[str]) -> list[dict]:
    if not data:
        warnings.append("assets: no scene_metadata source")
        return []

    raw_items = data.get("static_mesh_actors")
    if not isinstance(raw_items, list):
        raw_items = data.get("actors")
    if not isinstance(raw_items, list):
        warnings.append("assets: missing static_mesh_actors or actors array")
        return []

    mappings = (schema.get("field_mappings") or {}).get("assets") or {}
    required = (schema.get("sections") or {}).get("assets", {}).get("required_fields") or []
    assets: list[dict] = []

    for index, item in enumerate(sorted(raw_items, key=lambda entry: str(entry.get("label") or ""))):
        if not isinstance(item, dict):
            warnings.append(f"assets[{index}]: entry is not an object")
            continue
        mapped: dict[str, Any] = {}
        for target, sources in mappings.items():
            value = _first_present(item, sources)
            if value is not None:
                mapped[target] = value
        for field in required:
            if field not in mapped:
                label = item.get("label") or index
                warnings.append(f"assets[{label}]: missing required field '{field}'")
        if mapped:
            assets.append(mapped)

    return assets


def _map_materials(data: dict | None, schema: dict, warnings: list[str]) -> list[dict]:
    if not data:
        warnings.append("materials: no material_previews source")
        return []

    materials_obj = data.get("materials")
    if not isinstance(materials_obj, dict):
        warnings.append("materials: missing 'materials' object in previews_manifest")
        return []

    required = (schema.get("sections") or {}).get("materials", {}).get("required_fields") or []
    field_map = (schema.get("field_mappings") or {}).get("materials") or {}
    items: list[dict] = []

    for name in sorted(materials_obj.keys()):
        entry = materials_obj[name]
        if not isinstance(entry, dict):
            warnings.append(f"materials[{name}]: entry is not an object")
            continue
        mapped: dict[str, Any] = {"material_name": name}
        for target, sources in field_map.items():
            if target == "material_name":
                continue
            value = _first_present(entry, sources)
            if value is not None:
                mapped[target] = value
        for field in required:
            if field not in mapped:
                warnings.append(f"materials[{name}]: missing required field '{field}'")
        items.append(mapped)

    return items


def _map_renders(data: dict | None, schema: dict, warnings: list[str]) -> dict:
    required_groups = (schema.get("sections") or {}).get("renders", {}).get("required_groups") or []
    section: dict[str, Any] = _default_renders_section(schema)

    if not data:
        warnings.append("renders: no renders_manifest source, using empty arrays")
        return section

    for group in required_groups:
        if group not in data:
            warnings.append(f"renders: missing group '{group}', using empty array")
            continue
        value = data[group]
        if isinstance(value, list):
            section[group] = value
        elif value is None:
            section[group] = []
        else:
            section[group] = [value]
    return section


def _map_pcg(data: dict | None, schema: dict, warnings: list[str]) -> dict:
    required = (schema.get("sections") or {}).get("pcg", {}).get("required_fields") or []
    section = _default_pcg_section(schema)

    if not data:
        warnings.append("pcg: no pcg_build source, using empty defaults")
        return section

    for field in required:
        if field in data:
            section[field] = data[field]
        else:
            warnings.append(f"pcg: missing required field '{field}'")
    return section


def _map_stats(data: dict | None, schema: dict, warnings: list[str]) -> dict:
    required = (schema.get("sections") or {}).get("stats", {}).get("required_fields") or []
    section = _default_stats_section(schema)

    if not data:
        warnings.append("stats: no stats_manifest source, using null defaults")
        return section

    for field in required:
        if field in data:
            section[field] = data[field]
        else:
            warnings.append(f"stats: missing required field '{field}'")
    for key, value in data.items():
        if key not in section and key not in ("generated_at", "generated_by", "ok", "project_root"):
            section[key] = value
    return section


def _map_genome(data: dict | None, warnings: list[str]) -> dict:
    """Extract genome axis steps from export_genome_axis output."""
    if not data:
        warnings.append("genome: no genome_axis source")
        return {"axis_steps": [], "genome": None}
    inner = data.get("genome") or {}
    return {
        "genome": inner.get("genome"),
        "axis_steps": inner.get("axis_steps") or [],
        "step_count": inner.get("step_count", 0),
    }


def _map_heatmap(data: dict | None, warnings: list[str]) -> dict:
    """Extract PCG heatmap path from audit_pcg_heatmap output."""
    if not data:
        warnings.append("pcg_heatmap: no heatmap source")
        return {"path": None, "format": None}
    inner = data.get("heatmap") or {}
    return {
        "path": inner.get("path"),
        "format": inner.get("format"),
        "size_px": inner.get("size_px"),
        "exclusion_zones": inner.get("exclusion_zones", []),
    }


def _build_provenance(
    source_key: str,
    path: Path,
    data: dict | None,
) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": data is not None,
        "ok": data.get("ok") if data else None,
        "generated_at": _first_present(data or {}, ["generated_at", "timestamp", "scan_time"]),
        "generated_by": (data or {}).get("generated_by"),
    }


def _validate_package(package: dict, schema: dict, warnings: list[str]) -> None:
    for key in schema.get("required_top_level_keys") or []:
        if key not in package:
            warnings.append(f"package: missing top-level key '{key}'")


def _sections_ok(package: dict, schema: dict) -> bool:
    sections = schema.get("sections") or {}
    for section_name, section_schema in sections.items():
        if section_name == "metadata":
            continue
        section = package.get(section_name)
        if section_name == "scene":
            required = section_schema.get("required") or []
            if not isinstance(section, dict):
                return False
            if any(field not in section for field in required):
                return False
        elif section_name in ("assets", "materials"):
            if not isinstance(section, list):
                return False
        elif section_name == "renders":
            required = section_schema.get("required_groups") or []
            if not isinstance(section, dict):
                return False
            if section and any(group not in section for group in required):
                return False
        elif section_name in ("pcg", "stats"):
            required = section_schema.get("required_fields") or []
            if not isinstance(section, dict):
                return False
            if section and any(field not in section for field in required):
                return False
    return True


def _ensure_package_shape(package: dict, schema: dict) -> dict:
    """Guarantee all top-level keys and null-safe section defaults exist."""
    out = dict(package)
    for key in schema.get("required_top_level_keys") or []:
        if key not in out:
            out[key] = {}

    if not isinstance(out.get("scene"), dict):
        out["scene"] = _default_scene_section(schema)
    else:
        scene_defaults = _default_scene_section(schema)
        for field, default in scene_defaults.items():
            out["scene"].setdefault(field, default)

    if not isinstance(out.get("assets"), list):
        out["assets"] = []
    if not isinstance(out.get("materials"), list):
        out["materials"] = []

    render_defaults = _default_renders_section(schema)
    if not isinstance(out.get("renders"), dict):
        out["renders"] = render_defaults
    else:
        for group, default in render_defaults.items():
            value = out["renders"].get(group)
            if not isinstance(value, list):
                out["renders"][group] = default if value is None else [value]

    pcg_defaults = _default_pcg_section(schema)
    if not isinstance(out.get("pcg"), dict):
        out["pcg"] = pcg_defaults
    else:
        for field, default in pcg_defaults.items():
            out["pcg"].setdefault(field, default)

    stats_defaults = _default_stats_section(schema)
    if not isinstance(out.get("stats"), dict):
        out["stats"] = stats_defaults
    else:
        for field, default in stats_defaults.items():
            out["stats"].setdefault(field, default)

    metadata = out.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata.setdefault("schema_version", schema.get("version", "1.0"))
    metadata.setdefault("aggregated_at", datetime.now(timezone.utc).isoformat())
    metadata.setdefault("aggregated_by", "portfolio_aggregator.py")
    metadata.setdefault("sources", {})
    metadata.setdefault("validation_warnings", [])
    out["metadata"] = metadata
    return out


def write_package(package: dict, *, out_path: Path | None = None) -> Path:
    """Write portfolio_package.json; always creates parent directories."""
    path = out_path or OUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(package, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return path


def aggregate(*, project_root: Path | None = None) -> dict:
    root = project_root or PROJECT_ROOT
    schema = _load_schema()
    warnings: list[str] = []
    source_paths = _resolve_source_paths(project_root=root)

    loaded: dict[str, dict | None] = {}
    provenance: dict[str, dict[str, Any]] = {}

    scene_path = source_paths["scene_metadata"]
    scene_data = _load_json(scene_path)
    if scene_data is None:
        fallback = source_paths["scene_metadata_fallback"]
        scene_data = _load_json(fallback)
        if scene_data is not None:
            scene_path = fallback
        else:
            warnings.append("scene_metadata: missing or unreadable (checked Metadata and SceneMetadata)")
    loaded["scene_metadata"] = (
        _normalize_legacy_aliases(scene_data, schema) if scene_data else None
    )
    provenance["scene_metadata"] = _build_provenance("scene_metadata", scene_path, loaded["scene_metadata"])

    for source_key in SOURCE_ORDER:
        if source_key == "scene_metadata":
            continue
        path = source_paths[source_key]
        data = _load_json(path)
        if data is None:
            warnings.append(f"{source_key}: missing or unreadable at {path}")
        loaded[source_key] = _normalize_legacy_aliases(data, schema) if data else None
        provenance[source_key] = _build_provenance(source_key, path, loaded[source_key])
        warnings.extend(_validate_fragment(loaded[source_key], source_key, schema))

    scene_section = _map_scene(loaded["scene_metadata"], schema, warnings)
    assets_section = _map_assets(loaded["scene_metadata"], schema, warnings)
    materials_section = _map_materials(loaded["material_previews"], schema, warnings)
    renders_section = _map_renders(loaded["renders_manifest"], schema, warnings)
    pcg_section = _map_pcg(loaded["pcg_build"], schema, warnings)
    stats_section = _map_stats(loaded["stats_manifest"], schema, warnings)
    genome_section = _map_genome(loaded.get("genome_axis"), warnings)
    heatmap_section = _map_heatmap(loaded.get("pcg_heatmap"), warnings)

    metadata_section = {
        "schema_version": schema.get("version", "1.0"),
        "aggregated_at": datetime.now(timezone.utc).isoformat(),
        "aggregated_by": "portfolio_aggregator.py",
        "sources": provenance,
        "validation_warnings": warnings,
    }

    package = {
        "scene": scene_section,
        "assets": assets_section,
        "materials": materials_section,
        "renders": renders_section,
        "pcg": pcg_section,
        "stats": stats_section,
        "genome": genome_section,
        "pcg_heatmap": heatmap_section,
        "metadata": metadata_section,
    }

    _validate_package(package, schema, warnings)
    package["metadata"]["validation_warnings"] = warnings
    package = _ensure_package_shape(package, schema)
    package["metadata"]["validation_warnings"] = warnings
    return package


def _fallback_package(error: str) -> dict:
    schema = _load_schema()
    warnings = [f"aggregate: recovered with fallback package ({error})"]
    package = {
        "scene": _map_scene(None, schema, warnings),
        "assets": [],
        "materials": [],
        "renders": _map_renders(None, schema, warnings),
        "pcg": _map_pcg(None, schema, warnings),
        "stats": _map_stats(None, schema, warnings),
        "metadata": {
            "schema_version": schema.get("version", "1.0"),
            "aggregated_at": datetime.now(timezone.utc).isoformat(),
            "aggregated_by": "portfolio_aggregator.py",
            "sources": {},
            "validation_warnings": warnings,
            "fallback": True,
        },
    }
    return _ensure_package_shape(package, schema)


def ensure_package_written(*, out_path: Path | None = None) -> tuple[dict, Path]:
    """Aggregate fragment JSON and always write portfolio_package.json."""
    try:
        package = aggregate()
    except Exception as exc:
        _log_warning(f"aggregate failed ({exc}), writing fallback package")
        package = _fallback_package(str(exc))

    try:
        written = write_package(package, out_path=out_path)
    except OSError as exc:
        _log_warning(f"write failed ({exc}), retrying fallback package")
        package = _fallback_package(f"write error: {exc}")
        written = write_package(package, out_path=out_path)
    return package, written


def main() -> int:
    try:
        package, out_path = ensure_package_written()
    except OSError as exc:
        print(f"AGGREGATE_FAILED: could not write package: {exc}")
        return 1

    schema = _load_schema()
    warnings = package.get("metadata", {}).get("validation_warnings", [])
    for issue in warnings:
        _log_warning(issue)
    sections_ok = _sections_ok(package, schema)
    print(f"PORTFOLIO_PACKAGE sections_ok={sections_ok} warnings={len(warnings)} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
