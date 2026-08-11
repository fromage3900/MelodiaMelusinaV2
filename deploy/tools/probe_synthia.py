"""Probe Synthia math-viz addon operators (optional dependency)."""
from __future__ import annotations

import bpy

print("=== PROBE SYNTHIA ===")

# User may install Synthia under a custom folder — enable by module name if present.
for mod in ("synthia", "Synthia", "blender_synthia"):
  if mod in bpy.context.preferences.addons:
    print(f"addon enabled: {mod}")
    break
else:
  for mod in ("synthia", "Synthia"):
    try:
      bpy.ops.preferences.addon_enable(module=mod)
      print(f"enabled: {mod}")
      break
    except Exception:
      pass

has_spawn = hasattr(bpy.ops.synthia, "spawn_preset")
has_custom = hasattr(bpy.ops.synthia, "custom_formula")
print(f"synthia.spawn_preset: {has_spawn}")
print(f"synthia.custom_formula: {has_custom}")

if has_spawn:
  try:
    rna = bpy.ops.synthia.spawn_preset.get_rna_type()
    props = [p.identifier for p in rna.properties if not p.is_hidden]
    print("spawn_preset props:", ", ".join(props))
  except Exception as e:
    print(f"spawn_preset RNA: {e}")

if has_custom:
  try:
    rna = bpy.ops.synthia.custom_formula.get_rna_type()
    props = [p.identifier for p in rna.properties if not p.is_hidden]
    print("custom_formula props:", ", ".join(props))
  except Exception as e:
    print(f"custom_formula RNA: {e}")

if has_spawn:
  before = {o.name for o in bpy.data.objects}
  try:
    bpy.ops.synthia.spawn_preset(preset_name="torus_knot", preset_type="EQUATION")
    after = [o for o in bpy.data.objects if o.name not in before]
    print(f"spawn created {len(after)} object(s): {[o.name for o in after]}")
    for o in after:
      print(f"  {o.name} type={o.type} verts={len(o.data.vertices) if o.type == 'MESH' and o.data else 0}")
  except Exception as e:
    print(f"spawn smoke failed: {e}")
else:
  print("Synthia not installed — verify tier will SKIP")

print("=== PROBE SYNTHIA DONE ===")
