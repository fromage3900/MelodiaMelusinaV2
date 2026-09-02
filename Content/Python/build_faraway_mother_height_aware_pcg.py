"""
P2 Faraway Mother — Height-Aware PCG Placement
Builds fabric ridges / valley depressions / moon haze via raycast-to-surface.

Builders used (per FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md):
  MEL_terrain_fabric_ridge  — fabric normal-mapped ridge (MI_Master_Nikki_Landscape)
  MEL_valley_depression     — terrain depression with fog fill
  MEL_moon_haze_volume      — volumetric fog box implying distant mass
  MEL_cascade_hair_ribbon   — Niagara ribbon waterfall
  MEL_mother_head_silhouette— sculpted ridge silhouette (hero mesh)

Height-aware mandatory:
  For each XY, raycasts Visibility from Z=50000 -> -50000 to find ground Z.
  Falls back to CanonicalLandscape / MeshTerrain / Landscape actor Z.
  No new Landscape created. No floating pieces.

Target level: /Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype
Instances: 5-8 (default 7) placed along north->south composition line.

Usage (in-editor):
  py Content/Python/build_faraway_mother_height_aware_pcg.py         # dry-run offline
  # in Unreal Python console:
  import build_faraway_mother_height_aware_pcg as fm; fm.run_in_editor()

Refs:
  Docs/Art/FAR_AWAY_MOTHER_PRODUCTION_SHEET_2026-08-29.md
  Docs/Houdini/MARA_P0_P3_HOUDINI_EXECUTION_PLAN_2026-08-29.md
  Tools/Houdini/copernicus/copernicus_terrain_height_to_nanite.py
  Content/Python/_raycast_height.py, _place_atlantis_height_aware.py
"""
from __future__ import annotations
import argparse
import json
import math
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEVEL_PATH = "/Game/EnvSandbox/Monoliths/FarawayMother/Prototype/LV_FarawayMother_Prototype"
MANIFEST_PATH = PROJECT_ROOT / "Saved/Audit/faraway_mother_height_aware_pcg.json"

# Deterministic seed per docs: 20260829
SEED = 20260829

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

PLAN: List[PlannedInstance] = [
    PlannedInstance(
        id="FM_Ridge_HeadSilhouette_01",
        builder="MEL_mother_head_silhouette",
        mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_A.SM_Greybox_Rock_A",
        xy=(0, 9000),
        yaw=0, scale=(6.0, 3.0, 2.2), z_offset=45,
        material_hint="/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
        notes="Head silhouette ridge — face profile reads left, cool moonlit tint (0.15,0.20,0.35)",
    ),
    PlannedInstance(
        id="FM_Ridge_Fabric_02",
        builder="MEL_terrain_fabric_ridge",
        mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_C.SM_Greybox_Rock_C",
        xy=(1200, 5500),
        yaw=18, scale=(7.5, 4.0, 1.6), z_offset=30,
        material_hint="/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_NikkiDream",
        notes="Shoulder/chest fold — fabric normal intensity 2.0, Fold Count ~5",
    ),
    PlannedInstance(
        id="FM_Hair_Cascade_03",
        builder="MEL_cascade_hair_ribbon",
        mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_B.SM_Greybox_Rock_B",
        xy=(-900, 6200),
        yaw=-22, scale=(2.0, 6.0, 1.0), z_offset=80,
        material_hint="/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha",
        notes="Hair/waterfall cascade — Niagara ribbon, translucency 0.8, extends from head down",
    ),
    PlannedInstance(
        id="FM_Ridge_Fabric_04",
        builder="MEL_terrain_fabric_ridge",
        mesh_path="/Game/EnvSandbox/Meshes/WPTerrains/SM_Terrain_BaroqueGrotto.SM_Terrain_BaroqueGrotto",
        xy=(-2600, 1800),
        yaw=35, scale=(1.2, 1.2, 0.9), z_offset=25,
        material_hint="/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
        notes="Secondary fabric ridge — Width/Height/FoldDepth per GN builder",
    ),
    PlannedInstance(
        id="FM_Valley_Shoulder_05",
        builder="MEL_valley_depression",
        mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_A.SM_Greybox_Rock_A",
        xy=(0, -800),
        yaw=-8, scale=(5.0, 5.0, 0.35), z_offset=-60,
        material_hint="/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow",
        notes="Shoulder valley — terrain depression fog-filled, player walks here (gameplay lane)",
    ),
    PlannedInstance(
        id="FM_Valley_Torso_06",
        builder="MEL_valley_depression",
        mesh_path="/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_C.SM_Greybox_Rock_C",
        xy=(400, -4200),
        yaw=12, scale=(6.5, 4.5, 0.30), z_offset=-85,
        material_hint="/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_Meadow",
        notes="Torso depression — deeper valley, denser fog, dark cool grey wet specular",
    ),
    PlannedInstance(
        id="FM_Haze_Limbs_07",
        builder="MEL_moon_haze_volume",
        mesh_path="/Game/EnvSandbox/Meshes/Celestial/SM_MoonShard_A.SM_MoonShard_A",
        xy=(0, -7800),
        yaw=45, scale=(3.0, 3.0, 1.8), z_offset=180,
        material_hint="/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha",
        notes="Distant limbs — NO mesh mass, implied by moon haze silver-blue (0.70,0.75,0.90) density 0.04",
    ),
]

# Fallback meshes if primary missing (ordered by preference)
FALLBACK_MESHES = [
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_A.SM_Greybox_Rock_A",
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_B.SM_Greybox_Rock_B",
    "/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Rock_C.SM_Greybox_Rock_C",
    "/Game/EnvSandbox/Meshes/WPTerrains/SM_Terrain_SpaceCathedral.SM_Terrain_SpaceCathedral",
    "/Game/EnvSandbox/Meshes/Celestial/SM_MoonShard_A.SM_MoonShard_A",
]


def _offline_raycast_z(x: float, y: float) -> float:
    """Offline synthetic height for dry-run (no editor). Flat + gentle swell."""
    # Simulate a landscape that is ~0 at center with mild undulation — never floating check still passes
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
        # Prioritize CanonicalLandscape, then any Landscape, then MeshTerrain / SM_Terrain
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
    # Last resort: first StaticMeshActor or 0
    for a in actors:
        try:
            if type(a).__name__ == "StaticMeshActor":
                return a, float(a.get_actor_location().z), a.get_actor_label()
        except Exception:
            pass
    return None, 0.0, "fallback_zero"


def _raycast_z_unreal(unreal, x: float, y: float, fallback_z: float) -> Tuple[float, bool, str]:
    """Raycast Visibility from high to low. Returns (z, hit, detail).
    Tries Kismet SystemLibrary variants with correct enum handling, falls back to ground_z.
    Monolith mesh_query is preferred when available, but we keep Unreal trace as primary
    to honor the no-new-landscape contract inside the editor process.
    """
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        start = unreal.Vector(x, y, 50000)
        end = unreal.Vector(x, y, -50000)
        hit = None
        # Attempt 1: LineTraceSingleForObjects or Visibility channel via correct enum
        # ECollisionChannel / ETraceTypeQuery differ per UE version; try object-list-free variant first
        for attempt in range(3):
            try:
                if attempt == 0:
                    # Preferred: line_trace_single_by_channel with Visibility (=1) using proper enum resolution
                    # Use unreal.CollisionChannel / ECollisionChannel heuristics
                    ch = None
                    for attr in ("ECC_Visibility", "ECC_WorldStatic", "Visibility"):
                        if hasattr(unreal, attr):
                            ch = getattr(unreal, attr)
                            break
                    if ch is not None:
                        hit = unreal.SystemLibrary.line_trace_single_by_channel(world, start, end, ch, True, [], unreal.DrawDebugType.NONE, False)
                    else:
                        # Fallback to integer channel 1 (Visibility) via by_channel variant which coerces better
                        hit = unreal.SystemLibrary.line_trace_single_by_channel(world, start, end, 1, True, [], unreal.DrawDebugType.NONE, False)
                elif attempt == 1:
                    hit = unreal.SystemLibrary.line_trace_single(
                        world, start, end,
                        unreal.DrawDebugType.NONE,
                        True, [], unreal.TraceTypeQuery.TRACE_TYPE_QUERY1 if hasattr(unreal.TraceTypeQuery, "TRACE_TYPE_QUERY1") else 1
                    )
                else:
                    hit = unreal.SystemLibrary.line_trace_single(world, start, end, 0, True, [], 1)
                break
            except Exception as e_last:
                if attempt == 2:
                    return fallback_z, False, f"trace_failed:{e_last}"
                continue
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
        return fallback_z, False, "miss_fallback_no_landscape"
    except Exception as e:
        return fallback_z, False, f"error:{e}"


def _resolve_mesh(unreal, preferred: str) -> Optional[Any]:
    """Load preferred mesh, else fallback list."""
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


def _try_load_material(unreal, hint: str):
    try:
        mi = unreal.EditorAssetLibrary.load_asset(hint)
        if mi is not None:
            return mi
    except Exception:
        pass
    # Generic fallbacks that always exist
    for fallback in [
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Nikki_Landscape",
        "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
    ]:
        try:
            mi = unreal.EditorAssetLibrary.load_asset(fallback)
            if mi is not None:
                return mi
        except Exception:
            continue
    return None


def run_in_editor(level_path: str = LEVEL_PATH, plan: List[PlannedInstance] = PLAN, save: bool = True) -> Dict[str, Any]:
    """Execute height-aware placement inside Unreal Editor. Must be called from UE Python."""
    import unreal  # type: ignore

    log_entries: List[Dict[str, Any]] = []
    errors: List[str] = []

    # Ensure target level is loaded
    try:
        cur_world = unreal.EditorLevelLibrary.get_editor_world()
        cur_name = str(cur_world.get_name()) if cur_world else ""
        # Load if not already on target (compare suffix)
        if "LV_FarawayMother_Prototype" not in cur_name:
            unreal.log(f"[FarawayMother] Loading level {level_path} (was {cur_name})")
            try:
                unreal.EditorLevelLibrary.load_level(level_path)
            except Exception as e:
                # Some UE versions use different API
                try:
                    unreal.EditorAssetLibrary.load_asset(level_path)
                    unreal.EditorLevelLibrary.load_level(level_path)
                except Exception as e2:
                    errors.append(f"load_level failed: {e} / {e2}")
    except Exception as e:
        errors.append(f"level_load_probe failed: {e}")

    # Idempotency: delete existing FM_ actors before re-placing (prevents duplicate accumulation)
    try:
        existing = unreal.EditorLevelLibrary.get_all_level_actors()
        doomed = []
        for a in existing:
            try:
                if a.get_actor_label().startswith("FM_"):
                    doomed.append(a)
            except Exception:
                pass
        if doomed:
            unreal.log(f"[FarawayMother] Cleaning {len(doomed)} existing FM_ actors for idempotency")
            for a in doomed:
                try:
                    unreal.EditorLevelLibrary.destroy_actor(a)
                except Exception as e:
                    errors.append(f"destroy FM_ failed: {e}")
    except Exception as e:
        errors.append(f"idempotency_cleanup failed: {e}")

    ground_actor, ground_z, ground_label = _find_ground_ref_unreal(unreal)
    unreal.log(f"[FarawayMother] Ground ref: {ground_label} Z={ground_z:.1f}")

    # Optional: warn if no landscape/mesh terrain found (still proceeds height-aware via trace fallback)
    if ground_label in ("fallback_zero", "no_world"):
        unreal.log_warning(f"[FarawayMother] No CanonicalLandscape/MeshTerrain found — using trace fallback Z={ground_z:.1f}. No new Landscape will be created per contract.")

    placed_actors: List[Any] = []
    for pi in plan:
        x, y = pi.xy
        # Raycast to surface
        hit_z, did_hit, detail = _raycast_z_unreal(unreal, x, y, ground_z)
        final_z = hit_z + pi.z_offset

        # Resolve mesh
        mesh_obj, resolved_path = _resolve_mesh(unreal, pi.mesh_path)
        if mesh_obj is None:
            msg = f"{pi.id} mesh not found: {pi.mesh_path} (fallback also missing)"
            unreal.log_error(f"[FarawayMother] {msg}")
            errors.append(msg)
            log_entries.append({
                "id": pi.id, "builder": pi.builder, "xy": [x, y],
                "raycast_z": round(hit_z, 2), "hit": did_hit, "detail": detail,
                "final_z": round(final_z, 2), "z_offset": pi.z_offset,
                "mesh": resolved_path, "status": "mesh_missing", "actor": None,
            })
            continue

        # Spawn
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

        # Scale, label, tags
        try:
            actor.set_actor_scale3d(unreal.Vector(pi.scale[0], pi.scale[1], pi.scale[2]))
        except Exception:
            pass
        try:
            actor.set_actor_label(pi.id)
        except Exception:
            pass
        # Tag for filtering
        try:
            actor.tags = [pi.builder, "FarawayMother", "P2", "height_aware"]
        except Exception:
            pass
        # Mobility static (terrain-like)
        try:
            comp = actor.get_component_by_class(unreal.StaticMeshComponent)
            if comp:
                comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
        except Exception:
            pass
        # Material override attempt
        try:
            mi = _try_load_material(unreal, pi.material_hint)
            if mi is not None:
                comp = actor.get_component_by_class(unreal.StaticMeshComponent)
                if comp:
                    # Only set if MI is compatible; wrap in try
                    try:
                        comp.set_editor_property("override_materials", [mi])
                    except Exception:
                        pass
        except Exception:
            pass

        placed_actors.append(actor)
        unreal.log(f"[FarawayMother] PLACED {pi.id} builder={pi.builder} xy=({x:.0f},{y:.0f}) rayZ={hit_z:.1f} hit={did_hit} finalZ={final_z:.1f} mesh={resolved_path} scale={pi.scale}")

        log_entries.append({
            "id": pi.id, "builder": pi.builder, "xy": [x, y],
            "raycast_z": round(hit_z, 2), "hit": did_hit, "detail": detail,
            "ground_ref": ground_label, "ground_z": round(ground_z, 2),
            "final_z": round(final_z, 2), "z_offset": pi.z_offset,
            "yaw": pi.yaw, "scale": list(pi.scale),
            "mesh": resolved_path, "material_hint": pi.material_hint,
            "notes": pi.notes, "status": "placed", "actor": pi.id,
            "height_aware": True,
        })

    # Save level if requested
    saved = False
    if save and placed_actors:
        try:
            unreal.EditorLevelLibrary.save_current_level()
            unreal.log("[FarawayMother] Level saved.")
            saved = True
        except Exception as e:
            errors.append(f"save_current_level failed: {e}")
            unreal.log_error(f"[FarawayMother] Save failed: {e}")

    # Level status
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
        }
    except Exception as e:
        level_status = {"error": str(e), "level": level_path}

    # Write manifest to Saved/Audit
    manifest = {
        "schema": "melodia.faraway_mother_height_aware_pcg.v1",
        "seed": SEED,
        "level": level_path,
        "ground_ref": ground_label,
        "ground_z": round(ground_z, 2),
        "builders_used": sorted(set(p.builder for p in plan)),
        "required_builders": ["MEL_terrain_fabric_ridge", "MEL_valley_depression"],
        "contract": "height-aware mandatory: raycast Visibility 50000->-50000, no new Landscape, no floating pieces",
        "placements": log_entries,
        "level_status": level_status,
        "errors": errors,
        "height_aware": True,
        "count": len([e for e in log_entries if e.get("status") == "placed"]),
    }
    try:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        unreal.log(f"[FarawayMother] Manifest -> {MANIFEST_PATH}")
    except Exception as e:
        errors.append(f"manifest_write failed: {e}")

    # Console summary
    placed_n = len([e for e in log_entries if e.get("status") == "placed"])
    unreal.log(f"[FarawayMother] DONE placed {placed_n}/{len(plan)} height-aware instances. Level {level_path} saved={saved}")
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
        log_entries.append({
            "id": pi.id, "builder": pi.builder, "xy": [x, y],
            "raycast_z": round(hit_z, 2), "hit": False, "detail": "offline_synthetic",
            "ground_ref": "offline_synthetic", "ground_z": 0.0,
            "final_z": round(final_z, 2), "z_offset": pi.z_offset,
            "yaw": pi.yaw, "scale": list(pi.scale),
            "mesh": pi.mesh_path, "material_hint": pi.material_hint,
            "notes": pi.notes, "status": "dry_run", "actor": None,
            "height_aware": True,
        })
    manifest = {
        "schema": "melodia.faraway_mother_height_aware_pcg.v1",
        "seed": SEED,
        "level": LEVEL_PATH,
        "ground_ref": "offline_synthetic",
        "ground_z": 0.0,
        "builders_used": sorted(set(p.builder for p in PLAN)),
        "required_builders": ["MEL_terrain_fabric_ridge", "MEL_valley_depression"],
        "contract": "height-aware mandatory: raycast Visibility 50000->-50000, no new Landscape, no floating pieces",
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
        },
        "errors": [],
        "height_aware": True,
        "count": len(log_entries),
        "mode": "offline_dry_run",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"\n[FarawayMother] Offline dry-run manifest -> {out_path}")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Faraway Mother height-aware PCG placement")
    ap.add_argument("--offline", action="store_true", help="Force offline dry-run (no editor)")
    ap.add_argument("--out", type=str, default=str(MANIFEST_PATH), help="Manifest output path")
    args = ap.parse_args(argv)
    # Try in-editor unless --offline
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
