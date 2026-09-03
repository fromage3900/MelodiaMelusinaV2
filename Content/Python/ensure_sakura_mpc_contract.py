"""Ensure the legacy Sakura VFX MPC exposes its documented runtime channels."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MPC_PATH = "/Game/EnvSandbox/VFX/MPC/MPC_SakuraDream"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "sakura_mpc_contract.json"
CHANNELS = {
    "WindStrength": 0.3,
    "GustTrigger": 0.0,
    "SparklePulse": 0.0,
    "PetalDensity": 1.0,
}


def main() -> int:
    mpc = unreal.EditorAssetLibrary.load_asset(MPC_PATH)
    if not mpc:
        raise RuntimeError(f"Missing material parameter collection: {MPC_PATH}")

    scalar_parameters = list(mpc.get_editor_property("scalar_parameters") or [])
    existing = {str(p.get_editor_property("parameter_name")) for p in scalar_parameters}
    added: list[str] = []
    for name, default in CHANNELS.items():
        if name in existing:
            continue
        parameter = unreal.CollectionScalarParameter()
        parameter.set_editor_property("parameter_name", name)
        parameter.set_editor_property("default_value", default)
        scalar_parameters.append(parameter)
        added.append(name)

    mpc.set_editor_property("scalar_parameters", scalar_parameters)
    unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    final_names = {
        str(p.get_editor_property("parameter_name"))
        for p in (mpc.get_editor_property("scalar_parameters") or [])
    }
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc": MPC_PATH,
        "added": added,
        "missing": sorted(set(CHANNELS) - final_names),
        "ok": set(CHANNELS).issubset(final_names),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
