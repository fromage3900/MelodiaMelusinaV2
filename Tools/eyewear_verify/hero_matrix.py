"""11.7 delivery run: 6-hero WebGL matrix through the export gate.

3 silhouettes x 2 finishes. Each hero: 5 part GLBs + assembled GLB, all
gate-asserted (non-empty, TEXCOORD_0, COLOR_0, budgets). Writes manifest.json.
NOT a committed harness (delivery ops); the gate is the committed path and
the manifest records every parameter for reproducibility.
"""
import json
import os
import sys

WT = "P:/MelodiaMelusinaV2-Laptop"
sys.path.insert(0, WT + "/deploy")
from surreal_arch.melodia_gn import eyewear as EW  # noqa: E402

BASE = {"Base Curve": 6.0, "Form Angle": 4.4,
        "Top Tint": (0.15, 0.15, 0.18, 1.0),
        "Bottom Tint": (0.90, 0.95, 1.00, 1.0)}
ESP = (0.09, 0.055, 0.045, 1.0)
CHAMP = (0.95, 0.80, 0.60, 1.0)

HEROES = [
    ("rect-tortoise", dict(BASE, **{"Silhouette": 0, "Tortoise": 1.0,
                                    "Metal Frame": False, "Frame Solid": ESP})),
    ("rect-metal", dict(BASE, **{"Silhouette": 0, "Tortoise": 0.0, "Base Curve": 4.0,
                                 "Metal Frame": True, "Frame Solid": CHAMP})),
    ("panto-tortoise", dict(BASE, **{"Silhouette": 1, "Tortoise": 1.0,
                                     "Metal Frame": False, "Frame Solid": ESP})),
    ("panto-metal", dict(BASE, **{"Silhouette": 1, "Tortoise": 0.0, "Base Curve": 4.0,
                                  "Metal Frame": True, "Frame Solid": CHAMP})),
    ("cateye-tortoise", dict(BASE, **{"Silhouette": 2, "Tortoise": 1.0,
                                      "Metal Frame": False, "Frame Solid": ESP})),
    ("cateye-metal", dict(BASE, **{"Silhouette": 2, "Tortoise": 0.0, "Base Curve": 4.0,
                                   "Metal Frame": True, "Frame Solid": CHAMP})),
]

ROOT = os.path.join(WT, "Exports", "EyewearEditorial", "WebGL")
PARTS = ("Frame", "TempleL", "TempleR", "LensL", "LensR")
manifest = {"heroes": {}, "budgets": {"tris": 150000, "bytes": 3 * 1024 * 1024}}
fails = []
for tag, params in HEROES:
    d = os.path.join(ROOT, tag)
    try:
        rep = EW.melodia_eyewear_export_gate(d, parts=PARTS, params=params)
        rep2 = EW.melodia_eyewear_export_gate(d, parts=("Geometry",), params=params)
        hero = EW.melodia_eyewear_hero_export(d, hero_tag="hero", params=params)
        files = {}
        for k, v in list(rep.items()) + list(rep2.items()):
            files[k] = {"file": os.path.basename(v["file"]), "bytes": v["bytes"],
                        "tris": v["tris"], "prims": v["prims"]}
        files["hero"] = {"file": os.path.basename(hero["file"]), "bytes": hero["bytes"],
                         "tris": hero["tris"], "nodes": hero["nodes"]}
        manifest["heroes"][tag] = {
            "params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in params.items()},
            "files": files,
            "total_bytes": sum(v["bytes"] for v in files.values()),
            "total_tris": sum(v["tris"] for v in files.values()),
        }
        print("HERO %s OK tris=%d bytes=%d" % (
            tag, manifest["heroes"][tag]["total_tris"],
            manifest["heroes"][tag]["total_bytes"]))
    except AssertionError as exc:
        fails.append(tag)
        print("HERO %s FAIL %s" % (tag, str(exc)[:400]))

with open(os.path.join(ROOT, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=1)
print("HEROES %d/6 fails=%s" % (len(manifest["heroes"]), fails))
print("DONE")

