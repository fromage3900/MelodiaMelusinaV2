"""Graph audit for M_Master_Toon_Landscape_HeightBlend.

Headless:
  python Content/Python/audit_landscape.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "landscape_graph_audit.json"
MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

EXPECTED_LAYER_SAMPLES = ("Rock", "Grass", "Mud", "Path")
EXPECTED_NIKKI = (
    "PastelLift", "DreamSaturation", "RimWidth", "RimIntensity",
    "SparkleIntensity", "SparkleThreshold", "Iridescence",
)


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
    layer_samples: list[str] = []
    function_calls: list[str] = []

    for expr in unreal.MaterialEditingLibrary.get_material_expressions(mat) or []:
        if not expr:
            continue
        tname = type(expr).__name__

        if tname == "MaterialExpressionLandscapeLayerSample":
            pname = _param_name(expr)
            if pname:
                layer_samples.append(pname)

        if "MaterialFunctionCall" in tname:
            mf = None
            try:
                mf = expr.get_editor_property("material_function")
            except Exception:
                pass
            if mf:
                function_calls.append(mf.get_name())

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
            elif "StaticSwitch" in tname or "StaticBool" in tname:
                kind = "static_switch"
            elif "Scalar" in tname:
                kind = "scalar"
            params.append({"name": pname, "kind": kind, "group": group})

    flags = {}
    for flag in ("bUsedWithLandscape", "bUsedWithLandscapeGrass", "bUsesSubstrate"):
        try:
            flags[flag] = bool(mat.get_editor_property(flag))
        except Exception:
            flags[flag] = None

    existing = {p["name"] for p in params}
    grouped = sum(1 for p in params if p.get("group"))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "param_count": len(params),
        "grouped_count": grouped,
        "params": params,
        "layer_samples": sorted(layer_samples),
        "layer_samples_expected": list(EXPECTED_LAYER_SAMPLES),
        "layer_samples_ok": all(n in layer_samples for n in EXPECTED_LAYER_SAMPLES),
        "function_calls": sorted(set(function_calls)),
        "nikki_params_present": {n: n in existing for n in EXPECTED_NIKKI},
        "flags": flags,
        "ungrouped_params": [p["name"] for p in params if not p.get("group")],
        "clean": (
            grouped >= len(params) - 2
            and all(n in layer_samples for n in EXPECTED_LAYER_SAMPLES)
            and all(n in existing for n in EXPECTED_NIKKI)
            and any("MF_Nikki" in f for f in function_calls)
        ),
    }


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = _audit_in_ue()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"LANDSCAPE_AUDIT_OK params={report['param_count']} clean={report['clean']} -> {REPORT}")
        return 0
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "audit_landscape.log"
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/audit_landscape.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
