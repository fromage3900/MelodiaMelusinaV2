"""Disk-level Water v10 finalization audit.

This audit intentionally does not pretend that a .uasset filename proves its
serialized property bindings or runtime behavior. It verifies only evidence
available without an editor, then reports the UE-runtime gates separately.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Saved" / "Audit" / "water_v10_finalization_gate.json"

ASSETS = {
    "profile": "Content/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.uasset",
    "contact_channel": "Content/EnvSandbox/Water/v10/NDC_MelodiaWaterContact.uasset",
    "contact_system": "Content/EnvSandbox/Water/v10/NS_MelodiaWaterContact.uasset",
    "surface_movement": "Content/EnvSandbox/Water/v10/Audio/MS_Water_SurfaceMovement.uasset",
    "surface_entry": "Content/EnvSandbox/Water/v10/Audio/MS_Water_SurfaceEntry.uasset",
    "underwater_bubble": "Content/EnvSandbox/Water/v10/Audio/MS_Water_UnderwaterBubble.uasset",
    "impact": "Content/EnvSandbox/Water/v10/Audio/MS_Water_Impact.uasset",
    "reemergence": "Content/EnvSandbox/Water/v10/Audio/MS_Water_Reemergence.uasset",
    "concurrency": "Content/EnvSandbox/Water/v10/Audio/SC_WaterV10_AudioConcurrency.uasset",
    "attenuation": "Content/EnvSandbox/Water/v10/Audio/SA_WaterV10_3D_Attenuation.uasset",
    "quantum_reaction": "Content/Melodia/VFX/NS_Melusina_ChaosDrift.uasset",
    "quantum_entropy": "Content/Melodia/VFX/NS_Melusina_EntropyDust.uasset",
    "ripple": "Content/Melodia/VFX/NS_Melusina_Ripple.uasset",
    "splash": "Content/Melodia/VFX/NS_Melusina_Splash.uasset",
}

FLIP_ASSETS = {
    "flip2d_pool": "Content/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP2D_Pool.uasset",
    "flip2d_splash": "Content/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP2D_Splash.uasset",
    "flip3d_pool": "Content/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP3D_Pool.uasset",
    "flip3d_splash": "Content/EnvSandbox/Water/v10/FLIP/NS_WaterV10_FLIP3D_Splash.uasset",
}

SOURCE_CHECKS = {
    "quantum_queue": (
        "Source/BS_GodFile/MelodiaIntegration/MelodiaQuantumDrawSubsystem.cpp",
        ("PendingSongDraws", "ActiveRequestGeneration", "CancelActiveDraw", "RequestGeneration"),
    ),
    "niagara_exclusive_route": (
        "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterNiagaraBridgeComponent.cpp",
        ("bPublishedToDataChannel", "bSpawnDirectContactEffects", "WriteContactToDataChannel", "SpawnDirectContactVFX"),
    ),
    "audio_profile_authority": (
        "Source/BS_GodFile/MelodiaIntegration/MelodiaWaterAudioBridgeComponent.cpp",
        ("DefaultAudioConcurrency", "DefaultAudioAttenuation", "bAudioReady", "LastReemergenceTime"),
    ),
    "teardown_suppression": (
        "Source/BS_GodFile/MelodiaIntegration/MelodiaTraversalComponent.cpp",
        ("bSuppressWaterPresentation",),
    ),
    "asset_manager_registration": (
        "Config/DefaultEngine.ini",
        ("PrimaryAssetType=\"MelodiaWaterProfile\"",),
    ),
    "safe_commandlet_wrapper": (
        "Content/Python/run_world_partition_builder_safe.py",
        ("Refusing commandlet launch", "WorldPartitionBuilderCommandlet"),
    ),
}


def main() -> int:
    report = {
        "disk_evidence": {"assets": {}, "source_checks": {}},
        "runtime_gates": [
            "editor cold rebuild and module load",
            "serialized Water profile property readback",
            "Blueprint Niagara driver reads QuantumReactionColor and QuantumPulse",
            "single Data Channel consumer response",
            "PIE Water/audio traversal replay",
            "project-owned FLIP runtime capture",
            "World Partition PCG/HLOD commandlet replay",
        ],
        "blocking": [],
    }

    for name, relative in ASSETS.items():
        path = ROOT / relative
        report["disk_evidence"]["assets"][name] = {
            "path": str(relative).replace("\\", "/"),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        if not path.exists():
            report["blocking"].append(f"missing project asset: {relative}")

    for name, relative in FLIP_ASSETS.items():
        path = ROOT / relative
        report["disk_evidence"]["assets"][name] = {
            "path": str(relative).replace("\\", "/"),
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
        }
        if not path.exists():
            report["blocking"].append(f"missing project-owned FLIP asset: {relative}")

    for name, (relative, needles) in SOURCE_CHECKS.items():
        path = ROOT / relative
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        missing = [needle for needle in needles if needle not in text]
        report["disk_evidence"]["source_checks"][name] = {
            "path": str(relative).replace("\\", "/"),
            "exists": path.exists(),
            "missing_tokens": missing,
        }
        if missing:
            report["blocking"].append(f"source contract incomplete: {relative}: {', '.join(missing)}")

    report["ok"] = not report["blocking"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

