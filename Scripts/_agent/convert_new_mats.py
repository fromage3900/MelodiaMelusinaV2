import json, unreal

MASTER = unreal.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal")
PALETTES = {
    "nature": (0.40, 0.42, 0.52, 0.78, 0.88, 0.78, 1.0, 0.98, 0.93),
    "musical": (0.42, 0.36, 0.48, 0.93, 0.85, 0.72, 1.0, 0.97, 0.90),
    "medieval": (0.38, 0.34, 0.46, 0.86, 0.80, 0.90, 1.0, 0.96, 0.92),
    "castle": (0.36, 0.33, 0.44, 0.84, 0.80, 0.88, 0.99, 0.97, 0.94),
    "cave": (0.30, 0.28, 0.40, 0.72, 0.70, 0.82, 0.95, 0.93, 0.97),
    "crystal": (0.40, 0.30, 0.55, 0.75, 0.82, 0.95, 0.95, 0.90, 1.0),
    "forest": (0.35, 0.40, 0.45, 0.80, 0.90, 0.75, 1.0, 0.97, 0.90),
}
DEFAULT = PALETTES["nature"]

def palette_for(path):
    low = path.lower()
    for kw, pal in PALETTES.items():
        if kw in low:
            return pal
    return DEFAULT

reg = unreal.AssetRegistryHelpers.get_asset_registry()
converted = 0
for folder in ["/Game/EnvSandbox/Meshes/Environment"]:
    for a in reg.get_assets_by_path(folder, recursive=True):
        if str(a.asset_class_path.asset_name) != "MaterialInstanceConstant":
            continue
        mi = unreal.load_asset(str(a.package_name) + "." + str(a.asset_name))
        if not mi:
            continue
        try:
            parent = mi.get_editor_property("parent")
            if parent and str(parent.get_name()) == "M_Master_Toon_Universal":
                continue
            unreal.MaterialEditingLibrary.set_material_instance_parent(mi, MASTER)
            lr, lg, lb, mr, mg, mb, hr, hg, hb = palette_for(str(a.package_name))
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                mi, "PaletteRampLow", unreal.LinearColor(lr, lg, lb, 1.0))
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                mi, "PaletteRampMid", unreal.LinearColor(mr, mg, mb, 1.0))
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                mi, "PaletteRampHigh", unreal.LinearColor(hr, hg, hb, 1.0))
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RampSharpness", 0.65)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RampContrast", 0.55)
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RampStrength", 0.9)
            converted += 1
        except Exception:
            pass
unreal.EditorAssetLibrary.save_directory("/Game/EnvSandbox/Meshes", only_if_is_dirty=True, recursive=True)
json.dump({"newly_converted": converted}, open(r"C:\Users\froma\AppData\Local\Temp\opencode\mat_convert2.json", "w"))
