import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/rainbow_minimal.json"
rep = {}
al = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ELL = unreal.EditorLevelLibrary

try:
    g = al.duplicate_asset("/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell",
                           "/Game/EnvSandbox/PCG/House/PCG_RainbowBloom_Test")
    rep["duplicated"] = True
except Exception as e:
    rep["dup_err"] = str(e)[:200]
    open(OUT, "w").write(json.dumps(rep, indent=1))
    print("MINIMAL_WROTE")
    raise SystemExit
# prune everything
for x in list(g.get_editor_property("nodes")):
    try:
        g.remove_node(x)
    except Exception as e:
        rep.setdefault("prune_errs", []).append(str(e)[:100])
        break
rep["pruned"] = True
t = None
for a in svc.get_all_level_actors():
    try:
        if a.get_actor_label() == "PetalTemplate_R":
            t = a
            break
    except Exception:
        pass
try:
    grid = g.add_node_of_type(unreal.PCGCreatePointsGridSettings)[0]
    gs = grid.get_settings()
    gs.set_editor_property("grid_extents", unreal.Vector(400.0, 400.0, 200.0))
    gs.set_editor_property("cell_size", unreal.Vector(100.0, 100.0, 100.0))
    gs.set_editor_property("cull_points_outside_volume", False)
    rep["extents_rb"] = str(gs.get_editor_property("grid_extents"))
    rep["cell_rb"] = str(gs.get_editor_property("cell_size"))
    rep["cull_rb"] = str(gs.get_editor_property("cull_points_outside_volume"))
    sp = g.add_node_of_type(unreal.PCGSpawnActorSettings)[0]
    ss = sp.get_settings()
    ss.set_editor_property("template_actor", t)
    ss.set_editor_property("template_actor_class", unreal.StaticMeshActor)
    rep["template_rb"] = str(ss.get_editor_property("template_actor").get_actor_label())
    rep["class_rb"] = str(ss.get_editor_property("template_actor_class"))
    rep["wire"] = bool(g.add_edge(grid, "Out", sp, "In"))
except Exception as e:
    rep["build_err"] = str(e)[:200]
vol = ELL.spawn_actor_from_class(unreal.PCGVolume, unreal.Vector(-950.0, 2300.0, -415.0), unreal.Rotator(0, 0, 0))
vol.set_actor_label("RainbowBloom_TestVol")
vol.set_actor_scale3d(unreal.Vector(10.0, 10.0, 6.0))
comp = vol.get_component_by_class(unreal.PCGComponent)
comp.set_graph(g)
comp.generate(True)
rep["generated"] = True
open(OUT, "w").write(json.dumps(rep, indent=1))
print("MINIMAL_WROTE")
