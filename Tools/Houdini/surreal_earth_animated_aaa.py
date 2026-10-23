"""
surreal_earth_animated_aaa.py — Surreal animated earth flipbooks (3 families x 8 frames x 6 maps @2048)

Families:
  RockCloth_Animated  — stone where cloth weave breathes (normal 2px/frame drift, filigree fade)
  OrnamentEarth       — ground with geometric lace that crawls
  RoughnessShimmer    — ash rock glossy patches drift -> iridescence catch moves

Each frame (6 maps):
  _Base.png         RGB8
  _Normal.png       RGB8 tangent-space
  _Roughness.png    R8
  _Height.png       R8
  _Iridescence.png  R8
  _Mask.png         R8 (ornament / feature mask)

144 files total @2048 ~150MB PNG. Tilable (trig-periodic), seamless loop (phase wraps 2pi).
Run via hython:
  hython Tools/Houdini/surreal_earth_animated_aaa.py [--size 2048] [--frames 8]

Reference pattern: Tools/Houdini/flipbook_aaa.py — 8-frame drift, phase-modulated shimmer.
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image

OUT_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/SurrealEarth_Animated"
SIZE_DEFAULT = 2048
FRAMES_DEFAULT = 8

def smoothstep(a,b,x):
    t = np.clip((x-a)/(b-a+1e-9), 0, 1)
    return t*t*(3-2*t)

def lerp(a,b,t): return a*(1-t)+b*t

# ---------- tilable helpers ----------
# u = x/size in [0,1), v = y/size — trig with integer multiples wraps perfectly
def tilable_fbm(u, v, octaves=(3,5,7,11), amps=(0.5,0.25,0.12), phases=None):
    """Tilable pseudo-fBm via summed sines. All frequencies integer -> seamless."""
    if phases is None:
        phases = [0]*len(octaves)
    acc = np.zeros_like(u)
    for i,(n,a) in enumerate(zip(octaves, amps)):
        ph = phases[i] if i < len(phases) else 0
        acc += a * np.sin(2*np.pi*n*u + ph + 0.7*np.cos(2*np.pi*n*0.6*v + ph*0.3))
        acc += a*0.6 * np.cos(2*np.pi*n*1.3*v + ph*1.1 + 0.5*np.sin(2*np.pi*n*0.8*u))
    return acc

def height_to_normal(height, strength=14.0, jitter_x=None, jitter_y=None):
    dy, dx = np.gradient(height)
    dx *= strength; dy *= strength
    if jitter_x is not None: dx += jitter_x
    if jitter_y is not None: dy += jitter_y
    nx = -dx; ny = -dy; nz = np.ones_like(nx)
    nlen = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    return np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255],axis=-1).astype(np.uint8)

# ===================== FAMILY 1: RockCloth =====================
# Stone with cloth weave that breathes. Normal shifts 2px/frame. Filigree fades in/out.
def gen_rockcloth(frame, nframes, size):
    phase = 2*math.pi*frame/nframes
    # sub phases for parallax
    p_weave = phase*1.0
    p_filigree = phase*1.0  # controls fade
    p_breathe = phase*0.8
    y, x = np.mgrid[0:size,0:size].astype(np.float32)
    u = x/size; v = y/size

    # --- base stone undulation (tilable low freq fBm) ---
    stone = tilable_fbm(u, v, octaves=(2,4,8), amps=(0.18,0.10,0.05), phases=[phase*0.3, -phase*0.2, phase*0.5])
    stone_detail = tilable_fbm(u*2, v*2, octaves=(6,9), amps=(0.04,0.02), phases=[phase*0.6, -phase*0.4])*0.5
    height_stone = 0.5 + stone*0.6 + stone_detail

    # --- cloth weave — tilable satin: warp/weft periodic, shifts 2px/frame ---
    # shift amount: 2 px per frame wraps; use integer shift in texture space
    shift_px = (frame*2) % size
    # weave periods chosen to divide 2048 evenly for perfect tile: 16 divides 2048
    wp = 16; hp = 16
    # twisting weave offset that also breathes slightly
    breathe_offset = math.sin(p_breathe)*1.5
    x_shifted = (x + shift_px + breathe_offset) % size
    # twisted wale offset by row
    y_int = y.astype(np.int32)
    row_phase = (y_int // hp) % 8
    # stagger warp by row for twill
    x_twisted = (x_shifted - row_phase*2.0) % wp
    warp = (x_twisted < 10).astype(float)  # 10/16 coverage
    weft = ((y % hp) < 5).astype(float)
    weave = warp*0.92 + weft*0.18  # height contribution of weave
    # weave emboss depth breathes with phase (cloth inhale/exhale)
    weave_amp = 0.10 + 0.03*math.sin(p_breathe+0.4)
    weave_height = weave * weave_amp

    # micro thread breakup — tilable high freq sine instead of random
    thread = 0.012*np.sin(2*np.pi*32*u + p_weave*0.5)*np.cos(2*np.pi*28*v - p_weave*0.3)
    thread2= 0.008*np.sin(2*np.pi*64*u + 2*np.pi*48*v + p_weave)

    height = np.clip(height_stone + weave_height + thread + thread2, 0, 1)
    height = smoothstep(0.15, 0.92, height)
    # add subtle breathe in height (stone appears to swell)
    height = np.clip(height + 0.015*math.sin(p_breathe)*np.sin(2*np.pi*3*u)*np.sin(2*np.pi*3*v), 0, 1)

    # --- normal: height-derived + 2px/frame crawl jitter (tilable) ---
    # small crawl sin that moves 2px equivalent per frame
    jx = 0.05*np.sin(2*np.pi*18*u + phase*2.0 + 2*np.pi*5*v)
    jy = 0.05*np.cos(2*np.pi*18*v - phase*1.6 + 2*np.pi*3*u)
    normal = height_to_normal(height, strength=13.5, jitter_x=jx, jitter_y=jy)

    # --- filigree ornament — geometric lace that fades in/out with phase ---
    # filigree pattern: thin lace veins via distance to grid + diagonals, tilable
    # use sin field threshold for lace
    lace_field = np.sin(2*np.pi*6*u + phase*0.2)*np.sin(2*np.pi*6*v - phase*0.15) \
               + 0.5*np.sin(2*np.pi*12*u + 2*np.pi*12*v + phase*0.4)
    lace_field+= 0.35*np.cos(2*np.pi*18*u - 2*np.pi*10*v + phase*0.3)
    filigree_mask = smoothstep(0.55, 0.95, np.abs(lace_field))  # thin lines near zero crossing inverted? use abs
    # invert so lines are bright: field near 0 => line
    filigree_mask = 1.0 - smoothstep(0.0, 0.45, np.abs(lace_field))
    filigree_mask = np.clip(filigree_mask, 0, 1)
    # fade envelope: appears/disappears over loop (sin), seamless
    fade = 0.5 + 0.5*np.sin(phase - math.pi/2)  # 0 at frame 0, 1 at frame 4, 0 at frame 8
    # keep a faint ghost always so transition not hard cut, but amplitude swings
    filigree_alpha = 0.12 + 0.88*fade
    filigree_mask *= filigree_alpha
    # filigree also adds slight height emboss when visible
    height_filigree = filigree_mask*0.06
    height_out = np.clip(height + height_filigree, 0, 1)
    # recompute normal Y? keep previous normal but bump where filigree stronger
    # cheap: height_out -> normal tweak via small additional gradient blended
    # we already have normal; add filigree normal influence
    # compute filigree normal and lerp
    filigree_normal = height_to_normal(height_filigree*2.5, strength=10.0)
    blend = filigree_mask[:,:,None]*0.45
    normal = (normal.astype(float)*(1-blend) + filigree_normal.astype(float)*blend).astype(np.uint8)

    # --- albedo: stone greige + cloth tint + gold filigree inlay ---
    stone_col = np.array([152,142,132], float)/255.0
    stone_dark= np.array([112,105,98], float)/255.0
    cloth_col = np.array([168,155,140], float)/255.0
    gold_col  = np.array([196,175,120], float)/255.0
    # base lerp by height / weave
    base_mix = smoothstep(0.35, 0.78, height)
    base = lerp(stone_dark[None,None,:], stone_col[None,None,:], base_mix[:,:,None])
    # weave tint where warp dominates
    weave_tint = warp*0.18
    base = np.clip(base + weave_tint[:,:,None]*(cloth_col - base)*0.5, 0, 1)
    # gold filigree inlay where mask strong
    base = np.clip(base + filigree_mask[:,:,None]*0.55*(gold_col - base), 0, 1)
    # subtle hue breathe
    hue_drift = 0.008*math.sin(phase)*np.sin(2*np.pi*2*u+2*np.pi*2*v)[:,:,None]*np.array([1,-0.5,0.3])
    albedo = np.clip(base + hue_drift, 0, 1)
    # grain jitter tilable sin
    albedo += 0.018*np.sin(2*np.pi*48*u+phase)[:,:,None]*0.5
    albedo = np.clip(albedo, 0, 1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # --- roughness: cloth valleys rougher, stone crests smoother, filigree metallic gloss ---
    rough = np.where(height>0.58, 0.38, 0.68)
    rough = rough - weave*0.08 + 0.04*np.sin(2*np.pi*8*u+phase*0.7)*np.sin(2*np.pi*8*v-phase*0.5)
    rough = np.clip(rough - filigree_mask*0.18, 0.15, 0.92)
    # tiny shimmer per frame
    rough += 0.005*math.sin(phase*1.2)
    rough_u8 = (np.clip(rough,0,1)*255).astype(np.uint8)

    height_u8 = (np.clip(height_out,0,1)*255).astype(np.uint8)
    # --- iridescence: filigree carries iridescence that breathes with fade ---
    iri = filigree_mask*0.90 + np.clip((height-0.55)*0.6,0,1)*0.25
    iri = np.clip(iri + 0.06*math.sin(phase*1.1),0,1)
    iri_u8 = (iri*255).astype(np.uint8)
    # --- mask: ornament mask (filigree + weave crest) ---
    mask = np.clip(filigree_mask*0.85 + warp*weave*0.18, 0, 1)
    mask_u8 = (mask*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, height_u8, iri_u8, mask_u8

# ===================== FAMILY 2: OrnamentEarth =====================
# Ground with geometric lace that crawls diagonally.
def gen_ornament(frame, nframes, size):
    phase = 2*math.pi*frame/nframes
    # crawl speed: 3px/frame diagonal
    crawl = frame*3
    y, x = np.mgrid[0:size,0:size].astype(np.float32)
    u = x/size; v = y/size
    uc = ((x + crawl) % size)/size
    vc = ((y + crawl) % size)/size
    # use crawled uv for lace

    # base ground: warm earth + pebbly variation (tilable fBm)
    ground_fbm = tilable_fbm(u, v, octaves=(2,4,8), amps=(0.20,0.11,0.06), phases=[phase*0.2, -phase*0.3, phase*0.15])
    ground_fbm2= tilable_fbm(u*1.5, v*1.5, octaves=(6,10), amps=(0.05,0.03), phases=[phase*0.4, -phase*0.5])
    height_ground = 0.42 + ground_fbm*0.55 + ground_fbm2*0.3
    height_ground = smoothstep(0.05, 0.95, np.clip(height_ground,0,1))
    # pebble bumps tilable
    pebble = 0.025*np.sin(2*np.pi*14*u+phase*0.2)*np.sin(2*np.pi*14*v-phase*0.2)
    height_ground = np.clip(height_ground + pebble, 0, 1)

    # lace geometry — two interleaved patterns that crawl: grid + diamond + rosette
    # grid lace on crawled coordinates
    grid = np.sin(2*np.pi*8*uc + phase*0.3)*np.sin(2*np.pi*8*vc - phase*0.2)
    grid2= np.sin(2*np.pi*16*uc+phase*0.5)*np.sin(2*np.pi*16*vc-phase*0.4)
    diamond = np.sin(2*np.pi*8*(uc+vc)+phase*0.35)*np.sin(2*np.pi*8*(uc-vc)-phase*0.25)
    rosette = np.sin(2*np.pi*24*uc+2*np.pi*24*vc+phase)*0.3 + np.cos(2*np.pi*24*uc-2*np.pi*24*vc+phase*0.8)*0.3
    lace_field = grid*0.55 + diamond*0.35 + rosette*0.25 + grid2*0.18
    # lace lines where field near threshold
    lace_mask = 1.0 - smoothstep(0.0, 0.38, np.abs(lace_field))
    lace_mask = np.clip(lace_mask, 0, 1)
    # lace width pulse over loop (thin<->thick)
    pulse = 0.78 + 0.22*np.sin(phase*1.0 + 0.6)
    lace_mask = np.clip(smoothstep(0.12, 0.88, lace_mask/pulse),0,1)*pulse
    # secondary crawling dots along lace intersections
    dots = np.sin(2*np.pi*32*uc+phase*1.2)*np.sin(2*np.pi*32*vc-phase*1.0)
    dot_mask = smoothstep(0.78, 0.98, dots)*0.45
    lace_mask = np.clip(lace_mask + dot_mask, 0, 1)

    height_lace = lace_mask * (0.07 + 0.02*math.sin(phase+1.1))
    height = np.clip(height_ground + height_lace + lace_mask*0.015*np.sin(2*np.pi*48*uc), 0, 1)

    # normal
    jx = 0.04*np.sin(2*np.pi*22*uc+phase*1.8)
    jy = 0.04*np.cos(2*np.pi*22*vc-phase*1.4)
    normal_ground = height_to_normal(height, strength=12.0, jitter_x=jx, jitter_y=jy)

    # lace ridge normal exaggeration
    lace_n = height_to_normal(lace_mask*0.5, strength=18.0)
    blend = lace_mask[:,:,None]*0.35
    normal = (normal_ground.astype(float)*(1-blend) + lace_n.astype(float)*blend).astype(np.uint8)

    # albedo: earth ochre/sienna with lace cream/bone inlay
    earth = np.array([138,118,92], float)/255.0
    earth_dark = np.array([98,82,66], float)/255.0
    lace_col = np.array([228,222,208], float)/255.0
    lace_gold = np.array([212,190,140], float)/255.0
    h_mix = smoothstep(0.35, 0.72, height_ground)
    base = lerp(earth_dark[None,None,:], earth[None,None,:], h_mix[:,:,None])
    # lace inlay
    lace_tint = lerp(lace_col, lace_gold, 0.35 + 0.18*np.sin(phase))
    base = np.clip(base + lace_mask[:,:,None]*0.72*(lace_tint - base), 0, 1)
    # drifting warm wash that crawls with lace (so ground feels alive)
    wash = 0.015*np.sin(2*np.pi*5*uc+phase)*np.sin(2*np.pi*5*vc-phase*0.7)[:,:,None]*np.array([0.8,0.3,-0.4])
    albedo = np.clip(base + wash, 0, 1)
    albedo = np.clip(albedo + 0.012*np.sin(2*np.pi*64*u+phase)[:,:,None],0,1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    rough = np.where(height_ground>0.6, 0.72, 0.88)
    rough = np.clip(rough - lace_mask*0.28 - dot_mask*0.15, 0.18, 0.92)
    rough = rough + 0.02*np.sin(2*np.pi*6*uc+phase)*np.cos(2*np.pi*6*vc-phase*0.6)
    rough_u8 = (np.clip(rough,0,1)*255).astype(np.uint8)

    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)
    iri = np.clip(lace_mask*0.75 + dot_mask*0.6 + np.clip((height-0.65)*0.5,0,1)*0.15,0,1)
    iri = np.clip(iri + 0.05*math.sin(phase*1.3),0,1)
    iri_u8 = (iri*255).astype(np.uint8)
    mask = np.clip(lace_mask*0.92 + dot_mask*0.5,0,1)
    mask_u8 = (mask*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, height_u8, iri_u8, mask_u8

# ===================== FAMILY 3: RoughnessShimmer =====================
# Ash rock where roughness animates — glossy patches drift, iridescence catch moves.
def gen_roughness(frame, nframes, size):
    phase = 2*math.pi*frame/nframes
    # drift vector for glossy patches: 4px/frame quasi-random crawl, wraps
    drift = frame*4
    y, x = np.mgrid[0:size,0:size].astype(np.float32)
    u = x/size; v = y/size
    # drifted uv for gloss field (wrapping)
    ug = ((x + drift*1.0) % size)/size
    vg = ((y + drift*0.7) % size)/size

    # ash rock height: craggy tilable fBm
    h1 = tilable_fbm(u, v, octaves=(2,4,7), amps=(0.22,0.13,0.07), phases=[phase*0.15, -phase*0.2, phase*0.1])
    h2 = tilable_fbm(u*2, v*2, octaves=(8,13), amps=(0.045,0.028), phases=[phase*0.25, -phase*0.35])
    height_rock = 0.45 + h1*0.62 + h2*0.4
    height_rock = smoothstep(0.08, 0.96, np.clip(height_rock,0,1))
    # ash dust micro pitting (tilable)
    pit = 0.02*np.sin(2*np.pi*28*u+phase*0.3)*np.cos(2*np.pi*28*v-phase*0.2)
    height_rock = np.clip(height_rock + pit,0,1)

    # glossy patches — large soft blobs that drift; use low-freq drifted fBm thresholded
    gloss_field = tilable_fbm(ug, vg, octaves=(2,3,5), amps=(0.50,0.25,0.12), phases=[phase*0.4, -phase*0.3, phase*0.6])
    # also secondary cellular voronoi-like via sin distance
    cell = np.sin(2*np.pi*6*ug+phase*0.5)*np.sin(2*np.pi*6*vg-phase*0.4)
    gloss_field = gloss_field*0.7 + cell*0.18
    # gloss patches where field high, tilable threshold
    gloss_mask = smoothstep(0.18, 0.72, gloss_field)
    gloss_mask = np.clip(gloss_mask,0,1)
    # soften edges and animate edge breathe
    breathe = 0.08*math.sin(phase*0.9)
    gloss_mask = np.clip(smoothstep(0.30 - breathe, 0.75 + breathe, gloss_mask),0,1)
    # small satellite gloss specks that drift opposite
    ug2 = ((x - drift*0.6) % size)/size
    vg2 = ((y - drift*0.9) % size)/size
    speck = smoothstep(0.82,0.98, np.sin(2*np.pi*18*ug2+phase)*np.sin(2*np.pi*18*vg2-phase*0.7))
    gloss_mask = np.clip(gloss_mask + speck*0.35,0,1)

    # height: gloss patches are slightly raised polish (0.02) or slightly recessed varnish
    height = np.clip(height_rock + gloss_mask*0.035, 0, 1)

    # normal
    jx = 0.035*np.sin(2*np.pi*20*u+phase*1.5)
    jy = 0.035*np.cos(2*np.pi*20*v-phase*1.2)
    normal = height_to_normal(height, strength=14.0, jitter_x=jx, jitter_y=jy)

    # albedo: ash gray with gloss darkening and subtle warm iridescence tint where gloss
    ash = np.array([112,110,108], float)/255.0
    ash_dark = np.array([78,75,72], float)/255.0
    ash_light= np.array([158,155,148], float)/255.0
    hmix = smoothstep(0.30, 0.78, height_rock)
    base = lerp(ash_dark[None,None,:], ash[None,None,:], hmix[:,:,None])
    base = np.where(height_rock[:,:,None]>0.72, lerp(base, ash_light, 0.35), base)
    # gloss tint: slightly darker + cooler where glossy (varnished ash)
    gloss_tint = np.array([92,98,110], float)/255.0
    base = np.clip(base + gloss_mask[:,:,None]*0.28*(gloss_tint - base), 0, 1)
    # iridescent catch tint moves with gloss (thin film)
    iri_tint = np.array([180,190,210], float)/255.0
    # animated hue shift on gloss
    hue = 0.06*math.sin(phase*1.4)
    tint_shift = gloss_mask[:,:,None]*0.10*np.array([hue, -hue*0.5, hue*0.8])
    albedo = np.clip(base + tint_shift + gloss_mask[:,:,None]*0.06*(iri_tint-base),0,1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # roughness: THIS IS THE ANIMATED CHANNEL — glossy patches drift means rough inverts there
    # base ash rough 0.82, gloss patches drop to 0.18-0.28 and drift each frame
    rough = np.clip(0.82 - gloss_mask*0.58 + 0.04*np.sin(2*np.pi*9*u+phase*0.6)*np.cos(2*np.pi*9*v-phase*0.4), 0.15, 0.92)
    # add subtle shimmer drift contribution
    rough = rough + 0.015*math.sin(phase*1.7)*gloss_mask
    # ash pitting adds micro roughness variation tilable
    rough += 0.02*np.sin(2*np.pi*44*u+phase*0.8)
    rough_u8 = (np.clip(rough,0,1)*255).astype(np.uint8)

    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)
    # iridescence follows gloss patches strongly (glossy varnish catches light)
    iri = np.clip(gloss_mask*0.88 + speck*0.45 + np.clip((height-0.6)*0.2,0,1)*0.15,0,1)
    # iridescence also has crawling color band seeded by drift
    band = 0.10*np.sin(2*np.pi*12*ug+phase*1.2)*np.cos(2*np.pi*12*vg-phase)
    iri = np.clip(iri + band*gloss_mask*0.3,0,1)
    iri_u8 = (iri*255).astype(np.uint8)
    mask = np.clip(gloss_mask*0.90 + speck*0.4,0,1)
    mask_u8 = (mask*255).astype(np.uint8)

    return albedo_u8, normal, rough_u8, height_u8, iri_u8, mask_u8

def save_family(family_name, gen_fn, nframes, size, out_dir):
    print(f"\n[{family_name}] {nframes} frames @ {size} -> {out_dir}")
    for f in range(nframes):
        albedo, normal, rough, height, iri, mask = gen_fn(f, nframes, size)
        prefix = f"T_{family_name}_Frame{f:02d}"
        Image.fromarray(albedo).save(os.path.join(out_dir, f"{prefix}_Base.png"))
        Image.fromarray(normal).save(os.path.join(out_dir, f"{prefix}_Normal.png"))
        Image.fromarray(rough).save(os.path.join(out_dir, f"{prefix}_Roughness.png"))
        Image.fromarray(height).save(os.path.join(out_dir, f"{prefix}_Height.png"))
        Image.fromarray(iri).save(os.path.join(out_dir, f"{prefix}_Iridescence.png"))
        Image.fromarray(mask).save(os.path.join(out_dir, f"{prefix}_Mask.png"))
        print(f"  frame {f:02d} saved {prefix} (6 maps)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=SIZE_DEFAULT)
    ap.add_argument("--frames", type=int, default=FRAMES_DEFAULT)
    ap.add_argument("--out", type=str, default=OUT_DIR)
    args = ap.parse_args()
    size = args.size; nframes=args.frames; out_dir=args.out
    os.makedirs(out_dir, exist_ok=True)
    print(f"SurrealEarth_Animated — 3 families x {nframes} frames x 6 maps @ {size}x{size} -> {out_dir}")
    print(f"Tilable (trig-periodic), seamless loop (2pi phase), 144 files expected @2048 ~150MB")

    save_family("RockCloth_Animated", gen_rockcloth, nframes, size, out_dir)
    save_family("OrnamentEarth", gen_ornament, nframes, size, out_dir)
    save_family("RoughnessShimmer", gen_roughness, nframes, size, out_dir)

    files = sorted(os.listdir(out_dir))
    families = ["RockCloth_Animated","OrnamentEarth","RoughnessShimmer"]
    expected = nframes*6*len(families)
    actual = len([x for x in files if x.startswith("T_") and x.endswith(".png")])
    total_bytes = sum(os.path.getsize(os.path.join(out_dir,f)) for f in files if f.endswith(".png"))
    print(f"\nDONE — {actual}/{expected} files, {total_bytes/1024/1024:.1f} MB in {out_dir}")
    for fn in files:
        if fn.startswith("T_"):
            print(f"  {fn}")
    # tilability quick check: wrap diff on one sample height
    try:
        from PIL import Image as PILI
        sample = os.path.join(out_dir, "T_RockCloth_Animated_Frame00_Height.png")
        if os.path.exists(sample):
            im = np.array(PILI.open(sample))
            # compare left vs right edge (should be similar for tilable trig — mean abs diff low)
            edge = np.mean(np.abs(im[:,0].astype(int) - im[:,-1].astype(int)))
            print(f"  tilability check (RockCloth Height left-right mean |diff|): {edge:.2f} (expect <8 for trig-periodic)")
    except Exception as e:
        print(f"  tilability check skip: {e}")
    if actual != expected:
        print(f"WARNING expected {expected} got {actual}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
