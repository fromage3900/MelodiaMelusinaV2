import unreal
import material_lib as lib
PATH='/Game/Melodia/Materials/DistanceField/M_DF_ContactReference'
ROOT='/Game/Melodia/Materials/DistanceField'
def S(m,t,x,y): return unreal.MaterialEditingLibrary.create_material_expression(m,t,x,y)
def main():
    unreal.EditorAssetLibrary.make_directory(ROOT)
    m=unreal.EditorAssetLibrary.load_asset(PATH)
    if not m:
        m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DF_ContactReference',ROOT,unreal.Material,unreal.MaterialFactoryNew())
    mel=unreal.MaterialEditingLibrary
    for e in list(mel.get_material_expressions(m) or []): mel.delete_material_expression(m,e)
    wp=S(m,unreal.MaterialExpressionWorldPosition,-900,0)
    df=S(m,unreal.MaterialExpressionDistanceToNearestSurface,-700,0); lib.connect(wp,'',df,'Position')
    div=S(m,unreal.MaterialExpressionDivide,-500,0); lib.connect(df,'',div,'A')
    d=S(m,unreal.MaterialExpressionConstant,-700,180); d.set_editor_property('r',22.0); lib.connect(d,'',div,'B')
    inv=S(m,unreal.MaterialExpressionOneMinus,-300,0); lib.connect(div,'',inv,'')
    sat=S(m,unreal.MaterialExpressionSaturate,-100,0); lib.connect(inv,'',sat,'')
    base=S(m,unreal.MaterialExpressionConstant3Vector,-500,300); base.set_editor_property('constant',unreal.LinearColor(0.12,0.16,0.20,1))
    tint=S(m,unreal.MaterialExpressionConstant3Vector,-500,460); tint.set_editor_property('constant',unreal.LinearColor(0.36,0.48,0.62,1))
    lerp=S(m,unreal.MaterialExpressionLinearInterpolate,180,0); lib.connect(base,'',lerp,'A'); lib.connect(tint,'',lerp,'B'); lib.connect(sat,'',lerp,'Alpha')
    rough=S(m,unreal.MaterialExpressionConstant,-100,380); rough.set_editor_property('r',0.72)
    mel.connect_material_property(lerp,'',unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(m); unreal.EditorAssetLibrary.save_asset(PATH,only_if_is_dirty=False)
    unreal.log('[DistanceFieldReference] '+PATH)
if __name__=='__main__': main()
