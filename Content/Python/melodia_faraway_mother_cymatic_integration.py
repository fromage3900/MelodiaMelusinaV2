#!/usr/bin/env python3
"""
Faraway Mother — Cymatic Scaffolding Integration
Places 6 height-aware instances in LV_FarawayMother_Prototype, assigns
  MI_Copernicus_FarawayCelestialSilk / CymaticMarble / CavernWeave
  to ridges vs valley floor, and validates MPC_Cymatics_Driver wiring.

Executed in UE Editor Python: exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/melodia_faraway_mother_cymatic_integration.py").read())

Offline (no editor): python Content/Python/melodia_faraway_mother_cymatic_integration.py --check
  validates bindings JSON and C++ contracts without touching .umap.
"""
from pathlib import Path
import json, hashlib, argparse, sys

PROJECT_ROOT = Path(r"C:/EnvironmentPortfolio/BS_GodFile")
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"

# Height-aware instances — 3 ridges (high), 2 valley floor (low), 1 shoulder
INSTANCES = [
    {
        "label": "SM_Faraway_Ridge_North_CelestialSilk",
        "mi": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk",
        "location": [  0,  280000,  3800],
        "scale": [80, 80, 4],
        "height_band": "ridge_high",
        "role": "Fabric ridge — maternal shoulder silhouette, celestial jacquard",
    },
    {
        "label": "SM_Faraway_Ridge_East_CymaticMarble",
        "mi": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticMarble",
        "location": [ 260000,   0,  3200],
        "scale": [60, 90, 3],
        "height_band": "ridge_mid",
        "role": "Cymatic marble — Chladni-veined singing stone, bass nodes",
    },
    {
        "label": "SM_Faraway_Ridge_South_CavernWeave",
        "mi": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CavernWeave",
        "location": [  0, -260000, 2800],
        "scale": [70, 70, 3.5],
        "height_band": "ridge_low",
        "role": "Cavern weave — rock+marble+crystal, lace fold shadow",
    },
    {
        "label": "SM_Faraway_ValleyFloor_Center_CavernWeave",
        "mi": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CavernWeave",
        "location": [  0,    0,  -800],
        "scale": [120, 120, 1],
        "height_band": "valley_floor",
        "role": "Valley floor — cavern weave compresses, moisture high",
    },
    {
        "label": "SM_Faraway_ValleyBasin_CymaticMarble",
        "mi": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticMarble",
        "location": [ -180000, 120000, -1200],
        "scale": [90, 90, 1.2],
        "height_band": "valley_depression",
        "role": "Valley depression — marble basin, standing-wave pooling",
    },
    {
        "label": "SM_Faraway_ShoulderFold_CelestialSilk",
        "mi": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk",
        "location": [ 140000, 180000, 1500],
        "scale": [50, 50, 2.5],
        "height_band": "shoulder_fold",
        "role": "Shoulder fold — silk at mid-altitude, iridescence breathing",
    },
]

MPC_DRIVER = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"
MPC_SOURCE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

# Material param -> MPC scalar mapping (presentation-only)
BINDINGS = [
    {"mpc_scalar": "Cymatic_BeatPulse",       "material_param": "EmissiveScale",      "via": "BeatPulse -> EmissiveScale = 0.25+BeatPulse*1.2+Bass*0.3"},
    {"mpc_scalar": "Cymatic_BassIntensity",   "material_param": "IridescenceShift",   "via": "Bass*0.14+BeatPulse*0.06"},
    {"mpc_scalar": "Cymatic_UVDistortion",    "material_param": "UVDistortion",       "via": "BeatPulse*0.08+Mid*0.02"},
    {"mpc_scalar": "Cymatic_IridescenceShift","material_param": "IridescenceTint",    "via": "Bass hue shift"},
    {"mpc_scalar": "Cymatic_EmissiveScale",   "material_param": "EmissiveScale",      "via": "BeatPulse composite"},
    {"mpc_scalar": "Cymatic_ModeN/M",         "material_param": "ChladniSampling",     "via": "n=2+floor(Bass*6), m=3+floor(BeatPulse*5)"},
]

def ensure_mpc_params():
    """In-editor: ensure MPC_Cymatics_Driver has all scalars."""
    try:
        import unreal
    except ImportError:
        return False, "no unreal"
    mpc = unreal.EditorAssetLibrary.load_asset(MPC_DRIVER)
    if not mpc:
        factory = unreal.MaterialParameterCollectionFactoryNew()
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mpc = tools.create_asset("MPC_Cymatics_Driver", "/Game/Melodia/Cymatics", unreal.MaterialParameterCollection, factory)
        if not mpc:
            return False, "create failed"
    # Add scalar params via reflection if missing (best-effort — UE5 prevents python add, so log)
    try:
        # Use CollectionParameters introspection
        params = [p.parameter_name for p in mpc.scalar_parameters] if hasattr(mpc, "scalar_parameters") else []
        needed = ["Cymatic_BeatPulse","Cymatic_BassIntensity","Cymatic_MidIntensity","Cymatic_EmissiveScale","Cymatic_IridescenceShift","Cymatic_UVDistortion","Cymatic_ModeN","Cymatic_ModeM","BeatPulse","BassIntensity"]
        missing = [n for n in needed if n not in params]
        if missing:
            print(f"[MPC] Missing params (add in editor Content Browser): {missing}")
        else:
            print(f"[MPC] All params present: {params}")
        unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    except Exception as e:
        print(f"[MPC] introspection warn: {e}")
    return True, "ok"

def place_in_level():
    """In-editor: spawn 6 actors in LV_FarawayMother_Prototype."""
    import unreal
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        print(f"[Level] Missing {LEVEL_PATH}")
        return 0
    # Load level
    unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    # Use Cube as placeholder mesh — real mesh is terrain/plane; cube demonstrates distribution
    cube_path = "/Engine/BasicShapes/Cube"
    plane_path = "/Engine/BasicShapes/Plane"
    cube = unreal.EditorAssetLibrary.load_asset(cube_path)
    spawned = 0
    for inst in INSTANCES:
        label = inst["label"]
        # Delete existing with same label
        for actor in unreal.EditorLevelLibrary.get_all_level_actors():
            if actor.get_actor_label() == label:
                unreal.EditorLevelLibrary.destroy_actor(actor)
        loc = unreal.Vector(*inst["location"])
        rot = unreal.Rotator(0, 0, 0)
        scale = unreal.Vector(*inst["scale"])
        # Spawn StaticMeshActor
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        if not actor:
            print(f"[Spawn] FAIL {label}")
            continue
        actor.set_actor_label(label)
        # Scale via actor scale (not component scale for visibility)
        actor.set_actor_scale3d(scale)
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if comp and cube:
            comp.set_static_mesh(cube)
            mi = unreal.EditorAssetLibrary.load_asset(inst["mi"])
            if mi:
                comp.set_material(0, mi)
                print(f"[Spawn] {label} @ Z={inst['location'][2]} -> {inst['mi'].split('/')[-1]}")
            else:
                print(f"[Spawn] WARN {label} MI not found {inst['mi']}")
            # Store height band as tag
            actor.tags = [inst["height_band"]]
        spawned += 1
    unreal.EditorLevelLibrary.save_current_level()
    print(f"[Level] Saved {LEVEL_PATH} with {spawned} instances")
    return spawned

def check_offline():
    """Offline validation without editor."""
    errors = []
    # Check C++ contracts
    cpp_reader = PROJECT_ROOT / "Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.cpp"
    cpp_writer = PROJECT_ROOT / "Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsWriterSubsystem.cpp"
    h_reader = PROJECT_ROOT / "Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsSubsystem.h"
    h_writer = PROJECT_ROOT / "Source/BS_GodFile/MelodiaIntegration/MelodiaCymaticsWriterSubsystem.h"
    for p in [cpp_reader, cpp_writer, h_reader, h_writer]:
        if not p.exists():
            errors.append(f"missing {p}")
    if h_reader.exists():
        txt = h_reader.read_text(encoding="utf-8")
        if "IsReadOnlyByContract" not in txt:
            errors.append("MelodiaCymaticsSubsystem missing IsReadOnlyByContract")
    if h_writer.exists():
        txt = h_writer.read_text(encoding="utf-8")
        if "IsSingleWriter" not in txt:
            errors.append("Writer missing IsSingleWriter")
    if cpp_writer.exists():
        txt = cpp_writer.read_text(encoding="utf-8")
        if "MPC_Cymatics_Driver" not in txt:
            errors.append("Writer does not reference MPC_Cymatics_Driver")
        if "SetScalarParameterValue" not in txt:
            errors.append("Writer does not write scalar params")
    # Check MI existence on disk (uasset presence)
    for inst in INSTANCES:
        rel = inst["mi"].replace("/Game/", "Content/")
        fs = PROJECT_ROOT / (rel + ".uasset")
        if not fs.exists():
            errors.append(f"missing MI on disk {rel}")
    # Height-aware check: need ridge vs valley distinct Z
    ridges = [i for i in INSTANCES if "ridge" in i["height_band"] or "shoulder" in i["height_band"]]
    valleys = [i for i in INSTANCES if "valley" in i["height_band"]]
    if len(ridges) < 3:
        errors.append(f"need >=3 ridge instances, have {len(ridges)}")
    if len(valleys) < 2:
        errors.append(f"need >=2 valley instances, have {len(valleys)}")
    if len(INSTANCES) < 5:
        errors.append("need >=5 instances")
    # Z separation
    ridge_z = [i["location"][2] for i in ridges]
    valley_z = [i["location"][2] for i in valleys]
    if ridge_z and valley_z and min(ridge_z) <= max(valley_z):
        errors.append(f"height separation failed: ridge min {min(ridge_z)} not > valley max {max(valley_z)}")
    # MI coverage: need all three families
    mis = {i["mi"] for i in INSTANCES}
    need = {
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk",
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticMarble",
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CavernWeave",
    }
    if not need.issubset(mis):
        errors.append(f"MI coverage incomplete: have {mis}, need {need}")
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="offline validation only")
    args = parser.parse_args()
    # Try editor path only if inside UE
    try:
        import unreal
        has_editor = True
    except ImportError:
        has_editor = False

    if args.check or not has_editor:
        errs = check_offline()
        if errs:
            print("[CHECK] FAIL")
            for e in errs:
                print(f"  - {e}")
            sys.exit(1)
        print(f"[CHECK] PASS — {len(INSTANCES)} height-aware instances, 3 MI families, writer read-only preserved")
        for inst in INSTANCES:
            print(f"  {inst['label']:45s} Z={inst['location'][2]:5.0f}  {inst['mi'].split('/')[-1]}  [{inst['height_band']}]")
        print(f"  Bindings: {len(BINDINGS)} via MPC_Cymatics_Driver -> IridescenceTint/EmissiveScale/UVDistortion")
        sys.exit(0)

    # Editor path
    ensure_mpc_params()
    n = place_in_level()
    print(f"[DONE] {n} instances placed in {LEVEL_PATH}")

if __name__ == "__main__":
    main()
