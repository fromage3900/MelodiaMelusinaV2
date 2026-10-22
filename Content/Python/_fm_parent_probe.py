import unreal, json
EAL = unreal.EditorAssetLibrary
paths = [
    "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha",
]
out = {}
for p in paths:
    out[p] = {
        "exists": EAL.does_asset_exist(p),
        "loaded": bool(EAL.load_asset(p)),
        "type": type(EAL.load_asset(p)).__name__ if EAL.load_asset(p) else None,
    }
# list Masters folder
try:
    out["masters"] = [a for a in EAL.list_assets("/Game/EnvSandbox/Materials/Masters", False, False) if "Nikki" in a or "Universal" in a][:30]
except Exception as e:
    out["list_err"] = str(e)
print("PAR " + json.dumps(out))
