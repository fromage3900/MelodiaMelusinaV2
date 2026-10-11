import unreal
MEL=unreal.MaterialEditingLibrary
p='/Game/EnvSandbox/Materials/PostProcess/Candidates/Profiles/MI_StorybookOutline_Premium_Hero_Dream'
mi=unreal.load_asset(p)
new=dict(MultiplyDarken=0.35,UseMultiplyTintAmount=0.0,FoliageDepthInkStrength=0.12,FoliageNormalInkStrength=0.04,FoliageDistanceFadeStart=700,FoliageDistanceFadeEnd=4500,
 BeatPulseStrength=2.0,bEnableBeatPulse=0.0,DayNightFactor=1.0,DistanceFadeStart=4000,DistanceFadeEnd=20000,DreamRimStrength=0.0,DreamRimPower=3.0,
 HalftoneAmount=0.0,HalftoneScale=6.0,HalftoneAngle=45.0,Iridescence=0.0,IridescencePower=2.0,DepthWeight=1.0,EdgeStrength=0.9,FalloffStart=3000,FalloffEnd=8000,
 NormalWeight=1.0,OutlineWidth=1.5,DepthRelativeThreshold=0.015,AAWidth=1.5,CreaseThreshold=0.55,JitterCompensation=1.0,MaxWidthPx=3.0,MinWidthPx=0.6,RefDistance=1500,TaperStrength=0.6)
for k,v in new.items(): MEL.set_material_instance_scalar_parameter_value(mi,k,v)
MEL.update_material_instance(mi)
print('saved',unreal.EditorAssetLibrary.save_asset(p,only_if_is_dirty=False),'Halftone',MEL.get_material_instance_scalar_parameter_value(mi,'HalftoneAmount'))
