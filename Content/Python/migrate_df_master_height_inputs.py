import unreal
import material_lib as lib
MASTER='/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal'
GROUP='02b | Distance Field Contact'
def main():
    m=unreal.load_asset(MASTER); mel=unreal.MaterialEditingLibrary
    call=None
    for e in mel.get_material_expressions(m) or []:
        if isinstance(e,unreal.MaterialExpressionMaterialFunctionCall):
            f=e.get_editor_property('material_function')
            if f and 'MF_DF_ContactBlend' in f.get_path_name(): call=e
    if not call: raise RuntimeError('DF function call not found')
    names=list(mel.get_material_expression_input_names(call) or [])
    for name,default,y in [('GroundHeight',0.0,620),('HeightFalloff',28.0,740)]:
        if name in names: continue
        n=mel.create_material_expression(m,unreal.MaterialExpressionScalarParameter,13700,y)
        n.set_editor_property('parameter_name','DFContact'+name)
        n.set_editor_property('default_value',default); n.set_editor_property('group',GROUP)
        lib.connect(n,'',call,name)
    mel.recompile_material(m); unreal.EditorAssetLibrary.save_asset(MASTER,only_if_is_dirty=False)
    unreal.log('[DFMasterMigration] added GroundHeight/HeightFalloff')
if __name__=='__main__': main()
