"""Map Gaea exports once across SeaAbove; preserve detail UVs on the shared master."""
import json
from pathlib import Path
import unreal
ROOT=Path("C:/EnvironmentPortfolio/BS_GodFile")
M="/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape"
MI="/Game/Gaea/Glacier/Materials/MI_Glacier_Landscape_Layered"
lib=unreal.MaterialEditingLibrary
mat=unreal.load_asset(M)
mi=unreal.load_asset(MI)
before=json.loads((ROOT/"Saved/Audit/sea_above_gaea_uv_before.json").read_text())
land=next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class().get_name()=="Landscape")
center,extent=land.get_actor_bounds(False)
origin=[center.x-extent.x,center.y-extent.y,0]
size=[extent.x*2,extent.y*2,1]
def node(cls,x,y):
    e=lib.create_material_expression(mat,cls,x,y)
    assert e
    return e
def wire(a,b,pin="",output=""):
    assert lib.connect_material_expressions(a,output,b,pin), (a,b,pin)
mat.modify()
wp=node(unreal.MaterialExpressionWorldPosition,-3400,-1800)
mn=node(unreal.MaterialExpressionVectorParameter,-3400,-1600)
mn.set_editor_property("parameter_name","GaeaLandscapeMin")
mn.set_editor_property("default_value",unreal.LinearColor(*origin,0))
sz=node(unreal.MaterialExpressionVectorParameter,-3400,-1400)
sz.set_editor_property("parameter_name","GaeaLandscapeSize")
sz.set_editor_property("default_value",unreal.LinearColor(*size,0))
sub=node(unreal.MaterialExpressionSubtract,-3100,-1800)
wire(wp,sub,"A");wire(mn,sub,"B")
div=node(unreal.MaterialExpressionDivide,-2900,-1800)
wire(sub,div,"A");wire(sz,div,"B")
uv=node(unreal.MaterialExpressionComponentMask,-2700,-1800)
uv.set_editor_property("r",True);uv.set_editor_property("g",True)
uv.set_editor_property("b",False);uv.set_editor_property("a",False)
wire(div,uv)
color_names={"Ground_Albedo","Rock_Albedo","Grass_Albedo","Snow_Albedo","Water_Albedo"}
changed=[]
for n in before["nodes"]:
    name=n.get("props",{}).get("ParameterName","")
    if n["class"]!="TextureSampleParameter2D" or not (name in color_names or name.startswith("Gaea_")):
        continue
    e=unreal.find_object(mat,n["id"]);assert e
    if name in color_names:
        connection=next((c for c in before['connections'] if c['to']==n['id'] and c['to_pin']=='Coordinates'),None)
        old=unreal.find_object(mat,connection['from']) if connection else None
        if old is None:
            old=node(unreal.MaterialExpressionTextureCoordinate,-3100,-1100)
        sw=node(unreal.MaterialExpressionStaticSwitchParameter,n["pos"][0]-220,n["pos"][1]-100)
        sw.set_editor_property("parameter_name","bGaeaWholeLandscapeColor")
        sw.set_editor_property("default_value",False)
        wire(uv,sw,"True");wire(old,sw,"False")
        wire(sw,e,"UVs")
    else:
        wire(uv,e,"UVs")
        e.set_editor_property("sampler_source",unreal.SamplerSourceMode.SSM_CLAMP_WORLD_GROUP_SETTINGS)
    changed.append({"node":n["id"],"parameter":name})
lib.set_material_instance_vector_parameter_value(mi,"GaeaLandscapeMin",unreal.LinearColor(*origin,0))
lib.set_material_instance_vector_parameter_value(mi,"GaeaLandscapeSize",unreal.LinearColor(*size,0))
lib.set_material_instance_texture_parameter_value(mi,"Ground_Albedo",unreal.load_asset("/Game/Gaea/Glacier/Textures/T_Glacier_ColorErosion"))
blend=unreal.find_object(mat,'MaterialExpressionLandscapeLayerBlend_5')
for expression,layer in [('MaterialExpressionTextureSampleParameter2D_6','Ground'),('MaterialExpressionTextureSampleParameter2D_8','Grass'),('MaterialExpressionTextureSampleParameter2D_11','Rock')]:
    wire(unreal.find_object(mat,expression),blend,'Layer '+layer,'RGB')
lib.recompile_material(mat)
lib.update_material_instance(mi)
(ROOT/"Saved/Audit/sea_above_gaea_uv_applied.json").write_text(json.dumps({"origin":origin,"size":size,"changed":changed,"uv_corners":[[0,0],[1,1]],"saved":False},indent=2))
print("Gaea UV wiring applied",json.dumps(changed))
