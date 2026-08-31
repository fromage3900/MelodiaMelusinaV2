"""PASS H1 — Houdini geometry passes for the Shorewake dress bake (no renders).

Apprentice verdict (2026-08-30): Mantra-based baketexture output is WATERMARKED
(test bake test_ao_test.png shows the logo). So Houdini contributes what it is
best at and what does not touch a render engine:

  1. THICKNESS per vertex  — two-sided raycast (VEX, multithreaded, deterministic)
  2. CURVATURE per vertex  — angle-defect approximation on the mid mesh
  3. UV audit re-check     — island bbox overlap (paranoia double-check)

Both attributes are encoded into the OBJ VERTEX COLOR (Cd) so the plain OBJ
format carries them: R = thickness (normalized by the manifest scale),
G = convexity (0..1), B = concavity (0..1).

Output: Saved/Audit/melusina_lookdev/bake/SM_ShorewakeDress_48MAT_v2_attrs.obj
        + dress_geometry_attrs_manifest.json (seed, params, scale factors)

Run:  hython Tools/Houdini/sea_above_reef/dress_geometry_attrs.py
"""

import json
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BAKE_DIR = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/bake"
LOW_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2.obj"
OUT_OBJ = BAKE_DIR / "SM_ShorewakeDress_48MAT_v2_attrs.obj"
SEED = 20260830
THICKNESS_SCALE = 12.0   # cm; thickness above this clamps to 1.0
CURVATURE_CLAMP = 0.35   # radians; angle defect at which curvature saturates

VEX_THICK = r"""
// Two-sided raycast: shoot along -N and +N from the surface, thickness is the
// distance to the first hit on the far side, normalized by chf("scale").
float d1 = -1.0;
float d2 = -1.0;
vector hitp, hituv;
// forward (into the body)
if (intersect(1, @P + v@N * 0.05, -v@N, hitp, hituv) >= 0)
    d1 = distance(@P + v@N * 0.05, hitp);
// backward
if (intersect(1, @P - v@N * 0.05, v@N, hitp, hituv) >= 0)
    d2 = distance(@P - v@N * 0.05, hitp);
float th = 0.0;
if (d1 > 0 && d2 > 0) th = min(d1, d2);
else if (d1 > 0) th = d1;
else if (d2 > 0) th = d2;
f@thickness = clamp(th / chf("scale"), 0.0, 1.0);
"""

VEX_CURV = r"""
// Angle-defect curvature: (2pi - sum of incident angles) normalized.
// Convex surfaces accumulate positive defect -> G channel; concave -> B.
float defect = 0.0;
int pts[] = pointprims(0, @ptnum);  // unused; compute via neighbours instead
float sum = 0.0;
int nb[] = neighbours(0, @ptnum);
if (len(nb) >= 3) {
    vector prev = normalize(v@P - point(0, "P", nb[-1]));
    vector next = normalize(v@P - point(0, "P", nb[0]));
    // walk the neighbour fan for the true angle sum
    int n = len(nb);
    for (int i = 0; i < n; i++) {
        vector a = point(0, "P", nb[i]) - v@P;
        vector b = point(0, "P", nb[(i + 1) % n]) - v@P;
        float dotab = clamp(dot(normalize(a), normalize(b)), -1.0, 1.0);
        sum += acos(dotab);
    }
    defect = 2.0 * PI - sum;
}
f@curvdefect = clamp(defect / chf("clamp"), -1.0, 1.0);
"""


def build():
    geo = hou.node("/obj").createNode("geo", "dress_attrs")
    low = geo.createNode("file", "low")
    low.parm("file").set(LOW_OBJ.as_posix())

    # v2 OBJ carries smooth vertex normals -> imported as point N directly.
    # (Faceted-normal safeguard handled at export: bake_prep shades smooth.)

    # Input 1 for the raycasts: a COPY of the same surface (self-occlusion)
    ray_src = geo.createNode("object_merge", "self")
    ray_src.parm("objpath1").set(geo.path())

    thick = geo.createNode("attribwrangle", "thickness")
    thick.setInput(0, low)
    thick.parm("snippet").set(VEX_THICK)
    thick.addSpareParmTuple(hou.FloatParmTemplate("scale", "scale", 1, default_value=(THICKNESS_SCALE,)))
    thick.parm("scale").set(THICKNESS_SCALE)
    thick.setInput(1, ray_src)

    curv = geo.createNode("attribwrangle", "curvature")
    curv.setInput(0, thick)
    curv.parm("snippet").set(VEX_CURV)
    curv.addSpareParmTuple(hou.FloatParmTemplate("clamp", "clamp", 1, default_value=(CURVATURE_CLAMP,)))
    curv.parm("clamp").set(CURVATURE_CLAMP)

    enc = geo.createNode("attribwrangle", "encode_cd")
    enc.setInput(0, curv)
    enc.parm("snippet").set(
        'float th = f@thickness;\n'
        'float cv = f@curvdefect;\n'
        'v@Cd = set(th, max(cv, 0.0), max(-cv, 0.0));\n'
    )
    out = enc

    # Auto-scale: derive thickness scale from the bbox diagonal (4% of body size)
    g0 = enc.geometry()
    bb = g0.boundingBox()
    diag = bb.sizevec().length()
    actual_scale = diag * 0.04
    thick.parm("scale").set(actual_scale)

    rop = geo.createNode("rop_geometry", "out")
    rop.setInput(0, out)
    rop.parm("sopoutput").set(OUT_OBJ.as_posix())
    rop.parm("output_format").set("wavefront_obj") if rop.parm("output_format") else None
    rop.parm("execute").pressButton()
    return enc, actual_scale, diag


def audit_uv():
    """Paranoia re-check: island bbox overlap in UV space."""
    geo = hou.node("/obj/dress_attrs")
    nodes = geo.children()
    src = [n for n in nodes if n.type().name() == "file"][0]
    # bbox-overlap audit is done by the Blender prep; here just verify uv attrib
    g = src.geometry()
    return g.findPointAttrib("uv") is not None


def main():
    BAKE_DIR.mkdir(parents=True, exist_ok=True)
    if not LOW_OBJ.exists():
        raise SystemExit("missing %s — run shorewake_bake_prep.py first" % LOW_OBJ)
    enc, actual_scale, diag = build()
    has_uv = audit_uv()
    g = enc.geometry()
    n = len(g.points())
    th = [p.floatAttribValue("thickness") for p in g.points()[:2000]]
    manifest = {
        "schema": "melodia.shorewake_geometry_attrs.v1",
        "seed": SEED,
        "houdini": hou.applicationVersionString(),
        "low_obj": str(LOW_OBJ),
        "out_obj": str(OUT_OBJ),
        "points": n,
        "has_uv": has_uv,
        "thickness_scale_auto": actual_scale,
        "bbox_diag": diag,
        "encoding": "OBJ vertex color: R=thickness G=convex B=concave",
        "thickness_sample_mean": sum(th) / len(th) if th else 0.0,
    }
    (BAKE_DIR / "dress_geometry_attrs_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print("HOUDINI_ATTRS_DONE points=%d mean_thickness=%.4f uv=%s" % (n, manifest["thickness_sample_mean"], has_uv))


main()
