"""Review + tune portfolio masters: textures, graph health, compile (editor-safe).

  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/review_portfolio_masters.py"

Shell:
  python Content/Python/review_portfolio_masters.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "master_review.json"
LOOP_REPORT = PROJECT_ROOT / "Saved" / "Audit" / "master_texture_loop.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

SAFE_MASTERS = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_SDF_Toon",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Unified",
]


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _param_name(expr) -> str | None:
    for prop in ("parameter_name", "ParameterName"):
        try:
            raw = expr.get_editor_property(prop)
            if raw is not None:
                return str(raw)
        except Exception:
            continue
    return None


def _has_front_material(material) -> bool:
    import unreal

    for expr in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if expr and "SubstrateToonBSDF" in type(expr).__name__:
            return True
    try:
        for out in material.get_editor_property("material_outputs") or []:
            if out and str(out).lower().find("front") >= 0:
                return True
    except Exception:
        pass
    return False


def _dead_function_calls(material, path: str) -> list[dict]:
    import unreal

    dead: list[dict] = []
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(material) or []:
        if not expr or "MaterialFunctionCall" not in type(expr).__name__:
            continue
        mf = None
        try:
            mf = expr.get_editor_property("material_function")
        except Exception:
            pass
        mf_base = mf.get_path_name().split(".", 1)[0] if mf else None
        if not mf_base or not unreal.EditorAssetLibrary.does_asset_exist(mf_base):
            dead.append({"asset": path, "missing_function": mf_base or "(null)"})
    return dead


def _unwired_texture_slots(material, path: str) -> list[str]:
    import unreal
    import material_lib as lib

    missing: list[str] = []
    me = unreal.MaterialEditingLibrary
    if hasattr(me, "get_texture_parameter_names"):
        for raw in me.get_texture_parameter_names(material) or []:
            pname = str(raw)
            tex = None
            if hasattr(me, "get_material_default_texture_parameter_value"):
                try:
                    tex = me.get_material_default_texture_parameter_value(material, raw)
                except Exception:
                    pass
            if lib.is_placeholder_texture(tex) or lib.is_banned_texture(tex):
                missing.append(pname)
        return missing

    for expr, _owner in lib.iter_texture_parameter_expressions(material):
        pname = _param_name(expr)
        if not pname:
            continue
        tex = None
        for prop in ("texture", "Texture"):
            try:
                tex = expr.get_editor_property(prop)
                if tex:
                    break
            except Exception:
                continue
        if not tex or lib.is_placeholder_texture(tex) or lib.is_banned_texture(tex):
            missing.append(pname)
    return missing


def _review_master(path: str, *, read_only: bool = False) -> dict:
    import unreal
    import material_lib as lib
    import portfolio_texture_catalog as catalog

    base = path
    full = f"{base}.{base.rsplit('/', 1)[-1]}"
    entry: dict = {"path": path, "exists": False}
    if not unreal.EditorAssetLibrary.does_asset_exist(base):
        return entry

    mat = unreal.load_asset(full)
    if not mat:
        return entry

    entry["exists"] = True
    exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(mat) or [])
    entry["expression_count"] = len(exprs)
    entry["substrate_toon"] = _has_front_material(mat)
    entry["dead_functions"] = _dead_function_calls(mat, path)
    entry["unwired_textures_before"] = _unwired_texture_slots(mat, path)
    entry["texture_parameter_names"] = lib.texture_parameter_names(mat)

    if read_only:
        entry["texture_violations"] = catalog.scan_master_texture_violations(mat)
        entry["unwired_textures_after"] = entry["unwired_textures_before"]
        entry["banned_textures_after"] = entry["texture_violations"].get("banned", [])
        entry["read_only"] = True
        return entry

    wired = catalog.apply_master_defaults(mat, path, force=True)
    entry["master_textures_wired"] = wired
    entry["texture_violations"] = catalog.scan_master_texture_violations(mat)
    entry["unwired_textures_after"] = _unwired_texture_slots(mat, path)
    entry["banned_textures_after"] = entry["texture_violations"].get("banned", [])

    try:
        unreal.MaterialEditingLibrary.recompile_material(mat)
        entry["compile"] = "ok"
    except Exception as exc:
        entry["compile"] = f"error: {exc}"

    lib.save_package(mat)
    return entry


def _run_in_ue() -> int:
    import unreal
    import portfolio_texture_catalog as catalog

    read_only = os.environ.get("BS_AAA_READ_ONLY", "").lower() in ("1", "true", "yes")
    unreal.log("=== PORTFOLIO MASTER REVIEW ===")

    if not read_only:
        import apply_compositing_texture_defaults as comp

        comp._run_in_ue()

    masters: dict = {}
    for path in SAFE_MASTERS:
        unreal.log(f"[MasterReview] auditing {path}")
        masters[path] = _review_master(path, read_only=read_only)

    dead_total = sum(len(m.get("dead_functions", [])) for m in masters.values())
    unwired_after = sum(len(m.get("unwired_textures_after", [])) for m in masters.values())
    banned_after = sum(len(m.get("banned_textures_after", [])) for m in masters.values())
    wrong_role = sum(len(m.get("texture_violations", {}).get("wrong_role", [])) for m in masters.values())

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "masters": masters,
        "summary": {
            "dead_function_calls": dead_total,
            "unwired_texture_slots": unwired_after,
            "banned_texture_slots": banned_after,
            "unwired_texture_count": unwired_after,
            "banned_texture_count": banned_after,
            "wrong_role_orm_slots": wrong_role,
            "all_substrate_toon": all(m.get("substrate_toon") for m in masters.values() if m.get("exists")),
            "clean": banned_after == 0 and unwired_after == 0 and dead_total == 0,
            "read_only": read_only,
        },
    }

    LOOP_REPORT.parent.mkdir(parents=True, exist_ok=True)
    LOOP_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Dead-node audit: safe masters + Functions only (skip bulk SDF copies)
    dead_functions: list[dict] = []
    missing_textures: list[dict] = []
    import audit_dead_material_nodes as dead_mod

    for path in SAFE_MASTERS:
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        try:
            owner = unreal.load_asset(f"{path}.{path.rsplit('/', 1)[-1]}")
        except Exception:
            continue
        if not owner:
            continue
        for expr in dead_mod._expressions(owner):
            if not expr:
                continue
            tname = type(expr).__name__
            if tname == "MaterialExpressionMaterialFunctionCall":
                mf = None
                try:
                    mf = expr.get_editor_property("material_function")
                except Exception:
                    pass
                mf_path = dead_mod._asset_base(mf)
                if not mf_path or not unreal.EditorAssetLibrary.does_asset_exist(mf_path):
                    dead_functions.append({
                        "asset": path,
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
                    tp = dead_mod._asset_base(tex)
                    if tp and not unreal.EditorAssetLibrary.does_asset_exist(tp):
                        pname = _param_name(expr) or ""
                        missing_textures.append({
                            "asset": path,
                            "param": pname,
                            "missing_texture": tp,
                        })

    report["dead_node_audit"] = {
        "dead_functions": len(dead_functions),
        "missing_textures": len(missing_textures),
        "dead_function_details": dead_functions[:20],
        "missing_texture_details": missing_textures[:20],
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(
        f"[MasterReview] dead_mf={dead_total} banned_tex={banned_after} unwired_tex={unwired_after} -> {REPORT}"
    )
    return 0 if dead_total == 0 and banned_after == 0 and unwired_after == 0 else 1


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        return 1
    subprocess.run([sys.executable, str(PROJECT_ROOT / "Content/Python/repair_crash_assets.py")], check=False)
    log = PROJECT_ROOT / "Saved" / "Logs" / "master_review.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/review_portfolio_masters.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    print(f"Master review -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
