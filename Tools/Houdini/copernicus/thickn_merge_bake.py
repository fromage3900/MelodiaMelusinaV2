# Thickness rework: merged hair bake (cross-strand distance is the real signal)
# with quadrant-padded UVs (A bottom-left, B bottom-right, C top-right in UV space),
# self-hit floor (offset 8 mm, sub-10mm hits -> 0.5 fallback), then quadrant split.
# Plus: HairB AO auto-levels (p1->0, p99->1) — its tangle swallows all rays and a
# gamma cannot lift true zero; levels spreads the surviving signal (documented).
import hou, json, os
from PIL import Image
import numpy as np

SEED = 20260922
SIZE = 1024
LANE = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_bake_staging_20260922"
OBJ_DIR = LANE + "/obj"
OUT_ROOT = LANE + "/copernicus_out"
HAIR = [("Melusina_HairA_Strand004", 0.0, 0.0),
        ("Melusina_HairB_Strand007", 0.5, 0.0),
        ("Melusina_HairC_Strand010", 0.5, 0.5)]

SNIPPET = """
vector nd = normalize(v@N);
vector hitp; vector hituvw;
float tmin = -1.0;
int h1 = intersect(0, v@P + nd*0.008, -nd, hitp, hituvw);
if (h1 >= 0) tmin = distance(hitp, v@P);
int h2 = intersect(0, v@P - nd*0.008, nd, hitp, hituvw);
if (h2 >= 0) {
  float t2 = distance(hitp, v@P);
  tmin = (tmin < 0.0) ? t2 : min(tmin, t2);
}
float diag = length(getbbox_size(0));
if (tmin < 0.010 || diag <= 0.0) {
  f@thickn = 0.5;   // self-hit or open space: honest mid fallback
} else {
  f@thickn = clamp(tmin / diag, 0.0, 1.0);
}
"""

hou.hipFile.clear(suppress_save_prompt=True)
sopnet = hou.node("/obj").createNode("geo", "hair_thickn_merged")
merge = sopnet.createNode("merge", "MERGE")
for i, (stem, ou, ov) in enumerate(HAIR):
    f = sopnet.createNode("file", "IN_" + stem)
    f.parm("file").set(OBJ_DIR + "/" + stem + ".obj")
    uvt = sopnet.createNode("uvtransform", "PAD_" + stem)
    uvt.parm("sx").set(0.5)
    uvt.parm("sy").set(0.5)
    uvt.parm("sz").set(0.5)
    uvt.parm("tx").set(ou)
    uvt.parm("ty").set(ov)
    uvt.setInput(0, f)
    merge.setInput(i, uvt)
wr = sopnet.createNode("attribwrangle", "VEX_thickn")
wr.parm("class").set(2)
wr.parm("snippet").set(SNIPPET)
wr.setInput(0, merge)
out = sopnet.createNode("null", "OUT_SOP")
out.setInput(0, wr)
out.setDisplayFlag(True)
out.setRenderFlag(True)
sopnet.layoutChildren()

copnet = hou.node("/img").createNode("copnet", "cop_thickn")
sop_import = copnet.createNode("sopimport", "SOP_Import")
sop_import.parm("usesoppath").set(1)
sop_import.parm("soppath").set("/obj/hair_thickn_merged/OUT_SOP")
pre = copnet.createNode("bakepreprocess", "PRE")
pre.setInput(0, sop_import)
sc = copnet.createNode("constant", "SIZE_Const")
rs = copnet.createNode("resample", "SIZE_Ref")
rs.setInput(0, sc)
rs.parm("resolution1").set(SIZE)
rs.parm("resolution2").set(SIZE)
baker = copnet.createNode("bakegeometrytextures::2.0", "Baker_Thickn")
baker.parm("uvattribute").set("uv")
baker.parm("enableuvfilling").set(1)
baker.parm("tracingmode").set(2)
baker.parm("bakecurvature").set(0)
baker.parm("bakethickness").set(0)
baker.parm("attribs").set(1)
baker.parm("doattrib1").set(1)
baker.parm("attrib1").set("thickn")
baker.setInput(0, rs)
baker.setInput(1, pre)
nl = copnet.createNode("null", "BR_Roughness")
nl.setInput(0, baker, 11)
copnet.layoutChildren()

merged_png = OUT_ROOT + "/_merged_hair_thickn.png"
rop = hou.node("/out").createNode("image", "ROP_Thickn")
rop.parm("coppath").set(nl.path())
rop.parm("aov1").set("C")
rop.parm("setres").set(1)
rop.parm("res1").set(SIZE)
rop.parm("res2").set(SIZE)
rop.parm("copoutput").set(merged_png)
rop.render()
hou.hipFile.save(LANE + "/hip/hair_thickn_merged.hip")

# quadrant split (UV v=0 is PNG bottom)
half = SIZE // 2
img = np.asarray(Image.open(merged_png))
quads = {"Melusina_HairA_Strand004": (0, half, half, SIZE),     # u 0-.5, v 0-.5 -> bottom-left
         "Melusina_HairB_Strand007": (half, half, SIZE, SIZE),  # bottom-right
         "Melusina_HairC_Strand010": (half, 0, SIZE, half)}     # top-right
report = {"schema": "melodia.thickn_merge.v1", "merged": merged_png, "quadrants": {}}
for stem, (c0, r0, c1, r1) in quads.items():
    q = img[r0:r1, c0:c1]
    dst = "%s/%s/T_%s_Roughness.png" % (OUT_ROOT, stem, stem)
    Image.fromarray(q).save(dst)
    a = q.astype("float32") / 255.0
    report["quadrants"][stem] = {"png": dst, "std": round(float(a.std()), 4),
                                 "mean": round(float(a.mean()), 3)}

# HairB AO auto-levels (p1 -> 0, p99 -> 1), honest remap, recorded
ao_png = "%s/Melusina_HairB_Strand007/T_Melusina_HairB_Strand007_BaseColor.png" % OUT_ROOT
a = np.asarray(Image.open(ao_png).convert("RGB"), dtype=np.float32) / 255.0
p1, p99 = np.percentile(a, 1), np.percentile(a, 99)
lvl = np.clip((a - p1) / max(p99 - p1, 1e-4), 0, 1)
Image.fromarray((lvl * 255).astype("uint8")).save(ao_png)
la = lvl.mean(axis=2)
report["hairB_ao_levels"] = {"p1": round(float(p1), 4), "p99": round(float(p99), 4),
                             "std_after": round(float(la.std()), 4),
                             "mean_after": round(float(la.mean()), 3)}
with open(LANE + "/thickn_merge_evidence.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1)
print("THICKN_MERGE:", json.dumps(report["quadrants"]))
print("HAIRB_AO_LEVELS:", json.dumps(report["hairB_ao_levels"]))
