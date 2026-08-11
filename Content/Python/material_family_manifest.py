"""Build a disk-only material family manifest for portfolio/package tooling.

This script intentionally does not import Unreal. It reads curated Python data
tables with AST, emits a generic material-family contract, and also writes a
`previews_manifest.json` shape that the existing portfolio aggregator already
consumes for `materials[]`.

Run:
  python Content/Python/material_family_manifest.py
"""
from __future__ import annotations

import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = Path(__file__).resolve().parent
PORTFOLIO_ROOT = PROJECT_ROOT / "Saved" / "Portfolio"
MANIFEST_DIR = PORTFOLIO_ROOT / "Materials"
PREVIEW_DIR = PORTFOLIO_ROOT / "MaterialPreviews"
MANIFEST_PATH = MANIFEST_DIR / "material_family_manifest.json"
PREVIEWS_PATH = PREVIEW_DIR / "previews_manifest.json"

MATERIALS_ROOT = "/Game/EnvSandbox/Materials"
UNIVERSAL_MASTER = f"{MATERIALS_ROOT}/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal"
LANDSCAPE_MASTER = (
    f"{MATERIALS_ROOT}/Masters/M_Master_Toon_Landscape_HeightBlend."
    "M_Master_Toon_Landscape_HeightBlend"
)
WATER_MASTER = f"{MATERIALS_ROOT}/Masters/M_Water_Master_Grand_v6.M_Water_Master_Grand_v6"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _literal_assignment(module_path: Path, name: str) -> Any:
    tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == name and node.value is not None:
                return ast.literal_eval(node.value)
    return []


def _safe_list(module_name: str, assignment: str) -> list[dict[str, Any]]:
    path = PYTHON_DIR / module_name
    if not path.is_file():
        return []
    try:
        data = _literal_assignment(path, assignment)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def _asset_path(folder: str, name: str) -> str:
    return f"{folder}/{name}.{name}"


def _family_from_name(name: str) -> str:
    if name.startswith("MI_Show_"):
        return "Showcase"
    if name.startswith("MI_ZenTrim_") or name.startswith("MI_Trimsheet_"):
        return "Trimsheet"
    if name.startswith("MI_Zen_"):
        return "Zen"
    if name.startswith("MI_Baroque_"):
        return "Baroque"
    if name.startswith("MI_Landscape_"):
        return "Landscape"
    if name.startswith("MI_GrandWater_"):
        return "Water"
    if name.startswith("MI_Sakura_"):
        return "Sakura"
    return "Universal"


def _material_type(shader_family: str) -> str:
    if shader_family == "Landscape":
        return "landscape"
    if shader_family == "Water":
        return "water"
    if shader_family == "Trimsheet":
        return "trimsheet"
    return "surface"


def _parent_master(shader_family: str) -> str:
    if shader_family == "Landscape":
        return LANDSCAPE_MASTER
    if shader_family == "Water":
        return WATER_MASTER
    return UNIVERSAL_MASTER


def _parameter_groups(spec: dict[str, Any], shader_family: str) -> list[str]:
    groups = {shader_family}
    scalars = spec.get("scalars") if isinstance(spec.get("scalars"), dict) else {}
    textures = spec.get("textures") if isinstance(spec.get("textures"), dict) else {}
    switches = spec.get("switches") if isinstance(spec.get("switches"), dict) else {}
    for key in list(scalars) + list(textures) + list(switches):
        text = str(key).lower()
        if "parallax" in text or "normal" in text or "triplanar" in text:
            groups.add("Parallax")
            groups.add("Triplanar / Temporal")
        if "nikki" in text or "dream" in text or "rim" in text or "sparkle" in text:
            groups.add("Nikki")
        if "celestial" in text or "constellation" in text or "star" in text:
            groups.add("Celestial")
        if "gild" in text or "gold" in text:
            groups.add("Gilding")
        if "motif" in text or "fairy" in text or "magical" in text:
            groups.add("FairyDust")
            groups.add("Magical")
        if "flower" in text:
            groups.add("FlowerShadow")
        if "wet" in text or "shore" in text or "water" in text:
            groups.add("World / Wetness")
        if "macro" in text or "moss" in text:
            groups.add("World / Macro")
        if "audio" in text:
            groups.add("Audio")
    return sorted(groups)


def _output_maps(spec: dict[str, Any], shader_family: str) -> list[str]:
    maps = ["base_color", "roughness", "emissive"]
    textures = spec.get("textures") if isinstance(spec.get("textures"), dict) else {}
    scalars = spec.get("scalars") if isinstance(spec.get("scalars"), dict) else {}
    keys = {str(k).lower() for k in list(textures) + list(scalars)}
    if any("normal" in key for key in keys) or shader_family in {"Showcase", "Trimsheet", "Landscape"}:
        maps.append("normal")
    if any("height" in key or "parallax" in key for key in keys):
        maps.append("height")
    if any("metal" in key for key in keys):
        maps.append("metallic")
    if shader_family == "Water":
        maps.extend(["opacity", "refraction", "world_position_offset"])
    return sorted(set(maps))


def _entry(spec: dict[str, Any], *, source_module: str, fallback_folder: str | None = None) -> dict[str, Any]:
    name = str(spec.get("name") or "UNKNOWN")
    family = _family_from_name(name)
    folder = str(spec.get("folder") or fallback_folder or f"{MATERIALS_ROOT}/Instances/Showcase")
    return {
        "material_name": name,
        "asset_path": _asset_path(folder, name),
        "parent_master": _parent_master(family),
        "shader_family": family,
        "material_type": _material_type(family),
        "parameter_groups": _parameter_groups(spec, family),
        "output_maps": _output_maps(spec, family),
        "preview_path": None,
        "status": "metadata_only",
        "purpose": str(spec.get("purpose") or ""),
        "profile": spec.get("profile"),
        "key_params": spec.get("key_params"),
        "source_module": source_module,
    }


def build_manifest() -> dict[str, Any]:
    entries: list[dict[str, Any]] = []

    starter = _safe_list("starter_instances.py", "STARTER_INSTANCES")
    for spec in starter:
        entries.append(
            _entry(
                spec,
                source_module="starter_instances.py",
                fallback_folder=f"{MATERIALS_ROOT}/Instances/Showcase",
            )
        )

    zen = _safe_list("zen_instances.py", "ZEN_INSTANCES")
    for spec in zen:
        entries.append(_entry(spec, source_module="zen_instances.py"))

    baroque = _safe_list("theme_instances.py", "BAROQUE_INSTANCES")
    for spec in baroque:
        entries.append(_entry(spec, source_module="theme_instances.py"))

    # De-dupe by material name while preserving first source-table ordering.
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in entries:
        name = item["material_name"]
        if name in seen:
            continue
        seen.add(name)
        deduped.append(item)

    families: dict[str, int] = {}
    for item in deduped:
        families[item["shader_family"]] = families.get(item["shader_family"], 0) + 1

    return {
        "generated_at": _now_iso(),
        "generated_by": "material_family_manifest.py",
        "ok": True,
        "schema_version": "1.0",
        "project_root": PROJECT_ROOT.as_posix(),
        "source_modules": [
            "starter_instances.py",
            "zen_instances.py",
            "theme_instances.py",
        ],
        "counts": {
            "materials": len(deduped),
            "families": families,
        },
        "materials": deduped,
    }


def build_previews_manifest(material_manifest: dict[str, Any]) -> dict[str, Any]:
    materials: dict[str, dict[str, Any]] = {}
    for item in material_manifest.get("materials", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("material_name") or "")
        if not name:
            continue
        materials[name] = {
            "path": item.get("asset_path"),
            "label": name,
            "thumbnail": item.get("preview_path"),
            "material_type": item.get("material_type"),
            "shader_family": item.get("shader_family"),
            "output_maps": item.get("output_maps") or [],
            "parent_master": item.get("parent_master"),
            "status": item.get("status"),
            "purpose": item.get("purpose"),
            "source_module": item.get("source_module"),
        }
    return {
        "generated_at": _now_iso(),
        "generated_by": "material_family_manifest.py",
        "ok": True,
        "count": len(materials),
        "materials": materials,
    }


def write_outputs() -> tuple[dict[str, Any], Path, Path]:
    manifest = build_manifest()
    previews = build_previews_manifest(manifest)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    PREVIEWS_PATH.write_text(json.dumps(previews, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return manifest, MANIFEST_PATH, PREVIEWS_PATH


def main() -> int:
    manifest, manifest_path, previews_path = write_outputs()
    counts = manifest.get("counts", {})
    print(
        "MATERIAL_FAMILY_MANIFEST "
        f"materials={counts.get('materials')} "
        f"families={counts.get('families')} "
        f"-> {manifest_path} ; {previews_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
