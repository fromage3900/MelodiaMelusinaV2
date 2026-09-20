import unreal, json
graph_path = "/Game/EnvSandbox/PCG/House/PCG_MelusinaRoomShell_PCGex"
out = {"actors": []}
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in svc.get_all_level_actors():
    lab = a.get_actor_label() or ""
    if "RoomShell" in lab or "SalonA" in lab:
        t = a.get_actor_location()
        comps = []
        for c in (a.get_components_by_class(unreal.PCGComponent) or []):
            g = None
            try:
                g = c.get_editor_property("graph")
            except Exception:
                pass
            comps.append({
                "name": c.get_name(),
                "graph": g.get_path_name() if g else None,
            })
        out["actors"].append({
            "label": lab,
            "class": a.get_class().get_name(),
            "loc": [round(t.x,1), round(t.y,1), round(t.z,1)],
            "pcg": comps,
        })
out["graph_exists"] = unreal.EditorAssetLibrary.does_asset_exist(graph_path)
print("VERIFY " + json.dumps(out))
