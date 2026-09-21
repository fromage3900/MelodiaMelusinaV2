# variant_convert.py — convert variant still raws to website jpgs.
# Usage: python variant_convert.py <src_raw_dir> <dst_dir> <prefix>
# Produces <prefix>_<sky>_<view>.jpg (1200x1500) + _800.jpg (800x1000), like
# stills_convert.py, but variant-tagged so the flower set is never touched.
import os
import sys
from PIL import Image

SRC = sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else (
    sys.argv[1] if len(sys.argv) > 1 else r"P:/MelodiaMelusinaV2-Laptop/Saved/Audit")
DST = sys.argv[sys.argv.index("--dst") + 1] if "--dst" in sys.argv else (
    sys.argv[2] if len(sys.argv) > 2 else r"P:/MelodiaMelusinaV2-Laptop/Saved/Website/Brooch/stills_variants")
PREFIX = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else (
    sys.argv[3] if len(sys.argv) > 3 else "sil")

import re

os.makedirs(DST, exist_ok=True)
n = 0
for f in sorted(os.listdir(SRC)):
    m = re.match(r"sky_(.+)\.png$", f)
    if not m:
        continue
    stem = m.group(1)
    im = Image.open(os.path.join(SRC, f)).convert("RGB")
    im.save(os.path.join(DST, "%s_%s.jpg" % (PREFIX, stem)), quality=90, subsampling=0)
    im.resize((800, 1000), Image.LANCZOS).save(
        os.path.join(DST, "%s_%s_800.jpg" % (PREFIX, stem)), quality=88, subsampling=0)
    n += 1
print("converted %d raws -> %s (prefix %s)" % (n, DST, PREFIX))
