"""bake_heartgate_textures.py -- Copernicus hero-texture bake for the HeartGate
(hython 22.0.368). Bakes curvature, geometric normals, and a point-attrib map
(e.g. live sonifold_amp) into texture layers and exports PNGs.

Geometry needs UVs: use the remeshed proxy (HeartGate_clean.obj) via
bakepreprocess, or add UVs to the HDA cook upstream.
"""
import hou

ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\toolchain\Sonifold"
GEO = f"{ROOT}/data/meshes/HeartGate_clean.obj"
OUT = f"{ROOT}/data/textures"

obj = hou.node("/obj")
geo = obj.createNode("geo")
filsop = geo.createNode("file")
filsop.parm("file").set(GEO)
prep = geo.createNode("bakepreprocess")
prep.setInput(0, filsop)
prep.cook(force=True)
g = prep.geometry()
print("bakepreprocess out:", len(g.prims()), "prims;",
      "has uv:", g.findVertexAttrib("uv") is not None)

copnet = obj.createNode("copnet")
copnet.setName("heartgate_textures")

def cop(name):
    return copnet.createNode(name)

# 1) curvature -> gold gilding mask
curv = cop("curvature")
curv.parm("geometry").set(prep.path())

# 2) normals -> surface orientation for iridescence tinting
nrm = cop("normal")
nrm.parm("geometry").set(prep.path())

# 3) point attrib -> e.g. live Sonifold amplitude pattern stamped into the hero map
attr = cop("attribute")
attr.parm("geometry").set(prep.path())

for n in (curv, nrm, attr):
    n.cook(force=True)
    layers = n.layers()
    print(n.name(), "->", [str(l) for l in layers])

import os
os.makedirs(OUT, exist_ok=True)
for n, fname in ((curv, "T_HeartGate_Curvature"), (nrm, "T_HeartGate_Normal"),
                 (attr, "T_HeartGate_Attrib")):
    out = cop("rop_fileoutput")
    out.setInput(0, n)
    out.parm("filename").set(f"{OUT}/{fname}.png")
    out.cook(force=True)
    print("wrote", f"{OUT}/{fname}.png", os.path.getsize(f"{OUT}/{fname}.png"), "bytes")

hou.hipFile.save(f"{ROOT}/houdini/heartgate_cop_textures.hip")
print("saved hip")
