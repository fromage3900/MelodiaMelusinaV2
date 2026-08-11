"""Read-only Water v10 profile contract audit.

This script never saves assets. Run it in the editor after a cold C++ rebuild
and after the profile binder has been applied. It deliberately reports missing
FLIP assets rather than treating constructor fallbacks as production binding.
"""

from __future__ import annotations

import json
import unreal


PROFILE_PATH = "/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default"

REQUIRED_FIELDS = (
    "ContactDataChannel",
    "ContactSystem",
    "RippleSystem",
    "SplashSystem",
    "FluidSystem",
    "QuantumReactionSystem",
    "QuantumEntropySystem",
    "SurfaceMovementMetaSound",
    "SurfaceEntryMetaSound",
    "UnderwaterBubbleMetaSound",
    "WaterImpactMetaSound",
    "ReemergenceMetaSound",
    "AudioConcurrency",
    "AudioAttenuation",
)


def _asset_path(value) -> str:
    if value is None:
        return ""
    try:
        path = value.get_path_name()
        if path and path != "None":
            return str(path).split(".")[0]
    except Exception:
        pass
    text = str(value)
    return "" if text in ("None", "", "<None>") else text.split(".")[0]


def main() -> int:
    profile = unreal.EditorAssetLibrary.load_asset(PROFILE_PATH)
    if not profile:
        raise RuntimeError(f"Missing Water profile: {PROFILE_PATH}")

    missing = []
    resolved = {}
    for field in REQUIRED_FIELDS:
        try:
            value = profile.get_editor_property(field)
        except Exception as exc:
            missing.append({"field": field, "reason": f"reflection:{exc}"})
            continue
        path = _asset_path(value)
        resolved[field] = path
        if not path:
            missing.append({"field": field, "reason": "unbound"})
        elif not unreal.EditorAssetLibrary.does_asset_exist(path):
            missing.append({"field": field, "reason": "asset_missing", "path": path})

    report = {
        "ok": not missing,
        "profile": PROFILE_PATH,
        "resolved": resolved,
        "missing": missing,
        "budgets": {
            "MaxContactsPerSecond": profile.get_editor_property("MaxContactsPerSecond"),
            "MaxAudioEventsPerSecond": profile.get_editor_property("MaxAudioEventsPerSecond"),
            "MaxAudioVoices": profile.get_editor_property("MaxAudioVoices"),
            "MaxQuantumReactionEventsPerSecond": profile.get_editor_property("MaxQuantumReactionEventsPerSecond"),
        },
    }
    unreal.log(json.dumps(report, indent=2))
    if missing:
        unreal.log_error("Water v10 profile contract is incomplete; see the report above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
