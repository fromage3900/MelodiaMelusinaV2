import os, numpy as np
from PIL import Image
out_dir="C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_4K"
os.makedirs(out_dir, exist_ok=True)
def gen_pearl(name, base_rgb, blush_rgb, roughness_base, size=4096):
    np.random.seed(hash(name)%2**32)
    y,x=np.mgrid[0:size,0:size]
    warp_period=16
    weft_period=16
    offset=(y // weft_period)%5
    warp_shift=((x - offset*3)%warp_period)<12
    weft=(y%weft_period)<4
    over=warp_shift.astype(float)*0.9 + weft.astype(float)*0.2
    noise=np.random.randn(size,size)*0.02
    height=np.clip(over+noise,0,1)
    dy,dx=np.gradient(height)
    dx*=12; dy*=12
    nx=-dx; ny=-dy; nz=np.ones_like(nx)
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)
    base=np.array(base_rgb,float)/255.0
    blush=np.array(blush_rgb,float)/255.0
    tint=np.where(warp_shift[:,:,None],base,blush)
    shimmer=0.04*np.sin(x*0.015+y*0.01)[:,:,None]+0.03*np.sin(x*0.008 - y*0.02)[:,:,None]
    albedo=np.clip(tint+shimmer + np.random.randn(size,size,3)*0.015,0,1)
    albedo_u8=(albedo*255).astype(np.uint8)
    rough=np.where(height>0.6,roughness_base-0.08,roughness_base+0.06)+ np.random.randn(size,size)*0.02
    rough=np.clip(rough,0.15,0.85)
    rough_u8=(rough*255).astype(np.uint8)
    metal_u8=np.zeros((size,size),dtype=np.uint8)
    height_u8=(np.clip(height,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0-(1-height_u8.astype(float)/255.0)*0.4,0,1)
    orm=np.stack([(ao*255).astype(np.uint8),rough_u8,metal_u8],axis=-1)
    return albedo_u8,normal,rough_u8,metal_u8,height_u8,orm

family=[("Moon",(245,242,235),(230,228,222),0.32),("Blush",(245,232,228),(235,210,205),0.30),("Dusk",(220,218,230),(200,195,220),0.34)]
for name,base,blush,rough in family:
    print(f"4K {name} ...")
    albedo,normal,rough_u8,metal_u8,height_u8,orm=gen_pearl(name,base,blush,rough,4096)
    Image.fromarray(albedo).save(os.path.join(out_dir,f"T_PearlWoven_{name}_BaseColor.png"))
    Image.fromarray(normal).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Normal.png"))
    Image.fromarray(rough_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Roughness.png"))
    Image.fromarray(metal_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Metallic.png"))
    Image.fromarray(height_u8).save(os.path.join(out_dir,f"T_PearlWoven_{name}_Height.png"))
    Image.fromarray(orm).save(os.path.join(out_dir,f"T_PearlWoven_{name}_ORM.png"))
    print(f"  saved {name} 4K")

print("4K DONE")
