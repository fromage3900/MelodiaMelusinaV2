"""Convert the Unreal portfolio package into website-ready config JSON.

Run from project root:
  python Content/Python/package_to_website_handoff.py

Default input:
  Saved/Portfolio/portfolio_package.json

Default output:
  _github_deploy/generated/*_config.json

The adapter is intentionally disk-only so it can run in CI, a normal shell, or
inside Unreal after `portfolio_aggregator.py` writes the package.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = PROJECT_ROOT / "Saved" / "Portfolio" / "portfolio_package.json"
DEPLOY_GENERATED = PROJECT_ROOT / "_github_deploy" / "generated"
DEPLOY_CONFIG = DEPLOY_GENERATED / "deployment_config.json"
DEPLOY_MANIFEST = DEPLOY_GENERATED / "deployment_manifest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _format_int(value: Any, fallback: str = "Unknown") -> str:
    try:
        if value is None:
            return fallback
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value) if value not in (None, "") else fallback


def _compact_count(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return _format_int(value)
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M".replace(".0M", "M")
    if number >= 1_000:
        return f"{number / 1_000:.0f}K"
    return str(number)


def _engine_label(engine: Any) -> str:
    text = str(engine or "Unreal Engine")
    if text.startswith("5."):
        return f"Unreal Engine {text.split('-')[0]}"
    if "UE5" in text or "Unreal" in text:
        return text.split("+++")[0]
    return text


def _date_label(package: dict[str, Any]) -> str:
    scene = package.get("scene") if isinstance(package.get("scene"), dict) else {}
    metadata = package.get("metadata") if isinstance(package.get("metadata"), dict) else {}
    value = scene.get("timestamp") or metadata.get("aggregated_at") or metadata.get("generated_at")
    if not value:
        return _now_iso()[:7]
    return str(value)[:7]


def _family_counts(materials: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for material in materials:
        family = str(material.get("shader_family") or "Uncategorized")
        counts[family] = counts.get(family, 0) + 1
    return dict(sorted(counts.items()))


def _featured_materials(materials: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    ranked = sorted(
        materials,
        key=lambda item: (
            str(item.get("status") or "") != "metadata_only",
            str(item.get("shader_family") or ""),
            str(item.get("material_name") or ""),
        ),
    )
    featured: list[dict[str, Any]] = []
    for item in ranked[:limit]:
        featured.append(
            {
                "name": item.get("material_name") or item.get("label"),
                "family": item.get("shader_family"),
                "type": item.get("material_type"),
                "purpose": item.get("purpose"),
                "parent_master": item.get("parent_master"),
                "output_maps": item.get("output_maps") or [],
                "path": item.get("path") or item.get("asset_path"),
                "status": item.get("status"),
            }
        )
    return featured


def _render_items(package: dict[str, Any]) -> list[dict[str, Any]]:
    renders = package.get("renders") if isinstance(package.get("renders"), dict) else {}
    items: list[dict[str, Any]] = []
    for group, group_items in sorted(renders.items()):
        if not isinstance(group_items, list):
            continue
        for item in group_items:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "")
            items.append(
                {
                    "group": group,
                    "filename": item.get("filename") or (Path(path).name if path else None),
                    "path": path or None,
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "aspect_ratio": item.get("aspect_ratio"),
                    "plate_role": (item.get("presentation") or {}).get("plate_role")
                    if isinstance(item.get("presentation"), dict)
                    else None,
                }
            )
    return items


def _base_url(target_generated: Path) -> str:
    config = _read_json(target_generated / "deployment_config.json", {})
    github = config.get("github") if isinstance(config, dict) else {}
    return str(github.get("pages_base_url") or "https://fromage3900.github.io/my-site").rstrip("/")


def build_configs(package: dict[str, Any], target_generated: Path) -> dict[str, dict[str, Any]]:
    scene = package.get("scene") if isinstance(package.get("scene"), dict) else {}
    stats = package.get("stats") if isinstance(package.get("stats"), dict) else {}
    metadata = package.get("metadata") if isinstance(package.get("metadata"), dict) else {}
    materials = package.get("materials") if isinstance(package.get("materials"), list) else []
    assets = package.get("assets") if isinstance(package.get("assets"), list) else []
    pcg = package.get("pcg") if isinstance(package.get("pcg"), dict) else {}

    project_name = str(scene.get("scene_name") or "Unreal Portfolio Scene")
    engine = _engine_label(scene.get("engine"))
    material_count = len(materials)
    asset_count = len(assets)
    graph_count = len(pcg.get("graphs") or {}) if isinstance(pcg.get("graphs"), dict) else 0
    date_label = _date_label(package)
    family_counts = _family_counts(materials)
    render_items = _render_items(package)
    base_url = _base_url(target_generated)

    hero_config = {
        "theme": "dark",
        "contentTheme": "environment",
        "kicker": "3D Environment & Technical Art",
        "title": project_name,
        "sub": f"{engine} look-dev package with {material_count} materials and {graph_count} PCG graphs",
        "starCount": 70,
        "gstarCount": 7,
        "enableParallax": True,
        "parallaxStrength": 0.05,
        "performance": "highQuality",
    }

    passport_config = {
        "theme": "dark",
        "highlight": "environment",
        "project": project_name,
        "category": scene.get("environment_type") or "Environment",
        "version": "v1.0",
        "animations": True,
        "hoverEffects": True,
        "decorativeStars": True,
        "rows": [
            ["Triangles", _format_int(stats.get("triangle_count"))],
            ["Draw Calls", _format_int(stats.get("draw_calls"))],
            ["Materials", _format_int(material_count)],
            ["Assets", _format_int(asset_count)],
            ["PCG Graphs", _format_int(graph_count)],
            ["Engine", engine],
            ["Date", date_label],
        ],
    }

    portfolio_config = {
        "generated_at": _now_iso(),
        "generated_by": "package_to_website_handoff.py",
        "source_package": str(PACKAGE_PATH),
        "project": {
            "name": project_name,
            "level_path": scene.get("level_path"),
            "category": scene.get("environment_type") or "Environment",
            "engine": engine,
        },
        "counts": {
            "assets": asset_count,
            "materials": material_count,
            "material_families": family_counts,
            "renders": len(render_items),
            "pcg_graphs": graph_count,
            "validation_warnings": len(metadata.get("validation_warnings") or []),
        },
        "stats": {
            "triangles": stats.get("triangle_count"),
            "triangles_label": _compact_count(stats.get("triangle_count")),
            "draw_calls": stats.get("draw_calls"),
            "unique_meshes": stats.get("unique_meshes"),
            "unique_materials": stats.get("unique_materials"),
        },
        "embeds": {
            "hero": f"{base_url}/generated/l-sakurapath-hero.html",
            "passport": f"{base_url}/generated/l-sakurapath-passport.html",
        },
    }

    materials_config = {
        "generated_at": _now_iso(),
        "generated_by": "package_to_website_handoff.py",
        "count": material_count,
        "families": family_counts,
        "featured": _featured_materials(materials),
    }

    renders_config = {
        "generated_at": _now_iso(),
        "generated_by": "package_to_website_handoff.py",
        "count": len(render_items),
        "renders": render_items,
    }

    stats_config = {
        "generated_at": _now_iso(),
        "generated_by": "package_to_website_handoff.py",
        "scene": project_name,
        "engine": engine,
        "stats": portfolio_config["stats"],
        "passport_rows": passport_config["rows"],
    }

    return {
        "hero_config.json": hero_config,
        "passport_config.json": passport_config,
        "portfolio_package_config.json": portfolio_config,
        "materials_config.json": materials_config,
        "renders_config.json": renders_config,
        "stats_config.json": stats_config,
    }


def update_deployment_manifest(
    target_generated: Path,
    package: dict[str, Any],
    written: dict[str, Path],
) -> Path:
    manifest_path = target_generated / "deployment_manifest.json"
    manifest = _read_json(manifest_path, {})
    if not isinstance(manifest, dict):
        manifest = {}

    scene = package.get("scene") if isinstance(package.get("scene"), dict) else {}
    stats = package.get("stats") if isinstance(package.get("stats"), dict) else {}
    materials = package.get("materials") if isinstance(package.get("materials"), list) else []
    base_url = _base_url(target_generated)

    manifest.setdefault("version", "2.0")
    manifest["generated_at"] = _now_iso()
    manifest["package_handoff"] = {
        "generated_at": _now_iso(),
        "source_package": str(PACKAGE_PATH),
        "configs": {
            path.name: f"{base_url}/generated/{path.name}"
            for path in sorted(written.values(), key=lambda item: item.name)
        },
        "scene": {
            "name": scene.get("scene_name"),
            "level_path": scene.get("level_path"),
            "engine": _engine_label(scene.get("engine")),
        },
        "stats": {
            "triangles": stats.get("triangle_count"),
            "draw_calls": stats.get("draw_calls"),
            "materials": len(materials),
        },
    }

    return _write_json(manifest_path, manifest)


def write_handoff(
    *,
    package_path: Path = PACKAGE_PATH,
    target_generated: Path = DEPLOY_GENERATED,
) -> dict[str, Any]:
    package = _read_json(package_path, None)
    if not isinstance(package, dict):
        raise FileNotFoundError(f"missing or unreadable portfolio package: {package_path}")

    target_generated.mkdir(parents=True, exist_ok=True)
    configs = build_configs(package, target_generated)
    written = {
        filename: _write_json(target_generated / filename, payload)
        for filename, payload in configs.items()
    }
    manifest_path = update_deployment_manifest(target_generated, package, written)

    return {
        "ok": True,
        "generated_at": _now_iso(),
        "generated_by": "package_to_website_handoff.py",
        "source_package": str(package_path),
        "target_generated": str(target_generated),
        "written": {name: str(path) for name, path in written.items()},
        "deployment_manifest": str(manifest_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=PACKAGE_PATH)
    parser.add_argument("--target-generated", type=Path, default=DEPLOY_GENERATED)
    args = parser.parse_args()

    report = write_handoff(package_path=args.package, target_generated=args.target_generated)
    print(
        "PACKAGE_TO_WEBSITE_HANDOFF "
        f"ok={report['ok']} "
        f"configs={len(report['written'])} "
        f"target={report['target_generated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
