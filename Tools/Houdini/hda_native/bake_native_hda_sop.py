"""Bake a source HDA into a native **SOP-level** HDA with no PythonModule.

The first native pass created an *Object-level* HDA by calling
``createDigitalAsset`` on the Object ``geo``. The source assets are SOP-level
HDAs, and the Object-level shape doubled the cooked height in the UE Houdini
Engine import (source bbox y=7.78, UE z=15.61). This tool keeps the same
cook-once/stash strategy but publishes a SOP-level HDA:

  source HDA (Sop) -> cook -> stash(stashinput) -> null OUT
  -> copy stash+OUT into a SOP subnet -> subnet.createDigitalAsset()
  -> native SOP HDA (no PythonModule)

Usage:
  hython bake_native_hda_sop.py <source.hda> <output_native.hda> <new_type>

The source's primitive attributes/groups are preserved by the stash. The source
HDA parameter interface is intentionally not retained; this is a fixed-geometry
runtime delivery, not an authoring replacement.
"""
import json
import os
import sys

import hou


def _vec(v):
    return [round(float(x), 6) for x in v]


def _geo_info(g):
    if g is None:
        return None
    bb = g.boundingBox()
    info = {
        "points": len(g.points()),
        "prims": len(g.prims()),
        "bbox_min": _vec(bb.minvec()),
        "bbox_max": _vec(bb.maxvec()),
        "bbox_size": _vec(bb.sizevec()),
    }
    for attr_name in ("material_role", "unreal_material"):
        attr = g.findPrimAttrib(attr_name)
        if attr is not None:
            counts = {}
            for prim in g.prims():
                value = str(prim.attribValue(attr_name))
                counts[value] = counts.get(value, 0) + 1
            info[attr_name + "_counts"] = counts
    return info


def bake(src_path, out_path, new_type, overrides=None):
    receipt_path = os.path.splitext(out_path)[0] + "_receipt.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    overrides = overrides or {}

    hou.hda.installFile(src_path)
    defs = hou.hda.definitionsInFile(src_path)
    if not defs:
        raise RuntimeError("no HDA definitions in " + src_path)
    src_type = defs[0].nodeTypeName()
    src_category = defs[0].nodeTypeCategory().name()

    holder = hou.node("/obj").createNode("geo", "bake_holder")
    src = holder.createNode(src_type, "src_node")
    applied_overrides = {}
    for parm_name, value in overrides.items():
        parm = src.parm(parm_name)
        if parm is None:
            print("OVERRIDE_SKIP", parm_name, "not present on", src_type)
            continue
        parm.set(value)
        applied_overrides[parm_name] = value
    if applied_overrides:
        print("OVERRIDES", applied_overrides)
    src.cook(force=True)
    src_errors = [str(e) for e in src.errors()]
    src_geo = _geo_info(src.geometry())
    if not src_geo:
        raise RuntimeError("source produced no geometry")

    stash = holder.createNode("stash", "geometry_stash")
    stash.setInput(0, src)
    stash.cook(force=True)
    try:
        stash.parm("stashinput").pressButton()
    except Exception as exc:
        raise RuntimeError("stashinput failed: %s" % exc)
    out = holder.createNode("null", "OUT")
    out.setInput(0, stash)
    out.cook(force=True)
    stash_geo = _geo_info(stash.geometry())
    out_geo = _geo_info(out.geometry())
    src.destroy()

    net = holder.createNode("subnet", "native_net")
    copies = hou.copyNodesTo([stash, out], net)
    by_name = {c.name(): c for c in copies}
    copied_stash = by_name.get("geometry_stash")
    copied_out = by_name.get("OUT")
    if copied_stash is None or copied_out is None:
        raise RuntimeError("copyNodesTo did not return geometry_stash/OUT: %s" % list(by_name))
    copied_out.setDisplayFlag(True)
    copied_stash.setDisplayFlag(False)
    stash.destroy()
    out.destroy()

    net.createDigitalAsset(
        name=new_type,
        hda_file_name=out_path,
        description="Native SOP baked " + os.path.basename(src_path) + " (no PythonModule)",
        min_num_inputs=0,
        max_num_inputs=0,
        version="1.0",
    )

    out_defs = hou.hda.definitionsInFile(out_path)
    out_def = out_defs[0]
    sections = sorted(out_def.sections().keys())
    category = out_def.nodeTypeCategory().name()
    has_python = any("Python" in s for s in sections)

    probe_holder = hou.node("/obj").createNode("geo", "native_probe_holder")
    probe = probe_holder.createNode(out_def.nodeTypeName(), "native_probe")
    probe.cook(force=True)
    probe_errors = [str(e) for e in probe.errors()]
    native_geo = _geo_info(probe.geometry())
    display = probe.displayNode()

    receipt = {
        "source": src_path,
        "source_type": src_type,
        "source_category": src_category,
        "source_parm_overrides": applied_overrides,
        "source_points": src_geo["points"],
        "source_prims": src_geo["prims"],
        "source_bbox_min": src_geo["bbox_min"],
        "source_bbox_max": src_geo["bbox_max"],
        "source_errors": src_errors,
        "stash_points": stash_geo["points"] if stash_geo else None,
        "stash_prims": stash_geo["prims"] if stash_geo else None,
        "stash_bbox_size": stash_geo["bbox_size"] if stash_geo else None,
        "out_points": out_geo["points"] if out_geo else None,
        "out_prims": out_geo["prims"] if out_geo else None,
        "output": out_path,
        "new_type": out_def.nodeTypeName(),
        "new_category": category,
        "sections": sections,
        "has_python_module": has_python,
        "native_points": native_geo["points"] if native_geo else None,
        "native_prims": native_geo["prims"] if native_geo else None,
        "native_bbox_min": native_geo["bbox_min"] if native_geo else None,
        "native_bbox_max": native_geo["bbox_max"] if native_geo else None,
        "native_bbox_size": native_geo["bbox_size"] if native_geo else None,
        "native_material_role_counts": native_geo.get("material_role_counts") if native_geo else None,
        "native_unreal_material_counts": native_geo.get("unreal_material_counts") if native_geo else None,
        "probe_errors": probe_errors,
        "display": display.name() if display else None,
        "ok": (
            not has_python
            and category == "Sop"
            and native_geo is not None
            and native_geo["points"] == src_geo["points"]
            and native_geo["prims"] == src_geo["prims"]
        ),
    }
    with open(receipt_path, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=1)
    print(json.dumps(receipt, indent=2))
    print("RECEIPT", receipt_path)
    return receipt


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(
            "usage: bake_native_hda_sop.py <source.hda> <output.hda> <new_type> "
            "[--engine-y-up 0|1] [--engine-flip 0|1]"
        )
    parsed = {}
    extra = sys.argv[4:]
    index = 0
    while index < len(extra):
        token = extra[index]
        if token in ("--engine-y-up", "--engine-flip") and index + 1 < len(extra):
            parsed[token.lstrip("-").replace("-", "_")] = float(extra[index + 1])
            index += 2
        else:
            raise SystemExit("unknown argument: " + token)
    result = bake(sys.argv[1], sys.argv[2], sys.argv[3], overrides=parsed)
    if not result["ok"]:
        raise SystemExit(2)
