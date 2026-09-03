"""Single source of truth for /Game/... content paths.

Created 2026-07-09 during the 2-root consolidation (Melodia/, EnvSandbox/,
_ThirdParty/, _Legacy/ + UE-reserved roots). Import these constants instead of
writing literal /Game/... strings — the consolidation had to rewrite ~35
scripts precisely because paths were scattered literals. Don't regress.

If an asset folder moves again, update it HERE and nowhere else.
"""
from __future__ import annotations

# Primary roots
ENV = "/Game/EnvSandbox"
MELODIA = "/Game/Melodia"
THIRD_PARTY = "/Game/_ThirdParty"
LEGACY = "/Game/_Legacy"
JRPG_TEMPLATE = f"{THIRD_PARTY}/TurnBasedJRPGTemplate"

# EnvSandbox lanes
MATERIALS = f"{ENV}/Materials"
MASTERS = f"{MATERIALS}/Masters"
INSTANCES = f"{MATERIALS}/Instances"
FUNCTIONS = f"{MATERIALS}/Functions"
SDF = f"{MATERIALS}/SDF"
NIAGARA_MATS = f"{MATERIALS}/Niagara"
PCG = f"{ENV}/PCG"
PCG_UNIVERSAL = f"{PCG}/Universal"
PCG_STYLES = f"{PCG}/Styles"
PCG_WP = f"{PCG_STYLES}/WP"
MESHES = f"{ENV}/Meshes"
VFX = f"{ENV}/VFX"
ENVIRONMENTS = f"{ENV}/Environments"
WP_LEVELS = f"{ENVIRONMENTS}/WP"

# Absorbed from old /Game roots (2026-07-09 consolidation)
TEXTURES = f"{ENV}/Textures_Shared"      # was /Game/Textures
GREYBOX_KIT = f"{ENV}/Greybox_Kit"       # was /Game/Greybox_Kit
LIBRARY = f"{ENV}/Library"               # was /Game/Library
FOLIAGE_CARDS = f"{LIBRARY}/FoliageCards"
ALPHAS = f"{ENV}/Alphas_Sparkles"        # was /Game/Alphas_Sparkles
ALPHAS_MELODIA = f"{ENV}/Alphas_Melodia"  # Melodia game UI masks (Figma page 12)
MELODIA_GAME_UI_TEXTURES = f"{ENV}/Textures/Melodia/GameUI"
STYLIZATION = f"{ENV}/Stylization"       # was /Game/Stylization
SAKURA_LEGACY = f"{ENV}/Sakura"          # was /Game/Sakura
WP_TERRAINS = f"{MESHES}/WPTerrains"     # was /Game/_PROJECT/Meshes/WPTerrains

# Melodia (gameplay/legacy project)
MELODIA_PROJECT = f"{MELODIA}/_PROJECT"  # was /Game/_PROJECT

# Key masters
M_UNIVERSAL = f"{MASTERS}/M_Master_Toon_Universal"
M_LANDSCAPE = f"{MASTERS}/M_Master_Toon_Landscape_HeightBlend"
M_WATER = f"{MASTERS}/M_Water_Master_Grand_v10_Upgrade"
M_COSMIC = f"{MASTERS}/M_Master_Toon_Cosmic"
M_SDF_TOON = f"{MASTERS}/M_Master_SDF_Toon"
M_TOON_SDF = f"{MASTERS}/M_Toon_SDF"
M_TOON_FOLIAGE = f"{MASTERS}/M_ToonFoliage"
