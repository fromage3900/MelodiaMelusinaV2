"""Probe shade operators and apply_modifiers path."""
import bpy
import importlib
import math

bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object

for op in dir(bpy.ops.object):
    if "smooth" in op.lower() or "shade" in op.lower():
        print("op:", op)

# Try shade_auto_smooth if exists
for name in ("shade_auto_smooth", "shade_smooth_by_angle", "shade_smooth"):
    fn = getattr(bpy.ops.object, name, None)
    if fn:
        print("trying", name)
        try:
            r = fn()
            print(name, "->", r, "mods:", [m.name for m in obj.modifiers])
        except Exception as e:
            print(name, "err", e)

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

mesh = bpy.data.meshes.new("ProbeMesh2")
obj2 = bpy.data.objects.new("ProbeApply", mesh)
bpy.context.collection.objects.link(obj2)
bpy.context.view_layer.objects.active = obj2
obj2.select_set(True)
p = obj2.surreal_arch_props
p.arch_type = "GB_ZEN_ROJI_STEP"
p.apply_modifiers = True
p.bevel_mode = "EDGE"
bpy.ops.surreal_arch.generate()
print("after apply_modifiers generate:", [(m.name, m.type) for m in obj2.modifiers])
