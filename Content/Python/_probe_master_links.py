"""Probe M_Master_Toon_Universal for broken MF/texture refs (editor)."""
from __future__ import annotations

import unreal
import material_lib as lib

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
REQUIRED_MFS = (
    "MF_AnimeSkinWrap",
    "MF_SpaceParallax",
    "MF_ParallaxCore",
    "MF_NormalAdjust",
    "MF_MapComposite",
    "MF_GildingOverlay",
    "MF_CurvatureOrnament",
    "MF_RealParallax",
    "MF_UVTransform",
)


def main() -> None:
    m = unreal.load_asset(MASTER)
    if not m:
        unreal.log_error(f"[Probe] FAILED to load {MASTER}")
        return

    exprs = list(unreal.MaterialEditingLibrary.get_material_expressions(m) or [])
    unreal.log(f"[Probe] master loaded expressions={len(exprs)}")

    missing_mf: list[str] = []
    for name in REQUIRED_MFS:
        path = f"{lib.FUNCTION_DIR}/{name}"
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            missing_mf.append(path)
    unreal.log(f"[Probe] missing_mf_assets={missing_mf}")

    dead_calls: list[str] = []
    for expr in exprs:
        if not expr or "MaterialFunctionCall" not in type(expr).__name__:
            continue
        mf = None
        try:
            mf = expr.get_editor_property("material_function")
        except Exception:
            pass
        if not mf:
            dead_calls.append("(null material_function)")
            continue
        base = mf.get_path_name().split(".", 1)[0]
        if not unreal.EditorAssetLibrary.does_asset_exist(base):
            dead_calls.append(base)

    unreal.log(f"[Probe] dead_function_calls={sorted(set(dead_calls))}")

    import portfolio_texture_catalog as catalog

    v = catalog.scan_master_texture_violations(m)
    unreal.log(
        f"[Probe] texture_violations banned={v['banned']} unwired={v['unwired'][:20]} "
        f"wrong_role={v['wrong_role']}"
    )

    try:
        unreal.MaterialEditingLibrary.recompile_material(m)
        unreal.log("[Probe] recompile=OK")
    except Exception as exc:
        unreal.log_error(f"[Probe] recompile=FAIL {exc}")


if __name__ == "__main__":
    main()
