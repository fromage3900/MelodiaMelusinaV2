"""Add all 6 feature systems to M_Master_Toon_Universal (fixed, consolidated).

Fixes over the delegate scripts:
  - Custom HLSL node title property is `description`, NOT `name`.
  - Finalize with recompile_material + save_loaded_asset (rebuild_material_editing_data
    does not exist in UE 5.8 Python).
  - Params that already exist (fabric + triplanar from the first pass) are skipped.

Installs:
  TriplanarUVs       (triplanar single-calc gated by bTriplanar_Active)
  FabricWeaveNormal  (fabric anisotropy weave lane)
  Gemstone lane      (8 params + GemstoneDispersion node)
  Dream compositor   (4 params + DreamCompositor node)
  Material stack     (14 params, layers 2 + 3)
  Face SDF + skin    (7 params + SkinSSS node)
"""
import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MEL = unreal.MaterialEditingLibrary


def existing_names(material) -> set:
    names = set()
    for e in MEL.get_material_expressions(material) or []:
        for prop in ("parameter_name",):
            try:
                raw = e.get_editor_property(prop)
                if raw:
                    names.add(str(raw))
            except Exception:
                continue
    return names


def existing_hlsl(material) -> set:
    names = set()
    for e in MEL.get_material_expressions(material) or []:
        if e.get_class().get_name() == "MaterialExpressionCustom":
            try:
                d = e.get_editor_property("description")
                if d:
                    names.add(str(d))
            except Exception:
                continue
    return names


def _safe_desc(e, desc):
    if not desc:
        return
    for prop in ("description", "desc"):
        try:
            if e.has_editor_property(prop):
                e.set_editor_property(prop, desc)
                return
        except Exception:
            continue


def add_scalar(m, name, default, group, x, y, lo=None, hi=None, desc=None):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("group", group)
    e.set_editor_property("default_value", default)
    if lo is not None:
        e.set_editor_property("slider_min", lo)
    if hi is not None:
        e.set_editor_property("slider_max", hi)
    _safe_desc(e, desc)
    return e


def add_bool(m, name, default, group, x, y, desc=None):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionStaticBoolParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("group", group)
    e.set_editor_property("default_value", default)
    _safe_desc(e, desc)
    return e


def add_vector(m, name, color, group, x, y, desc=None):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("group", group)
    e.set_editor_property("default_value", unreal.LinearColor(*color))
    _safe_desc(e, desc)
    return e


def add_texture(m, name, group, x, y, desc=None):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureObjectParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("group", group)
    _safe_desc(e, desc)
    return e


def add_custom(m, title, code, inputs, output_type, x, y, desc=None):
    e = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, x, y)
    e.set_editor_property("description", title)
    e.set_editor_property("code", code)
    e.set_editor_property("output_type", output_type)
    if desc:
        e.set_editor_property("description", desc)
    if inputs:
        cis = []
        for iname, itype in inputs:
            ci = unreal.CustomInput()
            ci.set_editor_property("input_name", iname)
            cis.append(ci)
        e.set_editor_property("inputs", cis)
    return e


def main():
    m = unreal.load_asset(MASTER)
    if not m:
        unreal.log_error(f"[FixAll] Material not found: {MASTER}")
        return
    unreal.log(f"[FixAll] Loaded {MASTER}")

    known = existing_names(m)
    hlsl = existing_hlsl(m)
    created = []

    # ---------- 1. Triplanar single-calc ----------
    code_tri = """float3 AbsN = abs(Parameters.WorldNormal);
float3 Wt = pow(AbsN, TriplanarSharpness);
Wt /= dot(Wt, float3(1,1,1) + 0.0001);
float2 uvX = Parameters.WorldPosition.yz * TriplanarTiling;
float2 uvY = Parameters.WorldPosition.xz * TriplanarTiling;
float2 uvZ = Parameters.WorldPosition.xy * TriplanarTiling;
float3 uvw = (Parameters.WorldPosition / (TriplanarTiling + 0.0001));
float4 layerUVs = float4(uvX, uvY);
float4 zUV_weights = float4(uvZ, Wt.xy);
float3 weightOut;
weightOut.xy = Wt.xy;
weightOut.z = Wt.z;
return float3(0,0,0);"""
    if "TriplanarUVs" not in hlsl:
        add_custom(m, "TriplanarUVs", code_tri,
                   [("TriplanarSharpness", "float"), ("TriplanarTiling", "float")],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1680, 200)
        created.append("TriplanarUVs")
        unreal.log("[FixAll] Created TriplanarUVs")

    # ---------- 2. Fabric weave normal ----------
    code_fab = """float2 wUV = UV * WeaveScale;
float warp = 0.5 + 0.5 * sin(wUV.x * 6.28318);
float weft = 0.5 + 0.5 * sin(wUV.y * 6.28318);
float pattern = warp * weft;
float3 n;
n.xy = float2(ddx(pattern), ddy(pattern)) * WeaveStrength;
n.z = 1.0;
return normalize(n);"""
    if "FabricWeaveNormal" not in hlsl:
        add_custom(m, "FabricWeaveNormal", code_fab,
                   [("UV", "float2"), ("WeaveScale", "float"), ("WeaveStrength", "float")],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, 240, 240)
        created.append("FabricWeaveNormal")
        unreal.log("[FixAll] Created FabricWeaveNormal")

    # ---------- 3. Gemstone lane ----------
    GEM = "06 | Gemstone"
    if "bGemstone_Active" not in known:
        add_bool(m, "bGemstone_Active", False, GEM, -1720, 700, "Enable gemstone IOR/dispersion lane")
        created.append("bGemstone_Active")
    for nm, dflt, lo, hi in (("IOR", 2.42, 1.0, 3.0), ("Dispersion", 0.044, 0.0, 0.12),
                             ("GemstoneRoughness", 0.02, 0.0, 1.0),
                             ("GlintIntensity", 0.0, 0.0, 2.0),
                             ("GlintScale", 16.0, 1.0, 128.0),
                             ("ChromaticStrength", 0.1, 0.0, 1.0)):
        if nm not in known:
            add_scalar(m, nm, dflt, GEM, -1720, 760 + 90 * (len(created) % 6), lo, hi)
            created.append(nm)
    if "GemstoneTint" not in known:
        add_vector(m, "GemstoneTint", (1, 1, 1, 1), GEM, -1720, 780)
        created.append("GemstoneTint")
    code_gem = """float r = saturate(Rim + Disp);
float g = saturate(Rim);
float b = saturate(Rim - Disp);
return float3(r*r, g*g, b*b);"""
    if "GemstoneDispersion" not in hlsl:
        add_custom(m, "GemstoneDispersion", code_gem,
                   [("Rim", "float"), ("Disp", "float")],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -1720, 920)
        created.append("GemstoneDispersion")
        unreal.log("[FixAll] Created GemstoneDispersion")

    # ---------- 4. Dream glow compositor ----------
    DREAM = "08 Nikki Dream"
    if "DreamIntensity" not in known:
        add_scalar(m, "DreamIntensity", 1.0, DREAM, -1720, 1040, 0.0, 2.0)
        created.append("DreamIntensity")
    if "DreamComposition" not in known:
        add_scalar(m, "DreamComposition", 0.0, DREAM, -1720, 1130, 0.0, 2.0)
        created.append("DreamComposition")
    if "DreamThreshold" not in known:
        add_scalar(m, "DreamThreshold", 0.0, DREAM, -1720, 1220, 0.0, 1.0)
        created.append("DreamThreshold")
    if "DreamWarmth" not in known:
        add_vector(m, "DreamWarmth", (1.0, 0.85, 0.70, 1.0), DREAM, -1720, 1310)
        created.append("DreamWarmth")
    code_dream = """float luma = dot(DreamColor, float3(0.2126, 0.7152, 0.0722));
if (luma < Threshold) return BaseColor;
float3 result;
int mode = (int)round(Composition);
if (mode == 0) result = BaseColor + DreamColor * DreamIntensity;
else if (mode == 1) result = max(BaseColor, DreamColor * DreamIntensity);
else result = 1.0 - (1.0 - BaseColor) * (1.0 - DreamColor * DreamIntensity);
return result;"""
    if "DreamCompositor" not in hlsl:
        add_custom(m, "DreamCompositor", code_dream,
                   [("DreamColor", "float3"), ("BaseColor", "float3"),
                    ("DreamIntensity", "float"), ("Composition", "float"),
                    ("Threshold", "float")],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT3, -1720, 1400)
        created.append("DreamCompositor")
        unreal.log("[FixAll] Created DreamCompositor")

    # ---------- 5. Material stack (layers 2 + 3) ----------
    STACK = "07 | Material Stack"
    if "bStackLayer2_Active" not in known:
        add_bool(m, "bStackLayer2_Active", False, STACK, -1720, 1560)
        created.append("bStackLayer2_Active")
    for nm in ("Stack2_Albedo", "Stack2_Normal", "Stack2_ORM"):
        if nm not in known:
            add_texture(m, nm, STACK, -1720, 1620 + 90 * len(created) % 4)
            created.append(nm)
    for nm, dflt, lo, hi in (("Stack2_Tiling", 1.0, 0.1, 10.0), ("Stack2_Blend", 0.5, 0.0, 1.0),
                             ("Stack2_Metallic", 0.0, 0.0, 1.0), ("Stack2_Roughness", 0.5, 0.0, 1.0)):
        if nm not in known:
            add_scalar(m, nm, dflt, STACK, -1720, 1680 + 90 * (len(created) % 6))
            created.append(nm)
    if "bStackLayer3_Active" not in known:
        add_bool(m, "bStackLayer3_Active", False, STACK, -1720, 1760)
        created.append("bStackLayer3_Active")
    for nm in ("Stack3_Albedo", "Stack3_Normal"):
        if nm not in known:
            add_texture(m, nm, STACK, -1720, 1820 + 90 * len(created) % 4)
            created.append(nm)
    for nm, dflt, lo, hi in (("Stack3_Tiling", 1.0, 0.1, 10.0), ("Stack3_Metallic", 1.0, 0.0, 1.0),
                             ("Stack3_Roughness", 0.1, 0.0, 1.0)):
        if nm not in known:
            add_scalar(m, nm, dflt, STACK, -1720, 1880 + 90 * (len(created) % 6))
            created.append(nm)

    # ---------- 6. Face SDF + skin SSS ----------
    CHAR = "09 | Character"
    if "FaceSDF_Texture" not in known:
        add_texture(m, "FaceSDF_Texture", CHAR, -1720, 1960)
        created.append("FaceSDF_Texture")
    if "FaceSDF_Strength" not in known:
        add_scalar(m, "FaceSDF_Strength", 0.0, CHAR, -1720, 2020, 0.0, 1.0)
        created.append("FaceSDF_Strength")
    if "FaceSDF_Tiling" not in known:
        add_scalar(m, "FaceSDF_Tiling", 1.0, CHAR, -1720, 2110, 0.1, 10.0)
        created.append("FaceSDF_Tiling")
    if "bFaceSDF_UV1" not in known:
        add_bool(m, "bFaceSDF_UV1", True, CHAR, -1720, 2200, "True = UV channel 1")
        created.append("bFaceSDF_UV1")
    if "SkinSSS_Strength" not in known:
        add_scalar(m, "SkinSSS_Strength", 0.0, CHAR, -1720, 2290, 0.0, 1.0)
        created.append("SkinSSS_Strength")
    if "SkinSSS_Color" not in known:
        add_vector(m, "SkinSSS_Color", (1.0, 0.35, 0.25, 1.0), CHAR, -1720, 2380)
        created.append("SkinSSS_Color")
    if "SkinSSS_Radius" not in known:
        add_scalar(m, "SkinSSS_Radius", 0.3, CHAR, -1720, 2470, 0.0, 1.0)
        created.append("SkinSSS_Radius")
    code_sss = """float wrap = 1.0 + SkinSSSRadius;
float sss = saturate((NdotL + SkinSSSRadius) / (wrap * wrap));
return lerp(NdotL, sss, SkinSSSStrength);"""
    if "SkinSSS" not in hlsl:
        add_custom(m, "SkinSSS", code_sss,
                   [("NdotL", "float"), ("SkinSSSStrength", "float"), ("SkinSSSRadius", "float")],
                   unreal.CustomMaterialOutputType.CMOT_FLOAT1, -1720, 2560)
        created.append("SkinSSS")
        unreal.log("[FixAll] Created SkinSSS")

    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    unreal.log(f"[FixAll] DONE — created/missing: {', '.join(created) if created else 'nothing'}")


if __name__ == "__main__":
    main()