"""Optional Melodia icon helper.

Returns empty kwargs when Figma/custom icons are not installed so UI draws
still work with Blender built-in icons.

P2-f builtin map: category -> Blender icon, so the GN stack browser and hub
rows get stable visual coding with zero asset risk. Figma custom-icon load is
P3 (MELODIA_STUDIO_SHIP_CHECKLIST L4).
"""

from __future__ import annotations


CATEGORY_ICONS = {
    # GN stack sections
    "castle_kit": "MOD_BUILD",
    "musical_notation": "IPO_BEZIER",
    "ornament": "BRUSH_DATA",
    "magic_effects": "PARTICLES",
    "architecture": "MESH_CUBE",
    "geometry": "GEOMETRY_NODES",
    "material": "MATERIAL",
    "stage": "SCENE_DATA",
    # Hub rails
    "build": "MESH_CUBE",
    "shape": "MESH_PLANE",
    "style": "RNA",
    "music": "PLAY",
    "dress": "PARTICLES",
    "ship": "EXPORT",
}


def icon_kwargs(name: str | None = None, **_extra) -> dict:
    """Return operator/layout icon kwargs. Builtin map; {} when unknown."""
    if name and name in CATEGORY_ICONS:
        return {"icon": CATEGORY_ICONS[name]}
    return {}


def get_icon_id(name: str | None = None) -> int:
    return 0
