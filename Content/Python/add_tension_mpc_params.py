"""Add tension/dread MPC scalar parameters to MPC_Melodia_Palette.

Counterpart to add_cozy_mpc_params.py -- the "cold" register that balances the
cozy warm set so the cute palette can cool as dread rises (OMORI saturated->muted
split, Decision 033, presentation-only). The C++ side
(UMelodiaRhythmReactivitySubsystem::Publish) already writes these names; a write
to a nonexistent MPC param is a safe no-op, so this can run before or after the
code rebuild.

Run headless (editor closed):
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/.../Content/Python/add_tension_mpc_params.py"
"""

import unreal

MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

TENSION_SCALARS = [
    # 0..1 smoothed "how dangerous right now" register; cools the palette.
    ("DreadPresence", 0.0),
    # 0 = Clear, 1 = Strain, 2 = Rupture continuous dissonance register.
    ("DissonanceAmount", 0.0),
]

mpc = unreal.EditorAssetLibrary.load_asset(MPC_PATH)
if not mpc:
    unreal.log_error(f"[TensionMPC] Could not load {MPC_PATH}")
    exit(1)

scalar_params = list(mpc.get_editor_property("scalar_parameters"))
existing = {s.get_editor_property("parameter_name")
            for s in scalar_params}

added = []
skipped = []
for name, default in TENSION_SCALARS:
    if name in existing:
        try:
            mpc.set_scalar_parameter_default_value(name, default)
            skipped.append(name)
        except Exception as e:
            unreal.log_warning(f"[TensionMPC] Could not set default for {name}: {e}")
    else:
        try:
            param = unreal.CollectionScalarParameter()
            param.set_editor_property("parameter_name", name)
            param.set_editor_property("default_value", default)
            scalar_params.append(param)
            added.append(name)
        except Exception as e:
            unreal.log_warning(f"[TensionMPC] Could not add {name}: {e}")

if added:
    mpc.set_editor_property("scalar_parameters", scalar_params)

unreal.EditorAssetLibrary.save_loaded_asset(mpc)

unreal.log(f"[TensionMPC] Added {len(added)} params: {added}")
unreal.log(f"[TensionMPC] Already existed (defaults refreshed): {skipped}")
unreal.log(f"[TensionMPC] Total scalars now: {len(mpc.get_editor_property('scalar_parameters'))}")