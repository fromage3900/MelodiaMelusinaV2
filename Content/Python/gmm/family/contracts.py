"""Dependency-free vocabulary shared by Blender Melodia Studio and GMM UE."""
from __future__ import annotations

FORMAT = "melodia_project_manifest_v1"
SUPPORTED_UNITS = {"meters", "centimeters"}
SUPPORTED_COORDINATE_SYSTEMS = {"blender_z_up", "unreal_z_up"}

ROLES = frozenset({
    "wall", "floor", "roof", "ornament", "musical_ornament",
    "foliage", "ground", "hero", "character", "vfx",
})

STYLES = frozenset({
    "MELODIA_STAGE", "NIKKI_FLORAWISH", "ZEN_SHRINE", "BAROQUE",
    "ESCHER",
})

APPLICATIONS = frozenset({"blender", "unreal", "gmm", "melodia_studio"})


def is_known_role(value: str) -> bool:
    return value in ROLES


def is_known_style(value: str) -> bool:
    return value in STYLES
