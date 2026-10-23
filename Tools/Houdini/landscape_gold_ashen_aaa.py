import os, numpy as np
from PIL import Image
out_dir="C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/Landscape"
os.makedirs(out_dir, exist_ok=True)
SIZE=4096

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a+1e-6),0,1)
    return t*t*(3-2*t)
def lerp(a,b,t): return a*(1-t)+b*t
def fract(x): return x - np.floor(x)

def tilable_rand(size, tile, seed):
    rng=np.random.RandomState(seed)
    small=rng.rand(tile,tile).astype(np.float32)
    reps=size//tile
    if reps==1:
        return small
    return np.tile(small, (reps,reps)).astype(np.float32)

def blur_tilable(img, iters=1):
    # separable box blur with wrap
    out=img
    for _ in range(iters):
        out=(out + np.roll(out,1,0) + np.roll(out,-1,0) + np.roll(out,1,1) + np.roll(out,-1,1) + np.roll(np.roll(out,1,0),1,1) + np.roll(np.roll(out,1,0),-1,1) + np.roll(np.roll(out,-1,0),1,1) + np.roll(np.roll(out,-1,0),-1,1))/9.0
    return out

def fbm_sin(x,y, size, seed):
    # tilable sin fbm, returns ~ -1..1
    rng=np.random.RandomState(seed)
    acc=np.zeros_like(x,dtype=np.float32)
    amp_sum=0
    # frequencies that divide size
    freqs=[2,4,8,16,32,64,128]
    amps=[0.5,0.35,0.22,0.14,0.08,0.04,0.02]
    for f,a in zip(freqs, amps):
        ox=rng.rand()*6.28
        oy=rng.rand()*6.28
        ph=rng.rand()*6.28
        # tilable: 2*pi*f*x/size
        fx=2*np.pi*f*x/size + ox
        fy=2*np.pi*f*y/size + oy
        # combine sin/cos for organic
        v=np.sin(fx+ph)*np.cos(fy-ph*0.7) + 0.5*np.sin(fx*1.3 + fy*0.7)
        acc+= (v* a)
        amp_sum+=a
    return acc/amp_sum

def normal_from_height(h, strength=8.0):
    # tilable gradient via roll
    dx=(np.roll(h,-1,axis=1).astype(np.float32)-np.roll(h,1,axis=1).astype(np.float32))*strength*0.5
    dy=(np.roll(h,-1,axis=0).astype(np.float32)-np.roll(h,1,axis=0).astype(np.float32))*strength*0.5
    # add micro jitter tilable
    # jx, jy small random
    nx=-dx
    ny=-dy
    nz=np.ones_like(nx)
    nlen=np.sqrt(nx*nx+ny*ny+nz*nz)+1e-6
    nx/=nlen; ny/=nlen; nz/=nlen
    nm=np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)
    return nm

def make_fleck_mask(size, seed, coverage=0.02):
    # 2% gold flecks, tilable via tiled rand
    # use high freq tile
    base=tilable_rand(size,512,seed)
    # threshold to get 2%
    thresh=np.percentile(base, 100*(1-coverage))
    mask=(base > thresh).astype(np.float32)
    # dilate slightly via blur then threshold to make fleck shape 2-4 px
    # create small bright centers with soft edge
    # blur then re-threshold to get soft circular flecks
    soft=blur_tilable(mask,1)
    # keep sharp centers
    mask2=np.clip(soft*1.2,0,1)
    # make flecks slightly irregular by modulating with grain
    grain=tilable_rand(size,1024,seed+101)
    mask2=np.where(mask2>0.3, np.clip(mask2* (0.8+0.4*grain),0,1), 0)
    # final binary-ish with soft edge
    mask2=smoothstep(0.35,0.65,mask2)
    return mask2

def gen_dirt(tag, base_rgb, gold_intensity, roughness_base=0.75, size=SIZE):
    y,x=np.mgrid[0:size,0:size].astype(np.float32)
    # tilable fbm
    fbm=fbm_sin(x,y,size, seed=abs(hash(tag))%2**31)
    fbm=(fbm+1)*0.5 # 0..1
    # large undulation via blurred rand tile
    und=tilable_rand(size,256, seed=abs(hash(tag+"und"))%2**31)
    und=blur_tilable(und,2)
    und=smoothstep(0.3,0.7,und)
    # fine aggregate via high freq
    fine=tilable_rand(size,512, seed=abs(hash(tag+"fine"))%2**31)
    fine=blur_tilable(fine,1)
    # pebble hints: sparse bumps
    pebble_noi=tilable_rand(size,256, seed=abs(hash(tag+"pebble"))%2**31)
    pebble_noi=blur_tilable(pebble_noi,1)
    pebble_mask=smoothstep(0.72,0.82, pebble_noi) # sparse
    # pebble shape soft
    pebble_mask=pebble_mask* (0.7+0.3*fbm)

    # height composition
    h=np.clip( fbm*0.35 + und*0.25 + fine*0.12 + pebble_mask*0.22 ,0,1)
    # add subtle soil clump variation via sin warp
    warp=np.sin(x*0.015 + y*0.011)*0.03 + np.cos(y*0.02 - x*0.008)*0.02
    h=np.clip(h+warp,0,1)
    # ripple micro irrelevant for dirt, keep subtle
    h=smoothstep(0.15,0.92,h)

    # gold mica flecks 2%
    fleck=make_fleck_mask(size, seed=abs(hash(tag+"gold"))%2**31, coverage=0.02)
    # flecks sit in crevices slightly lower? mica is flat, add tiny height bump + shimmer
    h_fleck=np.clip(h + fleck*0.06,0,1)

    # albedo
    base=np.array(base_rgb,float)/255.0
    # variation
    tint_var=(fbm[:,:,None]*0.08 + und[:,:,None]*0.06 + np.random.RandomState(abs(hash(tag))%2**31).randn(size,size,1)*0.008)
    # but use tilable rand for third term
    jitter=tilable_rand(size,1024, seed=abs(hash(tag+"jit"))%2**31)
    jitter=(jitter[:,:,None]-0.5)*0.04
    albedo=np.clip(base + tint_var + jitter + (pebble_mask[:,:,None]*0.07),0,1)
    # darken crevices, lighten pebble tops
    albedo=np.clip(albedo * (0.88+0.24*h_fleck[:,:,None]),0,1)
    # gold flecks color
    gold_rgb=np.array([1.0,0.78,0.28])  # light gold
    # gold influence on base
    gold_mix=fleck[:,:,None]* gold_intensity
    albedo=np.clip( albedo*(1-gold_mix*0.9) + gold_rgb*gold_mix*0.95 ,0,1)
    # add subtle desaturation for moon variant: already low sat base

    # roughness: base 0.75, pebble tops slightly smoother, flecks glossier, crevices rougher
    rough=np.full((size,size), roughness_base, dtype=np.float32)
    rough+= (1-h_fleck)*0.10  # crevice rougher
    rough-= pebble_mask*0.08
    rough-= fleck*0.18  # mica less rough
    rough+= (tilable_rand(size,1024, seed=abs(hash(tag+"r2"))%2**31)-0.5)*0.06
    rough=np.clip(rough,0.12,0.92)

    metal=np.clip(fleck*0.85,0,1)  # gold metallic
    # slight metallic on pebble sheen 0
    height_u8=(np.clip(h_fleck,0,1)*255).astype(np.uint8)
    # AO from height cavity
    ao=np.clip(1.0 - (1-h_fleck)*0.55,0,1)
    ao=np.clip(ao - pebble_mask*0.04,0,1)
    # subtle ao blur
    ao=blur_tilable(ao,1)*0.92+0.08

    # iridescence: subtle gold catch on flecks + pebble crests
    iri=np.clip(fleck*0.95 + smoothstep(0.65,0.85,h_fleck)*0.18,0,1)
    # add faint sheen on overall surface
    iri=np.clip(iri + (fbm*0.08),0,1)
    # normal
    normal=normal_from_height(h_fleck, strength=10.0)

    # ORM packing R=AO G=Rough B=Metal
    rough_u8=(np.clip(rough,0,1)*255).astype(np.uint8)
    metal_u8=(np.clip(metal,0,1)*255).astype(np.uint8)
    ao_u8=(np.clip(ao,0,1)*255).astype(np.uint8)
    orm=np.stack([ao_u8, rough_u8, metal_u8],axis=-1)
    iri_u8=(np.clip(iri,0,1)*255).astype(np.uint8)
    albedo_u8=(np.clip(albedo,0,1)*255).astype(np.uint8)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, ao_u8, iri_u8

def gen_sand(tag, base_rgb, gold_intensity, roughness_base=0.65, size=SIZE):
    y,x=np.mgrid[0:size,0:size].astype(np.float32)
    fbm=fbm_sin(x,y,size, seed=abs(hash(tag))%2**31)
    fbm=(fbm+1)*0.5
    # dune large undulation: low freq sine
    dune=np.sin(x*2*np.pi*3/size + np.sin(y*2*np.pi*2/size)*0.5)*0.5+0.5
    dune2=np.sin(y*2*np.pi*2/size + x*2*np.pi*1/size*0.3)*0.5+0.5
    dune=np.clip(dune*0.6+dune2*0.4,0,1)
    # ripple micro-height: directional ripples ~ 40-80 px wavelength
    # use sin with tiling
    ripple=np.sin(x*2*np.pi*28/size + np.sin(y*2*np.pi*6/size)*2.0)*0.5+0.5
    ripple2=np.sin(x*2*np.pi*44/size + y*2*np.pi*3/size)*0.5+0.5
    ripple=np.clip(ripple*0.65+ripple2*0.35,0,1)
    ripple=smoothstep(0.2,0.8,ripple)
    # fine dune grain
    fine=tilable_rand(size,512, seed=abs(hash(tag+"fine"))%2**31)
    fine=blur_tilable(fine,1)
    fine=smoothstep(0.35,0.75,fine)
    h=np.clip(dune*0.30 + ripple*0.35 + fbm*0.18 + fine*0.12,0,1)
    h=smoothstep(0.18,0.88,h)
    # subtle warp
    h=np.clip(h + np.sin((x+y)*0.008)*0.015,0,1)
    fleck=make_fleck_mask(size, seed=abs(hash(tag+"gold"))%2**31, coverage=0.018 if "Moon" in tag else 0.022)
    h_fleck=np.clip(h + fleck*0.05,0,1)
    base=np.array(base_rgb,float)/255.0
    jitter=tilable_rand(size,1024, seed=abs(hash(tag+"jit"))%2**31)
    jitter=(jitter[:,:,None]-0.5)*0.03
    # sand has soft grain color variation
    grain_tint=fbm[:,:,None]*0.06 + dune[:,:,None]*0.04
    albedo=np.clip(base + grain_tint + jitter,0,1)
    # ripple shadows slightly darker in troughs
    albedo=np.clip(albedo * (0.86+0.28*h_fleck[:,:,None]),0,1)
    gold_rgb=np.array([1.0,0.80,0.32])
    gold_mix=fleck[:,:,None]* gold_intensity
    albedo=np.clip(albedo*(1-gold_mix*0.85)+ gold_rgb*gold_mix*0.92,0,1)

    rough=np.full((size,size), roughness_base, dtype=np.float32)
    rough+= (1-h_fleck)*0.08
    rough-= fleck*0.15
    rough+= (tilable_rand(size,1024, seed=abs(hash(tag+"r"))%2**31)-0.5)*0.05
    rough=np.clip(rough,0.12,0.90)
    metal=np.clip(fleck*0.82,0,1)
    height_u8=(np.clip(h_fleck,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0 - (1-h_fleck)*0.45,0,1)
    ao=blur_tilable(ao,1)*0.94+0.06
    iri=np.clip(fleck*0.92 + smoothstep(0.60,0.85,h_fleck)*0.15,0,1)
    iri=np.clip(iri + ripple*0.06,0,1)
    normal=normal_from_height(h_fleck, strength=7.0) # softer dune normal
    rough_u8=(np.clip(rough,0,1)*255).astype(np.uint8)
    metal_u8=(np.clip(metal,0,1)*255).astype(np.uint8)
    ao_u8=(np.clip(ao,0,1)*255).astype(np.uint8)
    orm=np.stack([ao_u8, rough_u8, metal_u8],axis=-1)
    iri_u8=(np.clip(iri,0,1)*255).astype(np.uint8)
    albedo_u8=(np.clip(albedo,0,1)*255).astype(np.uint8)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, ao_u8, iri_u8

def gen_rock(tag, base_rgb, gold_intensity, roughness_face=0.45, roughness_crevice=0.70, size=SIZE):
    y,x=np.mgrid[0:size,0:size].astype(np.float32)
    fbm=fbm_sin(x,y,size, seed=abs(hash(tag))%2**31)
    fbm=(fbm+1)*0.5
    # pale ash stone large blocks
    base_fbm=tilable_rand(size,128, seed=abs(hash(tag+"base"))%2**31)
    base_fbm=blur_tilable(base_fbm,3)
    base_fbm=smoothstep(0.3,0.7,base_fbm)
    # soft cracks: grid with jitter warp
    # warp coords
    wx=x + np.sin(y*2*np.pi*8/size)*12 + np.sin(x*2*np.pi*4/size)*8
    wy=y + np.cos(x*2*np.pi*8/size)*12
    # tilable crack grid: use fractional
    tiles=10
    fx=(wx * tiles / size) % 1
    fy=(wy * tiles / size) % 1
    # distance to edge
    dx=np.minimum(fx, 1-fx)
    dy=np.minimum(fy, 1-fy)
    d=np.minimum(dx,dy)
    # crack line where d < 0.03
    crack=smoothstep(0.045,0.012,d) # 1 on crack
    # break up cracks with noise
    crack*= (0.6+0.4*fbm)
    # randomize crack width
    jitter=tilable_rand(size,256, seed=abs(hash(tag+"cj"))%2**31)
    crack=np.clip(crack * (0.7+0.6*jitter),0,1)
    # second larger crack scale
    tiles2=4
    fx2=(x*tiles2/size)%1
    fy2=(y*tiles2/size)%1
    d2=np.minimum(np.minimum(fx2,1-fx2), np.minimum(fy2,1-fy2))
    crack2=smoothstep(0.08,0.02,d2)*0.5
    crack=np.clip(np.maximum(crack,crack2),0,1)
    # height: face high, crevice low
    face_h=base_fbm*0.5 + fbm*0.25 + 0.25
    h=np.clip(face_h - crack*0.45,0,1)
    # soft cracks: blur the height a bit
    h=blur_tilable(h,1)*0.7 + h*0.3
    h=smoothstep(0.18,0.88,h)
    # gold in crevices for Gilded, sparse flecks for Ashen
    if "Gilded" in tag:
        fleck=tilable_rand(size,256, seed=abs(hash(tag+"gold"))%2**31)
        fleck=blur_tilable(fleck,1)
        # gold concentrated in cracks
        gold_mask=np.clip(crack*0.85 + fleck*0.25* crack,0,1)
        gold_mask=smoothstep(0.25,0.65,gold_mask)
        # add sparse mica outside cracks too
        extra=make_fleck_mask(size, seed=abs(hash(tag+"extra"))%2**31, coverage=0.01)
        gold_mask=np.clip(gold_mask + extra*0.4,0,1)
    else:
        gold_mask=make_fleck_mask(size, seed=abs(hash(tag+"gold"))%2**31, coverage=0.012)
        # keep subtle
        gold_mask=gold_mask*0.7
    h_fleck=np.clip(h + gold_mask*0.04,0,1)
    base=np.array(base_rgb,float)/255.0
    # low saturation: base already desaturated
    # variation very subtle
    jitter=tilable_rand(size,1024, seed=abs(hash(tag+"jit"))%2**31)
    jitter=(jitter[:,:,None]-0.5)*0.025
    albedo=np.clip(base + (fbm[:,:,None]-0.5)*0.04 + (base_fbm[:,:,None]-0.5)*0.05 + jitter,0,1)
    # crack darkening
    albedo=np.clip(albedo * (1 - crack[:,:,None]*0.18) ,0,1)
    # gold
    gold_rgb=np.array([0.94,0.76,0.32]) # slightly deeper for rock
    gold_mix=gold_mask[:,:,None]* gold_intensity
    albedo=np.clip(albedo*(1-gold_mix*0.8) + gold_rgb*gold_mix*0.88,0,1)
    # roughness: 0.45 face, 0.70 crevice, interpolate by crack/height
    # face = high h, crevice = high crack
    crevice_factor=np.clip(crack*0.9 + (1-h)*0.5,0,1)
    rough=lerp(roughness_face, roughness_crevice, crevice_factor)
    rough=rough.astype(np.float32)
    rough-= gold_mask*0.12
    rough+= (tilable_rand(size,1024, seed=abs(hash(tag+"r"))%2**31)-0.5)*0.04
    rough=np.clip(rough,0.10,0.92)
    metal=np.clip(gold_mask*0.78,0,1)
    height_u8=(np.clip(h_fleck,0,1)*255).astype(np.uint8)
    ao=np.clip(1.0 - crack*0.55 - (1-h_fleck)*0.25,0,1)
    ao=blur_tilable(ao,1)*0.96+0.04
    iri=np.clip(gold_mask*0.88 + smoothstep(0.3,0.7,crack)*0.10,0,1)
    iri=np.clip(iri + gold_mask*0.2,0,1)
    normal=normal_from_height(h_fleck, strength=11.0)
    rough_u8=(np.clip(rough,0,1)*255).astype(np.uint8)
    metal_u8=(np.clip(metal,0,1)*255).astype(np.uint8)
    ao_u8=(np.clip(ao,0,1)*255).astype(np.uint8)
    orm=np.stack([ao_u8, rough_u8, metal_u8],axis=-1)
    iri_u8=(np.clip(iri,0,1)*255).astype(np.uint8)
    albedo_u8=(np.clip(albedo,0,1)*255).astype(np.uint8)
    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, ao_u8, iri_u8

variants=[
    ("Dirt_Moon", "dirt", (142,132,118), 0.85),
    ("Dirt_Gold", "dirt", (148,136,118), 1.0),
    ("Sand_Moon", "sand", (196,184,165), 0.80),
    ("Sand_Gold", "sand", (200,186,162), 1.0),
    ("Rock_Ashen", "rock", (178,176,170), 0.75),
    ("Rock_AshenGilded", "rock", (180,178,172), 0.95),
]

for tag, typ, base_rgb, gold_i in variants:
    print(f"generating {tag} ...")
    if typ=="dirt":
        albedo, normal, rough, metal, height, orm, ao, iri = gen_dirt(tag, base_rgb, gold_i, 0.75, SIZE)
    elif typ=="sand":
        albedo, normal, rough, metal, height, orm, ao, iri = gen_sand(tag, base_rgb, gold_i, 0.65, SIZE)
    else:
        albedo, normal, rough, metal, height, orm, ao, iri = gen_rock(tag, base_rgb, gold_i, 0.45, 0.70, SIZE)
    prefix=f"T_Landscape_{tag}"
    Image.fromarray(albedo).save(f"{out_dir}/{prefix}_BaseColor.png")
    Image.fromarray(normal).save(f"{out_dir}/{prefix}_Normal.png")
    Image.fromarray(orm).save(f"{out_dir}/{prefix}_ORM.png")
    Image.fromarray(rough).save(f"{out_dir}/{prefix}_Roughness.png")
    Image.fromarray(metal).save(f"{out_dir}/{prefix}_Metallic.png")
    Image.fromarray(height).save(f"{out_dir}/{prefix}_Height.png")
    Image.fromarray(ao).save(f"{out_dir}/{prefix}_AO.png")
    Image.fromarray(iri).save(f"{out_dir}/{prefix}_Iridescence.png")
    print(f"  -> {prefix} done")

print(f"All landscape done. total {len(variants)} variants x 8 maps")
