import unreal
import material_lib as lib
PATH='/Game/Melodia/Materials/DistanceField/M_DF_ContactMaskDebug'
ROOT='/Game/Melodia/Materials/DistanceField'
def main():
    unreal.EditorAssetLibrary.make_directory(ROOT)
    mel=unreal.MaterialEditingLibrary
    m=unreal.load_asset(PATH)
    if not m: m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DF_ContactMaskDebug',ROOT,unreal.Material,unreal.MaterialFactoryNew())
    for e in list(mel.get_material_expressions(m) or []): mel.delete_material_expression(m,e)
    wp=mel.create_material_expression(m,unreal.MaterialExpressionWorldPosition,-800,0)
    z=mel.create_material_expression(m,unreal.MaterialExpressionComponentMask,-420,0)
    z.set_editor_property('r',False); z.set_editor_property('g',False); z.set_editor_property('b',True); z.set_editor_property('a',False)
    lib.connect(wp,'',z,'Input')
    div=mel.create_material_expression(m,unreal.MaterialExpressionDivide,-220,0); lib.connect(z,'',div,'A')
    d=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-420,160); d.set_editor_property('r',28.0); lib.connect(d,'',div,'B')
    inv=mel.create_material_expression(m,unreal.MaterialExpressionOneMinus,-240,0); lib.connect(div,'',inv,'')
    sat=mel.create_material_expression(m,unreal.MaterialExpressionSaturate,-60,0); lib.connect(inv,'',sat,'')
    color=mel.create_material_expression(m,unreal.MaterialExpressionLinearInterpolate,180,0)
    black=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-120,240)
    black.set_editor_property('constant',unreal.LinearColor(0.01,0.01,0.01,1))
    cyan=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-120,400)
    cyan.set_editor_property('constant',unreal.LinearColor(0.05,0.8,1.0,1))
    lib.connect(black,'',color,'A'); lib.connect(cyan,'',color,'B'); lib.connect(sat,'',color,'Alpha')
    mel.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(color,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m); unreal.EditorAssetLibrary.save_asset(PATH,only_if_is_dirty=False)
    unreal.log('[DistanceFieldMaskDebug] '+PATH)
if __name__=='__main__': main()
