"""Optional frost roughness band from the documented Gaea snow distance bake."""
import unreal
lib=unreal.MaterialEditingLibrary
m=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape')
expressions=list(lib.get_material_expressions(m))
def node(cls,tag,x,y):
    e=next((e for e in expressions if str(e.get_editor_property('desc'))==tag),None)
    if e is None:
        e=lib.create_material_expression(m,cls,x,y);e.set_editor_property('desc',tag);expressions.append(e)
    return e
def wire(a,b,pin='',out=''):
    assert a and b
    assert lib.connect_material_expressions(a,out,b,pin),(a.get_name(),b.get_name(),pin)
def scalar(name,value,x,y):
    e=node(unreal.MaterialExpressionScalarParameter,'SnowSDF:'+name,x,y)
    e.set_editor_property('parameter_name',name);e.set_editor_property('default_value',value)
    e.set_editor_property('group','04 | Snow Distance Field');return e
m.modify()
tex=node(unreal.MaterialExpressionTextureSampleParameter2D,'SnowSDF:Texture',-1200,-3200)
tex.set_editor_property('parameter_name','SnowEdgeDistanceTexture')
tex.set_editor_property('texture',unreal.load_asset('/Game/Gaea/Glacier/Textures/T_Glacier_SnowEdge_SDF16'))
tex.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
wire(unreal.find_object(m,'MaterialExpressionComponentMask_0'),tex,'UVs')
band=node(unreal.MaterialExpressionCustom,'SnowSDF:FrostBand',-900,-3200)
names=['Encoded','RangeCM','WidthCM','Strength']
inputs=[]
for name in names:
    ci=unreal.CustomInput();ci.set_editor_property('input_name',name);inputs.append(ci)
band.set_editor_property('inputs',inputs)
band.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
band.set_editor_property('code','float d=(Encoded*2.0-1.0)*max(RangeCM,1.0); float w=max(WidthCM,1.0); float aa=max(fwidth(d),1.0); return (1.0-smoothstep(max(w-aa,0.0),w+aa,abs(d)))*saturate(Strength);')
wire(tex,band,'Encoded','R')
wire(scalar('SnowEdgeDistanceRangeCM',25000,-1400,-3450),band,'RangeCM')
wire(scalar('SnowFrostBandWidthCM',1000,-1200,-3450),band,'WidthCM')
wire(scalar('SnowFrostBandStrength',0.2,-1000,-3450),band,'Strength')
baseline=unreal.find_object(m,'MaterialExpressionLinearInterpolate_13')
blend=node(unreal.MaterialExpressionLinearInterpolate,'SnowSDF:RoughnessBlend',-500,-3200)
wire(baseline,blend,'A');wire(band,blend,'Alpha')
target=node(unreal.MaterialExpressionSaturate,'SnowSDF:TargetRange',-650,-3450)
wire(scalar('SnowFrostRoughness',0.7,-850,-3650),target);wire(target,blend,'B')
switch=node(unreal.MaterialExpressionStaticSwitchParameter,'SnowSDF:Enabled',-200,-3200)
switch.set_editor_property('parameter_name','bSnowFrostDistanceBand');switch.set_editor_property('default_value',False)
switch.set_editor_property('group','04 | Snow Distance Field')
wire(blend,switch,'True');wire(baseline,switch,'False')
wire(switch,unreal.find_object(m,'MaterialExpressionSubstrateToonBSDF_1'),'Roughness')
lib.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
print('Saved optional frost roughness band; disabled pending terrain/performance acceptance.')
