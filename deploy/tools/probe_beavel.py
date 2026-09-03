"""Probe Beavel Pro addon operator RNA (factory-startup safe)."""
from __future__ import annotations

import bpy

print("=== PROBE BEAVEL ===")

if "Beavel" not in bpy.context.preferences.addons:
  try:
    bpy.ops.preferences.addon_enable(module="Beavel")
  except Exception as e:
    print(f"enable Beavel failed: {e}")

has_op = hasattr(bpy.ops.mesh, "beavel_operator")
print(f"mesh.beavel_operator: {has_op}")

if has_op:
  try:
    rna = bpy.ops.mesh.beavel_operator.get_rna_type()
    props = [p.identifier for p in rna.properties if not p.is_hidden]
    print("RNA props:", ", ".join(props))
  except Exception as e:
    print(f"RNA probe failed: {e}")

  mesh = bpy.data.meshes.new("ProbeCube")
  obj = bpy.data.objects.new("ProbeBeavel", mesh)
  bpy.context.collection.objects.link(obj)
  bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
  obj = bpy.context.active_object
  bpy.ops.object.mode_set(mode="EDIT")
  bpy.ops.mesh.select_all(action="SELECT")
  try:
    bpy.ops.mesh.beavel_operator(
      prop_plen=0.1,
      prop_ths=0.01,
      prop_cut=1,
      prop_engine=1,
      prop_profile_type="ROUND",
    )
    print("smoke bevel: OK")
  except Exception as e:
    print(f"smoke bevel failed: {e}")
  bpy.ops.object.mode_set(mode="OBJECT")

print("=== PROBE BEAVEL DONE ===")
