"""Materials-only audit report (no website integration).

Reads:
  - Saved/Portfolio/portfolio_package.json
  - Saved/Portfolio/MaterialPreviews/previews_manifest.json
  - (optional) Saved/Audit/material_library_audit.json

Writes:
  - Saved/Audit/material_instance_audit.json

Goal: Identify the current material bottlenecks:
  - missing thumbnails
  - inconsistent classification fields
  - parent master gaps
  - output-map coverage per family
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_PACKAGE = PROJECT_ROOT / "Saved" / "Portfolio" / "portfolio_package.json"
PREVIEWS_MANIFEST = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialPreviews" / "previews_manifest.json"
LIBRARY_AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "material_library_audit.json"
OUT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "material_instance_audit.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


@dataclass(frozen=True)
class MaterialRow:
    name: str
    shader_family: str
    material_type: str
    parent_master: str | None
    path: str | None
    output_maps: list[str]
    status: str


def _normalize_preview_materials(previews: dict[str, Any]) -> dict[str, dict[str, Any]]:
    materials = previews.get("materials")
    if isinstance(materials, dict):
        return materials
    return {}

def _exists(path_value: Any) -> bool:
    if not path_value:
        return False
    try:
        path = Path(str(path_value))
    except Exception:
        return False
    return path.is_file()


def build_report() -> dict[str, Any]:
    package = _as_dict(_read_json(PORTFOLIO_PACKAGE))
    previews = _as_dict(_read_json(PREVIEWS_MANIFEST))
    library_audit = _as_dict(_read_json(LIBRARY_AUDIT))

    mats = _as_list(package.get("materials"))
    preview_mats = _normalize_preview_materials(previews)

    rows: list[MaterialRow] = []
    for item in mats:
        if not isinstance(item, dict):
            continue
        name = str(item.get("material_name") or item.get("label") or "").strip()
        if not name:
            continue
        rows.append(
            MaterialRow(
                name=name,
                shader_family=str(item.get("shader_family") or "Uncategorized"),
                material_type=str(item.get("material_type") or "unknown"),
                parent_master=str(item.get("parent_master")) if item.get("parent_master") else None,
                path=str(item.get("path") or item.get("asset_path")) if (item.get("path") or item.get("asset_path")) else None,
                output_maps=[str(x) for x in _as_list(item.get("output_maps")) if x],
                status=str(item.get("status") or "unknown"),
            )
        )

    family_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    output_map_counts: dict[str, int] = {}
    output_maps_by_family: dict[str, dict[str, int]] = {}

    missing_thumbnail: list[str] = []
    missing_parent_master: list[str] = []
    unknown_material_type: list[str] = []
    missing_path: list[str] = []

    for row in rows:
        family_counts[row.shader_family] = family_counts.get(row.shader_family, 0) + 1
        type_counts[row.material_type] = type_counts.get(row.material_type, 0) + 1
        status_counts[row.status] = status_counts.get(row.status, 0) + 1

        if not row.parent_master:
            missing_parent_master.append(row.name)
        if not row.path:
            missing_path.append(row.name)
        if row.material_type in {"unknown", "surface"}:
            # surface is valid, but we flag it because the export currently does not distinguish master vs instance.
            unknown_material_type.append(row.name)

        preview = preview_mats.get(row.name) if isinstance(preview_mats.get(row.name), dict) else {}
        if not preview or not preview.get("thumbnail"):
            missing_thumbnail.append(row.name)

        for om in row.output_maps:
            output_map_counts[om] = output_map_counts.get(om, 0) + 1
            fam_maps = output_maps_by_family.setdefault(row.shader_family, {})
            fam_maps[om] = fam_maps.get(om, 0) + 1

    missing_texture_refs = []
    try:
        missing_texture_refs = _as_list(_as_dict(library_audit).get("missing_texture_refs"))
    except Exception:
        missing_texture_refs = []

    # Thumbnail capture health (disk evidence)
    thumb_entries = [
        (name, (preview_mats.get(name) if isinstance(preview_mats.get(name), dict) else {}))
        for name in sorted(preview_mats.keys())
    ]
    thumb_declared = [
        {"material": name, "thumbnail": item.get("thumbnail")}
        for name, item in thumb_entries
        if item.get("thumbnail")
    ]
    thumb_declared_count = len(thumb_declared)
    thumb_existing = [entry for entry in thumb_declared if _exists(entry["thumbnail"])]
    thumb_existing_count = len(thumb_existing)
    thumb_missing_files = [
        entry for entry in thumb_declared if not _exists(entry["thumbnail"])
    ]
    thumb_missing_files_count = len(thumb_missing_files)

    thumb_dir = PREVIEWS_MANIFEST.parent
    thumb_files = sorted(thumb_dir.glob("thumb_*.png")) if thumb_dir.is_dir() else []
    thumb_files_count = len(thumb_files)

    return {
        "generated_at": _now_iso(),
        "generated_by": "material_instance_audit.py",
        "inputs": {
            "portfolio_package": str(PORTFOLIO_PACKAGE),
            "previews_manifest": str(PREVIEWS_MANIFEST),
            "material_library_audit": str(LIBRARY_AUDIT) if LIBRARY_AUDIT.is_file() else None,
        },
        "thumbnail_capture_health": {
            "preview_manifest_generated_by": previews.get("generated_by"),
            "preview_manifest_generated_at": previews.get("generated_at"),
            "thumbnail_entries_total": len(thumb_entries),
            "thumbnails_declared": thumb_declared_count,
            "thumbnails_existing": thumb_existing_count,
            "thumbnails_missing_files": thumb_missing_files_count,
            "thumbnail_files_on_disk": thumb_files_count,
            "example_missing_files": thumb_missing_files[:10],
        },
        "counts": {
            "materials_total": len(rows),
            "families": family_counts,
            "material_types": type_counts,
            "statuses": status_counts,
            "missing_thumbnail": len(missing_thumbnail),
            "missing_parent_master": len(missing_parent_master),
            "missing_path": len(missing_path),
        },
        "output_maps": {
            "totals": dict(sorted(output_map_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
            "by_family": {
                fam: dict(sorted(m.items(), key=lambda kv: (-kv[1], kv[0])))
                for fam, m in sorted(output_maps_by_family.items(), key=lambda kv: kv[0])
            },
        },
        "issues": {
            "missing_thumbnail": sorted(set(missing_thumbnail)),
            "missing_parent_master": sorted(set(missing_parent_master)),
            "missing_path": sorted(set(missing_path)),
            "coarse_material_type": sorted(set(unknown_material_type)),
            "missing_texture_refs": missing_texture_refs,
            "thumbnail_missing_files": thumb_missing_files,
        },
    }


def main() -> int:
    report = build_report()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        "MATERIAL_INSTANCE_AUDIT "
        f"materials={report['counts']['materials_total']} "
        f"missing_thumbs={report['counts']['missing_thumbnail']} "
        f"-> {OUT_PATH}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

