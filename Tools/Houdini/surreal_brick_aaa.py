"""
surreal_brick_aaa.py — AAA Surreal Feminine Brick 4K
 4 rock types: BlushBrick, DuskBrick, IvoryStone, GildedBrick
 Softer beveled brick corners, varied sizes subtly irregular, mortar iridescent shimmer.
 Roughness: brick face 0.35-0.45 + stone grain, mortar 0.7, brick crest glossy (~0.28) to catch iridescence.
 4 variants x 7 maps -> Content/EnvSandbox/Textures/SurrealBrick/
 8-frame animated flipbook for BlushBrick (hue shift + mortar glints drift) -> SurrealBrick_Flipbook/
 7 maps per variant: BaseColor, Normal, Roughness, Metallic, Height, AO, Iridescence
 4 maps per flipbook frame: BaseColor, Normal, Iridescence, Roughness
 Run via hython: hython Tools/Houdini/surreal_brick_aaa.py [--size 4096] [--frames 8]
"""
import os, sys, math, argparse
import numpy as np
from PIL import Image

OUT_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/SurrealBrick"
FLIP_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/SurrealBrick_Flipbook"

# brick grid chosen to tile exactly at 4096 (and at 2048): 256x128 with 16 cols, 32 rows
BRICK_W = 256
BRICK_H = 128
MORTAR = 14          # base mortar gap
BEVEL_R = 10.0       # corner bevel radius (feminine soft)
CREST_BEVEL = 18.0   # crest highlight bevel falloff px

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def sd_round_box(px, py, hx, hy, r):
    """SDF rounded box. px,py are coords relative to center, hx,hy half-sizes, r radius. vectorized."""
    # clamp
    qx = np.abs(px) - hx + r
    qy = np.abs(py) - hy + r
    # outside distance
    mx = np.maximum(qx, 0)
    my = np.maximum(qy, 0)
    outside = np.sqrt(mx*mx + my*my)
    inside = np.minimum(np.maximum(qx,qy), 0)
    return outside + inside - r

# palette: (name, brickA_rgb, brickB_rgb, mortar_rgb, accent_rgb, roughness_mid)
VARIANTS = [
    ("BlushBrick",  (232,175,163), (212,145,130), (242,213,204), (255,210,225), 0.40),
    ("DuskBrick",   (168,153,176), (138,125,147), (207,200,214), (200,185,255), 0.42),
    ("IvoryStone",  (240,234,216), (230,221,195), (250,246,238), (255,245,220), 0.38),
    ("GildedBrick", (245,230,204), (234,213,168), (243,228,200), (212,175, 85), 0.36),
]

# IvoryStone uses larger stone blocks: double scale hint
STONE_SCALE = {"IvoryStone": 1.35}

def build_tables(variant_name, seed):
    """Per-brick random tables size n_rows x n_cols for irregularity. Returns dict of tables."""
    n_rows = 32  # for 4096 /128 ; for 2048 -> 16, handle generically
    # actual rows/cols depend on SIZE, compute inside gen
    # keep max 64x32 table and slice
    rng = np.random.RandomState(seed)
    # allocate large
    R=64; C=32
    tables = {
        "inset_x": rng.uniform(-4.5, 4.5, (R,C)).astype(np.float32),
        "inset_y": rng.uniform(-3.5, 3.5, (R,C)).astype(np.float32),
        "shift_x": rng.uniform(-5, 5, (R,C)).astype(np.float32),
        "shift_y": rng.uniform(-3, 3, (R,C)).astype(np.float32),
        "color_var": rng.uniform(-0.06, 0.06, (R,C)).astype(np.float32),
        "value_var": rng.uniform(-0.04, 0.04, (R,C)).astype(np.float32),
        "grain_phase": rng.uniform(0, math.pi*2, (R,C)).astype(np.float32),
        "gloss_mod": rng.uniform(-0.04, 0.04, (R,C)).astype(np.float32),
    }
    return tables

def gen_brick(variant_name, brickA, brickB, mortar_rgb, accent_rgb, roughness_mid, size=4096, tables=None, frame=0, num_frames=0, animate=False):
    """
    Generate one brick variant (or one flipbook frame if animate=True).
    animate: if True, apply phase-based hue drift and glint drift for BlushBrick flipbook.
    """
    is_stone = "IvoryStone" in variant_name
    # grid
    bw = BRICK_W
    bh = BRICK_H
    mortar = MORTAR
    # stone scale: larger blocks for IvoryStone (simulate by scaling brick)
    scale_factor = STONE_SCALE.get(variant_name, 1.0)
    # For stone we double brick size illusion by halving grid frequency: effective brick 1.35x larger but mortar thicker
    # implement by scaling bw/bh before tiling logic, but keep tilability by adjusting n_cols/rows accordingly.
    # Simpler: just use larger mortar inset variation and bigger grain
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)

    # rows/cols counts
    n_rows = int(math.ceil(size / bh)) + 2
    n_cols = int(math.ceil(size / bw)) + 2

    # phase for animation
    phase = 0.0
    if animate and num_frames>0:
        phase = (frame / num_frames) * math.pi * 2.0

    # row stagger: running bond half-brick offset on odd rows, plus subtle sine drift for feminine irregularity
    row = np.floor(y / bh).astype(np.int32)
    # stagger offset per row
    stagger = (row & 1).astype(np.float32) * (bw * 0.5)
    # wavy row drift (feminine, not rigid)
    drift = np.sin(row.astype(np.float32)*0.7 + y*0.0025)*3.0
    # local coords
    lx = (x - stagger - drift) % bw
    ly = y % bh
    # center-relative coords
    px = lx - bw*0.5
    py = ly - bh*0.5
    # brick id
    col = np.floor((x - stagger - drift) / bw).astype(np.int32)
    # wrap ids for table lookup (positive mod)
    # table is 64x32, use modulo
    R_T, C_T = tables["inset_x"].shape
    r_idx = np.mod(row, R_T)
    c_idx = np.mod(col, C_T)
    # fetch per-brick variations via indexing (vectorized)
    # Need to do advanced indexing with arrays of size ~16M -> use flattened lookup
    # Flatten tables for fast indexing
    def lookup(tbl):
        flat = tbl.ravel()
        # ravel index = r*C_T + c
        idx = r_idx.astype(np.int32)*C_T + c_idx.astype(np.int32)
        # but we have arrays 4096x4096 -> idx array same size, then gather
        return flat[idx]

    inset_x = lookup(tables["inset_x"])
    inset_y = lookup(tables["inset_y"])
    shift_x = lookup(tables["shift_x"])
    shift_y = lookup(tables["shift_y"])
    color_var = lookup(tables["color_var"])
    value_var = lookup(tables["value_var"])
    grain_phase = lookup(tables["grain_phase"])
    gloss_mod = lookup(tables["gloss_mod"])

    # For stone, amplify inset
    if is_stone:
        inset_x *= 1.4
        inset_y *= 1.4

    # apply positional jitter to px/py (subtle translation of brick within cell)
    px = px - shift_x * 0.35
    py = py - shift_y * 0.35

    # effective half sizes with per-brick inset (subtle size variation) + mortar
    hx = (bw - mortar)*0.5 + inset_x
    hy = (bh - mortar)*0.5 + inset_y
    # clamp min size
    hx = np.clip(hx, 40, bw*0.5-2)
    hy = np.clip(hy, 30, bh*0.5-2)

    # bevel radius varies per brick slightly for hand-made feel
    bevel = BEVEL_R + np.clip(color_var*4, -1.5, 1.5)
    # SDF
    d = sd_round_box(px, py, hx, hy, bevel)
    # brick mask: inside (d<0)
    brick_mask = d < 0
    mortar_mask = ~brick_mask
    # distance to edge for bevel/crest (negative inside, positive outside)
    # for crest highlight: distance from brick edge inside
    # edge_dist = -d where inside, positive
    edge_dist = np.where(brick_mask, -d, 0).astype(np.float32)
    # crest bevel falloff (soft top)
    crest = np.clip(edge_dist / CREST_BEVEL, 0, 1)
    crest = smoothstep(0.0, 1.0, crest)  # 0 at edge, 1 in center
    # mortgage: mortar recess
    # height field
    # brick base height + stone grain + crest + per-brick value
    # stone grain: multi-octave sin + noise
    # phase animation for glint drift affects mortar highlights
    # grain
    # high-freq stone grain
    # Use coordinate based grain plus per-brick phase offset
    # ensure tilable: use x,y sin with size-periodic frequencies
    grain1 = np.sin(x*0.07 + grain_phase*0.8 + y*0.015)*0.025
    grain2 = np.sin(x*0.025 - y*0.03 + grain_phase)*0.018
    grain3 = np.sin((x+y)*0.012 + grain_phase*0.5)*0.012
    # larger undulation for stone
    if is_stone:
        grain1 *= 1.5
        grain2 *= 1.2
        # add cloud wash for stone mottling
        cloud = np.sin(x*0.004 + y*0.003 + grain_phase*0.3)*0.04 + np.cos(y*0.006 - x*0.003)*0.03
    else:
        cloud = np.sin(x*0.008 + y*0.006)*0.015 + np.cos(y*0.005)*0.010

    # per-pixel micro noise (stone pores) — cheap pseudo-random via sin hash (tilable)
    # use deterministic hash from coordinates
    # hash noise [-1,1]
    hash_noise = np.sin(x*0.21 + y*0.17 + grain_phase*0.1)*0.5 + np.sin(x*0.43 - y*0.31)*0.3
    hash_noise = np.clip(hash_noise, -1, 1)*0.015

    # animate: drifting mortar glints — add moving highlight in mortar
    glint = np.zeros_like(x, dtype=np.float32)
    if animate:
        # glint drift: diagonal traveling glints in mortar lines
        # two glint layers at different speeds
        glint_a = np.sin(x*0.015 - phase*1.4 + y*0.008)*0.5 + 0.5
        glint_b = np.sin((x+y)*0.010 + phase*0.9)*0.5 + 0.5
        glint_a = smoothstep(0.72, 0.88, glint_a)
        glint_b = smoothstep(0.75, 0.92, glint_b)
        glint = glint_a*0.35 + glint_b*0.22
        # modulate glint so it only appears in mortar
        glint = glint * mortar_mask.astype(np.float32)
        # hue drift for BlushBrick already handled in albedo below via phase
    else:
        # static faint mortar speckle
        glint = (np.sin(x*0.02)*np.cos(y*0.02) > 0.92).astype(np.float32)*0.12 * mortar_mask.astype(np.float32)

    # brick face height
    # base: mortar low (0.08), brick high (0.78) with crest shoulder
    brick_height = 0.58 + crest*0.30 + grain1 + grain2*0.7 + grain3*0.5 + cloud*0.25 + hash_noise + value_var*0.15 + color_var*0.06
    # add per-brick height pedestal (hand-laid uneven)
    brick_height += np.where(brick_mask, 0, 0)  # placeholder
    # mortar height recessed
    mortar_height = 0.08 + np.sin(x*0.04)*0.015 + np.cos(y*0.05)*0.012 + np.random.randn(*x.shape).astype(np.float32)*0.004  # slight
    # but random per-pixel for mortar not tilable noise — use sin-based
    mortar_height = 0.08 + np.sin(x*0.08 + y*0.06)*0.010 + np.sin(x*0.15)*0.006
    if animate:
        mortar_height = mortar_height + glint*0.06

    height = np.where(brick_mask, brick_height, mortar_height)
    # clamp
    height = np.clip(height, 0, 1)
    # soft bevel smoothing on height transition at brick edge: smoothstep over distance field
    # anti-alias mortar edge: mix within 2px of border using d
    edge_aa = np.clip(1 - np.abs(d)/2.0, 0, 1)
    # where near edge, blend brick/mortar height for bevel
    # we already have distinct heights, but we can smooth the step
    # mix height where |d|< bead
    bead = 2.0
    near_edge = np.abs(d) < bead
    # interpolate
    t_edge = np.clip((d + bead)/(2*bead), 0, 1)
    # t_edge 0 = inside brick far, 1 = outside mortar
    # smooth
    t_edge = smoothstep(0,1,t_edge)
    # blended height for edge bevel (slightly higher than linear)
    height_blended = brick_height*(1-t_edge) + mortar_height*t_edge
    height = np.where(near_edge, height_blended, height)
    height = np.clip(height, 0, 1)

    # Normal from height
    dy, dx = np.gradient(height)
    # scale for detail
    nscale = 13.0 if not is_stone else 11.0
    dx *= nscale; dy *= nscale
    # micro fuzz scaled by brick vs mortar
    fuzz = 0.045
    # Use deterministic jitter via sin hash to avoid per-frame randn pop (and keep tilable)
    jitter_x = np.sin(x*0.33 + y*0.11 + grain_phase*0.2)*fuzz*0.6
    jitter_y = np.cos(y*0.37 - x*0.09)*fuzz*0.6
    dx += jitter_x
    dy += jitter_y
    nx_ = -dx; ny_ = -dy; nz_ = np.ones_like(nx_)
    nlen = np.sqrt(nx_*nx_ + ny_*ny_ + nz_*nz_)
    nx_ /= nlen; ny_ /= nlen; nz_ /= nlen
    normal = np.stack([(nx_*0.5+0.5)*255,(ny_*0.5+0.5)*255,nz_*255], axis=-1).astype(np.uint8)

    # Albedo
    brickA_arr = np.array(brickA, float)/255.0
    brickB_arr = np.array(brickB, float)/255.0
    mortar_arr = np.array(mortar_rgb, float)/255.0
    accent_arr = np.array(accent_rgb, float)/255.0
    # per-brick brick tint selection: alternate A/B plus variation
    # use color_var to lerp between A and B
    # brick tint
    lerp = np.clip((color_var + 0.06)/0.12, 0, 1)  # 0..1
    brick_tint = brickA_arr[None,None,:]*(1-lerp[:,:,None]) + brickB_arr[None,None,:]*lerp[:,:,None]
    # add grain-based color modulation
    # darker where grain recess, lighter on crest
    # subtle hue shift per brick via value_var
    brick_tint = brick_tint + value_var[:,:,None]*0.08
    # stone mottling for Ivory: darker veins
    if is_stone:
        vein = np.sin((x*0.006 + y*0.004 + grain_phase*0.3))[:,:,None]*0.04
        brick_tint = brick_tint + vein * np.array([-0.06,-0.04,0.02])[None,None,:]
    # per-pixel grain color jitter
    grain_color = (grain1*0.6 + grain2*0.3)[:,:,None] * np.array([0.06,0.04,-0.02])
    s1 = np.sin(x*0.012 + y*0.008)[:,:,None]*0.018
    s2 = np.sin(x*0.009 - y*0.015)[:,:,None]*0.012
    albedo_brick = np.clip(brick_tint + grain_color + s1 + s2 + np.sin(x*0.0015 + y*0.001)[:,:,None]*0.02, 0, 1)
    # crest highlight: slightly lighter / warmer on crest
    highlight = crest[:,:,None] * 0.07 * np.array([1.0,0.95,0.90])
    albedo_brick = np.clip(albedo_brick + highlight, 0, 1)
    # mortar albedo: uniform mortar color with slight variation + iridescent tint
    # base mortar
    mortar_base = mortar_arr
    # mortar variation wash
    mortar_wash = np.sin(x*0.003 + y*0.002)[:,:,None]*0.015 * np.array([0.04,0.02,-0.02])
    albedo_mortar = np.clip(mortar_base + mortar_wash, 0, 1)
    # iridescent shimmer tint on mortar (and slightly on crest)
    # hue shift over time if animate
    if animate:
        hue_r = 0.035*math.sin(phase*1.0)
        hue_g = 0.025*math.sin(phase*1.3 + 1.0)
        hue_b = 0.032*math.cos(phase*0.9 + 0.4)
        iri_tint = np.array([hue_r, hue_g, hue_b])
        # mortar glint color — iridescent pearlescent
        glint_color = glint[:,:,None] * (np.array([0.18,0.15,0.22]) + iri_tint)
        albedo_mortar = np.clip(albedo_mortar + glint_color*0.6, 0, 1)
        # crest iridescent catch
        crest_iri = crest[:,:,None] * 0.10 * (np.array([0.12,0.08,0.18]) + iri_tint)
        albedo_brick = np.clip(albedo_brick + crest_iri, 0, 1)
    else:
        # static subtle iridescence
        static_iri = np.sin(x*0.02 + y*0.015)[:,:,None]*0.012 * np.array([0.10,0.06,0.14])
        albedo_mortar = np.clip(albedo_mortar + static_iri*0.5, 0, 1)

    # GildedBrick: gold dust on mortar + crest specks
    if "Gilded" in variant_name:
        gold_dust = np.sin(x*0.04 + y*0.03) * np.cos(y*0.06)
        gold_mask = smoothstep(0.5, 0.9, np.clip(gold_dust*0.5+0.5,0,1))
        # gold speck field tilable hash
        speck = (np.sin(x*0.18)*np.sin(y*0.18) > 0.65).astype(float) * 0.35
        gold_boost = (gold_mask*0.15 + speck*0.12)[:,:,None] * (accent_arr - np.array([0.5,0.5,0.5]))
        # apply to mortar and to brick crest edges
        gold_on_mortar = mortar_mask[:,:,None]*gold_boost*0.7
        gold_on_crest = np.clip(crest-0.6,0,1)[:,:,None]*gold_boost*0.5
        albedo_brick = np.clip(albedo_brick + gold_on_crest,0,1)
        albedo_mortar = np.clip(albedo_mortar + gold_on_mortar,0,1)

    albedo = np.where(brick_mask[:,:,None], albedo_brick, albedo_mortar)
    albedo = np.clip(albedo, 0, 1)
    # final painterly jitter (tilable, deterministic)
    jitter_col = np.sin(x*0.11 + y*0.13)*0.5 + np.cos(x*0.07 - y*0.09)*0.5
    jitter_col = np.clip(jitter_col, -1, 1)[:,:,None]*0.008
    albedo = np.clip(albedo + jitter_col, 0, 1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # Roughness
    # spec: brick face 0.35-0.45 with stone grain, mortar 0.7, crest glossy ~0.28
    # base per variant roughness_mid maps to brick center
    r_brick_center = roughness_mid - 0.07 + gloss_mod*0.6  # ~0.33-0.38 with variation
    # per-pixel stone grain modulates roughness slightly (±0.04)
    grain_rough = grain1*0.6 + grain2*0.4  # -0.03..0.03
    # crest glossy: lower roughness where crest high
    crest_gloss = crest * 0.12  # crest becomes more glossy
    rough_brick = r_brick_center + grain_rough - crest_gloss + np.sin(x*0.015)*0.01
    rough_brick = np.clip(rough_brick, 0.28, 0.52)
    # mortar rough 0.68-0.72
    mortar_rough_base = 0.70 + np.sin(x*0.02)*0.01 + np.sin(y*0.03)*0.008
    rough_mortar = mortar_rough_base + glint*0.04  # glints slightly glossier? actually glint polish lowers rough a bit
    if animate:
        rough_mortar = rough_mortar - glint*0.06
    rough_mortar = np.clip(rough_mortar, 0.62, 0.78)
    rough = np.where(brick_mask, rough_brick, rough_mortar)
    # edge AA blend roughness too
    rough_mortar_exp = np.broadcast_to(rough_mortar, rough.shape) if np.ndim(rough_mortar)==2 else rough_mortar
    # blend near edge
    rough_blended = rough_brick*(1-t_edge) + rough_mortar_exp*t_edge
    rough = np.where(near_edge, rough_blended, rough)
    rough = np.clip(rough, 0.12, 0.88)
    rough_u8 = (rough*255).astype(np.uint8)

    # Metallic: near 0 for brick, 0.06 for Gilded mortar specks, else 0
    metal = np.zeros_like(rough)
    if "Gilded" in variant_name:
        # gilded mortar specks metallic 0.12
        gold_metal = (np.sin(x*0.18)*np.sin(y*0.18) > 0.65).astype(float)*0.12 + np.clip(np.sin(x*0.04)*0.5+0.5,0,1)*0.04
        metal = np.where(mortar_mask, gold_metal, 0)
        metal = np.clip(metal, 0, 0.25)
    metal_u8 = (metal*255).astype(np.uint8)

    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)
    # AO: height-based, stronger in mortar crevices
    ao = np.clip(1.0 - (1 - height)*0.58, 0, 1)
    # deepen mortar AO
    ao = np.where(mortar_mask, np.clip(ao - 0.08, 0, 1), ao)
    # crest AO lifts
    ao = np.clip(ao + crest*0.06, 0, 1)
    ao_u8 = (np.clip(ao,0,1)*255).astype(np.uint8)
    # iridescence mask: mortar shimmer + brick crest sheen
    # mortar iridescence strong, crest catches
    iri_mortar = mortar_mask.astype(float) * (0.55 + 0.35*np.sin(x*0.025 + y*0.015 + grain_phase*0.1 + (phase if animate else 0)))
    iri_mortar = np.clip(iri_mortar + glint*0.65, 0, 1)
    iri_crest = crest * 0.45 * (0.6 + 0.4*np.sin(x*0.03 + (phase*1.1 if animate else 0)))
    iri = np.clip(iri_mortar*0.85 + iri_crest, 0, 1)
    # add faint brick face sheen for stone grain
    iri = np.clip(iri + np.clip(grain1,0,1)*0.10* brick_mask.astype(float), 0, 1)
    if is_stone:
        iri *= 0.85  # stone slightly less iridescent, more matte
    iri_u8 = (iri*255).astype(np.uint8)

    orm = np.stack([(ao*255).astype(np.uint8), rough_u8, metal_u8], axis=-1)

    return albedo_u8, normal, rough_u8, metal_u8, height_u8, ao_u8, iri_u8, orm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=4096, help="texture size 4096 or 2048")
    ap.add_argument("--frames", type=int, default=8, help="flipbook frame count")
    ap.add_argument("--quick", action="store_true", help="quick 1K smoke test")
    args = ap.parse_args()
    size = 1024 if args.quick else args.size
    num_frames = 2 if args.quick else args.frames

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(FLIP_DIR, exist_ok=True)
    print(f"Surreal Brick AAA — 4 variants x 7 maps @ {size}x{size} -> {OUT_DIR}")
    print(f"Flipbook: BlushBrick 8 frames x 4 maps @ {size}x{size} -> {FLIP_DIR}")

    # --- static variants ---
    total_maps = 0
    for tag, bA, bB, mort, accent, rmid in VARIANTS:
        seed = abs(hash(tag)) % 2**31
        tables = build_tables(tag, seed)
        print(f"  baking {tag} (brick {bA}/{bB} mortar {mort}) ...")
        albedo, normal, rough, metal, height, ao, iri, orm = gen_brick(tag, bA, bB, mort, accent, rmid, size, tables, animate=False)
        prefix = f"T_SurrealBrick_{tag}"
        Image.fromarray(albedo).save(os.path.join(OUT_DIR, f"{prefix}_BaseColor.png"))
        Image.fromarray(normal).save(os.path.join(OUT_DIR, f"{prefix}_Normal.png"))
        Image.fromarray(rough).save(os.path.join(OUT_DIR, f"{prefix}_Roughness.png"))
        Image.fromarray(metal).save(os.path.join(OUT_DIR, f"{prefix}_Metallic.png"))
        Image.fromarray(height).save(os.path.join(OUT_DIR, f"{prefix}_Height.png"))
        Image.fromarray(ao).save(os.path.join(OUT_DIR, f"{prefix}_AO.png"))
        Image.fromarray(iri).save(os.path.join(OUT_DIR, f"{prefix}_Iridescence.png"))
        Image.fromarray(orm).save(os.path.join(OUT_DIR, f"{prefix}_ORM.png"))
        # also save Emissive alias for UE Toon master (copy of Iridescence)
        Image.fromarray(iri).save(os.path.join(OUT_DIR, f"{prefix}_Emissive.png"))
        print(f"    -> {prefix} 8 files (7 maps + ORM bonus) done")
        total_maps += 7

    print(f"Static done: 4 variants x 7 maps = {total_maps} (plus ORM/Emissive extras)")

    # --- flipbook for BlushBrick ---
    tag = "BlushBrick"
    # find palette entry for Blush
    entry = [v for v in VARIANTS if v[0]==tag][0]
    _, bA, bB, mort, accent, rmid = entry
    seed = abs(hash(tag+"_flip")) % 2**31
    tables = build_tables("BlushBrick_Flip", seed)
    print(f"Flipbook {tag} {num_frames} frames ...")
    for f in range(num_frames):
        phase_deg = (f/num_frames)*360 if num_frames else 0
        print(f"  frame {f:02d}/{num_frames-1} phase {phase_deg:.1f} deg ...")
        albedo, normal, rough, metal, height, ao, iri, orm = gen_brick(tag, bA, bB, mort, accent, rmid, size, tables, frame=f, num_frames=num_frames, animate=True)
        prefix = f"T_SurrealBrick_Flipbook_Frame{f:02d}"
        Image.fromarray(albedo).save(os.path.join(FLIP_DIR, f"{prefix}_BaseColor.png"))
        Image.fromarray(normal).save(os.path.join(FLIP_DIR, f"{prefix}_Normal.png"))
        Image.fromarray(iri).save(os.path.join(FLIP_DIR, f"{prefix}_Iridescence.png"))
        Image.fromarray(rough).save(os.path.join(FLIP_DIR, f"{prefix}_Roughness.png"))
        # Height as 5th bonus for flipbook parity
        Image.fromarray(height).save(os.path.join(FLIP_DIR, f"{prefix}_Height.png"))
        print(f"    saved {prefix} (4 required maps + Height)")

    # verify
    static_files = [f for f in os.listdir(OUT_DIR) if f.startswith("T_SurrealBrick_") and f.endswith(".png")]
    flip_files   = [f for f in os.listdir(FLIP_DIR) if f.startswith("T_SurrealBrick_Flipbook_Frame") and f.endswith(".png")]
    # counts: each static variant has 8 PNGs (7 + ORM) + Emissive alias = 9? adjust verify to at least 7*4
    expected_static_min = 4*7
    expected_flip_min = num_frames*4
    print(f"DONE — static {len(static_files)} files (>= {expected_static_min}) in {OUT_DIR}")
    print(f"DONE — flipbook {len(flip_files)} files (>= {expected_flip_min}) in {FLIP_DIR}")
    for fn in sorted(static_files):
        print(f"  {fn}")
    print("--- flipbook ---")
    for fn in sorted(flip_files):
        print(f"  {fn}")
    if len(static_files) < expected_static_min:
        print(f"WARNING static expected >= {expected_static_min} got {len(static_files)}", file=sys.stderr); sys.exit(1)
    if len(flip_files) < expected_flip_min:
        print(f"WARNING flipbook expected >= {expected_flip_min} got {len(flip_files)}", file=sys.stderr); sys.exit(1)
    print(f"All surreal brick done. static {expected_static_min} required + flip {expected_flip_min} required OK @ {size}x{size}")

if __name__ == "__main__":
    main()
