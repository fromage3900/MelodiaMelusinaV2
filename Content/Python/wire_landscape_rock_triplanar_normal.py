"""Wire the existing triplanar function into the rock normal layer."""
import unreal
lib=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape')
expressions=list(lib.get_material_expressions(m))
def node(cls,tag,x,y):
    e=next((e for e in expressions if str(e.get_editor_property('desc'))==tag),None)
    if not e:
        e=lib.create_material_expression(m,cls,x,y);e.set_editor_property('desc',tag);expressions.append(e)
    return e
def wire(a,b,pin='',out=''):
    assert lib.connect_material_expressions(a,out,b,pin),(a.get_name(),b.get_name(),pin)
def scalar(name,value,x,y):
    e=node(unreal.MaterialExpressionScalarParameter,'RockTri:'+name,x,y)
    e.set_editor_property('parameter_name',name);e.set_editor_property('default_value',value)
    e.set_editor_property('group','03 | Rock Triplanar Detail');return e
m.modify()
existing=unreal.find_object(m,'MaterialExpressionMaterialFunctionCall_15')
f=node(unreal.MaterialExpressionMaterialFunctionCall,'RockTri:Function',-2000,1800)
f.set_material_function(unreal.load_asset('/Game/EnvSandbox/Materials/Functions/MF_Triplanar_LandscapePro'))
for pin,source in zip(lib.get_material_expression_input_names(existing),lib.get_inputs_for_material_expression(m,existing)):
    if source and str(pin)!='ProjectionScale':wire(source,f,str(pin))
tex=node(unreal.MaterialExpressionTextureObjectParameter,'RockTri:NormalTexture',-2600,1800)
tex.set_editor_property('parameter_name','Rock_NormalMap')
tex.set_editor_property('texture',unreal.load_asset('/Game/EnvSandbox/Textures/Utility/T_Neutral_Normal'))
tex.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
wire(tex,f,'NormalTex')
wire(scalar('Rock_TriplanarNormalStrength',1,-2600,2000),f,'NormalStrength')
size=scalar('Rock_DetailWorldSizeCM',400,-3000,2200)
recip=node(unreal.MaterialExpressionDivide,'RockTri:ReciprocalSize',-2600,2200)
recip.set_editor_property('const_a',1.0)
safe=node(unreal.MaterialExpressionMax,'RockTri:PositiveSize',-2800,2200)
safe.set_editor_property('const_b',1.0);wire(size,safe,'A');wire(safe,recip,'B');wire(recip,f,'ProjectionScale')
transform=node(unreal.MaterialExpressionTransform,'RockTri:WorldToTangent',-1700,1800)
transform.set_editor_property('transform_source_type',unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD)
transform.set_editor_property('transform_type',unreal.MaterialVectorCoordTransform.TRANSFORM_TANGENT)
wire(f,transform,out='NormalWS')
uv=unreal.find_object(m,'MaterialExpressionTextureSampleParameter2D_12')
blend=node(unreal.MaterialExpressionLinearInterpolate,'RockTri:RuntimeBlend',-1400,1800)
wire(uv,blend,'A');wire(transform,blend,'B')
alpha=scalar('Rock_TriplanarBlend',1,-1700,2100)
clamp=node(unreal.MaterialExpressionSaturate,'RockTri:BlendRange',-1500,2100);wire(alpha,clamp);wire(clamp,blend,'Alpha')
normal=node(unreal.MaterialExpressionNormalize,'RockTri:Normalized',-1200,1800);wire(blend,normal)
switch=node(unreal.MaterialExpressionStaticSwitchParameter,'RockTri:Enabled',-1000,1800)
switch.set_editor_property('parameter_name','bRockTriplanarNormals')
switch.set_editor_property('default_value',False)
switch.set_editor_property('group','03 | Rock Triplanar Detail')
wire(normal,switch,'True');wire(uv,switch,'False')
wire(switch,unreal.find_object(m,'MaterialExpressionLandscapeLayerBlend_4'),'Layer Rock')
lib.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
print('Saved rock UV/triplanar normal blend; default-off static variant retained')
