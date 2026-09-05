"""Teach the shared Nikki base surface to consume Gaea's existing Base layer."""
import json
from pathlib import Path
import unreal

root=Path('C:/EnvironmentPortfolio/BS_GodFile')
path='/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape'
mat=unreal.load_asset(path)
lib=unreal.MaterialEditingLibrary
changes=[]
for name,source,output in [
    ('MaterialExpressionLandscapeLayerBlend_5','MaterialExpressionTextureSampleParameter2D_6','RGB'),
    ('MaterialExpressionLandscapeLayerBlend_4','MaterialExpressionTextureSampleParameter2D_7','RGB'),
    ('MaterialExpressionLandscapeLayerBlend_6','MaterialExpressionScalarParameter_19','')]:
    blend=unreal.find_object(mat,name)
    layers=list(blend.get_editor_property('layers'))
    if not any(str(x.get_editor_property('layer_name'))=='Base' for x in layers):
        layer=unreal.LayerBlendInput()
        layer.set_editor_property('layer_name','Base')
        layer.set_editor_property('blend_type',unreal.LandscapeLayerBlendType.LB_WEIGHT_BLEND)
        layers.append(layer)
        blend.set_editor_property('layers',layers)
    assert lib.connect_material_expressions(unreal.find_object(mat,source),output,blend,'Layer Base')
    changes.append(name)
lib.recompile_material(mat)
assert unreal.EditorAssetLibrary.save_loaded_asset(mat,False)
(root/'Saved/Audit/sea_above_base_binding.json').write_text(json.dumps({'saved':True,'blends':changes,'preserved_layer':'Ground','added_layer':'Base'},indent=2))
print('Saved Gaea Base support for colour, normal and roughness')
