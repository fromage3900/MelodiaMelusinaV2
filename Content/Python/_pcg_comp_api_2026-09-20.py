import unreal, json
actor = None
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in svc.get_all_level_actors():
    if (a.get_actor_label() or "") == "WC_HouseRoomShell_SalonA":
        actor = a
        break
c = actor.get_component_by_class(unreal.PCGComponent)
info = {"methods": [m for m in dir(c) if "graph" in m.lower() or "Graph" in m]}
# try get_graph
for meth in ["get_graph", "GetGraph", "get_editor_property"]:
    info[meth] = hasattr(c, meth)
try:
    g = c.get_graph()
    info["get_graph"] = g.get_path_name() if g else None
except Exception as e:
    info["get_graph_err"] = str(e)
# try GraphInstance / local
for prop in ["graph", "Graph", "graph_local", "graph_instance", "instance"]:
    try:
        v = c.get_editor_property(prop)
        info["prop_"+prop] = str(v)[:200]
    except Exception as e:
        info["prop_"+prop] = "ERR:"+str(e)[:120]
print("PCGAPI " + json.dumps(info))
