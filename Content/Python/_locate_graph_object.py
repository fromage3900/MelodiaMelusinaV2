import unreal

ASSET = "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro"
BP = "BP_MelodiaSirMelodiousMorningIntro"

candidates = [
    ASSET + "." + BP + ".EventGraph.K2Node_CreateDelegate_0",
    ASSET + ".EventGraph.K2Node_CreateDelegate_0",
    ASSET + "." + BP + ".EventGraph",
    ASSET + ".EventGraph",
]

for p in candidates:
    o = unreal.load_object(None, p)
    print("load_object:", p, "->", o)
    if o:
        print("   class:", o.get_class().get_name())

# try find_object variants
for p in candidates:
    o = unreal.find_object(None, p)
    print("find_object:", p, "->", o)