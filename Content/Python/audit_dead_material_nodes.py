"""Audit dead material function calls and broken texture refs (editor).

  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/audit_dead_material_nodes.py"

Output: Saved/Audit/dead_material_nodes.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "dead_material_nodes.json"
MATERIALS_ROOT = "/Game/EnvSandbox/Materials"

SAFE_MASTERS = [
    f"{MATERIALS_ROOT}/Masters/M_Master_Toon_Universal",
    f"{MATERIALS_ROOT}/Masters/M_Master_SDF_Toon",
    f"{MATERIALS_ROOT}/Masters/M_Master_Toon_Unified",
]

SAFE_FOLDERS = (
    f"{MATERIALS_ROOT}/Functions",
    f"{MATERIALS_ROOT}/PostProcess",
    f"{MATERIALS_ROOT}/Impressionist",
)


def _asset_base(asset) -> str | None:
    if not asset:
        return None
    return asset.get_path_name().split(".", 1)[0]


def _load_owner(path: str):
    import unreal

    try:
        asset = unreal.load_asset(path)
    except Exception:
        return None
    if isinstance(asset, (unreal.Material, unreal.MaterialFunction)):
        return asset
    return None


def _iter_owners(safe_only: bool = True):
    import unreal

    skipped: list[str] = []

    if safe_only:
        paths: list[str] = []
        for base in SAFE_MASTERS:
            stem = base.rsplit("/", 1)[-1]
            paths.append(f"{base}.{stem}")
        for folder in SAFE_FOLDERS:
            if not unreal.EditorAssetLibrary.does_directory_exist(folder):
                continue
            paths.extend(
                unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False)
            )
    else:
        paths = []
        for folder in (
            f"{MATERIALS_ROOT}/Masters",
            f"{MATERIALS_ROOT}/SDF",
            f"{MATERIALS_ROOT}/Impressionist",
            f"{MATERIALS_ROOT}/Functions",
            f"{MATERIALS_ROOT}/PostProcess",
        ):
            if not unreal.EditorAssetLibrary.does_directory_exist(folder):
                continue
            for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=True, include_folder=False):
                if "/M_SDF_" in path or "/Masters/M_SDF_" in path:
                    skipped.append(path)
                    continue
                paths.append(path)

    for path in paths:
        owner = _load_owner(path)
        if owner:
            yield path, owner
        else:
            skipped.append(path)

    if skipped:
        import unreal

        unreal.log_warning(
            f"[DeadNodeAudit] skipped {len(skipped)} unloadable assets "
            f"(run repair_crash_assets.py; use --full only in interactive editor)"
        )


def _expressions(owner) -> list:
    import unreal

    if isinstance(owner, unreal.Material):
        return list(unreal.MaterialEditingLibrary.get_material_expressions(owner) or [])
    if isinstance(owner, unreal.MaterialFunction):
        try:
            return list(unreal.MaterialEditingLibrary.get_material_function_expressions(owner) or [])
        except Exception:
            return []
    return []


def audit(recompile: bool = False, safe_only: bool = True) -> dict:
    import unreal

    dead_functions: list[dict] = []
    missing_textures: list[dict] = []
    compile_errors: list[dict] = []

    for path, owner in _iter_owners(safe_only=safe_only):
        label = path.split("/")[-1]
        for expr in _expressions(owner):
            if not expr:
                continue
            tname = type(expr).__name__
            if tname == "MaterialExpressionMaterialFunctionCall":
                mf = None
                try:
                    mf = expr.get_editor_property("material_function")
                except Exception:
                    pass
                mf_path = _asset_base(mf)
                if not mf_path or not unreal.EditorAssetLibrary.does_asset_exist(mf_path):
                    dead_functions.append({
                        "asset": path,
                        "label": label,
                        "missing_function": mf_path or "(null)",
                    })
            if "Texture" in tname:
                tex = None
                for prop in ("texture", "Texture"):
                    try:
                        tex = expr.get_editor_property(prop)
                        if tex:
                            break
                    except Exception:
                        continue
                if tex:
                    tp = _asset_base(tex)
                    if tp and not unreal.EditorAssetLibrary.does_asset_exist(tp):
                        pname = ""
                        try:
                            pname = expr.get_editor_property("parameter_name") or ""
                        except Exception:
                            pass
                        missing_textures.append({
                            "asset": path,
                            "param": pname,
                            "missing_texture": tp,
                        })

        if recompile and isinstance(owner, unreal.Material):
            try:
                unreal.MaterialEditingLibrary.recompile_material(owner)
            except Exception as exc:
                compile_errors.append({"asset": path, "error": str(exc)})

    return {
        "mode": "safe" if safe_only else "full",
        "dead_function_calls": dead_functions,
        "missing_texture_refs": missing_textures,
        "compile_errors": compile_errors,
        "dead_function_count": len(dead_functions),
        "missing_texture_count": len(missing_textures),
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
    except ImportError:
        print("Requires Unreal Editor Python")
        return 1

    recompile = "--recompile" in sys.argv
    safe_only = "--full" not in sys.argv
    result = audit(recompile=recompile, safe_only=safe_only)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "dead_functions": result["dead_function_count"],
        "missing_textures": result["missing_texture_count"],
        "report": str(REPORT),
    }, indent=2))
    return 0 if result["dead_function_count"] == 0 and result["missing_texture_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
