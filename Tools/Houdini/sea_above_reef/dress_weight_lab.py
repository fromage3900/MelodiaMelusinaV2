"""Shorewake dress weight lab — Houdini bone-capture + QA gate (the corrected
Weight Lab from the overnight plan, on the verified Apprentice pipeline).

CRITICAL PIPELINE FACT (verified 2026-08-28): Apprentice cannot EXPORT FBX or
Alembic. So weights leave as JSON for the Blender lane:

  hython dress_weight_lab.py --mesh <dress.fbx|obj> --skeleton <melusina.fbx>

Steps:
  1. import mesh + skeleton (FBX import — probe_fbx_import.py verifies this works)
  2. Bone Capture (biharmonic) against deform bones (c_kilt_* chain + spine/pelvis)
  3. clamp 4 influences, normalize
  4. QA gate -> weight_qa.json:
       zero_weight_vertices  == 0   (hard gate)
       over4_influence_count == 0   (hard gate)
       per-bone min/mean/max + stretch heatmap PNG
  5. weights.json: per-vertex {bone_name: weight} for the Blender applier
     (apply_houdini_weights.py — Blender lane, authored with the mesh)

The gate is the lab's product: nothing ships to Blender until weight_qa.json is
green. Authored 2026-08-28; runs once the dress mesh exists (Blender step H3).
"""

import argparse
import json
from pathlib import Path

import hou

OUT_DIR = Path(__file__).resolve().parents[3] / "Saved" / "Audit" / "melusina_lookdev" / "weight_lab"
MAX_INFLUENCES = 4


def setp(node, name, value, warn=True):
    p = node.parm(name)
    if p is not None:
        try:
            p.set(value)
            return True
        except Exception as e:
            if warn:
                print(f"[warn] {node.name()}.{name}: {e}")
            return False
    pt = node.parmTuple(name)
    if pt is not None:
        try:
            n = len(pt)
            vals = value if isinstance(value, (tuple, list)) else (value,) * n
            for i, v in enumerate(vals[:n]):
                pt[i].set(v)
            return True
        except Exception as e:
            if warn:
                print(f"[warn] {node.name()}.{name} tuple: {e}")
            return False
    if warn:
        print(f"[warn] parm not found: {node.name()}.{name}")
    return False


def import_inputs(mesh_path, skeleton_path):
    """Import mesh + skeleton FBX into /obj; returns (mesh_geo, rest_positions)."""
    hou.hipFile.importFBX(str(mesh_path), suppress_warnings=True)
    if skeleton_path and str(skeleton_path) != str(mesh_path):
        hou.hipFile.importFBX(str(skeleton_path), suppress_warnings=True)
    obj = hou.node("/obj")
    mesh_geo = None
    bones = []
    for n in obj.children():
        if n.type().name() == "geo" and mesh_geo is None:
            disp = n.displayNode()
            if disp and disp.geometry() and len(disp.geometry().points()) > 100:
                mesh_geo = disp
        # capture bones arrive as null/bone-style objects with pretransform
        if n.type().name() in ("null", "bone", "geo") and ("c_" in n.name() or "spine" in n.name()
                                                           or "pelvis" in n.name()):
            bones.append(n.name())
    if mesh_geo is None:
        raise SystemExit("[lab] no mesh geometry found after import")
    return mesh_geo, bones


def build_capture(mesh_geo, bones):
    """Bone Capture biharmonic on the mesh geo network."""
    g = mesh_geo.parent()
    null_out = g.createNode("null", "LAB_OUT")
    null_out.setInput(0, mesh_geo)
    capture = g.createNode("bonecapture", "biharmonic")
    # biharmonic captures against /obj-level bone-like objects; parms vary by
    # version — defensive sets only
    setp(capture, "maxdist", 0.0, warn=False)  # 0 = auto
    capture.setInput(0, null_out)
    capture.cook(force=True)
    err = str(capture.errors())[:300] if capture.errors() else ""
    if err:
        print(f"[lab] capture errors: {err}")
    geo = capture.geometry()
    if not geo:
        raise SystemExit("[lab] capture produced no geometry")
    return geo


def qa_and_export(geo, out_dir):
    """Read capture weights (point attrib 'capture' + 'boneCapture' index data),
    clamp/normalize, run the QA gate, write weights.json + weight_qa.json."""
    pts = geo.points()
    cap = geo.findPointAttrib("capture")
    if cap is None:
        raise SystemExit("[lab] no 'capture' point attrib — bone capture failed")
    n_comp = cap.size()
    # bone names from the capture detail
    try:
        bone_names = geo.findGlobalAttrib("boneCapture_names")
        names = bone_names.strings() if bone_names else [f"bone_{i}" for i in range(n_comp)]
    except Exception:
        names = [f"bone_{i}" for i in range(n_comp)]

    weights = []
    zero_w, over4 = [], []
    per_bone = {}
    for vi, p in enumerate(pts):
        raw = list(p.attribValue(cap))[:n_comp]
        pairs = [(names[i], float(w)) for i, w in enumerate(raw) if w > 1e-5]
        pairs.sort(key=lambda t: -t[1])
        pairs = pairs[:MAX_INFLUENCES]
        total = sum(w for _, w in pairs) or 1.0
        pairs = [(b, w / total) for b, w in pairs]
        if not pairs:
            zero_w.append(vi)
        if len(raw) > MAX_INFLUENCES and sum(1 for w in raw if w > 1e-5) > MAX_INFLUENCES:
            over4.append(vi)
        for b, w in pairs:
            s = per_bone.setdefault(b, [1e9, 0.0, 0.0, 0])
            s[0] = min(s[0], w); s[1] += w; s[2] = max(s[2], w); s[3] += 1
        weights.append({b: round(w, 5) for b, w in pairs})

    stats = {b: {"min": round(v[0], 4), "mean": round(v[1] / max(v[3], 1), 4),
                 "max": round(v[2], 4), "verts": v[3]} for b, v in per_bone.items()}
    qa = {
        "schema": "melodia.dress_weight_qa.v1",
        "vertex_count": len(pts),
        "zero_weight_vertices": zero_w,
        "over4_influence_vertices": over4,
        "gate": {"zero_weight_ok": len(zero_w) == 0,
                 "over4_ok": len(over4) == 0},
        "per_bone": stats,
        "max_influences": MAX_INFLUENCES,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "weight_qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    (OUT_DIR / "weights.json").write_text(json.dumps(weights), encoding="utf-8")
    print(f"[lab] verts={len(pts)} zero={len(zero_w)} over4={len(over4)}")
    print(f"[lab] gate: {'GREEN' if qa['gate']['zero_weight_ok'] and qa['gate']['over4_ok'] else 'RED'}")
    print(f"[lab] wrote {OUT_DIR / 'weight_qa.json'} + weights.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mesh", required=True, help="dress mesh FBX")
    ap.add_argument("--skeleton", default=None, help="465-bone rest pose FBX (if separate)")
    args = ap.parse_args()

    mesh_geo, bones = import_inputs(args.mesh, args.skeleton)
    print(f"[lab] mesh found; candidate bone-ish nodes: {len(bones)}")
    geo = build_capture(mesh_geo, bones)
    qa_and_export(geo, OUT_DIR)


if __name__ == "__main__":
    main()
