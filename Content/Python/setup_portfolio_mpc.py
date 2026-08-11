"""Ensure the portfolio grade channels live on the grandmaster MPC.

These drive scene-wide color cohesion; the five scalars (BaseTintShift
ShadowDreamBias RimWarmth ElementalGrade TimeOfDayWarmth) and PaletteTint live
on MPC_Melodia_Palette, the single grandmaster collection, sampled via
CollectionParameter nodes on M_Master_Toon_Universal. No second MPC is created
(Sunset_Master still reads ShadowDreamBias via its own CollectionParameter).

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/setup_portfolio_mpc.py"
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "portfolio_mpc.json"
MPC_NAME = "MPC_MemMelodia_Palette_Grandmaster"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

MPC_SCALARS = [
    ("BaseTintShift", 1.0),       # multiply global base tint (1=neutral)
    ("ShadowDreamBias", 0.0),     # add to ShadowDreamStrength on instances
    ("RimWarmth", 0.0),           # add to RimIntensity (warm rim push)
    ("ElementalGrade", 0.0),      # add to ElementStrength
    ("TimeOfDayWarmth", 0.0),     # global TOD warmth (-1 cool .. +1 warm)
]

MPC_VECTORS = [
    ("PaletteTint", (1.0, 1.0, 1.0, 1.0)),  # multiply final grade vector
]


def _add_scalar(mpc, name: str, default: float) -> None:
    try:
        param = unreal.CollectionScalarParameter()
        param.parameter_name = name
        param.default_value = default
        mpc.add_scalar_parameter(param)
    except Exception:
        try:
            mpc.set_scalar_parameter_default_value(name, default)
        except Exception as exc:
            unreal.log_warning(f"[MPC Palette] scalar {name}: {exc}")


def _add_vector(mpc, name: str, default: tuple[float, float, float, float]) -> None:
    try:
        param = unreal.CollectionVectorParameter()
        param.parameter_name = name
        param.default_value = unreal.LinearColor(*default)
        mpc.add_vector_parameter(param)
    except Exception:
        try:
            mpc.set_vector_parameter_default_value(name, unreal.LinearColor(*default))
        except Exception as exc:
            unreal.log_warning(f"[MPC Palette] vector {name}: {exc}")


def build_mpc() -> str:
    # Grandmaster MPC already carries the grade channels; do not recreate a second
    # palette island. Ensure the channels exist and return the path.
    if not unreal.EditorAssetLibrary.does_asset_exist(MPC_PATH):
        raise RuntimeError(f"Missing grandmaster MPC {MPC_PATH}")

    mpc = unreal.load_asset(MPC_PATH)
    existing = {str(s.get_editor_property("parameter_name"))
                for s in mpc.get_editor_property("scalar_parameters")}
    for name, default in MPC_SCALARS:
        if name not in existing:
            _add_scalar(mpc, name, default)
    vexisting = {str(v.get_editor_property("parameter_name"))
                 for v in mpc.get_editor_property("vector_parameters")}
    for name, default in MPC_VECTORS:
        if name not in vexisting:
            _add_vector(mpc, name, default)

    unreal.log(f"[MPC Palette] grandmaster MPC ok: {MPC_PATH}")
    return MPC_PATH


def main() -> int:
    path = build_mpc()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc_grandmaster": path,
        "mpc_audio": MPC_PATH,
        "scalars": {n: d for n, d in MPC_SCALARS},
        "vectors": {n: list(v) for n, v in MPC_VECTORS},
        "usage": (
            "M_Master_Toon_Universal reads ShadowDreamBias via CollectionParameter; "
            "BaseTintShift/PaletteTint/RimWarmth reserved for the palette pass. "
            "Tune once per scene for cohesive grade."
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
