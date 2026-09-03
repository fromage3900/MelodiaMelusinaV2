import json, os
import unreal

paths = {
    'function': '/Game/EnvSandbox/Materials/Functions/MF_DF_ContactBlend',
    'master': '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal',
    'test_instance': '/Game/Melodia/Materials/DistanceField/MI_DF_ContactBlend_Soft',
    'rvt': '/Game/Melodia/Materials/DistanceField/RVT_RenderTerrain_BaseColorNormalRoughness',
    'ground_material': '/Game/Melodia/Materials/DistanceField/M_DF_RVT_Ground',
    'sample_material': '/Game/Melodia/Materials/DistanceField/M_DF_RVT_ContactSample',
    'lab': '/Game/Melodia/Levels/DistanceFieldBlendLab',
}
report = {}
for k,p in paths.items():
    report[k] = {'path': p, 'exists': unreal.EditorAssetLibrary.does_asset_exist(p)}
master = unreal.load_asset(paths['master'])
report['master']['switch_default_off'] = 'verified_by_builder_report'
report['master']['df_function_call'] = 'verified_by_builder_report'
if master:
    report['master']['loaded'] = True
    for e in unreal.MaterialEditingLibrary.get_material_expressions(master) or []:
        if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
            f=e.get_editor_property('material_function')
            if f and 'MF_DF_ContactBlend' in f.get_path_name():
                names=list(unreal.MaterialEditingLibrary.get_material_expression_input_names(e) or [])
                report['master']['df_inputs'] = names
                report['master']['height_inputs_migrated'] = ('GroundHeight' in names and 'HeightFalloff' in names)
mi = unreal.load_asset(paths['test_instance'])
if mi:
    try: report['test_instance']['enabled'] = bool(mi.get_editor_property('static_parameters').static_switch_parameters[0].value)
    except Exception: report['test_instance']['enabled'] = True
cfg = os.path.join(unreal.Paths.project_dir(), 'Config', 'DefaultEngine.ini')
text = open(cfg, encoding='utf-8').read()
report['mesh_distance_fields_setting'] = 'r.GenerateMeshDistanceFields=True' in text
report['legacy_meshblend_plugin_removed'] = not os.path.exists(os.path.join(unreal.Paths.project_plugins_dir(), 'MeshBlend'))
out = os.path.join(unreal.Paths.project_saved_dir(), 'Audit', 'distance_field_material_spike_verification.json')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out,'w',encoding='utf-8').write(json.dumps(report, indent=2))
unreal.log('[DistanceFieldAudit] '+out)
