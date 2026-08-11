
import unreal
import json

result = {}
dirs = [
    "/Game/Melodia/Characters/Melusina/Animations",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap",
]
melusina_skel = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"

for d in dirs:
    assets = unreal.EditorAssetLibrary.list_assets(d, False, False)
    for ap in assets:
        obj = unreal.load_asset(ap)
        if obj and obj.get_class().get_name() == "AnimSequence":
            skel = obj.get_editor_property("skeleton")
            if skel and skel.get_path_name() == melusina_skel:
                name = ap.split("/")[-1].split(".")[0]
                result[name] = 1

print(json.dumps(list(result.keys())))
