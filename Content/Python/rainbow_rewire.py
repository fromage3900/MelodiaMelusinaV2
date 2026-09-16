import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_rewire.json"
rep = {"wires": []}
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
rep["found"] = {"grids": grids, "rays": rays, "spawners": spawners}
for gr, ra, sp in zip(grids, rays, spawners):
    rec = {"branch": [gr, ra, sp]}
    try:
        ok1 = g.add_edge(nodes[gr], "Out", nodes[ra], "Origins")
        ok2 = g.add_edge(nodes[ra], "Out", nodes[sp], "In")
        rec["wired"] = [bool(ok1), bool(ok2)]
    except Exception as e:
        rec["err"] = str(e)[:200]
    rep["wires"].append(rec)

by_label = {}
for a in svc.get_all_level_actors():
    try:
        by_label[a.get_actor_label()] = a
    except Exception:
        pass
fvol = by_label.get("RainbowBloom_Field")
try:
    comp = fvol.get_component_by_class(unreal.PCGComponent)
    comp.generate(True)
    rep["generated"] = True
except Exception as e:
    rep["generate_err"] = str(e)[:200]
open(OUT, "w").write(json.dumps(rep, indent=1))
print("REWIRE_WROTE")
