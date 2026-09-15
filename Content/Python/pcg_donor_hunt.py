import unreal, json

OUT = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/pcg_donor_hunt.json"
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
    "/Game/EnvSandbox/PCG/Styles/SeaAbove/PCG_SeaAbove_BellTreeGarden",
    "/Game/EnvSandbox/PCG/Styles/Sakura/PCG_Hero_TeaGarden",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_BellTreeGarden",
    "/Game/EnvSandbox/PCG/Musical/Hero/PCG_Hero_ArpeggioBridge",
]
al = unreal.EditorAssetLibrary
out = {}
for gp in graphs:
    try:
        g = al.load_asset(gp)
        if g is None:
            out[gp.split("/")[-1]] = "MISSING"
            continue
        names = [str(n.get_path_name()).split(":")[-1]
                 for n in g.get_editor_property("nodes")]
        out[gp.split("/")[-1]] = names
    except Exception as e:
        out[gp.split("/")[-1]] = "ERR " + str(e)[:120]
open(OUT, "w").write(json.dumps(out, indent=1))
print("DONORHUNT_WROTE")
