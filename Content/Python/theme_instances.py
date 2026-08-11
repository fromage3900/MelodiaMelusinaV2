"""Surreal baroque + zen themed MI_* for M_Master_Toon_Universal.

Uses Japanese ornament alphas from /Game/Textures/70_Japanese_Ornament_Alphas_vfxMed.
Zen library: see zen_instances.py (apply via apply_zen_instances.py).
"""
from __future__ import annotations

import material_lib as lib
from zen_instances import ZEN_INSTANCES, ZEN_DIR

MASTER = f"{lib.MASTER_DIR}/M_Master_Toon_Universal.M_Master_Toon_Universal"
BAROQUE_DIR = f"{lib.MATERIALS_ROOT}/Instances/Environment/Baroque"

BAROQUE_INSTANCES: list[dict] = [
    {
        "name": "MI_Baroque_GildedFiligree",
        "folder": BAROQUE_DIR,
        "purpose": "Surreal baroque — gilded filigree motif on warm stone",
        "profile": "TP_Default",
        "vectors": {
            "BaseTint": (0.72, 0.58, 0.32, 1.0),
            "GoldTint": (1.0, 0.82, 0.38, 1.0),
            "MotifColor": (0.95, 0.78, 0.28, 1.0),
            "RimColor": (1.0, 0.92, 0.65, 1.0),
        },
        "scalars": {
            "TextureWeight": 0.55,
            "Roughness": 0.42,
            "Metallic": 0.35,
            "GildingStrength": 0.85,
            "OrnamentScale": 4.5,
            "MotifScale": 5.5,
            "ParallaxHeight": 0.12,
            "ParallaxScale": 0.08,
            "RimIntensity": 1.2,
            "RimPower": 3.5,
        },
        "textures": {"MotifMask": "baroque04", "FairyGlyphMask": "baroque08"},
    },
    {
        "name": "MI_Baroque_CathedralSurreal",
        "folder": BAROQUE_DIR,
        "purpose": "Surreal baroque — cathedral rosette with inner glow and parallax",
        "profile": "TP_Default",
        "vectors": {
            "BaseTint": (0.38, 0.34, 0.42, 1.0),
            "InnerGlowColor": (0.55, 0.42, 0.88, 1.0),
            "MotifColor": (0.88, 0.72, 0.95, 1.0),
            "GlowColor": (0.7, 0.55, 1.0, 1.0),
        },
        "scalars": {
            "TextureWeight": 0.4,
            "Roughness": 0.55,
            "InnerGlowIntensity": 0.75,
            "GlowIntensity": 0.45,
            "MotifScale": 7.0,
            "ParallaxHeight": 0.18,
            "ParallaxSteps": 12.0,
            "MagicalTransform": 0.25,
        },
        "textures": {"MotifMask": "baroque12", "FairyGlyphMask": "baroque41"},
    },
    {
        "name": "MI_Baroque_EscherOrnament",
        "folder": BAROQUE_DIR,
        "purpose": "Surreal baroque — impossible lattice ornament + ink temporal wash",
        "profile": "TP_Default",
        "vectors": {
            "BaseTint": (0.52, 0.48, 0.55, 1.0),
            "MotifColor": (0.82, 0.68, 0.92, 1.0),
            "MagicalPalette": (0.65, 0.55, 0.82, 1.0),
        },
        "scalars": {
            "TextureWeight": 0.35,
            "Roughness": 0.48,
            "InkIntensity": 0.55,
            "TemporalStrength": 0.4,
            "MotifScale": 6.5,
            "MagicalTransform": 0.55,
            "TransformGlow": 2.2,
            "OrnamentStyle": 2.0,
        },
        "textures": {"MotifMask": "baroque19", "FairyGlyphMask": "baroque22"},
    },
    {
        "name": "MI_Baroque_FiligreeDream",
        "folder": BAROQUE_DIR,
        "purpose": "Surreal baroque — dreamy filigree with fairy dust and sparkle",
        "profile": "TP_Default",
        "vectors": {
            "BaseTint": (0.88, 0.72, 0.82, 1.0),
            "FairyDustColor": (1.0, 0.92, 0.98, 1.0),
            "MotifColor": (1.0, 0.65, 0.78, 1.0),
            "SparkleColor": (1.0, 0.95, 0.85, 1.0),
        },
        "scalars": {
            "TextureWeight": 0.28,
            "Roughness": 0.45,
            "PastelLift": 0.35,
            "FairyDustIntensity": 1.1,
            "FairyDustScale": 16.0,
            "SparkleIntensity": 1.3,
            "SparkleScale": 10.0,
            "MotifScale": 8.0,
        },
        "textures": {"MotifMask": "baroque41", "FairyGlyphMask": "baroque04", "SparkleMask": "twinkle"},
    },
]

THEME_INSTANCES: list[dict] = BAROQUE_INSTANCES + ZEN_INSTANCES
THEME_NAMES = frozenset(spec["name"] for spec in THEME_INSTANCES)
