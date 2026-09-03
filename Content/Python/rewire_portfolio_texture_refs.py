"""Rewire _PROJECT texture paths to portfolio SDF/Textures copies (editor-safe).

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript=".../rewire_portfolio_texture_refs.py"
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_texture_rewire.json"
MATERIALS_ROOT = "/Game/EnvSandbox/Materials"

TEXTURE_REPLACEMENTS: dict[str, str] = {
    "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_1_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_1_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_3_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_3_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_5_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_5_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_6_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_6_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_7_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_7_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Marble/Marble_9_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Marble/Marble_9_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Perlin/Perlin_1_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Perlin/Perlin_1_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Voronoi/Voronoi_2_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Voronoi/Voronoi_2_-_512x512",
    "/Game/_PROJECT/04_Materials/Textures/Voronoi/Voronoi_11_-_512x512": "/Game/EnvSandbox/Materials/SDF/Textures/Voronoi/Voronoi_11_-_512x512",
}


def _asset_base_path(asset) -> str | None:
    if not asset:
        return None
    return asset.get_path_name().split(".", 1)[0]


def _iter_material_assets():
    import unreal

    for folder in (
        f"{MATERIALS_ROOT}/Masters",
        f"{MATERIALS_ROOT}/SDF",
        f"{MATERIALS_ROOT}/Impressionist",
        f"{MATERIALS_ROOT}/Instances",
    ):
        if not unreal.EditorAssetLibrary.does_directory_exist(folder):
            continue
        for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
            if not path.endswith((".M_", ".MI_", ".MF_")) and "/M_" not in path and "/MI_" not in path:
                continue
            try:
                asset = unreal.load_asset(path)
            except Exception:
                yield path, None
                continue
            if isinstance(asset, (unreal.Material, unreal.MaterialInstanceConstant, unreal.MaterialFunction)):
                yield path, asset


def _get_expressions(owner) -> list:
    import unreal

    if isinstance(owner, unreal.Material):
        return list(unreal.MaterialEditingLibrary.get_material_expressions(owner))
    if isinstance(owner, unreal.MaterialFunction):
        try:
            return list(unreal.MaterialEditingLibrary.get_material_function_expressions(owner))
        except Exception:
            return []
    return []


def _rewire_owner(owner, label: str, report: dict) -> int:
    import unreal

    fixed = 0
    for expr in _get_expressions(owner):
        if not expr:
            continue
        if "Texture" not in type(expr).__name__:
            continue
        tex = None
        for prop in ("texture", "Texture"):
            try:
                tex = expr.get_editor_property(prop)
                if tex:
                    break
            except Exception:
                continue
        if not tex:
            continue
        current = _asset_base_path(tex)
        if not current or current not in TEXTURE_REPLACEMENTS:
            continue
        new_path = TEXTURE_REPLACEMENTS[current]
        new_tex = unreal.load_asset(new_path)
        if not new_tex:
            report["errors"].append(f"Missing portfolio texture: {new_path}")
            continue
        for prop in ("texture", "Texture"):
            try:
                expr.set_editor_property(prop, new_tex)
                fixed += 1
                report["changes"].append({"asset": label, "from": current, "to": new_path})
                break
            except Exception:
                continue
    return fixed


def _save_owner(owner, label: str) -> None:
    import unreal

    unreal.EditorAssetLibrary.save_loaded_asset(owner, only_if_is_dirty=False)
    if isinstance(owner, unreal.Material):
        unreal.MaterialEditingLibrary.recompile_material(owner)
    elif isinstance(owner, unreal.MaterialFunction):
        owner.post_edit_change()


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        print("rewire_portfolio_texture_refs.py requires Unreal Editor Python")
        return 1

    report: dict = {"changes": [], "errors": [], "assets_touched": 0, "textures_rewired": 0}

    for path, asset in _iter_material_assets():
        if asset is None:
            report["errors"].append(f"Failed to load: {path}")
            continue
        if isinstance(asset, unreal.MaterialInstanceConstant):
            continue
        try:
            count = _rewire_owner(asset, path, report)
        except Exception as exc:
            report["errors"].append(f"{path}: {exc}")
            continue
        if count:
            _save_owner(asset, path)
            report["assets_touched"] += 1
            report["textures_rewired"] += count

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
