"""Surreal Prop Reliquary — 4x 1024 tiling textures via reef_common.

Outputs to surreal_sweep_wave2/props/ + manifest companion.
- T_RelicBrass_Albedo (+ Normal/Rough)
- T_WeepingWax_Albedo (+ Normal/Rough)
- T_PearlescentShell_Albedo (+ Normal/Rough)
- T_DrownedWood_Albedo (+ Normal/Rough)

All tileable (periodic lattice), deterministic, seed-contract via reef_common.
Run: python Tools/Houdini/sea_above_reef/surreal_prop_textures.py  (or hython)
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc

SIZE = 1024
SEED = 20260829
OUT = Path(__file__).resolve().parents[3] / "surreal_sweep_wave2" / "props"

# sRGB authored colours
BRASS_BASE = np.array([201,168,106],np.float32)/255.0
BRASS_TARNISH = np.array([59,47,26],np.float32)/255.0
BRASS_VERDIGRIS = np.array([90,125,110],np.float32)/255.0
BRASS_HIGHLIGHT = np.array([232,210,160],np.float32)/255.0

WAX_CREAM = np.array([245,239,224],np.float32)/255.0
WAX_AMBER = np.array([232,217,176],np.float32)/255.0
WAX_SHADOW = np.array([195,175,140],np.float32)/255.0
WAX_DRIP_DARK = np.array([180,160,125],np.float32)/255.0

SHELL_BASE = np.array([245,240,235],np.float32)/255.0
SHELL_PINK = np.array([255,190,190],np.float32)/255.0
SHELL_AQUA = np.array([170,225,225],np.float32)/255.0
SHELL_LAV = np.array([200,190,235],np.float32)/255.0

WOOD_DARK = np.array([58,46,34],np.float32)/255.0
WOOD_MID = np.array([92,74,51],np.float32)/255.0
WOOD_ALGAE = np.array([70,90,70],np.float32)/255.0
WOOD_SALT = np.array([180,175,165],np.float32)/255.0

def build_relic_brass(seed,size):
    rng=np.random.default_rng(seed)
    # large hammered panel variation
    f1=rc.fbm(size,8,4,rng,gain=0.55)
    f2=rc.fbm(size,32,3,np.random.default_rng(seed+1),gain=0.5)
    scratches = rc.tileable_sine(size, 180,0, phase=0.3, warp=f2, warp_amp=1.2)
    scratches = scratches*0.35 + rc.tileable_sine(size,0,220, phase=1.1)*0.2
    patina_mask = rc.periodic_voronoi_f1(size,16,0.65,np.random.default_rng(seed+2))
    patina = np.clip(1.0 - patina_mask*2.2,0,1)**1.8  # pools in crevices
    edge_wear = rc.fbm(size,16,2,np.random.default_rng(seed+3))
    # albedo blend
    albedo = np.broadcast_to(BRASS_BASE[None,None,:]*(0.85) + BRASS_HIGHLIGHT[None,None,:]*0.15, (size,size,3)).copy()
    # darken with f1 (hammered)
    albedo = albedo * (0.88 + 0.24*f1[...,None])
    # tarnish in low f1
    tarnish = np.clip((0.5-f1)*1.4,0,1)[...,None]
    albedo = albedo*(1-tarnish*0.6) + BRASS_TARNISH[None,None,:]*tarnish*0.6
    # verdigris in patina pools
    patinas=np.clip(patina*0.9,0,1)[...,None]
    albedo = albedo*(1-patinas) + BRASS_VERDIGRIS[None,None,:]*patinas*0.55
    # scratch highlights
    albedo = np.clip(albedo + (scratches[...,None]-0.5)*0.18,0,1)
    # height: hammer + scratches (fine) - patina buildup slightly recessed
    height = np.clip(f1*0.45 + f2*0.2 + (scratches-0.5)*0.08 - patina*0.08 + 0.35,0,1)
    # roughness: brass is low rough, tarnish/verdigris high rough, scratches vary
    rough = np.clip(0.32 + tarnish[...,0]*0.45 + patina*0.35 - scratches*0.15 + edge_wear*0.12,0,1)
    return albedo, height, rough

def build_weeping_wax(seed,size):
    rng=np.random.default_rng(seed+10)
    f1=rc.fbm(size,8,4,rng,gain=0.5)
    f2=rc.periodic_value_noise(size,32,rng)
    # drip field: vertical sine warped
    warp = rc.fbm(size,16,2,np.random.default_rng(seed+11))
    drips = rc.tileable_sine(size, 12, 0, warp=warp, warp_amp=3.0)  # vertical streaks
    # actually need vertical drips: use x freq high, y low but warp creates wobble
    drip_mask = np.clip((drips-0.55)*3.5,0,1)
    # secondary fine driplets
    drip_mask2 = rc.fbm(size,64,2,np.random.default_rng(seed+12))
    drip_mask = np.clip(drip_mask*0.85 + drip_mask2*0.25,0,1)**1.2
    # wax pooling bulges
    bulge = rc.fbm(size,16,3,np.random.default_rng(seed+13),gain=0.6)
    albedo = WAX_CREAM[None,None,:]*(1 - f1[...,None]*0.18) + WAX_AMBER[None,None,:]*f1[...,None]*0.18
    # drips slightly darker / translucent edge
    albedo = albedo*(1 - drip_mask[...,None]*0.18) + WAX_SHADOW[None,None,:]*drip_mask[...,None]*0.18
    albedo = albedo*(0.96 + 0.08*f2[...,None])
    albedo = np.clip(albedo,0,1)
    height = np.clip(f1*0.18 + bulge*0.22 + drip_mask*0.32 + f2*0.08,0,1)
    rough = np.clip(0.65 + drip_mask*0.15 - bulge*0.1 + f1*0.08,0,1)
    # wax SSS mask: drips more translucent
    sss = np.clip(drip_mask*0.7 + 0.2,0,1)
    return albedo, height, rough, sss

def build_pearlescent_shell(seed,size):
    rng=np.random.default_rng(seed+20)
    f1=rc.fbm(size,8,5,rng,gain=0.55)
    # shell growth lines (tight parallel sine)
    growth = rc.tileable_sine(size,0,85, warp=rc.fbm(size,16,2,np.random.default_rng(seed+21)), warp_amp=2.0)
    growth = np.clip((growth-0.45)*2.5,0,1)**1.4
    # iridescent hue shift: thin-film interference via 2 sine fields hue
    hue1 = rc.tileable_sine(size,18,22, phase=0.0)
    hue2 = rc.tileable_sine(size,26,-14, phase=1.7)
    # low freq tint field
    tint = rc.fbm(size,4,3,np.random.default_rng(seed+22),gain=0.5)
    tint = (tint - tint.min())/(tint.max()-tint.min()+1e-6)
    # base shell
    albedo = SHELL_BASE[None,None,:].copy()
    # growth lines darken slightly
    albedo = albedo*(1 - growth[...,None]*0.18) + np.array([0.92,0.90,0.88])[None,None,:]*growth[...,None]*0.08
    # iridescence: blend pink/aqua/lav based on hue fields
    irid = np.clip((hue1-0.5)*0.6 + (hue2-0.5)*0.4 + (tint-0.5)*0.5 +0.5,0,1)
    # map irid 0..1 -> pink->aqua->lav
    pink_w = np.clip(1 - irid*2.2,0,1)
    aqua_w = np.clip(1 - np.abs(irid-0.5)*3.0,0,1)
    lav_w = np.clip((irid-0.5)*2.2,0,1)
    albedo = albedo*(1 - (pink_w+aqua_w+lav_w)[...,None]*0.32) \
             + SHELL_PINK[None,None,:]*pink_w[...,None]*0.30 \
             + SHELL_AQUA[None,None,:]*aqua_w[...,None]*0.30 \
             + SHELL_LAV[None,None,:]*lav_w[...,None]*0.28
    # add subtle nacre shimmer via high freq f2
    f2 = rc.fbm(size,64,2,np.random.default_rng(seed+23))
    albedo = np.clip(albedo + (f2[...,None]-0.5)*0.06,0,1)
    height = np.clip(growth*0.12 + f1*0.08 + f2*0.06 + 0.42,0,1)
    rough = np.clip(0.18 + growth*0.18 + (1-irid)*0.12,0,1)
    return albedo, height, rough

def build_drowned_wood(seed,size):
    rng=np.random.default_rng(seed+30)
    # wood grain: strong vertical sine + fbm warp
    warp = rc.fbm(size,8,3,rng,gain=0.6)
    grain = rc.tileable_sine(size,0,18, warp=warp, warp_amp=4.5)
    grain = grain*0.5 + rc.tileable_sine(size,0,36, phase=0.8, warp=warp, warp_amp=2.0)*0.3 + warp*0.25
    grain = np.clip(grain,0,1)
    # knot field via voronoi
    f1 = rc.periodic_voronoi_f1(size,8,0.7,np.random.default_rng(seed+31))
    knot = np.clip(1 - f1*3.2,0,1)**1.5
    # algae / barnacle patches
    algae_fbm = rc.fbm(size,16,3,np.random.default_rng(seed+32),gain=0.55)
    barnacle_mask = rc.periodic_voronoi_f1(size,32,0.85,np.random.default_rng(seed+33))
    barnacle = np.clip(1 - barnacle_mask*4.0,0,1)**1.2
    # albedo: dark base + mid grain
    albedo = WOOD_DARK[None,None,:]*(0.7) + WOOD_MID[None,None,:]*0.3
    albedo = albedo*(0.75 + 0.5*grain[...,None])
    # knots darker
    albedo = albedo*(1 - knot[...,None]*0.55) + np.array([0.16,0.12,0.08])[None,None,:]*knot[...,None]*0.4
    # algae green tint in low areas
    algae = np.clip((algae_fbm-0.45)*2.0,0,1)
    albedo = albedo*(1 - algae[...,None]*0.35) + WOOD_ALGAE[None,None,:]*algae[...,None]*0.35
    # salt crust highlights sparse
    salt = np.clip((rc.fbm(size,32,2,np.random.default_rng(seed+34))-0.6)*2.5,0,1)
    albedo = np.clip(albedo + WOOD_SALT[None,None,:]*salt[...,None]*0.22,0,1)
    height = np.clip(grain*0.35 + knot*0.18 + barnacle*0.22 + algae_fbm*0.08,0,1)
    rough = np.clip(0.78 + knot*0.12 + algae*0.08 - grain*0.1,0,1)
    return albedo, height, rough, barnacle

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    size=SIZE
    files=[]
    # --- Relic Brass ---
    albedo,h,rough = build_relic_brass(SEED, size)
    normal = rc.normal_from_height(h, strength=3.0)
    for name,arr,kind in [
        ("T_RelicBrass_Albedo", albedo,"rgb"),
        ("T_RelicBrass_Normal", normal,"rgb"),
        ("T_RelicBrass_Roughness", rough,"gray"),
        ("T_RelicBrass_Height", h,"gray"),
    ]:
        p=rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name":name,"file":p.name,"kind":kind,"size":size,"seed":SEED})
        print(f"[tex] wrote {p.name}")
    # --- Weeping Wax ---
    albedo,h,rough,sss = build_weeping_wax(SEED+10,size)
    normal = rc.normal_from_height(h, strength=2.2)
    for name,arr,kind in [
        ("T_WeepingWax_Albedo", albedo,"rgb"),
        ("T_WeepingWax_Normal", normal,"rgb"),
        ("T_WeepingWax_Roughness", rough,"gray"),
        ("T_WeepingWax_SSSMask", sss,"gray"),
    ]:
        p=rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name":name,"file":p.name,"kind":kind,"size":size,"seed":SEED+10})
        print(f"[tex] wrote {p.name}")
    # --- Pearlescent Shell ---
    albedo,h,rough = build_pearlescent_shell(SEED+20,size)
    normal = rc.normal_from_height(h, strength=1.8)
    for name,arr,kind in [
        ("T_PearlescentShell_Albedo", albedo,"rgb"),
        ("T_PearlescentShell_Normal", normal,"rgb"),
        ("T_PearlescentShell_Roughness", rough,"gray"),
    ]:
        p=rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name":name,"file":p.name,"kind":kind,"size":size,"seed":SEED+20})
        print(f"[tex] wrote {p.name}")
    # --- Drowned Wood ---
    albedo,h,rough,barnacle = build_drowned_wood(SEED+30,size)
    normal = rc.normal_from_height(h, strength=3.4)
    for name,arr,kind in [
        ("T_DrownedWood_Albedo", albedo,"rgb"),
        ("T_DrownedWood_Normal", normal,"rgb"),
        ("T_DrownedWood_Roughness", rough,"gray"),
        ("T_DrownedWood_BarnacleMask", barnacle,"gray"),
    ]:
        p=rc.save_image(OUT / f"{name}.png", arr, kind)
        files.append({"name":name,"file":p.name,"kind":kind,"size":size,"seed":SEED+30})
        print(f"[tex] wrote {p.name}")
    # contact sheet (albedos)
    try:
        from PIL import Image
        import numpy as np2
        albedos = [
            np.array(Image.open(str(OUT/"T_RelicBrass_Albedo.png"))),
            np.array(Image.open(str(OUT/"T_WeepingWax_Albedo.png"))),
            np.array(Image.open(str(OUT/"T_PearlescentShell_Albedo.png"))),
            np.array(Image.open(str(OUT/"T_DrownedWood_Albedo.png"))),
        ]
        thumb=256
        sheet=Image.new("RGB",(thumb*4,thumb),(22,24,28))
        for i,im in enumerate(albedos):
            t=Image.fromarray(im).resize((thumb,thumb), Image.LANCZOS)
            sheet.paste(t,(i*thumb,0))
        sheet.save(str(OUT/"_ContactSheet_Textures.png"),format="PNG")
        print(f"[tex] contact -> _ContactSheet_Textures.png")
        files.append({"name":"_ContactSheet_Textures","file":"_ContactSheet_Textures.png","kind":"contact_sheet","size":thumb,"seed":SEED})
    except Exception as e:
        print(f"[tex] contact sheet failed: {e}")
    manifest = rc.write_manifest(OUT/"textures_manifest.json","surreal.props.textures.v1",SEED,{"size":size,"count":4,"tiling":"reef_common lattice-periodic","runtime":"python+PIL via reef_common"},files)
    print(f"[tex] manifest -> {manifest}")

if __name__=="__main__":
    main()
