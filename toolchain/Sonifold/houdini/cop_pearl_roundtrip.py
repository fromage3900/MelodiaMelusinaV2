"""cop_pearl_roundtrip.py -- Copernicus pearlescent round-trip on the HeartGate.

Chain: sopimport (geometry->layers) -> ramp (HSV cycles = thin-film banding)
-> hsv (tint shift) -> geoattribfromlayer (3D sample back to points as Cd).
Saves P + Cd npz for the matplotlib viewer. hython 22.0.368.
"""
import hou
import numpy as np

ROOT = r"C:\EnvironmentPortfolio\BS_GodFile\toolchain\Sonifold"
GEO = f"{ROOT}/data/meshes/HeartGate_clean.obj"

obj = hou.node("/obj")
geo = obj.createNode("geo")
filsop = geo.createNode("file")
filsop.parm("file").set(GEO)

copnet = obj.createNode("copnet")
copnet.setName("heartgate_pearl")

imp = copnet.createNode("sopimport")
imp.parm("soppath").set(filsop.path())
imp.cook(force=True)
print("sopimport outputs:", imp.outputNames() if hasattr(imp, "outputNames") else "?")

ramp = copnet.createNode("ramp")
ramp.setInput(0, imp)
rt = ramp.parm("rampType")
items = rt.menuItems()
print("ramp types:", items)
for i, tok in enumerate(items):
    if "hsv" in str(tok).lower():
        rt.set(i); break
ramp.parm("cycles").set(3.0) if ramp.parm("cycles") else None
ramp.cook(force=True)

hue = copnet.createNode("hsv")
hue.setInput(0, ramp)
hue.parm("hueshift").set(160.0)
hue.cook(force=True)

sampler = copnet.createNode("geoattribfromlayer")
print("geoattribfromlayer parms:", [p.name() for p in sampler.parms()])
ref = None
for p in sampler.parms():
    t = p.parmTemplate()
    if t.type() == hou.parmTemplateType.String and \
       t.stringType() == hou.stringParmType.NodeReference:
        ref = p
        break
if ref:
    ref.set(filsop.path())
sampler.setInput(0, hue)
sampler.parm("numattribs").set(1)
if sampler.parm("attrib1"):
    sampler.parm("attrib1").set("Cd")
t1 = sampler.parm("type1")
if t1 and hasattr(t1, "menuItems"):
    for i, tok in enumerate(t1.menuItems()):
        if "color" in str(tok).lower() or "vector" in str(tok).lower():
            t1.set(i); break
sampler.cook(force=True)

g = sampler.geometry()
pa = g.pointFloatAttribValues("Cd") if g.findPointAttrib("Cd") else None
P = np.array([[p.position().x, p.position().y, p.position().z] for p in g.points()])
if pa is None and g.findVertexAttrib("Cd"):
    # vertex attrib -> expand per point via first vertex
    pa = None
print("points:", len(P), "Cd points:", None if pa is None else len(pa))
if pa is not None:
    Cd = np.array(pa).reshape(-1, 3)
    np.savez(f"{ROOT}/data/heartgate_pearl.npz", P=P, Cd=Cd)
    print("saved data/heartgate_pearl.npz  Cd range:", Cd.min(), Cd.max())
hou.hipFile.save(f"{ROOT}/houdini/heartgate_pearl.hip")
print("saved hip")
