"""Independent rock detail colour; Gaea macro coordinates stay untouched.

Idempotent tagged additions. Defaults preserve the existing macro colour.
The runtime projection blend samples both branches before interpolation.
"""
import unreal

lib = unreal.MaterialEditingLibrary
m = unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape')
expressions = list(lib.get_material_expressions(m))

def node(cls, tag, x, y):
    e = next((e for e in expressions if str(e.get_editor_property('desc')) == tag), None)
    if e is None:
        e = lib.create_material_expression(m, cls, x, y)
        e.set_editor_property('desc', tag)
        expressions.append(e)
    return e

def tagged(tag):
    return next(e for e in expressions if str(e.get_editor_property('desc')) == tag)

def wire(a, b, pin='', out=''):
    assert lib.connect_material_expressions(a, out, b, pin), (a.get_name(), b.get_name(), pin)

def scalar(name, value, x, y):
    e = node(unreal.MaterialExpressionScalarParameter, 'RockColour:' + name, x, y)
    e.set_editor_property('parameter_name', name)
    e.set_editor_property('default_value', value)
    e.set_editor_property('group', '03 | Rock Triplanar Detail')
    return e

m.modify()
f = tagged('RockTri:Function')
tex = node(unreal.MaterialExpressionTextureObjectParameter, 'RockColour:Texture', -2600, 2700)
tex.set_editor_property('parameter_name', 'Rock_DetailAlbedo')
tex.set_editor_property('texture', unreal.load_asset('/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures/T_SeaAbove_WetRock_Albedo'))
tex.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
wire(tex, f, 'Tex')

# Same transformed Z-plane coordinates as the triplanar shader; preserves
# scale, rotation and offset when switching to planar projection.
planar = node(unreal.MaterialExpressionCustom, 'RockColour:PlanarSample', -2000, 2700)
names = ['Tex', 'WorldPosition', 'ProjectionOffset', 'ProjectionRotation', 'ProjectionScale']
custom_inputs = []
for name in names:
    ci = unreal.CustomInput()
    ci.set_editor_property('input_name', name)
    custom_inputs.append(ci)
planar.set_editor_property('inputs', custom_inputs)
planar.set_editor_property('output_type', unreal.CustomMaterialOutputType.CMOT_FLOAT3)
planar.set_editor_property('code', '''
float3 sr,cr;
sincos(ProjectionRotation*(3.14159265359/180.0),sr,cr);
float3x3 R=float3x3(
cr.y*cr.z,sr.x*sr.y*cr.z-cr.x*sr.z,cr.x*sr.y*cr.z+sr.x*sr.z,
cr.y*sr.z,sr.x*sr.y*sr.z+cr.x*cr.z,cr.x*sr.y*sr.z-sr.x*cr.z,
-sr.y,sr.x*cr.y,cr.x*cr.y);
float2 uv=(mul(R,WorldPosition+ProjectionOffset)*max(abs(ProjectionScale),0.00001)).xy;
return Texture2DSampleGrad(Tex,TexSampler,uv,ddx(uv),ddy(uv)).rgb;
''')
sources = dict(zip(map(str, lib.get_material_expression_input_names(f)), lib.get_inputs_for_material_expression(m, f)))
for name in names:
    assert sources[name], name
    wire(sources[name], planar, name)
blend = node(unreal.MaterialExpressionLinearInterpolate, 'RockColour:ProjectionBlend', -1700, 2700)
wire(planar, blend, 'A')
wire(f, blend, 'B', 'Color')
wire(tagged('RockTri:BlendRange'), blend, 'Alpha')

# Multiplicative modulation around a configurable linear-light reference.
# Strength zero gives an exact identity; static off removes all colour samples.
reference = scalar('Rock_DetailAlbedoReference', 0.18, -2000, 3000)
safe = node(unreal.MaterialExpressionMax, 'RockColour:SafeReference', -1800, 3000)
safe.set_editor_property('const_b', 0.001)
wire(reference, safe, 'A')
ratio = node(unreal.MaterialExpressionDivide, 'RockColour:RelativeColour', -1500, 2700)
wire(blend, ratio, 'A')
wire(safe, ratio, 'B')
strength = scalar('Rock_DetailAlbedoStrength', 0.0, -1700, 3200)
clamp = node(unreal.MaterialExpressionSaturate, 'RockColour:StrengthRange', -1500, 3200)
wire(strength, clamp)
modulation = node(unreal.MaterialExpressionLinearInterpolate, 'RockColour:Modulation', -1300, 2700)
modulation.set_editor_property('const_a', 1.0)
wire(ratio, modulation, 'B')
wire(clamp, modulation, 'Alpha')
macro = unreal.find_object(m, 'MaterialExpressionTextureSampleParameter2D_11')
combined = node(unreal.MaterialExpressionMultiply, 'RockColour:MacroTimesDetail', -1100, 2700)
wire(macro, combined, 'A')
wire(modulation, combined, 'B')
switch = node(unreal.MaterialExpressionStaticSwitchParameter, 'RockColour:Enabled', -900, 2700)
switch.set_editor_property('parameter_name', 'bRockDetailAlbedo')
switch.set_editor_property('default_value', False)
switch.set_editor_property('group', '03 | Rock Triplanar Detail')
wire(combined, switch, 'True')
wire(macro, switch, 'False')
wire(switch, unreal.find_object(m, 'MaterialExpressionLandscapeLayerBlend_5'), 'Layer Rock')
lib.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m, False)
print('Saved independent rock colour detail; static default off, strength zero.')
