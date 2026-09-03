"""Wire the layered material stack (layers 2 + 3) on M_Master_Toon_Universal.

Default-neutral: all blend factor scalars default 0 so visuals are identical.
Only purpose-built rewires touch existing connections.
"""
import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MEL = unreal.MaterialEditingLibrary
STACK = "07 | Material Stack"


def desc_label(e):
    try:
        d = e.get_editor_property("description")
        if d:
            return str(d)
    except Exception:
        pass
    return e.get_name()


def find_expr(mat, predicate):
    for e in MEL.get_material_expressions(mat) or []:
        if predicate(e):
            return e
    return None


def find_custom(mat, label_substring):
    return find_expr(mat, lambda e: e.get_class().get_name() == "MaterialExpressionCustom"
                     and label_substring in desc_label(e))


def find_source(mat, consumer, pin):
    ins = MEL.get_inputs_for_material_expression(mat, consumer)
    names = list(MEL.get_material_expression_input_names(consumer) or [])
    try:
        idx = names.index(pin)
    except ValueError:
        idx = None
    if idx is not None and idx < len(ins):
        return ins[idx]
    return None


def new_param(mat, cls, pname, group, x, y):
    e = MEL.create_material_expression(mat, cls, x, y)
    return e


def main():
    mat = unreal.load_asset(MASTER)
    if not mat:
        print("[WireStack] material not found")
        return
    print("[WireStack] loaded %s" % MASTER)

    if find_expr(mat, lambda e: _is_param(e, "Stack2BlendStrength")):
        print("[WireStack] Stack2BlendStrength exists — already wired, skipping")
        MEL.recompile_material(mat)
        unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
        return

    bsdf = find_expr(mat, lambda e: e.get_class().get_name().startswith("MaterialExpressionSubstrateToonBSDF"))
    if not bsdf:
        print("[WireStack] BSDF not found — abort")
        return

    sw10 = find_source(mat, bsdf, "BaseColor")
    sw11 = find_source(mat, bsdf, "Roughness")
    sw12 = find_source(mat, bsdf, "Normal")
    print("[WireStack] BaseColor switch=%s Roughness switch=%s Normal switch=%s Metallic=%s"
          % (sw10.get_name() if sw10 else None,
             sw11.get_name() if sw11 else None,
             sw12.get_name() if sw12 else None,
             find_source(mat, bsdf, "Metallic").get_name() if find_source(mat, bsdf, "Metallic") else None))
    if not (sw10 and sw11 and sw12):
        print("[WireStack] switch chain incomplete — abort")
        return

    base_true = find_source(mat, sw10, "True")
    rough_true = find_source(mat, sw11, "True")
    norm_true = find_source(mat, sw12, "True")
    metal_src = find_source(mat, bsdf, "Metallic")
    print("[WireStack] baseTrue=%s roughTrue=%s normTrue=%s metal=%s"
          % (base_true.get_name() if base_true else None,
             rough_true.get_name() if rough_true else None,
             norm_true.get_name() if norm_true else None,
             metal_src.get_name() if metal_src else None))

    # ---------- shared gates ----------
    one1 = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant2Vector, -2000, 300)
    one1.set_editor_property("r", 1.0)
    one1.set_editor_property("g", 1.0)

    # Layer 2 = trim/embroidery
    s2_alb = find_expr(mat, lambda e: _is_param(e, "Stack2_Albedo"))
    s2_nrm = find_expr(mat, lambda e: _is_param(e, "Stack2_Normal"))
    s2_orm = find_expr(mat, lambda e: _is_param(e, "Stack2_ORM"))
    s2_til = find_expr(mat, lambda e: _is_param(e, "Stack2_Tiling"))
    s2_ms = find_expr(mat, lambda e: _is_param(e, "Stack2_Metallic"))
    s2_rs = find_expr(mat, lambda e: _is_param(e, "Stack2_Roughness"))
    s2_on = find_expr(mat, lambda e: _is_param(e, "bStackLayer2_Active"))

    stack2_uv = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -2400, 300)
    MEL.connect_material_expressions(s2_til, "", stack2_uv, "A")
    MEL.connect_material_expressions(one1, "", stack2_uv, "B")

    def make_sample(tp_obj, uv_src, label):
        s = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -2200, 200)
        MEL.connect_material_expressions(tp_obj, "", s, "TextureObject")
        MEL.connect_material_expressions(uv_src, "", s, "UVs")
        return s

    alb2 = make_sample(s2_alb, stack2_uv, "WireStackStack2AlbedoSample")
    nrm2 = make_sample(s2_nrm, stack2_uv, "WireStackStack2NormalSample")
    orm2 = make_sample(s2_orm, stack2_uv, "WireStackStack2ORMSample")

    stack2_gate = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1500, 200)
    MEL.connect_material_expressions(s2_on, "", stack2_gate, "B")
    MEL.connect_material_expressions(alb2, "RGB", stack2_gate, "A")
    # Alpha = bStackLayer2_Active bool (defaults False -> 0 contributions from B path)

    stack2_blend = new_param(mat, unreal.MaterialExpressionScalarParameter, "Stack2BlendStrength", STACK, -2200, 500)
    stack2_blend.set_editor_property("default_value", 0.0)
    stack2_blend.set_editor_property("slider_min", 0.0)
    stack2_blend.set_editor_property("slider_max", 1.0)

    color2 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 200)
    MEL.connect_material_expressions(base_true, "", color2, "A")
    MEL.connect_material_expressions(stack2_gate, "", color2, "B")
    MEL.connect_material_expressions(stack2_blend, "", color2, "Alpha")
    MEL.connect_material_expressions(color2, "", sw10, "True")

    rough2 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 340)
    MEL.connect_material_expressions(rough_true, "", rough2, "A")
    MEL.connect_material_expressions(s2_rs, "", rough2, "B")
    MEL.connect_material_expressions(stack2_blend, "", rough2, "Alpha")
    MEL.connect_material_expressions(rough2, "", sw11, "True")

    norm2 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 480)
    MEL.connect_material_expressions(norm_true, "", norm2, "A")
    MEL.connect_material_expressions(nrm2, "", norm2, "B")
    MEL.connect_material_expressions(stack2_blend, "", norm2, "Alpha")
    MEL.connect_material_expressions(norm2, "", sw12, "True")

    # Layer 3 = jewel overlay
    s3_alb = find_expr(mat, lambda e: _is_param(e, "Stack3_Albedo"))
    s3_nrm = find_expr(mat, lambda e: _is_param(e, "Stack3_Normal"))
    s3_til = find_expr(mat, lambda e: _is_param(e, "Stack3_Tiling"))
    s3_ms = find_expr(mat, lambda e: _is_param(e, "Stack3_Metallic"))
    s3_rs = find_expr(mat, lambda e: _is_param(e, "Stack3_Roughness"))
    s3_on = find_expr(mat, lambda e: _is_param(e, "bStackLayer3_Active"))

    stack3_uv = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -2400, 700)
    MEL.connect_material_expressions(s3_til, "", stack3_uv, "A")
    MEL.connect_material_expressions(one1, "", stack3_uv, "B")

    alb3 = make_sample(s3_alb, stack3_uv, "WireStackStack3AlbedoSample")
    nrm3 = make_sample(s3_nrm, stack3_uv, "WireStackStack3NormalSample")

    stack3_gate = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1500, 700)
    MEL.connect_material_expressions(color2, "", stack3_gate, "A")
    MEL.connect_material_expressions(s3_on, "", stack3_gate, "B")
    MEL.connect_material_expressions(alb3, "RGB", stack3_gate, "B")
    # Alpha = bStackLayer3_Active (default False -> A = color2)

    stack3_blend = new_param(mat, unreal.MaterialExpressionScalarParameter, "Stack3BlendStrength", STACK, -2200, 900)
    stack3_blend.set_editor_property("default_value", 0.0)
    stack3_blend.set_editor_property("slider_min", 0.0)
    stack3_blend.set_editor_property("slider_max", 1.0)

    color3 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 700)
    MEL.connect_material_expressions(color2, "", color3, "A")
    MEL.connect_material_expressions(stack3_gate, "", color3, "B")
    MEL.connect_material_expressions(stack3_blend, "", color3, "Alpha")
    MEL.connect_material_expressions(color3, "", sw10, "True")

    rough3 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 840)
    MEL.connect_material_expressions(rough2, "", rough3, "A")
    MEL.connect_material_expressions(s3_rs, "", rough3, "B")
    MEL.connect_material_expressions(stack3_blend, "", rough3, "Alpha")
    MEL.connect_material_expressions(rough3, "", sw11, "True")

    norm3 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 980)
    MEL.connect_material_expressions(norm2, "", norm3, "A")
    MEL.connect_material_expressions(nrm3, "", norm3, "B")
    MEL.connect_material_expressions(stack3_blend, "", norm3, "Alpha")
    MEL.connect_material_expressions(norm3, "", sw12, "True")

    if metal_src:
        metal2 = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -1200, 1100)
        MEL.connect_material_expressions(metal_src, "", metal2, "A")
        MEL.connect_material_expressions(s3_ms, "", metal2, "B")
        MEL.connect_material_expressions(stack3_blend, "", metal2, "Alpha")
        MEL.connect_material_expressions(metal2, "", bsdf, "Metallic")
        print("[WireStack] Metallic rewired through Stack3MetalGate (default=passthrough)")
    else:
        print("[WireStack] Metallic source not found — left as-is")

    MEL.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, only_if_is_dirty=False)
    print("[WireStack] DONE — stack layers wired, default-neutral")


def _is_param(e, name):
    try:
        return str(e.get_editor_property("parameter_name")) == name
    except Exception:
        return False


main()