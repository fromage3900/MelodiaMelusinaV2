# Resonance Loom core - pure-Python logic, no bpy.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Everything testable without Blender lives under this package:
#   lanes.py     - Q/W/O/P vocabulary + the eight rhythm skill ids
#   midi_grid.py - stdlib SMF parser -> tempo-resolved beat grid
#   sidecar.py   - the UE handoff contract (schema v1)
#   naming.py    - authored-name conventions + collision pre-checks
#
# bpy-dependent operators live one level up and import this package lazily so
# `python -m unittest` runs without a Blender install.
