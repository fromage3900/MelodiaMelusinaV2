import unreal, json
GRAPH = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
out = {"regen": False}
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out["world"] = world.get_name() if world else None
if out["world"] != "L_MelusinaMorning":
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level("/Game/Melodia/Levels/Opening/L_MelusinaMorning")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    out["world"] = world.get_name() if world else None
graph = unreal.EditorAssetLibrary.load_asset(GRAPH)
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in svc.get_all_level_actors():
    if (a.get_actor_label() or "") == "WC_HouseRoomShell_SalonA":
        t = a.get_actor_location()
        out["loc"] = [round(t.x,1), round(t.y,1), round(t.z,1)]
        for c in (a.get_components_by_class(unreal.PCGComponent) or []):
            try:
                c.set_graph(graph)
            except Exception:
                pass
            try:
                g = c.get_graph()
                out["get_graph"] = g.get_path_name() if g else None
            except Exception as e:
                out["get_graph_err"] = str(e)
            try:
                c.cleanup_local_generation()
            except Exception:
                pass
            try:
                c.generate(True)
                out["regen"] = True
            except Exception as e:
                out["regen_err"] = str(e)
        break
try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    out["level_saved"] = True
except Exception as e:
    out["level_save_err"] = str(e)
print("REGEN " + json.dumps(out))
