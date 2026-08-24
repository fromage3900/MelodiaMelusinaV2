# Melodia Showroom — integrated terrain → dress → frame → render
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

try:
    from . import operators, panel, properties
except Exception:
    operators = panel = properties = None


def register():
    if operators is None:
        return
    properties.register()
    operators.register()
    panel.register()


def unregister():
    if panel is None:
        return
    panel.unregister()
    operators.unregister()
    properties.unregister()
