"""Dump the music params a builder actually exposes, for the ones the pulse moves most."""
import json
import os
import sys

import bpy

_WT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_WT, "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS  # noqa: E402

IDS = ["MEL_eyewear_hinge", "MEL_castle_gothic_window", "MEL_castle_machicolations",
       "MEL_church_bell", "MEL_nikki_bead", "MEL_sdf_star_panel", "MEL_baroque_facade",
       "MEL_nikki_cord", "MEL_music_treble_clef_mp"]

for i in IDS:
    sub = GROUP_BUILDERS[i]()
    sub = sub[0] if isinstance(sub, (tuple, list)) else sub
    params = []
    for it in sub.interface.items_tree:
        n = getattr(it, "name", None) or ""
        if getattr(it, "in_out", None) == "INPUT" and "Music" in n:
            params.append("%s=%r" % (n, getattr(it, "default_value", None)))
    print("  %-30s %s" % (i, "  ".join(params) or "(none)"))
print("DONE")
