import unreal, json
# find Morning asset path
EAL = unreal.EditorAssetLibrary
cands = []
for root in ["/Game/Melodia", "/Game/EnvSandbox", "/Game"]:
    try:
        assets = EAL.list_assets(root, recursive=True, include_folder=False)
    except Exception:
        continue
    for a in assets:
        if "L_MelusinaMorning" in a:
            cands.append(a.split(".")[0])
print("MAPS " + json.dumps(sorted(set(cands))))
