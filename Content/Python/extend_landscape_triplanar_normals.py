"""Extend the existing triplanar function without replacing its colour interface."""
from pathlib import Path
import unreal

ROOT=Path(__file__).resolve().parent
PATH='/Game/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro'
lib=unreal.MaterialEditingLibrary
f=unreal.load_asset(PATH)
assert f
expr=list(lib.get_material_function_expressions(f))
inputs={str(e.get_editor_property('input_name')):e for e in expr if isinstance(e,unreal.MaterialExpressionFunctionInput)}
def node(cls,tag,x,y):
    found=next((e for e in expr if str(e.get_editor_property('desc'))==tag),None)
    if found:return found
    e=lib.create_material_expression_in_function(f,cls,x,y)
    e.set_editor_property('desc',tag);expr.append(e);return e
def wire(a,b,pin='',out=''):
    assert lib.connect_material_expressions(a,out,b,pin),(a.get_name(),b.get_name(),pin)

f.modify()
tex=node(unreal.MaterialExpressionFunctionInput,'LTriPro:Input_NormalTex',-1500,900)
tex.set_editor_property('input_name','NormalTex')
tex.set_editor_property('input_type',unreal.FunctionInputType.FUNCTION_INPUT_TEXTURE2D)
tex.set_editor_property('sort_priority',11)
tex.set_editor_property('use_preview_value_as_default',True)
neutral=node(unreal.MaterialExpressionTextureObject,'LTriPro:NeutralNormal',-1800,900)
neutral.set_editor_property('texture',unreal.load_asset('/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal'))
neutral.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
wire(neutral,tex,'Preview')
strength=node(unreal.MaterialExpressionFunctionInput,'LTriPro:Input_NormalStrength',-1500,1100)
strength.set_editor_property('input_name','NormalStrength')
strength.set_editor_property('input_type',unreal.FunctionInputType.FUNCTION_INPUT_SCALAR)
strength.set_editor_property('sort_priority',12)
default_strength=node(unreal.MaterialExpressionConstant,'LTriPro:DefaultNormalStrength',-1800,1100)
default_strength.set_editor_property('r',1.0)
wire(default_strength,strength,'Preview')
strength.set_editor_property('use_preview_value_as_default',True)
inputs['NormalTex']=tex;inputs['NormalStrength']=strength
common=(ROOT/'shaders/landscape_triplanar_pro.hlsl').read_text().split('float3 sampleX =')[0]
normal_code=common+'''
// Surface-gradient composition, using UE's platform-aware normal decoder.
// Reference: Mikkelsen, JCGT 9(3), 2020. UV axes match the colour projections.
float3 nx = UnpackNormalMap(Texture2DSampleGrad(NormalTex,NormalTexSampler,uvX,ddxp.yz,ddyp.yz)).xyz;
float3 ny = UnpackNormalMap(Texture2DSampleGrad(NormalTex,NormalTexSampler,uvY,ddxp.xz,ddyp.xz)).xyz;
float3 nz = UnpackNormalMap(Texture2DSampleGrad(NormalTex,NormalTexSampler,uvZ,ddxp.xy,ddyp.xy)).xyz;
float2 sx=nx.xy/max(nx.z,0.05), sy=ny.xy/max(ny.z,0.05), sz=nz.xy/max(nz.z,0.05);
float3 N=mul(projection,geometricNormal);
// Convert the three 2D slopes to the common projection frame before blending.
float3 perturb=w.x*float3(0,sx.x,sx.y)+w.y*float3(sy.x,0,sy.y)+w.z*float3(sz.x,sz.y,0);
perturb-=N*dot(N,perturb);
float3 result=normalize(N+max(NormalStrength,0.0)*perturb);
return normalize(mul(transpose(projection),result));
'''
(ROOT/'shaders/landscape_triplanar_normal.hlsl').write_text(normal_code)
custom=node(unreal.MaterialExpressionCustom,'LTriPro:NormalCustom',-500,1000)
custom.set_editor_property('code',normal_code)
custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
names=[n for n in inputs if n!='Tex']
cis=[]
for name in names:
    ci=unreal.CustomInput();ci.set_editor_property('input_name',name);cis.append(ci)
custom.set_editor_property('inputs',cis)
for name in names:wire(inputs[name],custom,name)
output=node(unreal.MaterialExpressionFunctionOutput,'LTriPro:Output_NormalWS',300,1000)
output.set_editor_property('output_name','NormalWS')
output.set_editor_property('sort_priority',1)
wire(custom,output)
lib.update_material_function(f)
print('Added optional NormalTex/NormalStrength and NormalWS output; save follows compiled probe.')
