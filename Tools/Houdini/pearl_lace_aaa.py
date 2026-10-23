import os, numpy as np
from PIL import Image
out_dir="C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Lace"
os.makedirs(out_dir, exist_ok=True)

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def sd_circle(p, r):
    return np.sqrt(p[0]**2 + p[1]**2) - r

def gen_lace(name, base_rgb, blush_rgb, accent_rgb, ornament="floral", roughness_base=0.31, size=4096):
    np.random.seed(abs(hash(name+ornament)) % 2**32)
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # centered coords for tiling
    fx = (x / size * 8) % 1  # 8 repeats
    fy = (y / size * 8) % 1

    # --- PEARL SATIN BASE (AAA, twisted, beveled) ---
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

    # --- LACE MOTIF (opacity + raised embroidery) ---
    # tile-local coordinates
    tx = fx*2 -1  # -1..1 in tile
    ty = fy*2 -1
    dist_center = np.sqrt(tx*tx + ty*ty)
    # lace web: eyelets + threads
    # distance to lace thread: define pattern per ornament
    if ornament == "floral":
        # floral: 5-petal flower center + vine lattice
        ang = np.arctan2(ty, tx)
        petal = np.cos(ang*5)  # 5 petals
        flower = np.clip(1 - dist_center*1.4 + petal*0.18, 0, 1)
        flower = smoothstep(0.35, 0.72, flower)
        # vine lattice: sin lattice
        lattice = np.sin(fx*np.pi*2)*np.sin(fy*np.pi*2)
        lattice = np.abs(lattice)
        lattice = smoothstep(0.45, 0.85, lattice)
        vine = np.clip(lattice*0.9, 0, 1)
        lace = np.maximum(flower*0.95, vine*0.75)
        # eyelet holes: where lace is NOT
        eyelet = np.clip(1 - dist_center*2.2, 0, 1)  # center hole
        eyelet = smoothstep(0.55, 0.9, eyelet) * 0.85
        lace = np.maximum(lace, eyelet*0.3)
    elif ornament == "geometric":
        # geometric: diamond + dot grid, art-deco
        diamond = 1 - (np.abs(tx) + np.abs(ty))*0.85  # diamond sdf
        diamond = smoothstep(0.15, 0.45, np.clip(diamond,0,1))
        dot = np.clip(1 - dist_center*3.0, 0, 1)
        dot = smoothstep(0.6, 0.95, dot)
        lattice_h = np.abs(np.sin(fx*np.pi*2))*0.5 + np.abs(np.sin(fy*np.pi*2))*0.5
        lattice_h = smoothstep(0.5, 0.9, lattice_h)
        lace = np.maximum(diamond*0.9, dot*0.7)
        lace = np.maximum(lace, lattice_h*0.45)
    else: # star / celestial
        ang = np.arctan2(ty, tx)
        # 8-point star
        star = np.cos(ang*4)*0.5 + np.cos(ang*8)*0.3
        star_shape = np.clip(1 - dist_center*1.6 + star*0.22, 0, 1)
        star_shape = smoothstep(0.32, 0.78, star_shape)
        # tiny star freckles
        freckle = (np.sin(fx*30)*np.sin(fy*30) > 0.7).astype(float)*0.5
        # connecting filigree
        filigree = np.abs(np.sin((fx+fy)*np.pi*2))*0.6
        filigree = smoothstep(0.6, 0.95, filigree)
        lace = np.maximum(star_shape*0.92, filigree*0.55)
        lace = np.maximum(lace, freckle)

    # soften lace edges for fabric realism, ensure tilable by blending edge
    lace = np.clip(lace, 0, 1)
    # lace thickness variation (hand-made)
    lace *= (0.92 + 0.08*np.sin(x*0.015 + y*0.013))
    # opacity: lace threads are opaque, eyelets are transparent (cutout)
    # pearl base shows through eyelets with sheer. So opacity = lace coverage + pearl sheen
    # For masked material: white = opaque (thread), black = hole
    # We want lace-dominant with pearl showing in gaps as translucent sheen (still opaque base, but lace defines raised embroidery)
    # So opacity = 1 where lace thread, 0.08 where eyelet hole (sheer)
    opacity = np.clip(lace*0.95 + 0.08, 0, 1)
    # add subtle lace edge fray (painterly)
    opacity = np.clip(opacity + np.random.randn(size,size)*0.012, 0, 1)
    # height: base pearl + raised lace embroidery (lace 1.5mm higher)
    height_lace = lace * 0.55  # emboss height
    height = np.clip(height_base + height_lace + np.random.randn(size,size)*0.008, 0, 1)
    # bevel lace tops
    height = smoothstep(0.0, 1.0, height)

    # normal from final height
    dy,dx=np.gradient(height)
    dx*= 14; dy*=14
    dx += np.random.randn(size,size)*0.07
    dy += np.random.randn(size,size)*0.07
    nx=-dx; ny=-dy; nz=np.ones_like(nx)
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)

    # ALBEDO: pearl base tint + lace ivory + accent metallic thread on lace crests
    base=np.array(base_rgb,float)/255.0
    blush=np.array(blush_rgb,float)/255.0
    accent=np.array(accent_rgb,float)/255.0
    tint=np.where(warp_shift[:,:,None], base, blush)
    s1=0.035*np.sin(x*0.018 + y*0.012)[:,:,None]
    s2=0.025*np.sin(x*0.009 - y*0.022)[:,:,None]
    s3=0.018*np.sin((x+y)*0.006)[:,:,None]
    fleck = 0.02*(np.random.rand(size,size)[:,:,None] > 0.985).astype(float) * (accent - tint)
    wash_color = 0.03*np.sin(x*0.001 + y*0.002)[:,:,None] * np.array([0.02,0.01,-0.01])
    albedo_pearl=np.clip(tint + s1 + s2 + s3 + fleck + wash_color + np.random.randn(size,size,3)*0.012, 0, 1)
    # lace ivory overlay: where lace, shift toward warm ivory + accent on highest crests
    ivory = np.array([0.98,0.96,0.92])
    # accent thread metallic hint on lace peaks (lace >0.7)
    metallic_hint = np.clip((lace-0.65)*2.5,0,1)[:,:,None] * (accent - ivory) * 0.35
    lace_color = ivory + metallic_hint.squeeze() if metallic_hint.ndim==3 else ivory
    # blend pearl and lace by lace coverage
    lace_mask = lace[:,:,None]
    albedo=np.clip(albedo_pearl*(1-lace_mask*0.45) + (ivory+metallic_hint if isinstance(metallic_hint,np.ndarray) else ivory)*lace_mask*0.95,0,1)
    # keep painterly jitter
    albedo=np.clip(albedo,0,1)
    albedo_u8=(albedo*255).astype(np.uint8)

    # ROUGHNESS: pearl crests glossy, lace slightly softer, eyelets sheer
    rough=np.where(height_base>0.62, roughness_base-0.09, roughness_base+0.07)
    rough = np.where(lace>0.5, np.clip(rough+0.04,0.12,0.88), rough)  # lace a touch softer than pearl
    rough += wash_x*0.12 + np.random.randn(size,size)*0.018
    rough=np.clip(rough,0.12,0.88)
    rough_u8=(rough*255).astype(np.uint8)
    metal_u8 = (np.clip((lace-0.65)*3,0,1)*18).astype(np.uint8)  # faint metallic on raised lace only
    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0-(1-height_u8.astype(float)/255.0)*0.45,0,1)
    iri = np.clip((height - 0.5)*1.8,0,1) * (0.7 + 0.3*np.sin(x*0.02))
    # lace gets stronger iridescence on thread
    iri = np.clip(iri + lace*0.25,0,1)
    iri_u8=(iri*255).astype(np.uint8)
    orm=np.stack([(ao*255).astype(np.uint8),rough_u8,metal_u8],axis=-1)
    opacity_u8=(np.clip(opacity,0,1)*255).astype(np.uint8)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, iri_u8, opacity_u8

palettes=[
    ("Moon",(245,242,235),(230,228,222),(235,225,210)),
    ("Blush",(245,232,228),(235,210,205),(255,210,200)),
    ("Dusk",(220,218,230),(200,195,220),(210,200,235)),
]
ornaments=["floral","geometric","star"]

for name, base, blush, accent in palettes:
    for orn in ornaments:
        tag=f"{name}_{orn.capitalize()}"
        print(f"weaving {tag} ...")
        albedo, normal, rough, metal, height, orm, iri, opacity = gen_lace(tag, base, blush, accent, orn, 0.31, 4096)
        prefix=f"T_PearlWoven_Lace_{tag}"
        Image.fromarray(albedo).save(f"{out_dir}/{prefix}_BaseColor.png")
        Image.fromarray(normal).save(f"{out_dir}/{prefix}_Normal.png")
        Image.fromarray(orm).save(f"{out_dir}/{prefix}_ORM.png")
        Image.fromarray(rough).save(f"{out_dir}/{prefix}_Roughness.png")
        Image.fromarray(metal).save(f"{out_dir}/{prefix}_Metallic.png")
        Image.fromarray(height).save(f"{out_dir}/{prefix}_Height.png")
        Image.fromarray(iri).save(f"{out_dir}/{prefix}_Iridescence.png")
        Image.fromarray(opacity).save(f"{out_dir}/{prefix}_Opacity.png")
        print(f"  -> {prefix} done")

print("All lace done. total", len(palettes)*len(ornaments), "variants x 8 maps")
