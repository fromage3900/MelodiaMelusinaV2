"""Rebuild triplanar on M_Master_Toon_Universal - INLINE (no MF_Triplanar).

MF_Triplanar is broken (internal TextureSamples unwired to its Tex input) and
MaterialFunction internals are not editable from Python, so this builds the
triplanar base-color path directly in the master instead. World-position 3-axis
projection sampling the EXISTING 'Albedo' param (so instance texture overrides
apply - no checkerboard), normal-weighted blend, gated behind bTriplanar_Active
(default OFF = current UV base, zero change).

Run after editor relaunch (Monolith run_python):
  import rebuild_master_triplanar as t; t.build()

Verify with material_query.get_compilation_stats -> is_compiled True afterward.
Group: 02 | Triplanar. Params: TriplanarWorldScale (~0.01=1m), TriplanarSharpness.
"""
from __future__ import annotations

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"


def build() -> str:
    import unreal
    MEL = unreal.MaterialEditingLibrary
    m = unreal.EditorAssetLibrary.load_asset(MASTER)
    E = MEL.get_material_expressions(m)
    # idempotency: skip if already built
    if any(isinstance(e, unreal.MaterialExpressionStaticSwitchParameter)
           and str(e.get_editor_property("parameter_name")) == "bTriplanar_Active" for e in E):
        return "bTriplanar_Active already present - skipping (already built)"
    byname = {e.get_name(): e for e in E}
    bsdf = next(e for e in E if e.get_name() == "MaterialExpressionSubstrateToonBSDF_4")
    base_src = MEL.get_inputs_for_material_expression(m, bsdf)[0]  # current BaseColor
    albedo = next(e for e in E if e.get_class().get_name().endswith("TextureObjectParameter")
                  and str(e.get_editor_property("parameter_name")) == "Albedo")
    con = MEL.connect_material_expressions
    GRP = "02 | Triplanar"

    def mk(cls, x, y):
        return MEL.create_material_expression(m, cls, x, y)

    def sp(nm, dv, lo, hi, y):
        p = mk(unreal.MaterialExpressionScalarParameter, 2400, y)
        p.set_editor_property("parameter_name", nm)
        p.set_editor_property("default_value", dv)
        p.set_editor_property("slider_min", lo)
        p.set_editor_property("slider_max", hi)
        p.set_editor_property("group", GRP)
        return p

    def mask(src, r, g, b, y):
        cm = mk(unreal.MaterialExpressionComponentMask, 2750, y)
        cm.set_editor_property("r", r); cm.set_editor_property("g", g)
        cm.set_editor_property("b", b); cm.set_editor_property("a", False)
        con(src, "", cm, "")
        return cm

    def sample(uv, y):
        ts = mk(unreal.MaterialExpressionTextureSample, 3050, y)
        ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
        con(albedo, "", ts, "TextureObject")
        con(uv, "", ts, "UVs")
        return ts

    scale = sp("TriplanarWorldScale", 0.01, 0.001, 0.2, -3800)
    sharp = sp("TriplanarSharpness", 4.0, 1.0, 16.0, -3740)
    wp = mk(unreal.MaterialExpressionWorldPosition, 2500, -3650)
    wps = mk(unreal.MaterialExpressionMultiply, 2620, -3650)
    con(wp, "", wps, "A"); con(scale, "", wps, "B")
    # projection UVs: YZ (faces X), XZ (faces Y), XY (faces Z)
    uvYZ = mask(wps, False, True, True, -3720)
    uvXZ = mask(wps, True, False, True, -3620)
    uvXY = mask(wps, True, True, False, -3520)
    sYZ = sample(uvYZ, -3720); sXZ = sample(uvXZ, -3620); sXY = sample(uvXY, -3520)
    # weights from vertex normal
    vn = mk(unreal.MaterialExpressionVertexNormalWS, 2500, -3400)
    an = mk(unreal.MaterialExpressionAbs, 2620, -3400); con(vn, "", an, "")
    anp = mk(unreal.MaterialExpressionPower, 2740, -3400)
    con(an, "", anp, "Base"); con(sharp, "", anp, "Exp")
    wx = mask(anp, True, False, False, -3400)
    wy = mask(anp, False, True, False, -3360)
    wz = mask(anp, False, False, True, -3320)
    ssum = mk(unreal.MaterialExpressionAdd, 3200, -3380)
    a2 = mk(unreal.MaterialExpressionAdd, 3120, -3390)
    con(wx, "", a2, "A"); con(wy, "", a2, "B")
    con(a2, "", ssum, "A"); con(wz, "", ssum, "B")
    # weighted sum
    def wmul(s, w, y):
        mo = mk(unreal.MaterialExpressionMultiply, 3300, y)
        con(s, "", mo, "A"); con(w, "", mo, "B"); return mo
    mYZ = wmul(sYZ, wx, -3720); mXZ = wmul(sXZ, wy, -3620); mXY = wmul(sXY, wz, -3520)
    sum1 = mk(unreal.MaterialExpressionAdd, 3450, -3650)
    con(mYZ, "", sum1, "A"); con(mXZ, "", sum1, "B")
    sum2 = mk(unreal.MaterialExpressionAdd, 3560, -3600)
    con(sum1, "", sum2, "A"); con(mXY, "", sum2, "B")
    blended = mk(unreal.MaterialExpressionDivide, 3680, -3600)
    con(sum2, "", blended, "A"); con(ssum, "", blended, "B")
    # gated switch
    sw = mk(unreal.MaterialExpressionStaticSwitchParameter, 3820, -3560)
    sw.set_editor_property("parameter_name", "bTriplanar_Active")
    sw.set_editor_property("default_value", False)
    sw.set_editor_property("group", GRP)
    con(base_src, "", sw, "False"); con(blended, "", sw, "True")
    con(sw, "", bsdf, "BaseColor")
    MEL.recompile_material(m)
    ok = unreal.EditorAssetLibrary.save_asset(MASTER, only_if_is_dirty=False)
    msg = f"inline triplanar built (bTriplanar_Active default OFF) | saved={ok}"
    print(msg)
    return msg


if __name__ == "__main__":
    build()
