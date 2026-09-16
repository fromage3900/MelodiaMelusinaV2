"""Downscale the KitBash3D/character textures the web viewer references but never shipped.

The viewer's FBX files reference sibling .png files that were never committed, so five of
fourteen assets render untextured. The 4K sources total 471 MB, which is far too heavy for a
browser. This downsamples them to web-appropriate PNGs under the exact filenames the loaders
expect (so the extension must stay .png).
"""
import json, os, re
from PIL import Image

MODELS = r"C:\Users\froma\AppData\Local\Temp\ms-sub\wix\models"
REPORT = r"C:\EnvironmentPortfolio\browser-test\all_assets\all_assets_report.json"
SIZE = 512

ROOTS = [
    r"C:\EnvironmentPortfolio\Imports",
    r"C:\EnvironmentPortfolio\BS_GodFile\Content",
    r"C:\EnvironmentPortfolio\BS_GodFile\Saved",
]

rep = json.load(open(REPORT))
missing = set()
for r in rep["results"]:
    for f in r["newFailures"]:
        m = re.search(r"/wix/models/([^,\s]+)", f)
        if m:
            missing.add(m.group(1))

# index sources by basename
index = {}
for root in ROOTS:
    if not os.path.isdir(root):
        continue
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".tga", ".jpeg")):
                index.setdefault(f, os.path.join(dirpath, f))

done, skipped, failed = [], [], []
total_out = 0
for name in sorted(missing):
    src = index.get(name) or index.get(name.replace(".inverted.png", ".png"))
    if not src:
        skipped.append((name, "source not on disk"))
        continue
    out = os.path.join(MODELS, name)
    try:
        im = Image.open(src)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        # keep alpha for masks/emission if present
        target_mode = "RGBA" if im.mode == "RGBA" else "RGB"
        im = im.resize((SIZE, SIZE), Image.LANCZOS).convert(target_mode)
        im.save(out, "PNG", optimize=True)
        b = os.path.getsize(out)
        total_out += b
        done.append((name, os.path.getsize(src), b))
    except Exception as e:
        failed.append((name, str(e)[:60]))

print(f"wrote {len(done)} textures at {SIZE}px")
print(f"total shipped: {total_out/1048576:.1f} MB")
print(f"skipped {len(skipped)}, failed {len(failed)}\n")
for n, s, b in sorted(done, key=lambda x: -x[2])[:8]:
    print(f"  {s/1048576:7.2f} MB -> {b/1024:7.1f} KB   {n}")
print()
for n, why in skipped:
    print(f"  SKIP {n}: {why}")
for n, why in failed:
    print(f"  FAIL {n}: {why}")
