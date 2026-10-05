"""Author Quality Tier instances for M_Master_Toon_Universal and M_Master_Nikki.

Creates 4 tier instances per master (Fast / Standard / Hero / Cinematic) with
static switch overrides that gate expensive feature stacks per tier.

Universal Tier contract:
  Fast       — Base surface only. No layers, no triplanar, no parallax, no Nikki
               stack, no celestial, no fairy dust, no weather, no elemental,
               no impasto, no dream rim, no cloth wind, no gemstone, no SDF.
  Standard   — Base + LayerA + LayerB + triplanar + basic parallax + DFContactBlend
               + shadow ramp. No Nikki stack, no celestial, no fairy dust, no
               weather, no elemental, no impasto, no dream rim, no cloth wind,
               no gemstone, no SDF.
  Hero       — Standard + LayerC + Nikki stack + DreamRim + SparkleAdvanced +
               Celestial + FairyDust + Elemental + ClothWind + Gemstone + SDF +
               Impasto. No weather.
  Cinematic  — Everything including weather.

Nikki Tier contract:
  Fast       — Base landscape only. No Nikki features, no triplanar, no
               extended layers, no Gaea masks.
  Standard   — Base + extended layers + Gaea masks + triplanar + snow.
               No Nikki features.
  Hero       — Standard + Nikki features (TwinkleIris, PastelGrade, StickerShade,
               StickerEdge, GlitterHalo, PearlSheen, SDFRibbon, PetalShadow,
               DreamWatercolor, SquishWPO, KawaiiSquish, ShadowDream).
               No rock detail albedo.
  Cinematic  — Everything including rock detail albedo.

Run inside UE Editor via Monolith (editor_query:run_python):
  import author_universal_nikki_tiers
  import importlib
  importlib.reload(author_universal_nikki_tiers)
  author_universal_nikki_tiers.build_all()
"""
from __future__ import annotations

import unreal

UNIVERSAL_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
NIKKI_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki"
TIER_DIR = "/Game/EnvSandbox/Materials/Instances/Tiers"

# ─────────────────────────────────────────────────────────────────────────────
# Universal Master static switches (from T3D baseline)
# ─────────────────────────────────────────────────────────────────────────────
UNIVERSAL_SWITCHES = {
    # Core surface
    "triplanar": "bTriplanar_Active",
    "layer_a": "bLayerA_Active",
    "layer_b": "bLayerB_Active",
    "layer_c": "bLayerC_Active",
    "stack3": "bStackLayer3_Active",
    "height_to_normal": "bUseHeightToNormal",
    "emissive_map": "bUseEmissiveMap",
    "opacity_map": "bUseOpacityMap",
    "separate_roughness": "bUseSeparateRoughnessMap",
    "separate_metallic": "bUseSeparateMetallicMap",
    # Contact & shadow
    "df_contact": "bDFContactBlend_Active",
    "shadow_ramp": "bShadowRamp_Active",
    # Nikki stack
    "nikki_hero": "bNikkiHero",
    "sparkle_advanced": "bSparkleAdvanced",
    "sheen_uses_normal": "bSheenUsesNormal",
    # Premium features
    "dream_rim": "bDreamRim_active".replace("_active", "_Active"),
    "celestial": "bCelestial_Active",
    "fairy_dust": "bFairyDust_Active",
    "weather": "bWeather_Active",
    "elemental": "bElemental_Active",
    "impasto": "bImpasto_Active",
    "cloth_wind": "bClothWind_Active",
    "gemstone": "bGemstone_Active",
    "face_sdf": "bFaceSDF_UV1",
    "mesh_blend": "bMeshBlendActivator_Active",
}

UNIVERSAL_TIERS = {
    "Fast": {
        "triplanar": False,
        "layer_a": False,
        "layer_b": False,
        "layer_c": False,
        "stack3": False,
        "height_to_normal": False,
        "emissive_map": False,
        "opacity_map": False,
        "separate_roughness": False,
        "separate_metallic": False,
        "df_contact": False,
        "shadow_ramp": False,
        "nikki_hero": False,
        "sparkle_advanced": False,
        "sheen_uses_normal": False,
        "dream_rim": False,
        "celestial": False,
        "fairy_dust": False,
        "weather": False,
        "elemental": False,
        "impasto": False,
        "cloth_wind": False,
        "gemstone": False,
        "face_sdf": False,
        "mesh_blend": False,
    },
    "Standard": {
        "triplanar": True,
        "layer_a": True,
        "layer_b": True,
        "layer_c": False,
        "stack3": False,
        "height_to_normal": True,
        "emissive_map": False,
        "opacity_map": False,
        "separate_roughness": False,
        "separate_metallic": False,
        "df_contact": True,
        "shadow_ramp": True,
        "nikki_hero": False,
        "sparkle_advanced": False,
        "sheen_uses_normal": False,
        "dream_rim": False,
        "celestial": False,
        "fairy_dust": False,
        "weather": False,
        "elemental": False,
        "impasto": False,
        "cloth_wind": False,
        "gemstone": False,
        "face_sdf": False,
        "mesh_blend": False,
    },
    "Hero": {
        "triplanar": True,
        "layer_a": True,
        "layer_b": True,
        "layer_c": True,
        "stack3": True,
        "height_to_normal": True,
        "emissive_map": True,
        "opacity_map": True,
        "separate_roughness": True,
        "separate_metallic": True,
        "df_contact": True,
        "shadow_ramp": True,
        "nikki_hero": True,
        "sparkle_advanced": True,
        "sheen_uses_normal": True,
        "dream_rim": True,
        "celestial": True,
        "fairy_dust": True,
        "weather": False,
        "elemental": True,
        "impasto": True,
        "cloth_wind": True,
        "gemstone": True,
        "face_sdf": True,
        "mesh_blend": False,
    },
    "Cinematic": {
        "triplanar": True,
        "layer_a": True,
        "layer_b": True,
        "layer_c": True,
        "stack3": True,
        "height_to_normal": True,
        "emissive_map": True,
        "opacity_map": True,
        "separate_roughness": True,
        "separate_metallic": True,
        "df_contact": True,
        "shadow_ramp": True,
        "nikki_hero": True,
        "sparkle_advanced": True,
        "sheen_uses_normal": True,
        "dream_rim": True,
        "celestial": True,
        "fairy_dust": True,
        "weather": True,
        "elemental": True,
        "impasto": True,
        "cloth_wind": True,
        "gemstone": True,
        "face_sdf": True,
        "mesh_blend": True,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Nikki Master static switches (from T3D baseline)
# ─────────────────────────────────────────────────────────────────────────────
NIKKI_SWITCHES = {
    # Core landscape
    "gaea_whole": "bGaeaWholeLandscapeColor",
    "gaea_masks": "bUseGaeaMasks",
    "extended_layers": "bUseExtendedLayers",
    "triplanar": "bTriplanarPro_Active",
    "rock_triplanar_normals": "bRockTriplanarNormals",
    "rock_detail": "bRockDetailAlbedo",
    # Snow
    "snow_frost_band": "bSnowFrostDistanceBand",
    "snow_coverage_breakup": "bSnowCoverageBreakup",
    # Nikki features
    "squish_wpo": "bNikkiSquishWPO_Active",
    "kawaii_squish": "bKawaiiSquish_Active",
    "petal_shadow": "bNikkiPetalShadow_Active",
    "glitter_halo": "bNikkiGlitterHalo_Active",
    "sticker_edge": "bNikkiStickerEdge_Active",
    "dream_watercolor": "bNikkiDreamWatercolor_Active",
    "pearl_sheen": "bNikkiPearlSheen_Active",
    "sdf_ribbon": "bNikkiSDFRibbon_Active",
    "shadow_dream": "bShadowDream_Active",
    "pastel_grade": "bNikkiPastelGrade_Active",
    "twinkle_iris": "bNikkiTwinkleIris_Active",
    "sticker_shade": "bNikkiStickerShade_Active",
}

NIKKI_TIERS = {
    "Fast": {
        "gaea_whole": False,
        "gaea_masks": False,
        "extended_layers": False,
        "triplanar": False,
        "rock_triplanar_normals": False,
        "rock_detail": False,
        "snow_frost_band": False,
        "snow_coverage_breakup": False,
        "squish_wpo": False,
        "kawaii_squish": False,
        "petal_shadow": False,
        "glitter_halo": False,
        "sticker_edge": False,
        "dream_watercolor": False,
        "pearl_sheen": False,
        "sdf_ribbon": False,
        "shadow_dream": False,
        "pastel_grade": False,
        "twinkle_iris": False,
        "sticker_shade": False,
    },
    "Standard": {
        "gaea_whole": True,
        "gaea_masks": True,
        "extended_layers": True,
        "triplanar": True,
        "rock_triplanar_normals": True,
        "rock_detail": False,
        "snow_frost_band": True,
        "snow_coverage_breakup": True,
        "squish_wpo": False,
        "kawaii_squish": False,
        "petal_shadow": False,
        "glitter_halo": False,
        "sticker_edge": False,
        "dream_watercolor": False,
        "pearl_sheen": False,
        "sdf_ribbon": False,
        "shadow_dream": False,
        "pastel_grade": False,
        "twinkle_iris": False,
        "sticker_shade": False,
    },
    "Hero": {
        "gaea_whole": True,
        "gaea_masks": True,
        "extended_layers": True,
        "triplanar": True,
        "rock_triplanar_normals": True,
        "rock_detail": False,
        "snow_frost_band": True,
        "snow_coverage_breakup": True,
        "squish_wpo": True,
        "kawaii_squish": True,
        "petal_shadow": True,
        "glitter_halo": True,
        "sticker_edge": True,
        "dream_watercolor": True,
        "pearl_sheen": True,
        "sdf_ribbon": True,
        "shadow_dream": True,
        "pastel_grade": True,
        "twinkle_iris": True,
        "sticker_shade": True,
    },
    "Cinematic": {
        "gaea_whole": True,
        "gaea_masks": True,
        "extended_layers": True,
        "triplanar": True,
        "rock_triplanar_normals": True,
        "rock_detail": True,
        "snow_frost_band": True,
        "snow_coverage_breakup": True,
        "squish_wpo": True,
        "kawaii_squish": True,
        "petal_shadow": True,
        "glitter_halo": True,
        "sticker_edge": True,
        "dream_watercolor": True,
        "pearl_sheen": True,
        "sdf_ribbon": True,
        "shadow_dream": True,
        "pastel_grade": True,
        "twinkle_iris": True,
        "sticker_shade": True,
    },
}


def _log(msg: str):
    unreal.log(f"[Universal+Nikki Tiers] {msg}")


def build_tier_instance(tier_name: str, master, switches: dict, overrides: dict, prefix: str) -> str:
    """Create or update a tier instance with static switch overrides."""
    inst_path = f"{TIER_DIR}/MI_{prefix}_Tier_{tier_name}"
    inst = unreal.EditorAssetLibrary.load_asset(inst_path)

    if inst is None:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        inst = tools.create_asset(
            f"MI_{prefix}_Tier_{tier_name}",
            TIER_DIR,
            unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew(),
        )

    if inst is None:
        raise RuntimeError(f"Failed to create tier instance at {inst_path}")

    unreal.MaterialEditingLibrary.set_material_instance_parent(inst, master)

    for switch_key, switch_param in switches.items():
        value = overrides.get(switch_key)
        if value is None:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(
                inst, switch_param, bool(value)
            )
        except Exception as e:
            _log(f"  Warning: could not set {switch_param} on {prefix}/{tier_name}: {e}")

    unreal.MaterialEditingLibrary.update_material_instance(inst)
    unreal.EditorAssetLibrary.save_loaded_asset(inst)
    _log(f"  Created/updated: {inst_path}")
    return inst_path


def build_all() -> dict:
    """Entry point: loads both masters and creates all tier instances."""
    _log("Starting Universal + Nikki Quality Tier authoring...")

    results = {"universal": [], "nikki": []}

    # Universal
    universal = unreal.EditorAssetLibrary.load_asset(UNIVERSAL_PATH)
    if universal is None:
        _log(f"ERROR: Universal master not found at {UNIVERSAL_PATH}")
    else:
        _log(f"Loaded Universal master: {UNIVERSAL_PATH}")
        for tier_name, overrides in UNIVERSAL_TIERS.items():
            _log(f"Building Universal tier: {tier_name}")
            path = build_tier_instance(tier_name, universal, UNIVERSAL_SWITCHES, overrides, "Universal")
            results["universal"].append(path)

    # Nikki
    nikki = unreal.EditorAssetLibrary.load_asset(NIKKI_PATH)
    if nikki is None:
        _log(f"ERROR: Nikki master not found at {NIKKI_PATH}")
    else:
        _log(f"Loaded Nikki master: {NIKKI_PATH}")
        for tier_name, overrides in NIKKI_TIERS.items():
            _log(f"Building Nikki tier: {tier_name}")
            path = build_tier_instance(tier_name, nikki, NIKKI_SWITCHES, overrides, "Nikki")
            results["nikki"].append(path)

    _log(f"Done. Universal: {len(results['universal'])} tiers, Nikki: {len(results['nikki'])} tiers.")
    return results


if __name__ == "__main__":
    build_all()
