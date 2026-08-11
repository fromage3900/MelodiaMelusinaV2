"""Stage 2 Pass A of the M_Master_Toon_Universal professional review
(Docs/Production/UNIVERSAL_MASTER_NODE_REVIEW.md): pure ease-of-use retrofit,
zero visual change by construction.

  1. Slider clamps: every ScalarParameter gets slider_min/slider_max by name
     pattern (defaults untouched -- only the UI range is constrained, fixing
     the 5-billion-slider disease seen on MI_IridescentRock).
  2. Group hygiene: Itto* params regroup to 'InkWear', Madoka* to 'VeinGlow'
     (user decision 2026-07-03: absorb as generic env families; NAMES are
     kept -- renaming would break the 9 live instances' overrides).
  3. Advanced ColorRamp insert at the BaseColor tail (traced splice:
     Lerp_310 -> {MaterialFunctionCall_0.'BaseColorIn (V3)',
     StaticSwitchParameter_0.'False'}): luminance-masked MF_ColorRamp3,
     lerped in by RampStrength (default 0 = bypass -> zero visual change).
     Same param names/groups as M_Master_Nikki for muscle memory.

Run inside the editor (Monolith run_python):
  import universal_master_stage2 as s2
  s2.run()
"""
from __future__ import annotations

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MF_RAMP = "/Game/EnvSandbox/Materials/Functions/MF_ColorRamp3"

# (pattern, slider_min, slider_max) -- first match wins. Defaults NOT changed.
CLAMP_RULES = [
    ("*BlendAmount", 0.0, 1.0), ("*Strength", 0.0, 2.0), ("*Amount", 0.0, 2.0),
    ("*Intensity", 0.0, 4.0), ("*Power", 0.0, 16.0), ("*Bias", -2.0, 2.0),
    ("*Width", 0.0, 4.0), ("*Softness", 0.0, 2.0), ("*Sharpness", 0.0, 8.0),
    ("*Threshold", 0.0, 4.0), ("*Radius", 0.0, 4.0), ("*Lift", -1.0, 1.0),
    ("*Contrast", 0.0, 4.0), ("*Sens", 0.0, 16.0), ("*Clamp", 0.0, 8.0),
    ("UVScale", 0.05, 10.0), ("*UVScale", 0.05, 10.0),
    ("MacroScale", 1.0, 512.0), ("DetailTiling", 0.1, 64.0),
    ("SparkleScale", 1.0, 1024.0), ("*PatternScale", 0.1, 32.0),
    ("*Scale", 0.0, 64.0), ("*Speed", 0.0, 8.0), ("*Steps", 1.0, 32.0),
    ("*Tiling", 0.01, 64.0), ("*Weight", -1.0, 2.0), ("*Depth", 0.0, 4.0),
    ("Roughness", 0.0, 1.5), ("Metallic", 0.0, 1.0),
    ("DistanceFadeStart", 0.0, 100000.0), ("DistanceFadeEnd", 100.0, 500000.0),
    ("*Bands", 1.0, 32.0), ("*Mix", 0.0, 1.0), ("*Blend", 0.0, 1.0),
    ("*Fade", 0.0, 1.0), ("*Boost", 0.0, 4.0),
]

REGROUP = [("Itto*", "InkWear"), ("Madoka*", "VeinGlow")]


def run() -> dict:
    import fnmatch
    import unreal
    MEL = unreal.MaterialEditingLibrary
    mat = unreal.EditorAssetLibrary.load_asset(MASTER)
    exprs = list(MEL.get_material_expressions(mat))

    clamped = 0
    regrouped = 0
    for e in exprs:
        try:
            pn = str(e.get_editor_property("parameter_name"))
        except Exception:
            continue
        if not pn or pn == "None":
            continue
        # regroup
        for pat, grp in REGROUP:
            if fnmatch.fnmatch(pn, pat):
                try:
                    e.set_editor_property("group", grp)
                    regrouped += 1
                except Exception:
                    pass
                break
        # clamp scalars only
        if isinstance(e, unreal.MaterialExpressionScalarParameter):
            for pat, lo, hi in CLAMP_RULES:
                if fnmatch.fnmatch(pn, pat):
                    try:
                        e.set_editor_property("slider_min", lo)
                        e.set_editor_property("slider_max", hi)
                        clamped += 1
                    except Exception:
                        pass
                    break

    # ---- ColorRamp insert at BaseColor tail ----
    def find(name):
        for e in exprs:
            if e.get_name() == name:
                return e
        return None

    tail = find("MaterialExpressionLinearInterpolate_310")
    mfc0 = find("MaterialExpressionMaterialFunctionCall_0")
    sw0 = find("MaterialExpressionStaticSwitchParameter_0")
    ramp_added = False
    already = any(
        (getattr(e, "get_editor_property", None)
         and isinstance(e, unreal.MaterialExpressionScalarParameter)
         and str(e.get_editor_property("parameter_name")) == "RampStrength")
        for e in exprs)
    if tail and mfc0 and sw0 and not already:
        def expr(cls, x, y):
            return MEL.create_material_expression(mat, cls, x, y)

        def sparam(pname, default, lo, hi, x, y):
            p = expr(unreal.MaterialExpressionScalarParameter, x, y)
            p.set_editor_property("parameter_name", pname)
            p.set_editor_property("default_value", default)
            p.set_editor_property("slider_min", lo)
            p.set_editor_property("slider_max", hi)
            p.set_editor_property("group", "ColorRamp")
            return p

        def vparam(pname, rgba, x, y):
            p = expr(unreal.MaterialExpressionVectorParameter, x, y)
            p.set_editor_property("parameter_name", pname)
            p.set_editor_property("default_value", unreal.LinearColor(*rgba))
            p.set_editor_property("group", "ColorRamp")
            return p

        con = MEL.connect_material_expressions
        X, Y = 5200, -2400  # free area
        lum_w = expr(unreal.MaterialExpressionConstant3Vector, X, Y + 260)
        lum_w.set_editor_property("constant", unreal.LinearColor(0.299, 0.587, 0.114, 0.0))
        lum = expr(unreal.MaterialExpressionDotProduct, X + 180, Y + 220)
        con(tail, "", lum, "A")
        con(lum_w, "", lum, "B")
        r_low = vparam("RampLow", (0.20, 0.15, 0.30, 1), X, Y - 260)
        r_mid = vparam("RampMid", (0.85, 0.60, 0.75, 1), X, Y - 130)
        r_high = vparam("RampHigh", (1.0, 0.95, 0.90, 1), X, Y)
        r_pos = sparam("RampPosMid", 0.5, 0.05, 0.95, X, Y + 90)
        r_con = sparam("RampContrast", 1.0, 0.1, 4.0, X, Y + 140)
        r_str = sparam("RampStrength", 0.0, 0.0, 1.0, X, Y + 190)
        ramp = expr(unreal.MaterialExpressionMaterialFunctionCall, X + 380, Y - 100)
        ramp.set_editor_property("material_function", unreal.EditorAssetLibrary.load_asset(MF_RAMP))
        con(r_low, "", ramp, "RampLow")
        con(r_mid, "", ramp, "RampMid")
        con(r_high, "", ramp, "RampHigh")
        con(r_pos, "", ramp, "RampPosMid")
        con(lum, "", ramp, "Mask")
        con(r_con, "", ramp, "RampContrast")
        graded = expr(unreal.MaterialExpressionLinearInterpolate, X + 620, Y - 40)
        con(tail, "", graded, "A")
        con(ramp, "Color", graded, "B")
        con(r_str, "", graded, "Alpha")
        # splice into both consumers
        con(graded, "", mfc0, "BaseColorIn (V3)")
        con(graded, "", sw0, "False")
        ramp_added = True

    MEL.recompile_material(mat)
    ok = unreal.EditorAssetLibrary.save_asset(MASTER, only_if_is_dirty=False)
    out = {"clamped": clamped, "regrouped": regrouped,
           "ramp_added": ramp_added, "saved": bool(ok)}
    print(out)
    return out


if __name__ == "__main__":
    run()
