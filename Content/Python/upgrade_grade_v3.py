"""Grade V3 — ArtOfShader integration. Adds optional cel-shading, adaptive contrast, selective color."""
import unreal

MAT = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"
MEL = unreal.MaterialEditingLibrary

m = unreal.load_asset(MAT)
if not m:
    raise RuntimeError(f"Missing {MAT}")

custom = [e for e in MEL.get_material_expressions(m) if type(e).__name__ == "MaterialExpressionCustom"][0]
code = custom.get_editor_property("code")
changes = 0

# ── Step 1: Add 3 new scalar parameter expressions ─────────────────────
print("=== Adding V3 scalar parameters ===")
# Check if params already exist
existing_params = set()
for expr in MEL.get_material_expressions(m) or []:
    try: existing_params.add(str(expr.get_editor_property("parameter_name")))
    except: pass

new_params = [
    ("CelSteps", 0.0, 0.0, 8.0, "V3 Cel-Shading"),
    ("DynamicContrast", 0.0, 0.0, 1.0, "V3 Adaptive"),
    ("SelectiveStrength", 0.0, 0.0, 1.0, "V3 Adaptive"),
    ("KeepColorHue", 0.0, 0.0, 1.0, "V3 Adaptive"),
]
y = 3000
for name, default, smin, smax, group in new_params:
    if name not in existing_params:
        expr = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1200, y)
        expr.set_editor_property("parameter_name", name)
        expr.set_editor_property("default_value", default)
        expr.set_editor_property("slider_min", smin)
        expr.set_editor_property("slider_max", smax)
        expr.set_editor_property("group", group)
        y += 50
        print(f"  [OK] {name} created")
    else:
        print(f"  [SKIP] {name} already exists")

# ── Step 2: Inject V3 code block before the return ────────────────────
old_return = "return lerp(src,max(split,0.0),g);"

v3_block = """
// ---- V3 ART OF SHADER INTEGRATION -----------------------------------
// ColorQuantize — cel-shading posterization. Reduces color bands to N steps.
if (CelSteps > 0.5) {
    float steps = max(round(CelSteps), 2.0);
    split = floor(split * steps) / steps;
}
// DynamicContrast — adaptive mid-tone contrast boost.
if (DynamicContrast > 0.001) {
    float mid = dot(split, float3(0.2126, 0.7152, 0.0722));
    float boost = 1.0 + DynamicContrast * 2.0;
    float adapted = (mid - 0.18) * boost + 0.18;
    split *= max(adapted / max(mid, 1e-5), 0.0);
}
// SelectiveGrayscale — keep one hue, desaturate the rest.
if (SelectiveStrength > 0.001) {
    float luma = dot(split, float3(0.2126, 0.7152, 0.0722));
    float3 hsv = float3(0.0, 0.0, luma);
    float mx = max(split.r, max(split.g, split.b));
    float mn = min(split.r, min(split.g, split.b));
    float delta = mx - mn;
    if (delta > 0.001) {
        if (split.r >= mx) hsv.x = (split.g - split.b) / delta;
        else if (split.g >= mx) hsv.x = 2.0 + (split.b - split.r) / delta;
        else hsv.x = 4.0 + (split.r - split.g) / delta;
        hsv.x = frac(hsv.x / 6.0 + 1.0);
    }
    float hueDist = abs(hsv.x - KeepColorHue);
    hueDist = min(hueDist, 1.0 - hueDist);
    float desat = saturate(hueDist * 4.0 - 0.5) * SelectiveStrength;
    split = lerp(split, float3(luma, luma, luma), desat);
}
// -------------------------------------------------------------------------
"""

if old_return in code:
    code = code.replace(old_return, v3_block + old_return)
    changes += 1
    print("[OK] V3 block inserted before return")
else:
    print("[WARN] Old return pattern not found — trying alternative")
    # Try finding just 'return lerp' without the exact match
    for alt in ["return lerp(src,", "return lerp(src, max(split, 0.0), g)"]:
        if alt in code:
            idx = code.find(alt)
            code = code[:idx] + v3_block + code[idx:]
            changes += 1
            print(f"[OK] V3 block inserted via partial match '{alt[:30]}'")
            break

# ── Step 3: Write back ────────────────────────────────────────────────
if changes > 0:
    custom.set_editor_property("code", code)
    # Recompile isn't possible via Custom HLSL code change alone if we changed pin count
    # But we only changed code, not pins, so it should work
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    print(f"\n[DONE] V3 applied — {changes} changes, code length {len(code)}")
else:
    print("\n[NOOP] No changes — may already be V3")
