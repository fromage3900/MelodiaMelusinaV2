"""Starskiff Regal Suite v2 — rope + waterline + jewels + sail damask
Iterates on v1 filigree: adds nautical rope, barnacle waterline, aqua jewels, pearl sail.
Tilable where it wraps, all hython/PIL via reef_common.
Run: hython Tools/Houdini/sea_above_reef/starskiff_regal_suite_v2.py --size 1024
"""
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc

SIZE=1024
SEED=20260829
OUT=rc.PROJECT_ROOT/"Saved"/"Audit"/"melusina_lookdev"/"houdini_variants"

AQUA=np.array([110,235,225],np.float32)/255.0
BRASS=np.array([184,150,88],np.float32)/255.0
PEARL=np.array([235,228,212],np.float32)/255.0
BARNACLE=np.array([68,58,52],np.float32)/255.0

def build_rope_set(size, seed):
    # Tilable rope normal + height: 3-strand twist horizontal band
    ys=np.mgrid[0:size,0:size][0].astype(np.float32)/size
    xs=np.mgrid[0:size,0:size][1].astype(np.float32)/size*4.0  # 4 repeats horizontally
    # twist: sin along x, offset per strand
    rope=np.zeros((size,size),np.float32)
    for k in range(3):
        phase=k*2*np.pi/3
        strand=np.sin(2*np.pi*xs + phase + 4*ys)*0.5+0.5
        strand=np.clip((strand-0.35)/0.65,0,1)**0.8
        rope=np.maximum(rope, strand*0.85)
    # braid veins
    braid=np.abs(np.sin(2*np.pi*xs*0.5))*0.15
    rope=np.clip(rope+braid,0,1)
    # add fBm for fiber
    fiber=rc.fbm(size,64,2,np.random.default_rng(seed),gain=0.45)
    height=rope*0.75 + fiber*0.12 + 0.08
    normal=rc.normal_from_height(height, strength=3.2)
    return normal, height, rope

def build_barnacle_waterline(size, seed):
    # Waterline band: bottom third of texture is barnacle zone, tilable X, gradient Y
    # Center barnacles at mid-height, fade up/down
    ys=np.mgrid[0:size,0:size][0].astype(np.float32)/size
    # waterline band centered at 0.42 (just above keel), width 0.18
    band=np.exp(-((ys-0.42)/0.11)**2)
    band*= (0.85+0.15*rc.fbm(size,16,2,np.random.default_rng(seed+3),gain=0.5))
    # voronoi-like clusters
    rng=np.random.default_rng(seed+5)
    pts=rng.integers(0,size,(220,2))
    dist=np.ones((size,size),np.float32)*1e6
    # cheap distance to nearest point (coarse but tilable via WrappedDraw)
    from PIL import Image, ImageDraw
    wd=rc.WrappedDraw(size, background=0)
    for y,x in pts:
        r=int(3+rng.integers(0,5))
        wd.ellipse([(x-r,y-r),(x+r,y+r)],fill=200)
        wd.ellipse([(x-r//2,y-r//2),(x+r//2,y+r//2)],fill=255)
    cluster=np.array(wd.result()).astype(np.float32)/255.0
    mask=np.clip(band*cluster*1.4 + band*0.25,0,1)
    # also color variation for albedo
    col=np.ones((size,size,3),np.float32)*PEARL
    col=col*(1 - 0.45*mask[...,None]) + BARNACLE*mask[...,None]*0.55
    return mask, col

def build_jewel_mask(size, seed):
    # Jewel dots at scroll intersections: 4x2 grid, tilable via WrappedDraw
    wd=rc.WrappedDraw(size, background=0)
    tx,ty=4,2
    r=size//tx//6
    for iy in range(ty):
        for ix in range(tx):
            cx=(ix+0.5)*size/tx
            cy=(iy+0.5)*size/ty
            # central jewel
            wd.ellipse([(cx-r,cy-r),(cx+r,cy+r)], fill=255)
            # smaller facet highlight
            wd.ellipse([(cx-r*0.35,cy-r*0.45),(cx+r*0.25,cy+r*0.15)], fill=180)
    jew=np.array(wd.result()).astype(np.float32)/255.0
    jew=np.clip(jew*1.1,0,1)
    # glow: blur via height-> add outer falloff
    return jew

def build_sail_damask(size, seed):
    # Pearl sail filigree border: central field pearly, border 14% with damask
    from PIL import Image, ImageDraw
    wd=rc.WrappedDraw(size, background=0)
    # border damask - diagonal vine
    for i in range(size//32):
        x=(i*43 + seed)%size
        wd.line([(x,0),(x+size//3,size)], fill=110, width=max(1,size//512))
        wd.ellipse([(x-size//48, i*size//10),(x+size//48,i*size//10+size//24)],fill=70)
    dam=np.array(wd.result()).astype(np.float32)/255.0*0.55
    # center fade
    ys,xs=np.mgrid[0:size,0:size].astype(np.float32)/size
    # L-shaped border (outer 0.14)
    border=np.maximum(np.maximum(xs<0.14, xs>0.86), np.maximum(ys<0.14, ys>0.86)).astype(np.float32)
    mask=border* (0.6 + 0.4*dam) + (1-border)*0.08
    # base pearl with subtle fBm
    pearl=rc.fbm(size,32,2,np.random.default_rng(seed+9),gain=0.5)*0.08+0.92
    base=np.ones((size,size,3),np.float32)*PEARL
    base*=pearl[...,None]
    base=base*(1 - mask[...,None]*0.15) + BRASS*mask[...,None]*0.18
    return mask, base

def build():
    pass

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ap=argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=SIZE)
    ap.add_argument("--seed", type=int, default=SEED)
    args=ap.parse_args()
    size=args.size
    seed=args.seed
    rope_normal, rope_height, rope_mask = build_rope_set(size, seed+20)
    barn_mask, barn_col = build_barnacle_waterline(size, seed+30)
    jewel = build_jewel_mask(size, seed+40)
    sail_mask, sail_base = build_sail_damask(size, seed+50)

    images={
        "T_Starskiff_Rope_Normal": (rope_normal,"rgb"),
        "T_Starskiff_Rope_Height": (rope_height,"gray"),
        "T_Starskiff_BarnacleWaterline_Mask": (barn_mask,"gray"),
        "T_Starskiff_Barnacle_BaseColor": (barn_col,"rgb"),
        "T_Starskiff_Jewel_Mask": (jewel,"gray"),
        "T_Starskiff_SailDamask_Mask": (sail_mask,"gray"),
        "T_Starskiff_Sail_Pearl_BaseColor": (sail_base,"rgb"),
    }
    files=[]
    for name,(arr,kind) in images.items():
        p=rc.save_image(OUT/f"{name}.png",arr,kind)
        files.append({"name":name,"path":str(p),"kind":kind,"size":int(size),"seed":seed})
        print(f"[regal v2] wrote {p.name} {kind} {arr.shape}")
    mf=rc.write_manifest(OUT/"starskiff_regal_v2_manifest.json","melodia.starskiff_regal.v2",seed,
        {"generator":"starskiff_regal_suite_v2.py","asset":"rope+barnacle+jewel+sail","tilable":"rope X, barnacle X, jewel XY, sail border"},files)
    print(f"[regal v2] manifest -> {mf}")
    seam=(np.abs(rope_mask[0,:]-rope_mask[-1,:]).mean()+np.abs(rope_mask[:,0]-rope_mask[:,-1]).mean())/2
    print(f"[regal v2] rope seam {seam:.4f} barn max {barn_mask.max():.2f} jewel max {jewel.max():.2f}")

if __name__=="__main__":
    main()
