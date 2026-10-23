"""Probe: how does THIS Houdini build write geometry from a File SOP?
Prints the filemode menu tokens/labels and attempts each mode on a sphere,
plus hou.Geometry.saveToFile as a fallback. Evidence over recall.
"""
import hou

g = hou.node("/obj").createNode("geo", "probe_fmt", run_init_scripts=True)
sph = g.createNode("sphere")
f = g.createNode("file")
f.setInput(0, sph)
p = f.parm("filemode")
print("filemode tokens:", p.menuItems())
print("filemode labels:", p.menuLabels())

import os
for i, tok in enumerate(p.menuItems()):
    p.set(i)
    path = os.path.join(os.environ["TEMP"], f"probe_fmt_{tok}.bgeo.sc")
    if os.path.exists(path):
        os.remove(path)
    f.parm("file").set(path)
    try:
        f.cook(force=True)
        print(f"mode {i} ({tok}): exists={os.path.exists(path)} "
              f"size={os.path.getsize(path) if os.path.exists(path) else 0} "
              f"errors={f.errors()}")
    except Exception as e:
        print(f"mode {i} ({tok}): EXCEPTION {e}")

# fallback: saveToFile on the source geometry
try:
    path2 = os.path.join(os.environ["TEMP"], "probe_fmt_savetofile.bgeo.sc")
    g2 = hou.node("/obj/probe_fmt")
    geo = g2.geometry()  # display geo of the network (the sphere)
    geo.saveToFile(path2)
    print("saveToFile:", os.path.exists(path2), os.path.getsize(path2))
except Exception as e:
    print("saveToFile EXCEPTION:", e)

try:
    hou.node("/obj").children()[-1].destroy()
except Exception:
    pass
