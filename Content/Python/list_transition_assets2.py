import unreal
ar=unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_all_assets():
 p=str(a.package_name)
 if any(k in p.lower() for k in ['volume','teleport','trigger','transition','encounter']): print(p,str(a.asset_name),str(a.asset_class))
