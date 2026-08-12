"""Optional Melodia icon helper.

Returns empty kwargs when Figma/custom icons are not installed so UI draws
still work with Blender built-in icons.
"""

from __future__ import annotations


def icon_kwargs(name: str | None = None, **_extra) -> dict:
    """Return operator/layout icon kwargs. Currently a no-op stub."""
    return {}


def get_icon_id(name: str | None = None) -> int:
    return 0
