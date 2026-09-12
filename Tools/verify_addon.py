"""Melodia Studio addon gate. Run:
     blender.exe --background --factory-startup --python Tools/verify_addon.py
Exits non-zero on any failure. Prints one GATE line per assertion.
See Docs/Production/MELODIA_STUDIO_FREEZE_2026-09-11.md section 4.
"""
import collections
import glob
import hashlib
import json
import os
import re
import sys
import traceback

import bpy

REPO = r"P:/MelodiaMelusinaV2-Laptop"
APPDATA_ADDONS = os.path.join(os.environ["APPDATA"], "Blender Foundation",
                              "Blender", "5.2", "scripts", "addons")
BASELINE = os.path.join(REPO, "Tools", "registry_baseline.json")

# Duplicate-id clusters that predate the 2026-09-11 freeze. A NEW one fails the
# gate; these two are recorded debt, not sanctioned design.
KNOWN_DUPLICATES = {
    "MEL_arch": ["core_forms_kit.py", "structures.py"],
    "MEL_ogee_arch": ["euro_kit.py", "experimental_kit.py"],
}
# Files that must be byte-identical across the checkout and the live install.
CONVERGED_FILES = [
    ("deploy/surreal_arch/melodia_gn/nikki_decor.py",
     "surreal_arch/melodia_gn/nikki_decor.py"),
    ("deploy/surreal_arch/melodia_gn/nikki_musical_decorations.py",
     "surreal_arch/melodia_gn/nikki_musical_decorations.py"),
    ("Tools/BlenderAddons/melodia_utils.py", "melodia_utils.py"),
    ("Tools/BlenderAddons/melodia_studio/midi_bridge.py", "melodia_studio/midi_bridge.py"),
    ("Tools/BlenderAddons/melodia_studio/walkable_world.py", "melodia_studio/walkable_world.py"),
    ("Tools/BlenderAddons/melodia_studio/tests/test_midi_bridge.py",
     "melodia_studio/tests/test_midi_bridge.py"),
]
# Baseline for assertion D, measured by THIS gate's method (evaluate every tree on
# an empty base mesh, count those producing 0 verts). It is not the census's
# `baseline_empty_count` (111) — that uses a different scope, so the two numbers are
# not comparable. This one exists only to catch growth: a new builder that silently
# needs inputs will push it up.
RECORDED_EMPTIES = 125

results = []


def gate(name, ok, detail=""):
    results.append((name, ok))
    print("GATE %-2s %-6s %s" % (name, "PASS" if ok else "FAIL", detail))


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None


# ---- A: registry imports; every builder builds -----------------------------
if APPDATA_ADDONS not in sys.path:
    sys.path.insert(0, APPDATA_ADDONS)
try:
    from surreal_arch.melodia_gn.core import GROUP_BUILDERS, CATEGORY_META
    ids = sorted(GROUP_BUILDERS)
    errs = []
    for k in ids:
        try:
            r = GROUP_BUILDERS[k]()
            t = r[0] if isinstance(r, (tuple, list)) else r
            if t is None:
                errs.append((k, "no tree"))
        except Exception as e:
            errs.append((k, "%s: %s" % (type(e).__name__, str(e)[:70])))
    gate("A", not errs, "registry=%d errors=%d %s" % (len(ids), len(errs), errs[:4]))
except Exception:
    traceback.print_exc()
    gate("A", False, "registry import failed")
    ids = []

if not ids:
    print("GATE RESULT: FAIL (no registry)")
    raise SystemExit(1)

# ---- B: registry ids == baseline ------------------------------------------
try:
    bl = json.load(open(BASELINE))
    base = set(bl.get("package", []))
    lost, new = sorted(base - set(ids)), sorted(set(ids) - base)
    gate("B", not lost and not new,
         "baseline=%d lost=%d new=%d %s%s"
         % (len(base), len(lost), len(new), lost[:5], new[:5]))
except Exception as e:
    gate("B", False, "baseline unreadable: %s" % e)

# ---- C: duplicate-id clusters ---------------------------------------------
owners = collections.defaultdict(set)
for p in glob.glob(os.path.join(APPDATA_ADDONS, "surreal_arch", "melodia_gn", "*.py")):
    src = open(p, encoding="utf-8", errors="replace").read()
    for i in set(re.findall(r"register_builder\(\s*[\r\n ]*[\"']([^\"']+)[\"']", src)):
        owners[i].add(os.path.basename(p))
dups = {i: sorted(v) for i, v in owners.items() if len(v) > 1}
unexpected = {i: v for i, v in dups.items() if i not in KNOWN_DUPLICATES}
gate("C", not unexpected,
     "clusters=%d known=%d unexpected=%s" % (len(dups), len(dups) - len(unexpected),
                                             sorted(unexpected)))

# ---- D: input-dependent empties must not grow -----------------------------
empties = 0
try:
    scene = bpy.context.scene
    for k in ids:
        try:
            r = GROUP_BUILDERS[k]()
            ng = r[0] if isinstance(r, (tuple, list)) else r
            if ng is None:
                continue
            base = bpy.data.meshes.new("__gate_base__")
            ob = bpy.data.objects.new("__gate_obj__", base)
            scene.collection.objects.link(ob)
            mod = ob.modifiers.new("gate", "NODES")
            mod.node_group = ng
            dg = bpy.context.evaluated_depsgraph_get()
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            n = len(me.vertices) if me else 0
            if n == 0:
                empties += 1
            ev.to_mesh_clear()
            ob.modifiers.clear()
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(base)
        except Exception:
            continue
    gate("D", empties <= RECORDED_EMPTIES,
         "empties=%d recorded=%d" % (empties, RECORDED_EMPTIES))
except Exception as e:
    gate("D", False, str(e))

# ---- E: checkout <-> live byte convergence --------------------------------
bad = []
for rel, live_rel in CONVERGED_FILES:
    a, b = md5(os.path.join(REPO, rel)), md5(os.path.join(APPDATA_ADDONS, live_rel))
    if a is None or a != b:
        bad.append(rel)
gate("E", not bad, "checked=%d mismatched=%s" % (len(CONVERGED_FILES), bad))

# ---- F: no tree reads a BoundBox over unrealized instances ----------------
try:
    REALIZE = "GeometryNodeRealizeInstances"
    offenders = []
    for k in ids:
        try:
            r = GROUP_BUILDERS[k]()
            ng = r[0] if isinstance(r, (tuple, list)) else r
        except Exception:
            continue
        bboxes = [n for n in ng.nodes if n.bl_idname == "GeometryNodeBoundBox"]
        if not bboxes:
            continue
        for b in bboxes:
            stack = [(l.from_node, False, 0) for l in b.inputs["Geometry"].links]
            seen = set()
            while stack:
                node, realized, d = stack.pop()
                if node is None or d > 120:
                    continue
                key = (node.name, realized)
                if key in seen:
                    continue
                seen.add(key)
                if node.bl_idname == REALIZE:
                    realized = True
                if node.bl_idname == "GeometryNodeInstanceOnPoints" and not realized:
                    offenders.append("%s.%s" % (ng.name, node.name))
                for inp in node.inputs:
                    for l in inp.links:
                        stack.append((l.from_node, realized, d + 1))
    gate("F", not offenders, "offenders=%s" % (sorted(set(offenders))[:6] or "none"))
except Exception as e:
    gate("F", False, str(e))

ok = all(r[1] for r in results)
print("GATE RESULT: %s  (%d/%d passed)"
      % ("PASS" if ok else "FAIL", sum(1 for r in results if r[1]), len(results)))
print("GATE metrics: builders=%d categories=%d dup_clusters=%d" % (len(ids), len(CATEGORY_META), len(dups)))
raise SystemExit(0 if ok else 1)
