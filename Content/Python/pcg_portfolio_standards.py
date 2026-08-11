"""EnvSandbox universal PCG portfolio standards â€” paths, tags, presets, ISM bands."""
from __future__ import annotations

PCG_ROOT = "/Game/EnvSandbox/PCG"
MELODIA_PCG_ROOT = "/Game/_PROJECT/PCG"

DIR_UNIVERSAL = f"{PCG_ROOT}/Universal"
DIR_SUBGRAPHS = f"{PCG_ROOT}/Universal/Subgraphs"
DIR_GREYBOX = f"{PCG_ROOT}/Greybox"
DIR_COLLECTIONS = f"{PCG_ROOT}/Collections"
DIR_STYLES = f"{PCG_ROOT}/Styles"
DIR_DEPRECATED = f"{PCG_ROOT}/_Deprecated"

GRAPH_FOLIAGE = f"{DIR_UNIVERSAL}/PCG_FoliageDensity"
GRAPH_ROCK = f"{DIR_UNIVERSAL}/PCG_RockScatter"
GRAPH_WALL = f"{DIR_UNIVERSAL}/PCG_WallDetail"
GRAPH_EXCLUSION = f"{DIR_SUBGRAPHS}/PCG_ExclusionFalloff"
GRAPH_MEADOW_BLOOM = f"{DIR_UNIVERSAL}/PCG_MeadowBloom"
GRAPH_BLOSSOM_PATH = f"{DIR_UNIVERSAL}/PCG_BlossomPath"
GRAPH_LANTERN_GROVE = f"{DIR_UNIVERSAL}/PCG_LanternGrove"
GRAPH_GARDEN_RUINS = f"{DIR_UNIVERSAL}/PCG_GardenRuins"
GRAPH_PETAL_DRIFT = f"{DIR_STYLES}/Sakura/PCG_Sakura_PetalDrift"
GRAPH_MOSS_GROUNDCOVER = f"{DIR_STYLES}/Sakura/PCG_Zen_MossGroundcover"
GRAPH_GREYBOX_MINIMAL = f"{DIR_GREYBOX}/PCG_Greybox_Minimal"
GRAPH_GREYBOX_STANDARD = f"{DIR_GREYBOX}/PCG_Greybox_Standard"
GRAPH_SAKURA_SHOWCASE = f"{DIR_STYLES}/Sakura/PCG_Sakura_Showcase"

SMC_PORTFOLIO = f"{DIR_COLLECTIONS}/SMC_Portfolio_ScatterKit"
SMC_GREYBOX = f"{DIR_COLLECTIONS}/SMC_Greybox_ScatterKit"
SMC_SAKURA = f"{DIR_STYLES}/Sakura/SMC_Sakura_ScatterKit"
SMC_BAROQUE = f"{DIR_STYLES}/Baroque/SMC_Baroque_ScatterKit"

ORPHAN_MEADOW_SCATTER = f"{PCG_ROOT}/PCG_MeadowScatter"
DEPRECATED_MEADOW = f"{DIR_DEPRECATED}/PCG_MeadowScatter"
ORPHAN_SAKURA_GROVE = f"{PCG_ROOT}/PCG_SakuraGrove"
GRAPH_SAKURA_GROVE = f"{DIR_STYLES}/Sakura/PCG_SakuraGrove"

LEVEL_TEMPLATE = "/Game/EnvSandbox/_Template/L_Template"
LEVEL_SAKURA = "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath"

SHIPPING_LEVELS = (
    LEVEL_TEMPLATE,
    LEVEL_SAKURA,
    "/Game/EnvSandbox/VFX/_Showcase/L_VFX_Showcase",
)

TAG_GROUND = "PCG_Ground"
TAG_EXCLUDE = "PCG_Exclude"
TAG_SPLINE = "PCG_Spline"
TAG_PATH = "PCG_Path"
TAG_POND = "PCG_Pond"

ACTOR_GROUND_COVER = "PCG_Greybox_GroundCover"
ACTOR_ROCKS = "PCG_Greybox_Rocks"
ACTOR_EXCLUDE_PREFIX = "PCG_Exclude_"
ACTOR_SAKURA_VOLUME = "PCG_Sakura_GroundCover"

# Melodia salvage defaults (Tier B â€” meadow/forest reference).
DEFAULT_VOXEL_CM = 180.0
DEFAULT_DENSITY = 0.42
DEFAULT_EXCLUDE_FALLOFF = 220.0
SPACING_PRUNE_RADIUS_CM = 85.0

SEED_FOLIAGE = 4242
SEED_ROCKS = 5150
SEED_BLOSSOMS = 6161
SEED_DECOR = 7171
SEED_PETALS = 8181

GROUND_HALF_EXTENT_UU = 3000.0
PCG_VOLUME_CENTER = (0.0, 0.0, 28.0)
PCG_VOLUME_SCALE = (52.0, 52.0, 3.0)

GRASS_SCALE_MIN = 0.6
GRASS_SCALE_MAX = 1.0
ROCK_SCALE_MIN = 0.4
ROCK_SCALE_MAX = 1.2
PETAL_SCALE_MIN = 0.18
PETAL_SCALE_MAX = 0.55
FLOWER_SCALE_MIN = 0.35
FLOWER_SCALE_MAX = 0.85
DECOR_SCALE_MIN = 0.65
DECOR_SCALE_MAX = 1.35

ISM_BAND_PORTFOLIO = (250, 1600)
ISM_BAND_SAKURA = (320, 1800)
ISM_BAND_MINIMAL = (120, 900)

MI_GREYBOX_GRASS = "/Game/EnvSandbox/Materials/Instances/Showcase/MI_Show_ForestFoliage"
MI_GREYBOX_ROCK = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow"
MI_SAKURA_GRASS = "/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Grass"
MI_SAKURA_PETALS = "/Game/EnvSandbox/Materials/Instances/Sakura/MI_Sakura_Petals"

SCATTER_MESHES: dict[str, list[str]] = {
    # NOTE (2026-07-02): real grass-card content now exists and is wired --
    # see Content/Python/build_experimental_foliage.py, which pairs a real
    # alpha-cutout texture (T_FoliageCards_grass1, previously authored but
    # never used) with a properly-renamed M_ToonFoliage master and a new
    # MI_ExperimentalGrassCard instance, verified live (9583 instances,
    # correct material override confirmed). Currently a self-contained
    # experimental script (mesh+material paired directly), not yet folded
    # into this shared role table -- "grass" below is still the old
    # placeholder set. "petal"/"flower"/"moss" remain genuinely unaddressed.
    "grass": [
        "/Game/Greybox_Kit/SM_Block_Cube_1.SM_Block_Cube_1",
        "/Engine/BasicShapes/Cone.Cone",
        "/Engine/BasicShapes/Cylinder.Cylinder",
    ],
    "rock": [
        "/Game/Greybox_Kit/SM_SM_Rock_1.SM_SM_Rock_1",
        "/Game/Greybox_Kit/SM_SM_Rock_2.SM_SM_Rock_2",
        "/Game/Greybox_Kit/SM_SM_Rock_3.SM_SM_Rock_3",
    ],
    "petal": ["/Engine/BasicShapes/Plane.Plane"],
    "flower": ["/Engine/BasicShapes/Cone.Cone"],
    "moss": [
        "/Engine/BasicShapes/Plane.Plane",
        "/Game/Greybox_Kit/SM_Block_Cube_1.SM_Block_Cube_1",
    ],
    "lantern": [
        "/Game/Library/Migrated/MagiciansLibrary/Lantern/SM_Lantern.SM_Lantern",
        "/Game/Library/Migrated/MagiciansLibrary/LanternGlass/SM_LanternGlass.SM_LanternGlass",
    ],
    "ruin": [
        "/Game/Greybox_Kit/SM_Block_Wall_4x3.SM_Block_Wall_4x3",
        "/Game/Greybox_Kit/SM_Block_Column_05.SM_Block_Column_05",
        "/Game/Greybox_Kit/SM_SM_Rock_1.SM_SM_Rock_1",
    ],
    "decor": [
        "/Game/Library/Migrated/MagiciansLibrary/Deco1/SM_Deco1.SM_Deco1",
        "/Game/Library/Migrated/MagiciansLibrary/Deco2/SM_Deco2.SM_Deco2",
        "/Game/Library/Migrated/MagiciansLibrary/Deco3/SM_Deco3.SM_Deco3",
        "/Game/Library/Migrated/MagiciansLibrary/Deco4/SM_Deco4.SM_Deco4",
        "/Game/Library/Migrated/MagiciansLibrary/Box/SM_Box.SM_Box",
        "/Game/Library/Migrated/MagiciansLibrary/GlassBottle/SM_GlassBottle_Object1715.SM_GlassBottle_Object1715",
    ],
    "structural": [
        "/Game/Greybox_Kit/SM_Block_Cube_1.SM_Block_Cube_1",
        "/Game/Greybox_Kit/SM_Block_Wall_4x3.SM_Block_Wall_4x3",
        "/Game/Greybox_Kit/SM_Block_Column_05.SM_Block_Column_05",
        "/Game/Greybox_Kit/SM_Block_Pillar_03.SM_Block_Pillar_03",
    ],
}

PRESETS: dict[str, dict] = {
    "minimal": {
        "density": 0.28,
        "voxel_cm": 240.0,
        "spawn_rocks": False,
        "spawn_exclusion": False,
        "use_surface_tag": False,
        "transform_jitter": 12.0,
        "ism_band": ISM_BAND_MINIMAL,
        "volume_scale": (38.0, 38.0, 1.6),
        "volume_center_z": 22.0,
    },
    "standard": {
        "density": 0.38,
        "voxel_cm": 200.0,
        "spawn_rocks": True,
        "spawn_exclusion": False,
        "use_surface_tag": False,
        "transform_jitter": 18.0,
        "ism_band": ISM_BAND_PORTFOLIO,
        "volume_scale": (44.0, 44.0, 2.0),
        "volume_center_z": 26.0,
    },
    "showcase": {
        "density": 0.32,
        "voxel_cm": 220.0,
        "spawn_rocks": True,
        "spawn_exclusion": True,
        "use_surface_tag": True,
        "transform_jitter": 24.0,
        "ism_band": ISM_BAND_SAKURA,
        "volume_scale": (46.0, 46.0, 1.8),
        "volume_center_z": 24.0,
        "foliage_graph": GRAPH_SAKURA_SHOWCASE,
    },
}

# Universal style graphs inspired by soft collectible-world staging: readable paths,
# layered groundcover, flowers/petals, lantern accents, ruins, and strong exclusion zones.
STYLE_PRESETS: dict[str, dict] = {
    "meadow_bloom": {
        "label": "Meadow Bloom",
        "graph": GRAPH_MEADOW_BLOOM,
        "role": "flower",
        "material": MI_GREYBOX_GRASS,
        "density": 0.26,
        "voxel_cm": 190.0,
        "use_surface_tag": True,
        "spawn_exclusion": True,
        "transform_jitter": 20.0,
        "scale": (FLOWER_SCALE_MIN, FLOWER_SCALE_MAX),
        "seed": SEED_BLOSSOMS,
        "notes": "Soft flower/ground accent layer for fantasy meadow and garden scenes.",
    },
    "blossom_path": {
        "label": "Blossom Path",
        "graph": GRAPH_BLOSSOM_PATH,
        "role": "petal",
        "material": MI_SAKURA_PETALS,
        "density": 0.18,
        "voxel_cm": 160.0,
        "use_surface_tag": True,
        "spawn_exclusion": True,
        "transform_jitter": 32.0,
        "scale": (PETAL_SCALE_MIN, PETAL_SCALE_MAX),
        "seed": SEED_PETALS,
        "notes": "Readable petal scatter intended for paths, shrine approaches, and reveal shots.",
    },
    "lantern_grove": {
        "label": "Lantern Grove",
        "graph": GRAPH_LANTERN_GROVE,
        "role": "lantern",
        "material": None,
        "density": 0.08,
        "voxel_cm": 420.0,
        "use_surface_tag": False,
        "spawn_exclusion": True,
        "transform_jitter": 40.0,
        "scale": (DECOR_SCALE_MIN, DECOR_SCALE_MAX),
        "seed": SEED_DECOR,
        "notes": "Sparse vertical accent scatter for magical grove or festival staging.",
    },
    "garden_ruins": {
        "label": "Garden Ruins",
        "graph": GRAPH_GARDEN_RUINS,
        "role": "ruin",
        "material": MI_GREYBOX_ROCK,
        "density": 0.10,
        "voxel_cm": 360.0,
        "use_surface_tag": False,
        "spawn_exclusion": True,
        "transform_jitter": 28.0,
        "scale": (0.8, 1.8),
        "seed": SEED_DECOR + 1,
        "notes": "Low-frequency blockout ruin accents for garden/courtyard compositions.",
    },
    "sakura_petal_drift": {
        "label": "Sakura Petal Drift",
        "graph": GRAPH_PETAL_DRIFT,
        "role": "petal",
        "material": MI_SAKURA_PETALS,
        "density": 0.22,
        "voxel_cm": 150.0,
        "use_surface_tag": True,
        "spawn_exclusion": True,
        "transform_jitter": 45.0,
        "scale": (PETAL_SCALE_MIN, PETAL_SCALE_MAX),
        "seed": SEED_PETALS + 1,
        "notes": "Sakura-specific petal layer that stays separate from universal grass.",
    },
    "zen_moss_groundcover": {
        "label": "Zen Moss Groundcover",
        "graph": GRAPH_MOSS_GROUNDCOVER,
        "role": "moss",
        "material": MI_SAKURA_GRASS,
        "density": 0.34,
        "voxel_cm": 210.0,
        "use_surface_tag": True,
        "spawn_exclusion": True,
        "transform_jitter": 18.0,
        "scale": (0.45, 0.9),
        "seed": SEED_FOLIAGE + 1,
        "notes": "Quiet Zen groundcover layer for shrine gardens and neutral template captures.",
    },
}
# Melodia salvage tier hints by asset name fragment.
MELODIA_TIER_HINTS: dict[str, str] = {
    "PCGCol_": "A",
    "MeadowFalloff": "B",
    "MelodiaForest": "B",
    "ForestScatter": "B",
    "SplinePath": "B",
    "WallGarden": "B",
    "Sub_Baroque": "C",
    "Baroque": "C",
    "DreamWalls": "D",
    "Bezier": "D",
    "PCGResearch": "E",
    "Escher": "E",
    "Penrose": "E",
}

PCG_PYTHON_OWNERS: dict[str, str] = {
    GRAPH_FOLIAGE: "setup_pcg_universal.py",
    GRAPH_ROCK: "setup_pcg_universal.py",
    GRAPH_WALL: "setup_pcg_universal.py",
    GRAPH_EXCLUSION: "setup_pcg_universal.py",
    GRAPH_MEADOW_BLOOM: "setup_pcg_universal.py",
    GRAPH_BLOSSOM_PATH: "setup_pcg_universal.py",
    GRAPH_LANTERN_GROVE: "setup_pcg_universal.py",
    GRAPH_GARDEN_RUINS: "setup_pcg_universal.py",
    GRAPH_PETAL_DRIFT: "setup_pcg_universal.py",
    GRAPH_MOSS_GROUNDCOVER: "setup_pcg_universal.py",
    GRAPH_MEADOW_BLOOM: "setup_pcg_universal.py",
    GRAPH_BLOSSOM_PATH: "setup_pcg_universal.py",
    GRAPH_LANTERN_GROVE: "setup_pcg_universal.py",
    GRAPH_GARDEN_RUINS: "setup_pcg_universal.py",
    GRAPH_PETAL_DRIFT: "setup_pcg_universal.py",
    GRAPH_MOSS_GROUNDCOVER: "setup_pcg_universal.py",
    GRAPH_GREYBOX_MINIMAL: "setup_pcg_greybox.py",
    GRAPH_GREYBOX_STANDARD: "setup_pcg_greybox.py",
    GRAPH_SAKURA_SHOWCASE: "setup_pcg_greybox.py",
}

ALL_PORTFOLIO_DIRS = (
    PCG_ROOT,
    DIR_UNIVERSAL,
    DIR_SUBGRAPHS,
    DIR_GREYBOX,
    DIR_COLLECTIONS,
    f"{DIR_STYLES}/Sakura",
    f"{DIR_STYLES}/Baroque",
    DIR_DEPRECATED,
)


def resolve_mesh(role: str):
    try:
        import unreal
    except ImportError:
        paths = SCATTER_MESHES.get(role, [])
        return paths[0] if paths else None
    for path in SCATTER_MESHES.get(role, []):
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            return path
    return None


def melodia_tier(asset_name: str) -> str:
    for frag, tier in MELODIA_TIER_HINTS.items():
        if frag in asset_name:
            return tier
    if asset_name.startswith("PCG_"):
        return "B"
    return "E"



