"""Single-call kit registration — reduces monolith touch points for new greybox modules."""

from __future__ import annotations

_REGISTERED = []


def register_kit(
    monolith,
    arch_id,
    builder,
    *,
    snap_fn=None,
    builder_attr=None,
    material_key=None,
):
    """Register a greybox kit builder + optional snap compute hook.

    Sets monolith builder attribute and entries in monolith._KIT_DISPATCH / _KIT_SNAP_FN.
    arch_id must already exist in arch_type enum and dispatch dict (or use dynamic dispatch hook).
    """
    global _REGISTERED
    attr = builder_attr or _default_builder_attr(arch_id)
    monolith.__dict__[attr] = lambda t, p, bx=-1400: builder(t, monolith, p, bx)

    try:
        from .catalog_dispatch import register_dispatch_entry
        register_dispatch_entry(
            monolith,
            arch_id,
            attr,
            snap_fn=snap_fn,
            material_key=material_key,
        )
    except ImportError:
        if not hasattr(monolith, "_KIT_DISPATCH"):
            monolith._KIT_DISPATCH = {}
        monolith._KIT_DISPATCH[arch_id] = attr
        if snap_fn is not None:
            if not hasattr(monolith, "_KIT_SNAP_FN"):
                monolith._KIT_SNAP_FN = {}
            monolith._KIT_SNAP_FN[arch_id] = snap_fn
        if material_key and hasattr(monolith, "DEFAULT_MATERIAL_FOR_TYPE"):
            monolith.DEFAULT_MATERIAL_FOR_TYPE[arch_id] = material_key

    _REGISTERED.append(arch_id)
    return arch_id


def _default_builder_attr(arch_id):
    slug = arch_id.lower().replace("gb_", "").replace("greybox_", "")
    return f"build_{slug}"


def registered_kits():
    return list(_REGISTERED)


def clear_registry(monolith):
    global _REGISTERED
    _REGISTERED = []
    if hasattr(monolith, "_KIT_DISPATCH"):
        monolith._KIT_DISPATCH.clear()
    if hasattr(monolith, "_KIT_SNAP_FN"):
        monolith._KIT_SNAP_FN.clear()
