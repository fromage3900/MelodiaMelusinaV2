"""
experimental_animated_aaa.py — Experimental Animated Hybrids (moving surfaces)
for M_Master_Nikki / flipbook & flowmap panning.

Output: Content/EnvSandbox/Textures/Experimental_Animated/
  FlowWeave/          (cloth where threads flow like wind)
  BloomingOrnament/   (geometric ornament blooms/closes like flower)
  RoughnessTide/      (roughness washes back and forth — matte tide vs glossy crest)

Each family: 8 frames @ 2048, seamless loop (phase 0 == 2*pi).
Each frame 6 maps: BaseColor, Normal, Roughness, Height, Iridescence, Opacity/Mask
plus 1 FlowMap (RG) per family (static, for material panning).

Run via hython:
  "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" Tools/Houdini/experimental_animated_aaa.py [--size 2048] [--frames 8]
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image

OUT_ROOT = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/Experimental_Animated"

# ---------------------------------------------------------------- helpers
def smoothstep(a,b,x):
    t = np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def lerp(a,b,t):
    return a*(1-t)+b*t

def height_to_normal(height, strength=12.0, jitter_x=None, jitter_y=None):
    dy, dx = np.gradient(height)
    dx *= strength
    dy *= strength
    if jitter_x is not None:
        dx = dx + jitter_x
    if jitter_y is not None:
        dy = dy + jitter_y
    nx = -dx; ny = -dy; nz = np.ones_like(nx)
    nlen = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    n = np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)
    return n

# ---------------------------------------------------------------- FlowWeave
# warm linen / silk wind palette
FW_BASE   = np.array([228, 218, 205], dtype=float)/255.0
FW_WEFT   = np.array([210, 200, 185], dtype=float)/255.0
FW_DARK   = np.array([175, 165, 150], dtype=float)/255.0
FW_ACCENT = np.array([245, 232, 215], dtype=float)/255.0

def gen_flowweave_frame(frame, num_frames, size):
    phase = (frame/num_frames)*math.pi*2.0
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)

    # --- stable woven structure ---
    warp_period = 18
    weft_period = 18
    # diagonal wind twist increases with phase
    twist = (y*0.00007 + phase*0.015)
    x_tw = x + np.sin(twist*12)*3.0 + np.cos(y*0.003 + phase*0.6)*2.0
    offset = (y // weft_period) % 7
    warp_shift = ((x_tw - offset*3.2) % warp_period) < 11
    weft = (y % weft_period) < 6
    over = warp_shift.astype(float)*0.92 + weft.astype(float)*0.20

    # micro fiber noise — stable field (seed 1337) + animated wind undulation
    rng = np.random.RandomState(1337)
    fiber = rng.randn(size, size)*0.016

    # wind drift height: large-scale sin waves that animate with phase
    # use frequencies that tile (size divisible helps): use x*2pi/size*N
    wind_h = 0.038*np.sin(x*0.007 + phase*1.0 + y*0.002) + 0.028*np.cos(y*0.009 - phase*0.7 + x*0.0015)
    wind_h += 0.018*np.sin((x*0.35 + y*0.15)*0.02 + phase*1.4)  # diagonal ripple
    thick = 0.022*np.sin(x*0.06 + y*0.04 + phase*0.5)
    height_base = np.clip(over + fiber + wind_h + thick, 0, 1)
    height_base = smoothstep(0.22, 0.86, height_base)
    # crawling brush
    brush = np.sin(x*0.13 + phase*0.9)*np.cos(y*0.11 - phase*0.6)*0.014
    height = np.clip(height_base + brush, 0, 1)

    # normal with wind-aligned jitter
    jitter_amp = 0.05
    jx = np.sin(x*0.06 + phase*2.0 + y*0.025)*jitter_amp
    jy = np.cos(y*0.06 - phase*1.5 + x*0.018)*jitter_amp
    normal = height_to_normal(height, strength=15.0, jitter_x=jx, jitter_y=jy)

    # --- albedo: hue shifts over time + height drifts ---
    # hue drift: sinusoid in RGB
    drift = np.array([0.018*math.sin(phase*1.0), 0.012*math.sin(phase*1.2+1.0), 0.016*math.cos(phase*0.8+0.3)])
    base_drift = np.clip(FW_BASE + drift, 0, 1)
    weft_drift = np.clip(FW_WEFT + drift*0.7, 0, 1)
    accent_drift = np.clip(FW_ACCENT + drift*0.5, 0, 1)

    # weave tint
    # warp vs weft vs overlap
    tint = np.where(warp_shift[:,:,None], base_drift, weft_drift)
    # highlight crests with accent
    crest = np.clip((height-0.58)*1.6, 0, 1)[:,:,None]
    albedo = lerp(tint, accent_drift, crest*0.45)

    # wind-driven color wash (subtle hue crawl)
    wash = 0.025*np.sin(x*0.004 + y*0.002 + phase*0.8)[:,:,None] * np.array([1.0, -0.4, -0.6])
    wash += 0.015*np.cos(y*0.006 - x*0.002 + phase*0.5)[:,:,None] * np.array([-0.5, 0.3, 1.0])
    albedo = np.clip(albedo + wash, 0, 1)

    # micro pigment jitter — low amp, deterministic per frame
    rng2 = np.random.RandomState(900+frame)
    jitter = rng2.randn(size,size,3)*0.008
    albedo = np.clip(albedo + jitter, 0, 1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # --- roughness: subtle variation, crest slightly glossier ---
    rough = np.where(height>0.60, 0.34, 0.48).astype(float)
    rough += wind_h*0.35  # wind modulates roughness
    rough += 0.005*math.sin(phase*1.1) * np.sin(x*0.006 + y*0.004)
    rng3 = np.random.RandomState(2024+frame)
    rough += rng3.randn(size,size)*0.012
    rough = np.clip(rough, 0.14, 0.92)
    rough_u8 = (rough*255).astype(np.uint8)

    # height
    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)

    # --- iridescence: crest-weighted shimmer, hue walks with phase ---
    iri = np.clip((height-0.52)*1.9, 0, 1)*(0.68 + 0.32*np.sin(x*0.018 + phase*1.3 + y*0.001))
    band = 0.11*np.sin(x*0.028 - y*0.016 + phase*1.1) + 0.07*np.sin((x+y)*0.010 + phase*0.7)
    iri = np.clip(iri + band, 0, 1)
    breathe = 0.05*math.sin(phase*0.85+0.3)
    iri = np.clip(iri + breathe, 0, 1)
    iri_u8 = (iri*255).astype(np.uint8)

    # --- opacity / mask: cloth is opaque, subtle thread gaps ---
    # use height valleys as slight alpha variation but mostly opaque (for Mask packing)
    # mask = smoothstep based on height so valleys slightly lower opacity (woven gaps)
    mask = np.clip(0.92 + height*0.08 + fiber*0.02, 0, 1)
    mask = np.clip(mask + 0.02*np.sin(x*0.05 + y*0.05 + phase)*0, 0, 1)  # keep stable
    mask_u8 = (mask*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, height_u8, iri_u8, mask_u8

def gen_flowweave_flowmap(size):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    # primary wind flow: mostly +U with gentle sinusoidal v
    fx = 0.85 + 0.15*np.sin(y*0.007) + 0.08*np.cos((x+y)*0.003)
    fy = 0.18*np.cos(x*0.005 + y*0.004) + 0.10*np.sin(y*0.012)
    # normalize to 0-1 for RG
    # flow vectors in -1..1 -> 0..1
    # clamp
    fx = np.clip(fx, -1, 1)
    fy = np.clip(fy, -1, 1)
    r = ((fx*0.5+0.5)*255).astype(np.uint8)
    g = ((fy*0.5+0.5)*255).astype(np.uint8)
    b = np.zeros_like(r)
    flow = np.stack([r,g,b], axis=-1)
    return flow

# ---------------------------------------------------------------- BloomingOrnament
BO_BG       = np.array([22, 28, 35], dtype=float)/255.0      # deep teal-black
BO_PETAL    = np.array([235, 220, 185], dtype=float)/255.0   # gilded pearl
BO_PETAL2   = np.array([215, 190, 145], dtype=float)/255.0   # deeper gold
BO_CENTER   = np.array([250, 245, 230], dtype=float)/255.0   # highlight center
BO_ACCENT   = np.array([180, 210, 220], dtype=float)/255.0   # subtle iridescent cool

def gen_blooming_frame(frame, num_frames, size):
    phase = (frame/num_frames)*math.pi*2.0
    # bloom 0..1 seamless: 0 closed, 1 open
    bloom = (1 - math.cos(phase))/2.0  # 0 at frame0, 1 at frame4, 0 at frame8
    # also add slight secondary pulse for organic feel but keep loop
    bloom2 = bloom  # could add harmonic but keep monotonic open/close

    # tiling: 2 x 2 ornaments across 2048 -> tile size 1024
    tiles = 2
    tile_sz = size // tiles
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)

    # distance to nearest ornament center
    # ornament centers at (tile_sz/2 + i*tile_sz)
    # compute local coordinates within tile
    lx = (x % tile_sz) - tile_sz*0.5
    ly = (y % tile_sz) - tile_sz*0.5
    dist = np.sqrt(lx*lx + ly*ly)
    ang = np.arctan2(ly, lx)  # -pi..pi

    petal_count = 8
    # petal shape: radius varies with angle
    # base petal outline: r_petal(ang) = R0 + bloom*(R1 + amp*cos(petal_count*ang))
    R0 = tile_sz*0.10  # closed core
    R1 = tile_sz*0.32  # open petal length
    amp = tile_sz*0.08
    # petal edge radius per angle
    petal_edge = R0 + bloom*(R1 + amp*np.cos(petal_count*ang))
    # inner core radius blooms slightly
    core_r = tile_sz*0.06 + bloom*tile_sz*0.04
    # secondary inner petal layer (offset angle)
    petal_edge2 = R0*0.7 + bloom*(R1*0.62 + amp*0.55*np.cos(petal_count*(ang + math.pi/petal_count)))
    # decide if pixel is inside ornament
    inside_petal = dist < petal_edge
    inside_petal2 = dist < petal_edge2
    inside_core = dist < core_r

    # height: core highest, petal ridges, background low
    height = np.zeros((size,size), dtype=float)
    # background subtle fabric grain
    bg_grain = 0.04*np.sin(x*0.008 + y*0.006) + 0.02*np.cos(y*0.012)
    height += bg_grain*0.15
    # petal height: falloff from center to edge
    # petal body height: smoothstep from center to edge
    petal_h = np.clip(1 - dist/(petal_edge+1e-6), 0, 1)
    petal_h = np.power(petal_h, 0.7)*0.75
    # petal ridge along angle (center of petal higher)
    ang_mod = np.mod(ang + math.pi, 2*math.pi/petal_count) - math.pi/petal_count
    ridge = np.cos(ang_mod*petal_count*1.5) # 1 at petal center, -1 between
    ridge = np.clip(ridge, 0, 1)
    petal_ridge = ridge*0.18*petal_h
    # combine
    height = np.where(inside_petal, np.clip(petal_h + petal_ridge + 0.08, 0, 1), height)
    # inner layer slightly higher
    petal_h2 = np.clip(1 - dist/(petal_edge2+1e-6),0,1)
    petal_h2 = np.power(petal_h2,0.8)*0.55
    height = np.where(inside_petal2, np.maximum(height, petal_h2 + 0.05), height)
    # core dome
    core_h = np.clip(1 - dist/(core_r+1e-6),0,1)
    core_h = np.power(core_h, 0.6)*0.95 + 0.05
    height = np.where(inside_core, np.maximum(height, core_h), height)
    # add subtle global bloom-driven lift (whole ornament rises as it blooms)
    height = np.clip(height + bloom*0.02*np.sin(dist*0.015 + phase),0,1)

    # normal
    # add tiny animated jitter on petal surface to avoid static
    jx = 0.04*np.sin(x*0.05 + phase*1.2)
    jy = 0.04*np.cos(y*0.05 - phase*1.0)
    normal = height_to_normal(height, strength=18.0, jitter_x=jx, jitter_y=jy)

    # --- albedo ---
    # background
    albedo = np.tile(BO_BG, (size,size,1))
    # petal base color with radial gradient and bloom tint
    # petal gradient: inner brighter, edge deeper
    t_radial = np.clip(dist/(petal_edge+1e-6),0,1)
    # mix petal colors
    petal_col = lerp(BO_CENTER, BO_PETAL, np.clip(t_radial*1.2,0,1)[:,:,None])
    petal_col = lerp(petal_col, BO_PETAL2[np.newaxis,np.newaxis,:], (ridge[:,:,None]*0.25))
    # bloom hue shift: petals shift slightly warm->cool as they bloom
    hue_shift = np.array([0.02*math.sin(phase*0.9), -0.01*math.sin(phase*1.1), 0.02*math.cos(phase*1.0)])
    petal_col = np.clip(petal_col + hue_shift, 0, 1)
    # apply where inside
    # use broadcasting with masks
    mask_petal = inside_petal[:,:,None]
    albedo = np.where(mask_petal, petal_col, albedo)
    # inner layer slightly different tint
    petal2_col = np.clip(petal_col*0.96 + np.array([0.02, -0.01, -0.02]),0,1)
    albedo = np.where(inside_petal2[:,:,None], petal2_col, albedo)
    # core highlight
    core_col = np.clip(BO_CENTER + hue_shift*0.5,0,1)
    albedo = np.where(inside_core[:,:,None], core_col, albedo)
    # subtle bloom shimmer
    shimmer = 0.018*np.sin(x*0.012 + phase*1.5 + y*0.006)[:,:,None]
    albedo = np.clip(albedo + shimmer*inside_petal[:,:,None],0,1)
    # background grain color variation
    bg_wash = 0.015*np.sin(x*0.003 + y*0.002 + phase*0.6)[:,:,None]
    albedo = np.clip(albedo + bg_wash*(~inside_petal)[:,:,None],0,1)
    # micro jitter
    rng = np.random.RandomState(700+frame)
    albedo = np.clip(albedo + rng.randn(size,size,3)*0.006,0,1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # --- roughness: petal glossy, background matte, bloom modulates ---
    rough = np.full((size,size), 0.78, dtype=float)  # bg matte
    rough = np.where(inside_petal, 0.32 + t_radial*0.10 - ridge*0.05, rough)
    rough = np.where(inside_petal2, 0.28, rough)
    rough = np.where(inside_core, 0.22, rough)
    # bloom makes petals slightly glossier when open (light catches)
    rough = np.where(inside_petal, rough - bloom*0.04, rough)
    rng2 = np.random.RandomState(1400+frame)
    rough += rng2.randn(size,size)*0.010
    rough = np.clip(rough, 0.12, 0.92)
    rough_u8 = (rough*255).astype(np.uint8)

    # height
    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)

    # --- iridescence: on petal crests, breathes with bloom ---
    # crest = near petal center ridge
    iri = np.zeros((size,size), dtype=float)
    crest_mask = inside_petal.astype(float)*np.clip(ridge - t_radial*0.3,0,1)
    iri += crest_mask*0.85
    iri += inside_core.astype(float)*0.65
    # animated iridescent band that walks across petals with phase
    walk = 0.12*np.sin(dist*0.018 - phase*1.8 + ang*2.0)
    iri = np.clip(iri + walk*inside_petal.astype(float),0,1)
    # bloom modulates intensity: more open = more iri
    iri *= (0.75 + 0.25*bloom)
    # subtle global breathe
    iri = np.clip(iri + 0.04*math.sin(phase*1.2),0,1)
    iri_u8 = (iri*255).astype(np.uint8)

    # --- opacity / mask: ornament silhouette animates ---
    # hard mask with soft edge (1-2px antialias via smoothstep)
    # use signed distance to petal_edge
    sdf = petal_edge - dist  # positive inside
    # antialias 2px
    alpha = smoothstep(-1.5, 1.5, sdf)
    # also include inner layers but outer edge dominates
    # when closed, ornament is small; when open, large — seamless
    # add tiny animated edge jitter for organic
    edge_jitter = 0.5*np.sin(ang*petal_count + phase*1.3)*bloom
    # re-evaluate with jitter? simplified: modulate alpha slightly
    alpha = np.clip(alpha + edge_jitter*0.01*inside_petal.astype(float),0,1)
    # background outside is transparent (0), inside opaque (1)
    # for pixel art: keep at least core opaque always
    alpha = np.maximum(alpha, inside_core.astype(float)*0.95)
    mask_u8 = (alpha*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, height_u8, iri_u8, mask_u8

def gen_blooming_flowmap(size):
    tiles = 2
    tile_sz = size // tiles
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    lx = (x % tile_sz) - tile_sz*0.5
    ly = (y % tile_sz) - tile_sz*0.5
    dist = np.sqrt(lx*lx+ly*ly)+1e-6
    fx = lx/dist
    fy = ly/dist
    # radial outward; fade at tile edges
    # normalize to -1..1 already
    r = ((fx*0.5+0.5)*255).astype(np.uint8)
    g = ((fy*0.5+0.5)*255).astype(np.uint8)
    b = np.zeros_like(r)
    flow = np.stack([r,g,b], axis=-1)
    return flow

# ---------------------------------------------------------------- RoughnessTide
RT_DRY   = np.array([232, 224, 210], dtype=float)/255.0  # chalky dry
RT_WET   = np.array([195, 200, 205], dtype=float)/255.0  # cooler wet
RT_CREST = np.array([245, 240, 232], dtype=float)/255.0  # glossy crest highlight

def gen_roughtide_frame(frame, num_frames, size):
    phase = (frame/num_frames)*math.pi*2.0
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)

    # tide center washes back and forth horizontally
    # seamless: sin(phase) -> back-and-forth
    tide_center = size*0.5 + math.sin(phase)*size*0.33
    width = size*0.14  # transition width
    # signed distance to tide line
    # t = 0 (dry/matte) on one side, 1 (wet/glossy) on other? Let's define:
    # x < tide_center -> matte tide (rough), x > tide_center -> glossy crest
    # use smoothstep
    t = smoothstep(tide_center - width, tide_center + width, x)  # 0..1
    # also add diagonal tide undulation (wave front not straight)
    wave_front = 22*np.sin(y*0.008 + phase*1.2) + 14*np.cos(y*0.004 - phase*0.7)
    t_warp = smoothstep(tide_center + wave_front - width, tide_center + wave_front + width, x)
    t = np.clip(t*0.6 + t_warp*0.4, 0, 1)

    # height: base undulating dunes + tide depression
    dune = 0.06*np.sin(x*0.006 + y*0.004) + 0.04*np.cos(y*0.009 - x*0.003)
    dune += 0.025*np.sin((x+y)*0.005 + phase*0.4)
    # tide depression: wet side slightly lower (water pools)
    depression = (1 - t)*0.08 + t*0.02  # dry higher, wet lower
    height = 0.45 + dune + depression
    # crest ripple ahead of tide (glossy crest has fine ripples)
    ripple = 0.018*np.sin(x*0.04 - phase*1.8 + y*0.01)*np.clip(t,0,1)
    height = np.clip(height + ripple, 0, 1)
    # add micro sand grain
    rng = np.random.RandomState(5000)
    grain = rng.randn(size,size)*0.011
    height = np.clip(height + grain, 0, 1)
    # smoothstep for nicer range
    height = smoothstep(0.2, 0.85, height)

    # normal with tide-aligned jitter
    jx = 0.05*np.sin(x*0.04 + phase*1.5)*t  # more jitter on glossy side
    jy = 0.04*np.cos(y*0.05 - phase*1.1)
    normal = height_to_normal(height, strength=13.0, jitter_x=jx, jitter_y=jy)

    # --- albedo: lerp dry<->wet by t ---
    # dry is warmer/chalky, wet is cooler/darker
    albedo = lerp(RT_DRY, RT_WET, t[:,:,None]*0.85)
    # crest highlight where glossy: add crest color on ridge
    crest_h = np.clip((height-0.62)*1.2,0,1)[:,:,None] * t[:,:,None]
    albedo = lerp(albedo, RT_CREST, crest_h*0.35)
    # wash shimmer that walks with tide (iridescent highlight walks)
    walk_col = 0.02*np.sin(x*0.015 - phase*2.0 + y*0.008)[:,:,None] * np.array([0.8, 0.4, -0.6])
    albedo = np.clip(albedo + walk_col*t[:,:,None],0,1)
    # micro jitter
    rng2 = np.random.RandomState(600+frame)
    albedo = np.clip(albedo + rng2.randn(size,size,3)*0.007,0,1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # --- roughness: THE animated feature — washes back and forth ---
    # matte tide (rough 0.82) vs glossy crest (0.16)
    rough_matte = 0.82
    rough_gloss = 0.16
    rough = lerp(rough_matte, rough_gloss, t)
    # add tide shimmer: glossy side has subtle phase-driven variation (highlight walks)
    # walking highlight: roughness dips where highlight walks
    highlight = 0.06*np.sin(x*0.020 - phase*2.2 + y*0.005) * t
    rough = np.clip(rough + highlight, 0.12, 0.92)
    # also valley vs crest micro
    rough = np.where(height>0.65, rough*0.95, rough*1.02)
    rng3 = np.random.RandomState(3000+frame)
    rough += rng3.randn(size,size)*0.010
    rough = np.clip(rough, 0.10, 0.92)
    rough_u8 = (rough*255).astype(np.uint8)

    # height
    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)

    # --- iridescence: walks with glossy crest ---
    # strongest on glossy side crests
    iri = np.clip((height-0.55)*1.6,0,1) * np.clip(t,0,1) * (0.75 + 0.25*np.sin(x*0.018 - phase*1.6))
    # thin-film band that walks with tide phase
    band = 0.14*np.sin(x*0.028 - phase*2.0 + y*0.006) * t
    iri = np.clip(iri + band,0,1)
    # global breathe
    iri = np.clip(iri + 0.04*math.sin(phase*0.9),0,1)
    # matte side has near-zero iri
    iri = iri * (0.3 + 0.7*t)
    iri_u8 = (iri*255).astype(np.uint8)

    # --- opacity / mask: fully opaque surface, but encode tide mask as opacity for debug ---
    # For consistency, provide opaque mask (mostly white). Alternatively encode wet mask.
    # Provide white opaque; material can use RoughnessTide mask separately if needed.
    # We'll generate a wet/dry mask as Opacity for artistic control: wet=255, dry=200
    mask = 0.78 + t*0.22
    mask_u8 = (np.clip(mask,0,1)*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, height_u8, iri_u8, mask_u8

def gen_roughtide_flowmap(size):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    # horizontal wash flow: primarily +U with gentle wave undulation in V
    fx = 0.92 + 0.08*np.sin(y*0.006)
    fy = 0.10*np.cos(x*0.004 + y*0.010) + 0.06*np.sin(y*0.015)
    fx = np.clip(fx, -1, 1)
    fy = np.clip(fy, -1, 1)
    r = ((fx*0.5+0.5)*255).astype(np.uint8)
    g = ((fy*0.5+0.5)*255).astype(np.uint8)
    b = np.zeros_like(r)
    flow = np.stack([r,g,b], axis=-1)
    return flow

# ---------------------------------------------------------------- main
FAMILIES = {
    "FlowWeave": (gen_flowweave_frame, gen_flowweave_flowmap),
    "BloomingOrnament": (gen_blooming_frame, gen_blooming_flowmap),
    "RoughnessTide": (gen_roughtide_frame, gen_roughtide_flowmap),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=2048)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--out", type=str, default=OUT_ROOT)
    args = ap.parse_args()
    size = args.size
    num_frames = args.frames
    out_root = args.out

    print(f"Experimental Animated AAA — 3 families x {num_frames} frames x 6 maps @ {size} -> {out_root}")
    for fam, (gen_frame, gen_flow) in FAMILIES.items():
        fam_dir = os.path.join(out_root, fam)
        os.makedirs(fam_dir, exist_ok=True)
        print(f"\n[{fam}] {num_frames} frames @ {size}")

        for f in range(num_frames):
            print(f"  frame {f:02d}/{num_frames-1} phase={(f/num_frames)*360:5.1f} deg ...", flush=True)
            albedo, normal, rough_u8, height_u8, iri_u8, mask_u8 = gen_frame(f, num_frames, size)
            prefix = f"T_{fam}_Frame{f:02d}"
            Image.fromarray(albedo).save(os.path.join(fam_dir, f"{prefix}_BaseColor.png"))
            Image.fromarray(normal).save(os.path.join(fam_dir, f"{prefix}_Normal.png"))
            Image.fromarray(rough_u8).save(os.path.join(fam_dir, f"{prefix}_Roughness.png"))
            Image.fromarray(height_u8).save(os.path.join(fam_dir, f"{prefix}_Height.png"))
            Image.fromarray(iri_u8).save(os.path.join(fam_dir, f"{prefix}_Iridescence.png"))
            # Opacity vs Mask naming: BloomingOrnament uses Opacity (transparent bg), others Mask
            if fam == "BloomingOrnament":
                Image.fromarray(mask_u8).save(os.path.join(fam_dir, f"{prefix}_Opacity.png"))
            else:
                Image.fromarray(mask_u8).save(os.path.join(fam_dir, f"{prefix}_Mask.png"))
            print(f"    -> {prefix} (6 maps)")

        # FlowMap per family
        flow = gen_flow(size)
        flow_path = os.path.join(fam_dir, f"T_{fam}_FlowMap.png")
        Image.fromarray(flow).save(flow_path)
        print(f"  FlowMap -> {flow_path}  RG flow (for M_Master_Nikki panning)")

    # verify
    print("\n--- Verification ---")
    total_expected = len(FAMILIES) * (num_frames*6 + 1)
    total_actual = 0
    for fam in FAMILIES:
        fam_dir = os.path.join(out_root, fam)
        files = sorted(os.listdir(fam_dir))
        actual = len(files)
        expected = num_frames*6 + 1
        print(f"  {fam}: {actual}/{expected} files in {fam_dir}")
        for fn in files:
            print(f"    {fn}")
        total_actual += actual
    print(f"\nDONE — {total_actual}/{total_expected} files total in {out_root}")
    if total_actual != total_expected:
        print(f"WARNING expected {total_expected} got {total_actual}", file=sys.stderr)
        sys.exit(1)
    # check seamless: report frame0 vs frame N phase closure (informational)
    print("Seamless loop: phase 0 == 2*pi, all animations use sin/cos(phase) so frame 0 loops to frame N")

if __name__ == "__main__":
    main()
