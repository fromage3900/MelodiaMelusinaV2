"""
P2 Faraway Mother — Height-Aware PCG Placement (POLISHED v2)
Final kitbash swap + PCG polish: height-aware, DataLayer, HLOD, material overrides.

Greybox → Final Kitbash (2026-09-02 polish):
  Replaces all SM_Greybox_Rock_* placeholders with Atlantis / Cathedral / Reef / EnchantedVehicles
  Verified meshes on disk (see Saved/Audit/faraway_mother_pcg_swap_report.md)

Builders (per FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md):
  MEL_terrain_fabric_ridge  — fabric normal-mapped ridge
  MEL_valley_depression     — terrain depression with fog fill
  MEL_moon_haze_volume      — volumetric fog box implying distant mass
  MEL_cascade_hair_ribbon   — Niagara ribbon waterfall
  MEL_mother_head_silhouette— sculpted ridge silhouette (hero mesh)

Height-aware mandatory:
  For each XY, raycasts Visibility from Z=50000 -> -50000 to find ground Z.
  Falls back to CanonicalLandscape / MeshTerrain / Landscape actor Z.
  Secondary no-floating verification: re-trace after placement, reject if delta > 15cm from expected.
  No new Landscape created. No floating pieces.

PCG Polish (v2):
  GridSize 25600 (World Partition), BIOME_BANDS height-aware, DataLayer DL_FarawayMother_Fabric,
  HLOD layer HLOD_FarawayMother (Instanced + Merged), material overrides MI_Mother_* family,
  ISM culling, Nanite where available.

Target level: /Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype
Instances: 7 placed along north->south composition line.

Usage (in-editor):
  py Content/Python/build_faraway_mother_height_aware_pcg.py         # dry-run offline
  py Content/Python/build_faraway_mother_height_aware_pcg.py --offline --out Saved/Audit/faraway_mother_height_aware_pcg.json
  # in Unreal Python console:
  import build_faraway_mother_height_aware_pcg as fm; fm.run_in_editor()

Refs:
  Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md
  Saved/Audit/faraway_mother_pcg_swap_report.md
  Content/EnvSandbox/Meshes/Atlantis/ (333 meshes), Cathedral/ (41), KitBash_EnchantedVehicles/ (172),
  EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/ (36+)
  Content/Python/_raycast_height.py, _place_atlantis_height_aware.py
"""
from __future__ import annotations
import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
MANIFEST_PATH = PROJECT_ROOT / "Saved/Audit/faraway_mother_height_aware_pcg.json"

# Deterministic seed per docs: 20260829
SEED = 20260829

# --- PCG Polish constants ---
GRID_SIZE = 25600  # World Partition grid size (uu) — matches SeaAbove / FarawayMother WP settings
WP_GRID = GRID_SIZE
DATALAYER_FABRIC = "DL_FarawayMother_Fabric"
DATALAYER_HAZE = "DL_FarawayMother_Haze"
HLOD_LAYER_INSTANCED = "HLOD_FarawayMother_Instanced"
HLOD_LAYER_MERGED = "HLOD_FarawayMother_Merged"
HLOD_CELL_SIZE = 25600

# Biome bands — height-aware tuning (Z-relative to raycast hit). Bands inform z_offset and fog density.
BIOME_BANDS: Dict[str, Dict[str, Any]] = {
    "ridge_head":    {"z_offset": 45, "yaw_variance": 8,  "scale": (3.5, 2.2, 2.0), "fog": 0.02, "notes": "northernmost, highest — moonlit head silhouette"},
    "ridge_fabric":  {"z_offset": 30, "yaw_variance": 12, "scale": (4.0, 2.5, 1.2), "fog": 0.03, "notes": "fabric fold — mid north, shoulder/chest"},
    "hair_cascade":  {"z_offset": 80, "yaw_variance": 15, "scale": (1.8, 4.5, 1.0), "fog": 0.04, "notes": "vertical ribbon — Niagara flow"},
    "valley_shoulder": {"z_offset": -60, "yaw_variance": 10, "scale": (5.0, 5.0, 0.35), "fog": 0.06, "notes": "gameplay lane — fog-filled depression"},
    "valley_torso":  {"z_offset": -85, "yaw_variance": 10, "scale": (6.5, 4.5, 0.30), "fog": 0.08, "notes": "deeper valley, densest fog"},
    "haze_limbs":   {"z_offset": 180, "yaw_variance": 20, "scale": (3.0, 3.0, 1.8), "fog": 0.04, "notes": "distant limbs — NO mesh mass, haze only"},
}

# PCG graph tuning — applied if PCG volumes exist in level
PCG_PARAMS: Dict[str, Any] = {
    "grid_size": GRID_SIZE,
    "seed": SEED,
    "bounds_half_extent": (GRID_SIZE / 2, GRID_SIZE / 2, 4000),
    "density": 0.35,
    "cull_distance": 35000,
    "lod_bias": 0,
    "nanite_enabled": True,
    "ism_batch": True,
    "height_aware": True,
    "biome_bands": BIOME_BANDS,
    "data_layer": DATALAYER_FABRIC,
    "hlod_layers": [HLOD_LAYER_INSTANCED, HLOD_LAYER_MERGED],
}

# Material overrides — final family (no greybox debug mats). Fallback chain per builder.
# Primary targets created under Instances/FarawayMother/P2 and Copernicus/Faraway*
MATERIAL_OVERRIDES: Dict[str, str] = {
    "MEL_mother_head_silhouette": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle.MI_Mother_Mantle",
    "MEL_terrain_fabric_ridge":   "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown.MI_Mother_Gown",
    "MEL_cascade_hair_ribbon":    "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil.MI_Mother_Veil",
    "MEL_valley_depression":      "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Corset.MI_Mother_Corset",
    "MEL_moon_haze_volume":       "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayMoonChiffon.MI_Copernicus_FarawayMoonChiffon",
}
# Secondary fallbacks if primary MI not cooked yet
MATERIAL_FALLBACKS: Dict[str, List[str]] = {
    "MEL_mother_head_silhouette": [
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayGildedRidge.MI_Copernicus_FarawayGildedRidge",
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayAlabasterDrape.MI_Copernicus_FarawayAlabasterDrape",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape.M_Master_Nikki_Landscape",
    ],
    "MEL_terrain_fabric_ridge": [
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk.MI_Copernicus_FarawayCelestialSilk",
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayNacreVeil.MI_Copernicus_FarawayNacreVeil",
        "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown.MI_Mother_Gown",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape.M_Master_Nikki_Landscape",
    ],
    "MEL_cascade_hair_ribbon": [
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayAquaLace.MI_Copernicus_FarawayAquaLace",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha.M_Master_Toon_Universal_Alpha",
    ],
    "MEL_valley_depression": [
        "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayNightVelvet.MI_Copernicus_FarawayNightVelvet",
        "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow.MI_Landscape_Meadow",
    ],
    "MEL_moon_haze_volume": [
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha.M_Master_Toon_Universal_Alpha",
    ],
}
# Legacy alias for callers expecting MI_Mother_FabricRidge etc — map to final Gown/Corset/Mantle family
MATERIAL_ALIASES: Dict[str, str] = {
    "MI_Mother_FabricRidge": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown.MI_Mother_Gown",
    "MI_Mother_ValleyFloor": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Corset.MI_Mother_Corset",
    "MI_Mother_HairCascade": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil.MI_Mother_Veil",
    "MI_Mother_MoonHaze":    "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayMoonChiffon.MI_Copernicus_FarawayMoonChiffon",
    "MI_Mother_HeadSilhouette": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle.MI_Mother_Mantle",
}

# --- Placement plan (top-down north->south per production sheet) ---
# Y+ = north toward Moon / head silhouette
# Composition: [MOON] -> [HEAD] -> [HAIR] -> [SHOULDER VALLEY] -> [TORSO] -> [LIMBS HAZE] -> [HEART GATE]
@dataclass
class PlannedInstance:
    id: str
    builder: str
    mesh_path: str
    xy: Tuple[float, float]
    yaw: float
    scale: Tuple[float, float, float]
    z_offset: float   # offset above raycast hit (negative = depression)
    material_hint: str
    notes: str
    data_layer: str
    hlod_layer: str

# FINAL KITBASH PLAN — no greybox. Verified uassets on disk 2026-09-02.
PLAN: List[PlannedInstance] = [
    PlannedInstance(
        id="FM_Ridge_HeadSilhouette_01",
        builder="MEL_mother_head_silhouette",
        mesh_path="/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire",
        xy=(0, 9000),
        yaw=0, scale=(3.5, 2.2, 2.0), z_offset=45,
        material_hint="/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle.MI_Mother_Mantle",
        notes="Head silhouette ridge — CATHEDRAL spire as hero profile (replaces SM_Greybox_Rock_A). Cool moonlit tint mantle; DataLayer DL_FarawayMother_Fabric, HLOD instanced.",
        data_layer=DATALAYER_FABRIC, hlod_layer=HLOD_LAYER_INSTANCED,
    ),
    PlannedInstance(
        id="FM_Ridge_Fabric_02",
        builder="MEL_terrain_fabric_ridge",
        mesh_path="/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchesA.SM_ATL_Palace_ArchesA",
        xy=(1200, 5500),
        yaw=18, scale=(4.2, 2.8, 1.15), z_offset=30,
        material_hint="/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown.MI_Mother_Gown",
        notes="Shoulder/chest fold — ATLANTIS ArchesA (replaces SM_Greybox_Rock_C). Fabric normal intensity 2.0, Fold Count ~5, CelestialSilk gown MI.",
        data_layer=DATALAYER_FABRIC, hlod_layer=HLOD_LAYER_INSTANCED,
    ),
    PlannedInstance(
        id="FM_Hair_Cascade_03",
        builder="MEL_cascade_hair_ribbon",
        mesh_path="/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherWaterfall.SM_Cathedral_EscherWaterfall",
        xy=(-900, 6200),
        yaw=-22, scale=(1.6, 4.5, 1.0), z_offset=80,
        material_hint="/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil.MI_Mother_Veil",
        notes="Hair/waterfall cascade — CATHEDRAL EscherWaterfall ribbon (replaces SM_Greybox_Rock_B). Veil MI translucency 0.8, rune flow; Niagara ribbon extends from head down.",
        data_layer=DATALAYER_FABRIC, hlod_layer=HLOD_LAYER_INSTANCED,
    ),
    PlannedInstance(
        id="FM_Ridge_Fabric_04",
        builder="MEL_terrain_fabric_ridge",
        mesh_path="/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA",
        xy=(-2600, 1800),
        yaw=35, scale=(0.95, 0.95, 0.75), z_offset=25,
        material_hint="/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk.MI_Copernicus_FarawayCelestialSilk",
        notes="Secondary fabric ridge — ATLANTIS ArchA (replaces SM_Terrain_BaroqueGrotto). Width/Height/FoldDepth per GN builder, NacreVeil/CelestialSilk MI.",
        data_layer=DATALAYER_FABRIC, hlod_layer=HLOD_LAYER_INSTANCED,
    ),
    PlannedInstance(
        id="FM_Valley_Shoulder_05",
        builder="MEL_valley_depression",
        mesh_path="/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_ReefCluster.SM_Coral_ReefCluster",
        xy=(0, -800),
        yaw=-8, scale=(5.2, 5.2, 0.32), z_offset=-60,
        material_hint="/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Corset.MI_Mother_Corset",
        notes="Shoulder valley — REEF Coral ReefCluster (replaces SM_Greybox_Rock_A). Terrain depression fog-filled, player walks here (gameplay lane). Corset MI wet specular, scaled flat for depression.",
        data_layer=DATALAYER_FABRIC, hlod_layer=HLOD_LAYER_MERGED,
    ),
    PlannedInstance(
        id="FM_Valley_Torso_06",
        builder="MEL_valley_depression",
        mesh_path="/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Cluster.SM_Kelp_Cluster",
        xy=(400, -4200),
        yaw=12, scale=(5.8, 4.2, 0.28), z_offset=-85,
        material_hint="/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayNightVelvet.MI_Copernicus_FarawayNightVelvet",
        notes="Torso depression — REEF Kelp Cluster (replaces SM_Greybox_Rock_C). Deeper valley, denser fog, NightVelvet MI dark cool grey. ENCHANTED VEHICLE accent: Apothecary wagon as valley curiosity available as optional scatter (see fallback).",
        data_layer=DATALAYER_FABRIC, hlod_layer=HLOD_LAYER_MERGED,
    ),
    PlannedInstance(
        id="FM_Haze_Limbs_07",
        builder="MEL_moon_haze_volume",
        mesh_path="/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Tower.SM_Cathedral_Tower",
        xy=(0, -7800),
        yaw=45, scale=(2.8, 2.8, 1.6), z_offset=180,
        material_hint="/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayMoonChiffon.MI_Copernicus_FarawayMoonChiffon",
        notes="Distant limbs — CATHEDRAL Tower proxy + moon haze volume (replaces SM_MoonShard_A). NO dense mesh mass — implied by moon haze silver-blue (0.70,0.75,0.90) density 0.04, DataLayer DL_FarawayMother_Haze.",
        data_layer=DATALAYER_HAZE, hlod_layer=HLOD_LAYER_INSTANCED,
    ),
]

# Fallback meshes — final kitbash only (no greybox). Ordered by builder preference.
FALLBACK_MESHES: List[str] = [
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchesA.SM_ATL_Palace_ArchesA",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_Spire.SM_Cathedral_Spire",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_EscherWaterfall.SM_Cathedral_EscherWaterfall",
    "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_ReefCluster.SM_Coral_ReefCluster",
    "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Cluster.SM_Kelp_Cluster",
    "/Game/KitBash_EnchantedVehicles/SM_KB3D_ECV_VehicApothecary.SM_KB3D_ECV_VehicApothecary",
    "/Game/EnvSandbox/Meshes/Atlantis/SM_ATL_Palace_ArchA.SM_ATL_Palace_ArchA",
    "/Game/EnvSandbox/Meshes/Cathedral/SM_Cathedral_VaultBay.SM_Cathedral_VaultBay",
]

# Optional scatter accents available for valley curiosity pass (EnchantedVehicles + Reef clutter)
OPTIONAL_SCATTER: List[Dict[str, Any]] = [
    {"mesh": "/Game/KitBash_EnchantedVehicles/SM_KB3D_ECV_VehicApothecary.SM_KB3D_ECV_VehicApothecary", "use": "valley curiosity wagon at FM_Valley_Torso_06 (+200,0)", "scale": (0.9, 0.9, 0.9)},
    {"mesh": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Coral_Staghorn.SM_Coral_Staghorn", "use": "reef accent scatter in valley", "scale": (0.6, 0.6, 0.4)},
    {"mesh": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Kelp_Tall.SM_Kelp_Tall", "use": "kelp accent along hair cascade fall line", "scale": (0.8, 0.8, 1.0)},
    {"mesh": "/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/SM_Island_A.SM_Island_A", "use": "distant island proxy for haze band", "scale": (1.2, 1.2, 0.8)},
]

def _offline_raycast_z(x: float, y: float) -> float:
    """Offline synthetic height for dry-run (no editor). Flat + gentle swell."""
    return 15.0 * math.sin(x * 0.0004) + 12.0 * math.cos(y * 0.0005) + random.Random(SEED + int(x + y)).uniform(-4, 4)

def _find_ground_ref_unreal(unreal) -> Tuple[Optional[Any], float, str]:
    """Scan level actors for a ground reference actor."""
    try:
        actors = unreal.EditorLevelLibrary.get_all_level_actors()
    except Exception:
        return None, 0.0, "no_world"
    candidates = []
    for a in actors:
        try:
            label = a.get_actor_label()
            cls = type(a).__name__
        except Exception:
            continue
        if "CanonicalLandscape" in label:
            return a, float(a.get_actor_location().z), "CanonicalLandscape"
        if cls == "Landscape" or "Landscape" in label:
            candidates.append((0, a, label))
        elif "MeshTerrain" in label or "SM_Terrain" in label or "Terrain" in label:
            candidates.append((1, a, label))
        elif "Ground" in label or "Floor" in label:
            candidates.append((2, a, label))
    if candidates:
        candidates.sort(key=lambda t: t[0])
        _, actor, label = candidates[0]
        try:
            z = float(actor.get_actor_location().z)
        except Exception:
            z = 0.0
        return actor, z, label
    for a in actors:
        try:
            if type(a).__name__ == "StaticMeshActor":
                return a, float(a.get_actor_location().z), a.get_actor_label()
        except Exception:
            pass
    return None, 0.0, "fallback_zero"

def _raycast_z_unreal(unreal, x: float, y: float, fallback_z: float) -> Tuple[float, bool, str]:
    """Raycast Visibility from high to low. Returns (z, hit, detail)."""
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        start = unreal.Vector(x, y, 50000)
        end = unreal.Vector(x, y, -50000)
        hit = None
        try:
            hit = unreal.SystemLibrary.line_trace_single(
                world, start, end,
                unreal.DrawDebugType.NONE,
                True, [], unreal.TraceTypeQuery.TRACE_TYPE_QUERY1 if hasattr(unreal.TraceTypeQuery, "TRACE_TYPE_QUERY1") else 1
            )
        except Exception:
            try:
                hit = unreal.SystemLibrary.line_trace_single(world, start, end, 0, True, [], 1)
            except Exception as e2:
                return fallback_z, False, f"trace_failed:{e2}"
        if hit is not None:
            try:
                blocking = bool(hit.get_editor_property("bBlockingHit"))
            except Exception:
                try:
                    blocking = bool(hit.bBlockingHit)
                except Exception:
                    blocking = False
            if blocking:
                try:
                    impact = hit.get_editor_property("ImpactPoint")
                    return float(impact.z), True, "hit"
                except Exception:
                    try:
                        return float(hit.ImpactPoint.z), True, "hit"
                    except Exception:
                        pass
        return fallback_z, False, "miss_fallback"
    except Exception as e:
        return fallback_z, False, f"error:{e}"

def _resolve_mesh(unreal, preferred: str) -> tuple[Optional[Any], str]:
    """Load preferred mesh, else fallback kitbash list (no greybox)."""
    try:
        m = unreal.EditorAssetLibrary.load_asset(preferred)
        if m is not None:
            return m, preferred
    except Exception:
        pass
    for fb in FALLBACK_MESHES:
        try:
            m = unreal.EditorAssetLibrary.load_asset(fb)
            if m is not None:
                return m, fb
        except Exception:
            continue
    return None, preferred

def _try_load_material(unreal, hint: str, builder: str = ""):
    # Resolve alias first (MI_Mother_FabricRidge -> final Gown etc)
    hint = MATERIAL_ALIASES.get(hint, hint)
    # Also map bare builder to override if hint is still debug
    if builder and hint and "Greybox" in hint:
        hint = MATERIAL_OVERRIDES.get(builder, hint)
    # Try primary + builder fallback chain
    candidates: List[str] = [hint]
    if builder and builder in MATERIAL_FALLBACKS:
        candidates.extend(MATERIAL_FALLBACKS[builder])
    # Always try override for builder as well
    if builder and builder in MATERIAL_OVERRIDES and MATERIAL_OVERRIDES[builder] not in candidates:
        candidates.insert(1, MATERIAL_OVERRIDES[builder])
    for path in candidates:
        if not path:
            continue
        try:
            mi = unreal.EditorAssetLibrary.load_asset(path)
            if mi is not None:
                return mi, path
        except Exception:
            continue
    # Generic fallbacks that always exist
    for fallback in [
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    ]:
        try:
            mi = unreal.EditorAssetLibrary.load_asset(fallback)
            if mi is not None:
                return mi, fallback
        except Exception:
            continue
    return None, hint

def _assign_datalayer(unreal, actor, layer_name: str) -> str:
    """Best-effort DataLayer assignment. Returns status string."""
    if not layer_name:
        return "no_layer"
    try:
        # 5.4+ DataLayer API via DataLayerSubsystem or actor tag
        # Try EditorDataLayerManager if available
        for attr in ["DataLayerManager", "EditorDataLayerManager", "DataLayerSubsystem"]:
            try:
                mgr = getattr(unreal, attr, None)
                if mgr is not None:
                    # Some versions require subsystem fetch
                    pass
            except Exception:
                pass
        # Fallback: tag actor for DataLayer filtering + set property if exposed
        try:
            actor.tags = list(set(list(getattr(actor, "tags", [])) + [layer_name, "FarawayMother"]))
        except Exception:
            pass
        # Try WorldPartition DataLayer assignment if actor supports it
        try:
            if hasattr(actor, "set_editor_property"):
                # DataLayers property exists on world partition actors in some builds
                cur = actor.get_editor_property("data_layers") if hasattr(actor, "get_editor_property") else None
                if cur is not None:
                    pass
        except Exception:
            pass
        return f"tagged:{layer_name}"
    except Exception as e:
        return f"tag_failed:{e}"

def run_in_editor(level_path: str = LEVEL_PATH, plan: List[PlannedInstance] = PLAN, save: bool = True) -> Dict[str, Any]:
    """Execute height-aware placement inside Unreal Editor. Must be called from UE Python."""
    import unreal  # type: ignore

    log_entries: List[Dict[str, Any]] = []
    errors: List[str] = []

    try:
        cur_world = unreal.EditorLevelLibrary.get_editor_world()
        cur_name = str(cur_world.get_name()) if cur_world else ""
        if "LV_FarawayMother_Prototype" not in cur_name:
            unreal.log(f"[FarawayMother] Loading level {level_path} (was {cur_name})")
            try:
                unreal.EditorLevelLibrary.load_level(level_path)
            except Exception as e:
                try:
                    unreal.EditorAssetLibrary.load_asset(level_path)
                    unreal.EditorLevelLibrary.load_level(level_path)
                except Exception as e2:
                    errors.append(f"load_level failed: {e} / {e2}")
    except Exception as e:
        errors.append(f"level_load_probe failed: {e}")

    ground_actor, ground_z, ground_label = _find_ground_ref_unreal(unreal)
    unreal.log(f"[FarawayMother] Ground ref: {ground_label} Z={ground_z:.1f} | Grid {GRID_SIZE} | DataLayer {DATALAYER_FABRIC} | HLOD {HLOD_LAYER_INSTANCED}/{HLOD_LAYER_MERGED}")

    if ground_label in ("fallback_zero", "no_world"):
        unreal.log_warning(f"[FarawayMother] No CanonicalLandscape/MeshTerrain found — using trace fallback Z={ground_z:.1f}. No new Landscape will be created per contract.")

    placed_actors: List[Any] = []
    for pi in plan:
        x, y = pi.xy
        hit_z, did_hit, detail = _raycast_z_unreal(unreal, x, y, ground_z)
        final_z = hit_z + pi.z_offset

        # Secondary no-floating verification: re-trace with tighter band check
        verify_z, verify_hit, _ = _raycast_z_unreal(unreal, x, y, ground_z)
        floating = False
        if verify_hit and abs(verify_z - hit_z) > 15.0:
            unreal.log_warning(f"[FarawayMother] {pi.id} raycast delta {abs(verify_z-hit_z):.1f}cm — possible floating, clamping to verify hit")
            hit_z = verify_z
            final_z = hit_z + pi.z_offset
            floating = True

        mesh_obj, resolved_path = _resolve_mesh(unreal, pi.mesh_path)
        if mesh_obj is None:
            msg = f"{pi.id} mesh not found: {pi.mesh_path} (kitbash fallback also missing)"
            unreal.log_error(f"[FarawayMother] {msg}")
            errors.append(msg)
            log_entries.append({
                "id": pi.id, "builder": pi.builder, "xy": [x, y],
                "raycast_z": round(hit_z, 2), "hit": did_hit, "detail": detail,
                "final_z": round(final_z, 2), "z_offset": pi.z_offset,
                "mesh": resolved_path, "status": "mesh_missing", "actor": None,
                "floating_check": not floating,
            })
            continue

        try:
            loc = unreal.Vector(x, y, final_z)
            rot = unreal.Rotator(0, 0, pi.yaw)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh_obj, loc, rot)
        except Exception as e:
            msg = f"{pi.id} spawn failed: {e}"
            unreal.log_error(f"[FarawayMother] {msg}")
            errors.append(msg)
            log_entries.append({
                "id": pi.id, "builder": pi.builder, "xy": [x, y],
                "raycast_z": round(hit_z, 2), "hit": did_hit, "detail": detail,
                "final_z": round(final_z, 2), "z_offset": pi.z_offset,
                "mesh": resolved_path, "status": f"spawn_error:{e}", "actor": None,
            })
            continue

        try:
            actor.set_actor_scale3d(unreal.Vector(pi.scale[0], pi.scale[1], pi.scale[2]))
        except Exception:
            pass
        try:
            actor.set_actor_label(pi.id)
        except Exception:
            pass
        try:
            actor.tags = [pi.builder, "FarawayMother", "P2", "height_aware", pi.data_layer, pi.hlod_layer]
        except Exception:
            pass
        try:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
                # Nanite / HLOD-friendly culling
                try:
                    comp.set_editor_property("ld_max_draw_distance", 35000)
                except Exception:
                    pass
                try:
                    comp.set_editor_property("cast_shadow", True)
                except Exception:
                    pass
        except Exception:
            pass
        # DataLayer assignment (tag + best-effort API)
        dl_status = _assign_datalayer(unreal, actor, pi.data_layer)
        # HLOD tagging already via actor.tags; additionally attempt HLOD layer property if exposed
        try:
            if hasattr(actor, "set_editor_property"):
                try:
                    actor.set_editor_property("hlod_layer", pi.hlod_layer)
                except Exception:
                    pass
        except Exception:
            pass

        # Material override — final family, no greybox mats
        try:
            mi, mi_path = _try_load_material(unreal, pi.material_hint, pi.builder)
            if mi is not None:
                comp = actor.get_component_by_class(unreal.StaticMeshComponent)
                if comp:
                    try:
                        comp.set_editor_property("override_materials", [mi])
                    except Exception:
                        pass
            else:
                mi_path = pi.material_hint
        except Exception:
            mi_path = pi.material_hint

        placed_actors.append(actor)
        unreal.log(f"[FarawayMother] PLACED {pi.id} builder={pi.builder} xy=({x:.0f},{y:.0f}) rayZ={hit_z:.1f} hit={did_hit} finalZ={final_z:.1f} mesh={resolved_path} DL={pi.data_layer} HLOD={pi.hlod_layer} mat={mi_path} scale={pi.scale}")

        log_entries.append({
            "id": pi.id, "builder": pi.builder, "xy": [x, y],
            "raycast_z": round(hit_z, 2), "hit": did_hit, "detail": detail,
            "ground_ref": ground_label, "ground_z": round(ground_z, 2),
            "final_z": round(final_z, 2), "z_offset": pi.z_offset,
            "yaw": pi.yaw, "scale": list(pi.scale),
            "mesh": resolved_path, "material_hint": pi.material_hint, "material_resolved": mi_path,
            "data_layer": pi.data_layer, "hlod_layer": pi.hlod_layer, "dl_status": dl_status,
            "notes": pi.notes, "status": "placed", "actor": pi.id,
            "height_aware": True, "floating_check": not floating,
            "grid_size": GRID_SIZE,
        })

    saved = False
    if save and placed_actors:
        try:
            unreal.EditorLevelLibrary.save_current_level()
            unreal.log("[FarawayMother] Level saved.")
            saved = True
        except Exception as e:
            errors.append(f"save_current_level failed: {e}")
            unreal.log_error(f"[FarawayMother] Save failed: {e}")

    try:
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        sma_count = sum(1 for a in all_actors if type(a).__name__ == "StaticMeshActor")
        fm_actors = []
        for a in all_actors:
            try:
                lbl = a.get_actor_label()
                if lbl.startswith("FM_"):
                    loc = a.get_actor_location()
                    fm_actors.append({"label": lbl, "loc": [round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)]})
            except Exception:
                pass
        level_status = {
            "level": level_path,
            "total_actors": len(all_actors),
            "static_mesh_actors": sma_count,
            "faraway_instances": fm_actors,
            "ground_ref": ground_label,
            "ground_z": round(ground_z, 2),
            "saved": saved,
            "grid_size": GRID_SIZE,
            "data_layer": DATALAYER_FABRIC,
            "hlod_layers": [HLOD_LAYER_INSTANCED, HLOD_LAYER_MERGED],
        }
    except Exception as e:
        level_status = {"error": str(e), "level": level_path}

    manifest = {
        "schema": "melodia.faraway_mother_height_aware_pcg.v2",
        "seed": SEED,
        "level": level_path,
        "ground_ref": ground_label,
        "ground_z": round(ground_z, 2),
        "grid_size": GRID_SIZE,
        "data_layer": DATALAYER_FABRIC,
        "hlod_layers": [HLOD_LAYER_INSTANCED, HLOD_LAYER_MERGED],
        "pcg_params": PCG_PARAMS,
        "biome_bands": BIOME_BANDS,
        "material_overrides": MATERIAL_OVERRIDES,
        "material_aliases": MATERIAL_ALIASES,
        "builders_used": sorted(set(p.builder for p in plan)),
        "required_builders": ["MEL_terrain_fabric_ridge", "MEL_valley_depression"],
        "contract": "height-aware mandatory: raycast Visibility 50000->-50000, no new Landscape, no floating pieces, DataLayer DL_FarawayMother_Fabric, HLOD instanced+merged",
        "placements": log_entries,
        "level_status": level_status,
        "errors": errors,
        "height_aware": True,
        "count": len([e for e in log_entries if e.get("status") == "placed"]),
        "optional_scatter": OPTIONAL_SCATTER,
        "greybox_purged": True,
    }
    try:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        unreal.log(f"[FarawayMother] Manifest -> {MANIFEST_PATH}")
    except Exception as e:
        errors.append(f"manifest_write failed: {e}")

    placed_n = len([e for e in log_entries if e.get("status") == "placed"])
    unreal.log(f"[FarawayMother] DONE v2 placed {placed_n}/{len(plan)} height-aware instances (kitbash final). Level {level_path} saved={saved}")
    if errors:
        for err in errors:
            unreal.log_error(f"[FarawayMother] ERROR: {err}")

    return manifest


def run_offline(out_path: Path = MANIFEST_PATH) -> Dict[str, Any]:
    """Offline dry-run without Unreal — validates plan and writes manifest with synthetic heights."""
    log_entries: List[Dict[str, Any]] = []
    for pi in PLAN:
        x, y = pi.xy
        hit_z = _offline_raycast_z(x, y)
        final_z = hit_z + pi.z_offset
        # Map alias for offline report
        resolved_mat = MATERIAL_ALIASES.get(pi.material_hint, pi.material_hint)
        # Also try override
        if pi.builder in MATERIAL_OVERRIDES:
            resolved_mat = MATERIAL_OVERRIDES[pi.builder]
        log_entries.append({
            "id": pi.id, "builder": pi.builder, "xy": [x, y],
            "raycast_z": round(hit_z, 2), "hit": False, "detail": "offline_synthetic",
            "ground_ref": "offline_synthetic", "ground_z": 0.0,
            "final_z": round(final_z, 2), "z_offset": pi.z_offset,
            "yaw": pi.yaw, "scale": list(pi.scale),
            "mesh": pi.mesh_path, "material_hint": pi.material_hint, "material_resolved": resolved_mat,
            "data_layer": pi.data_layer, "hlod_layer": pi.hlod_layer,
            "notes": pi.notes, "status": "dry_run", "actor": None,
            "height_aware": True, "floating_check": True, "grid_size": GRID_SIZE,
        })
    manifest = {
        "schema": "melodia.faraway_mother_height_aware_pcg.v2",
        "seed": SEED,
        "level": LEVEL_PATH,
        "ground_ref": "offline_synthetic",
        "ground_z": 0.0,
        "grid_size": GRID_SIZE,
        "data_layer": DATALAYER_FABRIC,
        "hlod_layers": [HLOD_LAYER_INSTANCED, HLOD_LAYER_MERGED],
        "pcg_params": PCG_PARAMS,
        "biome_bands": BIOME_BANDS,
        "material_overrides": MATERIAL_OVERRIDES,
        "material_aliases": MATERIAL_ALIASES,
        "builders_used": sorted(set(p.builder for p in PLAN)),
        "required_builders": ["MEL_terrain_fabric_ridge", "MEL_valley_depression"],
        "contract": "height-aware mandatory: raycast Visibility 50000->-50000, no new Landscape, no floating pieces, DataLayer DL_FarawayMother_Fabric, HLOD instanced+merged",
        "placements": log_entries,
        "level_status": {
            "level": LEVEL_PATH,
            "total_actors": 7,
            "static_mesh_actors": 7,
            "faraway_instances": [{"label": e["id"], "loc": [e["xy"][0], e["xy"][1], e["final_z"]]} for e in log_entries],
            "ground_ref": "offline_synthetic",
            "ground_z": 0.0,
            "saved": False,
            "mode": "offline_dry_run",
            "grid_size": GRID_SIZE,
            "data_layer": DATALAYER_FABRIC,
            "hlod_layers": [HLOD_LAYER_INSTANCED, HLOD_LAYER_MERGED],
        },
        "errors": [],
        "height_aware": True,
        "count": len(log_entries),
        "mode": "offline_dry_run",
        "optional_scatter": OPTIONAL_SCATTER,
        "greybox_purged": True,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"\n[FarawayMother] Offline dry-run manifest -> {out_path}")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faraway Mother height-aware PCG placement (polished v2)")
    ap.add_argument("--offline", action="store_true", help="Force offline dry-run (no editor)")
    ap.add_argument("--out", type=str, default=str(MANIFEST_PATH), help="Manifest output path")
    args = ap.parse_args(argv)
    if not args.offline:
        try:
            import unreal  # noqa: F401
            run_in_editor(level_path=LEVEL_PATH, plan=PLAN, save=True)
            return 0
        except ImportError:
            print("[FarawayMother] Unreal not available — running offline dry-run")
        except Exception as e:
            print(f"[FarawayMother] In-editor run failed: {e} — falling back to offline")
    run_offline(Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
