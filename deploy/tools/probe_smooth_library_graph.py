"""Count Smooth by Angle modifiers after library init + graph spawn."""
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

from surreal_world import library
from surreal_arch.greybox_graph import GRAPH_ZEN_KARESANSHUI_WALK, spawn_graph

stats = library.init_library(s, force_refresh=True)
print("library:", stats)

smooth_objs = []
for obj in bpy.data.objects:
    for m in obj.modifiers:
        if m.name == "Smooth by Angle" or (m.type == "NODES" and m.node_group and "Smooth" in m.node_group.name):
            smooth_objs.append(obj.name)
            break
print("smooth after library:", len(smooth_objs), smooth_objs[:10])

objs = spawn_graph(bpy.context, s, GRAPH_ZEN_KARESANSHUI_WALK, spacing=8.0)
print("graph spawned", len(objs))
smooth_objs2 = []
for obj in bpy.data.objects:
    for m in obj.modifiers:
        if m.name == "Smooth by Angle":
            smooth_objs2.append(obj.name)
            break
print("smooth after graph:", len(smooth_objs2), smooth_objs2)
