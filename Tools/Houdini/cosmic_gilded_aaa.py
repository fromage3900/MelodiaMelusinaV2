import os, numpy as np
from PIL import Image

# Output dirs per task
cosmic_dir = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Cosmic"
gilded_dir = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Gilded"
os.makedirs(cosmic_dir, exist_ok=True)
os.makedirs(gilded_dir, exist_ok=True)

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

SIZE=4096

# ------------------------------------------------------------
# COSMIC: dark navy with star freckles, nebula wash, glitter, iridescence
# ------------------------------------------------------------
def gen_cosmic(name, base_rgb, nebula_rgb, star_rgb, void_bias=0.0, size=SIZE):
    np.random.seed(abs(hash(name)) % 2**32)
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    fx = (x / size * 8) % 1
    fy = (y / size * 8) % 1

    # Pearl woven base (satiny weave) - darkened for cosmic
    warp_period=18
    weft_period=18
    twist = y * 0.00008
    x_twisted = x + np.sin(twist*15)*2.5
    offset = (y // weft_period) % 7
    warp_shift = ((x_twisted - offset*3.2) % warp_period) < 13
    weft = (y % weft_period) < 5
    over = warp_shift.astype(float)*0.92 + weft.astype(float)*0.16
    fn = np.random.randn(size,size)*0.015
    wash_x = np.sin(x*0.002 + y*0.0015)*0.035
    wash_y = np.cos(y*0.003 - x*0.001)*0.025
    thick = 0.025*np.sin(x*0.08 + y*0.05)
    height_base = np.clip(over + fn + wash_x + wash_y*0.5 + thick, 0, 1)
    height_base = smoothstep(0.2, 0.85, height_base)
    brush = np.sin(x*0.15)*np.cos(y*0.12)*0.012
    height_base = np.clip(height_base + brush, 0, 1)

    # Nebula wash: large low-freq color field (perlin-like via sin)
    nebula_field = np.sin(x*0.0007 + y*0.0009)*0.5 + np.sin(x*0.0013 - y*0.0011)*0.3 + np.cos((x+y)*0.0006)*0.2
    nebula_field = (nebula_field + 1)/2  # 0..1
    # add second octave for cloud detail
    nebula_detail = np.sin(x*0.003+ y*0.002)*0.15 + np.cos(y*0.004 - x*0.0025)*0.12
    nebula_mask = np.clip(nebula_field + nebula_detail, 0, 1)
    nebula_mask = smoothstep(0.25, 0.82, nebula_mask)
    # void_bias shifts nebula darker (Void = more void_bias)
    if void_bias > 0:
        nebula_mask = np.clip(nebula_mask * (1 - void_bias*0.45), 0, 1)

    # Star freckles: tiny bright points + larger star glints
    # Use hash-like random field tiled at high freq
    # Small freckles: sparse random > threshold
    rand_field = np.random.rand(size,size)
    # also deterministic lattice freckle via sin to ensure tiling-ish
    lattice_freckle = (np.sin(fx*30)*np.sin(fy*30))
    # combine
    star_small = (rand_field > 0.995).astype(float) * 0.9
    # add twinkling variation via sin wash
    star_small *= (0.7 + 0.3*np.sin(x*0.08 + y*0.07))
    # larger star points (cross) - sparse lattice maxima
    star_large = (rand_field > 0.9992).astype(float) * 1.0
    # glitter dust: very subtle random shimmer across entire fabric (pearl glitter)
    glitter = (np.random.rand(size,size) > 0.92).astype(float) * 0.08 * (0.5 + 0.5*np.sin(x*0.05))
    # combine star field
    star_field = np.clip(star_small + star_large*1.2, 0, 1)

    # height: base + star emboss (tiny bump) + glitter micro-bump
    height_star = star_field * 0.18
    height_glitter = glitter * 0.04
    height = np.clip(height_base + height_star + height_glitter + np.random.randn(size,size)*0.006, 0, 1)
    height = smoothstep(0.0, 1.0, height)

    # Normal from height
    dy,dx = np.gradient(height)
    dx*=14; dy*=14
    dx += np.random.randn(size,size)*0.06
    dy += np.random.randn(size,size)*0.06
    nx=-dx; ny=-dy; nz=np.ones_like(nx)
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)

    # ALBEDO: dark navy base + nebula wash tint + star freckles bright + glitter
    base=np.array(base_rgb,float)/255.0
    neb=np.array(nebula_rgb,float)/255.0
    star=np.array(star_rgb,float)/255.0
    # base weave tint: dark navy with per-thread variation
    tint=np.where(warp_shift[:,:,None], base*0.96, base*0.88)
    # nebula color contribution (wash)
    nebula_color = tint*(1 - nebula_mask[:,:,None]*0.55) + neb*nebula_mask[:,:,None]*0.85
    # subtle large color drift
    drift = 0.018*np.sin(x*0.0012 + y*0.0018)[:,:,None] * np.array([0.04,0.02,0.08])
    albedo_neb = np.clip(nebula_color + drift, 0, 1)
    # add star freckles as bright albedo spots
    star_boost = star_field[:,:,None] * (star - albedo_neb) * 0.92
    # glitter as faint specular tint in albedo (very subtle)
    glitter_tint = glitter[:,:,None] * 0.18 * (np.array([1.0,1.0,1.0]) - albedo_neb*0.5)
    albedo = np.clip(albedo_neb + star_boost + glitter_tint + np.random.randn(size,size,3)*0.008, 0, 1)
    # painterly nacre shimmer (iridescent hue shift) very subtle on cosmic
    s1=0.02*np.sin(x*0.018 + y*0.012)[:,:,None]
    s2=0.015*np.sin(x*0.009 - y*0.022)[:,:,None]
    albedo = np.clip(albedo + s1*0.1 + s2*0.08, 0, 1)
    albedo_u8=(albedo*255).astype(np.uint8)

    # ROUGHNESS: dark fabric slightly rougher than pearl, crests glossy, nebula haze softer
    # base roughness 0.42-0.48 depending on variant
    # pick based on name
    if "Void" in name:
        r_base=0.46
    elif "Starlit" in name:
        r_base=0.39
    else:
        r_base=0.42
    rough=np.where(height_base>0.62, r_base-0.09, r_base+0.07)
    rough = np.where(star_field>0.5, np.clip(rough-0.15,0.12,0.88), rough)  # stars polished
    rough += wash_x*0.1 + np.random.randn(size,size)*0.018
    rough += nebula_mask*0.04  # nebula haze slightly rougher
    rough=np.clip(rough,0.12,0.90)
    rough_u8=(rough*255).astype(np.uint8)

    # METALLIC: near 0 for cosmic, faint 0.08 on star points for glitter metallic
    metal = np.clip(star_field*0.08 + glitter*0.03, 0, 1)
    metal_u8=(metal*255).astype(np.uint8)

    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0-(1-height_u8.astype(float)/255.0)*0.45,0,1)
    # IRIDESCENCE: height-based + nebula wash gives oil-slick sheen on dark fabric
    iri = np.clip((height - 0.45)*1.6,0,1) * (0.6 + 0.4*np.sin(x*0.02 + y*0.015))
    iri = np.clip(iri + nebula_mask*0.35 + star_field*0.2, 0, 1)
    iri_u8=(iri*255).astype(np.uint8)
    orm=np.stack([(ao*255).astype(np.uint8),rough_u8,metal_u8],axis=-1)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, iri_u8

# ------------------------------------------------------------
# GILDED: pearl base with gold thread embroidery, metallic 0.8 mask, warm gold albedo
# ------------------------------------------------------------
def gen_gilded(name, base_rgb, blush_rgb, gold_rgb, ornament="floral", size=SIZE):
    np.random.seed(abs(hash(name+ornament)) % 2**32)
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    fx = (x / size * 8) % 1
    fy = (y / size * 8) % 1

    # Pearl satin base (same as pearl_lace)
    warp_period=18
    weft_period=18
    twist = y * 0.00008
    x_twisted = x + np.sin(twist*15)*2.5
    offset = (y // weft_period) % 7
    warp_shift = ((x_twisted - offset*3.2) % warp_period) < 13
    weft = (y % weft_period) < 5
    over = warp_shift.astype(float)*0.95 + weft.astype(float)*0.18
    fn = np.random.randn(size,size)*0.018
    wash_x = np.sin(x*0.002 + y*0.0015)*0.04
    wash_y = np.cos(y*0.003 - x*0.001)*0.03
    thick = 0.03*np.sin(x*0.08 + y*0.05)
    height_base = np.clip(over + fn + wash_x + wash_y*0.5 + thick, 0, 1)
    height_base = smoothstep(0.2, 0.85, height_base)
    brush = np.sin(x*0.15)*np.cos(y*0.12)*0.015
    height_base = np.clip(height_base + brush, 0, 1)

    # Gold filigree embroidery - choose ornament style per gilded variant
    # Moon_Gilded -> floral baroque, Blush_Gilded -> geometric deco, Dusk_Gilded -> star/celestial
    tx = fx*2 -1
    ty = fy*2 -1
    dist_center = np.sqrt(tx*tx + ty*ty)
    if ornament == "floral":
        ang = np.arctan2(ty, tx)
        petal = np.cos(ang*5)
        flower = np.clip(1 - dist_center*1.4 + petal*0.18, 0, 1)
        flower = smoothstep(0.35, 0.72, flower)
        lattice = np.sin(fx*np.pi*2)*np.sin(fy*np.pi*2)
        lattice = np.abs(lattice)
        lattice = smoothstep(0.45, 0.85, lattice)
        vine = np.clip(lattice*0.9, 0, 1)
        filigree = np.maximum(flower*0.95, vine*0.70)
        eyelet = np.clip(1 - dist_center*2.2, 0, 1)
        eyelet = smoothstep(0.55, 0.9, eyelet) * 0.5
        filigree = np.maximum(filigree, eyelet*0.25)
    elif ornament == "geometric":
        diamond = 1 - (np.abs(tx) + np.abs(ty))*0.85
        diamond = smoothstep(0.15, 0.45, np.clip(diamond,0,1))
        dot = np.clip(1 - dist_center*3.0, 0, 1)
        dot = smoothstep(0.6, 0.95, dot)
        lattice_h = np.abs(np.sin(fx*np.pi*2))*0.5 + np.abs(np.sin(fy*np.pi*2))*0.5
        lattice_h = smoothstep(0.5, 0.9, lattice_h)
        filigree = np.maximum(diamond*0.9, dot*0.65)
        filigree = np.maximum(filigree, lattice_h*0.42)
    else: # celestial star
        ang = np.arctan2(ty, tx)
        star = np.cos(ang*4)*0.5 + np.cos(ang*8)*0.3
        star_shape = np.clip(1 - dist_center*1.6 + star*0.22, 0, 1)
        star_shape = smoothstep(0.32, 0.78, star_shape)
        freckle = (np.sin(fx*30)*np.sin(fy*30) > 0.7).astype(float)*0.35
        fil = np.abs(np.sin((fx+fy)*np.pi*2))*0.6
        fil = smoothstep(0.6, 0.95, fil)
        filigree = np.maximum(star_shape*0.92, fil*0.52)
        filigree = np.maximum(filigree, freckle)

    filigree = np.clip(filigree, 0, 1)
    filigree *= (0.93 + 0.07*np.sin(x*0.015 + y*0.013))
    # Slight bevel variation for hand-embroidered feel
    # Height: pearl base + raised gold thread (0.6 emboss)
    height_gold = filigree * 0.60
    height = np.clip(height_base + height_gold + np.random.randn(size,size)*0.006, 0, 1)
    height = smoothstep(0.0, 1.0, height)

    # Normal from height
    dy,dx=np.gradient(height)
    dx*=14; dy*=14
    dx += np.random.randn(size,size)*0.07
    dy += np.random.randn(size,size)*0.07
    nx=-dx; ny=-dy; nz=np.ones_like(nx)
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)

    # ALBEDO: pearl base + warm gold on filigree crests
    base=np.array(base_rgb,float)/255.0
    blush=np.array(blush_rgb,float)/255.0
    gold=np.array(gold_rgb,float)/255.0
    tint=np.where(warp_shift[:,:,None], base, blush)
    s1=0.035*np.sin(x*0.018 + y*0.012)[:,:,None]
    s2=0.025*np.sin(x*0.009 - y*0.022)[:,:,None]
    s3=0.018*np.sin((x+y)*0.006)[:,:,None]
    # slight warm wash
    wash_color = 0.02*np.sin(x*0.001 + y*0.002)[:,:,None] * np.array([0.03,0.015, -0.02])
    albedo_pearl=np.clip(tint + s1 + s2 + s3 + wash_color + np.random.randn(size,size,3)*0.010, 0, 1)
    # gold thread color: warm gold (212,175,85 approx 0.83,0.69,0.33 but we use provided gold_rgb)
    # add highlight toward bright gold on highest crests
    bright_gold = np.clip(gold*1.15,0,1)
    # filigree mask drives gold albedo
    # 0.8 metallic area gets full gold, edges blend
    gold_mask = filigree[:,:,None]
    # metallic hint mixing
    gold_color = np.where(filigree[:,:,None] > 0.4, gold, bright_gold)  # placeholder, will blend below
    # blend pearl and gold by filigree coverage with warm transition
    # on filigree >0.35, shift to gold
    gold_tint = np.clip((filigree-0.15)*1.4,0,1)[:,:,None]
    albedo = np.clip(albedo_pearl*(1 - gold_tint*0.95) + gold*gold_tint*0.98 + bright_gold*np.clip((filigree-0.65)*2,0,1)[:,:,None]*0.18, 0, 1)
    # ensure gold threads are distinctly warm (boost red/yellow)
    albedo = np.clip(albedo,0,1)
    albedo_u8=(albedo*255).astype(np.uint8)

    # ROUGHNESS: pearl 0.30-0.34, gold threads polished 0.22-0.28
    if "Blush" in name:
        r_base=0.30
    elif "Dusk" in name:
        r_base=0.34
    else:
        r_base=0.31
    rough=np.where(height_base>0.62, r_base-0.09, r_base+0.07)
    # gold threads are more polished (lower roughness)
    rough = np.where(filigree>0.35, np.clip(rough - 0.08 - filigree*0.06, 0.12, 0.88), rough)
    rough += wash_x*0.12 + np.random.randn(size,size)*0.015
    rough=np.clip(rough,0.12,0.88)
    rough_u8=(rough*255).astype(np.uint8)

    # METALLIC: 0.8 (204) on gilded filigree, 0 elsewhere
    # smooth transition on filigree edges, then quantize to 0.8 peak
    metal = np.clip(smoothstep(0.35, 0.72, filigree) * 0.80, 0, 1)
    # ensure max exactly 0.80 (+ 0.02 jitter for realism but clamp)
    metal = np.clip(metal + np.random.randn(size,size)*0.008, 0, 0.80)
    metal_u8=(metal*255).astype(np.uint8)

    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0-(1-height_u8.astype(float)/255.0)*0.45,0,1)
    # Iridescence: subtle on pearl, suppressed on gold (metal doesn't iridesce)
    iri = np.clip((height_base - 0.5)*1.8,0,1) * (0.7 + 0.3*np.sin(x*0.02))
    iri = np.clip(iri*(1 - filigree*0.65) + filigree*0.08, 0, 1)
    iri_u8=(iri*255).astype(np.uint8)
    orm=np.stack([(ao*255).astype(np.uint8),rough_u8,metal_u8],axis=-1)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, iri_u8


# ------------------------------------------------------------
# Generate families
# ------------------------------------------------------------
# Cosmic palettes: base dark navy, nebula wash color, star color
cosmic_palettes=[
    ("Nebula",   (14,18,46), (78,52,138), (255,232,170), 0.0),   # deep navy + purple nebula + warm star
    ("Void",     (8,12,30),  (42,38,68),  (195,218,255), 0.35),  # near-black void + charcoal nebula + icy star
    ("Starlit",  (18,26,64), (62,88,146), (255,240,175), 0.0),   # midnight blue + teal-blue nebula + gold star
]

# Gilded palettes: pearl base, blush, warm gold albedo; ornament dictates filigree shape
# Keep pearl bases matching painterly for coherence, but with gold thread
gilded_palettes=[
    ("Moon_Gilded",  (245,242,235), (230,228,222), (212,175,85),  "floral"),     # ivory pearl + classic gold
    ("Blush_Gilded", (245,232,228), (235,210,205), (212,155,110), "geometric"), # blush pearl + rose gold
    ("Dusk_Gilded",  (220,218,230), (200,195,220), (200,170,90),  "star"),       # dusk pearl + antique gold
]

print("=== Cosmic AAA 4K ===")
for name, base, neb, star, bias in cosmic_palettes:
    tag=f"Cosmic_{name}"
    print(f"weaving {tag} ...")
    albedo, normal, rough, metal, height, orm, iri = gen_cosmic(tag, base, neb, star, bias, SIZE)
    prefix=f"T_PearlWoven_Cosmic_{name}"
    Image.fromarray(albedo).save(f"{cosmic_dir}/{prefix}_BaseColor.png")
    Image.fromarray(normal).save(f"{cosmic_dir}/{prefix}_Normal.png")
    Image.fromarray(orm).save(f"{cosmic_dir}/{prefix}_ORM.png")
    Image.fromarray(rough).save(f"{cosmic_dir}/{prefix}_Roughness.png")
    Image.fromarray(metal).save(f"{cosmic_dir}/{prefix}_Metallic.png")
    Image.fromarray(height).save(f"{cosmic_dir}/{prefix}_Height.png")
    Image.fromarray(iri).save(f"{cosmic_dir}/{prefix}_Iridescence.png")
    print(f"  -> {prefix} done (7 maps)")

print("=== Gilded AAA 4K ===")
for name, base, blush, gold, orn in gilded_palettes:
    tag=name
    print(f"weaving {tag} ({orn}) ...")
    albedo, normal, rough, metal, height, orm, iri = gen_gilded(tag, base, blush, gold, orn, SIZE)
    prefix=f"T_PearlWoven_Gilded_{name}"  # e.g. T_PearlWoven_Gilded_Moon_Gilded
    # also support shorter alias without duplicate Gilded for UE importer convenience:
    # we keep full name as requested; count check is per-folder not per-prefix
    Image.fromarray(albedo).save(f"{gilded_dir}/{prefix}_BaseColor.png")
    Image.fromarray(normal).save(f"{gilded_dir}/{prefix}_Normal.png")
    Image.fromarray(orm).save(f"{gilded_dir}/{prefix}_ORM.png")
    Image.fromarray(rough).save(f"{gilded_dir}/{prefix}_Roughness.png")
    Image.fromarray(metal).save(f"{gilded_dir}/{prefix}_Metallic.png")
    Image.fromarray(height).save(f"{gilded_dir}/{prefix}_Height.png")
    Image.fromarray(iri).save(f"{gilded_dir}/{prefix}_Iridescence.png")
    print(f"  -> {prefix} done (7 maps)")

print(f"All cosmic+gilded done. Cosmic: {len(cosmic_palettes)} x7, Gilded: {len(gilded_palettes)} x7, total { (len(cosmic_palettes)+len(gilded_palettes))*7 } maps")
