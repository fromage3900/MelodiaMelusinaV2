import unreal, json
out = {}
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out["world"] = world.get_name() if world else None
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in svc.get_all_level_actors():
    if (a.get_actor_label() or "") == "WC_HouseRoomShell_SalonA":
        t = a.get_actor_location()
        comps = []
        for c in (a.get_components_by_class(unreal.PCGComponent) or []):
            g = None
            try:
                g = c.get_editor_property("graph")
            except Exception:
                pass
            gen = None
            try:
                gen = c.get_editor_property("generated")
            except Exception:
                pass
            comps.append({
                "name": c.get_name(),
                "graph": g.get_path_name() if g else None,
            })
        out["actor"] = {
            "label": a.get_actor_label(),
            "class": a.get_class().get_name(),
            "loc": [round(t.x,1), round(t.y,1), round(t.z,1)],
            "pcg": comps,
        }
        break
print("POST " + json.dumps(out))
