import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_bypass.json"
rep = {}
al = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

g = al.load_asset("/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell")
nodes = {}
for n in g.get_editor_property("nodes"):
    try:
        nodes[str(n.get_path_name()).split(":")[-1]] = n
    except Exception:
        pass
grids = sorted([k for k in nodes if k.startswith("CreatePointsGrid_")])
rays = sorted([k for k in nodes if k.startswith("WorldRaycast_")])
spawners = sorted([k for k in nodes if k.startswith("SpawnActor_")])
# band R = first of each
try:
    rs = nodes[rays[0]].get_settings()
    try:
        rep["keep_original_before"] = str(rs.get_editor_property("keep_original_point_on_miss"))
    except Exception as e:
        rep["keep_original_before"] = "READERR " + str(e)[:100]
except Exception as e:
    rep["ray_err"] = str(e)[:150]
try:
    r = g.remove_edge(nodes[rays[0]], "Out", nodes[spawners[0]], "In")
    rep["unwire_ray"] = bool(r)
except Exception as e:
    rep["unwire_err"] = str(e)[:150]
try:
    r = g.add_edge(nodes[grids[0]], "Out", nodes[spawners[0]], "In")
    rep["wire_direct"] = bool(r)
except Exception as e:
    rep["wire_err"] = str(e)[:150]
# spawner R input edge count
try:
    pins = list(nodes[spawners[0]].get_editor_property("input_pins"))
    rep["spawner_inputs"] = [[p.get_name(), len(list(p.get_editor_property("edges")))] for p in pins[:3]]
except Exception as e:
    rep["spawner_pins_err"] = str(e)[:120]
open(OUT, "w").write(json.dumps(rep, indent=1))
print("BYPASS_WROTE")
