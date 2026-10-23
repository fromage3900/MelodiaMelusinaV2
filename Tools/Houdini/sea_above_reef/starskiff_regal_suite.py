"""Starskiff Regal Suite — Houdini pipeline, tilable, for Melusina's boat.
Generates the regal layer on top of the base planks:
  T_Starskiff_RegalFiligree_Mask  (gunwale scrollwork, tilable)
  T_Starskiff_BrassFiligree_BaseColor (brass + filigree inlay)
  T_Starskiff_Hull_Regal_Normal (carved plank grooves + filigree emboss)
  T_Starskiff_SternCrest_Mask (stern cartouche)

Convergence: reuses reef_common wrap math, no parallel system.
Run:  hython Tools/Houdini/sea_above_reef/starskiff_regal_suite.py
      hython Tools/Houdini/sea_above_reef/starskiff_regal_suite.py --size 1024
"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc

SIZE = 1024
SEED = 20260829
OUT = rc.PROJECT_ROOT / "Saved" / "Audit" / "melusina_lookdev" / "houdini_variants"

# regal palette
SEAFOAM = np.array([78, 108, 140], np.float32)/255.0
IVORY = np.array([232, 222, 190], np.float32)/255.0
BRASS = np.array([184, 150, 88], np.float32)/255.0
BRASS_DARK = np.array([120, 92, 52], np.float32)/255.0
AQUA = np.array([80, 205, 210], np.float32)/255.0

def build_regal_filigree_mask(size, seed):
    """Tilable filigree scrollwork for gunwale - uses WrappedDraw for seamless motif."""
    from PIL import Image
    rng = np.random.default_rng(seed)
    # base: dark field
    wd = rc.WrappedDraw(size, background=0)
    # draw repeating scroll motif: 4x2 tiles, each with mirrored S-scroll
    tiles_x, tiles_y = 4, 2
    margin = size // 32
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            cx = (tx + 0.5) * size / tiles_x
            cy = (ty + 0.5) * size / tiles_y
            # central diamond
            d = size / tiles_x * 0.18
            pts = [(cx, cy-d), (cx+d, cy), (cx, cy+d), (cx-d, cy)]
            wd.polygon(pts, fill=180)
            # four corner curls - ellipses
            r = size / tiles_x * 0.12
            for ang in [45, 135, 225, 315]:
                import math
                ox = math.cos(math.radians(ang)) * d*0.7
                oy = math.sin(math.radians(ang)) * d*0.7
                # curl ellipse
                x0, y0 = cx+ox-r*0.6, cy+oy-r*0.6
                x1, y1 = cx+ox+r*0.6, cy+oy+r*0.6
                wd.ellipse([(x0,y0),(x1,y1)], fill=90)
                # inner highlight
                wd.ellipse([(x0+r*0.3,y0+r*0.3),(x1-r*0.3,y1-r*0.3)], fill=220)
            # connecting filigree lines - S curve approximated as polyline
            # horizontal bar
            wd.line([(cx - size/tiles_x*0.45, cy), (cx + size/tiles_x*0.45, cy)], fill=110, width=max(1, size//256))
            wd.line([(cx, cy - size/tiles_y*0.42), (cx, cy + size/tiles_y*0.42)], fill=110, width=max(1, size//256))
    # get mask and add subtle grain for hand-carved feel
    mask_img = wd.result()
    mask = np.array(mask_img).astype(np.float32) / 255.0
    # add fBm warp for hammered brass variation
    warp = rc.fbm(size, 32, 3, np.random.default_rng(seed+1), gain=0.6)
    mask = np.clip(mask * (0.92 + 0.16*(warp)), 0, 1)
    # sharpen
    mask = np.clip((mask - 0.12)/0.88, 0, 1) ** 0.95
    return mask

def build_brass_filigree_albedo(size, seed, filigree_mask):
    # brass field with filigree inlay + edge wear
    rng = np.random.default_rng(seed+2)
    # base brass with fBm patina
    patina = rc.fbm(size, 16, 3, rng, gain=0.5)
    # dark in grooves, bright on raised filigree
    brass = BRASS[None,None,:] * (0.88 + 0.24*(patina[...,None]-0.5)*2)
    # filigree raised = brighter, aqua kiss
    fil = filigree_mask[...,None]
    brass = brass * (1 - fil*0.35) + IVORY[None,None,:] * (fil*0.22) + BRASS_DARK[None,None,:] * (fil*0.10)
    # aqua oxidization in recesses (inverse filigree + low freq)
    oxid = (1-fil)*0.18 * np.clip((patina-0.3)/0.7,0,1)[...,None]
    brass = brass * (1 - oxid*0.6) + AQUA[None,None,:] * (oxid*0.35)
    # edge highlight (bevel) from mask gradient
    # simple Sobel for bevel
    dx = (np.roll(filigree_mask, -1, 1) - np.roll(filigree_mask, 1, 1))*0.5
    dy = (np.roll(filigree_mask, -1, 0) - np.roll(filigree_mask, 1, 0))*0.5
    bevel = np.sqrt(dx*dx + dy*dy)
    bevel = np.clip(bevel*4.0, 0, 1)
    brass += bevel[...,None] * 0.12
    return np.clip(brass, 0, 1)

def build_regal_normal(size, filigree_mask, seed):
    # height = filigree emboss (raised) + plank grooves (reused)
    # plank grooves: horizontal 14 planks
    ys = np.mgrid[0:size, 0:size][0].astype(np.float32) / size
    plank_freq = 14
    seam = np.abs(((ys * plank_freq) % 1.0) - 0.5) * 2.0
    # filigree height is mask, planks are grooves
    height = 0.55 * filigree_mask + 0.25 * (1-seam) + 0.12 * rc.fbm(size, 64, 2, np.random.default_rng(seed+5), gain=0.55)
    # sharpen filigree emboss
    normal = rc.normal_from_height(height, strength=3.8)
    return normal, height

def build_stern_crest_mask(size, seed):
    """Circular cartouche for stern — tilable but centered motif, not wrapped."""
    from PIL import Image, ImageDraw
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    cx, cy = size//2, size//2
    r_outer = size * 0.38
    r_inner = size * 0.32
    # outer ring
    d.ellipse([cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer], fill=90)
    d.ellipse([cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner], fill=0)
    # inner shield shape - diamond with curved top
    d.ellipse([cx-size*0.14, cy-size*0.18, cx+size*0.14, cy+size*0.06], fill=160)
    d.polygon([(cx, cy+size*0.18), (cx-size*0.12, cy+size*0.02), (cx+size*0.12, cy+size*0.02)], fill=160)
    # small crown above
    d.polygon([(cx-size*0.08, cy-size*0.14), (cx, cy-size*0.22), (cx+size*0.08, cy-size*0.14), (cx+size*0.06, cy-size*0.10), (cx-size*0.06, cy-size*0.10)], fill=200)
    # add side flourishes
    for sx in [-1, 1]:
        x0 = cx + sx*size*0.20
        d.ellipse([x0-size*0.06, cy-size*0.08, x0+size*0.06, cy+size*0.04], fill=120)
    mask = np.array(img).astype(np.float32)/255.0
    # soft edge
    mask = np.clip((mask*1.15 - 0.05), 0, 1)
    return mask

def build(size, seed):
    filigree = build_regal_filigree_mask(size, seed)
    brass = build_brass_filigree_albedo(size, seed, filigree)
    regal_normal, height = build_regal_normal(size, filigree, seed)
    crest = build_stern_crest_mask(size, seed+10)
    # roughness: brass smooth where raised filigree, rougher in recess + patina
    rough = np.clip(0.42 - 0.22*filigree + 0.18*(1-filieggee_mask_fallback(filigree)) if False else 0, 0, 1)
    # proper roughness calc:
    rough = 0.45 - 0.25*filigree + 0.15*rc.fbm(size, 16, 3, np.random.default_rng(seed+7), gain=0.5)
    rough = np.clip(rough, 0.15, 0.95)
    # add crest roughness as well
    return {
        "T_Starskiff_RegalFiligree_Mask": (filigree, "gray"),
        "T_Starskiff_BrassFiligree_BaseColor": (brass, "rgb"),
        "T_Starskiff_Hull_Regal_Normal": (regal_normal, "rgb"),
        "T_Starskiff_Hull_Regal_Height": (height, "gray"),
        "T_Starskiff_SternCrest_Mask": (crest, "gray"),
        "T_Starskiff_BrassFiligree_Roughness": (rough, "gray"),
    }

def filieggee_mask_fallback(x):
    return x

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--size", type=int, default=SIZE)
    args = ap.parse_args()
    images = build(args.size, args.seed)
    files=[]
    for name, (arr, kind) in images.items():
        p = rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name": name, "path": str(p), "kind": kind, "size": int(args.size), "seed": args.seed})
        print(f"[regal] wrote {p.name} {kind} {arr.shape}")
    manifest = rc.write_manifest(OUT / "starskiff_regal_manifest.json", "melodia.starskiff_regal.v1", args.seed,
        {"generator": "starskiff_regal_suite.py", "runtime": "hython/PIL via reef_common", "asset": "Starskiff Regal - filigree + brass + crest", "tilable": "filigree mask tilable via WrappedDraw, crest centered"}, files)
    print(f"[regal] manifest -> {manifest}")
    # also verify tiling on filigree
    arr = images["T_Starskiff_RegalFiligree_Mask"][0]
    # simple seam metric: edge diff
    seam = (np.abs(arr[0,:] - arr[-1,:]).mean() + np.abs(arr[:,0] - arr[:,-1]).mean())/2
    print(f"[regal] filigree seam mean {seam:.4f} (pass <0.03)")

if __name__ == "__main__":
    main()
