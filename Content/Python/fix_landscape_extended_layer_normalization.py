"""Normalize weighted extended layers before coverage interpolation.

Prevents applying snow/water/mud/path weights twice. Maintains the existing
coverage control and bUseExtendedLayers selector. Tagged and idempotent.
"""
import unreal
lib = unreal.MaterialEditingLibrary
m = unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape')
expressions = list(lib.get_material_expressions(m))
def existing(name):
    result = unreal.find_object(m, name)
    assert result, name
    return result
def node(cls, tag, x, y):
    result = next((e for e in expressions if str(e.get_editor_property('desc')) == tag), None)
    if result is None:
        result = lib.create_material_expression(m, cls, x, y)
        result.set_editor_property('desc', tag)
        expressions.append(result)
    return result
def wire(a, b, pin='', out=''):
    assert lib.connect_material_expressions(a, out, b, pin), (a.get_name(), b.get_name(), pin)
m.modify()
denominator = node(unreal.MaterialExpressionMax, 'Extended:SafeWeightSum', -600, -1900)
denominator.set_editor_property('const_b', 0.000001)
wire(existing('MaterialExpressionAdd_5'), denominator, 'A')
for suffix, source, destination, y in [
    ('Colour', 'MaterialExpressionAdd_8', 'MaterialExpressionStaticSwitchParameter_2', -1750),
    ('Normal', 'MaterialExpressionAdd_11', 'MaterialExpressionStaticSwitchParameter_3', -1550),
]:
    divide = node(unreal.MaterialExpressionDivide, 'Extended:Normalized' + suffix, -350, y)
    wire(existing(source), divide, 'A')
    wire(denominator, divide, 'B')
    wire(divide, existing(destination), 'True')
normal = node(unreal.MaterialExpressionNormalize, 'Extended:FinalUnitNormal', 100, 300)
wire(existing('MaterialExpressionLinearInterpolate_9'), normal)
wire(normal, existing('MaterialExpressionSubstrateToonBSDF_1'), 'Normal')
lib.recompile_material(m)
assert unreal.EditorAssetLibrary.save_loaded_asset(m, False)
print('Saved extended-layer normalization and final unit normal.')
