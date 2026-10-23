import os, numpy as np
from PIL import Image
out_dir = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Serene"
os.makedirs(out_dir, exist_ok=True)

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

# dreamy watercolor wash perlin bloom 0.02 — low freq sin/cos stack = perlin-like
def watercolor_bloom(x,y, amp=0.02):
    # x,y are float32 grids 4096
    b1 = np.sin(x*0.004 + y*0.003) * amp
    b2 = np.cos(y*0.005 - x*0.002) * amp*0.7
    b3 = np.sin((x+y)*0.0025) * amp*0.5
    return b1 + b2 + b3

def gen_serene(fabric, wash_name, base_rgb, blush_rgb, size=4096):
    seed = abs(hash(fabric+"_"+wash_name)) % 2**32
    np.random.seed(seed)
    y,x = np.mgrid[0:size,0:size].astype(np.float32)

    # common bloom
    bloom = watercolor_bloom(x,y, amp=0.02)
    # color bloom tint (warm/cool shift)
    bloom_color = bloom[:,:,None] * np.array([0.12,0.08,-0.06])

    if fabric == "Canvas":
        # COARSE plain weave heavy AO
        warp_period=26
        weft_period=26
        offset = (y // weft_period) % 4
        # coarse threads: wider, flatter crest
        warp_shift = ((x - offset*4.0) % warp_period) < 15
        weft = (y % weft_period) < 6
        over = warp_shift.astype(float)*0.92 + weft.astype(float)*0.22
        # coarse fiber jitter
        fiber = np.random.randn(size,size)*0.022
        # inter-yarn groove
        groove = 0.04*np.sin(x*0.12) + 0.03*np.sin(y*0.12)
        height_base = np.clip(over + fiber + groove + bloom*1.2, 0, 1)
        # heavy bevel: keep flat top
        height = smoothstep(0.18, 0.88, height_base)
        # brush grain heavier for canvas
        brush = np.sin(x*0.10)*np.cos(y*0.09)*0.018
        height = np.clip(height + brush, 0, 1)
        roughness_base = 0.58
        ao_strength = 0.62  # heavy AO
        aniso_strength = 0.06

    elif fabric == "Linen":
        # SLUBBY irregular knots — varying thread thickness + random slubs
        warp_period=22
        weft_period=20
        # irregular weft thickness per row
        row_id = (y // weft_period).astype(int)
        # pseudo random thickness per row using hash of row
        # build row thickness map
        np.random.seed((seed+11)%2**32)
        row_thick = np.random.uniform(0.75, 1.35, size=int(size/weft_period)+2)
        # map to pixel
        weft_thick = row_thick[np.clip(row_id,0,len(row_thick)-1)]
        # warp shift with slight drift (hand-loomed)
        drift = np.sin(y*0.008)*1.8
        offset = (y // weft_period) % 5
        warp_shift = ((x + drift - offset*2.5) % warp_period) < (11 + weft_thick*2)
        weft = (y % weft_period) < (5*weft_thick)
        over = warp_shift.astype(float)*0.88 + weft.astype(float)*0.20
        # slub knots: random ellipses
        knot = np.zeros((size,size), dtype=np.float32)
        nk = 900  # knots count
        rs = np.random.RandomState(seed+99)
        kx = rs.randint(0,size, nk)
        ky = rs.randint(0,size, nk)
        # add slubs as gaussian blobs
        # vectorized via small blot accumulation using loops over chunks
        # use numpy for speed: scatter with additive
        for i in range(nk):
            # random size
            rx = rs.randint(18,42)
            ry = rs.randint(8,18)
            # bounds
            x0=max(0,kx[i]-rx); x1=min(size,kx[i]+rx)
            y0=max(0,ky[i]-ry); y1=min(size,ky[i]+ry)
            if x1<=x0 or y1<=y0:
                continue
            yy,xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            # elliptical falloff
            dx = (xx - kx[i])/rx
            dy = (yy - ky[i])/ry
            d = np.sqrt(dx*dx + dy*dy)
            blob = np.clip(1 - d, 0, 1)
            blob = smoothstep(0.15,0.85,blob)*0.55
            knot[y0:y1, x0:x1] = np.maximum(knot[y0:y1, x0:x1], blob)
        # knot height
        height_base = np.clip(over + knot + np.random.randn(size,size)*0.016 + bloom*0.9, 0, 1)
        height = smoothstep(0.22, 0.86, height_base)
        # extra weave irregularity
        height = np.clip(height + np.sin(x*0.07+y*0.04)*0.012,0,1)
        roughness_base = 0.62
        ao_strength = 0.48
        aniso_strength = 0.08

    else: # Velvet
        # PILE direction + anisotropy — dense short pile streaked vertically
        # base weave hidden under pile
        # directional streaks along Y (pile lay)
        warp_period=14
        weft_period=14
        # very fine base
        warp_shift = (x % warp_period) < 8
        weft = (y % weft_period) < 5
        over = warp_shift.astype(float)*0.55 + weft.astype(float)*0.12
        # pile: anisotropic noise stretched in Y
        # high frequency pile pile
        pile_x = np.sin(x*0.18 + y*0.04)*0.025
        pile_y = np.cos(y*0.22 - x*0.02)*0.035  # stretch Y
        # directional anisotropy streaks
        streak = np.sin(x*0.015 + rs_phase(x,y,seed))*0.04 + np.sin(x*0.03)*0.02
        # pile height: dense, short, soft
        pile = 0.35 + pile_x + pile_y + streak + np.random.randn(size,size)*0.014
        # pile direction gradient: slight lean in +Y (sheen direction)
        direction_bias = np.clip(np.sin(x*0.002)*0.03 + 0.02, -0.03, 0.05)
        height_base = np.clip(over*0.35 + pile*0.85 + direction_bias + bloom*0.6, 0, 1)
        height = smoothstep(0.25, 0.82, height_base)
        # soft top for velvet
        height = np.clip(height*0.92 + 0.06, 0, 1)
        roughness_base = 0.42  # velvet has lower roughness with sheen
        ao_strength = 0.42
        aniso_strength = 0.78  # high

    # gradient normal from final height
    dy,dx = np.gradient(height)
    # scale per fabric for detail preservation
    nscale = 16 if fabric=="Canvas" else (14 if fabric=="Linen" else 12)
    dx*=nscale; dy*=nscale
    # micro fuzz
    fuzz = 0.07 if fabric=="Velvet" else 0.05
    dx += np.random.randn(size,size)*fuzz
    dy += np.random.randn(size,size)*fuzz
    nx = -dx; ny = -dy; nz = np.ones_like(nx)
    nlen = np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal = np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255], axis=-1).astype(np.uint8)

    # ALBEDO: dreamy watercolor wash 0.02 — base tints + bloom + shimmer
    base=np.array(base_rgb,float)/255.0
    blush=np.array(blush_rgb,float)/255.0
    # warp/blush selection per weave (reuse warp_shift if defined else fallback)
    try:
        tint = np.where(warp_shift[:,:,None], base, blush)
    except:
        tint = base
    # nacre shimmer light
    s1=0.02*np.sin(x*0.014 + y*0.011)[:,:,None]
    s2=0.015*np.sin(x*0.008 - y*0.018)[:,:,None]
    # watercolor bloom already computed, add to albedo
    albedo = np.clip(tint + s1 + s2 + bloom_color + np.random.randn(size,size,3)*0.010, 0, 1)
    # dreamy desaturation: slight lift
    albedo = np.clip(albedo*0.98 + 0.015, 0, 1)
    albedo_u8=(albedo*255).astype(np.uint8)

    # ROUGHNESS per fabric with height + bloom
    if fabric=="Velvet":
        # pile direction sheen: anisotropy lowers roughness along streaks
        streak_r = np.sin(x*0.015 + np.random.randn()*0.0)*0.5+0.5 # reused magnitude
        # directional roughness: along pile more glossy
        rough = np.where(height>0.55, roughness_base-0.07, roughness_base+0.05)
        # velvet sheen band
        sheen = np.clip(np.sin(x*0.015)*0.5+0.5,0,1)*0.06
        rough = rough - sheen
        rough += bloom*0.8 + np.random.randn(size,size)*0.015
    else:
        rough = np.where(height>0.60, roughness_base-0.08, roughness_base+0.06)
        rough += bloom*0.9 + np.random.randn(size,size)*0.018
    rough=np.clip(rough,0.12,0.88)
    rough_u8=(rough*255).astype(np.uint8)
    metal_u8=np.zeros((size,size),dtype=np.uint8)
    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0 - (1-height_u8.astype(float)/255.0)*ao_strength, 0, 1)
    ao_u8=(ao*255).astype(np.uint8)
    orm=np.stack([ao_u8, rough_u8, metal_u8], axis=-1)

    # ANISOTROPY map: velvet strong directional, others flat
    if fabric=="Velvet":
        # pile direction: horizontal variation = anisotropy strength, plus direction in G channel? single channel grayscale for anisotropy amount
        # use x streaks: anisotropy high (≈0.7) with variation
        aniso = 0.55 + 0.25*np.sin(x*0.018 + y*0.005) + 0.10*np.cos(y*0.03)
        aniso = np.clip(aniso + np.random.randn(size,size)*0.04, 0, 1)
    elif fabric=="Linen":
        aniso = np.clip(0.08 + knot*0.22 + np.random.randn(size,size)*0.02, 0, 1) if 'knot' in locals() else np.clip(0.06+np.random.randn(size,size)*0.02,0,1)
    else: # Canvas
        aniso = np.clip(0.05 + np.random.randn(size,size)*0.015, 0, 1)
    aniso_u8=(np.clip(aniso,0,1)*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, ao_u8, aniso_u8

def rs_phase(x,y,seed):
    # deterministic phase offset per seed
    return (seed % 1000)*0.001 + y*0.0005

palettes=[
    ("Moon",(245,242,235),(230,228,222)),
    ("Blush",(245,232,228),(235,210,205)),
    ("Dusk",(220,218,230),(200,195,220)),
]
fabrics=["Canvas","Linen","Velvet"]

total=0
for fabric in fabrics:
    for name,base,blush in palettes:
        tag=f"{fabric}_{name}"
        print(f"Serene AAA {tag} 4K ... fabric={fabric} wash={name} bloom=0.02")
        albedo,normal,rough,metal,height,orm,ao,aniso = gen_serene(fabric, name, base, blush, 4096)
        prefix=f"T_PearlWoven_Serene_{tag}"
        Image.fromarray(albedo).save(os.path.join(out_dir, f"{prefix}_BaseColor.png"))
        Image.fromarray(normal).save(os.path.join(out_dir, f"{prefix}_Normal.png"))
        Image.fromarray(orm).save(os.path.join(out_dir, f"{prefix}_ORM.png"))
        Image.fromarray(rough).save(os.path.join(out_dir, f"{prefix}_Roughness.png"))
        Image.fromarray(metal).save(os.path.join(out_dir, f"{prefix}_Metallic.png"))
        Image.fromarray(height).save(os.path.join(out_dir, f"{prefix}_Height.png"))
        Image.fromarray(ao).save(os.path.join(out_dir, f"{prefix}_AO.png"))
        Image.fromarray(aniso).save(os.path.join(out_dir, f"{prefix}_Anisotropy.png"))
        print(f"  -> {prefix} done (8 maps: BC/N/ORM/R/M/H/AO/Aniso)")
        total+=1

print(f"Serene AAA DONE total {total} variants x 8 maps ({total*8} files) in {out_dir}")
print(f"Core 7-map count per variant: 56 files (if counting AO as 7th) | with Anisotropy bonus 72 files")
