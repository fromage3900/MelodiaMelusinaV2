"""Generate toon material instances for imported packs on M_Master_Toon_Universal.

Fixed 2026-08-13: the previous version set a non-existent `BaseColorAtlas` param
and static switches that do not exist on the master, which silently produced
textureless instances (Survey: mi_texture_weight_survey_v2.json found 22
Universal instances with zero overrides). This version:
  - routes the real `Albedo` param (master's LayerA albedo slot)
  - sets `TextureWeight=1.0` (pipeline convention; master default is 0.0 so
    textures are invisible unless the instance overrides it)
  - loads color atlases from the real staging path
    (/Game/Melodia/_PROJECT/04_Materials/Textures/ColorAtlas_*)
  - sets the static switches that actually exist on the master
    (bNikkiHero, bTriplanar_Active) instead of non-existent ones
"""
import unreal


def generate_toon_material_instances():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material_factory = unreal.MaterialInstanceConstantFactoryNew()

    parent_material_path = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
    parent_material = unreal.EditorAssetLibrary.load_asset(parent_material_path)

    if not parent_material:
        unreal.log_error(f"Could not find parent material at {parent_material_path}")
        return

    # Color atlas defaults (staging path that exists on disk).
    atlas_base = "/Game/Melodia/_PROJECT/04_Materials/Textures"

    families = [
        {"name": "MI_Universal_Nature", "color": f"{atlas_base}/ColorAtlas_NatureFoliage"},
        {"name": "MI_Universal_Stone", "color": f"{atlas_base}/ColorAtlas_PastelFantasy"},
        {"name": "MI_Universal_Wood", "color": f"{atlas_base}/ColorAtlas_PastelFantasy"},
        {"name": "MI_Universal_Metal_Stylized", "color": f"{atlas_base}/ColorAtlas_PastelFantasy"},
    ]

    dest_path = "/Game/EnvSandbox/Materials/Instances"

    for family in families:
        asset_name = family["name"]

        if unreal.EditorAssetLibrary.does_asset_exist(f"{dest_path}/{asset_name}"):
            unreal.log(f"Asset {asset_name} already exists. Skipping creation.")
            continue

        new_mi = asset_tools.create_asset(asset_name, dest_path, unreal.MaterialInstanceConstant, material_factory)

        if new_mi:
            unreal.MaterialEditingLibrary.set_material_instance_parent(new_mi, parent_material)

            color_tex = unreal.EditorAssetLibrary.load_asset(family["color"])
            if color_tex:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(new_mi, "Albedo", color_tex)

            # TextureWeight is 0.0 on the master (procedural base) - instances with
            # textures MUST override it or they render textureless.
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(new_mi, "TextureWeight", 1.0)

            # Feature switches that exist on the master (off by default to save
            # Substrate budget).
            unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(new_mi, "bNikkiHero", False)
            unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(new_mi, "bTriplanar_Active", False)

            unreal.EditorAssetLibrary.save_loaded_asset(new_mi, only_if_is_dirty=False)
            unreal.log(f"Successfully generated {asset_name}")

    unreal.log("Material Instance generation complete!")


generate_toon_material_instances()
