import unreal, json
EAL = unreal.EditorAssetLibrary
hits = []
for root in ["/Game/EnvSandbox", "/Game/Melodia"]:
    try:
        assets = EAL.list_assets(root, recursive=True, include_folder=False)
    except Exception:
        continue
    for a in assets:
        if "/BP_" in a or a.endswith("BP_"):
            pass
# Search PCGVolume usages / known hosts
cands = []
for root in ["/Game/EnvSandbox", "/Game/Melodia", "/Game"]:
    try:
        assets = EAL.list_assets(root, recursive=True, include_folder=False)
    except Exception:
        continue
    for a in assets:
        base = a.split(".")[0]
        name = base.rsplit("/", 1)[-1]
        if name.startswith("BP_") and any(k in name.lower() for k in ["pcg", "room", "house", "volume"]):
            cands.append(base)
print("CANDS " + json.dumps(sorted(set(cands))[:60]))
# Inspect SubobjectDataSubsystem methods
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
print("SDS_METHODS " + ",".join([m for m in dir(sds) if not m.startswith("_")][:80]))
lib = unreal.SubobjectDataBlueprintFunctionLibrary
print("LIB_METHODS " + ",".join([m for m in dir(lib) if "object" in m.lower() or "assoc" in m.lower() or "sub" in m.lower()][:40]))
