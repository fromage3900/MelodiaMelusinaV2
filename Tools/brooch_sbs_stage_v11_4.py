"""v11.4 side-by-side stage â€” DEPRECATED SHIM (2026-09-22).

This file used to be a second, independent side-by-side renderer. It wrote the SAME
filenames (v114_sbs_front.png / v114_sbs_tq.png / v114_sbs_sil_{1600,256,128}.png) into
the same Saved/Audit/v114_sbs/ directory as Tools/brooch_sbs_render_v11_4.py â€” but
without the assertion report, without the V11 white-world silhouette recipe, and without
the 64 px icon read. Two writers on one surface: whichever ran last silently decided what
the evidence meant, and the contaminated set had no report to tell it apart from the good
one. That is the "two writers, no ownership" defect class in AGENTS.md.

It now DELEGATES. One canonical harness emits the frames and the report; this shim only
preserves the old CLI (--out / --res / --samples) so existing call sites keep working.

Usage (unchanged):
  blender -b <blend> --python Tools/brooch_sbs_stage_v11_4.py [-- --out <dir>]
"""
import runpy
import sys

_CANONICAL = "P:/MelodiaMelusinaV2-Laptop/Tools/brooch_sbs_render_v11_4.py"

print("[v11.4 stage] DEPRECATED -> delegating to brooch_sbs_render_v11_4.py")
if "--res" in sys.argv or "--samples" in sys.argv:
    print("[v11.4 stage] note: --res/--samples are accepted but not forwarded; the "
          "canonical harness owns resolution (1600x1000 beauty, 1600/256/128/64 flat).")
sys.argv = [a for a in sys.argv if a not in ("--res", "--samples")] + []
# Strip the two now-meaningless options and their values.
for flag in ("--res", "--samples"):
    while flag in sys.argv:
        i = sys.argv.index(flag)
        del sys.argv[i:i + 2]
runpy.run_path(_CANONICAL, run_name="__main__")
