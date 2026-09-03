"""Check Melusina level + MPC emissive + dirty packages."""
import unreal

# 1. Find Melusina in level
print("=== Melusina Level Actor Materials ===")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if les.load_level("/Game/L_MelusinaMorning"):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors() or []:
        if "Melusina" in a.get_actor_label():
            print(f"ACTOR: {a.get_actor_label()} CLASS: {a.get_class().get_name()}")
            try:
                mesh = a.get_editor_property("mesh")
                if mesh:
                    mats = mesh.get_editor_property("materials") or []
                    for i, m in enumerate(mats):
                        print(f"  SLOT{i}: {m.get_name() if m else 'NONE'}")
            except Exception as ex:
                print(f"  mesh error: {str(ex)[:100]}")
            break
    print("DONE")
else:
    print("FAIL: could not load level")

# 2. Check MPC emissive values
print("\n=== MPC Emissive Values ===")
mpc = unreal.load_asset("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette")
if mpc:
    for s in mpc.get_editor_property("scalar_parameters"):
        n = str(s.get_editor_property("parameter_name"))
        if any(x in n.lower() for x in ["emissive", "bloom", "global", "beat", "react", "tension"]):
            print(f"  {n} = {s.get_editor_property('default_value')}")

# 3. Check dirty packages
print("\n=== Dirty Packages ===")
dirty = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_editor_property("...")
# Actually list_dirty_packages is a static method
for pkg in unreal.SystemLibrary.get_dirty_packages() or []:
    print(f"  {pkg.get_name()}")
