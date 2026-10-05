"""Set Horizon Eater scalar params on MPC_Melodia_Palette.

MPC stores parameters in a struct array (ScalarParameters), not direct properties.
This script appends HorizonEatAmount, HorizonTension, DestructionAmount to the array.

Run inside UE Editor via Monolith (editor_query:run_python):
  import set_horizon_mpc_params
  import importlib
  importlib.reload(set_horizon_mpc_params)
  set_horizon_mpc_params.set_params()
"""
from __future__ import annotations

import unreal

MPC_PATH = "/Game/_PROJECT/04_Materials/MPC_Melodia_Palette"

HORIZON_PARAMS = {
    "HorizonEatAmount": 0.6,
    "HorizonTension": 0.8,
    "DestructionAmount": 0.3,
}


def _log(msg: str):
    unreal.log(f"[Horizon MPC] {msg}")


def set_params() -> dict:
    """Add horizon scalar params to MPC_Melodia_Palette."""
    mpc = unreal.EditorAssetLibrary.load_asset(MPC_PATH)
    if mpc is None:
        raise RuntimeError(f"MPC not found: {MPC_PATH}")

    _log(f"Loaded MPC: {mpc.get_name()}")

    # Get current scalar parameters
    current_params = mpc.get_editor_property("ScalarParameters")
    _log(f"Current scalar count: {len(current_params)}")

    # Check which horizon params already exist
    existing_names = set()
    for p in current_params:
        name = p.get_editor_property("ParameterName")
        existing_names.add(name)

    _log(f"Existing params: {existing_names}")

    # Add missing horizon params
    new_params = list(current_params)
    added = []
    for param_name, default_val in HORIZON_PARAMS.items():
        if param_name not in existing_names:
            # Create a new CollectionScalarParameter struct
            new_param = unreal.CollectionScalarParameter()
            new_param.set_editor_property("ParameterName", param_name)
            new_param.set_editor_property("DefaultValue", default_val)
            new_params.append(new_param)
            added.append(param_name)
            _log(f"  Added: {param_name} = {default_val}")
        else:
            _log(f"  Already exists: {param_name}")

    if added:
        # Set the updated array back
        mpc.set_editor_property("ScalarParameters", new_params)
        unreal.EditorAssetLibrary.save_loaded_asset(mpc)
        _log(f"Saved MPC with {len(new_params)} scalar params")
    else:
        _log("No new params to add")

    # Verify
    updated_params = mpc.get_editor_property("ScalarParameters")
    _log(f"Final scalar count: {len(updated_params)}")

    result = {
        "mpc": MPC_PATH,
        "added": added,
        "total_scalars": len(updated_params),
    }
    _log(f"Result: {result}")
    return result


if __name__ == "__main__":
    set_params()
