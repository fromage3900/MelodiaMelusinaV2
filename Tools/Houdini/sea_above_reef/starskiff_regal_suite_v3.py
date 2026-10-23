"""Starskiff Regal Suite v3 — cushion velvet + lantern crystal + brass patina
For MK34: stern cushion, mast lantern glass, worn brass edges.
Tilable/masked via reef_common, hython.
Run: hython Tools/Houdini/sea_above_reef/starskiff_regal_suite_v3.py --size 1024
"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc

SIZE=1024
SEED=20260829
OUT=rc.PROJECT_ROOT/"Saved"/"Audit"/"melusina_lookdev"/"houdini_variants"

VELVET=np.array([112,38,62],np.float32)/255.0
VELVET_DARK=np.array([68,22,38],np.float32)/255.0
AQUA=np.array([88,215,208],np.float32)/255.0
BRASS=np.array([184,150,88],np.float32)/255.0
CRYSTAL=np.array([195,225,242],np.float32)/255.0

def build_cushion_set(size, seed):
    # Velvet base + damask diamonds, tilable
    wd=rc.WrappedDraw(size, background=0)
    # damask diamonds 3x3
    for iy in range(3):
        for ix in range(3):
            cx=(ix+0.5)*size/3; cy=(iy+0.5)*size/3
            d=size/3*0.28
            pts=[(cx,cy-d),(cx+d,cy),(cx,cy+d),(cx-d,cy)]
            wd.polygon(pts, fill=90)
            wd.polygon([(cx-d*0.45,cy),(cx,cy-d*0.45),(cx+d*0.45,cy),(cx,cy+d*0.45)], fill=170)
    dam=np.array(wd.result()).astype(np.float32)/255.0
    # velvet fBm nap
    nap=rc.fbm(size,32,2,np.random.default_rng(seed),gain=0.5)
    vel=np.ones((size,size,3),np.float32)*VELVET
    # damask in aqua
    vel=vel*(1 - dam[...,None]*0.22) + AQUA*dam[...,None]*0.18 + (VELVET_DARK-VELVET)*nap[...,None]*0.15
    # roughness: velvet soft, damask slightly glossier
    rough=np.clip(0.78 - dam*0.12 + nap*0.08, 0.2, 0.95)
    height=dam*0.6 + nap*0.15
    normal=rc.normal_from_height(height, strength=1.8)
    return vel, normal, rough, dam

def build_lantern_glass(size, seed):
    # Crystal glass: subtle caustic ripples + brass cage shadow mask, tilable
    caust=rc.fbm(size,32,3,np.random.default_rng(seed+7),gain=0.6)*0.5+0.5
    caust=np.clip((caust-0.35)/0.65,0,1)**1.2
    # add radial prism flares
    ys,xs=np.mgrid[0:size,0:size].astype(np.float32)/size
    cx,cy=0.5,0.5
    dist=np.sqrt((xs-cx)**2 + (ys-cy)**2)*2
    prism=np.clip(np.sin(dist*18 - seed*0.01)*0.5+0.5,0,1)*np.exp(-dist*1.8)*0.35
    glass_rgb=np.ones((size,size,3),np.float32)*CRYSTAL
    glass_rgb=glass_rgb*(0.82+0.18*caust[...,None]) + prism[...,None]*0.25
    # glass normal from caust height
    normal=rc.normal_from_height(caust*0.5+prism*0.3, strength=1.1)
    mask=caust*0.7+prism*0.5
    return glass_rgb, normal, mask

def build_brass_patina(size, seed):
    # Edge wear / patina for brass: tilable, brighter on edges via fBm + Worley-like
    wear=rc.fbm(size,16,3,np.random.default_rng(seed+11),gain=0.55)
    # add streaks
    ys=np.mgrid[0:size,0:size][0].astype(np.float32)/size
    streak=np.sin(ys*16 + rc.fbm(size,32,2,np.random.default_rng(seed+13),gain=0.5)*2)*0.5+0.5
    streak=np.clip((streak-0.5)/0.5,0,1)*0.25
    patina=np.clip(wear*0.6 + streak,0,1)
    return patina

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap=argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--seed", type=int, default=SEED)
    args=ap.parse_args()
    size=args.size; seed=args.seed
    vel_col, vel_n, vel_r, vel_m = build_cushion_set(size, seed+60)
    glass_col, glass_n, glass_m = build_lantern_glass(size, seed+70)
    patina = build_brass_patina(size, seed+80)
    images={
        "T_Starskiff_Cushion_Velvet_BaseColor": (vel_col,"rgb"),
        "T_Starskiff_Cushion_Normal": (vel_n,"rgb"),
        "T_Starskiff_Cushion_Roughness": (vel_r,"gray"),
        "T_Starskiff_LanternGlass_BaseColor": (glass_col,"rgb"),
        "T_Starskiff_LanternGlass_Normal": (glass_n,"rgb"),
        "T_Starskiff_Brass_Patina_Mask": (patina,"gray"),
    }
    files=[]
    for name,(arr,kind) in images.items():
        p=rc.save_image(OUT/f"{name}.png",arr,kind)
        files.append({"name":name,"path":str(p),"kind":kind,"size":int(size),"seed":seed})
        print(f"[regal v3] wrote {p.name} {kind} {arr.shape}")
    mf=rc.write_manifest(OUT/"starskiff_regal_v3_manifest.json","melodia.starskiff_regal.v3",seed,
        {"generator":"starskiff_regal_suite_v3.py","asset":"cushion+lantern+patina"},files)
    print(f"[regal v3] manifest -> {mf}")

if __name__=="__main__":
    main()
