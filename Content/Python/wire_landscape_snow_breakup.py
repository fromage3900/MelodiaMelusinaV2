"""Add opt-in, world-anchored snow coverage refinement to existing snow path."""
import unreal
from pathlib import Path
lib=unreal.MaterialEditingLibrary
code=Path('C:/EnvironmentPortfolio/BS_GodFile/Content/Python/shaders/landscape_snow_breakup.hlsl').read_text()
def build(m, proof=False):
    expressions=list(lib.get_material_expressions(m))
    def node(cls,tag,x,y):
        e=next((e for e in expressions if str(e.get_editor_property('desc'))==tag),None)
        if e is None:
            e=lib.create_material_expression(m,cls,x,y)
            e.set_editor_property('desc',tag);expressions.append(e)
        return e
    def wire(a,b,pin=''):
        assert lib.connect_material_expressions(a,'',b,pin),(a.get_name(),b.get_name(),pin)
    def scalar(name,value,x,y):
        e=node(unreal.MaterialExpressionScalarParameter,'SnowBreakup:'+name,x,y)
        e.set_editor_property('parameter_name',name);e.set_editor_property('default_value',value)
        e.set_editor_property('group','04 | Snow Coverage Detail');return e
    m.modify()
    custom=node(unreal.MaterialExpressionCustom,'SnowBreakup:Coverage',-1800,-2400)
    custom.set_editor_property('code',code)
    custom.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    inputs=[]
    for name in ['Coverage','WorldPosition','WorldSizeCM','Strength']:
        ci=unreal.CustomInput();ci.set_editor_property('input_name',name);inputs.append(ci)
    custom.set_editor_property('inputs',inputs)
    if proof:
        coverage=scalar('ProofCoverage',0.5,-2400,-2300)
    else:
        coverage=unreal.find_object(m,'MaterialExpressionAdd_2')
        assert coverage
    wire(coverage,custom,'Coverage')
    wire(node(unreal.MaterialExpressionWorldPosition,'SnowBreakup:WorldPosition',-2400,-2500),custom,'WorldPosition')
    wire(scalar('Snow_BreakupWorldSizeCM',40 if proof else 600,-2400,-2700),custom,'WorldSizeCM')
    wire(scalar('Snow_BreakupStrength',0.5 if proof else 0.15,-2400,-2900),custom,'Strength')
    if proof:
        assert lib.connect_material_property(custom,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        m.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    else:
        switch=node(unreal.MaterialExpressionStaticSwitchParameter,'SnowBreakup:Enabled',-1500,-2400)
        switch.set_editor_property('parameter_name','bSnowCoverageBreakup')
        switch.set_editor_property('default_value',False)
        switch.set_editor_property('group','04 | Snow Coverage Detail')
        wire(custom,switch,'True');wire(coverage,switch,'False')
        for name,pin in [('MaterialExpressionAdd_3','A'),('MaterialExpressionMultiply_25','B'),('MaterialExpressionMultiply_34','B')]:
            wire(switch,unreal.find_object(m,name),pin)
    lib.recompile_material(m)
    assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)

master=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape')
build(master)
folder='/Game/EnvSandbox/Materials/Validation'
proof=unreal.load_asset(folder+'/M_Snow_CoverageProof')
if not proof:
    proof=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Snow_CoverageProof',folder,unreal.Material,unreal.MaterialFactoryNew())
build(proof,True)
print('Saved optional snow coverage refinement and active proof material.')
