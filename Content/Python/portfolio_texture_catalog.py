"""Compositing texture catalog: /Game/Textures + SDF/Textures roles for masters/instances.

Run audit (no editor):
  python Content/Python/portfolio_texture_catalog.py

Used by integrate_compositing_textures.py and setup_universal_instances.py.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT = PROJECT_ROOT / "Content"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "compositing_texture_catalog.json"

SDF = "/Game/EnvSandbox/Materials/SDF/Textures"
TEX = "/Game/Textures"
JRO = f"{TEX}/70_Japanese_Ornament_Alphas_vfxMed/70_Japanese_Ornament_Alphas/JRO_JP"


def jro_mask(stem: str) -> str:
    """Japanese ornament alpha mask path (vfxMed pack)."""
    if stem.endswith("_Mask"):
        base = stem
    else:
        base = f"{stem}_Mask"
    return f"{JRO}/{base}.{base}"


# Curated masks from 70_Japanese_Ornament_Alphas_vfxMed (baroque = ornate, zen = minimal)
JAPANESE_ORNAMENT = {
    "zen_minimal": jro_mask("JRO_JP_Ornament01_out"),
    "zen_circle": jro_mask("JRO_JP_Ornament03_out"),
    "zen_wave": jro_mask("JRO_JP_Ornament07_out"),
    "zen_bamboo": jro_mask("JRO_JP_Ornament23_out"),
    "zen_stone": jro_mask("JRO_JP_Ornament30_out"),
    "zen_sand": jro_mask("JRO_JP_Ornament35_out"),
    "baroque_filigree": jro_mask("JRO_JP_Ornament04_out"),
    "baroque_scroll": jro_mask("JRO_JP_Ornament08_1_out"),
    "baroque_rosette": jro_mask("JRO_JP_Ornament12_out"),
    "baroque_lattice": jro_mask("JRO_JP_Ornament19_2_out"),
    "baroque_mandala": jro_mask("JRO_JP_Ornament22_1_out"),
    "baroque_cathedral": jro_mask("JRO_JP_Ornament41_3_out"),
}

# Schema targets (portfolio SDF folder)
MARBLE = {
    "warm_stone": f"{SDF}/Marble/Marble_7_-_512x512.Marble_7_-_512x512",
    "cool_stone": f"{SDF}/Marble/Marble_3_-_512x512.Marble_3_-_512x512",
    "worn": f"{SDF}/Marble/Marble_5_-_512x512.Marble_5_-_512x512",
    "dark": f"{SDF}/Marble/Marble_9_-_512x512.Marble_9_-_512x512",
    "light": f"{SDF}/Marble/Marble_1_-_512x512.Marble_1_-_512x512",
}
HEIGHT = {
    "perlin": f"{TEX}/sbs_-_noise_texture_pack_-_512x512/512x512/Perlin/Perlin_1_-_512x512.Perlin_1_-_512x512",
    "perlin_sdf": f"{SDF}/Perlin/Perlin_1_-_512x512.Perlin_1_-_512x512",
}
MASK = {
    "voronoi_crack": f"{SDF}/Voronoi/Voronoi_2_-_512x512.Voronoi_2_-_512x512",
    "voronoi_swirl": f"{SDF}/Voronoi/Voronoi_11_-_512x512.Voronoi_11_-_512x512",
}
# /Game/Textures compositing library (SBS packs)
COMPOSITING = {
    "crack_overlay": f"{TEX}/sbs_-_noise_texture_pack_-_512x512/512x512/Cracks/Cracks_3_-_512x512.Cracks_3_-_512x512",
    "crack_heavy": f"{TEX}/sbs_-_noise_texture_pack_-_512x512/512x512/Cracks/Cracks_10_-_512x512.Cracks_10_-_512x512",
    "noise_fine": f"{TEX}/sbs_-_noise_texture_pack_-_512x512/512x512/Perlin/Perlin_10_-_512x512.Perlin_10_-_512x512",
    "abstract_a": f"{TEX}/sbs_-_seamless_abstract_pack_-_512x512/512x512/Texture_512x512_1.Texture_512x512_1",
    "gradient_warm": f"{TEX}/sbs_-_gradient_texture_pack_-_512x512/512x512/Basic/Horizontal_1_-_512x512.Horizontal_1_-_512x512",
    "space_nebula": (
        f"{TEX}/sbs_-_seamless_space_backgrounds_-_large_1024x1024/"
        "Large_1024x1024/Blue_Nebula/Blue_Nebula_1_-_1024x1024.Blue_Nebula_1_-_1024x1024"
    ),
}

# Author / Melodia custom textures (_PROJECT originals — permanent library)
PROJ = "/Game/_PROJECT/04_Materials/Textures"
CUSTOM = {
    "starry_albedo": f"{PROJ}/T_Starryfabric_albedo.T_Starryfabric_albedo",
    "starry_normal": f"{PROJ}/T_Starryfabric_normal.T_Starryfabric_normal",
    "starry_height": f"{PROJ}/T_Starryfabric_displace.T_Starryfabric_displace",
    "starry_orm": f"{PROJ}/T_Starryfabric_metal.T_Starryfabric_metal",
    "bss_sand_normal": f"{PROJ}/T_Sand_BSS_normal.T_Sand_BSS_normal",
    "wood_albedo": f"{PROJ}/T_WoodTrim_BaseColor.T_WoodTrim_BaseColor",
    "wood_normal": f"{PROJ}/T_WoodTrim_Normal.T_WoodTrim_Normal",
    "hearts_alpha": f"{PROJ}/tileableheartsalpha.tileableheartsalpha",
    "soil_albedo": f"{PROJ}/Textures/SOIL_materialized_diffuseOriginal.SOIL_materialized_diffuseOriginal",
    "soil_normal": f"{PROJ}/Textures/SOIL_materialized_normal.SOIL_materialized_normal",
    "landscape_gray_albedo": f"{PROJ}/landscapegrayscale_BaseColor.landscapegrayscale_BaseColor",
    "landscape_gray_normal": (
        f"{PROJ}/Textures/landscapegrayscale/landscapegrayscale_Normal.landscapegrayscale_Normal"
    ),
}


def _proj_tex(folder: str, stem: str) -> str:
    return f"{PROJ}/{folder}/{stem}.{stem}"


PROCEDURAL: dict[str, dict[str, str] | str] = {
    "vein": {"height": _proj_tex("Vein", "Vein_1_-_512x512"), "mask": _proj_tex("Vein", "Vein_5_-_512x512")},
    "swirl": {"mask": _proj_tex("Swirl", "Swirl_1_-_512x512"), "height": _proj_tex("Swirl", "Swirl_3_-_512x512")},
    "gabor": {"mask": _proj_tex("Gabor", "Gabor_1_-_512x512")},
    "grainy": {"height": _proj_tex("Grainy", "Grainy_1_-_512x512")},
    "techno": {"mask": _proj_tex("Techno", "Techno_1_-_512x512")},
    "spokes_radial": f"{PROJ}/Spokes/512x512/Texture_512x512_1.Texture_512x512_1",
}

# Fallback chains (first existing wins in editor)
def _chain(*paths: str) -> list[str]:
    return list(paths)


# Normal fallbacks — marble albedo packs as tangent-ish placeholders (not Perlin noise)
def _normal_chain() -> list[str]:
    return _chain(COMPOSITING["abstract_a"], COMPOSITING["gradient_warm"], MARBLE["light"], MARBLE["warm_stone"])


# Param role hints for MI editor grouping (see organize_*_groups.py)
TEXTURE_ROLE_HINTS: dict[str, str] = {
    "Albedo": "RGB albedo — swap any _D / colour texture",
    "LayerB_Albedo": "RGB overlay albedo",
    "LayerC_Albedo": "RGB second overlay albedo",
    "NormalMap": "Tangent-space normal (RGB)",
    "LayerB_NormalMap": "Tangent-space overlay normal",
    "LayerC_NormalMap": "Tangent-space second overlay normal",
    "ORM": "Packed ORM — R=AO, G=Roughness, B=Metallic",
    "LayerB_ORM": "Packed overlay ORM",
    "LayerC_ORM": "Packed second overlay ORM",
    "HeightMap": "Single-channel height — white=raised",
    "LayerB_HeightMap": "Overlay height map",
    "LayerC_HeightMap": "Second overlay height map",
    "RoughnessMap": "Optional standalone roughness map (R channel)",
    "LayerB_RoughnessMap": "Optional standalone overlay roughness map (R channel)",
    "LayerC_RoughnessMap": "Optional standalone second overlay roughness map (R channel)",
    "MetallicMap": "Optional standalone metallic map (R channel)",
    "LayerB_MetallicMap": "Optional standalone overlay metallic map (R channel)",
    "LayerC_MetallicMap": "Optional standalone second overlay metallic map (R channel)",
    "DetailNormal": "High-frequency detail normal overlay",
    "SparkleMask": "Nikki sparkle alpha mask",
    "StarMap": "Celestial star field alpha",
    "FairyGlyphMask": "Fairy dust motif alpha",
    "MotifMask": "Magical henshin motif alpha",
    "Rock_Albedo": "Landscape rock layer albedo",
    "Grass_Albedo": "Landscape grass layer albedo",
    "Mud_Albedo": "Landscape mud layer albedo",
    "PathMask": "Landscape path wear mask",
}


LANDSCAPE_TEXTURE_DEFAULTS: dict[str, list[str]] = {
    "Rock_Albedo": _chain(COMPOSITING["gradient_warm"], COMPOSITING["abstract_a"], MARBLE["warm_stone"]),
    "Rock_Normal": _normal_chain(),
    "Rock_Height": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
    "Grass_Albedo": _chain(CUSTOM["soil_albedo"], CUSTOM["landscape_gray_albedo"], COMPOSITING["abstract_a"]),
    "Grass_Normal": _chain(CUSTOM["soil_normal"], CUSTOM["landscape_gray_normal"], *_normal_chain()),
    "Grass_Height": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
    "Mud_Albedo": _chain(COMPOSITING["crack_heavy"], COMPOSITING["abstract_a"]),
    "Mud_Normal": _normal_chain(),
    "Mud_Height": _chain(
        PROCEDURAL["vein"]["height"] if isinstance(PROCEDURAL.get("vein"), dict) else COMPOSITING["crack_overlay"],
        COMPOSITING["crack_overlay"],
        HEIGHT["perlin"],
    ),
    "Path_Albedo": _chain(MARBLE["worn"], COMPOSITING["gradient_warm"]),
    "Path_Normal": _normal_chain(),
    "Path_Height": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
    "PathMask": _chain(MASK["voronoi_crack"], COMPOSITING["crack_overlay"]),
    "SparkleMask": _chain(
        "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
        "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
        COMPOSITING["noise_fine"],
    ),
    "ShadowFlowerMask": _chain(
        "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
        JAPANESE_ORNAMENT["zen_circle"],
    ),
}


MASTER_TEXTURE_DEFAULTS: dict[str, list[str]] = {
    "Albedo": _chain(
        COMPOSITING["abstract_a"],
        COMPOSITING["gradient_warm"],
        MARBLE["warm_stone"],
        MARBLE["light"],
    ),
    "NormalMap": _normal_chain(),
    "ORM": _chain(COMPOSITING["gradient_warm"], COMPOSITING["abstract_a"]),
    "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"], HEIGHT["perlin_sdf"]),
    "RoughnessMap": _chain(MARBLE["worn"], MARBLE["dark"], COMPOSITING["abstract_a"]),
    "MetallicMap": _chain(COMPOSITING["gradient_warm"], COMPOSITING["abstract_a"], MARBLE["dark"]),
    "LayerB_Albedo": _chain(COMPOSITING["crack_overlay"], MASK["voronoi_crack"]),
    "LayerB_NormalMap": _normal_chain(),
    "LayerB_ORM": _chain(COMPOSITING["abstract_a"], COMPOSITING["gradient_warm"]),
    "LayerB_HeightMap": _chain(COMPOSITING["crack_heavy"], HEIGHT["perlin"], MASK["voronoi_crack"]),
    "LayerB_RoughnessMap": _chain(COMPOSITING["crack_overlay"], MARBLE["worn"], COMPOSITING["abstract_a"]),
    "LayerB_MetallicMap": _chain(COMPOSITING["gradient_warm"], COMPOSITING["abstract_a"], MARBLE["dark"]),
    "LayerC_Albedo": _chain(MARBLE["light"], COMPOSITING["abstract_a"], COMPOSITING["gradient_warm"]),
    "LayerC_NormalMap": _normal_chain(),
    "LayerC_ORM": _chain(COMPOSITING["abstract_a"], COMPOSITING["gradient_warm"]),
    "LayerC_HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"], MASK["voronoi_crack"]),
    "LayerC_RoughnessMap": _chain(MARBLE["worn"], COMPOSITING["abstract_a"], COMPOSITING["noise_fine"]),
    "LayerC_MetallicMap": _chain(COMPOSITING["gradient_warm"], COMPOSITING["abstract_a"], MARBLE["dark"]),
    "DetailNormal": _chain(MARBLE["light"], MARBLE["worn"], COMPOSITING["noise_fine"]),
    "SparkleMask": _chain(
        "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
        "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
        COMPOSITING["noise_fine"],
    ),
    "FairyGlyphMask": _chain(
        JAPANESE_ORNAMENT["zen_minimal"],
        JAPANESE_ORNAMENT["baroque_filigree"],
        "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
        "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
        MASK["voronoi_swirl"],
        COMPOSITING["abstract_a"],
    ),
    "MotifMask": _chain(
        JAPANESE_ORNAMENT["baroque_rosette"],
        JAPANESE_ORNAMENT["baroque_cathedral"],
        JAPANESE_ORNAMENT["zen_wave"],
        "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
        "/Game/Magical/T_Magic_Bow.T_Magic_Bow",
        COMPOSITING["abstract_a"],
    ),
    "StarMap": _chain(
        "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
        "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
        COMPOSITING["noise_fine"],
        COMPOSITING["space_nebula"],
    ),
}

# M_Master_Toon_Unified / M_Master_SDF_Toon (TextureSampleParameter2D, no Albedo slot)
UNIFIED_SDF_TEXTURE_DEFAULTS: dict[str, list[str]] = {
    "NormalMap": _normal_chain(),
    "RoughnessMap": _chain(MARBLE["worn"], MARBLE["dark"], COMPOSITING["abstract_a"]),
    "HeightMap": _chain(HEIGHT["perlin"], HEIGHT["perlin_sdf"], COMPOSITING["crack_overlay"]),
}

INSTANCE_TEXTURE_DEFAULTS: dict[str, dict[str, list[str]]] = {
    "MI_Universal_Default": {
        "Albedo": _chain(MARBLE["warm_stone"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
    },
    "MI_Universal_LayeredStone": {
        "Albedo": _chain(MARBLE["warm_stone"]),
        "LayerB_Albedo": _chain(MASK["voronoi_crack"], COMPOSITING["crack_overlay"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
        "LayerB_HeightMap": _chain(COMPOSITING["crack_heavy"]),
    },
    "MI_Universal_CrackedClay": {
        "Albedo": _chain(MARBLE["worn"]),
        "LayerB_Albedo": _chain(COMPOSITING["crack_heavy"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
    },
    "MI_Universal_WetStone": {
        "Albedo": _chain(MARBLE["cool_stone"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
    },
    "MI_Universal_MossStone": {
        "Albedo": _chain(MARBLE["dark"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
    },
    "MI_Universal_SnowDusted": {
        "Albedo": _chain(MARBLE["light"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
    },
    "MI_Universal_DeepSpace": {
        "Albedo": _chain(COMPOSITING["space_nebula"], MARBLE["dark"]),
    },
    "MI_Universal_CelestialNebula": {
        "Albedo": _chain(COMPOSITING["space_nebula"]),
        "SparkleMask": _chain(f"/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8"),
    },
    # Starter showcase set (Instances/Showcase) — see starter_instances.py
    "MI_Show_Default": {
        "Albedo": _chain(MARBLE["warm_stone"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
        "NormalMap": _normal_chain(),
    },
    "MI_Show_StoneCliff": {
        "Albedo": _chain(MARBLE["warm_stone"]),
        "HeightMap": _chain(HEIGHT["perlin"], HEIGHT["perlin_sdf"]),
        "DetailNormal": _chain(COMPOSITING["noise_fine"]),
    },
    "MI_Show_CherryBlossom": {
        "Albedo": _chain(MARBLE["light"], COMPOSITING["gradient_warm"]),
        "SparkleMask": _chain(
            "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
            "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
        ),
        "FairyGlyphMask": _chain(
            "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
            "/Game/Sakura/T_Sakura_Blossom.T_Sakura_Blossom",
        ),
        "HeightMap": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
    },
    "MI_Show_CelestialNebula": {
        "Albedo": _chain(CUSTOM["starry_albedo"], COMPOSITING["space_nebula"]),
        "NormalMap": _chain(CUSTOM["starry_normal"], *_normal_chain()),
        "HeightMap": _chain(CUSTOM["starry_height"], HEIGHT["perlin"], COMPOSITING["noise_fine"]),
        "StarMap": _chain(
            "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
            "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
            COMPOSITING["noise_fine"],
        ),
        "SparkleMask": _chain(
            "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
            COMPOSITING["noise_fine"],
        ),
        "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
    },
    "MI_Show_FairyHearts": {
        "Albedo": _chain(MARBLE["light"], COMPOSITING["abstract_a"]),
        "SparkleMask": _chain(
            "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
            "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
        ),
        "FairyGlyphMask": _chain(
            CUSTOM["hearts_alpha"],
            "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
            "/Game/_PROJECT/04_Materials/Textures/tileableheartsalpha.tileableheartsalpha",
        ),
        "MotifMask": _chain(
            "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
            COMPOSITING["abstract_a"],
        ),
        "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
    },
    "MI_Show_SkinSoft": {
        "Albedo": _chain(MARBLE["light"], COMPOSITING["gradient_warm"]),
        "HeightMap": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
    },
    "MI_Show_ForestFoliage": {
        "Albedo": _chain(MARBLE["dark"], MARBLE["cool_stone"]),
        "HeightMap": _chain(MASK["voronoi_swirl"], HEIGHT["perlin"]),
        "LayerB_Albedo": _chain(COMPOSITING["abstract_a"], MASK["voronoi_swirl"]),
    },
    "MI_Show_ContactRimHero": {
        "Albedo": _chain(MARBLE["cool_stone"], MARBLE["warm_stone"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
    },
    "MI_Show_ElementHydro": {
        "Albedo": _chain(MARBLE["cool_stone"], COMPOSITING["abstract_a"]),
        "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
    },
    "MI_Show_InkWash": {
        "Albedo": _chain(MARBLE["light"], COMPOSITING["abstract_a"]),
        "MotifMask": _chain(
            "/Game/Magical/T_Magic_Bow.T_Magic_Bow",
            COMPOSITING["abstract_a"],
        ),
        "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
    },
    # Theme families — Baroque + Zen (see theme_instances.py)
    "MI_Baroque_GildedFiligree": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["baroque_filigree"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["baroque_scroll"]),
        "Albedo": _chain(MARBLE["warm_stone"], MARBLE["worn"]),
    },
    "MI_Baroque_CathedralSurreal": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["baroque_rosette"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["baroque_cathedral"]),
    },
    "MI_Baroque_EscherOrnament": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["baroque_lattice"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["baroque_mandala"]),
    },
    "MI_Baroque_FiligreeDream": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["baroque_cathedral"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["baroque_filigree"]),
    },
    "MI_Zen_MossGarden": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["zen_minimal"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["zen_circle"]),
        "Albedo": _chain(MARBLE["dark"], MARBLE["cool_stone"]),
    },
    "MI_Zen_InkWash": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["zen_wave"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["zen_wave"]),
        "Albedo": _chain(MARBLE["light"]),
    },
    "MI_Zen_BambooMist": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["zen_bamboo"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["zen_bamboo"]),
    },
    "MI_Zen_Karesansui": {
        "MotifMask": _chain(JAPANESE_ORNAMENT["zen_sand"]),
        "FairyGlyphMask": _chain(JAPANESE_ORNAMENT["zen_stone"]),
    },
    "MI_Trimsheet_VariationCracks": {
        "Albedo": _chain(MARBLE["warm_stone"]),
        "LayerB_Albedo": _chain(COMPOSITING["crack_overlay"]),
        "HeightMap": _chain(HEIGHT["perlin"]),
        "LayerB_HeightMap": _chain(COMPOSITING["crack_heavy"]),
    },
}

# Any instance with TextureWeight / layer weights but no explicit textures gets base pack
INSTANCE_FALLBACK_TEXTURES: dict[str, list[str]] = {
    "Albedo": MASTER_TEXTURE_DEFAULTS["Albedo"],
    "HeightMap": MASTER_TEXTURE_DEFAULTS["HeightMap"],
    "NormalMap": MASTER_TEXTURE_DEFAULTS["NormalMap"],
    "LayerB_Albedo": MASTER_TEXTURE_DEFAULTS["LayerB_Albedo"],
    "LayerB_HeightMap": MASTER_TEXTURE_DEFAULTS["LayerB_HeightMap"],
    "DetailNormal": MASTER_TEXTURE_DEFAULTS["DetailNormal"],
    "SparkleMask": MASTER_TEXTURE_DEFAULTS["SparkleMask"],
}

# Keyword rules: first match wins (order matters)
INSTANCE_TEXTURE_RULES: list[tuple[tuple[str, ...], dict[str, list[str]]]] = [
    (
        ("deepspace", "nebula", "constellation", "celestial", "galaxy", "cosmic", "starfield"),
        {
            "Albedo": _chain(CUSTOM["starry_albedo"], COMPOSITING["space_nebula"], MARBLE["dark"]),
            "NormalMap": _chain(CUSTOM["starry_normal"], *_normal_chain()),
            "HeightMap": _chain(CUSTOM["starry_height"], HEIGHT["perlin"], COMPOSITING["noise_fine"]),
            "StarMap": _chain(
                "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
                "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
                COMPOSITING["noise_fine"],
            ),
        },
    ),
    (
        ("ember", "volcanic", "ash", "lava"),
        {
            "Albedo": _chain(MARBLE["dark"], MARBLE["worn"]),
            "HeightMap": _chain(MASK["voronoi_crack"], HEIGHT["perlin"]),
            "LayerB_Albedo": _chain(COMPOSITING["crack_heavy"]),
        },
    ),
    (
        ("crack", "clay", "trim", "variationcracks", "weathered", "worn"),
        {
            "Albedo": _chain(MARBLE["worn"], MARBLE["warm_stone"]),
            "LayerB_Albedo": _chain(COMPOSITING["crack_heavy"], COMPOSITING["crack_overlay"]),
            "LayerB_HeightMap": _chain(COMPOSITING["crack_heavy"], MASK["voronoi_crack"]),
            "HeightMap": _chain(HEIGHT["perlin"], MASK["voronoi_crack"]),
        },
    ),
    (
        ("snow", "ice", "frost", "crust"),
        {
            "Albedo": _chain(MARBLE["light"], COMPOSITING["gradient_warm"]),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
            "SparkleMask": _chain(
                f"{TEX}/sbs_-_noise_texture_pack_-_512x512/512x512/Perlin/Perlin_10_-_512x512.Perlin_10_-_512x512"
            ),
        },
    ),
    (
        ("moss", "garden", "foliage", "grass", "fern"),
        {
            "Albedo": _chain(MARBLE["dark"], MARBLE["cool_stone"]),
            "HeightMap": _chain(HEIGHT["perlin"], MASK["voronoi_swirl"]),
        },
    ),
    (
        ("gold", "gild", "filigree", "ornament", "baroque"),
        {
            "Albedo": _chain(MARBLE["warm_stone"], MARBLE["worn"]),
            "HeightMap": _chain(MASK["voronoi_crack"], HEIGHT["perlin"]),
            "LayerB_Albedo": _chain(MASK["voronoi_swirl"], COMPOSITING["crack_overlay"]),
            "MotifMask": _chain(
                PROCEDURAL["spokes_radial"] if isinstance(PROCEDURAL["spokes_radial"], str) else COMPOSITING["abstract_a"],
                JAPANESE_ORNAMENT["baroque_filigree"],
                JAPANESE_ORNAMENT["baroque_cathedral"],
                JAPANESE_ORNAMENT["baroque_rosette"],
            ),
            "FairyGlyphMask": _chain(
                JAPANESE_ORNAMENT["baroque_mandala"],
                JAPANESE_ORNAMENT["baroque_scroll"],
            ),
        },
    ),
    (
        ("wood", "timber", "bark", "cedar", "teahouse"),
        {
            "Albedo": _chain(CUSTOM["wood_albedo"], MARBLE["worn"], MARBLE["warm_stone"]),
            "NormalMap": _chain(CUSTOM["wood_normal"], *_normal_chain()),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
        },
    ),
    (
        ("ancientruin", "ruin", "cathedral", "hybrid"),
        {
            "Albedo": _chain(MARBLE["cool_stone"], MARBLE["worn"]),
            "LayerB_Albedo": _chain(COMPOSITING["crack_overlay"], MASK["voronoi_crack"]),
            "HeightMap": _chain(HEIGHT["perlin_sdf"], HEIGHT["perlin"]),
        },
    ),
    (
        ("forest", "mossy", "fern", "canopy"),
        {
            "Albedo": _chain(MARBLE["dark"], COMPOSITING["abstract_a"]),
            "HeightMap": _chain(MASK["voronoi_swirl"], HEIGHT["perlin"]),
        },
    ),
    (
        ("frost", "sakura"),
        {
            "Albedo": _chain(MARBLE["light"], COMPOSITING["gradient_warm"]),
            "HeightMap": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
        },
    ),
    (
        ("ocean", "foam", "wet", "cobble", "rain", "storm"),
        {
            "Albedo": _chain(MARBLE["cool_stone"], MARBLE["dark"]),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
            "DetailNormal": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
        },
    ),
    (
        ("desert", "sand", "dune"),
        {
            "Albedo": _chain(MARBLE["light"], COMPOSITING["gradient_warm"]),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
        },
    ),
    (
        ("stone", "rock", "masonry", "layered", "brick"),
        {
            "Albedo": _chain(MARBLE["warm_stone"], MARBLE["cool_stone"]),
            "LayerB_Albedo": _chain(MASK["voronoi_crack"], COMPOSITING["crack_overlay"]),
            "HeightMap": _chain(HEIGHT["perlin"], HEIGHT["perlin_sdf"]),
        },
    ),
    (
        ("crystal", "glass", "prism", "irid", "opal"),
        {
            "Albedo": _chain(COMPOSITING["abstract_a"], MARBLE["cool_stone"]),
            "HeightMap": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
        },
    ),
    (
        ("cherry", "blossom", "sakura", "petal", "shadowflower"),
        {
            "Albedo": _chain(MARBLE["light"], COMPOSITING["gradient_warm"]),
            "SparkleMask": _chain(
                "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
                "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
            ),
            "FairyGlyphMask": _chain(
                "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
                "/Game/Sakura/T_Sakura_Blossom.T_Sakura_Blossom",
            ),
            "HeightMap": _chain(COMPOSITING["noise_fine"], HEIGHT["perlin"]),
        },
    ),
    (
        ("fairy", "dream", "blush", "lavender", "peach", "cotton", "pastel", "satin", "magical"),
        {
            "Albedo": _chain(COMPOSITING["abstract_a"], MARBLE["light"]),
            "SparkleMask": _chain(
                "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
                "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
            ),
            "FairyGlyphMask": _chain(
                "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
                "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
            ),
            "MotifMask": _chain(
                "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
                COMPOSITING["abstract_a"],
            ),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
        },
    ),
    (
        ("zen", "karesansui", "torii", "bamboo", "mossgarden", "roji", "inkwash"),
        {
            "Albedo": _chain(MARBLE["cool_stone"], MARBLE["dark"]),
            "NormalMap": _chain(CUSTOM["bss_sand_normal"], *_normal_chain()),
            "DetailNormal": _chain(CUSTOM["bss_sand_normal"], COMPOSITING["noise_fine"]),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
            "MotifMask": _chain(
                JAPANESE_ORNAMENT["zen_minimal"],
                JAPANESE_ORNAMENT["zen_stone"],
                JAPANESE_ORNAMENT["zen_sand"],
            ),
            "FairyGlyphMask": _chain(
                JAPANESE_ORNAMENT["zen_circle"],
                JAPANESE_ORNAMENT["zen_wave"],
                JAPANESE_ORNAMENT["zen_bamboo"],
            ),
        },
    ),
    (
        ("ink", "temporal", "impression", "wind", "smear"),
        {
            "Albedo": _chain(MARBLE["light"], COMPOSITING["abstract_a"]),
            "HeightMap": _chain(HEIGHT["perlin"], COMPOSITING["noise_fine"]),
        },
    ),
]


def scan_disk_catalog() -> dict:
    tex_root = CONTENT / "Textures"
    sdf_root = CONTENT / "EnvSandbox" / "Materials" / "SDF" / "Textures"
    packs: dict[str, int] = {}
    if tex_root.exists():
        for p in tex_root.rglob("*.uasset"):
            rel = p.relative_to(tex_root)
            key = rel.parts[0] if len(rel.parts) > 1 else "(root)"
            packs[key] = packs.get(key, 0) + 1
    sdf_count = len(list(sdf_root.rglob("*.uasset"))) if sdf_root.exists() else 0
    return {
        "textures_pack_counts": packs,
        "textures_total": sum(packs.values()),
        "sdf_textures_total": sdf_count,
        "roles": {
            "marble": MARBLE,
            "height": HEIGHT,
            "mask": MASK,
            "compositing": COMPOSITING,
        },
    }


def _param_name(expr) -> str | None:
    for prop in ("parameter_name", "ParameterName"):
        try:
            raw = expr.get_editor_property(prop)
            if raw is not None:
                return str(raw)
        except Exception:
            continue
    return None


def _master_default_map(material_path: str) -> dict[str, list[str]]:
    stem = material_path.rsplit("/", 1)[-1].lower()
    if "landscape_heightblend" in stem or "landscape" in stem and "height" in stem:
        return LANDSCAPE_TEXTURE_DEFAULTS
    if "universal" in stem:
        return MASTER_TEXTURE_DEFAULTS
    if stem in ("m_master_toon_unified", "m_master_sdf_toon"):
        return UNIFIED_SDF_TEXTURE_DEFAULTS
    return {**MASTER_TEXTURE_DEFAULTS, **UNIFIED_SDF_TEXTURE_DEFAULTS}


def resolve_instance_texture_map(instance_name: str) -> dict[str, list[str]]:
    """Merge explicit preset, keyword rules, inventory-verified chains, and fallbacks."""
    merged: dict[str, list[str]] = {}
    for pname, candidates in INSTANCE_FALLBACK_TEXTURES.items():
        merged[pname] = list(candidates)
    key = instance_name.lower().replace("mi_universal_", "").replace("mi_", "")
    for keywords, spec in INSTANCE_TEXTURE_RULES:
        if any(kw in key for kw in keywords):
            for pname, candidates in spec.items():
                merged[pname] = list(candidates)
            break
    explicit = INSTANCE_TEXTURE_DEFAULTS.get(instance_name, {})
    for pname, candidates in explicit.items():
        merged[pname] = list(candidates)
    try:
        import inventory_project_textures as inv

        chains = inv.load_inventory().get("verified_chains") or {}
        role_map = {
            "Albedo": "albedo",
            "LayerB_Albedo": "albedo",
            "NormalMap": "normal",
            "LayerB_NormalMap": "normal",
            "SparkleMask": "sparkle_mask",
            "StarMap": "sparkle_mask",
        }
        for pname, chain_key in role_map.items():
            extra = chains.get(chain_key) or []
            if extra and pname in merged:
                merged[pname] = list(dict.fromkeys(extra + merged[pname]))
    except Exception:
        pass
    return merged


def scan_master_texture_violations(material) -> dict[str, list[str]]:
    """Return banned (/Engine/) and unwired texture param names on a master."""
    import material_lib as lib

    banned: list[str] = []
    unwired: list[str] = []
    wrong_role: list[str] = []
    height_noise_markers = ("Perlin", "Cracks", "Voronoi", "noise_texture_pack")

    for expr, _owner in lib.iter_texture_parameter_expressions(material):
        pname = _param_name(expr)
        if not pname:
            continue
        tex = None
        for prop in ("texture", "Texture"):
            try:
                tex = expr.get_editor_property(prop)
                if tex:
                    break
            except Exception:
                continue
        if not tex or lib.is_placeholder_texture(tex):
            unwired.append(pname)
            continue
        path = lib.texture_asset_path(tex) or ""
        if lib.is_banned_texture(tex):
            banned.append(pname)
        if pname in ("ORM", "LayerB_ORM", "RoughnessMap") and any(m in path for m in height_noise_markers):
            wrong_role.append(pname)

    return {"banned": banned, "unwired": unwired, "wrong_role": wrong_role}


def apply_master_defaults(
    material, material_path: str | None = None, *, force: bool = False
) -> dict[str, str]:
    """Set default textures on master parameter nodes from /Game/Textures compositing catalog."""
    import unreal
    import material_lib as lib

    if material_path is None:
        try:
            material_path = str(material.get_path_name().split(".", 1)[0])
        except Exception:
            material_path = ""
    defaults = _master_default_map(material_path)
    wired: dict[str, str] = {}
    param_exprs: dict[str, object] = {}
    expr_owners: dict[str, object] = {}
    for expr, owner in lib.iter_texture_parameter_expressions(material):
        pname = _param_name(expr)
        if pname and pname not in param_exprs:
            param_exprs[pname] = expr
            expr_owners[pname] = owner

    texture_params = lib.texture_parameter_names(material)
    if not param_exprs and texture_params:
        unreal.log_warning(
            f"[texture_catalog] master {material_path}: params {texture_params[:12]} "
            "found via MaterialEditingLibrary but no graph nodes located"
        )

    modified_owners: set[object] = set()
    for pname, candidates in defaults.items():
        expr = param_exprs.get(pname)
        if not expr:
            continue
        current = None
        me = unreal.MaterialEditingLibrary
        if hasattr(me, "get_material_default_texture_parameter_value"):
            try:
                current = me.get_material_default_texture_parameter_value(material, pname)
            except Exception:
                current = None
        if not force and current and not lib.is_banned_texture(current):
            wired[pname] = lib.texture_asset_path(current) or ""
            continue
        candidates = lib.sanitize_candidates(candidates)
        if not candidates:
            unreal.log_warning(f"[texture_catalog] no valid candidates for master {pname}")
            continue
        path = lib.set_expression_texture(expr, candidates)
        if path:
            wired[pname] = path
            owner = expr_owners.get(pname)
            if owner:
                modified_owners.add(owner)
        else:
            unreal.log_warning(f"[texture_catalog] no asset for master {pname} on {material_path}")

    for owner in modified_owners:
        lib.save_package(owner)
    if not wired and texture_params:
        unmatched = [p for p in texture_params if p in defaults]
        if unmatched:
            unreal.log_warning(
                f"[texture_catalog] master {material_path}: {len(texture_params)} texture params "
                f"{texture_params[:12]} — wired 0, unmatched defaults for {unmatched[:8]}"
            )
        else:
            unreal.log_warning(
                f"[texture_catalog] master {material_path}: {len(texture_params)} texture params "
                f"{texture_params[:12]} — wired 0 (param names not in catalog defaults)"
            )
    if wired:
        try:
            unreal.MaterialEditingLibrary.recompile_material(material)
        except Exception:
            pass
    return wired


def apply_instance_texture_defaults(instance, instance_name: str, existing: dict | None = None) -> dict[str, str]:
    """Fill instance texture params from catalog rules + fallbacks."""
    import unreal
    import material_lib as lib

    existing = dict(existing or {})
    spec = resolve_instance_texture_map(instance_name)
    wired: dict[str, str] = {}
    stale_markers = ("/Texture_512x512",)
    for pname, candidates in spec.items():
        if pname in existing:
            continue
        skip = False
        try:
            current = instance.get_texture_parameter_value(pname)
            if current:
                cur_path = lib.texture_asset_path(current) or ""
                pkg = cur_path.split(".", 1)[0]
                is_stale = pkg.endswith("/Texture_512x512")
                if cur_path and not is_stale:
                    if unreal.EditorAssetLibrary.does_asset_exist(cur_path) or unreal.EditorAssetLibrary.does_asset_exist(pkg):
                        skip = True
        except Exception:
            pass
        if skip:
            continue
        path = lib.set_instance_texture(instance, pname, candidates)
        if path:
            wired[pname] = path
    return wired


def refresh_starter_instance_textures(
    showcase_dir: str = "/Game/EnvSandbox/Materials/Instances/Showcase",
) -> dict[str, dict]:
    """Apply compositing defaults to curated MI_Show_* starters only."""
    import unreal
    import material_lib as lib

    try:
        from starter_instances import STARTER_NAMES
    except ImportError:
        STARTER_NAMES = frozenset(k for k in INSTANCE_TEXTURE_DEFAULTS if k.startswith("MI_Show_"))

    results: dict[str, dict] = {}
    if not unreal.EditorAssetLibrary.does_directory_exist(showcase_dir):
        return results
    for asset_path in unreal.EditorAssetLibrary.list_assets(showcase_dir, recursive=False, include_folder=False):
        base = asset_path.split(".", 1)[0]
        stem = base.rsplit("/", 1)[-1]
        if stem not in STARTER_NAMES:
            continue
        inst = unreal.load_asset(f"{base}.{stem}")
        if not inst:
            continue
        wired = apply_instance_texture_defaults(inst, stem, {})
        if wired:
            lib.save_package(inst)
        results[base] = wired
    return results


def refresh_all_instance_textures(
    instances_root: str = "/Game/EnvSandbox/Materials/Instances",
    *,
    subfolders: tuple[str, ...] = ("Showcase", "Environment", "Landscape"),
) -> dict[str, dict]:
    """Walk portfolio MI folders and apply compositing texture defaults.

    Prefer refresh_starter_instance_textures() for day-to-day pipeline work.
    Skips Water/ and other legacy folders that may contain corrupt packages.
    """
    import unreal
    import material_lib as lib

    skip_stems = frozenset({"M_Water_Master_Grand_v6"})
    results: dict[str, dict] = {}
    roots = [instances_root]
    if subfolders:
        roots = [f"{instances_root.rstrip('/')}/{sf}" for sf in subfolders]
    for root in roots:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            continue
        for asset_path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            if not asset_path.startswith("/Game/") or "/MI_" not in asset_path:
                continue
            base = asset_path.split(".", 1)[0]
            stem = base.rsplit("/", 1)[-1]
            if not stem.startswith("MI_") or stem in skip_stems:
                continue
            try:
                inst = unreal.load_asset(f"{base}.{stem}")
            except Exception:
                continue
            if not inst:
                continue
            wired = apply_instance_texture_defaults(inst, stem, {})
            if wired:
                lib.save_package(inst)
            results[base] = wired
    return results


def main() -> int:
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **scan_disk_catalog(),
        "master_defaults": {k: v for k, v in MASTER_TEXTURE_DEFAULTS.items()},
        "instance_presets": list(INSTANCE_TEXTURE_DEFAULTS.keys()),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "textures_total": report["textures_total"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
