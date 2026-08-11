"""Build full disk-only material family manifests for portfolio/package tooling.

This is the robust variant of `material_family_manifest.py`: it safely evaluates
the curated instance data tables without importing Unreal-only modules.

Run:
  python Content/Python/material_family_manifest_full.py
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

EVAL_ENV: dict[str, Any] = {
    "MATERIALS_ROOT": MATERIALS_ROOT,
    "MASTER": UNIVERSAL_MASTER,
    "SHOWCASE_DIR": f"{MATERIALS_ROOT}/Instances/Showcase",
    "ZEN_DIR": f"{MATERIALS_ROOT}/Instances/Environment/Zen",
    "BAROQUE_DIR": f"{MATERIALS_ROOT}/Instances/Environment/Baroque",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _eval_node(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(item, env) for item in node.elts)
    if isinstance(node, ast.List):
        return [_eval_node(item, env) for item in node.elts]
    if isinstance(node, ast.Dict):
        return {
            _eval_node(key, env): _eval_node(value, env)
            for key, value in zip(node.keys, node.values)
            if key is not None
        }
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"unsupported name: {node.id}")
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append(str(_eval_node(value.value, env)))
            else:
                raise ValueError(f"unsupported f-string node: {type(value).__name__}")
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _eval_node(node.left, env) + _eval_node(node.right, env)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand, env)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
        return _eval_node(node.operand, env)
    raise ValueError(f"unsupported node: {type(node).__name__}")


def _assignment(module_path: Path, name: str) -> Any:
    tree = ast.parse(module_path.read_text(encoding="utf-8-sig"), filename=str(module_path))
    env = dict(EVAL_ENV)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        env[target.id] = _eval_node(node.value, env)
                    except Exception:
                        pass
                    if target.id == name:
                        return _eval_node(node.value, env)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            try:
                env[node.target.id] = _eval_node(node.value, env)
            except Exception:
                pass
            if node.target.id == name:
                return _eval_node(node.value, env)
    return []


def _safe_list(module_name: str, assignment: str) -> list[dict[str, Any]]:
    path = PYTHON_DIR / module_name
    if not path.is_file():
        return []
    try:
        data = _assignment(path, assignment)
    except Exception as exc:
        return [{"name": f"UNREADABLE_{module_name}_{assignment}", "purpose": str(exc)}]
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
    return {
        "Landscape": "landscape",
        "Water": "water",
        "Trimsheet": "trimsheet",
    }.get(shader_family, "surface")


def _parent_master(shader_family: str) -> str:
    return {
        "Landscape": LANDSCAPE_MASTER,
        "Water": WATER_MASTER,
    }.get(shader_family, UNIVERSAL_MASTER)


def _parameter_groups(spec: dict[str, Any], shader_family: str) -> list[str]:
    groups = {shader_family}
    scalars = spec.get("scalars") if isinstance(spec.get("scalars"), dict) else {}
    textures = spec.get("textures") if isinstance(spec.get("textures"), dict) else {}
    switches = spec.get("switches") if isinstance(spec.get("switches"), dict) else {}
    for key in list(scalars) + list(textures) + list(switches):
        text = str(key).lower()
        if "parallax" in text or "normal" in text or "triplanar" in text:
            groups.update(["Parallax", "Triplanar / Temporal"])
        if "nikki" in text or "dream" in text or "rim" in text or "sparkle" in text:
            groups.add("Nikki")
        if "celestial" in text or "constellation" in text or "star" in text:
            groups.add("Celestial")
        if "gild" in text or "gold" in text:
            groups.add("Gilding")
        if "motif" in text or "fairy" in text or "magical" in text:
            groups.update(["FairyDust", "Magical"])
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
    specs: list[tuple[str, list[dict[str, Any]], str | None]] = [
        ("starter_instances.py", _safe_list("starter_instances.py", "STARTER_INSTANCES"), f"{MATERIALS_ROOT}/Instances/Showcase"),
        ("zen_instances.py", _safe_list("zen_instances.py", "ZEN_INSTANCES"), None),
        ("theme_instances.py", _safe_list("theme_instances.py", "BAROQUE_INSTANCES"), None),
    ]

    entries: list[dict[str, Any]] = []
    for source_module, items, fallback_folder in specs:
        for spec in items:
            entries.append(_entry(spec, source_module=source_module, fallback_folder=fallback_folder))

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
        "generated_by": "material_family_manifest_full.py",
        "ok": True,
        "schema_version": "1.0",
        "project_root": PROJECT_ROOT.as_posix(),
        "source_modules": [name for name, _, _ in specs],
        "counts": {"materials": len(deduped), "families": families},
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
        "generated_by": "material_family_manifest_full.py",
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
        "MATERIAL_FAMILY_MANIFEST_FULL "
        f"materials={counts.get('materials')} "
        f"families={counts.get('families')} "
        f"-> {manifest_path} ; {previews_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
