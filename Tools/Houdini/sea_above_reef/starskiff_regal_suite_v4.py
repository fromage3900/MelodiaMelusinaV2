"""Starskiff Regal Suite v4 — plank nails + edge wear + floor grating
For MK35: hull plank iron nails, seam wear, interior slat grating.
"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc

SIZE=1024
SEED=20260829
OUT=rc.PROJECT_ROOT/"Saved"/"Audit"/"melusina_lookdev"/"houdini_variants"

AQUA=np.array([88,215,208],np.float32)/255.0
BRASS=np.array([184,150,88],np.float32)/255.0
IRON=np.array([68,62,58],np.float32)/255.0

def build_plank_nails(size, seed):
    # 14 planks -> nail row per seam, tilable X
    ys=np.mgrid[0:size,0:size][0].astype(np.float32)/size
    nail=np.zeros((size,size),np.float32)
    planks=14
    rng=np.random.default_rng(seed)
    for p in range(1, planks):
        y = p/planks
        # jitter per column
        for x in range(0, size, size//18):
            jx = (rng.integers(-4,5) + x) % size
            jy = int(y*size + rng.integers(-3,4))
            # nail head dot 4px
            for dy in range(-2,3):
                for dx in range(-2,3):
                    if dx*dx+dy*dy <=4:
                        nail[(jy+dy)%size, (jx+dx)%size]=1.0
    # also edge wear streaks along seams
    seam=np.abs(((ys*planks)%1.0)-0.5)*2
    wear=np.clip((1-seam)*0.7 + rc.fbm(size,32,2,np.random.default_rng(seed+3),gain=0.5)*0.15,0,1)
    # height: nails raised
    height=nail*0.9 + wear*0.12
    normal=rc.normal_from_height(height, strength=2.6)
    # color: iron nails on seafoam
    col=np.ones((size,size,3),np.float32)*np.array([0.30,0.42,0.55])
    nail_rgb = np.clip(nail[...,None]*0.85,0,1)
    col = col*(1 - nail_rgb*0.55) + IRON*nail_rgb*0.65 + AQUA*nail_rgb*0.08
    return nail, wear, col, normal, height

def build_grating(size, seed):
    # Floor grating: parallel slats with brass rivets, tilable
    from PIL import Image, ImageDraw
    wd=rc.WrappedDraw(size, background=0)
    slats=12
    for i in range(slats):
        y=int((i+0.5)*size/slats)
        # slat bar via two lines
        wd.line([(0, y- size//slats//4),(size, y- size//slats//4)], fill=180, width=max(1,size//slats//2))
        wd.line([(0, y+ size//slats//4),(size, y+ size//slats//4)], fill=180, width=max(1,size//slats//2))
        # also ellipse fill for slat body
        wd.ellipse([(0, y- size//slats//4),(size, y+ size//slats//4)], fill=150)
    mask=np.array(wd.result()).astype(np.float32)/255.0
    # wood + brass color
    wood=np.ones((size,size,3),np.float32)*np.array([0.42,0.34,0.26])
    wood=wood*(1 - mask[...,None]*0.18) + BRASS*mask[...,None]*0.28
    height=mask*0.6 + rc.fbm(size,32,2,np.random.default_rng(seed+9),gain=0.45)*0.1
    normal=rc.normal_from_height(height, strength=1.7)
    return mask, wood, normal

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap=argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--seed", type=int, default=SEED)
    args=ap.parse_args()
    size=args.size; seed=args.seed
    nail, wear, nail_col, nail_n, nail_h = build_plank_nails(size, seed+90)
    grat_mask, grat_col, grat_n = build_grating(size, seed+100)
    images={
        "T_Starskiff_PlankNail_Mask": (nail,"gray"),
        "T_Starskiff_PlankNail_BaseColor": (nail_col,"rgb"),
        "T_Starskiff_PlankNail_Normal": (nail_n,"rgb"),
        "T_Starskiff_EdgeWear_Mask": (wear,"gray"),
        "T_Starskiff_Grating_Mask": (grat_mask,"gray"),
        "T_Starskiff_Grating_BaseColor": (grat_col,"rgb"),
        "T_Starskiff_Grating_Normal": (grat_n,"rgb"),
    }
    files=[]
    for name,(arr,kind) in images.items():
        p=rc.save_image(OUT/f"{name}.png",arr,kind)
        files.append({"name":name,"path":str(p),"kind":kind,"size":int(size),"seed":seed})
        print(f"[regal v4] wrote {p.name} {kind} {arr.shape}")
    mf=rc.write_manifest(OUT/"starskiff_regal_v4_manifest.json","melodia.starskiff_regal.v4",seed,
        {"generator":"starskiff_regal_suite_v4.py","asset":"plank nails + grating"},files)
    print(f"[regal v4] manifest -> {mf}")

if __name__=="__main__":
    main()
