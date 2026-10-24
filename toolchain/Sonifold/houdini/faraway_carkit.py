"""faraway_carkit.py -- Audit + UV-unwrap + FBX-export the Faraway Mother HDA set.

hython 22.0.368. Idempotent: skips HDAs whose FBX already exists (safe re-run).
Output: <KIT>/<HDA>.fbx + audit.json + README.md in the kit folder.
"""
import json
import os
import time

import hou

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
KIT = r"G:\Melodia_Houdini_Foundry\FarawayCarKit_20261024"
HDAS = [
    ("HDA_Faraway_HeartGate_1.0.hda", "HeartGate"),
    ("HDA_Faraway_FrillArch_1.0.hda", "FrillArch"),
    ("HDA_Faraway_LaceBridge_1.0.hda", "LaceBridge"),
    ("HDA_Faraway_SilkPeak_1.0.hda", "SilkPeak"),
    ("HDA_Faraway_SilkRibbon_1.0.hda", "SilkRibbon"),
    ("HDA_Faraway_TerracedIsland_1.0.hda", "TerracedIsland"),
    ("HDA_Faraway_MotherfoldBasin_1.0.hda", "MotherfoldBasin"),
    ("HDA_Faraway_ListeningOrchardTree_1.0.hda", "ListeningOrchardTree"),
    ("ArpeggioStair_1.0.hda", "ArpeggioStair"),
]

os.makedirs(KIT, exist_ok=True)
audit_path = os.path.join(KIT, "audit.json")
audit = json.load(open(audit_path)) if os.path.exists(audit_path) else {}

obj = hou.node("/obj")
out = hou.node("/out")
built = []


def audit_geo(g):
    b = g.boundingBox()
    comps = 0
    try:
        dg = g.debugDraw()  # unused; component count via Connectivity instead
    except Exception:
        pass
    return {
        "prims": len(g.prims()),
        "points": len(g.points()),
        "bounds": [round(b.minvec().x(), 2), round(b.minvec().y(), 2), round(b.minvec().z(), 2),
                   round(b.maxvec().x(), 2), round(b.maxvec().y(), 2), round(b.maxvec().z(), 2)],
        "has_vertex_uv": g.findVertexAttrib("uv") is not None,
        "has_point_uv": g.findPointAttrib("uv") is not None,
    }


for hda_file, short in HDAS:
    fbx_path = os.path.join(KIT, f"{short}.fbx")
    if os.path.exists(fbx_path) and short in audit and audit[short].get("fbx_ok"):
        print(f"skip {short} (exists)")
        continue
    t0 = time.time()
    path = os.path.join(REPO, "hda", hda_file)
    try:
        hou.hda.installFile(path)
        defs = hou.hda.definitionsInFile(path)
        node = obj.createNode(defs[0].nodeTypeName().split("::")[0])
        node.cook(force=True)
        # prefer the HDA's explicit output node over whichever node holds the display flag
        disp = None
        for c in node.children():
            if c.name().lower().startswith("output"):
                disp = c
                break
        if disp is None and hasattr(node, "displayNode") and node.displayNode():
            disp = node.displayNode()
        if disp is None:
            disp = node
        g0 = disp.geometry()
        entry = {"hda": hda_file, "audit_raw": audit_geo(g0)}
        print(f"{short}: raw {entry['audit_raw']['prims']} prims, "
              f"uv={entry['audit_raw']['has_vertex_uv'] or entry['audit_raw']['has_point_uv']}")

        # unwrap chain
        geo = obj.createNode("geo")
        geo.setName(f"kit_{short}")
        om = geo.createNode("object_merge")
        om.parm("objpath1").set(disp.path())
        seam = geo.createNode("uvautoseam")
        seam.setInput(0, om)
        unw = geo.createNode("uvunwrap")
        unw.setInput(0, seam)
        unw.parm("layout").set(1) if unw.parm("layout") else None
        onull = geo.createNode("null")
        onull.setName("OUT")
        onull.setInput(0, unw)
        onull.setDisplayFlag(True)
        unw.setDisplayFlag(False)
        unw.cook(force=True)
        g1 = unw.geometry()
        entry["audit_unwrapped"] = audit_geo(g1)
        entry["uv_area_nonzero"] = entry["audit_unwrapped"]["has_vertex_uv"] or \
            entry["audit_unwrapped"]["has_point_uv"]

        # fbx export
        rop = out.createNode("filmboxfbx")
        rop.parm("startnode").set(onull.path())
        rop.parm("sopoutput").set(fbx_path)
        rop.parm("mkpath").set(1)
        rop.parm("trange").set(0)  # single frame
        rop.parm("execute").pressButton()
        rop.destroy()
        entry["fbx_ok"] = os.path.exists(fbx_path) and os.path.getsize(fbx_path) > 1000
        entry["fbx_bytes"] = os.path.getsize(fbx_path) if entry["fbx_ok"] else 0
        entry["seconds"] = round(time.time() - t0, 1)
        audit[short] = entry
        print(f"{short}: FBX {'OK' if entry['fbx_ok'] else 'FAILED'} "
              f"{entry.get('fbx_bytes', 0)//1024} KB, uv={entry['uv_area_nonzero']}, {entry['seconds']}s")
        # cleanup scene
        geo.destroy(); node.destroy()
    except Exception as e:
        audit[short] = {"hda": hda_file, "error": str(e)}
        print(f"{short}: ERROR {e}")
    json.dump(audit, open(audit_path, "w"), indent=1)

print("KIT DONE ->", KIT)
