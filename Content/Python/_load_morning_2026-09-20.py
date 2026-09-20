import unreal, json, time
LEVEL = "/Game/Melodia/Levels/Opening/L_MelusinaMorning"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ok = les.load_level(LEVEL)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
# wait briefly for WP
out = {"load_ok": bool(ok), "world": world.get_name() if world else None}
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# count
actors = list(svc.get_all_level_actors())
out["actor_count"] = len(actors)
room2 = []
for a in actors:
    lab = a.get_actor_label() or ""
    if "SM_room_2" in lab or a.get_name().startswith("SM_room_2"):
        t = a.get_actor_location()
        room2.append({"label": lab, "loc": [round(t.x,1), round(t.y,1), round(t.z,1)]})
out["SM_room_2"] = room2
shells = []
for a in actors:
    lab = a.get_actor_label() or ""
    if "RoomShell" in lab or "SalonA" in lab:
        t = a.get_actor_location()
        shells.append({"label": lab, "loc": [round(t.x,1), round(t.y,1), round(t.z,1)], "class": a.get_class().get_name()})
out["shells"] = shells
print("LOAD " + json.dumps(out))
