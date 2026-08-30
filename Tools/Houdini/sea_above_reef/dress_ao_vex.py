"""PASS H3 — per-vertex ambient occlusion with self-hit exclusion (Houdini VEX).

Why: Cycles AO on open thin panels self-shadows to black (no self-exclusion),
and Mantra baketexture is watermark-blocked on Apprentice. VEX gives exact
control: cosine-weighted hemisphere rays, hits closer than SELF_BIAS ignored
(grazing self-hits), everything else occludes.

Output: bake/SM_ShorewakeDress_48MAT_v2_ao.obj  (OBJ vertex color R = AO 0..1)
        bake/dress_ao_manifest.json
Run:  hython Tools/Houdini/sea_above_reef/dress_ao_vex.py
"""

import json
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BAKE_DIR = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/bake"
LOW_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2.obj"
OUT_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_ao.obj"
SEED = 20260830
AO_SAMPLES = 64
SELF_BIAS = 0.003   # m: ray start offset along normal
SELF_MIN = 0.002    # m: hits closer than this are grazing self-hits -> ignored

VEX_AO = r"""
vector n = normalize(v@N);
vector up = (abs(n.y) < 0.99) ? {0.0, 1.0, 0.0} : {1.0, 0.0, 0.0};
vector tx = normalize(cross(up, n));
vector ty = normalize(cross(n, tx));
float ao = 0.0;
int ns = chi("samples");
float bias = chf("self_bias");
float minhit = chf("self_min");
float golden = 2.399963229728653;
vector hitp, hituv;
for (int i = 0; i < ns; i++) {
    float t = (i + 0.5) / ns;
    float phi = i * golden;
    float ct = sqrt(1.0 - t);
    float st = sqrt(max(0.0, 1.0 - ct * ct));
    vector dir = normalize(tx * cos(phi) * st + ty * sin(phi) * st + n * ct);
    int hit = intersect(1, @P + n * bias, dir, hitp, hituv);
    if (hit < 0) {
        ao += 1.0;
    } else {
        float d = distance(@P + n * bias, hitp);
        if (d > minhit) ao += 1.0;
    }
}
f@ao = ao / ns;
"""


def build():
    geo = hou.node("/obj").createNode("geo", "dress_ao")
    low = geo.createNode("file", "low")
    low.parm("file").set(LOW_OBJ.as_posix())

    src = geo.createNode("object_merge", "self")
    src.parm("objpath1").set(geo.path())

    ao = geo.createNode("attribwrangle", "ao")
    ao.setInput(0, low)
    ao.setInput(1, src)
    ao.parm("snippet").set(VEX_AO)
    ao.addSpareParmTuple(hou.IntParmTemplate("samples", "samples", 1, default_value=(AO_SAMPLES,)))
    ao.addSpareParmTuple(hou.FloatParmTemplate("self_bias", "self_bias", 1, default_value=(SELF_BIAS,)))
    ao.addSpareParmTuple(hou.FloatParmTemplate("self_min", "self_min", 1, default_value=(SELF_MIN,)))
    ao.parm("samples").set(AO_SAMPLES)
    ao.parm("self_bias").set(SELF_BIAS)
    ao.parm("self_min").set(SELF_MIN)

    enc = geo.createNode("attribwrangle", "encode")
    enc.setInput(0, ao)
    enc.parm("snippet").set("v@Cd = set(f@ao, 0.0, 0.0);")

    rop = geo.createNode("rop_geometry", "out")
    rop.setInput(0, enc)
    rop.parm("sopoutput").set(OUT_OBJ.as_posix())
    rop.parm("execute").pressButton()
    return enc


def main():
    if not LOW_OBJ.exists():
        raise SystemExit("missing %s" % LOW_OBJ)
    enc = build()
    g = enc.geometry()
    pts = len(g.points())
    vals = [p.floatAttribValue("ao") for p in g.points()[:3000]]
    manifest = {
        "schema": "melodia.shorewake_ao_vex.v1",
        "seed": SEED,
        "samples": AO_SAMPLES,
        "self_bias_m": SELF_BIAS,
        "self_min_m": SELF_MIN,
        "points": pts,
        "ao_mean_sample": sum(vals) / len(vals),
        "out_obj": str(OUT_OBJ),
        "encoding": "OBJ vertex color R = AO",
    }
    (BAKE_DIR / "dress_ao_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print("AO_DONE points=%d mean=%.4f" % (pts, manifest["ao_mean_sample"]))


main()
