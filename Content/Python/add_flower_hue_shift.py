"""Adds MelodiaHueShift (hue rotation of the flower albedo, default 0 = unchanged) to M_MelodiaPlant_Wind.
Backup first: Saved/Backups/FlowerMaster_20261004/M_MelodiaPlant_Wind.uasset. Run inside the editor (idempotent)."""
import unreal
L = unreal.MaterialEditingLibrary
P = "/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind"
m = unreal.load_asset(P)
assert m, "master missing"

# idempotent: bail if already added
existing = [e for e in L.get_material_expressions(m) if str(e.get_editor_property("desc")) == "HueShift:Rotate"]
if existing:
    print("already present")
else:
    mf = unreal.find_object(m, "MaterialExpressionMaterialFunctionCall_2")
    bsdf = unreal.find_object(m, "MaterialExpressionSubstrateToonBSDF_0")
    assert mf and bsdf, ("nodes", mf, bsdf)
    m.modify()

    cust = L.create_material_expression(m, unreal.MaterialExpressionCustom, 1400, 0)
    cust.set_editor_property("desc", "HueShift:Rotate")
    cust.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for n in ("Color", "Shift"):
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    cust.set_editor_property("inputs", ins)
    cust.set_editor_property("code", """float a = Shift * 6.2831853;
float c = cos(a);
float s = sin(a);
float3 k = float3(0.57735027, 0.57735027, 0.57735027);
float3 r = Color * c + cross(k, Color) * s + k * dot(k, Color) * (1.0 - c);
return max(r, 0.0);""")

    sp = L.create_material_expression(m, unreal.MaterialExpressionScalarParameter, 1200, 120)
    sp.set_editor_property("parameter_name", "MelodiaHueShift")
    sp.set_editor_property("default_value", 0.0)
    sp.set_editor_property("slider_min", 0.0)
    sp.set_editor_property("slider_max", 1.0)
    sp.set_editor_property("group", "Melodia Wind Hue")
    sp.set_editor_property("desc", "HueShift:Amount (turns, 0 = authored colour)")

    assert L.connect_material_expressions(mf, "Color", cust, "Color")
    assert L.connect_material_expressions(sp, "", cust, "Shift")
    assert L.connect_material_expressions(cust, "", bsdf, "BaseColor")
    print("wired")

L.recompile_material(m)
ok = unreal.EditorAssetLibrary.save_loaded_asset(m, False)
st = L.get_statistics(m)
print("saved", ok, "ps_instr", st.get_editor_property("num_pixel_shader_instructions"))
names = [str(n) for n in L.get_scalar_parameter_names(m)]
print("has MelodiaHueShift:", "MelodiaHueShift" in names)
