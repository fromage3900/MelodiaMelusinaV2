"""Probe: can Apprentice hython IMPORT FBX? (Export is blocked; import is the
weight-lab's read path for the dress mesh + 465-bone rest pose.)

Isolated run pattern (never bare in a shared console):
  Start-Process hython -ArgumentList <this file> ... WaitForExit(60s) ... kill on hang

Tries hou.hipFile.importFBX on the Choral Sheep FBX (small, known-good) and
reports what landed in the scene.
"""
import os

import hou

CANDIDATE = r"C:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\Companions\ChoralSheep\choralsheep.fbx"

print("[probe] hou version:", hou.applicationVersionString())
print("[probe] hipFile.importFBX exists:", hasattr(hou.hipFile, "importFBX"))
print("[probe] candidate exists:", os.path.exists(CANDIDATE))

if hasattr(hou.hipFile, "importFBX") and os.path.exists(CANDIDATE):
    try:
        hou.hipFile.importFBX(CANDIDATE)
        obj = hou.node("/obj")
        children = obj.children() if obj else []
        print("[probe] IMPORT OK - nodes:", [n.name() for n in children])
        # count skinned geometry + captures if any
        for n in children:
            geo = None
            try:
                geo = n.displayNode()
            except Exception:
                pass
            if geo and geo.geometry():
                g = geo.geometry()
                pts = len(g.points())
                prims = len(g.prims())
                pt_groups = len(g.primGroups())
                print(f"[probe]   {n.name()}: {pts} pts, {prims} prims")
    except Exception as e:
        print("[probe] IMPORT FAILED:", str(e)[:400])
else:
    print("[probe] cannot attempt import (missing API or file)")
