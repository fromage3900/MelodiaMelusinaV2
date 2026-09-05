"""Add Horizon Eater + Faraway LOD destruction MPC scalars to MPC_Melodia_Palette.

Adds HorizonEatAmount / DestructionAmount / HorizonTension (aliases) so the
horizon-eater horizon kill and faraway LOD dithered destruction have a single
tunable bus. Mirrors add_tension_mpc_params.py pattern (safe no-op if exists,
single writer remains UMelodiaAudioReactivePresentationSubsystem).

Writes to /Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette (or legacy
 /Game/EnvSandbox/Materials/MPC_Melodia_Palette fallback).

Run headless (editor closed preferred):
  UnrealEditor-Cmd.exe BS_GodFile.uproject -ExecutePythonScript="Content/Python/add_horizon_eater_mpc_params.py"

Guardrails: writes are additive; existing values preserved; new defaults 0.0.
"""
import unreal

CANDIDATE_PATHS = [
    "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette",
    "/Game/EnvSandbox/Materials/MPC_Melodia_Palette",
    "/Game/Melodia/MPC_Melodia_Palette",
]

# Scalar name, default — 0..1 bus
HORIZON_SCALARS = [
    ("HorizonEatAmount", 0.0),   # 0 pristine horizon, 1 eaten/membrane. Primary.
    ("DestructionAmount", 0.0),  # Faraway local alias (can be HorizonEat*0.9)
    ("HorizonTension", 0.0),     # WorldField.Tension mirror for horizon-eater
    # Optional comfort: keep DreadPresence if callers already drive Tension there
    ("WorldHorizonEat", 0.0),
]

mpc = None
mpc_path = None
for p in CANDIDATE_PATHS:
    a = unreal.EditorAssetLibrary.load_asset(p)
    if a:
        mpc = a
        mpc_path = p
        break

if not mpc:
    unreal.log_error(f"[HorizonMPC] Could not load any of {CANDIDATE_PATHS}. Tried all.")
    # List what does exist for debugging
    try:
        found = unreal.EditorAssetLibrary.list_assets("/Game", recursive=True, include_folder=False)
        mpcs = [x for x in found if "MPC" in x]
        unreal.log_warning(f"[HorizonMPC] Found MPC-like assets: {mpcs[:10]}")
    except Exception as e:
        unreal.log_warning(f"[HorizonMPC] list_assets failed: {e}")
    # Do not exit with code 1 in pure-python check — raise for editor runner
    raise SystemExit(1)

scalar_params = list(mpc.get_editor_property("scalar_parameters"))
existing = {s.get_editor_property("parameter_name"): s for s in scalar_params}

added = []
refreshed = []
for name, default in HORIZON_SCALARS:
    if name in existing:
        try:
            mpc.set_scalar_parameter_default_value(name, default)
            refreshed.append(name)
        except Exception as e:
            unreal.log_warning(f"[HorizonMPC] refresh {name}: {e}")
    else:
        try:
            p = unreal.CollectionScalarParameter()
            p.set_editor_property("parameter_name", name)
            p.set_editor_property("default_value", float(default))
            scalar_params.append(p)
            added.append(name)
        except Exception as e:
            unreal.log_warning(f"[HorizonMPC] add {name}: {e}")

if added:
    mpc.set_editor_property("scalar_parameters", scalar_params)

# Also ensure audio tension scalars exist (reuse from tension script — harmless)
for name in ["DreadPresence", "DissonanceAmount"]:
    if name not in {s.get_editor_property("parameter_name") for s in scalar_params}:
        unreal.log(f"[HorizonMPC] note: {name} not on MPC — add_tension_mpc_params.py will add it")

unreal.EditorAssetLibrary.save_loaded_asset(mpc)
n = len(mpc.get_editor_property("scalar_parameters"))
unreal.log(f"[HorizonMPC] {mpc_path}: added {added}, refreshed {refreshed}, total scalars now {n}")
# Print binding contract for log
unreal.log("[HorizonMPC] Contract: UMelodiaAudioReactivePresentationSubsystem is sole writer of HorizonEatAmount/DestructionAmount/HorizonTension. MIs + UMelodiaCymaticsSubsystem read-only.")
