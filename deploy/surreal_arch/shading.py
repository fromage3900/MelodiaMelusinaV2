"""Shading helpers — avoid duplicate Blender 5.x Smooth by Angle modifiers."""

from __future__ import annotations


def is_smooth_by_angle_modifier(mod) -> bool:
    if mod is None:
        return False
    if mod.name == "Smooth by Angle":
        return True
    if getattr(mod, "type", None) != "NODES":
        return False
    ng = getattr(mod, "node_group", None)
    if ng is None:
        return False
    name = ng.name or ""
    return name == "Smooth by Angle" or "smooth_by_angle" in name.lower()


def purge_smooth_by_angle_modifiers(obj) -> int:
    """Remove object-level Smooth by Angle modifiers (GN cleanup handles shading)."""
    if obj is None or not hasattr(obj, "modifiers"):
        return 0
    removed = 0
    for mod in list(obj.modifiers):
        if is_smooth_by_angle_modifier(mod):
            try:
                obj.modifiers.remove(mod)
                removed += 1
            except Exception:
                pass
    return removed


def purge_addon_modifier_stack(obj, *, keep_bevel: bool = True) -> None:
    """Reset SurrealArch GN stack; optionally drop stray smooth-by-angle mods."""
    if obj is None or not hasattr(obj, "modifiers"):
        return
    purge_smooth_by_angle_modifiers(obj)
    for mod in list(obj.modifiers):
        name = mod.name
        if name.startswith("SurrealArch"):
            obj.modifiers.remove(mod)
        elif not keep_bevel and name in ("SurrealArch_Bevel", "SurrealArch_PolishBevel"):
            obj.modifiers.remove(mod)
