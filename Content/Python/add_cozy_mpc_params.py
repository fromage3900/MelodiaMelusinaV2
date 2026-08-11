"""Add cozy MPC scalar parameters to MPC_Melodia_Palette.

Run headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/.../Content/Python/add_cozy_mpc_params.py"
"""

import unreal

MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

COZY_SCALARS = [
    ("WarmthGlow", 0.0),
    ("PetalFallIntensity", 0.0),
    ("DreamRipple", 0.0),
    ("EmberDance", 0.0),
    ("CozyBloom", 0.0),
]

mpc = unreal.EditorAssetLibrary.load_asset(MPC_PATH)
if not mpc:
    unreal.log_error(f"[CozyMPC] Could not load {MPC_PATH}")
    exit(1)

existing = {s.get_editor_property("parameter_info").name
            for s in mpc.get_editor_property("scalar_parameters")}

added = []
skipped = []
for name, default in COZY_SCALARS:
    if name in existing:
        try:
            mpc.set_scalar_parameter_default_value(name, default)
            skipped.append(name)
        except Exception as e:
            unreal.log_warning(f"[CozyMPC] Could not set default for {name}: {e}")
    else:
        try:
            param = unreal.CollectionScalarParameter()
            param.parameter_name = name
            param.default_value = default
            mpc.add_scalar_parameter(param)
            added.append(name)
        except Exception as e:
            unreal.log_warning(f"[CozyMPC] Could not add {name}: {e}")

unreal.EditorAssetLibrary.save_loaded_asset(mpc)

unreal.log(f"[CozyMPC] Added {len(added)} params: {added}")
unreal.log(f"[CozyMPC] Already existed (defaults refreshed): {skipped}")
unreal.log(f"[CozyMPC] Total scalars now: {len(mpc.get_editor_property('scalar_parameters'))}")
