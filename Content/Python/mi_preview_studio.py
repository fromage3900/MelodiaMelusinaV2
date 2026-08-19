"""Shared constants and helpers for the material preview loop studio."""
from __future__ import annotations

import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LEVEL = "/Game/EnvSandbox/_Template/L_MaterialPreview_Studio"
LEVEL_ASSET = f"{LEVEL}.L_MaterialPreview_Studio"
STUDIO_DISPLAY_NAME = "Material Render Studio"

MRQ_PRESET_MI_LOOP = "/Game/EnvSandbox/MRQ/Presets/MRQ_Preset_MI_Loop_1080"
MRQ_SEQUENCES_DIR = "/Game/EnvSandbox/MRQ/Sequences/MI_Loops"

TAG_SWATCH = "MI_Preview_Swatch"
TAG_CAMERA = "CineCamera_PreviewLoop"
TAG_BACKDROP = "MI_Preview_Backdrop"
TAG_KEY_LIGHT = "MI_Preview_KeyLight"
TAG_FILL_LIGHT = "MI_Preview_FillLight"
TAG_RIM_LIGHT = "MI_Preview_RimLight"
TAG_PPV = "PPV_MaterialPreview"
TAG_PEDESTAL = "MI_Preview_Pedestal"
TAG_HYDRO = "MI_Preview_HydroSheet"
TAG_TRIM_CARD = "MI_Preview_TrimCard"

# Nikki render contract (RENDER_POST_PROCESS_NIKKI.md)
PPV_BLOOM = 0.65
PPV_VIGNETTE = 0.22
PPV_GRAIN = 0.06
PPV_CHROMATIC = 0.35
# EV bias is intentionally neutral for portfolio stills.  The previous value
# (+8 EV) saturated the SceneCapture PNG path and made every material look like
# the same white card, even though the swatch material was being applied.
PPV_EXPOSURE_BIAS = 0.0

# Recruiter / Infold Nikki-lens priority plates
NIKKI_PRIORITY = [
    "MI_Show_NikkiHero",
    "MI_Show_SkinSoft",
    "MI_Show_CherryBlossom",
    "MI_Show_FairyHearts",
    "MI_Show_CelestialNebula",
    "MI_NikkiHero_SakuraDream",
    "MI_NikkiHero_CosmicOrrery",
    "MI_NikkiHero_SpaceCathedral",
    "MI_Show_ElementHydro",
    "MI_SDF_RosyQuartz",
]

SHOWCASE_DIR = "/Game/EnvSandbox/Materials/Instances/Showcase"
NIKKI_HERO_DIR = "/Game/EnvSandbox/Materials/Instances/NikkiHero"
SDF_INST_DIR = "/Game/EnvSandbox/Materials/SDF/Instances"

LOOPS_ROOT = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "MaterialLoops"
MANIFEST_JSON = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialLoops" / "mi_preview_manifest.json"
LOOPS_MANIFEST_JSON = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialLoops" / "loops_manifest.json"
DIRTY_CACHE_JSON = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialLoops" / "dirty_cache.json"
PIPELINE_STATUS_JSON = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialLoops" / "pipeline_status.json"
LOOP_STATE_JSON = PROJECT_ROOT / "Saved" / "Audit" / "mi_preview_loop_state.json"
PREVIEW_FRAME_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialLoops" / "PreviewFrames"

FRAME_RATE = 30
LOOP_FRAMES = 120  # 4s @ 30fps
LOOP_RESOLUTION = 1080
# Tighter framing — swatch fills ~60–70% of square frame (was sky-heavy at 280/30°)
ORBIT_RADIUS = 220.0
ORBIT_ELEVATION_DEG = 18.0
CAMERA_FOCAL_LENGTH = 55.0
SWATCH_SPHERE_SCALE = (1.55, 1.55, 1.55)

SPHERE = "/Engine/BasicShapes/Sphere.Sphere"
PLANE = "/Engine/BasicShapes/Plane.Plane"
CUBE = "/Engine/BasicShapes/Cube.Cube"

PREVIEW_MESHES: dict[str, str] = {
    "sphere": SPHERE,
    "plane_vertical": PLANE,
    "plane_horizontal": PLANE,
    "cube": CUBE,
}

# Default Melodia void/iri gradient — never SkyAtmosphere / UDS (UE HQ look).
DEFAULT_BACKDROP = "Melodia_VoidGradient"
MELODIA_VOID_MI = f"{SHOWCASE_DIR}/MI_Show_MelodiaVoidGradient.MI_Show_MelodiaVoidGradient"
MELODIA_VOID_SAKURA = f"{SHOWCASE_DIR}/MI_Show_MelodiaVoid_Sakura.MI_Show_MelodiaVoid_Sakura"
MELODIA_VOID_COSMIC = f"{SHOWCASE_DIR}/MI_Show_MelodiaVoid_Cosmic.MI_Show_MelodiaVoid_Cosmic"
MELODIA_VOID_BAROQUE = f"{SHOWCASE_DIR}/MI_Show_MelodiaVoid_Baroque.MI_Show_MelodiaVoid_Baroque"
MELODIA_VOID_NEUTRAL = f"{SHOWCASE_DIR}/MI_Show_MelodiaVoid_Neutral.MI_Show_MelodiaVoid_Neutral"

BACKDROP_MIS: dict[str, str] = {
    "Melodia_VoidGradient": MELODIA_VOID_MI,
    "Sakura_SoftVoid": MELODIA_VOID_SAKURA,
    "Cosmic_DeepField": MELODIA_VOID_COSMIC,
    "Baroque_WarmVault": MELODIA_VOID_BAROQUE,
    "Studio_Neutral": MELODIA_VOID_NEUTRAL,
    # Legacy showcase paths kept as optional overrides (not default)
    "Legacy_Sakura": f"{SHOWCASE_DIR}/MI_Show_CherryBlossom",
    "Legacy_Cosmic": f"{SHOWCASE_DIR}/MI_Show_CelestialNebula",
    "Legacy_Baroque": f"{SHOWCASE_DIR}/MI_Show_TrimsheetHero",
    "Legacy_Neutral": f"{SHOWCASE_DIR}/MI_Show_Default",
}

# Soft pastel BaseTint overrides for pillar NikkiHero MIs (readability)
NIKKI_HERO_BASE_TINTS: dict[str, tuple[float, float, float, float]] = {
    "MI_NikkiHero_SakuraDream": (0.92, 0.78, 0.88, 1.0),  # soft pink lavender
    "MI_NikkiHero_CosmicOrrery": (0.72, 0.68, 0.95, 1.0),  # dream violet
    "MI_NikkiHero_SpaceCathedral": (0.62, 0.78, 0.95, 1.0),  # cool cathedral
    "MI_NikkiHero_BioGrotto": (0.55, 0.85, 0.78, 1.0),  # seafoam
    "MI_NikkiHero_BaroqueCastle": (0.95, 0.88, 0.72, 1.0),  # warm cream gold
}

PP_MELU_GRADE = "/Game/_PROJECT/04_Materials/PostProcess/M_PP_MeluColorGrade"

COSMIC_SDF_KEYWORDS = (
    "nebula",
    "starfield",
    "aurora",
    "void",
    "eclipse",
    "cosmic",
    "portal",
    "celestial",
    "dust",
    "vinyl",
)

BAROQUE_PROFILES = frozenset({"TP_Gold", "TP_Ornamental", "TP_Stucco"})
WATER_LANDSCAPE_NAMES = frozenset(
    {
        "MI_Show_ElementHydro",
        "MI_Landscape_Meadow",
        "MI_Landscape_SakuraGarden",
        "MI_Landscape_PondBank",
        "MI_GrandWater_ShorelinePond",
    }
)


def mesh_rotation(preview_mesh: str) -> tuple[float, float, float]:
    if preview_mesh == "plane_vertical":
        return (0.0, 90.0, 0.0)
    if preview_mesh == "plane_horizontal":
        return (0.0, 0.0, 0.0)
    return (0.0, 0.0, 0.0)


def default_mesh_scale(preview_mesh: str) -> tuple[float, float, float]:
    if preview_mesh == "plane_vertical":
        return (1.35, 1.35, 0.08)
    if preview_mesh == "plane_horizontal":
        return (1.55, 1.55, 1.0)
    if preview_mesh == "cube":
        return (1.15, 1.15, 1.15)
    return tuple(SWATCH_SPHERE_SCALE)


def orbit_camera_position(frame: int, *, total_frames: int = LOOP_FRAMES) -> tuple[float, float, float]:
    t = (frame / float(total_frames)) * 2.0 * math.pi
    elev = math.radians(ORBIT_ELEVATION_DEG)
    x = ORBIT_RADIUS * math.cos(t) * math.cos(elev)
    y = ORBIT_RADIUS * math.sin(t) * math.cos(elev)
    z = ORBIT_RADIUS * math.sin(elev)
    return (x, y, z)


def look_at_rotation(cam: tuple[float, float, float], target: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> tuple[float, float, float]:
    dx = target[0] - cam[0]
    dy = target[1] - cam[1]
    dz = target[2] - cam[2]
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx * dx + dy * dy)
    # UE camera pitch is positive-up; the target direction already carries the
    # correct sign.  Negating dz here aimed the studio camera above the swatch.
    pitch = math.degrees(math.atan2(dz, horiz))
    return (pitch, yaw, 0.0)


def ue_rotator(rotation: tuple[float, float, float]):
    """Build an Unreal Rotator without Python's positional field reordering."""
    import unreal

    return unreal.Rotator(
        pitch=float(rotation[0]),
        yaw=float(rotation[1]),
        roll=float(rotation[2]),
    )


def sequence_path_for_mi(mi_name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in mi_name)
    return f"{MRQ_SEQUENCES_DIR}/SEQ_{safe}"

def output_dir_for_mi(mi_name: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in mi_name)
    return LOOPS_ROOT / safe
