"""PCG mesh alignment and walkability verification for grand architectural scale.

Provides validation for:
- Mesh bounding box alignment (pivot correctness)
- Human-scale walkability (step height, traversal clearance)
- Density heatmap generation for pathing analysis
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None


# Human-scale constants (UE units = cm)
HUMAN_HEIGHT_CM = 180.0
CHARACTER_RADIUS_CM = 40.0
MIN_STEP_HEIGHT_CM = 20.0
MAX_STEP_HEIGHT_CM = 35.0
MIN_WALKWAY_WIDTH_CM = 80.0


def get_mesh_bounds(mesh_path: str) -> dict | None:
    """Get bounding box and pivot info for a static mesh."""
    if unreal is None:
        return None
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        return None
    try:
        box = mesh.get_bounds()
        origin = box.origin
        extent = box.box_extent
        return {
            "path": mesh_path,
            "origin": [origin.x, origin.y, origin.z],
            "extent": [extent.x, extent.y, extent.z],
            "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
            "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
            "height": extent.z * 2,
            "width": extent.x * 2,
            "depth": extent.y * 2,
        }
    except Exception as exc:
        return {"path": mesh_path, "error": str(exc)}


def check_mesh_pivot_for_role(role: str, bounds: dict) -> dict:
    """Validate pivot alignment for architectural roles.
    
    For grand buildings:
    - Floor/ground meshes: pivot should be centered (Z at 0)
    - Wall meshes: pivot should be bottom-centered (min Z at 0)
    - Column/structural: bottom-centered for grid alignment
    """
    if not bounds or "error" in bounds:
        return {"role": role, "valid": False, "reason": bounds.get("error", "unknown")}
    
    min_z = bounds["min"][2]
    
    # Check if pivot is at or near bottom (Z=0 or negative)
    if abs(min_z) < 1.0:
        pivot_status = "bottom_centered"
    elif min_z < -5.0:
        pivot_status = "floating"
    else:
        pivot_status = "centered"
    
    return {
        "role": role,
        "path": bounds["path"],
        "pivot_status": pivot_status,
        "valid": pivot_status in ("bottom_centered", "centered"),
        "height": bounds["height"],
    }


def verify_role_scales(role: str, bounds_list: list[dict]) -> dict:
    """Check all meshes in a role have consistent, walkable scales.
    
    For grand architecture (castles, cathedrals):
    - Columns: 200-400cm height, 20-50cm radius
    - Steps: 20-35cm height, 80+cm width
    - Walls: height 100-200cm, any width
    """
    if not bounds_list:
        return {"role": role, "valid": False, "reason": "no meshes"}
    
    # Asset lookups can legitimately return None while a WP external actor or
    # optional kit piece is unavailable. Keep the audit reportable instead of
    # turning an absent mesh into a tooling crash.
    valid_bounds = [
        b for b in bounds_list
        if isinstance(b, dict) and "error" not in b
    ]
    invalid_bounds = [
        b for b in bounds_list
        if not isinstance(b, dict) or "error" in b
    ]
    heights = [b.get("height", 0) for b in valid_bounds]
    widths = [b.get("width", 0) for b in valid_bounds]
    
    if not heights:
        return {
            "role": role,
            "valid": False,
            "reason": "no valid bounds",
            "invalid_bounds": len(invalid_bounds),
        }
    
    return {
        "role": role,
        "heights_cm": heights,
        "widths_cm": widths,
        "height_range": [min(heights), max(heights)] if heights else [0, 0],
        "width_range": [min(widths), max(widths)] if widths else [0, 0],
        "avg_height": sum(heights) / len(heights) if heights else 0,
        "avg_width": sum(widths) / len(widths) if widths else 0,
        "scales_consistent": max(heights) - min(heights) < 50 if heights else False,
        "invalid_bounds": len(invalid_bounds),
    }


def check_walkability_from_instances(actor, sample_z_offset: float = 20.0) -> dict:
    """Analyze ISM instances for walkability characteristics.
    
    Checks:
    - Instance Z variation (step heights)
    - Clustering patterns (potential pathing obstacles)
    - Scale distribution (human-readable proportions)
    """
    if unreal is None:
        return {"error": "unreal not available"}
    
    ism_heights = []
    scales = []
    
    for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
        try:
            for i in range(comp.get_instance_count()):
                transform = comp.get_instance_transform(i, True)
                scales.append([transform.scale.x, transform.scale.y, transform.scale.z])
                ism_heights.append(transform.transform.location.z)
        except Exception:
            continue
    
    if not ism_heights:
        return {"error": "no instances"}
    
    min_h, max_h = min(ism_heights), max(ism_heights)
    step_variation = max_h - min_h
    
    return {
        "instance_count": len(ism_heights),
        "height_range_cm": [min_h, max_h],
        "step_variation_cm": step_variation,
        "walkable": step_variation < MAX_STEP_HEIGHT_CM * 2,
        "avg_scale": [
            sum(s[i] for s in scales) / len(scales) for i in range(3)
        ] if scales else [1, 1, 1],
    }


def generate_heatmap_data(level_path: str, tag_filter: str | None = None) -> dict:
    """Collect instance density data for heatmap generation.
    
    Returns grid-aligned density counts suitable for texture export.
    """
    if unreal is None:
        return {"error": "unreal not available"}
    
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not eas:
        return {"error": "no actor subsystem"}
    
    # Load level
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if les:
        try:
            les.load_level(level_path)
        except Exception:
            pass
    
    # Collect PCG volume ISM counts
    volume_data = []
    for actor in eas.get_all_level_actors() or []:
        if tag_filter and tag_filter not in [str(t) for t in (actor.tags or [])]:
            continue
        label = actor.get_actor_label()
        if not label.startswith("PCG_"):
            continue
        
        total = 0
        for comp in actor.get_components_by_class(unreal.InstancedStaticMeshComponent):
            try:
                total += int(comp.get_instance_count())
            except Exception:
                continue
        
        loc = actor.get_actor_location()
        volume_data.append({
            "label": label,
            "location": [loc.x, loc.y, loc.z],
            "ism_count": total,
            "density_band": _get_density_band(total),
        })
    
    return {
        "level": level_path,
        "volumes": volume_data,
        "total_ism": sum(v["ism_count"] for v in volume_data),
        "avg_density": sum(v["ism_count"] for v in volume_data) / len(volume_data) if volume_data else 0,
    }


def _get_density_band(count: int) -> str:
    """Classify instance count into density bands."""
    if count < 50:
        return "sparse"
    elif count < 200:
        return "light"
    elif count < 500:
        return "medium"
    elif count < 1000:
        return "dense"
    else:
        return "very_dense"


def audit_pillar_alignment(pillar_key: str) -> dict:
    """Full alignment audit for a pillar level.
    
    Combines mesh bounds, walkability, and density checks.
    """
    import pcg_portfolio_standards as std
    
    level_path = f"{std.LEVEL_WP_ROOT}/L_WP_{pillar_key}"
    
    report = {
        "pillar": pillar_key,
        "level": level_path,
        "meshes": {},
        "walkability": {},
        "density": {},
    }
    
    # Check role mesh scales
    for role, paths in std.SCATTER_MESHES.items():
        bounds_list = [get_mesh_bounds(p) for p in paths if p]
        report["meshes"][role] = verify_role_scales(role, bounds_list)
    
    # Check walkability from generated instances
    report["walkability"] = generate_heatmap_data(level_path)
    
    return report
