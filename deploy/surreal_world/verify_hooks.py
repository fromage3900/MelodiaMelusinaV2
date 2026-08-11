"""Verify helpers for _mcp_verify_world.py."""

from __future__ import annotations

import bpy

from . import compose, instance, library, plans, tags


def count_sacred_buildings(plan_obj, style_key="WESTERN_CASTLE"):
    style = compose.COMPOSE_STYLES.get(style_key, {})
    sacred_lib = style.get("sacred", "")
    root_name = plan_obj.get("surreal_world_root")
    if not root_name:
        return 0
    root = bpy.data.objects.get(root_name)
    if not root:
        return 0
    n = 0
    for inst in instance.iter_world_instances(root):
        if inst.get("surreal_world_role") == "sacred":
            n += 1
    return n


def compose_metrics(world_root):
    """LD QA metrics for automated verify tier."""
    metrics = {
        "instance_count": 0,
        "roles": {},
        "walls": 0,
        "gates": 0,
        "corner_towers": 0,
        "large": 0,
        "sacred": 0,
        "monument": 0,
    }
    if world_root is None:
        return metrics
    for inst in instance.iter_world_instances(world_root):
        role = inst.get("surreal_world_role", "unknown")
        metrics["instance_count"] += 1
        metrics["roles"][role] = metrics["roles"].get(role, 0) + 1
        if role == "wall":
            metrics["walls"] += 1
        elif role == "gate":
            metrics["gates"] += 1
        elif role == "corner_tower":
            metrics["corner_towers"] += 1
        elif role == "large":
            metrics["large"] += 1
        elif role == "sacred":
            metrics["sacred"] += 1
        elif role == "monument":
            metrics["monument"] += 1
    return metrics


def check_castle_ld_metrics(world_root):
    """Return list of LD failures for castle compose."""
    m = compose_metrics(world_root)
    fails = []
    if m["instance_count"] < 15:
        fails.append(f"instance_count={m['instance_count']} < 15")
    if m["walls"] < 4:
        fails.append(f"walls={m['walls']} < 4")
    if m["gates"] < 1:
        fails.append("no gate instance")
    if m["corner_towers"] < 4:
        fails.append(f"corner_towers={m['corner_towers']} < 4")
    if m["large"] < 1:
        fails.append("no large/keep instance")
    return fails


def check_village_ld_metrics(world_root):
    """Return list of LD failures for village compose."""
    m = compose_metrics(world_root)
    fails = []
    if m["instance_count"] < 10:
        fails.append(f"instance_count={m['instance_count']} < 10")
    if m["monument"] < 1:
        fails.append("no plaza/monument instance")
    if m["gates"] < 1:
        fails.append("no gate instance")
    return fails


def check_motte_ld_metrics(world_root):
    """Return list of LD failures for motte/bailey compose (WESTERN_CASTLE or BRUTALIST_PLAZA)."""
    m = compose_metrics(world_root)
    fails = []
    if m["instance_count"] < 10:
        fails.append(f"instance_count={m['instance_count']} < 10")
    if m["large"] < 1:
        fails.append("no keep/large instance on motte")
    if m["gates"] < 1:
        fails.append("no gate instance")
    return fails


def check_city_ld_metrics(world_root):
    """Return list of LD failures for grid city ASIAN_CITY compose."""
    m = compose_metrics(world_root)
    fails = []
    if m["instance_count"] < 12:
        fails.append(f"instance_count={m['instance_count']} < 12")
    if m["gates"] < 1:
        fails.append("no gate instance")
    if m["monument"] < 1:
        fails.append("no monument/plaza instance")
    return fails


def check_zen_ld_metrics(world_root):
    """Return list of LD failures for zen roji compose."""
    m = compose_metrics(world_root)
    fails = []
    if m["instance_count"] < 8:
        fails.append(f"instance_count={m['instance_count']} < 8")
    if m["sacred"] < 1:
        fails.append("no sacred instance")
    has_torii = m["gates"] + m["corner_towers"] >= 1
    if world_root:
        for inst in instance.iter_world_instances(world_root):
            if "TORII" in inst.get("surreal_lib_piece", ""):
                has_torii = True
                break
    if not has_torii:
        fails.append("no torii/gate at entry")
    return fails


def check_zen_temple_ld_metrics(world_root):
    """Return list of LD failures for zen temple compound compose."""
    m = compose_metrics(world_root)
    fails = []
    if m["instance_count"] < 10:
        fails.append(f"instance_count={m['instance_count']} < 10")
    if m["sacred"] < 1:
        fails.append("no sacred instance")
    if m["large"] < 1:
        fails.append("no teahouse/keep instance")
    return fails


def probe_library_vs_enum(monolith):
    """Return arch_types in library spec missing from enum."""
    missing = []
    props = monolith.SurrealArchProperties if hasattr(monolith, "SurrealArchProperties") else None
    if props is None:
        return missing
    enum_ids = {item[0] for item in props.bl_rna.properties["arch_type"].enum_items}
    for at in library.SURREAL_LIBRARY_SPEC:
        if at not in enum_ids:
            missing.append(at)
    return missing
