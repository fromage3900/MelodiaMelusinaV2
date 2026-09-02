import unreal

# Fix up ObjectRedirectors under Atlantis (rename_asset left one for BuildingF)
tools = unreal.AssetToolsHelpers.get_asset_tools()
ar = unreal.AssetRegistryHelpers.get_asset_registry()

redirs = []
for a in ar.get_assets_by_path('/Game/EnvSandbox/Meshes/Atlantis', recursive=True):
    cls = str(a.asset_class_path)
    if 'ObjectRedirector' in cls:
        asset = a.get_asset()
        if asset is not None:
            redirs.append(asset)

unreal.log_warning('FIXUP_REDIRECTORS_V2 count=%d' % len(redirs))
if redirs:
    tools.fix_up_redirectors(redirs)
    unreal.log_warning('FIXUP_REDIRECTORS_V2 done')
else:
    unreal.log_warning('FIXUP_REDIRECTORS_V2 none')