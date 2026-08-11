"""Probe Smooth by Angle modifier accumulation on surreal_arch.generate."""
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


def smooth_mods(obj):
    return [m.name for m in obj.modifiers if "Smooth" in m.name or m.type == "NODES" and m.node_group and "Smooth" in m.node_group.name]


def all_mods(obj):
    return [(m.name, m.type) for m in obj.modifiers]


mesh = bpy.data.meshes.new("ProbeMesh")
obj = bpy.data.objects.new("ProbeZen", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

p = obj.surreal_arch_props
p.arch_type = "GB_ZEN_ROJI_STEP"
p.gb_length = 4.5
p.gb_width = 1.8
p.bevel_mode = "EDGE"
p.bevel_amount = 0.04
p.bevel_subdiv_level = 2

print("before generate:", all_mods(obj), "smooth:", smooth_mods(obj))
bpy.ops.surreal_arch.generate()
print("after gen 1:", all_mods(obj), "smooth:", smooth_mods(obj))
bpy.ops.surreal_arch.generate()
print("after gen 2:", all_mods(obj), "smooth:", smooth_mods(obj))
bpy.ops.surreal_arch.generate()
print("after gen 3:", all_mods(obj), "smooth:", smooth_mods(obj))
