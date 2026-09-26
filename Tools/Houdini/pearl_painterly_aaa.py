import os, numpy as np
from PIL import Image, ImageFilter
out_dir="C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Painterly_4K"
os.makedirs(out_dir, exist_ok=True)

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def gen_painterly(name, base_rgb, blush_rgb, accent_rgb, roughness_base, size=4096):
    np.random.seed(hash(name)%2**32)
    y,x=np.mgrid[0:size,0:size].astype(np.float32)
    # AAA satin with spinning weave - slight twist per row for living feel
    # TRUE interlaced weave: thin threads, 2/2 twill over/under step (AAA satin)
    p = 18.0
    twist = (y * 0.00008)                    # spin: living weave drift
    x_twisted = x + np.sin(twist*15)*2.5
    wx = ((x_twisted % p) / p) - 0.5         # across warp cell
    wy = ((y % p) / p) - 0.5                 # across weft cell
    warp_thread = 1.0 - smoothstep(0.14, 0.40, np.abs(wx))
    weft_thread = 1.0 - smoothstep(0.14, 0.40, np.abs(wy))
    cx = np.floor(x_twisted / p).astype(np.int32)
    cy = np.floor(y / p).astype(np.int32)
    warp_up = (((cx + 2*cy) % 4) < 2).astype(np.float32)   # 2/2 twill float
    h_weave = np.maximum(warp_thread * warp_up, weft_thread * (1.0 - warp_up))
    over = 0.25 + 0.70 * h_weave             # raised valleys: no black holes
    warp_shift = warp_thread > 0.45          # thread-level tint mask (albedo)
    # thread fiber micro-detail: per-thread anisotropy noise (painterly)
    fn = np.random.randn(size,size)*0.018
    # larger painterly wash: low-freq watercolor variation
    wash_x = np.sin(x*0.002 + y*0.0015)*0.04
    wash_y = np.cos(y*0.003 - x*0.001)*0.03
    # thread thickness variation (hand-loomed)
    thick = 0.03*np.sin(x*0.08 + y*0.05)
    height = np.clip(over + fn + wash_x + wash_y*0.5 + thick, 0, 1)
    # bevel for soft crest (triple-A)
    # use smoothstep on height for rounded thread top
    height = smoothstep(0.2, 0.85, height)
    # emboss height with subtle brush grain
    brush = np.sin(x*0.15)*np.cos(y*0.12)*0.015
    height = np.clip(height + brush, 0, 1)
    # normal from height - higher fidelity sobel with painterly scale
    dy,dx=np.gradient(height)
    dx*= 14; dy*=14
    # add micro-normal jitter for fabric fuzz
    dx += np.random.randn(size,size)*0.08
    dy += np.random.randn(size,size)*0.08
    nx=-dx; ny=-dy; nz=np.ones_like(nx)
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)
    # ALBEDO - painterly: base + blush + accent iridescence + watercolor wash
    base=np.array(base_rgb,float)/255.0
    blush=np.array(blush_rgb,float)/255.0
    accent=np.array(accent_rgb,float)/255.0
    tint=np.where(warp_shift[:,:,None], base, blush)
    # nacre shimmer - triple layer
    s1=0.035*np.sin(x*0.018 + y*0.012)[:,:,None]
    s2=0.025*np.sin(x*0.009 - y*0.022)[:,:,None]
    s3=0.018*np.sin((x+y)*0.006)[:,:,None]
    # accent flecks like pearl dust
    fleck = 0.02*(np.random.rand(size,size)[:,:,None] > 0.985).astype(float) * (accent - tint)
    wash_color = 0.03*np.sin(x*0.001 + y*0.002)[:,:,None] * np.array([0.02,0.01,-0.01])
    albedo=np.clip(tint + s1 + s2 + s3 + fleck + wash_color, 0, 1)
    # painterly jitter: hand-mixed pigment
    jitter=np.random.randn(size,size,3)*0.012
    albedo=np.clip(albedo + jitter, 0, 1)
    # slight bloom on highlights (painterly)
    albedo_u8=(albedo*255).astype(np.uint8)
    # ROUGHNESS - AAA: crest glossy, valley soft, with painterly variation
    rough=np.where(height>0.62, roughness_base-0.09, roughness_base+0.07)
    # add broad wash variation
    rough += wash_x*0.12 + np.random.randn(size,size)*0.018
    rough=np.clip(rough,0.12,0.88)
    rough_u8=(rough*255).astype(np.uint8)
    metal_u8=np.zeros((size,size),dtype=np.uint8)
    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0-(1-height_u8.astype(float)/255.0)*0.45,0,1)
    # IRIDESCENCE mask - where nacre shows strongest (crest)
    iri = np.clip((height - 0.5)*1.8,0,1) * (0.7 + 0.3*np.sin(x*0.02))
    iri_u8=(iri*255).astype(np.uint8)
    orm=np.stack([(ao*255).astype(np.uint8),rough_u8,metal_u8],axis=-1)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, iri_u8

family=[
    ("Moon_Painterly", (245,242,235),(230,228,222),(255,240,230),0.31),
    ("Blush_Painterly",(245,232,228),(235,210,205),(255,200,210),0.29),
    ("Dusk_Painterly", (220,218,230),(200,195,220),(210,200,255),0.33),
]

for name,base,blush,accent,rough in family:
    print(f"Painterly AAA {name} 4K ...")
    albedo,normal,rough_u8,metal_u8,height_u8,orm,iri_u8 = gen_painterly(name,base,blush,accent,rough,4096)
    Image.fromarray(albedo).save(os.path.join(out_dir,f"T_PearlWoven_{name}_BaseColor.png"))
    Image.fromarray(normal).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Normal.png"))
    Image.fromarray(rough_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Roughness.png"))
    Image.fromarray(metal_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Metallic.png"))
    Image.fromarray(height_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Height.png"))
    Image.fromarray(orm).save(os.path.join(out_dir,f"T_PearlWoven_{name}_ORM.png"))
    Image.fromarray(iri_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Iridescence.png"))
    print(f"  saved {name} 7 maps")
print("PAINTERLY AAA DONE")
