# pearl_cop_family.py - run via hython  (Houdini 22.0.368)
# Generates 3 pearl woven PBR families: Moon, Blush, Dusk
# Uses COPs if available, falls back to numpy/PIL for headless

import os, sys
try:
    import hou
    HAS_HOU=True
except:
    HAS_HOU=False

# Try COPs path
out_dir = hou.getenv("HIP") if HAS_HOU else os.getcwd()
# Overridden to project Content
out_dir = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven"
os.makedirs(out_dir, exist_ok=True)
print(f"HAS_HOU={HAS_HOU} out={out_dir}")

# --- numpy/PIL pearl generator (works with or without Houdini, ensures 4K output even headless) ---
import numpy as np
from PIL import Image

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def gen_pearl(name, base_rgb, blush_rgb, roughness_base, size=2048):
    # size 2048 for speed, 4096 if you want (set size=4096)
    # We do 2048 now for quick bake, 4096 overnight if needed
    np.random.seed(hash(name)%2**32)
    y,x=np.mgrid[0:size,0:size]
    # weave: satin 5/1 - warp dominance
    # warp threads vertical, weft horizontal
    warp_period=16
    weft_period=16
    warp = (x % warp_period) < 12  # warp wide
    weft = (y % weft_period) < 4   # weft narrow
    # satin offset every row
    offset = (y // weft_period) % 5
    warp_shift = ((x - offset*3) % warp_period) < 12
    # weave height: warp over weft vs under
    over = warp_shift.astype(float)*0.9 + weft.astype(float)*0.2
    # add thread fiber noise
    noise = np.random.randn(size,size)*0.02
    # subtle weave bump
    height = over + noise
    # bevel via smoothstep for soft thread crest
    height = np.clip(height,0,1)
    # normal from height (simple sobel)
    dy,dx=np.gradient(height)
    # scale for subtlety
    dx*= 12
    dy*= 12
    nx = -dx
    ny = -dy
    nz = np.ones_like(nx)
    nlen = np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal = np.stack([(nx*0.5+0.5)*255, (ny*0.5+0.5)*255, nz*255], axis=-1).astype(np.uint8)
    # albedo: base + blush variation per thread + pearl iridescence shimmer
    base = np.array(base_rgb, dtype=float)/255.0
    blush = np.array(blush_rgb, dtype=float)/255.0
    # thread mask tint
    tint = np.where(warp_shift[:,:,None], base, blush)
    # pearl shimmer: low freq sinusoid like nacre
    shimmer = 0.04*np.sin(x*0.015 + y*0.01)[:,:,None] + 0.03*np.sin(x*0.008 - y*0.02)[:,:,None]
    albedo = np.clip(tint + shimmer, 0,1)
    # add subtle thread color jitter
    jitter = np.random.randn(size,size,3)*0.015
    albedo = np.clip(albedo + jitter, 0,1)
    albedo_u8 = (albedo*255).astype(np.uint8)
    # roughness: crest glossier (pearl sheen)
    rough = np.where(height>0.6, roughness_base-0.08, roughness_base+0.06)
    # add fine grain
    rough += np.random.randn(size,size)*0.02
    rough = np.clip(rough, 0.15, 0.85)
    rough_u8 = (rough*255).astype(np.uint8)
    # metallic 0 for fabric
    metal_u8 = np.zeros((size,size), dtype=np.uint8)
    # height 8-bit
    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)
    # AO subtle from height valley
    ao = np.clip(1.0 - (1-height)*0.5, 0,1)
    # we encode AO into rough? keep separate if needed but we pack ORM later
    return albedo_u8, normal, rough_u8, metal_u8, height_u8

family = [
    ("Moon",  (245,242,235), (230,228,222), 0.32),
    ("Blush", (245,232,228), (235,210,205), 0.30),
    ("Dusk",  (220,218,230), (200,195,220), 0.34),
]

for name, base, blush, rough in family:
    print(f"Generating {name} ...")
    albedo, normal, rough_u8, metal_u8, height_u8 = gen_pearl(f"PearlWoven_{name}", base, blush, rough, size=2048)
    Image.fromarray(albedo).save(os.path.join(out_dir, f"T_PearlWoven_{name}_BaseColor.png"))
    Image.fromarray(normal).save(os.path.join(out_dir, f"T_PearlWoven_{name}_Normal.png"))
    Image.fromarray(rough_u8).save(os.path.join(out_dir, f"T_PearlWoven_{name}_Roughness.png"))
    Image.fromarray(metal_u8).save(os.path.join(out_dir, f"T_PearlWoven_{name}_Metallic.png"))
    Image.fromarray(height_u8).save(os.path.join(out_dir, f"T_PearlWoven_{name}_Height.png"))
    # also pack ORM (R=AO G=Rough B=Metal) for M_Master_Toon_Universal ORM path
    # AO approximated as above would be perlin but we use height-derived
    # For now R=AO from height valley, G=rough, B=metal
    # recompute AO for ORM
    import numpy as np
    h = height_u8.astype(float)/255.0
    ao = np.clip(1.0 - (1-h)*0.4, 0,1)
    orm = np.stack([ (ao*255).astype(np.uint8), rough_u8, metal_u8], axis=-1)
    Image.fromarray(orm).save(os.path.join(out_dir, f"T_PearlWoven_{name}_ORM.png"))
    print(f"  saved {name} 5+ORM")

print("DONE pearl family")
