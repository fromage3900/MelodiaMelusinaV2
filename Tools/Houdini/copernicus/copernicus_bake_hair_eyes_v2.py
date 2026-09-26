# Copernicus re-bake v2 for the Melusina hair + eye staging OBJs.
# Fixes from the contact-sheet review (2026-09-22 evening):
#   1. Thickness channel was flat white on ALL meshes -> open single-layer sheets
#      give the one-sided ray nothing to hit. Now: two-sided ray (min of +/-N hits),
#      normalized by bbox diagonal, 0.5 fallback when truly open, exported as the
#      SECOND custom attrib "thickn" and read from the baker's custom-2 branch.
#   2. HairB AO was near-black (dense tangle self-occlusion) -> per-mesh AO gamma
#      (HairB 0.45 lift; others 1.0).
# Chain otherwise identical to the proven dress bake. Token-replace, no .format.
import hou, json, os, shutil

SEED = 20260922
SIZE = 1024
LANE = "C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_bake_staging_20260922"
OBJ_DIR = LANE + "/obj"
OUT_ROOT = LANE + "/copernicus_out"
HIP_DIR = LANE + "/hip"
os.makedirs(HIP_DIR, exist_ok=True)

MESHES = ["Melusina_HairA_Strand004", "Melusina_HairB_Strand007", "Melusina_HairC_Strand010",
          "Melusina_IrisA_R1", "Melusina_IrisB_R2", "Melusina_Eyelash_R"]
AO_GAMMA = {"Melusina_HairB_Strand007": 0.45}
CHANNELS = {"BaseColor": 11, "Normal": 0, "Emission": 5, "Roughness": 12}  # 12 = custom attrib 2

SNIPPET_GEO = """
// two-sided thickness: open sheets need rays BOTH ways
vector nd = normalize(v@N);
vector hitp; vector hituvw;
float tmin = -1.0;
int h1 = intersect(0, v@P + nd*0.001, -nd, hitp, hituvw);
if (h1 >= 0) tmin = distance(hitp, v@P);
int h2 = intersect(0, v@P - nd*0.001, nd, hitp, hituvw);
if (h2 >= 0) {
  float t2 = distance(hitp, v@P);
  tmin = (tmin < 0.0) ? t2 : min(tmin, t2);
}
// curvature: Laplacian of N
vector lap = 0;
int npt[] = neighbours(0, @ptnum);
foreach(int n; npt) lap += point(0, "N", n) - v@N;
float curv = length(lap);
f@convex = max(curv, 0);
f@concave = max(-curv, 0);
v@Cd = set(max(tmin, 0.0), f@convex, f@concave);
// normalized thickness for the bake: bbox diagonal of the whole geometry
float diag = length(getbbox_size(0));
f@thickn = (tmin >= 0.0 && diag > 0.0) ? clamp(tmin / diag, 0.0, 1.0) : 0.5;
"""

SNIPPET_AO = """
// AO: hemisphere 64 rays, self-exclusion; per-mesh gamma lift on the result
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

manifest = {"schema": "melodia.copernicus_hair_eyes_bake.v2", "seed": SEED, "size": SIZE,
            "fixes": ["two-sided thickness -> thickn custom2", "per-mesh AO gamma"],
            "meshes": {}, "hython": hou.applicationVersionString()}

for stem in MESHES:
    out_dir = OUT_ROOT + "/" + stem
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    obj_path = OBJ_DIR + "/" + stem + ".obj"
    if not os.path.isfile(obj_path) or os.path.getsize(obj_path) < 1000:
        manifest["meshes"][stem] = {"verdict": "OBJ_MISSING"}
        continue

    hou.hipFile.clear(suppress_save_prompt=True)
    sopnet = hou.node("/obj").createNode("geo", "bake_" + stem)
    file_sop = sopnet.createNode("file", "IN_STAGED_MESH")
    file_sop.parm("file").set(obj_path)
    wrangle_geo = sopnet.createNode("attribwrangle", "VEX_geometry_attrs")
    wrangle_geo.parm("class").set(2)
    wrangle_geo.parm("snippet").set(SNIPPET_GEO)
    wrangle_geo.setInput(0, file_sop)
    wrangle_ao = sopnet.createNode("attribwrangle", "VEX_AO_64")
    wrangle_ao.parm("class").set(2)
    wrangle_ao.addSpareParmTuple(hou.IntParmTemplate("pival", "Pival", 1,
                                  default_value=(SEED,), min=0, max=99999999))
    wrangle_ao.parm("pival").set(SEED)
    wrangle_ao.addSpareParmTuple(hou.FloatParmTemplate("aog", "Aog", 1,
                                  default_value=(AO_GAMMA.get(stem, 1.0),)))
    wrangle_ao.parm("aog").set(AO_GAMMA.get(stem, 1.0))
    wrangle_ao.parm("snippet").set(SNIPPET_AO)
    wrangle_ao.setInput(0, wrangle_geo)
    out_sop = sopnet.createNode("null", "OUT_SOP")
    out_sop.setInput(0, wrangle_ao)
    out_sop.setDisplayFlag(True)
    out_sop.setRenderFlag(True)
    sopnet.layoutChildren()

    copnet = hou.node("/img").createNode("copnet", "cop_" + stem)
    sop_import = copnet.createNode("sopimport", "SOP_Import")
    sop_import.parm("usesoppath").set(1)
    sop_import.parm("soppath").set("/obj/bake_" + stem + "/OUT_SOP")
    pre = copnet.createNode("bakepreprocess", "PRE_Bake")
    pre.setInput(0, sop_import)
    size_const = copnet.createNode("constant", "SIZE_Const")
    size_rs = copnet.createNode("resample", "SIZE_Ref")
    size_rs.setInput(0, size_const)
    size_rs.parm("resolution1").set(SIZE)
    size_rs.parm("resolution2").set(SIZE)
    # Two bakers off the same preprocess: the baker exposes ONE custom output
    # (index 11), so Ao and thickn each get their own baker (honest signals).
    baker = copnet.createNode("bakegeometrytextures::2.0", "Baker_GeoTex_AO")
    baker.parm("uvattribute").set("uv")
    baker.parm("enableuvfilling").set(1)
    baker.parm("tracingmode").set(2)
    baker.parm("bakecurvature").set(1)
    baker.parm("bakethickness").set(0)
    baker.parm("attribs").set(1)
    baker.parm("doattrib1").set(1)
    baker.parm("attrib1").set("Ao")
    baker.setInput(0, size_rs)
    baker.setInput(1, pre)
    baker_t = copnet.createNode("bakegeometrytextures::2.0", "Baker_GeoTex_Thickn")
    baker_t.parm("uvattribute").set("uv")
    baker_t.parm("enableuvfilling").set(1)
    baker_t.parm("tracingmode").set(2)
    baker_t.parm("bakecurvature").set(0)
    baker_t.parm("bakethickness").set(0)
    baker_t.parm("attribs").set(1)
    baker_t.parm("doattrib1").set(1)
    baker_t.parm("attrib1").set("thickn")
    baker_t.setInput(0, size_rs)
    baker_t.setInput(1, pre)

    branch_nodes = {
        "BaseColor": ("baker", 11),
        "Normal": ("baker", 0),
        "Emission": ("baker", 5),
        "Roughness": ("baker_t", 11),
    }
    bakers = {"baker": baker, "baker_t": baker_t}
    for name, (src, idx) in branch_nodes.items():
        nl = copnet.createNode("null", "BR_" + name)
        nl.setInput(0, bakers[src], idx)
        branch_nodes[name] = nl
    denoise = copnet.createNode("denoiseai", "Denoise_AO")
    denoise.setInput(0, branch_nodes["BaseColor"])
    branch_nodes["BaseColor"] = denoise
    copnet.layoutChildren()

    outnet = hou.node("/out")
    rop_paths = {}
    for name in CHANNELS:
        rop = outnet.createNode("image", "ROP_OUT_" + name)
        rop.parm("coppath").set(copnet.path() + "/" + branch_nodes[name].name())
        rop.parm("aov1").set("C")
        rop.parm("setres").set(1)
        rop.parm("res1").set(SIZE)
        rop.parm("res2").set(SIZE)
        png = out_dir + "/T_" + stem + "_" + name + ".png"
        rop.parm("copoutput").set(png)
        rop.render()
        rop_paths[name] = png

    hou.hipFile.save(HIP_DIR + "/" + stem + ".hip")
    manifest["meshes"][stem] = {"verdict": "BAKED", "obj": obj_path, "outputs": rop_paths,
                                "ao_gamma": AO_GAMMA.get(stem, 1.0)}
    print("[Bake v2] %s -> %s" % (stem, json.dumps({k: os.path.getsize(v) for k, v in rop_paths.items()})))

with open(LANE + "/copernicus_bake_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=1)
print("[Bake v2] manifest updated")
