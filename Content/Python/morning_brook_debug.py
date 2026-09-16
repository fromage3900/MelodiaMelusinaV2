import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_brook_debug.json"
rep = {}
al = unreal.EditorAssetLibrary

try:
    bp = al.load_asset(
        "/Oceanology_Plugin/Design/Lake/Blueprints/Lake/BP_OceanologyLake")
    cls = bp.generated_class()
    rep["lake_cls"] = str(cls.get_name())
    cube = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-950.0, 2300.0, -600.0),
        unreal.Rotator(0, 0, 0))
    rep["cube_probe"] = bool(cube)
    if cube:
        cube.set_actor_label("Dbg_CubeProbe_DELETE")
    lake2 = unreal.EditorLevelLibrary.spawn_actor_from_class(
        cls, unreal.Vector(-950.0, 2300.0, 2000.0), unreal.Rotator(0, 0, 0))
    rep["lake_high"] = bool(lake2)
    if lake2:
        lake2.set_actor_label("Morning_SheepDell_Lake")
        lake2.set_actor_scale3d(unreal.Vector(0.2, 0.2, 0.2))
except Exception as e:
    rep["lake_debug_err"] = str(e)[:250]

try:
    g = al.load_asset(
        "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden")
    nodes = g.get_editor_property("nodes")
    for n in nodes:
        cn = n.get_class().get_name()
        if "Spawn" in cn:
            rep["spawner_class"] = cn
            for prop in ("template_actor", "spawn_template", "actor_template",
                         "template", "actor_descriptor", "spawn_descriptor"):
                try:
                    v = n.get_editor_property(prop)
                    rep.setdefault("spawner_vals", {})[prop] = str(v)[:200]
                except Exception as e:
                    rep.setdefault("spawner_vals", {})[prop] = "NO " + str(e)[:80]
            break
    n0 = nodes[0]
    chain, c = [], n0.get_class()
    for _ in range(6):
        chain.append(c.get_name())
        try:
            c = c.get_super_struct()
        except Exception:
            break
        if c is None:
            break
    rep["node0_chain"] = chain
except Exception as e:
    rep["graph_debug_err"] = str(e)[:250]

open(OUT, "w").write(json.dumps(rep, indent=1))
print("BROOK_DEBUG_WROTE " + OUT)
