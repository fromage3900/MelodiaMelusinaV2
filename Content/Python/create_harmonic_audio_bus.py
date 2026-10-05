"""create_harmonic_audio_bus.py -- editor packet, 2026-10-05.

Creates the runtime audio-bus convergence assets for the harmonic state spine:

  /Game/Melodia/Audio/Mix/MPC_Melodia_HarmonicState   (sole writer: UMelodiaHarmonicStateSubsystem)
  /Game/Melodia/Audio/Mix/MPC_MelodiaAudioBus        (writers: osc_server.py bus lanes; C++ fallback)
  /Game/Melodia/Audio/Mix/SM_MelodiaAudioBus         (consumed by UMelodiaAudioBusSubsystem)

Idempotent: skips creation when an asset already exists, but always re-checks that
every expected parameter is present and reports what it added.

Run from the UE editor (Live Coding / Tools > Execute Python File). One editor,
one mutating surface -- verify nothing else is holding the editor.

Evidence: Saved/Audit/Status/harmonic_audio_bus_created.json
"""

import unreal

MIX_FOLDER = "/Game/Melodia/Audio/Mix"

HARMONIC_PARAMS = [
    ("Harmonic_Tension", "0.0"),
    ("Harmonic_Consonance", "0.5"),
    ("Harmonic_Dissonance", "0.0"),
    ("Harmonic_Mode", "0.0"),
    ("Harmonic_Resolution", "0.0"),
    ("Harmonic_BarPhase", "0.0"),
    ("Harmonic_Tempo", "128.0"),
    # PCG awareness lane (2026-10-05): local resonant PCG density, written by
    # UMelodiaHarmonicStateSubsystem, fed by UMelodiaPCGResonanceSensorComponent.
    ("PCG_ResonanceDensity", "0.0"),
]

BUS_PARAMS = [
    ("Bus_AmbienceLevel", "1.0"),
    ("Bus_MusicLevel", "1.0"),
    ("Bus_SFXLevel", "1.0"),
    ("Bus_VoiceLevel", "1.0"),
]

REPORT = {
    "asset": "harmonic_audio_bus",
    "date": "2026-10-05",
    "actions": [],
    "missing_after": [],
}


def log(msg):
    print(msg)
    unreal.log(msg)


def ensure_mpc(name, params):
    path = f"{MIX_FOLDER}/{name}"
    asset = unreal.load_asset(path)
    if asset is None:
        asset = unreal.EditorAssetLibrary.create_asset(
            name, MIX_FOLDER, unreal.MaterialParameterCollection, ""
        )
        if asset is None:
            log(f"FAILED: could not create {path}")
            REPORT["missing_after"].append(path)
            return None
        REPORT["actions"].append(f"created {path}")
        log(f"Created {path}")

    added = []
    existing = [p.get_name() for p in asset.get_parameters()]
    for pname, _default in params:
        if pname in existing:
            continue
        ok = asset.add_parameter(
            unreal.MaterialParameterInfo(name=pname, type=unreal.ParameterType.SCALAR)
        )
        if ok:
            added.append(pname)
            REPORT["actions"].append(f"added {pname} to {name}")
    if added:
        log(f"{name}: added {added}")

    # Re-read to prove the params exist (delegated output is not evidence).
    still_missing = [p for p, _ in params if p not in [x.get_name() for x in asset.get_parameters()]]
    if still_missing:
        REPORT["missing_after"].append(f"{name} missing {still_missing}")
        log(f"WARNING {name}: still missing {still_missing}")
    return asset


def ensure_sound_mix(name):
    path = f"{MIX_FOLDER}/{name}"
    asset = unreal.load_asset(path)
    if asset is None:
        asset = unreal.EditorAssetLibrary.create_asset(
            name, MIX_FOLDER, unreal.SoundMix, ""
        )
        if asset is None:
            log(f"FAILED: could not create {path}")
            REPORT["missing_after"].append(path)
            return None
        REPORT["actions"].append(f"created {path}")
        log(f"Created {path}")

    # Class overrides are added by UMelodiaAudioBusSubsystem at runtime via
    # UGameplayStatics::SetSoundMixClassOverride (same proven pattern as
    # MelodiaCore's UpdateTensionAmbienceDuck, which uses SM_MelodiaTensionDuck
    # + SCL_Ambience). No need to bake overrides into the asset.
    return asset


harmonic = ensure_mpc("MPC_Melodia_HarmonicState", HARMONIC_PARAMS)
bus = ensure_mpc("MPC_MelodiaAudioBus", BUS_PARAMS)
mix = ensure_sound_mix("SM_MelodiaAudioBus")

if harmonic and bus and mix:
    REPORT["status"] = "ok"
    unreal.save_asset(f"{MIX_FOLDER}/MPC_Melodia_HarmonicState")
    unreal.save_asset(f"{MIX_FOLDER}/MPC_MelodiaAudioBus")
    unreal.save_asset(f"{MIX_FOLDER}/SM_MelodiaAudioBus")
    REPORT["actions"].append("saved all three assets")
else:
    REPORT["status"] = "partial"

import json
import os
report_dir = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\Status"
os.makedirs(report_dir, exist_ok=True)
with open(os.path.join(report_dir, "harmonic_audio_bus_created.json"), "w") as f:
    json.dump(REPORT, f, indent=2)
log("Done. Report: Saved/Audit/Status/harmonic_audio_bus_created.json")
