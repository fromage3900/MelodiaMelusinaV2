"""Alpha / mask texture catalog for storybook PP + universal master wiring.

Sources (read-only reference): _AssetLibrary, Content/_PROJECT, Content/Stylization,
Content/Alphas_Sparkles, EnvSandbox/SDF procedural textures.

Run ensure_alpha_imports() in-editor before wiring Magical/Sakura paths that are PNG-only.
"""
from __future__ import annotations

from pathlib import Path

import unreal

ASSET_LIBRARY = Path(r"G:\EnvironmentPortfolio\_AssetLibrary")
PROJECT_CONTENT = Path(__file__).resolve().parents[1]

# --- Vine / branch / ink (storybook PP VineBranchMask) ---
VINE_BRANCH_MASK = [
    "/Game/Stylization/T_Flow_Swirl.T_Flow_Swirl",
    "/Game/Stylization/T_Hatch_Diagonal.T_Hatch_Diagonal",
    "/Game/EnvSandbox/Materials/SDF/Textures/Voronoi/Voronoi_11_-_512x512.Voronoi_11_-_512x512",
    "/Game/EnvSandbox/Materials/SDF/Textures/Voronoi/Voronoi_2_-_512x512.Voronoi_2_-_512x512",
]

# --- Sparkles (SparkleMask on M_Master_Toon_Universal) ---
SPARKLE_MASKS = {
    "twinkle": "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
    "sparkle4": "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
    "glow": [
        "/Game/Alphas_Sparkles/T_Spark_Glow.T_Spark_Glow",
        "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
    ],
    "dot": "/Game/Alphas_Sparkles/T_Spark_Dot.T_Spark_Dot",
    "bokeh": "/Game/Alphas_Sparkles/T_Spark_Bokeh.T_Spark_Bokeh",
}

# --- Japanese ornament alphas (70_Japanese_Ornament_Alphas_vfxMed) ---
JRO_JP = "/Game/Textures/70_Japanese_Ornament_Alphas_vfxMed/70_Japanese_Ornament_Alphas/JRO_JP"


def _jro_mask(stem: str) -> str:
    base = f"{stem}_Mask" if not stem.endswith("_Mask") else stem
    return f"{JRO_JP}/{base}.{base}"


JAPANESE_ORNAMENT_MASKS = {
    "zen01": [_jro_mask("JRO_JP_Ornament01_out")],
    "zen02": [_jro_mask("JRO_JP_Ornament02_out")],
    "zen03": [_jro_mask("JRO_JP_Ornament03_out")],
    "zen05": [_jro_mask("JRO_JP_Ornament05_out")],
    "zen07": [_jro_mask("JRO_JP_Ornament07_out")],
    "zen10": [_jro_mask("JRO_JP_Ornament10_out")],
    "zen15": [_jro_mask("JRO_JP_Ornament15_out")],
    "zen18": [_jro_mask("JRO_JP_Ornament18_out")],
    "zen23": [_jro_mask("JRO_JP_Ornament23_out")],
    "zen28": [_jro_mask("JRO_JP_Ornament28_out")],
    "zen30": [_jro_mask("JRO_JP_Ornament30_out")],
    "zen35": [_jro_mask("JRO_JP_Ornament35_out")],
    "baroque04": [_jro_mask("JRO_JP_Ornament04_out")],
    "baroque08": [_jro_mask("JRO_JP_Ornament08_1_out")],
    "baroque12": [_jro_mask("JRO_JP_Ornament12_out")],
    "baroque19": [_jro_mask("JRO_JP_Ornament19_2_out")],
    "baroque22": [_jro_mask("JRO_JP_Ornament22_1_out")],
    "baroque41": [_jro_mask("JRO_JP_Ornament41_3_out")],
}

FAIRY_GLYPH_MASKS = {
    "heart": [
        "/Game/Magical/T_Magic_Heart.T_Magic_Heart",
        "/Game/_PROJECT/04_Materials/Textures/tileableheartsalpha.tileableheartsalpha",
    ],
    "star": [
        "/Game/Magical/T_Magic_Star.T_Magic_Star",
        "/Game/Alphas_Sparkles/T_Spark_Sparkle4.T_Spark_Sparkle4",
    ],
    "flower": [
        "/Game/Sakura/T_Sakura_Petal.T_Sakura_Petal",
        "/Game/Sakura/T_Sakura_Blossom.T_Sakura_Blossom",
    ],
    "moon": [
        "/Game/Alphas_Sparkles/T_Spark_Glow.T_Spark_Glow",
        "/Game/Alphas_Sparkles/T_Spark_Twinkle8.T_Spark_Twinkle8",
    ],
    "bow": [
        "/Game/Magical/T_Magic_Bow.T_Magic_Bow",
    ],
    "jro_zen": JAPANESE_ORNAMENT_MASKS["zen01"],
    "jro_baroque": JAPANESE_ORNAMENT_MASKS["baroque04"],
}

MOTIF_MASKS = {
    "heart": FAIRY_GLYPH_MASKS["heart"],
    "star": FAIRY_GLYPH_MASKS["star"],
    "bow": FAIRY_GLYPH_MASKS["bow"],
    "jro_zen": JAPANESE_ORNAMENT_MASKS["zen07"],
    "jro_baroque": JAPANESE_ORNAMENT_MASKS["baroque12"],
}

# PNGs under _AssetLibrary to import into /Game when uasset is missing.
IMPORT_FROM_LIBRARY: list[tuple[str, str]] = [
    ("Magical/T_Magic_Heart.png", "/Game/Magical"),
    ("Magical/T_Magic_Star.png", "/Game/Magical"),
    ("Magical/T_Magic_Bow.png", "/Game/Magical"),
    ("Sakura/T_Sakura_Petal.png", "/Game/Sakura"),
    ("Sakura/T_Sakura_Blossom.png", "/Game/Sakura"),
]

# Instance presets -> texture parameter wiring (setup_universal_instances.py, apply_starter_instances.py)
INSTANCE_TEXTURE_WIRES: dict[str, dict[str, list[str] | str]] = {
    # --- Starter showcase (canonical) ---
    "MI_Show_CherryBlossom": {
        "SparkleMask": SPARKLE_MASKS["twinkle"],
        "FairyGlyphMask": FAIRY_GLYPH_MASKS["flower"],
    },
    "MI_Show_CelestialNebula": {
        "StarMap": SPARKLE_MASKS["twinkle"],
        "SparkleMask": SPARKLE_MASKS["twinkle"],
    },
    "MI_Show_FairyHearts": {
        "FairyGlyphMask": FAIRY_GLYPH_MASKS["heart"],
        "MotifMask": MOTIF_MASKS["heart"],
        "SparkleMask": SPARKLE_MASKS["sparkle4"],
    },
    "MI_Show_InkWash": {"MotifMask": MOTIF_MASKS["bow"]},
    # --- Legacy MI_Universal_* (deprecated; kept for archived assets) ---
    "MI_Universal_FairyHearts": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["heart"]},
    "MI_Universal_FairyStars": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["star"]},
    "MI_Universal_FairyGarden": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["flower"]},
    "MI_Universal_FairyPetals": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["flower"]},
    "MI_Universal_FairyMoon": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["moon"]},
    "MI_Universal_FairySnowflake": {
        "FairyGlyphMask": FAIRY_GLYPH_MASKS["star"],
        "SparkleMask": SPARKLE_MASKS["twinkle"],
    },
    "MI_Universal_FairyFirefly": {
        "FairyGlyphMask": FAIRY_GLYPH_MASKS["star"],
        "SparkleMask": SPARKLE_MASKS["glow"],
    },
    "MI_Universal_CherryBlossom": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["flower"]},
    "MI_Universal_SakuraPath": {"FairyGlyphMask": FAIRY_GLYPH_MASKS["flower"]},
    "MI_Universal_CottonCandy": {"SparkleMask": SPARKLE_MASKS["bokeh"]},
    "MI_Universal_Starfield": {"SparkleMask": SPARKLE_MASKS["twinkle"]},
    "MI_Universal_DiamondSpark": {"SparkleMask": SPARKLE_MASKS["sparkle4"]},
    "MI_Universal_CometTrail": {"SparkleMask": SPARKLE_MASKS["glow"]},
    "MI_Universal_SnowCrust": {"SparkleMask": SPARKLE_MASKS["twinkle"]},
    "MI_Universal_GlitterGold": {"SparkleMask": SPARKLE_MASKS["sparkle4"]},
    "MI_Universal_HoloFabric": {"SparkleMask": SPARKLE_MASKS["bokeh"]},
    "MI_Universal_OpalSheen": {"SparkleMask": SPARKLE_MASKS["dot"]},
    "MI_Universal_OceanFoam": {"SparkleMask": SPARKLE_MASKS["glow"]},
    "MI_Universal_TemporalInk": {"MotifMask": MOTIF_MASKS["bow"]},
}


def resolve_texture_path(candidates: list[str] | str) -> str | None:
    if isinstance(candidates, str):
        candidates = [candidates]
    for path in candidates:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            return path
    return None


def ensure_alpha_imports() -> list[str]:
    """Import missing Magical/Sakura PNGs from _AssetLibrary into /Game."""
    imported: list[str] = []
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    for rel, dest in IMPORT_FROM_LIBRARY:
        stem = Path(rel).stem
        game_path = f"{dest}/{stem}.{stem}"
        if unreal.EditorAssetLibrary.does_asset_exist(game_path):
            continue
        src = ASSET_LIBRARY / rel.replace("/", "\\")
        if not src.exists():
            unreal.log_warning(f"[AlphaPaths] missing library source: {src}")
            continue
        unreal.EditorAssetLibrary.make_directory(dest)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(src))
        task.set_editor_property("destination_path", dest)
        task.set_editor_property("destination_name", stem)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)
        task.set_editor_property("replace_existing", True)
        tools.import_asset_tasks([task])
        if unreal.EditorAssetLibrary.does_asset_exist(game_path):
            imported.append(game_path)
            unreal.log(f"[AlphaPaths] imported {game_path}")
    return imported


def catalog_summary() -> dict:
    """Return resolved paths for audit reports."""
    return {
        "vine_branch_mask": resolve_texture_path(VINE_BRANCH_MASK),
        "sparkle_twinkle": resolve_texture_path(SPARKLE_MASKS["twinkle"]),
        "fairy_heart": resolve_texture_path(FAIRY_GLYPH_MASKS["heart"]),
        "fairy_star": resolve_texture_path(FAIRY_GLYPH_MASKS["star"]),
        "fairy_flower": resolve_texture_path(FAIRY_GLYPH_MASKS["flower"]),
        "motif_heart": resolve_texture_path(MOTIF_MASKS["heart"]),
    }
