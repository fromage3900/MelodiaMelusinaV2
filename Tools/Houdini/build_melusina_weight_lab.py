#!/usr/bin/env python
"""
Build Melusina Weight Lab HIP for Houdini Apprentice.

Two modes:
  --test-sheep     : builds lab for choralsheep.fbx (106 bones) — fast QA loop
  --melusina       : builds for Melusina (465 bones) — same HIP, swapped inputs

Creates:
  /obj/melusina_weight_lab
    geo_import        (File SOP → source FBX)
    geo_import_hi     (File SOP → hi-poly FBX for detail)
    bonecapture       (Bone Capture Biharmonic)
    capture_clean     (Attribute Wrangle: clamp influences, smooth, mirror)
    capture_qa        (Attribute VOP: heatmaps → export as images)
    delta_mush        (Delta Mush for skin sliding)
    export_fbx        (ROP FBX → skinned test)
    export_json       (Python SOP → boneCapture JSON + stats)

Run:
  hython Tools/Houdini/build_melusina_weight_lab.py --out Tools/Houdini/melusina_weight_lab.hipnc --test-sheep
  # or for Melusina:
  hython Tools/Houdini/build_melusina_weight_lab.py --out Tools/Houdini/melusina_weight_lab.hipnc --melusina

If hou unavailable, writes JSON stub.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SRC_TEST_SHEEP = Path("Content/Melodia/Companions/ChoralSheep/choralsheep.fbx")
SRC_TEST_SHEEP_HI = Path("Content/Melodia/Companions/ChoralSheep/choralsheephi.fbx")
SRC_MELUSINA = Path("Content/Melodia/Characters/Melusina/SK_Melusina.fbx")  # placeholder
SRC_MELUSINA_HI = Path("Content/Melodia/Characters/Melusina/SK_Melusina_HiPoly.fbx")

AUDIT_DIR = Path("Saved/Audit/melusina_weight_lab")

def _set_if(node, **parms):
    """Version-portable parm set: H22 renamed/removed several capture parms
    (maxdistance/smoothingiterations/mirrorplane do not exist on H22
    bonecapturebiharmonic). Only set parms the running build exposes."""
    for key, value in parms.items():
        try:
            parm = node.parm(key)
        except Exception:
            continue
        if parm is None:
            continue
        try:
            parm.set(value)
        except Exception:
            continue


def build_with_hou(out: Path, test_sheep: bool = False, melusina: bool = False):
    import hou
    hou.hipFile.clear(suppress_save_prompt=True)

    obj = hou.node("/obj")
    lab = obj.createNode("subnet", "melusina_weight_lab")
    lab.setPosition([0, 0])

    # --- Source geo ---
    src_geo = lab.createNode("geo", "geo_import")
    src_geo.setPosition([0, 0])
    file_sop = src_geo.createNode("file", "import_fbx")
    if test_sheep:
        fbx = SRC_TEST_SHEEP
        hi_fbx = SRC_TEST_SHEEP_HI
    elif melusina:
        fbx = SRC_MELUSINA
        hi_fbx = SRC_MELUSINA_HI
    else:
        fbx = SRC_TEST_SHEEP
        hi_fbx = SRC_TEST_SHEEP_HI
    file_sop.parm("file").set(str(fbx.resolve()).replace("\\", "/"))

    # Hi-poly import for detail transfer
    hi_geo = lab.createNode("geo", "geo_import_hi")
    hi_geo.setPosition([0, -2])
    hi_file = hi_geo.createNode("file", "import_hi")
    hi_file.parm("file").set(str(hi_fbx.resolve()).replace("\\", "/"))

    # --- Bone Capture Biharmonic ---
    cap_geo = lab.createNode("geo", "bonecapture")
    cap_geo.setPosition([3, 0])
    obj_merge = cap_geo.createNode("object_merge", "from_import")
    obj_merge.parm("objpath1").set("/obj/melusina_weight_lab/geo_import")

    # Bone Capture Biharmonic node
    bih = None
    for t in ("bonecapturebiharmonic", "bonecapture::2.0", "bonecapture"):
        try:
            bih = cap_geo.createNode(t, "bonecapture_biharmonic")
            break
        except Exception:
            continue
    if bih is None:
        raise RuntimeError("Bone Capture Biharmonic node type not found in this Houdini version")
    bih.setInput(0, obj_merge)
    # H22 requires a second (region) source on input 1; stage it from the same
    # import. Capture quality tuning (closed solid, skeleton regions) is a later
    # pass — staging must cook end-to-end first.
    region_merge = cap_geo.createNode("object_merge", "from_import_region")
    region_merge.parm("objpath1").set("/obj/melusina_weight_lab/geo_import")
    region_merge.setPosition([1, -1])
    # Region input must be tetrahedra: clean -> SDF -> tet chain (guarded parms).
    region_chain = region_merge
    for node_type, node_name in (("clean", "region_clean"),
                                 ("isooffset", "region_sdf"),
                                 ("tetrahedralize", "region_tets")):
        try:
            nxt = cap_geo.createNode(node_type, node_name)
        except Exception:
            nxt = None
        if nxt is None:
            break
        nxt.setInput(0, region_chain)
        nxt.setPosition([1, -2 - len(region_chain.outputConnections())])
        region_chain = nxt
    bih.setInput(1, region_chain)
    # H22 parm set (maxiter/difftol/blendfactor); legacy names no-op via _set_if.
    _set_if(bih, maxdistance=0, smoothingiterations=3 if test_sheep else 5,
            mirrorplane=0, mirrorprefix="L_", mirrorsuffix="R_",
            maxiter=100, difftol=1e-4)

    # --- Capture Clean: clamp 4 influences, smooth ---
    clean = cap_geo.createNode("attribwrangle", "capture_clean")
    clean.setInput(0, bih)
    clean.parm("class").set(0)  # point
    clean.parm("snippet").set(
        "// Doctor-staged: guarantee canonical capture attribs so QA always cooks.\n"
        "// i@capture_missing=1 means no skeleton reached this lab (wire joints next).\n"
        "int has_w = haspointattrib(0, \"boneCapture\");\n"
        "int has_i = haspointattrib(0, \"boneCaptureIndex\");\n"
        "if (!has_w) f[]@boneCapture = {};\n"
        "if (!has_i) i[]@boneCaptureIndex = {};\n"
        "i@capture_missing = (!has_w || !has_i) ? 1 : 0;\n"
        "if (has_w && has_i) {\n"
        "// Clamp to max 4 influences per point\n"
        "int max_inf = 4;\n"
        "int n = len(p[]@boneCapture);\n"
        "if (n > max_inf) {\n"
        "  // Keep top 4 by weight\n"
        "  float weights[] = p[]@boneCapture;\n"
        "  int indices[] = p[]@boneCaptureIndex;\n"
        "  // sort by weight desc (simple bubble for small n)\n"
        "  for (int i=0; i<n-1; i++) {\n"
        "    for (int j=i+1; j<n; j++) {\n"
        "      if (weights[i] < weights[j]) {\n"
        "        float tw = weights[i]; weights[i] = weights[j]; weights[j] = tw;\n"
        "        int ti = indices[i]; indices[i] = indices[j]; indices[j] = ti;\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "  resize(weights, max_inf);\n"
        "  resize(indices, max_inf);\n"
        "  // renormalize\n"
        "  float sum = 0; foreach(float w; weights) sum += w;\n"
        "  if (sum > 0) foreach(int i; weights) weights[i] /= sum;\n"
        "  p[]@boneCapture = weights;\n"
        "  p[]@boneCaptureIndex = indices;\n"
        "}\n"
        "} // end has_w && has_i — without a skeleton the canonical empties stand\n"
        "// Smooth capture weights per bone group (optional: add attribute blur later)"
    )

    # --- Capture QA: heatmaps ---
    qa_geo = lab.createNode("geo", "capture_qa")
    qa_geo.setPosition([6, 0])
    qa_merge = qa_geo.createNode("object_merge", "from_clean")
    qa_merge.parm("objpath1").set("/obj/melusina_weight_lab/bonecapture/capture_clean")

    # Heatmap 1: zero weight verts
    zero_heat = qa_geo.createNode("attribwrangle", "zero_weight_heatmap")
    zero_heat.setInput(0, qa_merge)
    zero_heat.parm("class").set(0)
    zero_heat.parm("snippet").set(
        "// Output: f@zero_weight = 1 if all weights ~0 else 0\n"
        "float sum = 0;\n"
        "foreach(float w; p[]@boneCapture) sum += w;\n"
        "f@zero_weight = (sum < 0.001) ? 1.0 : 0.0;\n"
    )

    # Heatmap 2: influence count
    inf_heat = qa_geo.createNode("attribwrangle", "influence_count_heatmap")
    inf_heat.setInput(0, qa_merge)
    inf_heat.parm("class").set(0)
    inf_heat.parm("snippet").set(
        "f@influence_count = len(p[]@boneCapture);\n"
        "f@over_influence = (f@influence_count > 4) ? 1.0 : 0.0;\n"
    )

    # Heatmap 3: stretch (approximate via capture distance to bone)
    stretch = qa_geo.createNode("attribwrangle", "stretch_heatmap")
    stretch.setInput(0, qa_merge)
    stretch.parm("snippet").set(
        "// Approximate stretch: max distance to captured bones\n"
        "// For now output capture weight variance as proxy\n"
        "float sum = 0, sumsq = 0;\n"
        "foreach(float w; p[]@boneCapture) { sum += w; sumsq += w*w; }\n"
        "float mean = sum / max(1, len(p[]@boneCapture));\n"
        "float variance = sumsq / max(1, len(p[]@boneCapture)) - mean*mean;\n"
        "f@capture_variance = variance;\n"
    )

    # Null output for QA
    qa_out = qa_geo.createNode("null", "OUT_QA")
    qa_out.setInput(0, stretch)
    qa_out.setDisplayFlag(True)
    qa_out.setRenderFlag(True)

    # --- Delta Mush (optional, for skin sliding) ---
    mush_geo = lab.createNode("geo", "delta_mush")
    mush_geo.setPosition([3, -3])
    mush_merge = mush_geo.createNode("object_merge", "from_clean")
    mush_merge.parm("objpath1").set("/obj/melusina_weight_lab/bonecapture/capture_clean")

    deltamush = None
    for t in ("deltamush::2.0", "deltamush"):
        try:
            deltamush = mush_geo.createNode(t, "deltamush")
            break
        except Exception:
            continue
    if deltamush:
        deltamush.setInput(0, mush_merge)
        _set_if(deltamush, iterations=5 if test_sheep else 8, stepsize=0.5)
        mush_out = mush_geo.createNode("null", "OUT_DELTAMUSH")
        mush_out.setInput(0, deltamush)
        mush_out.setDisplayFlag(True)
        mush_out.setRenderFlag(True)
    else:
        # fallback: just pass through
        mush_out = mush_geo.createNode("null", "OUT_DELTAMUSH")
        mush_out.setInput(0, mush_merge)

    # --- ROP FBX Export (test skinned mesh) ---
    out_net = hou.node("/out")
    if out_net is None:
        out_net = hou.node("/").createNode("ropnet", "out")
    rop = None
    for rop_type in ("rop_fbx", "filmboxfbx"):  # rop_fbx absent in H22 builds; filmboxfbx is the port
        try:
            rop = out_net.createNode(rop_type, "export_test_skinned")
            break
        except Exception:
            continue
    if rop is None:
        raise RuntimeError("No FBX ROP type available (tried rop_fbx, filmboxfbx)")
    _set_if(rop, soppath="/obj/melusina_weight_lab/delta_mush/OUT_DELTAMUSH",
            filename="$HIP/../../Saved/Audit/melusina_weight_lab/test_skinned.fbx",
            sopoutput="$HIP/../../Saved/Audit/melusina_weight_lab/test_skinned.fbx",
            exportskin=True, skindeform=True)

    # --- Python SOP for JSON export ---
    json_geo = lab.createNode("geo", "export_json")
    json_geo.setPosition([6, -3])
    json_merge = json_geo.createNode("object_merge", "from_clean")
    json_merge.parm("objpath1").set("/obj/melusina_weight_lab/bonecapture/capture_clean")

    py_sop = json_geo.createNode("python", "export_capture_json")
    py_sop.setInput(0, json_merge)
    py_sop.parm("python").set(r'''
import json, hou
node = hou.pwd()
geo = node.geometry()
audit = hou.expandString("$HIP/../../Saved/Audit/melusina_weight_lab")
import os; os.makedirs(audit, exist_ok=True)

# Per-point capture
capture_data = []
zero_count = 0
over_count = 0
max_inf = 0
def _av(pt, name):
    # hou cannot attribValue() a zero-length array attrib — treat as empty.
    try:
        v = pt.attribValue(name)
        return list(v) if v else []
    except Exception:
        return []
for pt in geo.points():
    idx = _av(pt, "boneCaptureIndex")
    w = _av(pt, "boneCapture")
    if not w or sum(w) < 0.001:
        zero_count += 1
    if len(idx) > 4:
        over_count += 1
    if len(idx) > max_inf:
        max_inf = len(idx)
    capture_data.append({
        "pt": pt.number(),
        "indices": list(idx) if idx else [],
        "weights": list(w) if w else [],
    })

# Bone stats
# Sum weights per bone index
bone_sums = {}
for cd in capture_data:
    for i, wi in zip(cd["indices"], cd["weights"]):
        bone_sums[i] = bone_sums.get(i, 0.0) + wi

stats = {
    "total_points": len(capture_data),
    "zero_weight_count": zero_count,
    "over_influence_count": over_count,
    "max_influences_per_point": max_inf,
    "bones_used": len(bone_sums),
    "bone_weight_sums": {str(k): v for k, v in sorted(bone_sums.items())},
}

with open(os.path.join(audit, "capture_stats.json"), "w") as f:
    json.dump(stats, f, indent=2)

# Also write full capture if small enough (sheep test)
if len(capture_data) < 20000:
    with open(os.path.join(audit, "boneCapture.json"), "w") as f:
        json.dump(capture_data, f)

print(f"[export_json] points={len(capture_data)} zero={zero_count} over4={over_count}")
''')

    hou.hipFile.save(str(out))
    print(f"[weight_lab] saved {out} (test_sheep={test_sheep}, melusina={melusina})")
    return True

def build_stub(out: Path, test_sheep: bool, melusina: bool):
    out.parent.mkdir(parents=True, exist_ok=True)
    stub = out.with_suffix(".json")
    data = {
        "schema": "melodia.houdini_weight_lab.v1",
        "note": "hou unavailable - JSON stub; run with hython to materialize",
        "hip": str(out),
        "mode": "test_sheep" if test_sheep else ("melusina" if melusina else "unknown"),
        "obj": "/obj/melusina_weight_lab",
        "nodes": [
            "geo_import (File → source FBX)",
            "geo_import_hi (File → hi-poly FBX)",
            "bonecapture/bonecapture_biharmonic (Bone Capture Biharmonic)",
            "bonecapture/capture_clean (Attribute Wrangle: clamp 4, smooth, mirror)",
            "capture_qa/zero_weight_heatmap (AttribWrangle: f@zero_weight)",
            "capture_qa/influence_count_heatmap (AttribWrangle: f@influence_count, f@over_influence)",
            "capture_qa/stretch_heatmap (AttribWrangle: f@capture_variance)",
            "delta_mush (Delta Mush SOP)",
            "/out/export_test_skinned (ROP FBX → test_skinned.fbx)",
            "export_json/python (Python SOP → capture_stats.json + boneCapture.json)",
        ],
        "audit_outputs": [
            "Saved/Audit/melusina_weight_lab/capture_stats.json",
            "Saved/Audit/melusina_weight_lab/boneCapture.json (if <20k pts)",
            "Saved/Audit/melusina_weight_lab/test_skinned.fbx",
        ],
        "scale_to_melusina_params": {
            "source_fbx": "Content/Melodia/Characters/Melusina/SK_Melusina.fbx",
            "source_hi_fbx": "Content/Melodia/Characters/Melusina/SK_Melusina_HiPoly.fbx",
            "bonecapture.smoothingiterations": 5,
            "bonecapture.maxdistance": "auto (set per-bone radius)",
            "delta_mush.iterations": 8,
            "capture_clean.max_inf": 4,
            "mirror": "XY plane, prefix L_, suffix R_",
            "regions": "add Bone Capture Regions for hair/face/cloth separate capture",
        },
        "next": "hython Tools/Houdini/build_melusina_weight_lab.py --out Tools/Houdini/melusina_weight_lab.hipnc --test-sheep",
    }
    stub.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out.write_bytes(b"# Houdini Weight Lab HIPNC stub - run with hython to populate\n")
    print(f"[weight_lab] hou not available - wrote stub {stub}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="Tools/Houdini/melusina_weight_lab.hipnc")
    ap.add_argument("--test-sheep", action="store_true", help="build for choralsheep.fbx (106 bones)")
    ap.add_argument("--melusina", action="store_true", help="build for Melusina (465 bones)")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import hou
        build_with_hou(out, test_sheep=args.test_sheep, melusina=args.melusina)
    except ImportError:
        build_stub(out, args.test_sheep, args.melusina)
    except Exception as e:
        print(f"[weight_lab] build failed: {e}")
        import traceback; traceback.print_exc()
        try: build_stub(out, args.test_sheep, args.melusina)
        except Exception: raise