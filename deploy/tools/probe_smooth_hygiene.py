"""Verify no stray Smooth by Angle modifiers after generate."""
import bpy
import importlib

if "surreal_architecture_gen" not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_enable(module="surreal_architecture_gen")
import surreal_architecture_gen as s
import surreal_arch.integration as integration
importlib.reload(s)
importlib.reload(integration)
try:
    s.unregister()
except Exception:
    pass
s.register()

from surreal_arch.shading import is_smooth_by_angle_modifier

mesh = bpy.data.meshes.new("SmoothProbe")
obj = bpy.data.objects.new("SmoothProbe", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
p = obj.surreal_arch_props
p.arch_type = "GB_ZEN_ROJI_STEP"
p.cleanup_apply_pass = True
p.auto_smooth = False

for i in range(3):
    bpy.ops.surreal_arch.generate()
    n = sum(1 for m in obj.modifiers if is_smooth_by_angle_modifier(m))
    print(f"gen {i+1}: smooth_mods={n} stack={[m.name for m in obj.modifiers]}")
    if n:
        raise SystemExit(1)
print("OK: no Smooth by Angle modifiers after 3 generates")
