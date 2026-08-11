"""Expand M_Water_Master_Grand_v6 — add depth/shoreline params + MF wiring.

Run after setup_material_functions.py --force.

Editor:
  py Content/Python/expand_grand_water.py

Headless:
  python Content/Python/expand_grand_water.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "grand_water_expand_graph.json"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
MF_DEPTH = "/Game/EnvSandbox/Materials/Functions/MF_WaterDepthColor.MF_WaterDepthColor"
MF_SHORE = "/Game/EnvSandbox/Materials/Functions/MF_WaterShorelineFade.MF_WaterShorelineFade"
MF_FOAM = "/Game/EnvSandbox/Materials/Functions/MF_WaterFoam.MF_WaterFoam"
MPC_SAKURA = "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _ensure_mfs() -> None:
    import setup_material_functions as mf_mod

    mf_mod.build_all(force=True)


def _mf_call(m, lib, path: str, x: int, y: int):
    if not __import__("unreal").EditorAssetLibrary.does_asset_exist(path):
        return None
    c = lib.create_expression(m, __import__("unreal").MaterialExpressionMaterialFunctionCall, x, y)
    c.set_editor_property("material_function", __import__("unreal").load_asset(path))
    return c


def _find_param(m, lib, name: str):
    import unreal

    for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
        if not expr:
            continue
        for prop in ("parameter_name", "ParameterName"):
            try:
                if str(expr.get_editor_property(prop)) == name:
                    return expr
            except Exception:
                pass
    return None


def _ensure_param_scalar(m, lib, name: str, group: str, default: float, x: int, y: int):
    existing = _find_param(m, lib, name)
    if existing:
        return existing
    return lib.scalar_param(m, name, group, default, x, y)


def _ensure_param_vector(m, lib, name: str, group: str, default, x: int, y: int):
    existing = _find_param(m, lib, name)
    if existing:
        return existing
    return lib.vector_param(m, name, group, default, x, y)


def expand(*, force: bool = False) -> dict:
    import unreal
    import material_lib as lib

    _ensure_mfs()

    asset_path = f"{MASTER}.M_Water_Master_Grand_v6"
    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing {MASTER}")

    m = unreal.load_asset(asset_path)
    lib.try_set_editor_property(m, "blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    lib.try_set_editor_property(m, "two_sided", True)

    # --- Params (neutral defaults) ---
    shallow = _ensure_param_vector(
        m, lib, "WaterColorShallow", "Depth",
        (0.15, 0.55, 0.62, 1.0), -2400, -200,
    )
    deep = _ensure_param_vector(
        m, lib, "WaterColorDeep", "Depth",
        (0.02, 0.12, 0.28, 1.0), -2400, -80,
    )
    caustic_tint = _ensure_param_vector(
        m, lib, "CausticTint", "Caustics",
        (1.0, 1.0, 1.0, 1.0), -2400, 40,
    )
    depth_fade = _ensure_param_scalar(m, lib, "DepthFadeDistance", "Depth", 800.0, -2400, 160)
    shore_w = _ensure_param_scalar(m, lib, "ShorelineWidth", "Shoreline", 0.15, -2400, 280)
    shore_foam = _ensure_param_scalar(m, lib, "ShorelineFoam", "Shoreline", 0.0, -2400, 400)
    opacity = _ensure_param_scalar(m, lib, "Opacity", "Surface", 0.85, -2400, 520)
    refract = _ensure_param_scalar(m, lib, "RefractionStrength", "Surface", 0.02, -2400, 640)

    rough = _find_param(m, lib, "WaterRoughness")
    if not rough:
        rough = _ensure_param_scalar(m, lib, "WaterRoughness", "Surface", 0.1, -2400, 760)

    # Static switch for shoreline UV path
    b_shore_uv = None
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
        if expr and "StaticSwitch" in type(expr).__name__:
            try:
                if str(expr.get_editor_property("parameter_name")) == "bUseShorelineUV":
                    b_shore_uv = expr
                    break
            except Exception:
                pass
    if not b_shore_uv:
        b_shore_uv = lib.create_expression(m, unreal.MaterialExpressionStaticSwitchParameter, -2400, 880)
        b_shore_uv.set_editor_property("parameter_name", "bUseShorelineUV")
        b_shore_uv.set_editor_property("group", "Shoreline")
        b_shore_uv.set_editor_property("default_value", False)

    # --- Depth MF ---
    cam_dist = lib.create_expression(m, unreal.MaterialExpressionPixelDepth, -1800, 200)
    depth_call = _mf_call(m, lib, MF_DEPTH, -1400, 80)
    wired = {"depth_mf": False, "shore_mf": False, "base_color": False, "opacity": False, "emissive": False, "mpc": False}
    if depth_call:
        lib.connect(shallow, "", depth_call, "WaterColorShallow")
        lib.connect(deep, "", depth_call, "WaterColorDeep")
        lib.connect(depth_fade, "", depth_call, "DepthFadeDistance")
        lib.connect(cam_dist, "", depth_call, "Depth")
        wired["depth_mf"] = True

    tex_coord = lib.create_expression(m, unreal.MaterialExpressionTextureCoordinate, -1800, 420)
    shore_call = _mf_call(m, lib, MF_SHORE, -1400, 380)
    if shore_call:
        lib.connect(tex_coord, "", shore_call, "UV")
        lib.connect(shore_w, "", shore_call, "ShorelineWidth")
        lib.connect(shore_foam, "", shore_call, "ShorelineFoam")
        wired["shore_mf"] = True

    base_col = depth_call if depth_call else shallow
    if depth_call:
        tinted = lib.create_expression(m, unreal.MaterialExpressionMultiply, -800, 120)
        lib.connect(depth_call, "", tinted, "A")
        lib.connect(caustic_tint, "", tinted, "B")
        caustic_mul = _find_param(m, lib, "CausticIntensity")
        if caustic_mul:
            final_col = lib.create_expression(m, unreal.MaterialExpressionMultiply, -600, 120)
            lib.connect(tinted, "", final_col, "A")
            lib.connect(caustic_mul, "", final_col, "B")
            base_col = final_col
        else:
            base_col = tinted

    if shore_call:
        one = lib.create_expression(m, unreal.MaterialExpressionConstant, -800, 360)
        one.set_editor_property("r", 1.0)
        lib.connect_static_switch(b_shore_uv, shore_call, one)
        shore_alpha = shore_call
        shore_foam_out = shore_call
        opac_mul = lib.create_expression(m, unreal.MaterialExpressionMultiply, -400, 360)
        lib.connect(opacity, "", opac_mul, "A")
        lib.connect(b_shore_uv, "", opac_mul, "B")
        # Shore tint on shallow color at edges
        if depth_call:
            shore_tint = lib.create_expression(m, unreal.MaterialExpressionLinearInterpolate, -400, 120)
            lib.connect(base_col, "", shore_tint, "A")
            lib.connect(shallow, "", shore_tint, "B")
            lib.connect(b_shore_uv, "", shore_tint, "Alpha")
            base_col = shore_tint
        try:
            unreal.MaterialEditingLibrary.connect_material_property(
                opac_mul, "", unreal.MaterialProperty.MP_OPACITY,
            )
            wired["opacity"] = True
        except Exception:
            try:
                unreal.MaterialEditingLibrary.connect_material_property(
                    opacity, "", unreal.MaterialProperty.MP_OPACITY,
                )
                wired["opacity"] = True
            except Exception:
                pass
        # Foam to emissive
        foam_mul = lib.create_expression(m, unreal.MaterialExpressionMultiply, -200, 400)
        lib.connect(shore_foam_out, "Foam", foam_mul, "A")
        lib.connect(shore_foam, "", foam_mul, "B")
        emissive = lib.create_expression(m, unreal.MaterialExpressionMultiply, 0, 400)
        lib.connect(foam_mul, "", emissive, "A")
        lib.connect(caustic_tint, "", emissive, "B")
        try:
            unreal.MaterialEditingLibrary.connect_material_property(
                emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR,
            )
            wired["emissive"] = True
        except Exception:
            pass
    else:
        try:
            unreal.MaterialEditingLibrary.connect_material_property(
                opacity, "", unreal.MaterialProperty.MP_OPACITY,
            )
            wired["opacity"] = True
        except Exception:
            pass

    magical = _find_param(m, lib, "MagicalIntensity")
    mpc_pulse = lib.collection_scalar(m, MPC_SAKURA, "SparklePulse", -600, 500)
    if mpc_pulse and magical:
        mag_scale = lib.create_expression(m, unreal.MaterialExpressionMultiply, -400, 500)
        lib.connect(magical, "", mag_scale, "A")
        lib.connect(mpc_pulse, "", mag_scale, "B")
        mag_boost = lib.create_expression(m, unreal.MaterialExpressionMultiply, -200, 500)
        lib.connect(mag_scale, "", mag_boost, "A")
        half = lib.create_expression(m, unreal.MaterialExpressionConstant, -400, 580)
        half.set_editor_property("r", 0.25)
        lib.connect(half, "", mag_boost, "B")
        one_c = lib.create_expression(m, unreal.MaterialExpressionConstant, -200, 580)
        one_c.set_editor_property("r", 1.0)
        mag_add = lib.create_expression(m, unreal.MaterialExpressionAdd, 0, 500)
        lib.connect(one_c, "", mag_add, "A")
        lib.connect(mag_boost, "", mag_add, "B")
        boosted = lib.create_expression(m, unreal.MaterialExpressionMultiply, 200, 120)
        lib.connect(base_col, "", boosted, "A")
        lib.connect(mag_add, "", boosted, "B")
        base_col = boosted
        wired["mpc"] = True

    try:
        unreal.MaterialEditingLibrary.connect_material_property(
            base_col, "", unreal.MaterialProperty.MP_BASE_COLOR,
        )
        wired["base_color"] = True
    except Exception:
        pass

    try:
        unreal.MaterialEditingLibrary.connect_material_property(
            rough, "", unreal.MaterialProperty.MP_ROUGHNESS,
        )
    except Exception:
        pass

    try:
        unreal.MaterialEditingLibrary.connect_material_property(
            refract, "", unreal.MaterialProperty.MP_REFRACTION,
        )
    except Exception:
        pass

    unreal.MaterialEditingLibrary.recompile_material(m)
    lib.save_package(m)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "wired": wired,
        "force": force,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"EXPAND_GRAND_WATER_OK wired={wired} -> {REPORT}")
    return result


def main() -> int:
    force = "--force" in sys.argv or __import__("os").environ.get("BS_WATER_EXPAND", "").lower() in ("1", "true")
    try:
        import unreal  # noqa: F401
        expand(force=force)
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "expand_grand_water.log"
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/expand_grand_water.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
