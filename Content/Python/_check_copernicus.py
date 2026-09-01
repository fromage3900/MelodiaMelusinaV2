import unreal
import json

# Check what Copernicus assets still exist
result = {}

# Textures
tex_dir = "/Game/EnvSandbox/Textures/Copernicus/"
textures = unreal.EditorAssetLibrary.list_assets(tex_dir)
result["textures"] = len(textures)

# MIs
mi_dir = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
mis = unreal.EditorAssetLibrary.list_assets(mi_dir)
result["mis"] = len(mis)
result["mi_names"] = [m.split("/")[-1] for m in mis]

print(json.dumps(result, indent=2))
