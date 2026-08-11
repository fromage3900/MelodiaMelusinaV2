"""ARCH_CATALOG-driven dispatch sync — builder registry + param spec stubs."""

from __future__ import annotations

_TRIM_SECTION = (
    "Trim sheet",
    "MOD_BOOLEAN",
    ["gb_trim_mode", "gb_trim_recess", "gb_frame", "gb_bake_trim_colors"],
)
_GRID_SECTION = ("Modular grid", "GRID", ["unit_size"])

_STUB_TEMPLATES = {
    "corridor": [
        (
            "Corridor",
            "MOD_BUILD",
            ["gb_length", "gb_corridor_profile", "gb_height", "gb_wall_thick", "gb_corridor_ceiling"],
        ),
        _TRIM_SECTION,
        _GRID_SECTION,
    ],
    "room": [
        (
            "Room shell",
            "MESH_CUBE",
            ["gb_width", "gb_depth", "gb_height", "gb_wall_thick", "gb_ceiling"],
        ),
        (
            "Openings",
            "MESH_GRID",
            ["gb_door_width", "gb_door_height", "gb_windows_enabled"],
        ),
        _TRIM_SECTION,
        _GRID_SECTION,
    ],
    "bay": [
        (
            "Bay",
            "MESH_CUBE",
            ["gb_width", "gb_height", "gb_wall_thick", "gb_leg_thick"],
        ),
        _TRIM_SECTION,
        _GRID_SECTION,
    ],
    "wall": [
        ("Wall module", "MESH_CUBE", ["gb_length", "gb_height", "gb_wall_thick"]),
        _TRIM_SECTION,
    ],
    "door": [
        (
            "Door end",
            "MESH_CUBE",
            ["gb_length", "gb_door_width", "gb_door_height", "gb_corridor_profile"],
        ),
        _TRIM_SECTION,
    ],
}


def _stub_kind(arch_id):
    low = arch_id.lower()
    if "corridor" in low or "offset" in low:
        return "corridor"
    if "door" in low or "portal" in low or "pressure" in low:
        return "door"
    if "wall" in low or "panel" in low:
        return "wall"
    if any(x in low for x in ("arcade", "loggia", "apse", "bifora", "bay")):
        return "bay"
    if low.startswith("greybox_"):
        return "room"
    return "bay"


def ensure_param_spec_stubs(monolith, arch_ids):
    spec = monolith._ARCH_PARAM_SPEC
    added = 0
    for aid in arch_ids:
        if aid in spec:
            continue
        if not (aid.startswith("GB_") or aid.startswith("GREYBOX_")):
            continue
        kind = _stub_kind(aid)
        spec[aid] = list(_STUB_TEMPLATES.get(kind, _STUB_TEMPLATES["bay"]))
        added += 1
    return added


def _ensure_registries(monolith):
    if not hasattr(monolith, "_CATALOG_DISPATCH"):
        monolith._CATALOG_DISPATCH = {}
    if not hasattr(monolith, "_KIT_DISPATCH"):
        monolith._KIT_DISPATCH = {}
    if not hasattr(monolith, "_KIT_SNAP_FN"):
        monolith._KIT_SNAP_FN = {}


def register_dispatch_entry(
    monolith,
    arch_id,
    builder_attr,
    *,
    snap_fn=None,
    material_key=None,
):
    """Register a catalog-backed builder attr used by apply_geometry_nodes dispatch."""
    _ensure_registries(monolith)
    monolith._CATALOG_DISPATCH[arch_id] = builder_attr
    monolith._KIT_DISPATCH[arch_id] = builder_attr
    if snap_fn is not None:
        monolith._KIT_SNAP_FN[arch_id] = snap_fn
    if material_key and hasattr(monolith, "DEFAULT_MATERIAL_FOR_TYPE"):
        monolith.DEFAULT_MATERIAL_FOR_TYPE[arch_id] = material_key
    ensure_param_spec_stubs(monolith, [arch_id])
    return arch_id


def sync_catalog_dispatch(monolith):
    """Merge overhaul kit builders into catalog dispatch + fill missing param stubs."""
    _ensure_registries(monolith)
    from .catalog import invalidate_catalog_cache, build_catalog

    explicit = {
        "GB_CORRIDOR_OFFSET": "build_greybox_corridor_offset",
        "GB_ROMANESQUE_ARCADE": "build_romanesque_arcade_bay",
        "GB_BRUTALIST_PANEL_WALL": "build_brutalist_panel_wall",
        "GB_VENETIAN_LOGGIA": "build_venetian_loggia_bay",
        "GB_GOTHIC_PORTAL": "build_gothic_portal",
        "GB_GOTHIC_BAY": "build_gothic_bay",
        "GB_GOTHIC_BUTTRESS": "build_gothic_buttress_kit",
        "GB_GOTHIC_TRACERY_PANEL": "build_gothic_tracery_panel",
    }
    for arch_id, attr in explicit.items():
        if hasattr(monolith, attr):
            monolith._CATALOG_DISPATCH[arch_id] = attr
            monolith._KIT_DISPATCH[arch_id] = attr

    invalidate_catalog_cache()
    catalog = build_catalog(monolith)
    for at_id in catalog:
        if at_id.startswith("_"):
            continue
        if at_id in monolith._CATALOG_DISPATCH:
            continue
        attr = _infer_builder_attr(monolith, at_id)
        if attr:
            monolith._CATALOG_DISPATCH[at_id] = attr

    ensure_param_spec_stubs(monolith, list(monolith._CATALOG_DISPATCH.keys()))
    invalidate_catalog_cache()
    return len(monolith._CATALOG_DISPATCH)


def _infer_builder_attr(monolith, arch_id):
    reg = getattr(monolith, "_CATALOG_DISPATCH", {})
    if arch_id in reg:
        return reg[arch_id]
    kit = getattr(monolith, "_KIT_DISPATCH", {})
    if arch_id in kit:
        return kit[arch_id]
    slug = arch_id.lower().replace("gb_", "").replace("greybox_", "")
    for candidate in (
        f"build_{slug}",
        f"build_greybox_{slug}",
        f"build_{slug}_bay",
        f"build_{slug.replace('_bay', '')}_bay",
    ):
        if hasattr(monolith, candidate):
            return candidate
    return None


def catalog_dispatch_summary(monolith):
    sync_catalog_dispatch(monolith)
    from .catalog import build_catalog
    cat = build_catalog(monolith)
    registered = getattr(monolith, "_CATALOG_DISPATCH", {})
    stubs = sum(
        1 for aid in registered
        if aid in monolith._ARCH_PARAM_SPEC and aid.startswith("GB_")
    )
    return {
        "dispatch_entries": len(registered),
        "catalog_types": sum(1 for k in cat if not k.startswith("_")),
        "param_stubs": stubs,
    }
