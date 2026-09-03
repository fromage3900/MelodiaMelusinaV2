"""Create RVT terrain infrastructure for DistanceFieldBlendLab."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


LEVEL = "/Game/Melodia/Levels/DistanceFieldBlendLab"
ROOT = "/Game/Melodia/Materials/DistanceField"
RVT_PATH = f"{ROOT}/RVT_RenderTerrain_BaseColorNormalRoughness"
GROUND_MAT_PATH = f"{ROOT}/M_DF_RVT_Ground"
SAMPLE_MAT_PATH = f"{ROOT}/M_DF_RVT_ContactSample"
REPORT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "distance_field_rvt_lab.json"


def _set(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def _asset(path):
    return unreal.EditorAssetLibrary.load_asset(path)


def _create_rvt():
    unreal.EditorAssetLibrary.make_directory(ROOT)
    rvt = _asset(RVT_PATH)
    if not rvt:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        rvt = tools.create_asset("RVT_RenderTerrain_BaseColorNormalRoughness", ROOT, unreal.RuntimeVirtualTexture, unreal.RuntimeVirtualTextureFactory())
    if not rvt:
        raise RuntimeError(f"Could not create {RVT_PATH}")
    _set(rvt, "material_type", unreal.RuntimeVirtualTextureMaterialType.BASE_COLOR_NORMAL_ROUGHNESS)
    _set(rvt, "tile_count", 512)
    _set(rvt, "tile_size", 128)
    _set(rvt, "material_quality", unreal.RuntimeVirtualTextureMaterialQuality.HIGH)
    unreal.EditorAssetLibrary.save_asset(RVT_PATH, only_if_is_dirty=False)
    return rvt


def _create_ground_material():
    mat = _asset(GROUND_MAT_PATH)
    if not mat:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mat = tools.create_asset("M_DF_RVT_Ground", ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        raise RuntimeError(f"Could not create {GROUND_MAT_PATH}")
    mel = unreal.MaterialEditingLibrary
    for expr in list(mel.get_material_expressions(mat) or []):
        mel.delete_material_expression(mat, expr)
    color = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -520, 0)
    color.set_editor_property("constant", unreal.LinearColor(0.16, 0.20, 0.22, 1.0))
    normal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -520, 160)
    normal.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -520, 320)
    rough.set_editor_property("r", 0.78)
    height = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -520, 480)
    output = mel.create_material_expression(mat, unreal.MaterialExpressionRuntimeVirtualTextureOutput, -120, 180)
    mel.connect_material_expressions(color, "", output, "BaseColor")
    mel.connect_material_expressions(normal, "", output, "Normal")
    mel.connect_material_expressions(rough, "", output, "Roughness")
    mel.connect_material_expressions(height, "", output, "WorldHeight")
    mel.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(normal, "", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    _set(mat, "b_used_with_runtime_virtual_texture", True)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(GROUND_MAT_PATH, only_if_is_dirty=False)
    return mat


def _volume(rvt):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(LEVEL):
        raise RuntimeError(f"Could not load {LEVEL}")
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    volume = next((a for a in eas.get_all_level_actors() if a.get_actor_label() == "DFLab_RVTVolume"), None)
    if not volume:
        volume = eas.spawn_actor_from_class(unreal.RuntimeVirtualTextureVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
        volume.set_actor_label("DFLab_RVTVolume")
    volume.set_actor_scale3d(unreal.Vector(7.5, 5.5, 2.0))
    component = volume.get_component_by_class(unreal.RuntimeVirtualTextureComponent)
    if not component:
        raise RuntimeError("RVT volume has no RuntimeVirtualTextureComponent")
    if not _set(component, "virtual_texture", rvt):
        _set(volume, "virtual_texture", rvt)
    _set(component, "bounds_align_actor", True)
    levels.save_current_level()
    return volume

def _create_sample_material(rvt):
    path = SAMPLE_MAT_PATH
    mat = _asset(path)
    if not mat:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        mat = tools.create_asset("M_DF_RVT_ContactSample", ROOT, unreal.Material, unreal.MaterialFactoryNew())
    mel = unreal.MaterialEditingLibrary
    for expr in list(mel.get_material_expressions(mat) or []):
        mel.delete_material_expression(mat, expr)
    sample = mel.create_material_expression(mat, unreal.MaterialExpressionRuntimeVirtualTextureSampleParameter, -420, 0)
    _set(sample, "virtual_texture", rvt)
    _set(sample, "material_type", unreal.RuntimeVirtualTextureMaterialType.BASE_COLOR_NORMAL_ROUGHNESS)
    try: _set(mat, "b_used_with_runtime_virtual_texture", True)
    except Exception: pass
    mel.connect_material_property(sample, "BaseColor", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(sample, "Normal", unreal.MaterialProperty.MP_NORMAL)
    mel.connect_material_property(sample, "Roughness", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return mat

def _assign_lab(rvt, ground_mat):
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in eas.get_all_level_actors():
        label = actor.get_actor_label()
        if label == "DFLab_Ground":
            for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                _set(comp, "override_materials", [ground_mat])
                ok = _set(comp, "runtime_virtual_textures", [rvt])
                unreal.log(f"[DistanceFieldRVT] {label} runtime VT assigned={ok}")
        elif label in ("DFLab_EmbeddedRock", "DFLab_WallContact", "DFLab_ColumnContact", "DFLab_SeparatedRock"):
            for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                ok = _set(comp, "runtime_virtual_textures", [rvt])
                unreal.log(f"[DistanceFieldRVT] {label} runtime VT assigned={ok}")


def main():
    rvt = _create_rvt()
    ground_mat = _create_ground_material()
    sample_mat = _create_sample_material(rvt)
    volume = _volume(rvt)
    _assign_lab(rvt, ground_mat)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    result = {"level": LEVEL, "rvt": RVT_PATH, "ground_material": GROUND_MAT_PATH, "sample_material": SAMPLE_MAT_PATH, "volume": volume.get_actor_label(), "material_type": "BASE_COLOR_NORMAL_ROUGHNESS", "generated": True}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    unreal.log(f"[DistanceFieldRVT] Built RVT lab infrastructure -> {REPORT}")


if __name__ == "__main__":
    main()
