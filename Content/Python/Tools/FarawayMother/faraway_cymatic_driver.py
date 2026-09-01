#!/usr/bin/env python3
"""
BP_FabricMountain_CymaticDriver — editor-time wiring helper.
Creates/updates a Blueprint actor that samples UMelodiaCymaticsSubsystem and drives MF_FabricMountainWPO via DMI.

Run inside Unreal Editor via Monolith:
  monolith run_python Content/Python/faraway_cymatic_driver.py

This does NOT write MPC_Melodia_Palette — read-only per EMERGING_TOOLCHAIN_MASTER_INDEX.
"""
import unreal

BP_PATH = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/BP_FabricMountain_CymaticDriver"
MF_WPO_PATH = "/Game/EnvSandbox/Materials/Functions/MF_FabricMountainWPO"
MI_PATH = "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_FabricRidge"
MASTER_LANDSCAPE = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"

def main():
    # Ensure MI exists on reuse master (no new master)
    master = unreal.load_asset(MASTER_LANDSCAPE)
    if not master:
        print("WARN: M_Master_Nikki_Landscape not loaded — check path")
    
    # Ensure MF exists (built by build_mf_fabric_mountain_wpo.py)
    mf = unreal.load_asset(MF_WPO_PATH)
    if mf:
        print(f"MF OK: {MF_WPO_PATH}")
    else:
        print(f"MF missing, will be built by build_mf_fabric_mountain_wpo.py: {MF_WPO_PATH}")

    # Create/verify BP_FabricMountain_CymaticDriver as Actor BP that on Tick samples cymatics
    # We write a minimal BP via asset tools if missing — full graph is wired by hand once per docs.
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = unreal.load_asset(BP_PATH)
    if bp:
        print(f"BP exists: {BP_PATH}")
    else:
        # Create Blueprint actor via factory
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("ParentClass", unreal.Actor)
        try:
            bp = tools.create_asset("BP_FabricMountain_CymaticDriver", "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype", unreal.Blueprint, factory)
            print(f"Created BP: {BP_PATH}" if bp else "Failed to create BP (factory needs editor context)")
        except Exception as e:
            print(f"BP create skipped (needs live editor): {e}")

    # Write wiring spec for manual verify
    spec = {
        "schema": "melodia_faraway_mother_cymatic_driver_v1",
        "bp": BP_PATH,
        "tick_logic": [
            "GetGameInstance().GetSubsystem(UMelodiaCymaticsSubsystem)",
            "SampleCymaticAmplitude( worldUV.x/8000, worldUV.y/8000 ) -> CymaticAmplitude",
            "GetCymaticMode( ModeN, ModeM )",
            "GetBeatPulse() -> BeatPulse; GetBassIntensity() -> BassIntensity",
            "Get MID from StaticMeshComponent -> SetScalarParameterValue(CymaticAmplitude, ModeN, ModeM, BeatPulse, BassIntensity)",
            "Optional: Get MPC BeatPhase for Niagara NPC_Melodia_Palette sync"
        ],
        "mid": MI_PATH,
        "master": MASTER_LANDSCAPE,
        "mf": MF_WPO_PATH,
        "wpo_inputs": ["UV","Time","CymaticAmplitude","BassIntensity","MidIntensity","BeatPulse","RhythmPulse","WindStrength","WindSpeed","WindDirection","FoldingAmount","HeightMap","MountainScale"],
        "guardrail": "READ-ONLY: never SetScalarParameterValue on MPC_Melodia_Palette. Cymatics IsReadOnlyByContract()==true.",
        "worldfield_bus": "ModeN/ModeM->Resonance, Amplitude->Tension, read by MF_FabricTensionMask + PCG + Niagara"
    }
    import json, os
    out = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/houdini_faraway_mother/cymatic_driver_spec.json"
    with open(out, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"Wrote spec: {out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
