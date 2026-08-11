import unreal

ASSET = "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro"
BP = "BP_MelodiaSirMelodiousMorningIntro"


def node_path(name):
    return ASSET + "." + BP + ":EventGraph." + name


o0 = unreal.find_object(None, node_path("K2Node_CreateDelegate_0"))
o0.set_create_delegate_function("HandleBattleCompleted")
print("set0:", o0.get_create_delegate_function())

o3 = unreal.find_object(None, node_path("K2Node_CreateDelegate_3"))
o3.set_create_delegate_function("HandleBattleRequested")
print("set3:", o3.get_create_delegate_function())

bp = unreal.load_asset(ASSET)
unreal.EditorAssetLibrary.save_asset(ASSET, only_if_is_dirty=True)
print("saved:", unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=True))
