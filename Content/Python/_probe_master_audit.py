"""Audit M_Master_Toon_Universal — writes Saved/Audit/master_link_audit.json."""
from __future__ import annotations

import json
import os

import unreal
import material_lib as lib

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "Audit", "master_link_audit.json")


def main() -> None:
    report: dict = {"master": MASTER, "ok": False}
    m = unreal.load_asset(MASTER)
    if not m:
        report["error"] = "load_failed"
        _write(report)
        return

    exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(m) or [])
    report["expression_count"] = len(exprs)

    dead_calls: list[str] = []
    mf_calls: list[str] = []
    for expr in exprs:
        if not expr or "MaterialFunctionCall" not in type(expr).__name__:
            continue
        mf = None
        try:
            mf = expr.get_editor_property("material_function")
        except Exception:
            pass
        if not mf:
            dead_calls.append("(null)")
            continue
        name = mf.get_name()
        mf_calls.append(name)
        base = mf.get_path_name().split(".", 1)[0]
        if not unreal.EditorAssetLibrary.does_asset_exist(base):
            dead_calls.append(base)

    report["mf_calls"] = sorted(set(mf_calls))
    report["dead_function_calls"] = sorted(set(dead_calls))
    report["missing_mf_assets"] = [
        f"{lib.FUNCTION_DIR}/{n}"
        for n in ("MF_ParallaxCore", "MF_NormalAdjust")
        if not unreal.EditorAssetLibrary.does_asset_exist(f"{lib.FUNCTION_DIR}/{n}")
    ]

    try:
        unreal.MaterialEditingLibrary.recompile_material(m)
        report["recompile"] = "ok"
        report["is_compiled"] = bool(m.get_editor_property("is_compiled"))
    except Exception as exc:
        report["recompile"] = f"fail: {exc}"

    report["ok"] = not report["dead_function_calls"] and report.get("recompile") == "ok"
    _write(report)
    print(f"MASTER_AUDIT ok={report['ok']} dead={report['dead_function_calls']} exprs={len(exprs)}")


def _write(report: dict) -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)


if __name__ == "__main__":
    main()
