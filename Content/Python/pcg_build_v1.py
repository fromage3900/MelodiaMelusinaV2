import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/pcg_build_v1.json"
rep = {"steps": []}
al = unreal.EditorAssetLibrary
g = al.load_asset("/Game/EnvSandbox/PCG/House/PCG_MelusinaHouse_MorningDell")


def step(name, fn):
    try:
        r = fn()
        rep["steps"].append(name + " OK " + str(r)[:160])
        return r
    except Exception as e:
        rep["steps"].append(name + " ERR " + str(e)[:220])
        return None


nodes = g.get_editor_property("nodes")
rep["steps"].append("start_count=%d" % len(nodes))
# keep the CreatePoints_0 we added (last), remove the 14 borrowed
doomed = [n for n in nodes
          if "CreatePoints_0" not in str(n.get_path_name())]
rep["steps"].append("doomed=%d" % len(doomed))
r = step("remove_borrowed", lambda: g.remove_nodes(doomed))
nodes = g.get_editor_property("nodes")
rep["steps"].append("after_strip=%d" % len(nodes))

spawner = step("add_spawner",
              lambda: g.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings))
sampler = step("add_sampler",
               lambda: g.add_node_of_type(unreal.PCGSurfaceSamplerSettings))
vol = step("add_volume_in",
           lambda: g.add_node_of_type(unreal.PCGGetVolumeSettings))
if spawner is not None:
    node = spawner[0] if isinstance(spawner, tuple) else spawner
    try:
        attrs = [m for m in dir(node) if not m.startswith("_")]
        rep["spawner_attrs"] = [m for m in attrs if any(
            k in m.lower() for k in ("mesh", "descript", "entry", "template",
                                     "spawn", "material"))][:20]
    except Exception as e:
        rep["spawner_attrs_err"] = str(e)[:150]
open(OUT, "w").write(json.dumps(rep, indent=1))
print("BUILDV1_WROTE")
