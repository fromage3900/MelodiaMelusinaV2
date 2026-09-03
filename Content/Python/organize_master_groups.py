"""Professional param organization for M_Master_Toon_Universal.

Assigns every parameter a canonical Group + SortPriority so the material-instance
editor reads top-to-bottom in a logical order (base surface -> texture layers ->
stylization -> Nikki -> magic -> character -> world -> cinematic). Metadata-only:
does NOT touch graph topology, so it's safe and idempotent.

Headless (editor closed, SCC can stay on — no asset create/delete):
  UnrealEditor-Cmd BS_GodFile.uproject
    -ExecutePythonScript=".../organize_master_groups.py" -unattended -nullrhi
"""
from __future__ import annotations

import unreal

MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"

# (Panel group label, [param names in display order]). Group order == panel order.
GROUPS: list[tuple[str, list[str]]] = [
    ("01 | Base Surface", ["BaseTint", "TextureWeight", "UVScale", "Roughness", "Metallic"]),
    ("02 | Triplanar", ["bTriplanar", "TriplanarTiling"]),
    ("03 | Texture Layer A", ["Albedo", "NormalMap", "ORM", "HeightMap",
                              "LayerA_TextureWeight", "LayerA_ParallaxScale", "LayerA_NormalStrength"]),
    ("04 | Texture Layer B", ["LayerB_Albedo", "LayerB_NormalMap", "LayerB_ORM",
                              "LayerB_HeightMap", "LayerB_TextureWeight",
                              "LayerB_ParallaxScale", "LayerB_NormalStrength", "LayerBlend"]),
    ("05 | Parallax", ["ParallaxScale", "ParallaxStrength", "ParallaxSteps", "ParallaxMode",
                       "ParallaxHeight", "NormalStrength", "NormalPower"]),
    ("06 | Macro & Detail", ["MacroVariationStrength", "MacroScale", "DetailNormal",
                             "DetailTiling", "DetailStrength"]),
    ("07 | Temporal / Ink", ["TemporalStrength", "WindSpeed", "NoiseScale",
                             "SmearStrength", "BoilIntensity"]),
    ("08 | Nikki Rim & Glow", ["bNikkiFast", "bNikkiHero",
                         "RimColor", "RimPower", "RimIntensity", "RimSoftness",
                         "RimWidth", "RimBias", "RimClamp",
                         "GlowColor", "GlowIntensity",
                         "InnerGlowIntensity", "InnerGlowWidth", "InnerGlowColor",
                         "BloomBoost"]),
    ("09 | Nikki Sparkle", ["SparkleMask", "SparkleScale", "SparkleIntensity", "SparkleColor",
                         "SparkleThreshold", "SparkleContrast",
                         "SparkleDriftSpeed", "SparkleTwinkleSpeed", "SparkleNoiseScale",
                         "SparkleColorLow", "SparkleColorHigh", "SparkleColorLerp",
                         "bSparkleAdvanced"]),
    ("10 | Nikki Iridescence & Sheen", ["DreamTint", "PastelLift",
                         "DreamSaturation", "DreamContrast", "DreamShadowLift", "DreamHighlightSoft", "DreamHueShift",
                         "Iridescence", "IridescenceTint", "IridescencePower", "IridescenceBias", "IridescenceRoughnessAtten",
                         "FabricSheen", "SheenTint", "SheenPower", "SheenWidth", "SheenBias", "bSheenUsesNormal"]),
    ("11 | Gilding", ["GildingStrength", "GoldTint", "GoldRoughness", "GoldEmissive",
                      "CurvatureSensitivity"]),
    ("12 | Shadow Garden (Flowers)", ["ShadowFlowerStrength", "ShadowFlowerScale",
                                      "ShadowFlowerColor"]),
    ("13 | Shadow Dream", ["ShadowDreamTint", "ShadowDreamStrength", "ShadowSoftness"]),
    ("14 | Celestial (Nebula)", ["ConstellationRampLow", "ConstellationRampMid",
                                 "ConstellationRampHigh", "ConstellationStrength",
                                 "ConstellationScale", "ConstellationPhase",
                                 "CelestialStarIntensity", "CelestialTwinkle",
                                 "CelestialNebulaStrength", "CelestialNebulaScale",
                                 "CelestialGalaxyStrength", "CelestialGalaxyScale",
                                 "CelestialGalaxyArms", "StarMap", "CelestialToonSteps"]),
    ("15 | Fairy Dust", ["FairyMotifStyle", "FairyDustIntensity", "FairyDustScale",
                         "FairyDustColor", "FairyHighlightThreshold", "FairyGlyphMask"]),
    ("16 | Magical (Henshin)", ["MagicalTransform", "MotifMask", "MotifScale",
                                "MotifColor", "TransformGlow", "WipeSoftness",
                                "MagicalPalette"]),
    ("17 | Character", ["SkinWrapStrength", "SkinWrapRadius", "SkinShadowTint",
                        "SkinShadowStrength", "CheekWarmthStrength", "CheekWarmthColor",
                        "CheekWarmthBias", "EyeHighlightStrength", "EyeHighlightPower",
                        "EyeHighlightColor", "HairSheenStrength", "HairSheenPower",
                        "HairSheenTint"]),
    ("18 | Elemental", ["ElementType", "ElementStrength", "ElementEmissiveBoost"]),
    ("19 | World / Weather", ["WetnessStrength", "WetnessRoughness", "WetnessDarken",
                              "WetnessNormalFlatten", "SnowDustStrength", "SnowDustColor",
                              "SnowUpBias", "MossConcavityStrength", "MossColor",
                              "MossCurvatureSens"]),
    ("20 | Cinematic", ["ContactRimStrength", "ContactRimPower", "ContactRimColor",
                        "DistanceFadeStrength", "DistanceFadeStart", "DistanceFadeEnd",
                        "AtmosphericFadeColor", "DitherDissolveStrength", "DitherEdgeGlow"]),
    ("21 | Time of Day", ["UseUDSTimeOfDay", "TimeOfDayMPCStrength", "TimeOfDayWarmth"]),
]

# Flatten to name -> (group, sort_priority). Sort priority strides by group so
# the panel orders groups then params predictably.
PARAM_META: dict[str, tuple[str, int]] = {}
for gi, (label, names) in enumerate(GROUPS):
    for pi, name in enumerate(names):
        PARAM_META[name] = (label, gi * 100 + pi)


def main():
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception as e:
        unreal.log_warning(f"[Organize] registry: {e}")

    if not unreal.EditorAssetLibrary.does_asset_exist(MASTER):
        unreal.log_error("[Organize] master missing")
        return

    m = unreal.load_asset(MASTER)
    seen, set_count, unmapped = set(), 0, []
    for expr in unreal.MaterialEditingLibrary.get_material_expressions(m) or []:
        pname = None
        for prop in ("parameter_name", "ParameterName"):
            try:
                raw = expr.get_editor_property(prop)
                if raw:
                    pname = str(raw)
                    break
            except Exception:
                continue
        if not pname:
            continue
        seen.add(pname)
        meta = PARAM_META.get(pname)
        if not meta:
            unmapped.append(pname)
            continue
        group, prio = meta
        try:
            expr.set_editor_property("group", group)
            expr.set_editor_property("sort_priority", prio)
            set_count += 1
        except Exception as e:
            unreal.log_warning(f"[Organize] {pname}: {e}")

    unreal.MaterialEditingLibrary.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m, only_if_is_dirty=False)
    mapped_missing = sorted(set(PARAM_META) - seen)
    unreal.log(f"[Organize] grouped={set_count}; unmapped_params={sorted(set(unmapped))}; "
               f"mapped_but_absent={mapped_missing}")
    print(f"ORGANIZE_OK grouped={set_count} unmapped={len(set(unmapped))} absent={len(mapped_missing)}")
    if unmapped:
        print(f"UNMAPPED (need a group): {sorted(set(unmapped))}")


if __name__ == "__main__":
    main()
