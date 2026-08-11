
import unreal
import json

result = {}
dirs = [
    "/Game/Melodia/Characters/Melusina/Animations",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap",
]
for d in dirs:
    assets = unreal.EditorAssetLibrary.list_assets(d, False, False)
    for ap in assets:
        obj = unreal.load_asset(ap)
        if obj and obj.get_class().get_name() == "AnimSequence":
            skel = obj.get_editor_property("skeleton")
            skel_name = skel.get_name() if skel else "None"
            nframes = obj.get_editor_property("num_frames")
            name = ap.split("/")[-1].split(".")[0]
            if skel:
                result[name] = {"skeleton": skel_name, "frames": nframes}

print(json.dumps(result))
