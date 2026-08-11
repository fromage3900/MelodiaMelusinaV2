import unreal

ASSET = "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro"
BP = "BP_MelodiaSirMelodiousMorningIntro"


def node_path(name):
    return ASSET + "." + BP + ":EventGraph." + name


for nid in ("K2Node_CreateDelegate_3", "K2Node_CreateDelegate_0"):
    o = unreal.find_object(None, node_path(nid))
    print("====", nid, o)
    if o:
        print("class:", o.get_class().get_name())
        print("dir:", [m for m in dir(o) if not m.startswith("_")])
        for prop in ("DelegateFunction", "FunctionReference", "DelegateFunctionName", "FunctionToCall", "Reference"):
            try:
                v = o.get_editor_property(prop)
                print("  ", prop, "=", v)
            except Exception as e:
                print("  ", prop, "ERR", e)
