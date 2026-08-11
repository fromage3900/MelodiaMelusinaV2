"""Patch monolith panel poll methods for BLOCKOUT / ARCHITECTURE workflow modes."""

from __future__ import annotations

import bpy

from .ui import workflow_allows_panel

PANEL_WORKFLOW_MAP = {
    "SURREAL_ARCH_PT_music": "music",
    "SURREAL_ARCH_PT_magic": "magic",
    "SURREAL_ARCH_PT_scifi": "scifi",
    "SURREAL_ARCH_PT_escher": "escher",
    "SURREAL_ARCH_PT_aesthetic_effects": "effects",
    "SURREAL_ARCH_PT_aesthetic_presets": "effects",
    "SURREAL_ARCH_PT_sverchok": "sverchok",
    "SURREAL_ARCH_PT_higgsas": "higgsas",
    "SURREAL_ARCH_PT_compose": "compose",
    "SURREAL_ARCH_PT_layer3": "layer3",
    "SURREAL_ARCH_PT_advanced_gn": "advanced_gn",
    "SURREAL_ARCH_PT_auto_building": "auto_building",
    "SURREAL_ARCH_PT_kepler": "kepler",
    "SURREAL_ARCH_PT_synthia": "integration",
    "SURREAL_ARCH_PT_curved_roof": "integration",
    "SURREAL_ARCH_PT_bbox_grow": "integration",
    "SURREAL_ARCH_PT_venetian": "integration",
    "SURREAL_ARCH_PT_effects": "effects",
    "SURREAL_ARCH_PT_more_presets": "escher",
}

_PATCHED = set()


def _props_from_context(context):
    obj = context.active_object
    if obj and hasattr(obj, "surreal_arch_props"):
        return obj.surreal_arch_props
    for o in bpy.data.objects:
        if o.type == "MESH" and hasattr(o, "surreal_arch_props"):
            return o.surreal_arch_props
    return None


def patch_workflow_polls(monolith):
    global _PATCHED
    for cls_name, kind in PANEL_WORKFLOW_MAP.items():
        if cls_name in _PATCHED:
            continue
        cls = getattr(monolith, cls_name, None)
        if cls is None:
            cls = getattr(bpy.types, cls_name, None)
        if cls is None:
            continue
        orig_poll = cls.__dict__.get("poll")
        if orig_poll is None:
            continue
        orig_fn = orig_poll.__func__ if isinstance(orig_poll, classmethod) else orig_poll

        def _make_poll(original, panel_kind):
            @classmethod
            def poll(cls, context):
                try:
                    if not original(cls, context):
                        return False
                except Exception:
                    return False
                props = _props_from_context(context)
                if props is None:
                    return panel_kind not in {
                        "music", "magic", "scifi", "escher", "effects", "sverchok",
                        "higgsas", "compose", "layer3", "advanced_gn", "auto_building", "kepler",
                        "integration",
                    }
                return workflow_allows_panel(panel_kind, props)

            return poll

        cls.poll = _make_poll(orig_fn, kind)
        _PATCHED.add(cls_name)
