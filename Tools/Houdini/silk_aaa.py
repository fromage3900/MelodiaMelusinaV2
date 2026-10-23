import os, numpy as np
from PIL import Image
out_dir="C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Silk"
os.makedirs(out_dir, exist_ok=True)

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def gen_silk(name, base_rgb, blush_rgb, accent_rgb, roughness_base=0.20, size=4096):
    np.random.seed(abs(hash(name)) % 2**32)
    y,x = np.mgrid[0:size,0:size].astype(np.float32)

    # --- TIGHT SILK WEAVE (AAA) ---
    # Charmeuse / satin: long floats, very fine threads (6-8px), subtle diagonal drift
    warp_period = 7
    weft_period = 7
    # satin float: warp dominates (5/7), weft short (2/7) — high luster
    # gentle bias twist for living drape
    bias = y * 0.00005
    x_biased = x + np.sin(bias*12)*1.8
    # satin interlock offset (7-end satin: step 3)
    offset = (y // weft_period) * 3  # classic satin stepping
    warp_float = ((x_biased - offset*2.1) % warp_period) < 5  # 5 warp over 2 weft
    weft_float = ~warp_float
    # thread profile: rounded crest (bevel) + subtle slub variation
    over = warp_float.astype(float)*0.96 + weft_float.astype(float)*0.14
    # thread thickness — hand-thrown silk slub (irregular)
    slub = 0.022*np.sin(x*0.11 + y*0.09) + 0.015*np.sin(x*0.037 - y*0.041)
    # fiber micro: ultra-fine filament noise (already silk is smoother than wool)
    fiber = np.random.randn(size,size)*0.010
    # large painterly dreamy wash — watercolor clouds at ~200-400px scale
    wash_a = np.sin(x*0.0028 + y*0.0019)*0.045
    wash_b = np.cos(y*0.0022 - x*0.0016)*0.035
    wash_c = np.sin((x*0.7 + y*1.1)*0.0017)*0.028  # diagonal watercolor drift
    wash_d = np.sin(x*0.0009 + y*0.0013)*0.02 * np.cos(y*0.0011)  # very large cloud
    # height: bi-level satin + slub + wash + fiber
    height_base = np.clip(over + slub + fiber + wash_a*0.6 + wash_b*0.5 + wash_c*0.4 + wash_d, 0, 1)
    # soft bevel for silk (softer than lace/painterly — silk threads are flattened/filled)
    height_base = smoothstep(0.28, 0.82, height_base)
    # brush grain — fine silk filament directionality (warp-aligned)
    brush_warp = np.sin(x*0.22)*np.cos(y*0.08)*0.010  # along warp
    brush_weft = np.sin(y*0.18)*0.006
    height_base = np.clip(height_base + brush_warp + brush_weft, 0, 1)
    # second-order crinkle for drape (very low freq, subtle folds)
    drape = 0.012*np.sin(x*0.004 + y*0.006) + 0.008*np.cos(x*0.003 - y*0.007)
    height = np.clip(height_base + drape, 0, 1)

    # --- NORMAL — VERY SOFT (silk is near-flat, filled weave) ---
    dy,dx = np.gradient(height)
    dx *= 5.5; dy *= 5.5  # much softer than lace (14) / painterly (14)
    # tiny filament jitter (silk fuzz is minimal)
    dx += np.random.randn(size,size)*0.035
    dy += np.random.randn(size,size)*0.035
    # add subtle anisotropic warp streak in normal (silk sheen direction)
    dx += np.sin(y*0.05)*0.015
    nx=-dx; ny=-dy; nz=np.ones_like(nx)*1.35  # boost Z for flatter normal
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)

    # --- ALBEDO — painterly dreamy wash, nacre + thin-film tint ---
    base=np.array(base_rgb,float)/255.0
    blush=np.array(blush_rgb,float)/255.0
    accent=np.array(accent_rgb,float)/255.0
    # warp/weft tint: warp = base, weft = blush (subtle 2-tone)
    tint=np.where(warp_float[:,:,None], base, blush)
    # triple nacre shimmer layers (pearlescent)
    s1=0.032*np.sin(x*0.019 + y*0.013)[:,:,None]
    s2=0.024*np.sin(x*0.010 - y*0.023)[:,:,None]
    s3=0.017*np.sin((x+y)*0.007)[:,:,None]
    # dreamy watercolor wash — tint oscillates between base/blush/accent at large scale
    # use wash fields to modulate toward accent (thin-film hue)
    wash_mix = (np.sin(x*0.0012 + y*0.0008)*0.5+0.5)*0.06 + (np.cos(y*0.0015 - x*0.001)*0.5+0.5)*0.04
    wash_color = wash_mix[:,:,None] * (accent - base) * 0.55
    # accent pearl dust — sparse
    fleck = 0.016*(np.random.rand(size,size)[:,:,None] > 0.988).astype(float) * (accent - tint)*0.8
    # very large cloud tint
    cloud = 0.018*np.sin(x*0.0007 + y*0.0009)[:,:,None] * np.array([0.015,0.008,-0.012])
    albedo=np.clip(tint + s1 + s2 + s3 + wash_color + fleck + cloud, 0, 1)
    # hand-mixed pigment jitter
    albedo=np.clip(albedo + np.random.randn(size,size,3)*0.009, 0, 1)
    # slight luminous bloom on warp crests (silk specular tint baked lightly into albedo)
    crest = np.clip((height - 0.58)*1.6, 0, 1)[:,:,None]
    albedo=np.clip(albedo + crest*0.035* (np.array([1.02,1.01,0.98])-1)*0 + crest*0.018, 0, 1)
    # ensure dreamy softness: very subtle desat toward center wash
    albedo=np.clip(albedo, 0, 1)
    albedo_u8=(np.clip(albedo,0,1)*255).astype(np.uint8)

    # --- ROUGHNESS — LOW 0.18-0.25, crest glossy, valley slightly higher ---
    # silk is highly polished; use roughness_base per colourway
    rough=np.where(height>0.60, roughness_base-0.045, roughness_base+0.045)
    # large wash modulates roughness (clouds = slightly different polish)
    rough += wash_a*0.06 + wash_b*0.04 + np.random.randn(size,size)*0.012
    rough=np.clip(rough, 0.14, 0.42)
    rough_u8=(rough*255).astype(np.uint8)

    # --- METALLIC — essentially 0 for silk (dielectric), faint 0-8 on accent fleck only ---
    # thin-film is dielectric iridescence, not metallic
    metal = np.zeros((size,size), dtype=np.float32)
    # only the sparse pearl dust flecks get a whisper of metallic hint (crushed pearl)
    fleck_mask = (np.random.rand(size,size) > 0.988).astype(float) * np.clip((height-0.55)*2,0,1)
    metal = np.clip(fleck_mask*0.06, 0, 0.06)
    metal_u8=(metal*255).astype(np.uint8)

    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0-(1-height_u8.astype(float)/255.0)*0.33,0,1)  # softer AO for flat silk

    # --- IRIDESCENCE — THIN-FILM: strong, angle-dependent, rainbow on crests ---
    # base iridescence tied to height crest + large interference pattern
    # create interference bands (thin-film Newton rings at silk scale)
    interference = 0.5+0.5*np.sin(x*0.015 + y*0.012 + wash_a*8)
    interference2 = 0.5+0.5*np.sin(x*0.028 - y*0.018)
    # crest-weighted thin film
    crest01 = np.clip((height - 0.42)*1.4, 0, 1)
    iri = crest01 * (0.55 + 0.30*interference + 0.15*interference2)
    # dreamy large-scale modulation (wash clouds shift interference hue strength)
    iri *= (0.85 + 0.15*np.sin(x*0.0011 + y*0.0014))
    # subtle filament-direction streak
    iri *= (0.96 + 0.04*np.sin(y*0.06))
    iri = np.clip(iri + np.random.randn(size,size)*0.015, 0, 1)
    # remap for thin-film: bias toward 0.3-0.95 so it reads as subtle rainbow, not binary
    iri = np.clip(iri*0.85 + 0.08, 0, 1)
    iri_u8=(iri*255).astype(np.uint8)

    orm=np.stack([(ao*255).astype(np.uint8),rough_u8,metal_u8],axis=-1)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, iri_u8

palettes=[
    ("Moon", (246,243,238),(232,230,226),(235,225,215),0.19),
    ("Blush",(248,233,229),(238,212,207),(255,210,205),0.20),
    ("Dusk", (224,220,233),(202,197,221),(212,200,238),0.22),
    ("Mist", (228,238,236),(210,225,223),(195,220,230),0.18),
    ("Haze", (222,228,233),(205,215,222),(200,210,225),0.21),
    ("Ember",(248,235,222),(238,218,200),(255,192,160),0.24),
]

for name, base, blush, accent, rough in palettes:
    print(f"Silk AAA {name} 4K (rough {rough}) ...")
    albedo, normal, rough_u8, metal_u8, height_u8, orm, iri_u8 = gen_silk(name, base, blush, accent, rough, 4096)
    prefix=f"T_PearlWoven_Silk_{name}"
    Image.fromarray(albedo).save(f"{out_dir}/{prefix}_BaseColor.png")
    Image.fromarray(normal).save(f"{out_dir}/{prefix}_Normal.png")
    Image.fromarray(orm).save(f"{out_dir}/{prefix}_ORM.png")
    Image.fromarray(rough_u8).save(f"{out_dir}/{prefix}_Roughness.png")
    Image.fromarray(metal_u8).save(f"{out_dir}/{prefix}_Metallic.png")
    Image.fromarray(height_u8).save(f"{out_dir}/{prefix}_Height.png")
    Image.fromarray(iri_u8).save(f"{out_dir}/{prefix}_Iridescence.png")
    print(f"  -> {prefix} 7 maps done")

print(f"All silk done. total {len(palettes)} variants x 7 maps = {len(palettes)*7} files in {out_dir}")
