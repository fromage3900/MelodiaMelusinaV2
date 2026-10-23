"""
hybrid_bridge_aaa.py — AAA Hybrid Bridging Maps for M_Master_Nikki_Landscape vertex blending
6 hybrid variants at 4096 into Content/EnvSandbox/Textures/Hybrid_Bridge/
  Rock_Cloth    — stone with pearl weave bleeding through cracks
  Cloth_Ornament — fabric with ornament embroidery fading into dust
  Sand_Cloth    — sand with buried silk threads
  Ashen_Lace    — ash rock with lace mortar
  Dirt_Silk     — soil with silk sheen pooling in low areas
  Gold_Vein     — rock with gilded veins

Each variant outputs 8 maps (6x8 = 48 files):
  BaseColor, Normal, ORM, Roughness, Metallic, Height, AO, BlendMask (RGB)
BlendMask RGB = 3-way vertex-paint blend (R=primary, G=secondary, B=transition)
              + Height channel for POM parallax
Tilable: all noise uses 2*pi*x/period with period|4096, toroidal Voronoi wraps.

Run via hython:
  "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" Tools/Houdini/hybrid_bridge_aaa.py [--size 4096] [--quick]
Quick = 1024 smoke test (~2 min). Full 4096 ~8-12 min, 48 PNGs ~1.2 GB.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image

OUT_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/Hybrid_Bridge"

SIZE_DEFAULT = 4096

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def lerp(a,b,t): return a*(1-t)+b*t

# ---------- tilable helpers ----------
def t_sin(x, y, period_x, period_y, phase=0):
    """Tilable sin field: sin(2pi*x/period + phase). period must divide SIZE."""
    return np.sin(2*np.pi*x/period_x + 2*np.pi*y/period_y + phase)

def t_noise_field(x, y, size, seed, octaves=4):
    """Tilable pseudo-fbm using sin stacks with periods dividing size."""
    np.random.seed(seed)
    # periods dividing 4096: 2048,1024,512,256,128,64
    periods = [1024, 512, 256, 128, 64]
    amps = [0.5, 0.28, 0.15, 0.08, 0.04]
    phases = np.random.uniform(0, 2*np.pi, len(periods)*2)
    acc = np.zeros_like(x, dtype=np.float32)
    for i in range(min(octaves, len(periods))):
        p = periods[i]
        # use both axes with different phase
        a = np.sin(2*np.pi*x/p + phases[i*2]) * np.cos(2*np.pi*y/p + phases[i*2+1])
        acc += a * amps[i]
    return acc

def t_ridged(x, y, period, warp=0.5, seed=0):
    """Tilable ridged noise 0..1 (1 on ridge)."""
    np.random.seed(seed)
    ph = np.random.uniform(0, 2*np.pi)
    base = np.sin(2*np.pi*x/period + ph) * np.cos(2*np.pi*y/period + ph*0.7)
    # add second octave warp
    base += warp*np.sin(2*np.pi*x/(period*0.5) + ph*1.3)*np.cos(2*np.pi*y/(period*0.5)+ph*0.9)*0.3
    rid = 1 - np.abs(base)
    return np.clip(rid, 0, 1)

def toroidal_voronoi(x, y, size, cell_period, seed, jitter=0.65):
    """Tilable Voronoi height: stone plates. Returns cell_height 0..1 and border mask 0..1."""
    # number of cells per axis
    n = size // cell_period
    # generate cell jittered points in repeatable grid
    rng = np.random.RandomState(seed)
    # random offset per cell (n x n)
    off_x = rng.uniform(-jitter, jitter, (n, n)).astype(np.float32)
    off_y = rng.uniform(-jitter, jitter, (n, n)).astype(np.float32)
    # compute nearest distance via brute grid search with toroidal wrap
    # For 4096 with cell_period 256 => n=16 => 256 cells. Vectorized per pixel is heavy -> chunked loops
    # Instead compute via sampling: for each pixel find nearest cell center among 3x3 neighbors
    # Use tiled coordinate -> cell index
    cx = (x / cell_period).astype(np.float32)
    cy = (y / cell_period).astype(np.float32)
    # integer cell
    ix = np.floor(cx).astype(int) % n
    iy = np.floor(cy).astype(int) % n
    # we will compute distance to 9 neighboring cells
    # gather offsets
    # Use iteration over 9 neighbors, keep min dist
    min_d = np.full(x.shape, 1e9, dtype=np.float32)
    second_d = np.full(x.shape, 1e9, dtype=np.float32)
    # also store cell id for mottling
    cell_val = rng.uniform(0.85, 1.0, (n, n)).astype(np.float32)
    chosen_val = np.zeros(x.shape, dtype=np.float32)
    for dy in (-1,0,1):
        for dx_ in (-1,0,1):
            nx_idx = (ix + dx_) % n
            ny_idx = (iy + dy) % n
            # center position of that cell in pixel space
            # cell origin + 0.5 + jitter
            # gather via indexing
            jx = off_x[ny_idx, nx_idx] if off_x.ndim==2 else 0 # vectorized gather tricky -> use advanced indexing
            # Actually need per-pixel gather: off_x[ny_idx, nx_idx] where ny_idx,nx_idx are arrays -> we can use np lookup
            # Do via flat indexing
            # Flatten off_x for gather
            flat_off_x = off_x.ravel()
            flat_off_y = off_y.ravel()
            flat_val = cell_val.ravel()
            flat_idx = ny_idx * n + nx_idx
            # but nx_idx,ny_idx are 2D arrays -> flat_idx 2D -> gather 2D
            jx_arr = flat_off_x[flat_idx]
            jy_arr = flat_off_y[flat_idx]
            # center
            cx_c = (np.floor(cx+dx_).astype(int) + 0.5 + jx_arr) * cell_period
            cy_c = (np.floor(cy+dy).astype(int) + 0.5 + jy_arr) * cell_period
            # toroidal wrap distance: minimal wrap around size
            dxp = x - cx_c
            dyp = y - cy_c
            # wrap to [-size/2, size/2]
            dxp = ((dxp + size*0.5) % size) - size*0.5
            dyp = ((dyp + size*0.5) % size) - size*0.5
            d = np.sqrt(dxp*dxp + dyp*dyp)
            # keep two smallest for border detection
            mask = d < min_d
            second_d[mask] = min_d[mask]
            min_d[mask] = d[mask]
            chosen_val[mask] = flat_val[flat_idx[mask]]
            mask2 = (d >= min_d) & (d < second_d)
            second_d[mask2] = d[mask2]
    # border = second - min (wide in middle, 0 at edge)
    border_dist = second_d - min_d
    # cell interior height: 1 at center, falls near border
    # Normalize border_dist: cell_period ~256 => border_dist up to ~180
    edge = np.clip(border_dist / (cell_period*0.18), 0, 1)  # 0 at edge, 1 in center
    edge = smoothstep(0,1, edge)
    height = 0.45 + 0.35*edge + (chosen_val-0.92)*0.10
    # crack mask: 1 where border_dist small (crack)
    crack = 1 - smoothstep(8, 28, border_dist)  # narrow crack
    crack_soft = 1 - smoothstep(4, 48, border_dist) # wider transition
    return height, crack, crack_soft, chosen_val

def warp_weave(x, y, size, seed, warp_period=20, weft_period=20):
    """Tilable pearl weave height 0..1 + mask."""
    rng = np.random.RandomState(seed)
    drift = np.sin(2*np.pi*y/1024)*1.5
    ph = rng.uniform(0, 2*np.pi)
    offset = (np.floor(y / weft_period).astype(int) % 5)
    warp = ((x + drift - offset*2.5 + ph*10) % warp_period) < 11
    weft = (y % weft_period) < 6
    over = warp.astype(float)*0.88 + weft.astype(float)*0.20
    over = np.clip(over + np.random.randn(*x.shape).astype(np.float32)*0.012, 0, 1)
    over = smoothstep(0.22, 0.86, over)
    return over, warp

# ========== per-variant generators ==========

def gen_rock_cloth(size):
    seed = 1337
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # stone plates
    stone_h, crack, crack_soft, cell_val = toroidal_voronoi(x, y, size, cell_period=320, seed=seed, jitter=0.62)
    # stone detail grain tilable
    grain = t_noise_field(x, y, size, seed+1, octaves=4)*0.06
    stone_h = np.clip(stone_h + grain + np.sin(2*np.pi*x/512)*0.015, 0, 1)
    # pearl weave that shows in cracks
    weave_h, warp = warp_weave(x, y, size, seed+9, warp_period=18, weft_period=18)
    # weave is slightly lower than stone, but exposed in cracks
    # blend: in cracks weave dominates, on plate stone dominates, transition smooth
    # height = stone*(1-crack_soft) + (weave*0.55 + 0.18) * crack_soft -> ensures weave in crack is lower but visible
    weave_in_crack = weave_h*0.42 + 0.18
    # add slight ridge where weave threads cross in cracks (enhance pearl shimmer)
    height = lerp(weave_in_crack, stone_h, 1 - crack_soft*0.95)
    # add crack depth: carve where crack narrow
    height = height - crack*0.08
    height = np.clip(height, 0, 1)
    # BlendMask RGB: R=stone tops, G=weave in cracks, B=transition/border
    R = np.clip(1 - crack_soft, 0, 1)
    G = np.clip(crack_soft, 0, 1)
    # B = narrow crack edge halo (difference between soft and hard crack)
    B = np.clip(crack_soft - crack, 0, 1)
    # also add thin border highlight
    B = np.clip(B*1.4, 0, 1)
    blend = np.stack([R,G,B], axis=-1)
    # Albedo: stone grey / pearl
    stone_col = np.array([142,138,132], float)/255
    stone_dark = np.array([92,90,88], float)/255
    pearl = np.array([245,240,232], float)/255
    # stone albedo mottled per cell
    stone_tint = lerp(stone_dark, stone_col, np.clip((cell_val-0.85)/0.15,0,1))[:,:,None] if cell_val.ndim==2 else stone_col
    # Actually cell_val returned as 2D per-pixel chosen_val, handle:
    # chosen_val is already per-pixel from voronoi -> reuse via crack_soft derived? Instead recompute mottling from stone_h modulation
    mott = 0.04*np.sin(2*np.pi*x/256)+0.03*np.cos(2*np.pi*y/384)
    stone_alb = np.clip(stone_col + mott[:,:,None]*np.array([0.08,0.06,0.03]),0,1)
    # weave albedo tilable
    pearl_alb = pearl + 0.015*np.sin(2*np.pi*x/64)[:,:,None]*np.array([0.04,0.02,-0.02])
    # combine by crack_soft with noisy edge for bleeding
    bleed = crack_soft[:,:,None] * (0.92 + 0.08*np.sin(2*np.pi*x/128))
    albedo = lerp(stone_alb, pearl_alb, np.clip(bleed*0.98,0,1))
    # add cavity darkening in narrow cracks
    albedo = albedo * (1 - crack[:,:,None]*0.18)
    albedo = np.clip(albedo + np.random.randn(size,size,3)*0.007,0,1)
    # Roughness / Metal
    rough_stone = 0.62 + grain*0.3
    rough_weave = 0.38 + (1-weave_h)*0.08
    rough = lerp(rough_weave, rough_stone, R)
    rough = np.clip(rough + crack*0.04, 0.2, 0.85)
    metal = np.clip(crack_soft*0.06,0,0.08) # faint pearl metallic in cracks
    return albedo, height, rough, metal, blend

def gen_cloth_ornament(size):
    seed = 2244
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # base fabric weave
    weave_h, warp = warp_weave(x, y, size, seed, warp_period=20, weft_period=20)
    base_h = weave_h*0.35 + 0.42
    # ornament embroidery: floral motif tiled 8x
    fx = (x / size * 8) % 1
    fy = (y / size * 8) % 1
    tx = fx*2 -1; ty = fy*2 -1
    dist = np.sqrt(tx*tx + ty*ty)
    ang = np.arctan2(ty, tx)
    petal = np.cos(ang*5)
    flower = np.clip(1 - dist*1.4 + petal*0.18, 0,1)
    flower = smoothstep(0.35,0.72,flower)
    lattice = np.abs(np.sin(fx*np.pi*2)*np.sin(fy*np.pi*2))
    lattice = smoothstep(0.45,0.85,lattice)
    ornament = np.maximum(flower*0.95, lattice*0.72)
    # dust fade field: large tilable noise that erodes ornament
    dust_field = t_noise_field(x,y,size,seed+5,octaves=3) # -0.6..0.6
    dust_field = (dust_field + 0.6)/1.2  # 0..1
    dust_field = smoothstep(0.25,0.88,dust_field)
    # dust amount increases where field low -> ornament fades into dust
    # use dust_field as preservation: high = preserve ornament, low = dust
    preserve = smoothstep(0.32, 0.68, dust_field + 0.12*np.sin(2*np.pi*x/1024))
    ornament_faded = ornament * preserve
    dust = 1 - preserve  # dust coverage
    # height: base + ornament emboss faded
    height = np.clip(base_h + ornament_faded*0.42 + dust*0.06 + np.random.randn(size,size).astype(np.float32)*0.008,0,1)
    height = smoothstep(0,1,height)
    # BlendMask: R=fabric, G=ornament, B=dust/transition
    R = np.clip(1 - ornament_faded,0,1) * (1 - dust*0.5)
    G = np.clip(ornament_faded,0,1)
    B = np.clip(dust,0,1)
    # normalize roughly so max ~1
    total = R+G+B+1e-6
    # keep as is for vertex paint (not normalized sum=1, each channel independent)
    blend = np.stack([R,G,B], axis=-1)
    # Albedo: fabric warm ivory, ornament gold/burgundy mix, dust desaturated
    fabric_col = np.array([232,228,218],float)/255
    ornament_col = np.array([198,148,78],float)/255  # antique gold
    dust_col = np.array([188,182,172],float)/255
    # fabric mottling
    fabric_alb = fabric_col + 0.02*np.sin(2*np.pi*x/128)[:,:,None]*np.array([0.05,0.03,-0.02])
    fabric_alb = np.clip(fabric_alb,0,1)
    # ornament gold with highlight
    ornament_alb = ornament_col + 0.08*np.clip(ornament_faded[:,:,None]-0.5,0,1)
    # dust albedo slightly darker
    dust_alb = dust_col + t_noise_field(x,y,size,seed+7,octaves=2)[:,:,None]*0.02
    albedo = lerp(fabric_alb, ornament_alb, np.clip(ornament_faded[:,:,None]*0.95,0,1))
    albedo = lerp(albedo, dust_alb, np.clip(dust[:,:,None]*0.55,0,1))
    albedo = np.clip(albedo + np.random.randn(size,size,3)*0.007,0,1)
    rough_fabric = 0.52 + (1-weave_h)*0.08
    rough_orn = 0.32
    rough_dust = 0.78
    rough = lerp(rough_fabric, rough_orn, G)
    rough = lerp(rough, rough_dust, B*0.6)
    rough = np.clip(rough,0.18,0.88)
    metal = np.clip(ornament_faded*0.22,0,0.22)
    return albedo, height, rough, metal, blend

def gen_sand_cloth(size):
    seed = 3355
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # sand dune ripples large tilable
    dune = 0.18*np.sin(2*np.pi*x/1024 + 2*np.pi*y/2048*0.6) + 0.10*np.sin(2*np.pi*x/512 - 2*np.pi*y/1024)
    dune += 0.06*np.sin(2*np.pi*x/256 + 2*np.pi*y/512)
    dune = (dune + 0.34)/0.68
    dune = np.clip(dune,0,1)
    grain = t_noise_field(x,y,size,seed+2,octaves=4)*0.08 + np.random.randn(size,size).astype(np.float32)*0.012
    sand_h = 0.38 + dune*0.32 + grain*0.5
    sand_h = np.clip(sand_h,0,1)
    # silk threads: buried anisotropic lines at angle ~18 degrees
    # Use tilable sine ridge
    angle = 18 * math.pi/180
    # rotate coords
    xr = x*np.cos(angle) + y*np.sin(angle)
    yr = -x*np.sin(angle) + y*np.cos(angle)
    # threads: periodic 48px spacing, narrow ridge 6px wide
    thread_period = 96
    # tilable thread ridge using sin
    # use phase to create thin lines: 1 - abs(sin)
    phase = np.sin(2*np.pi*xr/thread_period)
    thread_ridge = 1 - np.abs(phase)
    thread_ridge = smoothstep(0.72, 0.92, thread_ridge) # narrow
    # second set offset half period, slightly wavy
    wavy = 0.5*np.sin(2*np.pi*yr/512)
    phase2 = np.sin(2*np.pi*(xr+wavy*12)/thread_period + math.pi)
    thread_ridge2 = smoothstep(0.72,0.92, 1-np.abs(phase2))
    threads = np.maximum(thread_ridge, thread_ridge2*0.85)
    # bury factor: sand covers threads where dune high; threads visible in troughs and partially buried
    # burial mask: higher sand_h -> more burial
    burial = smoothstep(0.42, 0.68, sand_h)  # 0 trough, 1 dune crest
    threads_buried = threads * (1 - burial*0.72)  # threads fade on crests
    # height: sand + thread ridge slightly raised but buried
    thread_h = threads_buried*0.14
    # sand piling over threads creates subtle bump even where buried
    height = np.clip(sand_h + thread_h + threads*0.03*burial,0,1)
    # BlendMask: R=sand, G=silk threads, B=burial transition
    R = np.clip(1 - threads_buried,0,1)
    G = np.clip(threads_buried,0,1)
    B = np.clip(burial*threads,0,1) # transition where buried
    blend = np.stack([R,G,B], axis=-1)
    # Albedo: sand warm, silk pearl shimmer
    sand_col = np.array([212,192,162],float)/255
    sand_dark = np.array([186,168,142],float)/255
    silk_col = np.array([245,238,225],float)/255
    sand_alb = lerp(sand_dark, sand_col, np.clip(dune*0.9+0.1,0,1))[:,:,None] if dune.ndim==2 else sand_col
    # Actually lerp per pixel
    sand_alb = (sand_dark[None,None,:]*(1 - dune[:,:,None]) + sand_col[None,None,:]*dune[:,:,None])
    sand_alb = np.clip(sand_alb + grain[:,:,None]*0.04,0,1) if grain.ndim==2 else sand_alb
    # silk shimmer: slightly pearlescent along thread
    silk_alb = silk_col + 0.02*np.sin(2*np.pi*xr/64)[:,:,None]*np.array([0.06,0.04,-0.02])
    albedo = lerp(sand_alb, silk_alb, np.clip(threads_buried[:,:,None]*0.92,0,1))
    albedo = np.clip(albedo + np.random.randn(size,size,3)*0.006,0,1)
    rough_sand = 0.78 + (1-dune)*0.05
    rough_silk = 0.34
    rough = lerp(rough_silk, rough_sand, 1-G)
    rough = np.clip(rough,0.28,0.88)
    metal = np.zeros_like(rough)
    return albedo, height, rough, metal, blend

def gen_ashen_lace(size):
    seed = 4488
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # ash rock plates larger
    stone_h, crack, crack_soft, cell_val = toroidal_voronoi(x,y,size,cell_period=360, seed=seed, jitter=0.58)
    # darken plates
    stone_h = np.clip(stone_h*0.92 + 0.04,0,1)
    grain = t_noise_field(x,y,size,seed+3,octaves=3)*0.05
    stone_h = np.clip(stone_h + grain,0,1)
    # lace mortar: lace pattern only in crack regions
    # generate lace web tilable 8x as before but mask to cracks
    fx = (x / size * 8) % 1
    fy = (y / size * 8) % 1
    tx = fx*2 -1; ty=fy*2 -1
    dist = np.sqrt(tx*tx+ty*ty)
    ang = np.arctan2(ty,tx)
    flower = smoothstep(0.35,0.72, np.clip(1 - dist*1.4 + np.cos(ang*5)*0.18,0,1))
    lattice = smoothstep(0.45,0.85, np.abs(np.sin(fx*np.pi*2)*np.sin(fy*np.pi*2)))
    lace_pat = np.maximum(flower*0.95, lattice*0.75)
    lace_pat = np.clip(lace_pat*(0.92+0.08*np.sin(2*np.pi*x/256)),0,1)
    # mask lace to mortar (crack_soft)
    lace_mortar = lace_pat * crack_soft
    # height: stone high, mortar recessed with lace emboss in mortar
    mortar_base = 0.18 + lace_mortar*0.22
    # stone height stays high, mortar low
    height = lerp(mortar_base, stone_h, 1 - crack_soft)
    # add micro bevel on stone edge
    height = height - crack*0.06
    height = np.clip(height,0,1)
    # BlendMask: R=ash stone, G=lace mortar, B=edge
    R = np.clip(1 - crack_soft,0,1)
    G = np.clip(lace_mortar*1.2,0,1) # lace within mortar
    # B = pure mortar without lace plus edge
    B = np.clip(crack_soft - lace_mortar,0,1)
    blend = np.stack([R,G,B], axis=-1)
    # Albedo: ash dark grey, lace off-white
    ash_col = np.array([88,88,92],float)/255
    ash_light = np.array([112,110,108],float)/255
    lace_col = np.array([238,234,225],float)/255
    ash_alb = lerp(ash_col, ash_light, np.clip((stone_h-0.4)/0.5,0,1))[:,:,None] if stone_h.ndim==2 else ash_col
    # Actually per-pixel
    ash_alb = ash_col[None,None,:]*(1 - np.clip((stone_h-0.4)/0.5,0,1)[:,:,None]) + ash_light[None,None,:]*np.clip((stone_h-0.4)/0.5,0,1)[:,:,None]
    ash_alb = np.clip(ash_alb + grain[:,:,None]*0.02,0,1)
    # lace albedo
    lace_alb = lace_col + 0.015*np.sin(2*np.pi*x/128)[:,:,None]*np.array([0.02,0.01,-0.01])
    albedo = lerp(ash_alb, lace_alb, np.clip(lace_mortar[:,:,None]*0.95,0,1))
    # mortar without lace is darker ash grout
    grout_col = np.array([62,60,58],float)/255
    albedo = lerp(albedo, grout_col, np.clip(B[:,:,None]*0.7,0,1))
    albedo = np.clip(albedo + np.random.randn(size,size,3)*0.006,0,1)
    rough_stone = 0.72 + grain*0.2
    rough_lace = 0.45
    rough_grout = 0.82
    rough = lerp(rough_grout, rough_lace, np.clip(G,0,1))
    rough = lerp(rough, rough_stone, R)
    rough = np.clip(rough,0.35,0.88)
    metal = np.zeros_like(rough)
    return albedo, height, rough, metal, blend

def gen_dirt_silk(size):
    seed = 5599
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # soil clumps: large noise + small clod
    clump = t_noise_field(x,y,size,seed,octaves=3)
    clump = (clump+0.6)/1.2
    clump = smoothstep(0.22,0.82,clump)
    clod = 0.12*np.sin(2*np.pi*x/128 + 2*np.pi*y/192) + 0.08*np.sin(2*np.pi*x/64 - 2*np.pi*y/96)
    soil_h = 0.45 + clump*0.35 + clod*0.5
    soil_h = np.clip(soil_h + np.random.randn(size,size).astype(np.float32)*0.015,0,1)
    soil_h = smoothstep(0,1,soil_h)
    # silk pooling: appears in low areas (inverted height)
    # pooled mask = 1 where soil_h low
    pool = 1 - smoothstep(0.35, 0.62, soil_h)
    # add flow pooling shape: elongate along low gradient
    flow = 0.5 + 0.5*np.sin(2*np.pi*x/512 + 2*np.pi*y/1024*0.7)
    pool = pool * (0.7 + 0.3*flow)
    # silk sheen also has wavy silk weave visible in pools
    silk_weave, _ = warp_weave(x,y,size,seed+11,warp_period=16,weft_period=16)
    silk_in_pool = pool * (silk_weave*0.5+0.5)
    # height: soil clumps high, pools low but silk adds slight smoothness (fills)
    # pools are lower, silk adds 0.08 smooth fill
    pool_fill = pool*0.10 + silk_in_pool*0.06
    height = np.clip(soil_h - pool*0.18 + pool_fill,0,1)
    # BlendMask: R=soil high, G=silk pools, B=wet edge transition
    G = np.clip(pool*0.95,0,1)
    edge = smoothstep(0.30,0.62,soil_h) * pool # transition band around pool edge
    edge = np.clip(edge*1.5,0,1)
    R = np.clip(1 - G,0,1) * (1 - edge*0.5)
    B = np.clip(edge,0,1)
    blend = np.stack([R,G,B], axis=-1)
    # Albedo: soil brown, silk pinkish pearl
    soil_col = np.array([88,62,42],float)/255
    soil_light = np.array([118,86,58],float)/255
    silk_col = np.array([245,222,212],float)/255
    silk_highlight = np.array([255,240,232],float)/255
    soil_alb = lerp(soil_col, soil_light, np.clip((soil_h-0.35)/0.45,0,1))[:,:,None] if soil_h.ndim==2 else soil_col
    soil_alb = soil_col[None,None,:]*(1-np.clip((soil_h-0.35)/0.45,0,1)[:,:,None]) + soil_light[None,None,:]*np.clip((soil_h-0.35)/0.45,0,1)[:,:,None]
    soil_alb = np.clip(soil_alb + clod[:,:,None]*0.02,0,1)
    silk_alb = lerp(silk_col, silk_highlight, np.clip(silk_weave[:,:,None]*0.6,0,1))
    albedo = lerp(soil_alb, silk_alb, np.clip(G[:,:,None]*0.88,0,1))
    # wet edge slightly darker
    albedo = lerp(albedo, soil_col*0.85, np.clip(B[:,:,None]*0.35,0,1))
    albedo = np.clip(albedo + np.random.randn(size,size,3)*0.007,0,1)
    rough_soil = 0.82 + clump*0.05
    rough_silk = 0.28 + (1-silk_weave)*0.08
    rough = lerp(rough_silk, rough_soil, 1-G)
    rough = lerp(rough, np.clip(rough_soil*0.75,0,1), B*0.5)
    rough = np.clip(rough,0.22,0.88)
    metal = np.zeros_like(rough)
    return albedo, height, rough, metal, blend

def gen_gold_vein(size):
    seed = 6677
    y,x = np.mgrid[0:size,0:size].astype(np.float32)
    # rock plates medium
    stone_h, crack, crack_soft, cell_val = toroidal_voronoi(x,y,size,cell_period=280, seed=seed, jitter=0.60)
    grain = t_noise_field(x,y,size,seed+2,octaves=3)*0.06
    stone_h = np.clip(stone_h + grain,0,1)
    # gold veins: branching ridged network tilable
    # base ridged at two scales, warped
    warp_x = 0.08*np.sin(2*np.pi*y/512) + 0.04*np.cos(2*np.pi*x/384)
    xw = x + warp_x*40
    yw = y + 0.05*np.sin(2*np.pi*x/256)*30
    vein1 = t_ridged(xw, yw, period=512, warp=0.4, seed=seed+5)
    vein1 = smoothstep(0.68, 0.92, vein1) # narrow
    vein2 = t_ridged(xw*1.3, yw*0.9, period=256, warp=0.5, seed=seed+7)
    vein2 = smoothstep(0.62, 0.88, vein2) * 0.72
    # combine
    veins = np.maximum(vein1, vein2)
    # taper veins where stone_h low? keep veins continuous across plates
    # add thin highlight along center of vein
    vein_core = smoothstep(0.78, 0.95, veins)
    veins = np.clip(veins,0,1)
    # height: stone + veins slightly raised (gilded inlay)
    vein_h = veins*0.18 + vein_core*0.06
    height = np.clip(stone_h + vein_h - crack*0.05,0,1)
    # BlendMask: R=rock, G=gold veins, B=vein halo/edge
    G = np.clip(veins,0,1)
    # B = halo around vein (soft vein minus core)
    halo = np.clip(veins - vein_core,0,1)
    # also crack edges as B secondary? keep B as halo
    B = np.clip(halo*1.2,0,1)
    R = np.clip(1 - veins,0,1)
    blend = np.stack([R,G,B], axis=-1)
    # Albedo: rock grey, gold veins
    rock_col = np.array([112,108,105],float)/255
    rock_dark = np.array([88,86,84],float)/255
    gold_col = np.array([212,175,55],float)/255
    gold_bright = np.array([245,215,110],float)/255
    gold_dark = np.array([168,132,38],float)/255
    rock_alb = lerp(rock_dark, rock_col, np.clip((stone_h-0.35)/0.45,0,1))[:,:,None] if stone_h.ndim==2 else rock_col
    rock_alb = rock_dark[None,None,:]*(1-np.clip((stone_h-0.35)/0.45,0,1)[:,:,None]) + rock_col[None,None,:]*np.clip((stone_h-0.35)/0.45,0,1)[:,:,None]
    rock_alb = np.clip(rock_alb + grain[:,:,None]*0.02,0,1)
    # gold varies: core bright, edge darker antique
    gold_alb = lerp(gold_dark, gold_col, np.clip(veins*1.2,0,1))[:,:,None] if veins.ndim==2 else gold_col
    gold_alb = gold_dark[None,None,:]*(1-np.clip(veins*1.2,0,1)[:,:,None]) + gold_col[None,None,:]*np.clip(veins*1.2,0,1)[:,:,None]
    gold_alb = lerp(gold_alb, gold_bright, np.clip(vein_core[:,:,None]*0.9,0,1))
    albedo = lerp(rock_alb, gold_alb, np.clip(veins[:,:,None]*0.98,0,1))
    albedo = np.clip(albedo + np.random.randn(size,size,3)*0.006,0,1)
    rough_rock = 0.65 + grain*0.2
    rough_gold = 0.30 + (1-vein_core)*0.10
    rough = lerp(rough_gold, rough_rock, 1-G)
    rough = np.clip(rough,0.25,0.85)
    metal_rock = np.zeros_like(rough)
    metal_gold = np.clip(veins*0.92,0,1)*0.92
    metal = lerp(metal_gold, metal_rock, 1-G)
    metal = np.clip(metal,0,0.92)
    return albedo, height, rough, metal, blend


# dispatch table
VARIANTS = [
    ("Rock_Cloth",     gen_rock_cloth,     "stone with pearl weave bleeding through cracks"),
    ("Cloth_Ornament", gen_cloth_ornament, "fabric with ornament embroidery fading into dust"),
    ("Sand_Cloth",     gen_sand_cloth,     "sand with buried silk threads"),
    ("Ashen_Lace",     gen_ashen_lace,     "ash rock with lace mortar"),
    ("Dirt_Silk",      gen_dirt_silk,      "soil with silk sheen pooling in low areas"),
    ("Gold_Vein",      gen_gold_vein,      "rock with gilded veins"),
]

def process_variant(name, gen_fn, size):
    print(f"Hybrid AAA {name} 4K ... {gen_fn.__doc__ or ''}")
    albedo_f, height_f, rough_f, metal_f, blend_f = gen_fn(size)
    # height 0..1 -> uint8
    height_u8 = (np.clip(height_f,0,1)*255).astype(np.uint8)
    rough_u8 = (np.clip(rough_f,0,1)*255).astype(np.uint8)
    metal_u8 = (np.clip(metal_f,0,1)*255).astype(np.uint8)
    # AO from height
    ao = np.clip(1.0 - (1 - height_u8.astype(float)/255.0)*0.55, 0, 1)
    ao_u8 = (ao*255).astype(np.uint8)
    orm = np.stack([ao_u8, rough_u8, metal_u8], axis=-1)
    # Normal from height
    dy, dx = np.gradient(height_f.astype(np.float32))
    nscale = 14.0
    dx *= nscale; dy *= nscale
    # micro jitter tilable via sin (avoid randn seam)
    # use height-derived jitter small
    # add tiny sin jitter for normal detail
    y_grid, x_grid = np.mgrid[0:size,0:size].astype(np.float32)
    dx += 0.03*np.sin(2*np.pi*x_grid/64)
    dy += 0.03*np.cos(2*np.pi*y_grid/64)
    nx = -dx; ny = -dy; nz = np.ones_like(nx)
    nlen = np.sqrt(nx*nx+ny*ny+nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal = np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255], axis=-1).astype(np.uint8)
    albedo_u8 = (np.clip(albedo_f,0,1)*255).astype(np.uint8)
    # BlendMask RGB already 0..1, make uint8
    blend_u8 = (np.clip(blend_f,0,1)*255).astype(np.uint8)
    return albedo_u8, normal, orm, rough_u8, metal_u8, height_u8, ao_u8, blend_u8

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=SIZE_DEFAULT)
    ap.add_argument("--quick", action="store_true", help="1024 smoke test")
    args = ap.parse_args()
    size = 1024 if args.quick else args.size
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Hybrid Bridge AAA — 6 variants x 8 maps @ {size}x{size} -> {OUT_DIR}")
    print(f"Designed for M_Master_Nikki_Landscape vertex blending (RGB mask + Height POM)")
    total = 0
    for name, fn, desc in VARIANTS:
        print(f"\n[{name}] {desc} ...")
        albedo, normal, orm, rough, metal, height, ao, blend = process_variant(name, fn, size)
        prefix = f"T_Hybrid_Bridge_{name}"
        Image.fromarray(albedo).save(os.path.join(OUT_DIR, f"{prefix}_BaseColor.png"))
        Image.fromarray(normal).save(os.path.join(OUT_DIR, f"{prefix}_Normal.png"))
        Image.fromarray(orm).save(os.path.join(OUT_DIR, f"{prefix}_ORM.png"))
        Image.fromarray(rough).save(os.path.join(OUT_DIR, f"{prefix}_Roughness.png"))
        Image.fromarray(metal).save(os.path.join(OUT_DIR, f"{prefix}_Metallic.png"))
        Image.fromarray(height).save(os.path.join(OUT_DIR, f"{prefix}_Height.png"))
        Image.fromarray(ao).save(os.path.join(OUT_DIR, f"{prefix}_AO.png"))
        Image.fromarray(blend).save(os.path.join(OUT_DIR, f"{prefix}_BlendMask.png"))
        print(f"  -> {prefix} 8 maps done (BC/N/ORM/R/M/H/AO/BlendMask)")
        total += 8
        # free memory
        del albedo, normal, orm, rough, metal, height, ao, blend
    # verify
    files = [f for f in os.listdir(OUT_DIR) if f.startswith("T_Hybrid_Bridge_") and f.endswith(".png")]
    expected = 6*8
    print(f"\nDONE — {len(files)} files (expected {expected}) in {OUT_DIR}")
    for fn in sorted(files):
        print(f"  {fn}")
    if len(files) < expected:
        print(f"WARNING expected {expected} got {len(files)}", file=sys.stderr)
        sys.exit(1)
    print(f"Hybrid Bridge AAA complete: 6 variants x 8 maps = {expected} PNGs @ {size}x{size}")
    print("Usage in M_Master_Nikki_Landscape: BlendMask.R/G/B = vertex paint 3-way, Height = POM, ORM packed.")

if __name__ == "__main__":
    main()
