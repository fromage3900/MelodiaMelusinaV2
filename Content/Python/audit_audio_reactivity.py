"""Audit audio reactivity wiring on M_Master_Toon_Universal + grandmaster MPC."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

import material_lib as lib

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "audio_reactivity.json"
MASTER = f"{lib.MASTER_DIR}/M_Master_Toon_Universal"
MPC_AUDIO = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
MF_AUDIO = f"{lib.FUNCTION_DIR}/MF_AudioReactiveBlend"


def main() -> dict:
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception:
        pass
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mpc_audio_exists": unreal.EditorAssetLibrary.does_asset_exist(MPC_AUDIO),
        "mf_audio_blend_exists": unreal.EditorAssetLibrary.does_asset_exist(MF_AUDIO),
        "master_exists": unreal.EditorAssetLibrary.does_asset_exist(MASTER),
        "params": {},
        "all_ok": False,
    }
    required = (
        "AudioReactivity",
        "BassWeight",
        "BeatPhaseStrength",
        "ShadowFlowerMask",
        "LayerBlendMode",
    )
    if report["master_exists"]:
        m = unreal.load_asset(MASTER)
        names = set()
        for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
            for prop in ("parameter_name", "ParameterName"):
                try:
                    raw = expr.get_editor_property(prop)
                    if raw:
                        names.add(str(raw))
                except Exception:
                    continue
        report["params"] = {p: p in names for p in required}
    report["all_ok"] = (
        report["mpc_audio_exists"]
        and report["mf_audio_blend_exists"]
        and report["master_exists"]
        and all(report.get("params", {}).values())
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
