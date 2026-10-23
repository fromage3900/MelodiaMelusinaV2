"""Probe: can Apprentice write .vdb volumes (UE Sparse Volume Texture path)?
Isolated hython run. Sphere -> vdbfrompolygons -> File SOP .vdb write.
"""
import os

import hou

OUT = os.path.join(os.environ["TEMP"], "probe_vdb.vdb")
g = hou.node("/obj").createNode("geo", "probe_vdb", run_init_scripts=True)
sph = g.createNode("sphere")
vdb = g.createNode("vdbfrompolygons", "to_vdb")
print("[probe] vdbfrompolygons created:", vdb.type().name())
vdb.setInput(0, sph)
try:
    vdb.cook(force=True)
    err = " ".join(str(vdb.errors()).split()) if vdb.errors() else ""
    print("[probe] vdb cook:", err or "OK")
    g2 = g.createNode("file", "writer")
    g2.parm("file").set(OUT)
    g2.parm("filemode").set("write")
    g2.setInput(0, vdb)
    g2.cook(force=True)
    print("[probe] vdb file exists:", os.path.exists(OUT),
          os.path.getsize(OUT) if os.path.exists(OUT) else 0)
except Exception as e:
    print("[probe] EXCEPTION:", str(e)[:400])
