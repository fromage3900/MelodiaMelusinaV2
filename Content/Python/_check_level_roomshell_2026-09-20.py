import unreal, json
world = unreal.EditorLevelLibrary.get_editor_world()
out = {
    "world": world.get_path_name() if world else None,
    "map": unreal.EditorLevelLibrary.get_editor_world().get_name() if world else None,
}
# find SM_room_2
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
hits = []
room2 = []
for a in svc.get_all_level_actors():
    lab = a.get_actor_label() or ""
    name = a.get_name()
    if "SM_room_2" in lab or "SM_room_2" in name or lab == "SM_room_2":
        t = a.get_actor_location()
        room2.append({"label": lab, "name": name, "loc": [round(t.x,1), round(t.y,1), round(t.z,1)]})
    if "HouseRoom" in lab or "RoomShell" in lab or "WC_House" in lab:
        t = a.get_actor_location()
        hits.append({"label": lab, "name": name, "loc": [round(t.x,1), round(t.y,1), round(t.z,1)], "class": a.get_class().get_name()})
out["SM_room_2"] = room2
out["house_hits"] = hits[:40]
out["actor_count"] = len(list(svc.get_all_level_actors()))
print("LVL " + json.dumps(out))
