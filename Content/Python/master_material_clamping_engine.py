"""Master Material Clamping & Graph Organization Engine.

Single Source of Truth for numerical parameter clamping, UI grouping, and sort priorities
across the four primary Melodia Master Materials:
  1. M_Master_Toon_Universal (33 columns, 255 scalars, 365 total params)
  2. M_Master_Toon_Landscape_HeightBlend (24 columns, 76 scalars, 121 total params)
  3. M_Master_Nikki (18 columns, 70 scalars, 109 total params)
  4. M_Master_Nikki_Landscape (18 columns, 74 scalars, 116 total params)

Fixes the unbounded float "5-billion-slider disease" by enforcing physical and artistic
bounds (slider_min, slider_max), expression groups, and top-to-bottom sort priority.
"""
from __future__ import annotations

import fnmatch
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import master_column_scheme as scheme

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = PROJECT_ROOT / "Saved" / "Audit"
OUT_CATALOG = AUDIT_DIR / "master_material_clamps_catalog.json"

# =============================================================================
# EXPLICIT PARAMETER CLAMP SPECIFICATIONS
# (Exact parameter name -> (slider_min, slider_max, description / unit))
# =============================================================================
EXPLICIT_CLAMPS: Dict[str, Tuple[float, float, str]] = {
    # Base Physical PBR
    "Roughness": (0.0, 1.0, "Physical roughness [0=smooth mirror, 1=fully diffuse]"),
    "RoughnessMin": (0.0, 1.0, "Physical minimum roughness floor"),
    "RoughnessMax": (0.0, 1.0, "Physical maximum roughness ceiling"),
    "RoughnessScale": (0.0, 2.0, "Multiplier on sampled roughness"),
    "RoughnessBias": (-1.0, 1.0, "Additive offset on sampled roughness"),
    "RockRoughness": (0.0, 1.0, "Landscape rock layer roughness"),
    "GrassRoughness": (0.0, 1.0, "Landscape grass layer roughness"),
    "MudRoughness": (0.0, 1.0, "Landscape mud layer roughness"),
    "WetRoughness": (0.0, 1.0, "Wet surface specular roughness"),
    "GoldRoughness": (0.0, 1.0, "Metallic gilding roughness"),
    "DFContactRoughness": (0.0, 1.0, "Distance field contact zone roughness"),
    "GemstoneRoughness": (0.0, 1.0, "Gemstone facet surface roughness"),
    "ImpastoRoughness": (0.0, 1.0, "Impasto paint stroke roughness"),
    "Stack2_Roughness": (0.0, 1.0, "Secondary layer roughness"),
    "Stack3_Roughness": (0.0, 1.0, "Tertiary layer roughness"),
    "Ground_Roughness": (0.0, 1.0, "Landscape ground layer roughness"),
    "Rock_Roughness": (0.0, 1.0, "Landscape rock layer roughness"),
    "Grass_Roughness": (0.0, 1.0, "Landscape grass layer roughness"),

    "Metallic": (0.0, 1.0, "Conductor/dielectric ratio [0=dielectric, 1=metal]"),
    "MetallicScale": (0.0, 1.0, "Multiplier on sampled metallic"),
    "MetallicBias": (-1.0, 1.0, "Additive offset on sampled metallic"),
    "Stack2_Metallic": (0.0, 1.0, "Secondary layer metallic"),
    "Stack3_Metallic": (0.0, 1.0, "Tertiary layer metallic"),

    # UV & Tiling
    "UVScale": (0.01, 100.0, "Base UV tiling frequency"),
    "UVRotation": (0.0, 360.0, "Texture rotation in degrees"),
    "UVOffsetU": (-10.0, 10.0, "Horizontal UV coordinate offset"),
    "UVOffsetV": (-10.0, 10.0, "Vertical UV coordinate offset"),
    "LandscapeUVScale": (0.01, 100.0, "Landscape global UV scaling factor"),
    "Rock_UVScale": (0.01, 100.0, "Rock layer UV tiling factor"),
    "Ground_UVScale": (0.01, 100.0, "Ground layer UV tiling factor"),
    "Grass_UVScale": (0.01, 100.0, "Grass layer UV tiling factor"),
    "DetailTiling": (0.1, 64.0, "Micro-detail normal map tiling frequency"),
    "TriplanarTiling": (0.01, 50.0, "Triplanar projection UV tiling frequency"),
    "TriplanarWorldScale": (10.0, 10000.0, "World-space triplanar projection scale in cm"),
    "TriplanarSlopeStart": (0.0, 90.0, "Triplanar slope angle transition start in degrees"),
    "TriplanarSlopeEnd": (0.0, 90.0, "Triplanar slope angle transition end in degrees"),
    "TriplanarSharpness": (0.1, 32.0, "Triplanar blend sharpness between projection axes"),
    "TriplanarPro_Scale": (0.01, 50.0, "Triplanar Pro procedural projection scale"),
    "TriplanarPro_Sharpness": (0.1, 32.0, "Triplanar Pro axis blend sharpness"),
    "TriplanarPro_BlendStrength": (0.0, 2.0, "Triplanar Pro blend weight multiplier"),
    "TriplanarPro_BreakupStrength": (0.0, 2.0, "Noise breakup intensity on projection seams"),
    "TriplanarPro_BreakupScale": (0.1, 64.0, "Noise breakup spatial frequency"),
    "TriplanarPro_BreakupContrast": (0.1, 8.0, "Noise breakup contrast curve"),
    "TriplanarPro_ProjectionRotation": (0.0, 360.0, "Projection coordinate rotation in degrees"),

    # Normals, Parallax & Depth
    "NormalStrength": (0.0, 4.0, "Master normal map perturbation multiplier"),
    "NormalPower": (0.1, 8.0, "Normal curvature falloff power"),
    "HeightToNormalStrength": (0.0, 4.0, "Procedural heightfield gradient normal intensity"),
    "DetailStrength": (0.0, 2.0, "Micro-detail normal map intensity"),
    "ParallaxScale": (0.0, 0.2, "Parallax occlusion mapping depth scale"),
    "ParallaxStrength": (0.0, 1.0, "POM displacement weight"),
    "ParallaxHeight": (0.0, 1.0, "POM reference height offset"),
    "LayerA_NormalStrength": (0.0, 4.0, "Layer A normal map strength"),
    "LayerB_NormalStrength": (0.0, 4.0, "Layer B normal map strength"),
    "LayerC_NormalStrength": (0.0, 4.0, "Layer C normal map strength"),
    "LayerA_ParallaxScale": (0.0, 0.2, "Layer A POM depth scale"),
    "LayerB_ParallaxScale": (0.0, 0.2, "Layer B POM depth scale"),
    "LayerC_ParallaxScale": (0.0, 0.2, "Layer C POM depth scale"),

    # Ramps & Color Grading
    "RampContrast": (0.1, 4.0, "Color ramp midpoint contrast steepness"),
    "RampPosMid": (0.05, 0.95, "Color ramp midpoint position [0=shadow, 1=highlight]"),
    "RampSharpness": (0.0, 32.0, "Quantization sharpness for stylized cel bands"),
    "RampStrength": (0.0, 1.0, "Color ramp blend weight [0=albedo, 1=graded]"),
    "ShadowRampPosMid": (0.05, 0.95, "Shadow ramp midpoint position"),
    "LayerRampStrength": (0.0, 1.0, "Landscape layer ramp color blend weight"),
    "LayerRampDriver": (0.0, 4.0, "Landscape layer ramp luminance/slope driver"),
    "PaletteRampDriver": (0.0, 4.0, "Palette ramp luminance/slope driver"),
    "PaletteRampStrength": (0.0, 1.0, "Palette ramp blend weight"),

    # Nikki Hero Lighting & Glams
    "RimPower": (0.1, 16.0, "Fresnel rim lighting exponent [higher=thinner]"),
    "RimIntensity": (0.0, 10.0, "Fresnel rim lighting brightness multiplier"),
    "RimWidth": (0.01, 2.0, "Fresnel rim falloff width"),
    "RimBias": (-1.0, 1.0, "Fresnel rim angle bias"),
    "RimClamp": (0.0, 1.0, "Rim light highlight ceiling clamp"),
    "GlowIntensity": (0.0, 20.0, "Surface emissive glow intensity multiplier"),
    "InnerGlowIntensity": (0.0, 10.0, "Sub-surface interior glow intensity"),
    "InnerGlowWidth": (0.01, 2.0, "Interior glow depth penetration width"),
    "BloomBoost": (0.0, 5.0, "Post-process bloom threshold multiplier"),
    "DreamRimPower": (0.1, 16.0, "Dream grade rim lighting exponent"),
    "DreamRimCycles": (0.5, 8.0, "Dream rim harmonic wave frequency"),
    "DreamRimStrength": (0.0, 5.0, "Dream rim brightness multiplier"),
    "DreamBloomThreshold": (0.0, 4.0, "Dream bloom luminance activation threshold"),
    "DreamBloomStrength": (0.0, 5.0, "Dream bloom intensity multiplier"),
    "NikkiHeroGradeStrength": (0.0, 1.0, "Nikki hero cinematic color grade blend weight"),
    "PastelLift": (0.0, 1.0, "Black point luminance lift for soft pastel tones"),
    "DreamSaturation": (0.0, 3.0, "Chroma saturation multiplier"),
    "DreamContrast": (0.1, 3.0, "Tonal contrast curve steepness"),
    "DreamShadowLift": (0.0, 1.0, "Shadow floor lift for ethereal dream look"),
    "DreamHighlightSoft": (0.0, 1.0, "Highlight roll-off compression softness"),
    "DreamIntensity": (0.0, 2.0, "Dream grade overall multiplier"),
    "DreamThreshold": (0.0, 2.0, "Dream activation luminance threshold"),
    "DreamFlowStrength": (0.0, 2.0, "Dynamic dream flow distortion strength"),
    "DreamFlowSpeed": (0.0, 8.0, "Dynamic dream flow animation speed"),
    "DreamFlowScale": (0.1, 64.0, "Dynamic dream flow spatial pattern scale"),
    "DreamFlowCycles": (0.5, 16.0, "Dynamic dream flow harmonic cycle count"),
    "DreamPulseAmp": (0.0, 1.0, "Dream breathing pulse amplitude"),
    "DreamPulseSpeed": (0.0, 8.0, "Dream breathing pulse frequency"),

    # Sparkle, Sheen & Iridescence
    "SparkleScale": (1.0, 1024.0, "Procedural sparkle noise grid scale"),
    "SparkleIntensity": (0.0, 10.0, "Sparkle glint emission brightness"),
    "SparkleThreshold": (0.0, 1.0, "Sparkle noise activation cutoff threshold"),
    "SparkleContrast": (0.1, 8.0, "Sparkle glint point sharpness curve"),
    "SparkleDriftSpeed": (0.0, 10.0, "Sparkle spatial drift animation velocity"),
    "SparkleTwinkleSpeed": (0.0, 10.0, "Sparkle temporal flash oscillation speed"),
    "SparkleColorLerp": (0.0, 1.0, "Sparkle dual-color interpolation factor"),
    "GlintIntensity": (0.0, 10.0, "Specular highlight micro-glint intensity"),
    "Iridescence": (0.0, 2.0, "Thin-film optical interference strength"),
    "IridescencePower": (0.1, 16.0, "Iridescence angular curvature exponent"),
    "IridescenceBias": (-1.0, 1.0, "Iridescence angular viewing offset"),
    "IridescenceRoughnessAtten": (0.0, 1.0, "Suppression of iridescence on rough surfaces"),
    "IridescenceCycles": (0.5, 16.0, "Spectral fringe wavelength repeat count"),
    "FabricSheen": (0.0, 2.0, "Micro-fiber velvet/satin anisotropic sheen strength"),
    "SheenPower": (0.1, 16.0, "Fabric sheen grazing angle exponent"),
    "SheenWidth": (0.01, 2.0, "Fabric sheen lobe angular width"),
    "SheenBias": (-1.0, 1.0, "Fabric sheen angular offset"),
    "FabricAnisoLevel": (-1.0, 1.0, "Fabric tangent/bitangent anisotropy directionality"),
    "FabricWeaveScale": (0.5, 100.0, "Physical yarn weave normal pattern scale"),
    "FabricWeaveStrength": (0.0, 2.0, "Physical yarn weave bump height"),
    "FabricType": (0.0, 7.0, "Discrete fabric model index [0=cotton, 1=silk, 2=velvet...]"),
    "ToonAnisotropy": (-1.0, 1.0, "Stylized toon anisotropic highlight stretch"),

    # Nikki Couture & Novelty Features
    "NikkiEmissiveStrength": (0.0, 20.0, "Nikki couture signature emissive boost"),
    "EmissiveFloor": (0.0, 1.0, "Minimum baseline emissive illumination"),
    "NikkiFabricSheen": (0.0, 2.0, "Nikki couture fabric velvet sheen weight"),
    "NikkiIridescence": (0.0, 2.0, "Nikki couture thin-film iridescence weight"),
    "NikkiTwinkleScale": (1.0, 512.0, "Nikki twinkle iris micro-facet scale"),
    "NikkiTwinkleAmount": (0.0, 4.0, "Nikki twinkle iris sparkle brightness"),
    "NikkiStickerBandCount": (1.0, 16.0, "Discrete cel-shade step count"),
    "NikkiStickerBandSoftness": (0.001, 1.0, "Step edge anti-aliasing softness"),
    "NikkiStickerStrength": (0.0, 2.0, "Sticker cel shading influence"),
    "NikkiStickerEdge_Bands": (1.0, 16.0, "Outer outline cel quantization bands"),
    "NikkiStickerEdge_Softness": (0.001, 1.0, "Outer outline edge transition softness"),
    "NikkiStickerEdge_Strength": (0.0, 2.0, "Outer outline visual intensity"),
    "NikkiStickerEdge_Width": (0.001, 0.5, "Outer outline screen-space stroke width"),
    "NikkiPastelStrength": (0.0, 2.0, "Pastel grade tonal blending weight"),
    "NikkiPastelLift": (-1.0, 1.0, "Pastel grade shadow baseline lift"),
    "NikkiPastelPosMid": (0.05, 0.95, "Pastel grade tonal transfer midpoint"),
    "NikkiPastelBloom": (0.0, 5.0, "Pastel atmospheric glow diffusion intensity"),
    "NikkiSDFRibbon_Scale": (0.1, 64.0, "Signed distance field ribbon spatial frequency"),
    "NikkiSDFRibbon_Sharpness": (0.1, 32.0, "SDF ribbon isoline contour sharpness"),
    "NikkiSDFRibbon_Strength": (0.0, 2.0, "SDF ribbon overlay opacity weight"),
    "NikkiSDFRibbon_EdgeFalloff": (0.01, 1.0, "SDF ribbon border falloff gradient"),
    "NikkiSDFRibbon_EdgeStrength": (0.0, 2.0, "SDF ribbon border accent brightness"),
    "NikkiPearl_Frequency": (0.1, 32.0, "Mother-of-pearl interference primary frequency"),
    "NikkiPearl_SecondFrequency": (0.1, 32.0, "Mother-of-pearl interference secondary harmonic"),
    "NikkiPearl_Strength": (0.0, 2.0, "Mother-of-pearl luster intensity multiplier"),
    "NikkiWatercolor_Bleed": (0.0, 2.0, "Watercolor edge pigment bleed radius"),
    "NikkiWatercolor_Jitter": (0.0, 1.0, "Watercolor wet paper edge stochastics"),
    "NikkiWatercolor_Strength": (0.0, 2.0, "Watercolor wash layer opacity weight"),
    "NikkiGlitterHalo_Scale": (0.1, 64.0, "Glitter halo circular halo radius"),
    "NikkiGlitterHalo_Amount": (0.0, 1.0, "Glitter halo particle density coverage"),
    "NikkiGlitterHalo_Intensity": (0.0, 10.0, "Glitter halo particle luminous intensity"),
    "NikkiGlitterHalo_HaloStrength": (0.0, 5.0, "Atmospheric halo corona brightness"),
    "NikkiGlitterHalo_HaloPower": (0.1, 16.0, "Atmospheric halo radial sharpness falloff"),
    "NikkiGlitterHalo_TwinkleSpeed": (0.0, 10.0, "Glitter halo temporal scintillation velocity"),
    "NikkiPetal_Scale": (0.1, 64.0, "Procedural falling petal noise scale"),
    "NikkiPetal_Radius": (0.01, 2.0, "Falling petal contact shadow radius"),
    "NikkiPetal_Softness": (0.01, 2.0, "Falling petal shadow penumbra softness"),
    "NikkiPetal_Strength": (0.0, 2.0, "Falling petal shadow opacity weight"),
    "NikkiPetal_BloomSpeed": (0.0, 10.0, "Falling petal animation drift velocity"),
    "SquishAmount": (-1.0, 1.0, "Kawaii squash and stretch deformation scale"),
    "NikkiSquish_Amount": (-1.0, 1.0, "Nikki squish vertex offset amplitude"),
    "NikkiSquish_Speed": (0.0, 10.0, "Nikki squish oscillation frequency"),
    "NikkiSquish_Direction": (0.0, 360.0, "Nikki squish planar axis angle in degrees"),

    # Environmental, Weather & Distance Fields
    "Wetness": (0.0, 1.0, "Surface moisture saturation fraction [0=dry, 1=flooded]"),
    "WetnessStrength": (0.0, 1.0, "Environmental wetness layer influence"),
    "WetnessRoughness": (0.0, 0.5, "Wet surface roughness target clamp"),
    "WetnessDarken": (0.0, 1.0, "Porous albedo water absorption darkening factor"),
    "WetnessNormalFlatten": (0.0, 1.0, "Water film normal dampening strength"),
    "SnowStrength": (0.0, 2.0, "Environmental snow deposition depth weight"),
    "SnowDustStrength": (0.0, 2.0, "Light snow dusting weight"),
    "SnowUpBias": (-1.0, 1.0, "Normal vertical alignment bias for snow accumulation"),
    "MossConcavityStrength": (0.0, 2.0, "Moss growth concentration in surface crevices"),
    "MossCurvatureSens": (0.0, 16.0, "Curvature sensitivity threshold for moss"),
    "ShoreWetnessBoost": (0.0, 2.0, "Water boundary contact capillary wetness"),
    "ShoreColorDarken": (0.0, 1.0, "Water boundary contact sand/rock darkening"),
    "WaterPaletteAlign": (0.0, 1.0, "Gradual shore color harmonization to ocean body"),
    "HeightBlendStrength": (0.0, 1.0, "Landscape layer heightmap competition contrast"),
    "SlopeSharpness": (0.1, 32.0, "Slope cliff/flat transition sharpness"),
    "GrassAmount": (0.0, 1.0, "Grass layer coverage bias"),
    "MudAmount": (0.0, 1.0, "Mud layer coverage bias"),
    "PathWearStrength": (0.0, 2.0, "Trod pathway surface erosion depth"),
    "MacroStrength": (0.0, 2.0, "Large-scale color variation breakup intensity"),
    "MacroScale": (1.0, 512.0, "World-space macro variation noise wavelength"),
    "AtmosphericFadeStart": (0.0, 100000.0, "Depth cueing atmospheric haze start distance (cm)"),
    "AtmosphericFadeEnd": (100.0, 500000.0, "Depth cueing atmospheric haze full cutoff (cm)"),
    "AtmosphericFadeStrength": (0.0, 1.0, "Depth cueing atmospheric haze blend weight"),
    "AtmosphericStart": (0.0, 100000.0, "Atmospheric haze start distance in cm"),
    "AtmosphericEnd": (100.0, 500000.0, "Atmospheric haze 100% saturation distance in cm"),
    "AtmosphericStrength": (0.0, 1.0, "Atmospheric haze maximum opacity"),

    # Distance Field Contact & Seams
    "DFContactBlendDistance": (0.0, 500.0, "Mesh distance field ground contact radius in cm"),
    "DFContactBlendSharpness": (0.1, 32.0, "MDF ground contact transition curve steepness"),
    "DFContactBlendStrength": (0.0, 2.0, "MDF ground contact blend weight"),
    "DFContactNoiseBreakup": (0.0, 2.0, "MDF contact line procedural noise breakup"),
    "DFContactNoiseScale": (0.01, 10.0, "MDF contact line noise spatial scale"),
    "DFContactGroundHeight": (-1000.0, 1000.0, "MDF contact reference ground plane Z offset"),
    "DFContactHeightFalloff": (0.01, 500.0, "MDF vertical elevation falloff distance"),
    "SDF_SeamBlendDistance": (0.0, 500.0, "Signed distance field intersection blend radius"),
    "SDF_SeamBlendSharpness": (0.1, 32.0, "SDF intersection transition sharpness"),
    "SDF_SeamBlendNoiseScale": (0.01, 10.0, "SDF intersection noise spatial scale"),
    "SDF_SeamBlendNoiseBreakup": (0.0, 2.0, "SDF intersection noise amplitude"),
    "SDF_SeamBlendStrength": (0.0, 2.0, "SDF intersection blend influence weight"),

    # VeinGlow (Madoka) & InkWear (Itto)
    "MadokaBlendAmount": (0.0, 1.0, "VeinGlow wallpaper and barrier overlay weight"),
    "MadokaGlowAmount": (0.0, 5.0, "VeinGlow rune line brightness multiplier"),
    "MadokaRadialBands": (1.0, 32.0, "VeinGlow concentric ripple circle count"),
    "MadokaRadialSpeed": (0.0, 10.0, "VeinGlow concentric ripple expansion speed"),
    "MadokaEmissiveBrightness": (0.0, 20.0, "VeinGlow maximum emissive output"),
    "MadokaCuteBias": (-1.0, 1.0, "VeinGlow aesthetic balance [pastel cute vs eldritch dark]"),
    "MadokaVeinEmissive": (0.0, 10.0, "VeinGlow arterial pulse brightness"),
    "WitchBarrierWallpaperScale": (0.1, 64.0, "VeinGlow wallpaper damask motif scale"),
    "WitchBarrierMazeTightness": (0.1, 32.0, "VeinGlow labyrinthine line density"),
    "WitchBarrierPhaseSpeed": (0.0, 10.0, "VeinGlow labyrinthine motion speed"),
    "MadokaAudioReactiveAmount": (0.0, 2.0, "VeinGlow music beat pulsation sensitivity"),
    "MadokaRealityWarp": (0.0, 2.0, "VeinGlow optical refractive distortion weight"),
    "IttoBlendAmount": (0.0, 1.0, "InkWear sumi-e wash and crack layer weight"),
    "IttoPatternScale": (0.1, 32.0, "InkWear woodcut/crack pattern spatial frequency"),
    "IttoCrackDepth": (0.0, 4.0, "InkWear physical gouge normal depth"),
    "IttoWearAmount": (0.0, 2.0, "InkWear edge distress surface abrasion"),
    "IttoBreakupAmount": (0.0, 2.0, "InkWear procedural splatter fragmentation"),
    "IttoErosionStrength": (0.0, 2.0, "InkWear surface erosion cavity depth"),
    "IttoWearDepth": (0.0, 4.0, "InkWear deep lacquer gouge parallax depth"),
    "IttoInkStrength": (0.0, 2.0, "InkWear carbon ink opacity absorption"),
    "IttoSpiralIntensity": (0.0, 2.0, "InkWear calligraphic brush spiral intensity"),

    # Shadow Dream & Garden
    "ShadowDreamStrength": (0.0, 2.0, "Shadow dream ambient tinting weight"),
    "ShadowSoftness": (0.01, 2.0, "Shadow terminator penumbra transition width"),
    "ShadowContactBoost": (0.0, 2.0, "Ambient occlusion contact rim darkening multiplier"),
    "ShadowFlowerStrength": (0.0, 2.0, "Shadow flower silhouette projection weight"),
    "ShadowFlowerScale": (0.1, 64.0, "Shadow flower macro spatial scale"),
    "ShadowFlowerScaleFine": (0.1, 64.0, "Shadow flower petal micro-detail scale"),
    "ShadowFlowerPulseStrength": (0.0, 2.0, "Shadow flower breathing bloom oscillation"),

    # Celestial & Nebula
    "CelestialStarIntensity": (0.0, 20.0, "Celestial star point emission brightness"),
    "CelestialNebulaStrength": (0.0, 5.0, "Celestial deep-field gas nebula brightness"),
    "CelestialNebulaScale": (0.1, 64.0, "Celestial nebula cloud cluster scale"),
    "CelestialGalaxyStrength": (0.0, 5.0, "Celestial spiral galaxy arm brightness"),
    "CelestialGalaxyScale": (0.1, 64.0, "Celestial spiral galaxy arm spatial scale"),
    "CelestialToonSteps": (1.0, 32.0, "Celestial nebula cel posterization steps"),
    "ConstellationStrength": (0.0, 5.0, "Constellation astrolabe chart line brightness"),
    "ConstellationScale": (0.1, 64.0, "Constellation astrolabe chart grid scale"),

    # Fairy Dust & Henshin
    "FairyDustIntensity": (0.0, 10.0, "Fairy dust glowing glyph brightness"),
    "FairyDustScale": (0.1, 64.0, "Fairy dust rune pattern tiling frequency"),
    "FairyHighlightThreshold": (0.0, 1.0, "Fairy dust specular gleam threshold"),
    "MagicalTransform": (0.0, 1.0, "Henshin magical girl transform phase transition"),
    "MotifScale": (0.1, 64.0, "Henshin ornamental crest motif scale"),
    "TransformGlow": (0.0, 10.0, "Henshin wavefront energy release glow brightness"),
    "WipeSoftness": (0.001, 1.0, "Henshin transformation wipe edge softness"),

    # Gemstone & Dispersion
    "IOR": (1.0, 3.5, "Index of refraction [1.0=air, 1.33=water, 1.5=glass, 2.42=diamond]"),
    "Dispersion": (0.0, 0.2, "Abbe optical chromatic dispersion prism spread"),
    "ChromaticStrength": (0.0, 5.0, "Chromatic aberration dispersion intensity"),

    # Flipbook & SubUV Particle Parameters
    "GridCols": (1.0, 16.0, "Horizontal SubUV tile division"),
    "GridRows": (1.0, 16.0, "Vertical SubUV tile division"),
    "SubUV_Index": (0.0, 255.0, "Discrete SubUV tile frame index"),
    "AnimationSpeed": (0.0, 10.0, "SubUV playback rate multiplier"),
    "LoopCount": (0.0, 100.0, "SubUV cycle repetition ceiling"),
    "FlipbookRate": (0.0, 10.0, "Flipbook timeline scrub velocity"),

    # PostProcessVolume (PPV) Parameters
    "OutlineThickness": (0.1, 10.0, "Screen-space outline pixel width"),
    "OutlineDepthThreshold": (0.01, 10.0, "Depth discontinuity sensitivity"),
    "OutlineNormalThreshold": (0.01, 1.0, "Surface normal discontinuity sensitivity"),
    "OutlineOpacity": (0.0, 1.0, "Post-process outline composite blend weight"),
    "VinesDensity": (0.0, 10.0, "Perimeter vine coverage density"),
    "VinesDistortion": (0.0, 5.0, "Vignette border UV distortion"),
    "DesatRadius": (0.01, 2.0, "Edge desaturation radial boundary"),
    "DesatAmount": (0.0, 1.0, "Peripheral color desaturation ratio"),

    # Water & Oceanology Parameters
    "WaterExtinctionDistance": (10.0, 50000.0, "SingleLayerWater absorption extinction distance (cm)"),
    "WaterBioluminescenceWeight": (0.0, 10.0, "Water bioluminescence emissive intensity"),
    "GerstnerWaveSpeed": (0.0, 10.0, "Gerstner wave propagation speed"),
    "GerstnerWaveAmplitude": (0.0, 500.0, "Gerstner wave crest height displacement (cm)"),
    "CausticsSpeed": (0.0, 10.0, "Water caustics animation velocity"),
    "CausticsScale": (0.01, 50.0, "Water caustics projection frequency"),

    # SDF & Procedural Geometry
    "SDF_Steps": (1.0, 128.0, "Raymarch iteration sample step budget"),
    "SDF_Thickness": (0.001, 10.0, "SDF isoline shell thickness"),
    "SDF_BandingFrequency": (0.1, 100.0, "Concentric SDF wave frequency"),
    "SDF_SoftEdge": (0.001, 5.0, "SDF penumbra border blur radius"),

    # Cinematic & Distance Fade
    "ContactRimStrength": (0.0, 5.0, "Cinematic contact rim brightness"),
    "ContactRimPower": (0.1, 16.0, "Cinematic contact rim grazing angle power"),
    "DistanceFadeStart": (0.0, 100000.0, "Cinematic camera distance fade start (cm)"),
    "DistanceFadeEnd": (100.0, 500000.0, "Cinematic camera distance fade cutoff (cm)"),
    "DistanceFadeStrength": (0.0, 1.0, "Cinematic distance fade maximum influence"),
    "DitherDissolveStrength": (0.0, 1.0, "Temporal screen-door dither dissolve opacity"),
    "DitherEdgeGlow": (0.0, 5.0, "Dissolve boundary photon edge glow brightness"),
    "GlobalEmissiveBoost": (0.0, 10.0, "Global material-wide emissive scalar boost"),
    "GlobalSparkleIntensity": (0.0, 5.0, "Global sparkle brightness multiplier"),
}

# General Fallback Clamp Patterns
PATTERN_CLAMP_RULES: List[Tuple[str, float, float, str]] = [
    ("*Roughness", 0.0, 1.0, "Roughness clamped [0, 1]"),
    ("*Metallic", 0.0, 1.0, "Metallic clamped [0, 1]"),
    ("*BlendAmount", 0.0, 1.0, "Normalized blend amount [0, 1]"),
    ("*BlendMode", 0.0, 8.0, "Discrete blend mode enum index"),
    ("*Strength", 0.0, 2.0, "Standard strength factor [0, 2]"),
    ("*Amount", 0.0, 2.0, "Standard amount factor [0, 2]"),
    ("*Intensity", 0.0, 10.0, "Standard luminous intensity [0, 10]"),
    ("*Power", 0.1, 16.0, "Exponential power curve [0.1, 16]"),
    ("*Bias", -2.0, 2.0, "Symmetric bias offset [-2, 2]"),
    ("*Width", 0.01, 4.0, "Spatial/angular band width [0.01, 4]"),
    ("*Softness", 0.001, 2.0, "Transition softness [0.001, 2]"),
    ("*Sharpness", 0.1, 32.0, "Transition sharpness [0.1, 32]"),
    ("*Threshold", 0.0, 2.0, "Activation cutoff threshold [0, 2]"),
    ("*Radius", 0.01, 4.0, "Influence radius [0.01, 4]"),
    ("*Lift", -1.0, 1.0, "Curve black floor lift [-1, 1]"),
    ("*Contrast", 0.1, 4.0, "Contrast curve steepness [0.1, 4]"),
    ("*Sens", 0.0, 16.0, "Input sensitivity slope [0, 16]"),
    ("*Clamp", 0.0, 8.0, "Output ceiling clamp [0, 8]"),
    ("*UVScale", 0.01, 100.0, "UV coordinate tiling scale [0.01, 100]"),
    ("*Scale", 0.01, 64.0, "Spatial noise/procedural scale [0.01, 64]"),
    ("*Speed", 0.0, 10.0, "Animation cycle velocity [0, 10]"),
    ("*Steps", 1.0, 32.0, "Cel quantization steps [1, 32]"),
    ("*Tiling", 0.01, 64.0, "Texture tiling repeat count [0.01, 64]"),
    ("*Weight", -1.0, 2.0, "Linear blending weight [-1, 2]"),
    ("*Depth", 0.0, 4.0, "Relief indentation depth [0, 4]"),
    ("*Cycles", 0.5, 32.0, "Harmonic repeat cycles [0.5, 32]"),
    ("*FadeStart", 0.0, 100000.0, "Distance fade start in cm [0, 100000]"),
    ("*FadeEnd", 100.0, 500000.0, "Distance fade end in cm [100, 500000]"),
    ("*Fade", 0.0, 1.0, "Fade weight [0, 1]"),
    ("*Boost", 0.0, 5.0, "Gain boost multiplier [0, 5]"),
    ("*Bands", 1.0, 32.0, "Discrete band count [1, 32]"),
    ("*Mix", 0.0, 1.0, "Mix blend weight [0, 1]"),
    ("*Blend", 0.0, 1.0, "Blend weight [0, 1]"),
    ("*Sharp", 0.0, 32.0, "Edge sharpness [0, 32]"),
    ("*Cycles", 0.5, 32.0, "Frequency cycle count [0.5, 32]"),
    ("*Sides", 2.0, 16.0, "Geometric polygon sides [2, 16]"),
    ("*Rings", 1.0, 16.0, "Concentric ring count [1, 16]"),
    ("*Coverage", 0.0, 1.0, "Surface area coverage fraction [0, 1]"),
]


@dataclass
class ParameterClampDef:
    name: str
    slider_min: float
    slider_max: float
    description: str
    rule_source: str
    group: str
    sort_priority: int


def resolve_clamp(param_name: str, group_label: str = "Misc", sort_priority: int = 0) -> ParameterClampDef:
    """Resolve exact clamp specification for a given parameter name."""
    if param_name in EXPLICIT_CLAMPS:
        lo, hi, desc = EXPLICIT_CLAMPS[param_name]
        return ParameterClampDef(
            name=param_name,
            slider_min=lo,
            slider_max=hi,
            description=desc,
            rule_source="explicit",
            group=group_label,
            sort_priority=sort_priority,
        )

    for pattern, lo, hi, desc in PATTERN_CLAMP_RULES:
        if fnmatch.fnmatch(param_name, pattern):
            return ParameterClampDef(
                name=param_name,
                slider_min=lo,
                slider_max=hi,
                description=desc,
                rule_source=f"pattern:{pattern}",
                group=group_label,
                sort_priority=sort_priority,
            )

    # Universal default fallback
    return ParameterClampDef(
        name=param_name,
        slider_min=0.0,
        slider_max=1.0,
        description="Standard normalized scalar [0, 1]",
        rule_source="default_normalized_fallback",
        group=group_label,
        sort_priority=sort_priority,
    )


def build_catalog_for_master(master_stem: str, live_scalar_names: List[str]) -> Dict[str, Any]:
    """Build organized clamping catalogue with groups and priorities for a master."""
    meta = scheme.build_meta(scheme.groups_for(master_stem))
    catalog: Dict[str, Any] = {
        "master": master_stem,
        "total_scalars": len(live_scalar_names),
        "parameters": {},
        "groups": {},
    }

    group_counts = {}
    for name in live_scalar_names:
        grp, prio = meta.get(name, ("99 | Miscellaneous", 9900))
        clamp = resolve_clamp(name, group_label=grp, sort_priority=prio)
        catalog["parameters"][name] = asdict(clamp)
        group_counts[grp] = group_counts.get(grp, 0) + 1

    catalog["groups"] = group_counts
    return catalog


def export_full_catalog() -> Dict[str, Any]:
    """Generate and persist the master material clamps catalog."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    master_graphs_dir = sorted(AUDIT_DIR.glob("master_graphs_*"))[-1]

    manifest = {
        "schema": "melodia.master_material_clamps_catalog.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_graphs_dir": str(master_graphs_dir.resolve()).replace("\\", "/"),
        "masters": {},
        "global_explicit_count": len(EXPLICIT_CLAMPS),
        "global_pattern_count": len(PATTERN_CLAMP_RULES),
    }

    masters = [
        "M_Master_Toon_Universal",
        "M_Master_Toon_Landscape_HeightBlend",
        "M_Master_Nikki",
        "M_Master_Nikki_Landscape",
    ]

    for m in masters:
        json_path = master_graphs_dir / f"{m}.json"
        if not json_path.exists():
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        scalars = [s["name"] for s in data["get_material_parameters"]["scalar_parameters"]]
        manifest["masters"][m] = build_catalog_for_master(m, scalars)

    OUT_CATALOG.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Exported Master Material Clamps Catalog -> {OUT_CATALOG.resolve()}")
    return manifest


def apply_clamps_to_live_unreal(master_asset_path: str, dry_run: bool = True) -> Dict[str, Any]:
    """In-editor execution via unreal.MaterialEditingLibrary to apply clamps & groups."""
    try:
        import unreal  # type: ignore
    except ImportError:
        return {"ok": False, "error": "unreal module not available (run inside Unreal Editor)"}

    mel = unreal.MaterialEditingLibrary
    eal = unreal.EditorAssetLibrary

    if not eal.does_asset_exist(master_asset_path):
        return {"ok": False, "error": f"Asset {master_asset_path} does not exist"}

    mat = eal.load_asset(master_asset_path)
    stem = master_asset_path.rsplit("/", 1)[-1].split(".", 1)[0]

    try:
        groups = scheme.groups_for(stem)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    meta = scheme.build_meta(groups)
    exprs = list(mel.get_material_expressions(mat) or [])

    clamped_count = 0
    grouped_count = 0
    errors = []

    for expr in exprs:
        try:
            pname = str(expr.get_editor_property("parameter_name") or "")
        except Exception:
            continue
        if not pname or pname == "None":
            continue

        grp, prio = meta.get(pname, ("99 | Miscellaneous", 9900))

        # Assign Expression Group & Sort Priority
        try:
            expr.set_editor_property("group", grp)
            expr.set_editor_property("sort_priority", prio)
            grouped_count += 1
        except Exception as exc:
            errors.append(f"Group error on {pname}: {exc}")

        # If Scalar, assign slider_min and slider_max
        if isinstance(expr, unreal.MaterialExpressionScalarParameter):
            clamp_def = resolve_clamp(pname, group_label=grp, sort_priority=prio)
            try:
                expr.set_editor_property("slider_min", clamp_def.slider_min)
                expr.set_editor_property("slider_max", clamp_def.slider_max)
                clamped_count += 1
            except Exception as exc:
                errors.append(f"Clamp error on {pname}: {exc}")

    result = {
        "ok": len(errors) == 0,
        "master": master_asset_path,
        "dry_run": dry_run,
        "clamped_count": clamped_count,
        "grouped_count": grouped_count,
        "errors": errors,
    }

    if not dry_run and result["ok"]:
        mel.recompile_material(mat)
        saved = eal.save_loaded_asset(mat, only_if_is_dirty=True)
        result["saved"] = bool(saved)

    return result


if __name__ == "__main__":
    export_full_catalog()
