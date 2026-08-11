"""Lightweight diagnostic for procedural world pipeline."""
from __future__ import annotations

import bpy

print("=== PROBE WORLD PIPELINE ===")

if "surreal_architecture_gen" not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module="surreal_architecture_gen")

import surreal_architecture_gen as s

try:
    from surreal_arch.integration import patch_monolith
    patch_monolith(s)
except Exception as e:
    print(f"patch skipped: {e}")

from surreal_world import library, verify_hooks

print(f"library_spec: {len(library.SURREAL_LIBRARY_SPEC)} entries")
print(f"BOULDER_PILE in spec: {'BOULDER_PILE' in library.SURREAL_LIBRARY_SPEC}")
print(f"ZEN types: {[k for k in library.SURREAL_LIBRARY_SPEC if k.startswith('ZEN_')]}")

coll = library.library_collection(create=False)
if coll:
    objs = [o.name for o in coll.objects if o.name.startswith("_lib_")]
    print(f"library_objects: {len(objs)}")
    missing = [k for k in library.SURREAL_LIBRARY_SPEC if f"_lib_{k}" not in objs]
    if missing:
        print(f"missing_lib: {missing}")
else:
    print("library: NOT INITIALIZED")

enum_missing = verify_hooks.probe_library_vs_enum(s)
if enum_missing:
    print(f"enum_missing: {enum_missing}")
else:
    print("enum_missing: none")

print("=== PROBE DONE ===")
