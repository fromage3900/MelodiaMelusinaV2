"""Update v1 presets to v2 parameter names."""
import json
from pathlib import Path

PRESETS_DIR = Path(__file__).parent

# v1 -> v2 param name mapping
RENAME = {
    "DreamSaturation": "NikkiSaturation",
    "PastelLift": "NikkiPastelLift",
    "WitchBarrierEmissiveVeins": "MadokaVeinEmissive",
}

# v2 params that didn't exist in v1 (with defaults from builder)
V2_ONLY_PARAMS = {
    "GlobalSeed": 0.5,
    "NikkiSparkleAmount": 0.35,
    "NikkiFabricDetail": 0.15,
    "NikkiFlowStrength": 0.25,
    "MadokaGlowAmount": 0.3,
    "MadokaEmissiveBrightness": 2.0,
    "MadokaCuteBias": 0.5,
    "IttoWearAmount": 0.4,
    "IttoBreakupAmount": 0.25,
    "IttoErosionStrength": 0.2,
    "CelestialScale": 1.0,
    "CelestialDrift": 0.1,
    "CelestialOrbitSpeed": 0.05,
    "CelestialOrbitPeriod": 60,
    "CelestialCMBAmount": 0.15,
    "CelestialEmissiveBoost": 1.5,
    "HeightScale": 0.25,
    "NormalStrength": 0.8,
    "NormalDetail": 0.3,
    "RoughnessBias": 0.55,
    "RoughnessContrast": 0.3,
    "MetallicAmount": 0.05,
    "AOStrength": 0.7,
    "SSSAmount": 0.12,
    "EmissiveIntensity": 1.0,
    "ExportResolution": 11,
}

# Style-specific param overrides for each preset
STYLE_PARAMS = {
    "nikki": {
        "NikkiSparkleAmount": 0.5,
        "NikkiFabricDetail": 0.2,
        "NikkiFlowStrength": 0.3,
        "NikkiSaturation": 0.6,
    },
    "madoka": {
        "MadokaGlowAmount": 0.4,
        "MadokaEmissiveBrightness": 2.5,
        "MadokaCuteBias": 0.5,
        "MadokaVeinEmissive": 0.4,
    },
    "itto": {
        "IttoWearAmount": 0.4,
        "IttoBreakupAmount": 0.25,
        "IttoErosionStrength": 0.2,
    },
    "celestial": {
        "CelestialScale": 1.5,
        "CelestialNebulaScale": 0.5,
        "CelestialTwinkle": 0.6,
        "CelestialDrift": 0.15,
        "CelestialOrbitSpeed": 0.08,
        "CelestialCMBAmount": 0.2,
        "CelestialEmissiveBoost": 2.0,
    },
    "neutral": {},
}

for preset_file in sorted(PRESETS_DIR.glob("*.json")):
    if preset_file.name == "update_to_v2.py":
        continue
    with open(preset_file) as f:
        preset = json.load(f)

    old_params = preset["params"]
    new_params = {}

    # Rename v1 params and copy shared params
    for k, v in old_params.items():
        new_k = RENAME.get(k, k)
        new_params[new_k] = v

    # Add v2-only params with defaults
    for k, v in V2_ONLY_PARAMS.items():
        if k not in new_params:
            new_params[k] = v

    # Apply style-specific overrides
    name = preset["name"]
    if name in STYLE_PARAMS:
        for k, v in STYLE_PARAMS[name].items():
            new_params[k] = v

    preset["params"] = new_params
    with open(preset_file, "w") as f:
        json.dump(preset, f, indent=2)

    changed = [k for k in old_params if RENAME.get(k, k) != k]
    added = [k for k in V2_ONLY_PARAMS if k not in {RENAME.get(ok, ok) for ok in old_params} or k in STYLE_PARAMS.get(name, {})]
    print(f"  {preset_file.name}: renamed {changed}, {len(added)} v2 params added")

print("\nDone. Presets updated to v2 parameter names.")