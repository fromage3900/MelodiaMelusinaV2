"""Graph audit for M_Water_Master_Grand_v6 — params, blend mode, WPO, constants.

Run (editor):
  py Content/Python/audit_grand_water.py

Headless:
  python Content/Python/audit_grand_water.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "grand_water_graph_audit.json"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v6"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

SUGGESTED_NEW_PARAMS = {
    "vectors": ["WaterColorShallow", "WaterColorDeep", "CausticTint"],
    "scalars": [
        "DepthFadeDistance",
        "ShorelineWidth",
        "ShorelineFoam",
        "Opacity",
        "RefractionStrength",
    ],
    "static_switches": ["bUseShorelineUV"],
}


def _param_name(expr) -> str | None:
    for prop in ("parameter_name", "ParameterName"):
        try:
            raw = expr.get_editor_property(prop)
            if raw:
                return str(raw)
        except Exception:
            pass
    return None


def _audit_in_ue() -> dict:
    import unreal

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        raise RuntimeError(f"Missing {MASTER}")

    mat = unreal.load_asset(f"{MASTER}.{MASTER.split('/')[-1]}")
    params: list[dict] = []
    constants: list[dict] = []
    function_calls: list[str] = []
    has_wpo = False
    wpo_expr_types: list[str] = []

    for expr in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if not expr:
            continue
        tname = type(expr).__name__

        if "MaterialFunctionCall" in tname:
            mf = None
            try:
                mf = expr.get_editor_property("material_function")
            except Exception:
                pass
            if mf:
                function_calls.append(mf.get_name())

        if tname in ("MaterialExpressionConstant", "MaterialExpressionConstant3Vector",
                     "MaterialExpressionConstant4Vector"):
            val = None
            try:
                if tname == "MaterialExpressionConstant":
                    val = expr.get_editor_property("r")
                else:
                    val = str(expr.get_editor_property("constant"))
            except Exception:
                pass
            constants.append({"type": tname, "value": val})

        if "Parameter" in tname and "Function" not in tname:
            pname = _param_name(expr)
            if not pname:
                continue
            group = ""
            try:
                group = str(expr.get_editor_property("group") or "")
            except Exception:
                pass
            kind = "texture"
            if "Vector" in tname:
                kind = "vector"
            elif "StaticBool" in tname or "StaticSwitch" in tname:
                kind = "static_switch"
            elif "Scalar" in tname:
                kind = "scalar"
            default = None
            try:
                if kind == "scalar":
                    default = expr.get_editor_property("default_value")
                elif kind == "vector":
                    default = str(expr.get_editor_property("default_value"))
            except Exception:
                pass
            params.append({
                "name": pname,
                "kind": kind,
                "group": group,
                "default": default,
            })

    try:
        wpo = mat.get_editor_property("world_position_offset")
        if wpo:
            has_wpo = True
            wpo_expr_types.append(type(wpo).__name__)
    except Exception:
        pass

    blend_mode = str(mat.get_editor_property("blend_mode"))
    shading_model = str(mat.get_editor_property("shading_model"))
    try:
        two_sided = bool(mat.get_editor_property("two_sided"))
    except Exception:
        two_sided = False

    existing = {p["name"] for p in params}
    missing_suggested = {
        "vectors": [n for n in SUGGESTED_NEW_PARAMS["vectors"] if n not in existing],
        "scalars": [n for n in SUGGESTED_NEW_PARAMS["scalars"] if n not in existing],
        "static_switches": [n for n in SUGGESTED_NEW_PARAMS["static_switches"] if n not in existing],
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "blend_mode": blend_mode,
        "shading_model": shading_model,
        "two_sided": two_sided,
        "has_world_position_offset": has_wpo,
        "wpo_expression_types": wpo_expr_types,
        "param_count": len(params),
        "params": params,
        "function_calls": sorted(set(function_calls)),
        "internal_constant_count": len(constants),
        "internal_constants_sample": constants[:24],
        "ungrouped_params": [p["name"] for p in params if not p.get("group")],
        "missing_suggested_params": missing_suggested,
        "expand_ready": True,
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"GRAND_WATER_AUDIT_OK params={report['param_count']} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "audit_grand_water.log"
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_grand_water.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
