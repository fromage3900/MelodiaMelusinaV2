"""CANONICAL column (UI group) scheme for the four Melodia master materials.

Single source of truth for parameter organization. Pure Python (no `unreal`
import) so it can be used repo-side (documentation, audits) and in-editor
(organize_master_groups.py / organize_landscape_groups.py / Nikki organizers).

Build rule: every live parameter of a master MUST appear in exactly one group
here. `verify_coverage()` checks that against the Saved/Audit exports and is
part of Phase 2 completion.

Group label format: "NN | Name" — order of GROUPS == column order == panel order.
Sort priority = group_index * 100 + index_within_group (same stride the old
organizers used, so instance editor reads top-to-bottom by column).

Coverage verified 2026-08-16 against live exports:
  Universal 365/365, Landscape 121/121, Nikki 109/109, Nikki_Landscape 116/116.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# M_Master_Toon_Universal — 33 columns
# ---------------------------------------------------------------------------
UNIVERSAL_GROUPS: List[Tuple[str, List[str]]] = [
    ("01 | Base Surface", [
        "BaseTint", "TextureWeight", "UVScale", "UVRotation", "UVOffsetU", "UVOffsetV",
        "Roughness", "Metallic", "RoughnessScale", "RoughnessBias",
        "MetallicScale", "MetallicBias",
        "PaletteRampLow", "PaletteRampMid", "PaletteRampHigh",
        "PaletteRampStrength", "PaletteRampDriver",
        "RampSharpness",
    ]),
    ("02 | Triplanar", [
        "bTriplanar_Active", "TriplanarWorldScale", "TriplanarSharpness",
        "TriplanarSlopeStart", "TriplanarSlopeEnd",
        "TriplanarBlend_Albedo", "TriplanarBlend_Normal", "TriplanarBlend_Roughness",
        "TriplanarDetailMap",
    ]),
    ("03 | Texture Layer A", [
        "bLayerA_Active",
        "Albedo", "NormalMap", "ORM", "HeightMap",
        "RoughnessMap", "MetallicMap", "EmissiveMap",
        "bUseSeparateRoughnessMap", "bUseSeparateMetallicMap", "bUseHeightToNormal", "bUseEmissiveMap",
        "EmissiveMapIntensity", "EmissiveMapUVScale", "EmissiveMapTint",
        "LayerA_TextureWeight", "LayerA_ParallaxScale", "LayerA_NormalStrength",
    ]),
    ("04 | Texture Layer B", [
        "bLayerB_Active",
        "LayerB_Albedo", "LayerB_NormalMap", "LayerB_ORM", "LayerB_HeightMap",
        "LayerB_RoughnessMap", "LayerB_MetallicMap",
        "LayerB_TextureWeight", "LayerB_ParallaxScale", "LayerB_NormalStrength",
        "LayerBlend", "LayerBlendMode", "LayerHeightBias", "LayerHeightSharpness",
        "LayerBlendSoftness", "LayerNormalBlend", "LayerRoughnessBlend",
        "LayerManualMix", "LayerBaseHeightScale", "LayerOverlayHeightScale",
        "LayerHeightInvert", "LayerAlphaBias", "LayerAlphaContrast",
        "LayerColorBlend", "LayerAOBlend", "LayerHeightBlend", "LayerMetallicBlend",
    ]),
    ("05 | Texture Layer C", [
        "bLayerC_Active",
        "LayerC_Albedo", "LayerC_NormalMap", "LayerC_ORM", "LayerC_HeightMap",
        "LayerC_RoughnessMap", "LayerC_MetallicMap",
        "LayerC_TextureWeight", "LayerC_ParallaxScale", "LayerC_NormalStrength",
        "LayerCBlend", "LayerCBlendMode", "LayerCHeightBias", "LayerCHeightSharpness",
        "LayerCBlendSoftness", "LayerCNormalBlend", "LayerCRoughnessBlend",
        "LayerCManualMix", "LayerCBaseHeightScale", "LayerCOverlayHeightScale",
        "LayerCHeightInvert", "LayerCAlphaBias", "LayerCAlphaContrast",
        "LayerCColorBlend", "LayerCAOBlend", "LayerCHeightBlend", "LayerCMetallicBlend",
    ]),
    ("06 | Parallax", [
        "ParallaxScale", "ParallaxStrength", "ParallaxHeight",
        "NormalStrength", "NormalPower", "HeightToNormalStrength",
    ]),
    ("07 | Macro & Detail", [
        "MacroVariationStrength", "MacroScale",
        "DetailNormal", "DetailTiling", "DetailStrength",
    ]),
    ("08 | Temporal / Ink", [
        "TemporalStrength", "WindSpeed", "NoiseScale", "SmearStrength", "BoilIntensity",
    ]),
    ("09 | Color Ramp", [
        "RampLow", "RampMid", "RampHigh", "RampPosMid", "RampContrast", "RampStrength",
        "ShadowRampLow", "ShadowRampMid", "ShadowRampHigh", "ShadowRampPosMid",
        "bShadowRamp_Active",
    ]),
    ("10 | Nikki Rim & Glow", [
        "bNikkiHero",
        "RimColor", "RimPower", "RimIntensity", "RimWidth", "RimBias", "RimClamp",
        "GlowColor", "GlowIntensity", "InnerGlowColor", "InnerGlowIntensity", "InnerGlowWidth",
        "BloomBoost",
        "DreamRimColor", "DreamRimPower", "DreamRimCycles", "DreamRimStrength",
        "bDreamRim_Active", "DreamBloomColor", "DreamBloomThreshold", "DreamBloomStrength",
    ]),
    ("11 | Nikki Dream Grade", [
        "DreamTint", "DreamWarmth", "PastelLift", "DreamSaturation", "DreamContrast",
        "DreamShadowLift", "DreamHighlightSoft", "NikkiHeroGradeStrength",
        "DreamIntensity", "DreamComposition", "DreamThreshold", "DreamCompositeBlend",
        "DreamFlowStrength", "DreamFlowSpeed", "DreamFlowScale", "DreamFlowCycles",
        "DreamPulseAmp", "DreamPulseSpeed",
    ]),
    ("12 | Nikki Sparkle", [
        "bSparkleAdvanced", "SparkleMask", "SparkleScale", "SparkleIntensity",
        "SparkleThreshold", "SparkleContrast", "SparkleDriftSpeed", "SparkleTwinkleSpeed",
        "SparkleColor", "SparkleColorLow", "SparkleColorHigh", "SparkleColorLerp",
        "GlintIntensity",
    ]),
    ("13 | Nikki Iridescence & Sheen", [
        "bSheenUsesNormal",
        "Iridescence", "IridescenceTint", "IridescencePower", "IridescenceBias",
        "IridescenceRoughnessAtten", "IridescenceCycles",
        "FabricSheen", "SheenTint", "SheenPower", "SheenWidth", "SheenBias",
        "FabricType", "FabricAnisoLevel", "FabricWeaveScale", "FabricWeaveStrength",
        "FabricNormalBlend", "ToonAnisotropy",
    ]),
    ("14 | Gilding", [
        "GildingStrength", "GoldTint", "GoldRoughness", "GoldEmissive", "CurvatureSensitivity",
    ]),
    ("15 | Shadow Garden (Flowers)", [
        "ShadowFlowerStrength", "ShadowFlowerScale", "ShadowFlowerColor",
    ]),
    ("16 | Shadow Dream", [
        "ShadowDreamTint", "ShadowDreamStrength", "ShadowSoftness",
    ]),
    ("17 | Celestial (Nebula)", [
        "bCelestial_Active", "bCelestialUsesDreamPalette",
        "ConstellationRampLow", "ConstellationRampMid", "ConstellationRampHigh",
        "ConstellationStrength", "ConstellationScale",
        "CelestialStarIntensity", "CelestialNebulaStrength", "CelestialNebulaScale",
        "CelestialGalaxyStrength", "CelestialGalaxyScale", "CelestialToonSteps",
        "StarMap",
    ]),
    ("18 | Fairy Dust", [
        "bFairyDust_Active", "FairyGlyphMask", "FairyMotifStyle", "FairyDustIntensity",
        "FairyDustScale", "FairyDustColor", "FairyHighlightThreshold",
    ]),
    ("19 | Magical (Henshin)", [
        "MagicalTransform", "MotifMask", "MotifScale", "MotifColor",
        "TransformGlow", "WipeSoftness", "MagicalPalette",
    ]),
    ("20 | VeinGlow (Madoka)", [
        "MadokaBlendAmount", "WitchBarrierWallpaperScale", "MadokaGlowAmount",
        "MadokaVeinEmissive", "MadokaCuteBias", "MadokaEmissiveBrightness",
        "MadokaRadialBands", "MadokaAudioReactiveAmount", "MadokaRealityWarp",
        "MadokaRampLow", "MadokaRampMid", "MadokaRampHigh",
    ]),
    ("21 | InkWear (Itto)", [
        "IttoBlendAmount", "IttoPatternScale", "IttoCrackDepth", "IttoWearAmount",
        "IttoBreakupAmount", "IttoInkStrength", "IttoSpiralIntensity",
        "IttoRampLow", "IttoRampHigh",
    ]),
    ("22 | Impasto", [
        "bImpasto_Active", "ImpastoStrength", "ImpastoHeight", "StrokeMask",
        "ImpastoCoverage", "ImpastoRoughness",
    ]),
    ("23 | Sigil", [
        "SigilStrength", "SigilSides", "SigilRings", "SigilSpeed", "SigilSharp", "SigilCycles",
    ]),
    ("24 | Dawn & Mist", [
        "DawnStrength", "DawnHeightScale", "DawnBias", "DawnLowColor", "DawnHighColor",
        "MistStrength", "MistScale", "MistSpeed", "MistSharp", "MistColor",
    ]),
    ("25 | Glint & Halo", [
        "GlintStrength", "GlintScale", "GlintSize", "GlintSharp", "GlintSpeed", "GlintColor",
        "HaloStrength", "HaloPower", "HaloColor",
    ]),
    ("26 | Character & SDF", [
        "SkinSSS_Strength", "SkinSSS_Radius", "SkinSSS_Color",
        "FaceSDF_Strength", "FaceSDF_Tiling", "FaceSDF_Texture", "bFaceSDF_UV1",
    ]),
    ("27 | Elemental", [
        "bElemental_Active", "ElementType", "ElementStrength", "ElementEmissiveBoost",
    ]),
    ("28 | World / Weather", [
        "bWeather_Active",
        "WetnessStrength", "WetnessRoughness", "WetnessDarken", "WetnessNormalFlatten",
        "SnowDustStrength", "SnowDustColor", "SnowUpBias",
        "MossConcavityStrength", "MossColor", "MossCurvatureSens",
    ]),
    ("29 | Time of Day", [
        "UseUDSTimeOfDay", "TimeOfDayWarmth", "TimeOfDayMPCStrength",
    ]),
    ("30 | Cinematic", [
        "ContactRimStrength", "ContactRimPower", "ContactRimColor",
        "DistanceFadeStrength", "DistanceFadeStart", "DistanceFadeEnd",
        "AtmosphericFadeColor", "DitherDissolveStrength", "DitherEdgeGlow",
    ]),
    ("31 | DF Contact Blend", [
        "bDFContactBlend_Active",
        "DFContactBlendDistance", "DFContactBlendSharpness", "DFContactBlendStrength",
        "DFContactNoiseBreakup", "DFContactNoiseScale", "DFContactWorldPositionOffset",
        "DFContactGroundHeight", "DFContactHeightFalloff", "DFContactRoughness",
        "DFContactTint",
        "SDF_SeamBlendDistance", "SDF_SeamBlendSharpness", "SDF_SeamBlendNoiseScale",
        "SDF_SeamBlendNoiseBreakup", "SDF_SeamBlendStrength",
    ]),
    ("32 | Gemstone & Stack", [
        "bGemstone_Active", "GemstoneTint", "GemstoneRoughness", "IOR", "Dispersion",
        "ChromaticStrength",
        "Stack2_Tiling", "Stack2_Blend", "Stack2_Metallic", "Stack2_Roughness",
        "Stack2_Albedo", "Stack2_Normal", "Stack2_ORM",
        "Stack3_Tiling", "Stack3_Metallic", "Stack3_Roughness",
        "Stack3_Albedo", "Stack3_Normal",
        "bStackLayer3_Active",
    ]),
    ("33 | Mesh Blend", [
        "bMeshBlendActivator_Active", "AutoBlendID", "StaticAutoBlendID",
    ]),
    ("98 | Global", [
        "GlobalEmissiveBoost", "GlobalSparkleIntensity",
        "Melusina_Lavender", "Melusina_RoseGold", "Melusina_SoftWhite",
    ]),
    ("99 | Legacy / Diagnostic", [
        "Use Static Value", "DIAG_TestBool", "Param", "Param_1",
        "bGemstone_Active_LEGACY", "bStackLayer2_Active_LEGACY",
    ]),
]

# ---------------------------------------------------------------------------
# M_Master_Toon_Landscape_HeightBlend — 24 columns (live vocabulary 2026-08-16)
# ---------------------------------------------------------------------------
LANDSCAPE_GROUPS: List[Tuple[str, List[str]]] = [
    ("01 | Palette", ["RockTint", "GrassTint", "MudTint", "PathTint", "SnowTint", "WaterAlignTint"]),
    ("02 | Blend", [
        "HeightBlendStrength", "GrassAmount", "MudAmount", "SlopeSharpness",
        "bUsePaintedLayers", "bUseLandscapeUV", "LandscapeUVScale",
    ]),
    ("03 | Triplanar", [
        "TriplanarTiling",
        "bTriplanarPro_Active",
        "TriplanarPro_Scale", "TriplanarPro_Sharpness", "TriplanarPro_BlendStrength",
        "TriplanarPro_BreakupStrength", "TriplanarPro_BreakupScale",
        "TriplanarPro_BreakupContrast",
        "TriplanarPro_ProjectionOffset", "TriplanarPro_ProjectionRotation",
        "TriplanarPro_AxisWeights",
    ]),
    ("04 | Layer PBR", [
        "Rock_Albedo", "Rock_Normal", "Rock_Height",
        "Grass_Albedo", "Grass_Normal", "Grass_Height",
        "Mud_Albedo", "Mud_Normal", "Mud_Height",
        "Path_Albedo", "Path_Normal", "Path_Height",
    ]),
    ("05 | Surface", [
        "Roughness", "RockRoughness", "GrassRoughness", "MudRoughness",
        "NormalStrength", "NormalMapBlendAmount", "Wetness", "WetRoughness",
    ]),
    ("06 | Macro", ["MacroStrength", "MacroScale"]),
    ("07 | Snow", ["SnowStrength", "SnowUpBias"]),
    ("08 | Path", ["PathMask", "PathWearStrength"]),
    ("09 | Shore", ["ShoreWetnessBoost", "ShoreColorDarken", "WaterPaletteAlign"]),
    ("10 | Nikki Rim & Glow", [
        "bNikkiFast", "bNikkiHero", "RimColor", "RimWidth", "RimIntensity",
        "GlowIntensity", "BloomBoost",
    ]),
    ("11 | Nikki Sparkle", [
        "SparkleMask", "SparkleScale", "SparkleIntensity", "SparkleThreshold",
        "SparkleTwinkleSpeed", "SparkleColor",
    ]),
    ("12 | Nikki Iridescence & Sheen", [
        "PastelLift", "DreamTint", "DreamSaturation", "DreamContrast", "DreamShadowLift",
        "Iridescence", "IridescencePower", "IridescenceTint", "FabricSheen", "SheenTint",
    ]),
    ("13 | Layer Ramp", [
        "LayerRampLow", "LayerRampMid", "LayerRampHigh", "LayerRampStrength", "LayerRampDriver",
    ]),
    ("14 | VeinGlow (Madoka)", [
        "MadokaBlendAmount", "MadokaGlowAmount", "MadokaRadialBands", "MadokaRadialSpeed",
        "MadokaEmissiveBrightness", "MadokaCuteBias", "MadokaVeinEmissive",
        "WitchBarrierWallpaperScale", "WitchBarrierMazeTightness", "WitchBarrierPhaseSpeed",
        "MadokaAudioReactiveAmount", "MadokaRealityWarp",
        "MadokaRampLow", "MadokaRampMid", "MadokaRampHigh",
    ]),
    ("15 | InkWear (Itto)", [
        "IttoBlendAmount", "IttoPatternScale", "IttoCrackDepth", "IttoWearAmount",
        "IttoBreakupAmount", "IttoErosionStrength", "IttoWearDepth", "IttoInkStrength",
        "IttoSpiralIntensity", "IttoRampLow", "IttoRampHigh",
    ]),
    ("16 | Shadow Dream", ["ShadowDreamTint", "ShadowDreamStrength", "ShadowContactBoost"]),
    ("17 | Shadow Garden (Flowers)", [
        "ShadowFlowerMask", "ShadowFlowerStrength", "ShadowFlowerScale",
        "ShadowFlowerScaleFine", "ShadowFlowerPulseStrength", "ShadowFlowerColor",
    ]),
    ("18 | Color Ramp", ["RampSharpness"]),
    ("19 | Atmospheric", [
        "AtmosphericFadeStart", "AtmosphericFadeEnd", "AtmosphericFadeStrength",
        "AtmosphericFadeColor",
    ]),
]

# ---------------------------------------------------------------------------
# M_Master_Nikki / M_Master_Nikki_Landscape — shared family columns (live 2026-08-16)
# ---------------------------------------------------------------------------
NIKKI_BASE_GROUPS: List[Tuple[str, List[str]]] = [
    ("01 | Base Surface", [
        "BaseTint", "RoughnessMin", "RoughnessMax", "MetallicScale",
        "RampLow", "RampMid", "RampHigh", "RampPosMid", "RampContrast", "RampStrength",
        "RampSharpness",
    ]),
    ("02 | Textures", ["Albedo", "NormalMap", "ORM", "HeightMap"]),
    ("03 | Atmosphere", [
        "AtmosphericStart", "AtmosphericEnd", "AtmosphericStrength", "AtmosphericColor",
    ]),
    ("04 | Emissive", ["NikkiEmissiveStrength", "EmissiveFloor"]),
    ("05 | Triplanar", [
        "bTriplanarPro_Active",
        "TriplanarPro_Scale", "TriplanarPro_Sharpness", "TriplanarPro_BlendStrength",
        "TriplanarPro_BreakupStrength", "TriplanarPro_BreakupScale",
        "TriplanarPro_BreakupContrast",
        "TriplanarPro_ProjectionOffset", "TriplanarPro_ProjectionRotation",
        "TriplanarPro_AxisWeights",
    ]),
    ("06 | Parallax", ["ParallaxStrength", "UVScale"]),
    ("07 | Nikki Iridescence & Sheen", [
        "bSheenUsesNormal",
        "Iridescence", "IridescencePower", "IridescenceBias", "IridescenceRoughnessAtten",
        "FabricSheen", "SheenPower", "SheenWidth", "SheenBias",
    ]),
    ("08 | Nikki Sticker Shade", [
        "bNikkiStickerShade_Active", "NikkiStickerShadeColor",
        "NikkiStickerBandCount", "NikkiStickerBandSoftness", "NikkiStickerStrength",
    ]),
    ("09 | Nikki Twinkle Iris", [
        "bNikkiTwinkleIris_Active", "NikkiIrisTint",
        "NikkiFabricSheen", "NikkiIridescence", "NikkiTwinkleScale", "NikkiTwinkleAmount",
    ]),
    ("10 | Nikki Pastel Grade", [
        "bNikkiPastelGrade_Active",
        "NikkiPastelRampLow", "NikkiPastelRampMid", "NikkiPastelRampHigh",
        "NikkiPastelStrength", "NikkiPastelLift", "NikkiPastelPosMid", "NikkiPastelBloom",
    ]),
    ("11 | Shadow Dream", [
        "bShadowDream_Active", "ShadowDreamTint", "ShadowDreamStrength", "ShadowSoftness",
    ]),
    ("12 | Kawaii Squish", [
        "bKawaiiSquish_Active", "bNikkiSquishWPO_Active",
        "SquishAmount", "NikkiSquish_Amount", "NikkiSquish_Speed", "NikkiSquish_Direction",
    ]),
    ("13 | Nikki SDF Ribbon", [
        "bNikkiSDFRibbon_Active", "NikkiSDFRibbon_Color",
        "NikkiSDFRibbon_Scale", "NikkiSDFRibbon_Sharpness", "NikkiSDFRibbon_Strength",
        "NikkiSDFRibbon_EdgeFalloff", "NikkiSDFRibbon_EdgeStrength",
    ]),
    ("14 | Nikki Pearl Sheen", [
        "bNikkiPearlSheen_Active", "NikkiPearl_Tint",
        "NikkiPearl_Frequency", "NikkiPearl_SecondFrequency", "NikkiPearl_Strength",
    ]),
    ("15 | Nikki Dream Watercolor", [
        "bNikkiDreamWatercolor_Active", "NikkiWatercolor_BleedColor",
        "NikkiWatercolor_Bleed", "NikkiWatercolor_Jitter", "NikkiWatercolor_Strength",
    ]),
    ("16 | Nikki Sticker Edge", [
        "bNikkiStickerEdge_Active", "NikkiStickerEdge_Color",
        "NikkiStickerEdge_Width", "NikkiStickerEdge_Bands",
        "NikkiStickerEdge_Softness", "NikkiStickerEdge_Strength",
    ]),
    ("17 | Nikki Glitter Halo", [
        "bNikkiGlitterHalo_Active", "NikkiGlitterHalo_Color",
        "NikkiGlitterHalo_Scale", "NikkiGlitterHalo_Amount", "NikkiGlitterHalo_Intensity",
        "NikkiGlitterHalo_HaloStrength", "NikkiGlitterHalo_HaloPower",
        "NikkiGlitterHalo_TwinkleSpeed",
    ]),
    ("18 | Nikki Petal Shadow", [
        "bNikkiPetalShadow_Active", "NikkiPetal_Tint",
        "NikkiPetal_Scale", "NikkiPetal_Radius", "NikkiPetal_Softness",
        "NikkiPetal_Strength", "NikkiPetal_BloomSpeed",
    ]),
]

# Nikki landscape variant: painted-layer vocabulary replaces base Textures/Parallax.
# Columns 03+ reuse the shared family numbering with the two landscape groups
# inserted as 02 (Layer Textures) and 03 (Layer Surface).
NIKKI_LANDSCAPE_EXTRA_GROUPS: List[Tuple[str, List[str]]] = [
    ("02 | Layer Textures", [
        "Albedo", "Rock_Albedo", "Rock_NormalMap",
        "Ground_Albedo", "Ground_NormalMap",
        "Grass_Albedo", "Grass_NormalMap",
    ]),
    ("03 | Layer Surface", [
        "Rock_UVScale", "Rock_Roughness", "Ground_UVScale", "Ground_Roughness",
        "Grass_UVScale", "Grass_Roughness",
    ]),
]


def build_meta(groups: List[Tuple[str, List[str]]]) -> Dict[str, Tuple[str, int]]:
    """param name -> (group label, sort priority) with group-stride ordering."""
    meta: Dict[str, Tuple[str, int]] = {}
    for gi, (label, names) in enumerate(groups):
        for pi, name in enumerate(names):
            meta[name] = (label, gi * 100 + pi)
    return meta


# Groups the surface Nikki master owns that the landscape variant does not.
_NIKKI_LANDSCAPE_DROPPED = ("02 | Textures", "06 | Parallax")


def groups_for(material_stem: str) -> List[Tuple[str, List[str]]]:
    if material_stem == "M_Master_Toon_Universal":
        return UNIVERSAL_GROUPS
    if material_stem == "M_Master_Toon_Landscape_HeightBlend":
        return LANDSCAPE_GROUPS
    if material_stem == "M_Master_Nikki":
        return NIKKI_BASE_GROUPS
    if material_stem == "M_Master_Nikki_Landscape":
        kept = [g for g in NIKKI_BASE_GROUPS if g[0] not in _NIKKI_LANDSCAPE_DROPPED]
        return kept + NIKKI_LANDSCAPE_EXTRA_GROUPS
    raise ValueError(f"unknown master {material_stem}")


def verify_coverage(material_stem: str, live_names: List[str]) -> Dict:
    """Check every live param name has a group; report misses and orphans."""
    meta = build_meta(groups_for(material_stem))
    unmapped = [n for n in live_names if n not in meta]
    orphaned = [n for n in meta if n not in live_names]
    return {
        "master": material_stem,
        "live_count": len(live_names),
        "mapped": len(live_names) - len(unmapped),
        "unmapped": unmapped,
        "orphaned": orphaned,
    }


if __name__ == "__main__":
    import glob
    import json
    from pathlib import Path

    audit = Path(__file__).resolve().parents[2] / "Saved" / "Audit"
    dirs = sorted(audit.glob("master_graphs_*"))
    latest = dirs[-1]
    ok = True
    for stem in (
        "M_Master_Toon_Universal",
        "M_Master_Toon_Landscape_HeightBlend",
        "M_Master_Nikki",
        "M_Master_Nikki_Landscape",
    ):
        f = latest / f"{stem}.json"
        if not f.exists():
            print(stem, "NO EXPORT")
            continue
        p = json.loads(f.read_text(encoding="utf-8"))["get_material_parameters"]
        names = (
            [s["name"] for s in (p.get("scalar_parameters") or [])]
            + [v["name"] for v in (p.get("vector_parameters") or [])]
            + [t["name"] for t in (p.get("texture_parameters") or [])]
            + [s["name"] for s in (p.get("static_switch_parameters") or [])]
        )
        r = verify_coverage(stem, names)
        if r["unmapped"]:
            ok = False
        print(f"{stem}: live={r['live_count']} mapped={r['mapped']} "
              f"{'COVERED' if not r['unmapped'] else 'UNMAPPED=' + str(r['unmapped'])}")
        if r["orphaned"]:
            print(f"   orphaned (in scheme, not live): {r['orphaned']}")
    raise SystemExit(0 if ok else 1)
