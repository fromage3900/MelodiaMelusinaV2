"""Compile an actual consumer of the triplanar normal output."""
import unreal
lib=unreal.MaterialEditingLibrary
path='/Game/EnvSandbox/Materials/Validation/M_Triplanar_NormalProof'
m=unreal.load_asset(path)
if not m:m=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Triplanar_NormalProof',path.rsplit('/',1)[0],unreal.Material,unreal.MaterialFactoryNew())
assert m
if lib.get_num_material_expressions(m)>0:raise RuntimeError('Proof already built; inspect rather than rebuild')
def new(cls):return lib.create_material_expression(m,cls)
def wire(a,b,pin):assert lib.connect_material_expressions(a,'',b,pin)
f=new(unreal.MaterialExpressionMaterialFunctionCall)
f.set_material_function(unreal.load_asset('/Game/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro'))
print('inputs',lib.get_material_expression_input_names(f))
tex=new(unreal.MaterialExpressionTextureObject)
tex.set_editor_property('texture',unreal.load_asset('/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal'))
tex.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
for n in ['Tex','NormalTex']:wire(tex,f,n)
wire(new(unreal.MaterialExpressionWorldPosition),f,'WorldPosition')
wire(new(unreal.MaterialExpressionVertexNormalWS),f,'WorldNormal')
for name,value in {'ProjectionScale':0.01,'BlendSharpness':4,'BreakupScale':1,'BreakupStrength':0,'BreakupContrast':1,'NormalStrength':1}.items():
    p=new(unreal.MaterialExpressionScalarParameter);p.set_editor_property('parameter_name',name);p.set_editor_property('default_value',value);wire(p,f,name)
for name,value in {'ProjectionOffset':(0,0,0),'ProjectionRotation':(27,39,13),'AxisWeights':(1,1,1)}.items():
    p=new(unreal.MaterialExpressionVectorParameter);p.set_editor_property('parameter_name',name);p.set_editor_property('default_value',unreal.LinearColor(*value,0));wire(p,f,name)
m.set_editor_property('tangent_space_normal',False)
assert lib.connect_material_property(f,'NormalWS',unreal.MaterialProperty.MP_NORMAL)
color=new(unreal.MaterialExpressionConstant3Vector);color.set_editor_property('constant',unreal.LinearColor(0.18,0.18,0.18,1))
assert lib.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
lib.recompile_material(m)
print('Proof normal output connected and compile requested')
