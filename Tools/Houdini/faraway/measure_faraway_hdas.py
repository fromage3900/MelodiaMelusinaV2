r"""measure_faraway_hdas.py -- measured post-cook bounds / outputs / controls of the 8 Faraway HDAs (hython 22.0.368). spike: true

One HDA at a time, defaults only, no UE. Writes <out>/hda_measure.json (+ manifest line). Measured bounds are the
authority for placement footprints (handoff: params, staged boxes and docs disagree).

Usage: hython Tools/Houdini/faraway/measure_faraway_hdas.py [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NAMES = ["HeartGate", "FrillArch", "LaceBridge", "SilkPeak", "SilkRibbon", "MotherfoldBasin", "TerracedIsland", "ListeningOrchardTree"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayMeasure_20261026"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    import hou

    res = {}
    for n in NAMES:
        f = ROOT / "hda" / f"HDA_Faraway_{n}_1.0.hda"
        rec = {"hda": str(f.relative_to(ROOT)), "sha": hashlib.sha256(f.read_bytes()).hexdigest()[:16]}
        try:
            hou.hda.installFile(str(f))
            obj = hou.node("/obj")
            old = obj.node("M_" + n)
            if old:
                old.destroy()
            t = time.time()
            node = obj.createNode(f"HDA_Faraway_{n}", "M_" + n)
            node.cook(force=True)
            rec["cook_s"] = round(time.time() - t, 2)
            rec["errors"] = list(node.errors())
            rec["controls"] = {p.name(): (p.eval() if p.parmTemplate().type() != hou.parmTemplateType.Folder else None)
                               for p in node.parms() if p.name() not in ("stdswitcher1",)}
            outs = []
            for ch in node.children():
                if ch.type().name() == "output" or ch.name().lower().startswith("output"):
                    outs.append(ch)
            outs.sort(key=lambda c: c.name())
            rec["outputs"] = []
            for o in outs:
                try:
                    g = o.geometry()
                except Exception as exc:
                    rec["outputs"].append({"node": o.name(), "error": str(exc)})
                    continue
                if g is None:
                    continue
                bb = g.boundingBox()
                attrs = sorted(x.name() for x in g.primAttribs()) + sorted(x.name() for x in g.pointAttribs()) + sorted(x.name() for x in g.globalAttribs())
                mat = sorted({p.attribValue("unreal_material") for p in g.prims()} if g.findPrimAttrib("unreal_material") else [])
                rec["outputs"].append({
                    "node": o.name(), "pts": len(g.points()), "prims": len(g.prims()),
                    "min": [round(v, 3) for v in bb.minvec()], "max": [round(v, 3) for v in bb.maxvec()],
                    "size": [round(v, 3) for v in bb.sizevec()],
                    "unreal_material": mat[:6], "attribs": attrs[:30],
                })
            rec["display_bbox_size"] = None
            try:
                g = node.displayNode().geometry()
                rec["display_bbox_size"] = [round(v, 3) for v in g.boundingBox().sizevec()]
            except Exception:
                pass
            node.destroy()
        except Exception as exc:
            rec["fail"] = str(exc)[:300]
        res[n] = rec
        print(n, rec.get("cook_s"), rec.get("fail", ""), [o.get("size") for o in rec.get("outputs", [])][:2])

    doc = {"schema": "melodia.faraway_hda_measure.spike.v1", "spike": True, "houdini": hou.applicationVersionString(),
           "license": str(hou.licenseCategory()), "units": "m, Houdini Y-up local", "hdas": res}
    (out / "hda_measure.json").write_text(json.dumps(doc, indent=1))
    ok = all("fail" not in r and r.get("outputs") for r in res.values())
    print("GATE", json.dumps({"all_cooked": ok, "count": len(res)}))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
