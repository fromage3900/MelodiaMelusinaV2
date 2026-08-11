import unreal
m=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal')
mel=unreal.MaterialEditingLibrary
for e in mel.get_material_expressions(m) or []:
    if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
        f=e.get_editor_property('material_function')
        if f and 'MF_DF_ContactBlend' in f.get_path_name():
            unreal.log('[DFMaster] call=%s inputs=%s outputs=%s' % (e.get_name(), str(mel.get_material_expression_input_names(e)), str(mel.get_material_expression_output_names(e))))
            for p in ('function_inputs','function_outputs','function_input_infos'):
                try: unreal.log('[DFMaster] %s=%s' % (p,str(e.get_editor_property(p))))
                except Exception: pass
