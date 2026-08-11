"""Disable nonessential cosmetic branches that overflow SM6 MPC limits."""
from __future__ import annotations

import json
from pathlib import Path

ASSET = "/Game/EnvSandbox/Materials/Instances/Environment/Zen/MI_Zen_MossStone"
REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "zen_mossstone_sm6_fix.json"


def main() -> dict:
    import unreal

    instance = unreal.load_asset(ASSET)
    if not instance:
        raise RuntimeError(f"Could not load {ASSET}")

    editing = unreal.MaterialEditingLibrary
    changes = {}
    for name in ("bWeather_Active", "bFairyDust_Active"):
        editing.set_material_instance_static_switch_parameter_value(instance, name, False)
        changes[name] = False
    editing.update_material_instance(instance)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(instance)

    result = {"asset": ASSET, "changes": changes, "saved": bool(saved), "ok": bool(saved)}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log("Zen MossStone SM6 fix: " + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
