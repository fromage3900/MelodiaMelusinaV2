import unreal
ar=unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_all_assets():
 p=str(a.object_path)
 if any(k in p.lower() for k in ['volume','teleport','trigger','transition','encounter']): print(p)
