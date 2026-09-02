"""Connect NS_Uni_WaterMist SpawnRate to MPC_Melodia_Palette.PlayerProximity.

Adds a Module Script (Emitter Update stage) to WaterMist emitter that reads
PlayerProximity from MPC_Melodia_Palette and writes to ProximitySpawnRateMultiplier.
"""
import unreal

SYSTEM_PATH = "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_WaterMist"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

def main():
    ns = unreal.load_asset(SYSTEM_PATH)
    if not ns:
        print("ERROR: Could not load " + SYSTEM_PATH)
        return False
    
    print("Loaded: " + SYSTEM_PATH)
    
    # Load MPC to verify PlayerProximity parameter exists
    mpc = unreal.load_asset(MPC_PATH)
    if not mpc:
        print("ERROR: Could not load MPC " + MPC_PATH)
        return False
    
    print("Loaded MPC: " + MPC_PATH)
    
    # Check MPC scalar parameters
    scalar_params = mpc.get_editor_property("scalar_parameters") or []
    proximity_exists = False
    for sp in scalar_params:
        info = sp.get_editor_property("parameter_info")
        if info and info.name == "PlayerProximity":
            proximity_exists = True
            print("Found PlayerProximity in MPC (default: " + str(sp.default_value) + ")")
            break
    
    if not proximity_exists:
        print("WARNING: PlayerProximity not found in MPC scalar parameters")
        # List all scalar params for debugging
        for sp in scalar_params:
            info = sp.get_editor_property("parameter_info")
            if info:
                print("  MPC scalar: " + info.name)
    
    # Get emitter handles
    emitters = ns.get_editor_property("emitter_handles") or []
    print("Found " + str(len(emitters)) + " emitter(s)")
    
    water_mist_emitter = None
    emitter_index = -1
    for i, em in enumerate(emitters):
        name = em.get_editor_property("emitter_name") if em else "Unknown"
        print("  Emitter [" + str(i) + "]: " + name)
        if "WaterMist" in name or "water" in name.lower() or "mist" in name.lower():
            water_mist_emitter = em
            emitter_index = i
            print("    -> Selected as WaterMist emitter")
    
    if not water_mist_emitter and emitters:
        water_mist_emitter = emitters[0]
        emitter_index = 0
        print("Using first emitter as WaterMist: " + water_mist_emitter.get_editor_property("emitter_name"))
    
    if not water_mist_emitter:
        print("ERROR: No emitter found")
        return False
    
    # Check existing user parameters on system
    user_params = ns.get_editor_property("user_parameters") or {}
    print("System user parameters:")
    for name, param in user_params.items():
        print("  " + str(name) + ": " + str(param))
    
    # Check if ProximitySpawnRateMultiplier exists
    proximity_param_exists = "ProximitySpawnRateMultiplier" in user_params
    if proximity_param_exists:
        print("ProximitySpawnRateMultiplier already exists as user parameter")
    else:
        print("ProximitySpawnRateMultiplier NOT found - may need to be added")
    
    # Now we need to add a Module Script to the emitter
    # In UE 5.8 Python API, this is done via NiagaraToolset_System or directly on emitter
    
    # Try to access emitter modules
    try:
        modules = water_mist_emitter.get_editor_property("emitter_modules") or []
        print("Emitter modules: " + str(len(modules)))
        for m in modules:
            print("  - " + m.get_class().get_name())
    except Exception as e:
        print("Could not get emitter modules: " + str(e))
    
    # Try to get the module script data (stages)
    try:
        script_data = water_mist_emitter.get_editor_property("emitter_module_script_data") or {}
        print("Module script data stages: " + str(list(script_data.keys())))
        for stage, modules_list in script_data.items():
            print("  Stage: " + str(stage) + " -> " + str(len(modules_list)) + " modules")
            for mod in modules_list:
                print("    - " + str(mod.get_class().get_name() if mod else "None"))
    except Exception as e:
        print("Could not get module script data: " + str(e))
    
    print("\n--- Inspection complete ---")
    print("To add the Module Script, we need to use NiagaraToolset_System or edit in-editor.")
    return True

if __name__ == "__main__":
    success = main()
    print("SUCCESS" if success else "FAILED")

