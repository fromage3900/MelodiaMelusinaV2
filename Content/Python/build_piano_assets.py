"""Bake beveled piano meshes and small dedicated PBR materials.

The key actors remain light at runtime: Geometry Script runs here in the editor
to turn centered boxes into reusable StaticMesh assets with real edge bevels.
"""

from __future__ import annotations

from pcg_piano_layout import PianoDimensions


DEST_FOLDER = "/Game/EnvSandbox/PCG/Musical"
MASTER_PATH = f"{DEST_FOLDER}/M_Piano_Surface"
WHITE_MESH_PATH = f"{DEST_FOLDER}/SM_PianoKey_White_Bevel"
BLACK_MESH_PATH = f"{DEST_FOLDER}/SM_PianoKey_Black_Bevel"
KEYBED_MESH_PATH = f"{DEST_FOLDER}/SM_Piano_Keybed"
WHITE_MATERIAL_PATH = f"{DEST_FOLDER}/MI_Piano_Ivory"
BLACK_MATERIAL_PATH = f"{DEST_FOLDER}/MI_Piano_Ebony"
KEYBED_MATERIAL_PATH = f"{DEST_FOLDER}/MI_Piano_Keybed"


def _set_if_present(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _make_beveled_box(unreal, asset_path: str, dimensions: tuple[float, float, float], bevel_distance: float, subdivisions: int = 3):
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.load_asset(asset_path), False

    dm = unreal.new_object(unreal.DynamicMesh)
    prim_opts = unreal.GeometryScriptPrimitiveOptions()
    origin_enum = getattr(getattr(unreal, "GeometryScriptPrimitiveOriginMode", None), "CENTER", None)
    if origin_enum is None:
        origin_enum = getattr(getattr(unreal, "GeometryScriptPrimitiveOriginMode", None), "Center", None)

    transform = unreal.Transform()
    if origin_enum is None:
        # AppendBox's fallback origin is the base; offset it so the baked mesh is
        # still centered at the PCG point used by the layout script.
        transform = unreal.Transform(location=unreal.Vector(0.0, 0.0, -dimensions[2] * 0.5))
        origin_enum = getattr(getattr(unreal, "GeometryScriptPrimitiveOriginMode", None), "BASE", None)
        if origin_enum is None:
            origin_enum = getattr(getattr(unreal, "GeometryScriptPrimitiveOriginMode", None), "Base", 0)

    unreal.GeometryScript_Primitives.append_box(
        dm,
        prim_opts,
        transform,
        float(dimensions[0]),
        float(dimensions[1]),
        float(dimensions[2]),
        0,
        0,
        0,
        origin_enum,
    )

    bevel_opts = unreal.GeometryScriptMeshBevelOptions()
    _set_if_present(bevel_opts, "bevel_distance", float(bevel_distance))
    _set_if_present(bevel_opts, "subdivisions", int(subdivisions))
    _set_if_present(bevel_opts, "round_weight", 0.75)
    _set_if_present(bevel_opts, "b_infer_material_id", True)
    unreal.GeometryScript_MeshModeling.apply_mesh_polygroup_bevel(dm, bevel_opts)
    unreal.GeometryScript_Normals.recompute_normals(dm, unreal.GeometryScriptCalculateNormalsOptions())

    output_opts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    result = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, asset_path, output_opts)
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
        return unreal.load_asset(asset_path), True
    raise RuntimeError(f"Geometry Script failed to create {asset_path}: {result}")


def _create_master_material(unreal):
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_PATH):
        return unreal.load_asset(MASTER_PATH), False

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset("M_Piano_Surface", DEST_FOLDER, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError(f"Could not create {MASTER_PATH}")
    mel = unreal.MaterialEditingLibrary

    base = mel.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -500, 0)
    base.set_editor_property("parameter_name", "BaseColor")
    base.set_editor_property("default_value", unreal.LinearColor(0.7, 0.6, 0.45, 1.0))
    roughness = mel.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -500, 180)
    roughness.set_editor_property("parameter_name", "Roughness")
    roughness.set_editor_property("default_value", 0.3)
    specular = mel.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -500, 340)
    specular.set_editor_property("parameter_name", "Specular")
    specular.set_editor_property("default_value", 0.5)
    clear_coat = mel.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -500, 500)
    clear_coat.set_editor_property("parameter_name", "ClearCoat")
    clear_coat.set_editor_property("default_value", 0.1)

    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
    try:
        mel.connect_material_property(clear_coat, "", unreal.MaterialProperty.MP_CLEAR_COAT)
    except Exception:
        pass
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(MASTER_PATH, only_if_is_dirty=False)
    return material, True


def _create_material_instance(unreal, parent, path: str, color: tuple[float, float, float], roughness: float, specular: float, clear_coat: float):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        instance = unreal.load_asset(path)
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        name = path.rsplit("/", 1)[-1]
        instance = tools.create_asset(name, DEST_FOLDER, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    if not instance:
        raise RuntimeError(f"Could not create {path}")
    instance.set_editor_property("parent", parent)
    mel = unreal.MaterialEditingLibrary
    mel.set_material_instance_vector_parameter_value(instance, "BaseColor", unreal.LinearColor(*color, 1.0))
    mel.set_material_instance_scalar_parameter_value(instance, "Roughness", float(roughness))
    mel.set_material_instance_scalar_parameter_value(instance, "Specular", float(specular))
    mel.set_material_instance_scalar_parameter_value(instance, "ClearCoat", float(clear_coat))
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return instance


def build_assets() -> dict:
    import unreal

    if not unreal.EditorAssetLibrary.does_directory_exist(DEST_FOLDER):
        unreal.EditorAssetLibrary.make_directory(DEST_FOLDER)

    dimensions = PianoDimensions()
    total_width = 52 * dimensions.white_width + 51 * dimensions.inter_key_gap
    meshes = {
        "white": _make_beveled_box(
            unreal,
            WHITE_MESH_PATH,
            (dimensions.white_width - dimensions.inter_key_gap, dimensions.white_depth, dimensions.white_height),
            1.35,
            3,
        ),
        "black": _make_beveled_box(
            unreal,
            BLACK_MESH_PATH,
            (dimensions.black_width, dimensions.black_depth, dimensions.black_height),
            1.1,
            3,
        ),
        "keybed": _make_beveled_box(
            unreal,
            KEYBED_MESH_PATH,
            (total_width + 16.0, dimensions.white_depth + 18.0, 15.0),
            2.0,
            3,
        ),
    }
    master, master_created = _create_master_material(unreal)
    materials = {
        "white": _create_material_instance(unreal, master, WHITE_MATERIAL_PATH, (0.86, 0.78, 0.61), 0.27, 0.52, 0.18),
        "black": _create_material_instance(unreal, master, BLACK_MATERIAL_PATH, (0.012, 0.009, 0.007), 0.16, 0.66, 0.22),
        "keybed": _create_material_instance(unreal, master, KEYBED_MATERIAL_PATH, (0.035, 0.012, 0.006), 0.34, 0.48, 0.08),
    }
    result = {
        "meshes": {key: value[0].get_path_name() if value[0] else None for key, value in meshes.items()},
        "materials": {key: value.get_path_name() if value else None for key, value in materials.items()},
        "master_created": master_created,
        "bevel": "GeometryScript AppendBox + ApplyMeshPolygroupBevel, 3 subdivisions",
    }
    unreal.log(f"[PCG Piano] built assets {result}")
    return result


if __name__ == "__main__":
    print(build_assets())
