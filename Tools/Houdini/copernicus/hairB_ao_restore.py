# Targeted re-bake: HairB AO only (restores the gamma-lifted BaseColor map that the
# failed auto-levels overwrote). Normal/Emission/Roughness files are untouched.
import hou, json, os, shutil

SEED = 20260922
SIZE = 1024
LANE = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_bake_staging_20260922"
stem = "Melusina_HairB_Strand007"

SNIPPET_AO = """
int nsamples = 64;
float occ = 0;
int seed = chi("pival");
float aog = chf("aog");
for(int i=0;i<nsamples;i++) {
  vector dir = sample_direction_uniform(rand(seed*7+i*131+@ptnum*17));
  dir = dir * sign(dot(dir, v@N));
  vector hitpos; vector hituvw;
  int hit = intersect(0, v@P + v@N*0.001, dir, hitpos, hituvw);
  if(hit >= 0) occ += 1.0;
}
f@Ao = pow(1.0 - occ/float(nsamples), aog);
"""

hou.hipFile.clear(suppress_save_prompt=True)
sopnet = hou.node("/obj").createNode("geo", "hairB_ao")
f = sopnet.createNode("file", "IN")
f.parm("file").set(LANE + "/obj/" + stem + ".obj")
wr = sopnet.createNode("attribwrangle", "VEX_AO")
wr.parm("class").set(2)
wr.addSpareParmTuple(hou.IntParmTemplate("pival", "Pival", 1, default_value=(SEED,), min=0, max=99999999))
wr.parm("pival").set(SEED)
wr.addSpareParmTuple(hou.FloatParmTemplate("aog", "Aog", 1, default_value=(0.45,)))
wr.parm("aog").set(0.45)
wr.parm("snippet").set(SNIPPET_AO)
wr.setInput(0, f)
out = sopnet.createNode("null", "OUT_SOP")
out.setInput(0, wr)
out.setDisplayFlag(True)
out.setRenderFlag(True)
sopnet.layoutChildren()

copnet = hou.node("/img").createNode("copnet", "cop_hairB_ao")
si = copnet.createNode("sopimport", "SOP_Import")
si.parm("usesoppath").set(1)
si.parm("soppath").set("/obj/hairB_ao/OUT_SOP")
pre = copnet.createNode("bakepreprocess", "PRE")
pre.setInput(0, si)
sc = copnet.createNode("constant", "SIZE_Const")
rs = copnet.createNode("resample", "SIZE_Ref")
rs.setInput(0, sc)
rs.parm("resolution1").set(SIZE)
rs.parm("resolution2").set(SIZE)
baker = copnet.createNode("bakegeometrytextures::2.0", "Baker")
baker.parm("uvattribute").set("uv")
baker.parm("enableuvfilling").set(1)
baker.parm("tracingmode").set(2)
baker.parm("attribs").set(1)
baker.parm("doattrib1").set(1)
baker.parm("attrib1").set("Ao")
baker.setInput(0, rs)
baker.setInput(1, pre)
nl = copnet.createNode("null", "BR_AO")
nl.setInput(0, baker, 11)
copnet.layoutChildren()

png = "%s/copernicus_out/%s/T_%s_BaseColor.png" % (LANE, stem, stem)
rop = hou.node("/out").createNode("image", "ROP_AO")
rop.parm("coppath").set(nl.path())
rop.parm("aov1").set("C")
rop.parm("setres").set(1)
rop.parm("res1").set(SIZE)
rop.parm("res2").set(SIZE)
rop.parm("copoutput").set(png)
rop.render()

from PIL import Image
import numpy as np
a = np.asarray(Image.open(png).convert("L"), dtype=np.float32) / 255.0
res = {"schema": "melodia.hairB_ao_restore.v1", "png": png,
       "std": round(float(a.std()), 4), "mean": round(float(a.mean()), 4),
       "p95": round(float(np.percentile(a, 95)), 4)}
with open(LANE + "/hairB_ao_restore_evidence.json", "w", encoding="utf-8") as fo:
    json.dump(res, fo, indent=1)
print("HAIRB_AO_RESTORE:", json.dumps(res))
