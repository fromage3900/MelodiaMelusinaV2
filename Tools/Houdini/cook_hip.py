#!/usr/bin/env python
"""Generic Houdini HIP ROP cooker for MCP build_hip."""
import argparse
from pathlib import Path
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hip", required=True)
    ap.add_argument("--buildpath", required=True)
    args = ap.parse_args()
    try:
        import hou
        hou.hipFile.load(args.hip)
        # cook all ROPs under /out that are display-flagged
        out = hou.node("/out")
        if out:
            for rop in out.recursiveGlob("*", hou.nodeTypeFilter.Rop):
                if rop.isDisplayFlagSet():
                    rop.render()
                    print(f"[hip] cooked {rop.path()}")
        print(f"[hip] done -> {args.buildpath}")
    except ImportError:
        print("[hip] hou not available — skipping cook (install Houdini or set HOUDINI_HYTHON_EXE)")
        raise SystemExit(0)
