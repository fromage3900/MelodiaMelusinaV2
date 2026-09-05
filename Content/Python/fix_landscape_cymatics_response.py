"""Bound landscape cymatic emission while preserving the zero-beat baseline."""
import unreal
lib=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape')
expressions=list(lib.get_material_expressions(m))
def node(cls,tag,x,y):
    e=next((e for e in expressions if str(e.get_editor_property('desc'))==tag),None)
    if e is None:
        e=lib.create_material_expression(m,cls,x,y)
        e.set_editor_property('desc',tag);expressions.append(e)
    return e
def wire(a,b,pin=''):
    assert a and b
    assert lib.connect_material_expressions(a,'',b,pin),(a.get_name(),b.get_name(),pin)
m.modify()
response=node(unreal.MaterialExpressionCustom,'LandscapeCymatics:BoundedAdd',300,-550)
response.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
names=['Baseline','SurfaceColor','Beat','Amount','MaxEmission']
inputs=[]
for name in names:
    ci=unreal.CustomInput();ci.set_editor_property('input_name',name);inputs.append(ci)
response.set_editor_property('inputs',inputs)
response.set_editor_property('code','return Baseline + saturate(SurfaceColor)*saturate(Beat)*saturate(Amount)*clamp(MaxEmission,0.0,10.0);')
for name,src in {
    'Baseline':'MaterialExpressionMultiply_20',
    'SurfaceColor':'MaterialExpressionLinearInterpolate_8',
    'Beat':'MaterialExpressionCollectionParameter_4',
    'Amount':'MaterialExpressionScalarParameter_38',
}.items():wire(unreal.find_object(m,src),response,name)
limit=node(unreal.MaterialExpressionScalarParameter,'LandscapeCymatics:MaxEmission',0,-800)
limit.set_editor_property('parameter_name','CymaticsLandscapeMaxEmission')
limit.set_editor_property('default_value',1.0)
limit.set_editor_property('slider_min',0.0);limit.set_editor_property('slider_max',10.0)
limit.set_editor_property('group','05 | Landscape Cymatics')
wire(limit,response,'MaxEmission')
wire(response,unreal.find_object(m,'MaterialExpressionSubstrateToonBSDF_1'),'EmissiveColor')
lib.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
print('Saved bounded additive landscape cymatics. No MPC writes.')
