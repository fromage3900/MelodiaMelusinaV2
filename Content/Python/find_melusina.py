"""Find Melusina in levels."""
import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for lp in ["/Game/L_MelusinaMorning", "/Game/Melodia/Levels/Opening/L_MelusinaMorning"]:
    if les.load_level(lp):
        found = False
        for a in eas.get_all_level_actors() or []:
            if "Melusina" in a.get_actor_label():
                found = True
                cls = a.get_class().get_name()
                print(f"{lp.split('/')[-1]}: {a.get_actor_label()} ({cls})")
                try:
                    mesh = a.get_editor_property("mesh")
                    if mesh:
                        for i, m in enumerate(mesh.get_editor_property("materials") or []):
                            print(f"  SLOT{i}: {m.get_name() if m else 'NONE'}")
                except:
                    try:
                        # Try skeletal mesh
                        smesh = a.get_editor_property("skeletal_mesh")
                        if smesh:
                            for i, m in enumerate(smesh.get_editor_property("materials") or []):
                                print(f"  SKSLOT{i}: {m.get_name() if m else 'NONE'}")
                    except:
                        print("  (no mesh property)")
        if not found:
            print(f"{lp.split('/')[-1]}: NO Melusina actor found")
    else:
        print(f"{lp.split('/')[-1]}: COULD NOT LOAD")
