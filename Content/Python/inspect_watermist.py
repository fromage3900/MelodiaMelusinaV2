"Inspect NS_Uni_WaterMist Niagara system structure."
import unreal

SYSTEM_PATH = "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_WaterMist"

def main():
    ns = unreal.load_asset(SYSTEM_PATH)
    if not ns:
        print("Could not load " + SYSTEM_PATH)
        return
    
    print("Loaded: " + SYSTEM_PATH)
    print("Class: " + ns.get_class().get_name())
    
    try:
        emitters = ns.get_editor_property("emitter_handles")
        print("Emitter handles: " + str(len(emitters) if emitters else 0))
        for i, em in enumerate(emitters or []):
            print("  [" + str(i) + "] " + (em.get_editor_property("emitter_name") if em else "None"))
            try:
                stages = em.get_editor_property("emitter_module_script_data") or {}
                print("      Module script data: " + str(stages))
            except Exception as e:
                print("      Error getting module script data: " + str(e))
            
            try:
                modules = em.get_editor_property("emitter_modules") or []
                print("      Modules: " + str(len(modules)))
                for m in modules:
                    print("        - " + (m.get_class().get_name() if m else "None"))
            except Exception as e:
                print("      Error getting modules: " + str(e))
    except Exception as e:
        print("Error getting emitter handles: " + str(e))
    
    try:
        user_params = ns.get_editor_property("user_parameters") or {}
        print("User parameters:")
        for name, param in user_params.items():
            print("  " + str(name) + ": " + str(param))
    except Exception as e:
        print("Error getting user parameters: " + str(e))

    try:
        emitter_data = ns.get_editor_property("EmitterCompressedData") or []
        print("EmitterCompressedData: " + str(len(emitter_data)))
        for i, ed in enumerate(emitter_data):
            print("  [" + str(i) + "] " + str(ed))
    except Exception as e:
        print("Error getting EmitterCompressedData: " + str(e))

if __name__ == "__main__":
    main()

