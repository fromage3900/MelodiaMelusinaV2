"""F1 gate — Higgsas availability + no-silent-fallback proof.

Run headless against the LIVE install:
  blender.exe --background --factory-startup --python Tools/higgsas_gate.py

Gates (print lines are the authority):
  G1 capabilities resolver finds the library on disk
  G2 higgsas_bridge.is_available() True
  G3 all 33 HIGGSAS_ARCH_NODES load from the library
  G4 build_pillar_group tree contains a real GeometryNodeGroup (NTSpin), not fallback
  G5 build_brick_wall_group tree contains a real GeometryNodeGroup (NTBricks Grid)
  G6 kit-level _higg_load delegates (no hardcoded G: path remains in kits)
"""
import os
import sys

LIVE = os.path.expandvars(
    r"%APPDATA%\Blender Foundation\Blender\5.2\scripts\addons")
REPO = r"P:\MelodiaMelusinaV2-Laptop\deploy"
root = LIVE if os.path.isdir(os.path.join(LIVE, "surreal_arch")) else REPO
sys.path.insert(0, root)
print("[F1] addon root:", root)

fails = []

import bpy  # noqa: E402

from surreal_arch.capabilities import higgsas_library_path  # noqa: E402
lib = higgsas_library_path()
print("[F1] G1 resolved library path:", lib)
if os.path.exists(lib):
    print("[F1] G1 PASS: library exists")
else:
    print("[F1] G1 FAIL"); fails.append("G1")

from surreal_arch import higgsas_bridge  # noqa: E402
avail = higgsas_bridge.is_available()
print("[F1] G2 is_available:", avail, "PASS" if avail else "FAIL")
if not avail:
    fails.append("G2")

loaded, skipped = higgsas_bridge.load_arch_nodes()
print("[F1] G3 loaded %d/%d arch nodes" % (len(loaded),
                                           len(higgsas_bridge.HIGGSAS_ARCH_NODES)))
if skipped:
    print("[F1] G3 skipped:", skipped)
    fails.append("G3")
else:
    print("[F1] G3 PASS")

from surreal_arch.melodia_gn import core_forms_kit as cfk  # noqa: E402
from surreal_arch.melodia_gn import walls_kit as wk  # noqa: E402


def _tree_group_nodes(ng):
    return [n for n in ng.nodes if n.bl_idname == "GeometryNodeGroup"
            and n.node_tree and n.node_tree.name.startswith("NT")]


try:
    pillar_tree, _gin, _gout = cfk.build_pillar_group(group_name="_F1_pillar_probe")
    hits = _tree_group_nodes(pillar_tree)
    names = [n.node_tree.name for n in hits]
    print("[F1] G4 pillar NT-group nodes:", names)
    if "NTSpin" in names:
        print("[F1] G4 PASS")
    else:
        print("[F1] G4 FAIL: NTSpin absent — silent fallback"); fails.append("G4")
except Exception as e:
    print("[F1] G4 FAIL exception:", e); fails.append("G4")

try:
    wall_tree, _gin, _gout = cfk.build_brick_wall_group(group_name="_F1_wall_probe")
    hits = _tree_group_nodes(wall_tree)
    names = [n.node_tree.name for n in hits]
    print("[F1] G5 brick wall NT-group nodes:", names)
    if "NTBricks Grid" in names:
        print("[F1] G5 PASS")
    else:
        print("[F1] G5 FAIL: NTBricks Grid absent — silent fallback"); fails.append("G5")
except Exception as e:
    print("[F1] G5 FAIL exception:", e); fails.append("G5")

# G6 static: no hardcoded G: path or module-local LIB constant in the kits
bad = []
for mod, path in ((cfk, os.path.join(root, "surreal_arch", "melodia_gn", "core_forms_kit.py")),
                  (wk, os.path.join(root, "surreal_arch", "melodia_gn", "walls_kit.py"))):
    txt = open(path, encoding="utf-8").read()
    if "_HIGGSAS_LIB_PATH" in txt or "G:\\programs" in txt:
        bad.append(os.path.basename(path))
print("[F1] G6 kit hardcoded paths:", bad if bad else "none",
      "PASS" if not bad else "FAIL")
if bad:
    fails.append("G6")

print("[F1] RESULT:", "PASS" if not fails else "FAIL " + ",".join(fails))
sys.exit(0 if not fails else 1)
