import unreal, json
out = {"matches": [], "bp_instances": []}
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in svc.get_all_level_actors():
    try:
        lab = a.get_actor_label() or ""
        name = a.get_name()
        cls = a.get_class().get_name()
    except Exception:
        continue
    blob = (lab + " " + name + " " + cls).lower()
    if any(k in blob for k in ["roomshell", "salona", "melusinaroomshell", "houseroomshell"]):
        t = a.get_actor_location()
        out["matches"].append({
            "label": lab, "name": name, "class": cls,
            "loc": [round(t.x,1), round(t.y,1), round(t.z,1)],
            "hidden": a.is_hidden_ed(),
        })
    if "MelusinaRoomShell" in cls or "BP_MelusinaRoomShell" in cls:
        t = a.get_actor_location()
        comps = []
        for c in (a.get_components_by_class(unreal.PCGComponent) or []):
            g = None
            try:
                g = c.get_editor_property("graph")
            except Exception:
                pass
            comps.append({"name": c.get_name(), "graph": g.get_path_name() if g else None})
        out["bp_instances"].append({
            "label": lab, "name": name, "class": cls,
            "loc": [round(t.x,1), round(t.y,1), round(t.z,1)],
            "pcg": comps,
        })
# near SM_room_2
near = []
for a in svc.get_all_level_actors():
    t = a.get_actor_location()
    if abs(t.x - 461) < 50 and abs(t.y - 575) < 50 and abs(t.z + 222) < 80:
        near.append({
            "label": a.get_actor_label(),
            "name": a.get_name(),
            "class": a.get_class().get_name(),
            "loc": [round(t.x,1), round(t.y,1), round(t.z,1)],
        })
out["near_anchor"] = near[:30]
print("VERIFY2 " + json.dumps(out))
