"""LD metric probes for greybox tower and corridor modules (v2.72.2)."""

from __future__ import annotations


def check_greybox_tower_ld_metrics(obj, props):
    """Return list of failures for GREYBOX_TOWER walkability."""
    fails = []
    floors = max(1, getattr(props, "gb_floors", 4))
    fh = getattr(props, "gb_height", 3.2)
    dw = getattr(props, "gb_door_width", 1.4)
    if fh < 2.39:
        fails.append(f"per_floor_height={fh} < 2.4 m")
    if dw < 1.39:
        fails.append(f"door_width={dw} < 1.4 m")
    if floors < 1:
        fails.append("gb_floors < 1")
    return fails


def check_greybox_corridor_ld_metrics(props):
    fails = []
    h = getattr(props, "gb_height", 3.5)
    if h < 2.4:
        fails.append(f"corridor_height={h} < 2.4 m")
    return fails


def probe_greybox_ld_metrics(context, monolith):
    """Smoke-check greybox LD defaults after generate."""
    obj = context.active_object
    if not obj or not hasattr(obj, "surreal_arch_props"):
        return ["no active surreal_arch_props object"]
    props = obj.surreal_arch_props
    at = props.arch_type
    if at == "GREYBOX_TOWER":
        return check_greybox_tower_ld_metrics(obj, props)
    if at in ("GREYBOX_CORRIDOR", "GB_CORRIDOR_OFFSET", "GB_CORRIDOR_BEND"):
        return check_greybox_corridor_ld_metrics(props)
    return []
