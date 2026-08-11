"""Inventory project material instances and flag unsafe standards violations.

Run inside UE 5.8 with ``unreal`` available. This is read-only apart from the
JSON report; it does not reparent, rename, or rewrite material instances.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REPORT = PROJECT / "Saved" / "Audit" / "material_instance_standards_audit_v1.json"
ROOTS = ("/Game/EnvSandbox/", "/Game/Melodia/")


def _family(path: str) -> str:
    low = path.lower()
    for marker, name in (
        ("/melodia/", "melodia"), ("/_scratch/", "scratch"), ("/sdf/", "sdf"),
        ("/water/", "water"), ("/sakura/", "sakura"), ("/zen/", "zen"),
        ("/impressionist/", "impressionist"), ("/showcase", "showcase"),
        ("/baroque/", "baroque"), ("/nikkihero/", "nikki"),
        ("/environment/", "environment"),
    ):
        if marker in low:
            return name
    return "unknown"


def run() -> dict:
    import unreal

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class(
        unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant"), True
    )
    rows: list[dict] = []
    for asset_data in assets:
        path = str(asset_data.package_name)
        if not path.startswith(ROOTS):
            continue
        if "/Materials/_Archive/" in path:
            continue
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            continue
        chain: list[str] = []
        current = instance
        seen: set[str] = set()
        cycle = False
        while isinstance(current, unreal.MaterialInstanceConstant) and len(chain) < 12:
            current_path = current.get_path_name().split(".")[0]
            if current_path in seen:
                cycle = True
                break
            seen.add(current_path)
            chain.append(current_path)
            current = current.get_editor_property("parent")
        terminal = current.get_path_name().split(".")[0] if current else None
        textures: list[dict] = []
        missing_textures: list[str] = []
        for value in instance.get_editor_property("texture_parameter_values") or []:
            info = value.get_editor_property("parameter_info")
            texture = value.get_editor_property("parameter_value")
            texture_path = texture.get_path_name().split(".")[0] if texture else None
            textures.append({"name": str(info.get_editor_property("name")), "path": texture_path})
            if texture_path and not unreal.EditorAssetLibrary.does_asset_exist(texture_path):
                missing_textures.append(texture_path)
        rows.append({
            "path": path,
            "family": _family(path),
            "chain_depth": max(0, len(chain) - 1),
            "terminal_parent": terminal,
            "cycle": cycle,
            "scalar_count": len(instance.get_editor_property("scalar_parameter_values") or []),
            "vector_count": len(instance.get_editor_property("vector_parameter_values") or []),
            "texture_count": len(textures),
            "missing_textures": missing_textures,
            "textures": textures,
        })

    families: dict[str, int] = {}
    for row in rows:
        families[row["family"]] = families.get(row["family"], 0) + 1
    report = {
        "schema": "material_instance_standards_audit_v1",
        "engine": "UE5.8",
        "instance_count": len(rows),
        "families": families,
        "missing_parent_count": sum(not row["terminal_parent"] for row in rows),
        "missing_texture_binding_count": sum(bool(row["missing_textures"]) for row in rows),
        "cycle_count": sum(row["cycle"] for row in rows),
        "instances": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("Material instance standards audit: " + json.dumps({
        key: report[key] for key in (
            "instance_count", "families", "missing_parent_count",
            "missing_texture_binding_count", "cycle_count"
        )
    }))
    return report


if __name__ == "__main__":
    run()
