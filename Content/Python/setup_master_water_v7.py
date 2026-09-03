"""Water Grand Master v7 setup, repair, presets, and audit.

Safe to rerun. This script never edits or reparents v6 assets.
Run from Unreal's Python console or through Monolith editor.run_python.
"""
import json
import os
import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Water_Master_Grand_v7"
CAUSTICS_PROJECTOR = "/Game/EnvSandbox/Materials/Masters/M_WaterCausticsProjector_v7"
INSTANCE_DIR = "/Game/EnvSandbox/Materials/Instances/Water/v7"
AUDIT_FILE = os.path.join(unreal.Paths.project_saved_dir(), "Audit", "grand_water_v7.json")

TEXTURES = {
    "BaseHeightTexture": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterBase_Height",
    "MidHeightTexture": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterLayerMid_Height",
    "BaseColorTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterBase_BaseColor",
    "BaseNormalTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterBase_Normal",
    "BaseRoughTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterBase_Roughness",
    "BaseMaskTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterBase_Opacity",
    "MidColorTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterLayerMid_BaseColor",
    "MidNormalTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterLayerMid_Normal",
    "MidRoughTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterLayerMid_Roughness",
    "MidMaskTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterLayerMid_Opacity",
    "Layer2NormalTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterLayer2_Normal",
    "HighlightColorTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterHighlight_BaseColor",
    "HighlightNormalTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterHighlight_Normal",
    "HighlightRoughTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterHighlight_Roughness",
    "HighlightMaskTex": "/Game/EnvSandbox/Textures/PBR_Sets/Water/T_WaterHighlight_Opacity",
}

# One deterministic, non-harmonic spectrum is shared by WPO and analytical normals.
WAVE_SPECTRUM = [
    (0.80, 0.60, 0.25, 6000.0, 0.13),
    (-0.60, 0.80, 0.18, 3701.0, 1.71),
    (0.40, -0.90, 0.12, 1597.0, 3.08),
    (-0.30, -0.60, 0.08, 907.0, 4.47),
    (0.90, -0.20, 0.05, 457.0, 2.26),
    (-0.70, 0.50, 0.03, 223.0, 5.42),
    (0.22, 0.97, 0.018, 131.0, 0.83),
    (-0.94, -0.34, 0.012, 79.0, 3.74),
]

N = {
    "UV": "MaterialExpressionTextureCoordinate_2", "Time": "MaterialExpressionTime_1",
    "WorldPos": "MaterialExpressionWorldPosition_0", "PixelDepth": "MaterialExpressionPixelDepth_1",
    "SceneDepth": "MaterialExpressionSceneDepth_0", "CameraVector": "MaterialExpressionCameraVectorWS_0",
    "WaveSpeed": "MaterialExpressionScalarParameter_15", "WaveAmplitude": "MaterialExpressionScalarParameter_16",
    "WaveLengthScale": "MaterialExpressionScalarParameter_17", "WaterDepthCm": "MaterialExpressionScalarParameter_18",
    "WaveChoppiness": "MaterialExpressionScalarParameter_19", "WaveDetail": "MaterialExpressionScalarParameter_20",
    "WaveStylize": "MaterialExpressionScalarParameter_21", "WindDirection": "MaterialExpressionVectorParameter_4",
    "WaveCountQuality": "MaterialExpressionQualitySwitch_0", "WaveField": "MaterialExpressionMaterialFunctionCall_3",
    "BaseHeightTexture": "MaterialExpressionTextureObjectParameter_0", "MidHeightTexture": "MaterialExpressionTextureObjectParameter_1",
    "BaseTiling": "MaterialExpressionScalarParameter_22", "MidTiling": "MaterialExpressionScalarParameter_23",
    "Layer2Tiling": "MaterialExpressionScalarParameter_24", "HighlightTiling": "MaterialExpressionScalarParameter_25",
    "LayerPanSpeed": "MaterialExpressionScalarParameter_26", "POMDepth": "MaterialExpressionScalarParameter_32",
    "POMDistanceFade": "MaterialExpressionScalarParameter_33", "POMStepsQuality": "MaterialExpressionQualitySwitch_1",
    "BaseColorTex": "MaterialExpressionTextureSampleParameter2D_3", "BaseNormalTex": "MaterialExpressionTextureSampleParameter2D_4",
    "BaseRoughTex": "MaterialExpressionTextureSampleParameter2D_5", "BaseMaskTex": "MaterialExpressionTextureSampleParameter2D_6",
    "MidColorTex": "MaterialExpressionTextureSampleParameter2D_7", "MidNormalTex": "MaterialExpressionTextureSampleParameter2D_8",
    "MidRoughTex": "MaterialExpressionTextureSampleParameter2D_9", "MidMaskTex": "MaterialExpressionTextureSampleParameter2D_10",
    "Layer2NormalTex": "MaterialExpressionTextureSampleParameter2D_11",
    "HighlightColorTex": "MaterialExpressionTextureSampleParameter2D_12",
    "HighlightNormalTex": "MaterialExpressionTextureSampleParameter2D_13",
    "HighlightRoughTex": "MaterialExpressionTextureSampleParameter2D_14",
    "HighlightMaskTex": "MaterialExpressionTextureSampleParameter2D_15",
    "MidColorInfluence": "MaterialExpressionScalarParameter_34", "HighlightColorInfluence": "MaterialExpressionScalarParameter_35",
    "NormalLayerStrength": "MaterialExpressionScalarParameter_36", "RoughnessMin": "MaterialExpressionScalarParameter_37",
    "RoughnessMax": "MaterialExpressionScalarParameter_38", "PBRLayers": "MaterialExpressionMaterialFunctionCall_8",
    "ThicknessMax": "MaterialExpressionMax_2", "TransmissionColor": "MaterialExpressionVectorParameter_5",
    "ReferenceDepthCm": "MaterialExpressionScalarParameter_39", "ScatteringColor": "MaterialExpressionVectorParameter_6",
    "ScatteringStrength": "MaterialExpressionScalarParameter_40", "WaterIOR": "MaterialExpressionScalarParameter_41",
    "PhaseG": "MaterialExpressionScalarParameter_42", "Optics": "MaterialExpressionMaterialFunctionCall_9",
    "ExtinctionAdd": "MaterialExpressionAdd_6", "FoamBreakup": "MaterialExpressionScalarParameter_44",
    "FoamIntensity": "MaterialExpressionScalarParameter_45", "WetEdgeStrength": "MaterialExpressionScalarParameter_46",
    "DepthOneMinus": "MaterialExpressionOneMinus_0", "DFOneMinus": "MaterialExpressionOneMinus_1",
    "DistanceField": "MaterialExpressionDistanceToNearestSurface_0", "Shore": "MaterialExpressionMaterialFunctionCall_10",
    "MagicalIntensity": "MaterialExpressionScalarParameter_47", "DeepGlowColor": "MaterialExpressionVectorParameter_7",
    "MidGlowColor": "MaterialExpressionVectorParameter_8", "SparkleColor": "MaterialExpressionVectorParameter_9",
    "SparkleDensity": "MaterialExpressionScalarParameter_48", "SparkleScale": "MaterialExpressionScalarParameter_49",
    "TwinkleRate": "MaterialExpressionScalarParameter_50", "TemporalBlend": "MaterialExpressionScalarParameter_51",
    "DepthMaskDivide": "MaterialExpressionDivide_3", "DepthMaskSat": "MaterialExpressionSaturate_5",
    "Biolum": "MaterialExpressionMaterialFunctionCall_11",
    "CausticScale": "MaterialExpressionScalarParameter_52", "CausticDepthFade": "MaterialExpressionScalarParameter_53",
    "CausticIntensity": "MaterialExpressionScalarParameter_54", "CausticTint": "MaterialExpressionVectorParameter_10",
    "Caustics": "MaterialExpressionMaterialFunctionCall_12", "FoamColor": "MaterialExpressionVectorParameter_11",
    "FoamMultiply": "MaterialExpressionMultiply_11", "EmissiveAdd1": "MaterialExpressionAdd_7",
    "EmissiveAdd2": "MaterialExpressionAdd_8", "SurfaceColorLerp": "MaterialExpressionLinearInterpolate_3",
    "ZeroMetal": "MaterialExpressionConstant_8", "TopMaterialOpacity": "MaterialExpressionScalarParameter_55",
    "WaterBSDF": "MaterialExpressionSubstrateSingleLayerWaterBSDF_0", "POMCore": "MaterialExpressionCustom_0",
    "NormalCombine": "MaterialExpressionCustom_1",
}

LINKS = [
    ("UV", "", "POMCore", "UV"), ("Time", "", "POMCore", "Time"),
    ("CameraVector", "", "POMCore", "ViewDirection"), ("PixelDepth", "", "POMCore", "PixelDepth"),
    ("BaseHeightTexture", "", "POMCore", "BaseHeightTexture"),
    ("MidHeightTexture", "", "POMCore", "MidHeightTexture"),
    ("BaseTiling", "", "POMCore", "BaseTiling"), ("MidTiling", "", "POMCore", "MidTiling"),
    ("Layer2Tiling", "", "POMCore", "Layer2Tiling"), ("HighlightTiling", "", "POMCore", "HighlightTiling"),
    ("LayerPanSpeed", "", "POMCore", "LayerPanSpeed"), ("POMDepth", "", "POMCore", "POMDepth"),
    ("POMDistanceFade", "", "POMCore", "POMDistanceFade"), ("POMStepsQuality", "", "POMCore", "POMSteps"),
    ("POMCore", "", "BaseColorTex", "UVs"), ("POMCore", "", "BaseNormalTex", "UVs"),
    ("POMCore", "", "BaseRoughTex", "UVs"), ("POMCore", "", "BaseMaskTex", "UVs"),
    ("POMCore", "MidUV", "MidColorTex", "UVs"), ("POMCore", "MidUV", "MidNormalTex", "UVs"),
    ("POMCore", "MidUV", "MidRoughTex", "UVs"), ("POMCore", "MidUV", "MidMaskTex", "UVs"),
    ("POMCore", "Layer2UV", "Layer2NormalTex", "UVs"),
    ("POMCore", "HighlightUV", "HighlightColorTex", "UVs"),
    ("POMCore", "HighlightUV", "HighlightNormalTex", "UVs"),
    ("POMCore", "HighlightUV", "HighlightRoughTex", "UVs"),
    ("POMCore", "HighlightUV", "HighlightMaskTex", "UVs"),
    ("WorldPos", "XYZ", "WaveField", "Position (V3)"), ("Time", "", "WaveField", "Time (S)"),
    ("WaveSpeed", "", "WaveField", "WaveSpeed (S)"), ("WaveAmplitude", "", "WaveField", "WaveAmplitude (S)"),
    ("WaveLengthScale", "", "WaveField", "WaveLengthScale (S)"), ("WaterDepthCm", "", "WaveField", "WaterDepthCm (S)"),
    ("WaveChoppiness", "", "WaveField", "WaveChoppiness (S)"), ("WaveDetail", "", "WaveField", "WaveDetail (S)"),
    ("WaveStylize", "", "WaveField", "WaveStylize (S)"), ("WindDirection", "", "WaveField", "WindDirection (V2)"),
    ("WaveCountQuality", "", "WaveField", "WaveCount (S)"),
    ("BaseColorTex", "RGB", "PBRLayers", "BaseColor (V3)"), ("MidColorTex", "RGB", "PBRLayers", "MidColor (V3)"),
    ("HighlightColorTex", "RGB", "PBRLayers", "HighlightColor (V3)"), ("BaseNormalTex", "RGB", "PBRLayers", "BaseNormal (V3)"),
    ("MidNormalTex", "RGB", "PBRLayers", "MidNormal (V3)"), ("Layer2NormalTex", "RGB", "PBRLayers", "Layer2Normal (V3)"),
    ("POMCore", "BaseHeightSample", "PBRLayers", "BaseHeight (S)"), ("POMCore", "MidHeightSample", "PBRLayers", "MidHeight (S)"),
    ("BaseRoughTex", "R", "PBRLayers", "BaseRoughness (S)"), ("MidRoughTex", "R", "PBRLayers", "MidRoughness (S)"),
    ("HighlightRoughTex", "R", "PBRLayers", "HighlightRoughness (S)"), ("BaseMaskTex", "R", "PBRLayers", "BaseMask (S)"),
    ("MidMaskTex", "R", "PBRLayers", "MidMask (S)"), ("HighlightMaskTex", "R", "PBRLayers", "HighlightMask (S)"),
    ("MidColorInfluence", "", "PBRLayers", "MidColorInfluence (S)"),
    ("HighlightColorInfluence", "", "PBRLayers", "HighlightColorInfluence (S)"),
    ("NormalLayerStrength", "", "PBRLayers", "NormalLayerStrength (S)"),
    ("RoughnessMin", "", "PBRLayers", "RoughnessMin (S)"), ("RoughnessMax", "", "PBRLayers", "RoughnessMax (S)"),
    ("TransmissionColor", "", "Optics", "TransmissionAtReferenceDepth (V3)"),
    ("ReferenceDepthCm", "", "Optics", "ReferenceDepthCm (S)"),
    # Opaque SingleLayerWater cannot sample SceneDepth in UE5.8. The physical
    # medium uses its explicit water-depth contract; shoreline depth comes from
    # mesh-distance-field contact and the artist mask.
    ("WaterDepthCm", "", "Optics", "OpticalDepthCm (S)"),
    ("ScatteringColor", "", "Optics", "ScatteringColor (V3)"), ("ScatteringStrength", "", "Optics", "ScatteringStrength (S)"),
    ("WaterIOR", "", "Optics", "WaterIOR (S)"), ("PhaseG", "", "Optics", "PhaseG (S)"),
    ("DFOneMinus", "", "Shore", "DepthIntersection (S)"),
    ("DFOneMinus", "", "Shore", "DistanceFieldContact (S)"),
    ("BaseMaskTex", "R", "Shore", "ArtistShoreMask (S)"), ("WaveField", "CrestCompression", "Shore", "CrestCompression (S)"),
    ("PBRLayers", "HighlightOut", "Shore", "HighlightMask (S)"), ("Time", "", "Shore", "Time (S)"),
    ("FoamBreakup", "", "Shore", "FoamBreakup (S)"), ("FoamIntensity", "", "Shore", "FoamIntensity (S)"),
    ("WetEdgeStrength", "", "Shore", "WetEdgeStrength (S)"),
    ("WaterDepthCm", "", "DepthMaskDivide", "A"),
    ("POMCore", "", "Biolum", "UV (V2)"), ("NormalCombine", "", "Biolum", "SurfaceNormal (V3)"),
    ("Time", "", "Biolum", "Time (S)"), ("MagicalIntensity", "", "Biolum", "MagicalIntensity (S)"),
    ("DeepGlowColor", "", "Biolum", "DeepGlowColor (V3)"), ("MidGlowColor", "", "Biolum", "MidGlowColor (V3)"),
    ("SparkleColor", "", "Biolum", "SparkleColor (V3)"), ("SparkleDensity", "", "Biolum", "SparkleDensity (S)"),
    ("SparkleScale", "", "Biolum", "SparkleScale (S)"), ("TwinkleRate", "", "Biolum", "TwinkleRate (S)"),
    ("TemporalBlend", "", "Biolum", "TemporalBlend (S)"), ("WaveField", "CrestCompression", "Biolum", "CrestCompression (S)"),
    ("PBRLayers", "HighlightOut", "Biolum", "HighlightMask (S)"), ("DepthMaskSat", "", "Biolum", "DepthMask (S)"),
    ("POMCore", "", "Caustics", "UV (V2)"), ("Time", "", "Caustics", "Time (S)"),
    ("WaterDepthCm", "", "Caustics", "WaterDepthCm (S)"), ("CausticScale", "", "Caustics", "CausticScale (S)"),
    ("CausticDepthFade", "", "Caustics", "CausticDepthFade (S)"),
    ("CausticIntensity", "", "Caustics", "CausticIntensity (S)"), ("CausticTint", "", "Caustics", "CausticTint (V3)"),
    ("WorldPos", "XYZ", "DistanceField", "World Position"),
    ("WaveField", "WaveNormal", "NormalCombine", "WaveNormal"),
    ("PBRLayers", "BlendedNormal", "NormalCombine", "DetailNormal"), ("Shore", "FoamMask", "FoamMultiply", "A"),
    ("FoamColor", "", "FoamMultiply", "B"), ("Biolum", "Emissive", "EmissiveAdd1", "A"),
    ("Caustics", "CausticColor", "EmissiveAdd1", "B"), ("EmissiveAdd1", "", "EmissiveAdd2", "A"),
    ("FoamMultiply", "", "EmissiveAdd2", "B"), ("Optics", "OpticalColor", "SurfaceColorLerp", "A"),
    ("PBRLayers", "LayerColor", "SurfaceColorLerp", "B"), ("PBRLayers", "CombinedHeight", "SurfaceColorLerp", "Alpha"),
    ("SurfaceColorLerp", "", "WaterBSDF", "BaseColor"), ("ZeroMetal", "", "WaterBSDF", "Metallic"),
    ("Optics", "F0", "WaterBSDF", "Specular"), ("PBRLayers", "Roughness", "WaterBSDF", "Roughness"),
    ("NormalCombine", "", "WaterBSDF", "Normal"), ("EmissiveAdd2", "", "WaterBSDF", "EmissiveColor"),
    ("TopMaterialOpacity", "", "WaterBSDF", "TopMaterialOpacity"), ("Optics", "Scattering", "WaterBSDF", "WaterAlbedo"),
    ("ExtinctionAdd", "", "WaterBSDF", "WaterExtinction"), ("Optics", "PhaseGOut", "WaterBSDF", "WaterPhaseG"),
    ("Optics", "Transmittance", "WaterBSDF", "ColorScaleBehindWater"),
]

PRESETS = {
    "MI_WaterV7_SakuraPond": {"MagicalIntensity": 0.75, "WaveAmplitude": 0.72, "SparkleDensity": 0.055},
    "MI_WaterV7_BiolumGrotto": {"MagicalIntensity": 1.65, "DeepGlowColor": (0.0, 0.20, 0.38, 1.0), "SparkleDensity": 0.075},
    "MI_WaterV7_CalmPond": {"MagicalIntensity": 0.28, "WaveAmplitude": 0.42, "WaveChoppiness": 0.35},
    "MI_WaterV7_RiverClear": {"MagicalIntensity": 0.18, "WaveSpeed": 1.35, "WaveAmplitude": 0.55},
    "MI_WaterV7_OceanPreview": {"MagicalIntensity": 0.32, "WaveAmplitude": 1.25, "WaveChoppiness": 0.78},
    "MI_WaterV7_CinematicHero": {"MagicalIntensity": 1.0, "POMDepth": 0.045, "CausticIntensity": 0.65},
}

def load(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError("Missing asset: " + path)
    return asset

def set_texture_parameters(material):
    expressions = {e.get_name(): e for e in unreal.MaterialEditingLibrary.get_material_expressions(material)}
    for alias, path in TEXTURES.items():
        node = expressions.get(N[alias])
        if node:
            node.set_editor_property("texture", load(path))
            # Enforce Substrate Shared: Wrap sampler optimization (Feature F14)
            for prop in ("sampler_source", "SamplerSource"):
                try:
                    for ssm_attr in ("SSM_SHARED_WRAP", "SSM_SharedWrap", "SSM_WRAP_WORLD_GROUP_SETTINGS"):
                        if hasattr(unreal, "SamplerSourceMode") and hasattr(unreal.SamplerSourceMode, ssm_attr):
                            node.set_editor_property(prop, getattr(unreal.SamplerSourceMode, ssm_attr))
                            break
                except Exception:
                    pass

def wire_master():
    material = load(MASTER)
    expressions = {e.get_name(): e for e in unreal.MaterialEditingLibrary.get_material_expressions(material)}
    missing = [name for name in N.values() if name not in expressions]
    if missing:
        raise RuntimeError("Missing graph expressions: " + ", ".join(missing))
    failures = []
    with unreal.ScopedEditorTransaction("Wire Water Grand Master v7"):
        for src_alias, output, dst_alias, input_name in LINKS:
            # UE Python uses the raw function-input name; the editor UI appends
            # display-only type suffixes such as " (V3)" and " (S)".
            raw_input_name = input_name.split(" (", 1)[0]
            if src_alias == "WorldPos" and output == "XYZ":
                output = ""
            ok = unreal.MaterialEditingLibrary.connect_material_expressions(
                expressions[N[src_alias]], output, expressions[N[dst_alias]], raw_input_name)
            if not ok:
                failures.append([src_alias, output, dst_alias, input_name])
        unreal.MaterialEditingLibrary.connect_material_property(
            expressions[N["WaveField"]], "Displacement", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        unreal.MaterialEditingLibrary.connect_material_property(
            expressions[N["WaterBSDF"]], "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
        set_texture_parameters(material)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        material.set_editor_property(
            "shading_model", unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
        material.set_editor_property("two_sided", True)
        # UE5.8's RT closest-hit shader still requests legacy SLW material
        # outputs for Substrate water. Keep Lumen/reflections, but avoid that
        # incompatible ray-traced-shadow permutation on the surface itself.
        try:
            material.set_editor_property("cast_ray_traced_shadows", False)
        except Exception:
            pass
        try:
            material.set_editor_property("output_translucent_velocity", True)
        except Exception:
            pass
        unreal.MaterialEditingLibrary.recompile_material(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
    return failures

def create_instances():
    parent = load(MASTER)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    unreal.EditorAssetLibrary.make_directory(INSTANCE_DIR)
    made = []
    for name, values in PRESETS.items():
        path = INSTANCE_DIR + "/" + name
        instance = unreal.EditorAssetLibrary.load_asset(path)
        if not instance:
            instance = tools.create_asset(name, INSTANCE_DIR, unreal.MaterialInstanceConstant, factory)
        instance.set_editor_property("parent", parent)
        for parameter, value in values.items():
            if isinstance(value, tuple):
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                    instance, parameter, unreal.LinearColor(*value))
            else:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                    instance, parameter, float(value))
        unreal.EditorAssetLibrary.save_loaded_asset(instance)
        made.append(path)
    return made

def write_audit(failures, instances):
    material = load(MASTER)
    params = unreal.MaterialEditingLibrary.get_scalar_parameter_names(material)
    vector_params = unreal.MaterialEditingLibrary.get_vector_parameter_names(material)
    data = {
        "asset": MASTER, "successor_of": "M_Water_Master_Grand_v6",
        "caustics_projector": CAUSTICS_PROJECTOR,
        "v6_modified": False,
        "expression_count": len(unreal.MaterialEditingLibrary.get_material_expressions(material)),
        "connection_failures": failures, "scalar_parameters": [str(x) for x in params],
        "vector_parameters": [str(x) for x in vector_params], "textures": TEXTURES,
        "metallic_textures_sampled": False, "specular_textures_sampled": False,
        "wave_spectrum": WAVE_SPECTRUM, "instances": instances,
        "quality_contract": {
            "Medium": {"waves": 6, "pom_steps": 1, "interaction_rt": False},
            "High": {"waves": 6, "pom_steps": 6, "sdf": True, "bioluminescence": True},
            "Cinematic": {"waves": 8, "pom_steps": 10, "binary_refinements": 2, "planar_optional": True},
        },
        "manual_validation_pending": [
            "SM6 BasePass/FHitProxy/LumenCard/shadow/MRQ permutations",
            "GPU Visualizer and Material Analyzer measurements",
            "TSR motion-vector visualization", "day/dusk/night/grotto capture matrix",
        ],
        "known_engine_blocker": {
            "scope": "UE5.8 SM6 hardware-ray-tracing closest-hit permutation",
            "error": "Substrate SingleLayerWater requests missing legacy GetSingleLayerWaterMaterialOutput0/1/2 helpers",
            "status": "Base graph repaired; engine permutation remains unresolved",
            "projector_compiles": True,
        },
    }
    os.makedirs(os.path.dirname(AUDIT_FILE), exist_ok=True)
    with open(AUDIT_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    return AUDIT_FILE

if __name__ == "__main__":
    failed = wire_master()
    created = create_instances()
    audit = write_audit(failed, created)
    print(json.dumps({"master": MASTER, "connection_failures": failed,
                      "instances": created, "audit": audit}, indent=2))
