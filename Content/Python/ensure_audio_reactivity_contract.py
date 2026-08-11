"""Ensure the canonical runtime channels exist on the grandmaster Melodia MPC."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "audio_reactivity_contract.json"
CHANNELS = {
    # Runtime publisher compatibility: UMelodiaAudioReactivePresentationSubsystem
    # writes these names every frame.  Keep them alongside the expanded Melodia
    # signals below so existing materials and future systems share one MPC.
    "GlobalReactivity": 0.0,
    "Bass": 0.0,
    "Mid": 0.0,
    "Treble": 0.0,
    "BeatPulse": 0.0,
    "BeatPhase": 0.0,
    "GlobalAudioReactivity": 1.0,
    "BassIntensity": 0.0,
    "MidIntensity": 0.0,
    "TrebleIntensity": 0.0,
    "ComboNormalized": 0.0,
    "CrescendoNormalized": 0.0,
    "CommandEnergy": 0.0,
    "BreakPulse": 0.0,
    "VictoryPulse": 0.0,
    "EnemyTension": 0.0,
}


def main() -> int:
    mpc = unreal.EditorAssetLibrary.load_asset(MPC_PATH)
    if not mpc:
        raise RuntimeError(f"Missing material parameter collection: {MPC_PATH}")

    scalar_parameters = list(mpc.get_editor_property("scalar_parameters") or [])
    existing = {str(p.get_editor_property("parameter_name")) for p in scalar_parameters}
    added = []
    for name, default in CHANNELS.items():
        if name in existing:
            continue
        param = unreal.CollectionScalarParameter()
        param.set_editor_property("parameter_name", name)
        param.set_editor_property("default_value", default)
        scalar_parameters.append(param)
        added.append(name)

    mpc.set_editor_property("scalar_parameters", scalar_parameters)
    unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    final_names = {str(p.get_editor_property("parameter_name")) for p in (mpc.get_editor_property("scalar_parameters") or [])}
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc": MPC_PATH,
        "added": added,
        "missing": sorted(set(CHANNELS) - final_names),
        "ok": set(CHANNELS).issubset(final_names),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
