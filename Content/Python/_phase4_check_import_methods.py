import unreal, json
tools = unreal.AssetToolsHelpers.get_asset_tools()
methods = [m for m in dir(tools) if 'import' in m.lower() or 'asset' in m.lower()]
print(json.dumps({"import_methods": methods}))
