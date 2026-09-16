import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/morning_graph_census.json"
graphs = [
    "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_MandalaBloom",
    "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden",
    "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Nikki_PhyllotaxisGarden_Walkable",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BezierColonnadeAvenue",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_BezierVistaTerrace",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_WallGardenPath",
    "/Game/EnvSandbox/PCG/Styles/Baroque/PCG_TerraceGarden",
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisBiome",
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_East_PhyllotaxisCourtyard",
    "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Hero_TeaGarden",
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_BellTreeGarden",
]
al = unreal.EditorAssetLibrary
out = {}
for gp in graphs:
    g = al.load_asset(gp)
    if g is None:
        out[gp.split("/")[-1]] = "MISSING"
        continue
    try:
        nodes = g.get_editor_property("nodes")
        names = [n.get_class().get_name() for n in nodes]
        out[gp.split("/")[-1]] = {
            "nodes": len(nodes),
            "spawners": names.count("PCGSpawnActorNode"),
            "mesh_spawners": sum(1 for s in names if "StaticMesh" in s or "Spawner" in s),
        }
    except Exception as e:
        out[gp.split("/")[-1]] = "ERR " + str(e)[:120]
open(OUT, "w").write(json.dumps(out, indent=1))
print("GRAPH_CENSUS_WROTE")
