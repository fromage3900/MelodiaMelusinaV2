import unreal
import json

# Check what types the kitbash cathedral pieces are
cathedral_dir = "/Game/EnvSandbox/Meshes/Cathedral/"
assets = unreal.EditorAssetLibrary.list_assets(cathedral_dir)
print(f"Assets in Cathedral dir: {len(assets)}")
for a in sorted(assets)[:30]:
    obj = unreal.EditorAssetLibrary.load_asset(a)
    if obj:
        print(f"  {type(obj).__name__:30s} {a}")
    else:
        print(f"  {'(could not load)':30s} {a}")
