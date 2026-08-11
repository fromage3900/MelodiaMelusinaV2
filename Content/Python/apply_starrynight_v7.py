"""Starry Night V7 — DISCRETE brush strokes.

Run in the editor after the rebuild:
    import apply_starrynight_v7 as v7; v7.apply()

Why this exists
---------------
V3-V6 built a *continuous* height field and elongated it along the flow. That reads as flowing
texture, never as brushwork, because Van Gogh's marks are SEPARATE DABS: each one has a definite
start and end, canvas visible in the gaps, a tapered tail, and its own colour. Owner confirmed
directly that V6 still does not read as the painting.

V7 replaces the field with an actual stroke lattice:
  * stroke space is quantised into rows across the flow and cells along it
  * each row is offset by a hash so dabs never line up into a grid
  * each cell hashes to its own length, thickness and hue
  * strokes are shorter than their cell, which is what creates the GAPS
  * the brush texture now supplies bristle detail INSIDE a stroke instead of being the stroke field

Pins are updated BEFORE the code (the reverse order produces alarming transient
'undeclared identifier' compile failures), and the FULL pin set is rewired afterwards because
setting `inputs` wipes every existing connection.
"""
from __future__ import annotations

MAT = "/Game/EnvSandbox/Materials/PostProcess/Candidates/M_PP_StarryNightOverlay_Candidate"
PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
UDS = "/Game/UltraDynamicSky/Materials/Weather/UltraDynamicWeather_Parameters"

PINS = [
    "SceneColor", "NightAmount", "ManualNightAmount", "SkyDepthThreshold",
    "StarMap", "StarMapTiling", "StarMapOffset", "StarTint", "StarIntensity",
    "NebulaMap", "NebulaTiling", "NebulaTint", "NebulaIntensity",
    "BrushMap", "BrushTiling", "SwirlMap", "SwirlWarp", "SwirlSpeed",
    "ImpastoRelief", "ImpastoStrength", "PaintGloss", "PaintSpecular", "PaintLightDir",
    "SkyPaintAmount", "SkyPaintTint",
    "UDSTimeOfDay", "UDSCloudCoverage", "UDSFog", "UDSGlobalOcclusion",
    "UDSWindIntensity", "UDSWindAngle", "UDSSunVector", "UDSMoonVector",
    "UseUDSTimeOfDay", "UseUDSLighting", "UseUDSWind",
    "CloudRecede", "FogRecede", "OcclusionRecede", "StarSkyRejection",
    "VortexA", "VortexB", "StrokeElongation", "StrokeTravel",
    "HaloStrength", "HaloMip", "HaloRings", "HaloPower",
    "ValueStructure", "ValueLow", "ValueHigh", "DeepColor", "LightColor",
    "PaletteFollow", "PalDeep", "PalLight", "PalStar", "PalNebula",
    # V7
    "StrokeDensity", "StrokeGap", "StrokeThickness", "BristleAmount", "StrokeHueVar",
]

NEW_SCALARS = [
    ("StrokeDensity", 26.0),    # dabs per unit of stroke space
    ("StrokeGap", 0.35),        # 0 = strokes touch, 1 = mostly canvas
    ("StrokeThickness", 0.38),
    ("BristleAmount", 0.55),    # how much brush texture shows inside a stroke
    ("StrokeHueVar", 0.45),     # per-stroke hue scatter across the palette
]

SCALAR_PINS = [
    "ManualNightAmount", "SkyDepthThreshold", "StarMapTiling", "StarIntensity",
    "NebulaTiling", "NebulaIntensity", "BrushTiling", "SwirlWarp", "SwirlSpeed",
    "ImpastoRelief", "ImpastoStrength", "PaintGloss", "PaintSpecular", "SkyPaintAmount",
    "UseUDSTimeOfDay", "UseUDSLighting", "UseUDSWind", "CloudRecede", "FogRecede",
    "OcclusionRecede", "StarSkyRejection", "StrokeElongation", "StrokeTravel",
    "HaloStrength", "HaloMip", "HaloRings", "HaloPower", "ValueStructure",
    "ValueLow", "ValueHigh", "PaletteFollow", "NightAmount",
] + [n for n, _ in NEW_SCALARS]

VECTOR_PINS = ["StarTint", "NebulaTint", "SkyPaintTint", "PaintLightDir", "StarMapOffset",
               "VortexA", "VortexB", "DeepColor", "LightColor"]
TEXTURE_PINS = ["StarMap", "NebulaMap", "BrushMap", "SwirlMap"]
UDS_PINS = [("UDSTimeOfDay", "Time of Day"), ("UDSCloudCoverage", "Cloud Coverage"),
            ("UDSFog", "Fog"), ("UDSGlobalOcclusion", "Global Occlusion"),
            ("UDSWindIntensity", "Wind Intensity"), ("UDSWindAngle", "Wind Angle"),
            ("UDSSunVector", "Sun Vector"), ("UDSMoonVector", "Moon Vector")]
PAL_PINS = [("PalDeep", "R1999_Navy"), ("PalLight", "R1999_Gold"),
            ("PalStar", "Melusina_SoftWhite"), ("PalNebula", "Melusina_Lavender")]

STROKE_BLOCK = r'''
// ---- V7 DISCRETE STROKES -------------------------------------------------------------
// Quantise the flow-aligned space into rows (across the current) and cells (along it).
// Each cell is one brush dab. Because a dab is SHORTER than its cell, canvas shows between
// them - that gap is what separates brushwork from flowing texture.
float2 sUV = float2(dot(wuv, tangent), dot(wuv, across)) * max(StrokeDensity, 1.0);
float row = floor(sUV.y);
float rowJit = frac(sin(row * 78.233) * 43758.5453);
// row offset breaks the lattice so dabs never line up into a visible grid
float alongPos = sUV.x + rowJit * 3.7 + t * StrokeTravel;
float cellId = floor(alongPos);
float withinCell = frac(alongPos);
float acrossPos = frac(sUV.y) - 0.5;

float sh1 = frac(sin(cellId * 12.9898 + row * 78.233) * 43758.5453);
float sh2 = frac(sin(cellId * 39.346 + row * 11.135) * 24634.6345);

// per-dab length and thickness; StrokeGap pulls the length back to open the canvas up
float strokeLen = lerp(0.95, 0.40, saturate(StrokeGap)) * lerp(0.75, 1.0, sh1);
float thick = max(StrokeThickness, 0.02) * lerp(0.7, 1.15, sh2);

// tapered ends - a loaded brush starts blunt and lifts off thin
float endTaper = smoothstep(0.0, 0.14, withinCell) *
                 smoothstep(strokeLen, strokeLen - 0.22, withinCell);
float acrossFall = 1.0 - smoothstep(thick * 0.55, thick, abs(acrossPos));
float strokeMask = saturate(endTaper * acrossFall);

// The brush texture is now detail WITHIN a dab (bristle grain), not the dab field itself.
float bristle = Texture2DSample(BrushMap, BrushMapSampler,
    float2(withinCell * 2.0, acrossPos * 3.0 + sh1) * max(BrushTiling, 0.01) * 0.12).r;
float height = strokeMask * lerp(1.0, bristle, saturate(BristleAmount));

// per-dab hue: neighbouring strokes must differ, or the whole area reads as one wash
float strokeHue = (sh2 - 0.5) * saturate(StrokeHueVar);
// ---------------------------------------------------------------------------------------
'''


def apply() -> str:
    import unreal
    MEL = unreal.MaterialEditingLibrary
    m = unreal.load_asset(MAT)
    if not m:
        raise RuntimeError(f"missing {MAT}")
    custom = [e for e in MEL.get_material_expressions(m)
              if type(e).__name__ == "MaterialExpressionCustom"][0]

    code = custom.get_editor_property("code")
    code = code.replace("MELODIA_STARRY_VANGOGH_V6_PALETTE", "MELODIA_STARRY_VANGOGH_V7_DABS")

    # Replace the continuous 3-octave height field with the discrete stroke lattice.
    start = code.find("float h1 = Texture2DSample(BrushMap")
    end = code.find("float height = h1 *")
    if start == -1 or end == -1:
        raise RuntimeError("V6 octave block not found - material is not in the expected state")
    end = code.find("\n", end) + 1
    code = code[:start] + STROKE_BLOCK + code[end:]

    # per-dab hue scatter across the authored palette
    code = code.replace(
        "float3 painted = lerp(col * deepC, col * lightC, vmix);",
        "float3 painted = lerp(col * deepC, col * lightC, saturate(vmix + strokeHue));")

    custom.set_editor_property("code", code)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)

    rb = [e for e in MEL.get_material_expressions(m)
          if type(e).__name__ == "MaterialExpressionCustom"][0].get_editor_property("code")
    ok = "MELODIA_STARRY_VANGOGH_V7_DABS" in rb and "strokeMask" in rb
    print(f"V7 applied | readback ok: {ok}")
    return "ok" if ok else "READBACK FAILED"


def add_params() -> None:
    """Create the 5 new scalars. Safe to re-run."""
    import unreal
    MEL = unreal.MaterialEditingLibrary
    m = unreal.load_asset(MAT)
    have = set()
    for e in MEL.get_material_expressions(m) or []:
        try:
            have.add(str(e.get_editor_property("parameter_name")))
        except Exception:
            pass
    y = 4200
    for name, val in NEW_SCALARS:
        if name in have:
            continue
        e = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1400, y)
        y += 55
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", val)
        e.set_editor_property("group", "VanGogh Painting")
    unreal.EditorAssetLibrary.save_asset(MAT)


def rewire() -> str:
    """Reconnect every pin. Required after any `inputs` update - it wipes all connections."""
    import unreal
    MEL = unreal.MaterialEditingLibrary
    m = unreal.load_asset(MAT)
    ex = list(MEL.get_material_expressions(m) or [])
    custom = [e for e in ex if type(e).__name__ == "MaterialExpressionCustom"][0]

    def named(cls, n):
        for e in ex:
            if type(e).__name__ == cls:
                try:
                    if str(e.get_editor_property("parameter_name")) == n:
                        return e
                except Exception:
                    pass
        return None

    scene = [e for e in ex if type(e).__name__ == "MaterialExpressionSceneTexture"][0]
    ok, fail = 0, []

    def wire(src, pin, dst):
        nonlocal ok
        if src is None or not MEL.connect_material_expressions(src, pin, custom, dst):
            fail.append(dst)
        else:
            ok += 1

    wire(scene, "Color", "SceneColor")
    for n in SCALAR_PINS:
        wire(named("MaterialExpressionScalarParameter", n), "", n)
    for n in VECTOR_PINS:
        wire(named("MaterialExpressionVectorParameter", n), "RGB", n)
    for n in TEXTURE_PINS:
        wire(named("MaterialExpressionTextureObjectParameter", n), "", n)
    for pin, src in UDS_PINS + PAL_PINS:
        wire(named("MaterialExpressionCollectionParameter", src), "", pin)

    MEL.connect_material_property(custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_asset(MAT)
    msg = f"rewired {ok}/{len(PINS)} | failed: {fail}"
    print(msg)
    return msg


def run_all() -> None:
    """add_params -> apply -> rewire. Pins must already include the 5 V7 names."""
    add_params()
    apply()
    rewire()
