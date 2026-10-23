import os, numpy as np
from PIL import Image
out_dir = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/SurrealCobble"
os.makedirs(out_dir, exist_ok=True)

def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def gen_cobble(variant, base_rgb, highlight_rgb, accent_rgb, mortar_rgb,
               nx=12, mortar_width=20, bevel=14, size=4096):
    seed = abs(hash(variant)) % 2**32
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[0:size,0:size].astype(np.float32)
    cell_w = size / nx
    cell_h = size / nx  # square cells
    ny = nx

    # jittered points + per-cell attributes
    pts_x = np.zeros((ny,nx), dtype=np.float32)
    pts_y = np.zeros((ny,nx), dtype=np.float32)
    pts_r = np.zeros((ny,nx), dtype=np.float32)  # radius factor
    pts_col = np.zeros((ny,nx,3), dtype=np.float32)  # color shift per cobble
    # palette shift per cobble: interpolate base/highlight
    base = np.array(base_rgb, float)/255.0
    hi   = np.array(highlight_rgb, float)/255.0
    acc  = np.array(accent_rgb, float)/255.0
    mortar_col = np.array(mortar_rgb, float)/255.0

    for gy in range(ny):
        for gx in range(nx):
            jx = (rng.rand()-0.5)*cell_w*0.68
            jy = (rng.rand()-0.5)*cell_h*0.68
            cx = gx*cell_w + cell_w*0.5 + jx
            cy = gy*cell_h + cell_h*0.5 + jy
            # wrap to [0,size)
            cx = cx % size
            cy = cy % size
            pts_x[gy,gx]=cx
            pts_y[gy,gx]=cy
            pts_r[gy,gx]= rng.uniform(0.86,1.14)
            # color jitter per stone: random mix base/hi + accent whisper
            mix = rng.uniform(0.0,0.55)
            col = base*(1-mix) + hi*mix + (rng.randn(3)*0.04)
            # accent vein for some stones (15% chance stronger accent)
            if rng.rand() < 0.13:
                col = col*0.65 + acc*0.35 + rng.randn(3)*0.02
            pts_col[gy,gx]= np.clip(col,0,1)

    # per-pixel cell index
    gx0 = np.floor(x / cell_w).astype(np.int32) % nx
    gy0 = np.floor(y / cell_h).astype(np.int32) % ny
    # distance fields
    d1 = np.full((size,size), 1e9, dtype=np.float32)
    d2 = np.full((size,size), 1e9, dtype=np.float32)
    dx_best = np.zeros((size,size), dtype=np.float32)
    dy_best = np.zeros((size,size), dtype=np.float32)
    id_x = np.zeros((size,size), dtype=np.int32) # store gx of nearest
    id_y = np.zeros((size,size), dtype=np.int32)
    # also need per-pixel radius and color later via id lookup
    # iterate 9 neighbours
    for oy in (-1,0,1):
        for ox in (-1,0,1):
            ngx = gx0 + ox
            ngy = gy0 + oy
            # wrapped indices for lookup
            ngx_mod = np.mod(ngx, nx).astype(np.int32)
            ngy_mod = np.mod(ngy, ny).astype(np.int32)
            # wrap offset in pixels
            # compute k: how many wraps: (ngx - ngx_mod)/nx  essentially floorDiv
            # Since ngx in [-1, nx], simple logic: if ngx<0 -> -1, elif ngx>=nx -> +1 else 0
            # vectorized via where
            wrap_x = np.zeros_like(ngx, dtype=np.float32)
            wrap_y = np.zeros_like(ngy, dtype=np.float32)
            # use boolean masks
            wrap_x[ngx<0] = -size
            wrap_x[ngx>=nx] = size
            wrap_y[ngy<0] = -size
            wrap_y[ngy>=ny] = size
            # gather point positions
            # pts_x[ngy_mod, ngx_mod] via fancy indexing
            # Need to do advanced indexing: pts_x[ngy_mod, ngx_mod] doesn't work directly as 2D arrays
            # Use vectorized lookup via flattened index
            # pts_x flat index = ngy_mod*nx + ngx_mod
            flat_idx = ngy_mod.astype(np.int32)*nx + ngx_mod.astype(np.int32)
            # we can use np.take for speed? take from flattened pts
            pts_x_flat = pts_x.ravel()
            pts_y_flat = pts_y.ravel()
            px = np.take(pts_x_flat, flat_idx)
            py = np.take(pts_y_flat, flat_idx)
            px = px + wrap_x
            py = py + wrap_y
            dx = px - x
            dy = py - y
            dist = np.sqrt(dx*dx + dy*dy)
            # update d1/d2
            mask1 = dist < d1
            # when new nearest, old d1 becomes candidate for d2
            d2[mask1] = d1[mask1]
            d1[mask1] = dist[mask1]
            dx_best[mask1] = dx[mask1]
            dy_best[mask1] = dy[mask1]
            id_x[mask1] = ngx_mod[mask1]
            id_y[mask1] = ngy_mod[mask1]
            # for others where dist < d2 but not < d1
            mask2 = (~mask1) & (dist < d2)
            d2[mask2] = dist[mask2]

    # edge distance (mortar indicator)
    edge = d2 - d1
    # softened radius per pixel using nearest point's radius factor
    flat_idx_best = id_y.astype(np.int32)*nx + id_x.astype(np.int32)
    r_factor = np.take(pts_r.ravel(), flat_idx_best)  # (size,size)
    # base radius ~0.48*cell (allow variation)
    R_base = cell_w * 0.48
    R = R_base * r_factor
    # organic warp on d1: waviness by angle
    ang = np.arctan2(dy_best, dx_best)
    # phase per stone for organic asymmetry
    # generate phase array per stone, then lookup
    pts_phase = rng.uniform(0, np.pi*2, size=(ny,nx)).astype(np.float32)
    phase = np.take(pts_phase.ravel(), flat_idx_best)
    warp = 1.0 + 0.07*np.sin(ang*3.0 + phase) + 0.04*np.sin(ang*5.0 - phase*0.7)
    d1_w = d1 * warp
    # cobble dome height: cosine dome soft
    t = np.clip(d1_w / (R+1e-6), 0, 1)
    h_dome = np.cos(t * np.pi * 0.5)  # 1 center, 0 edge at R
    # soften top: keep plateau
    h_dome = np.power(h_dome, 0.85)
    # mortar / edge bevel
    # narrow lace-like mortar: where edge < mortar_width
    mortar_w = float(mortar_width)
    feather = 9.0
    mortar_mask = 1.0 - smoothstep(mortar_w - feather, mortar_w + feather, edge)
    # narrow pearl dust lace: sharpen mortar narrower than voronoi gap
    # bevel: height drops toward mortar edge
    # bevel height: smooth step around mortar edge transition
    # mortar is low, cobble is high. Use mortar_mask to lerp down
    bevel_m = smoothstep(0.15, 0.85, mortar_mask)
    # height in mortar lower + pearl dust relief (fine grain)
    mortar_low = 0.08
    # edge bevel curve: round edge (fillet) not harsh
    # blend dome with mortar floor using bevel
    height = h_dome * (1 - bevel_m*0.92) + mortar_low * bevel_m
    # subtle edge rounding: add fillet term
    fillet = smoothstep(mortar_w*0.4, mortar_w*1.4, edge)  # 0 near edge, 1 inside cobble
    height = height * (0.88 + 0.12*fillet) + 0.02*fillet
    # pearl dust in mortar: tiny speckled relief + slight height noise
    # lace-like pearl dust: fine granular noise only in mortar
    pearl_noise = (np.sin(x*0.18 + y*0.11)*0.35 + np.sin(x*0.33 - y*0.22)*0.25 + rng.randn(size,size)*0.18)*0.5+0.5
    pearl_noise = np.clip(pearl_noise,0,1)
    height = height + mortar_mask*pearl_noise*0.06* (0.5+0.5*np.sin(x*0.01))
    # painterly wash low-freq
    wash_a = np.sin(x*0.0018 + y*0.0012 + seed*0.001)*0.025
    wash_b = np.cos(y*0.0022 - x*0.0014)*0.018
    wash_c = np.sin((x*0.7 + y)*0.0011)*0.014
    wash_d = np.sin(x*0.0009 + y*0.0017)*0.012
    height = np.clip(height + (wash_a+wash_b+wash_c)*0.12, 0, 1)
    # limit
    height = np.clip(height, 0, 1)
    height = smoothstep(0.0, 1.0, height)
    # add micro random
    height = np.clip(height + rng.randn(size,size)*0.008, 0, 1)

    # ----- ALBEDO -----
    # per-pixel stone color from nearest stone
    # pts_col is (ny,nx,3)
    pts_col_r = pts_col[:,:,0].ravel()
    pts_col_g = pts_col[:,:,1].ravel()
    pts_col_b = pts_col[:,:,2].ravel()
    col_r = np.take(pts_col_r, flat_idx_best)
    col_g = np.take(pts_col_g, flat_idx_best)
    col_b = np.take(pts_col_b, flat_idx_best)
    stone_col = np.stack([col_r, col_g, col_b], axis=-1)  # (size,size,3)
    # mortar color with pearl dust tint (lighter, warm)
    mortar_rgb_f = mortar_col
    # blend stone vs mortar
    # lace-like narrow mortar: mortar color in mortar_mask, stone elsewhere
    # feather blend
    mortar_blend = mortar_mask[:,:,None]
    albedo = stone_col * (1 - mortar_blend*0.92) + mortar_rgb_f * mortar_blend*0.96
    # per-cobble highlight top (center lighter)
    center_highlight = np.clip(1 - t, 0, 1)  # 1 at center
    center_highlight = np.power(center_highlight, 1.4)
    albedo = albedo + center_highlight[:,:,None]*0.085  # lift centre
    # vein accent on some stones: use edge of accent stones already baked via pts_col, but add subtle vein streak
    vein = 0.5+0.5*np.sin(x*0.012 + y*0.018 + phase*0.3)*0.5 + 0.5*np.sin(ang*2)*0.3
    # only visible inside cobble, not mortar
    vein_mask = (1-mortar_mask)*np.clip(vein*0.5,0,1)
    # shift hue slightly toward accent for vein
    accent_shift = (acc - stone_col)*0.0 # we already have acc blended via pts_col; use subtle overlay
    # add gentle wash painterly color variation (large clouds tint)
    wash_col = (wash_a[:,:,None]*np.array([0.06,0.02,-0.04]) + wash_b[:,:,None]*np.array([-0.03,0.02,0.05]) + wash_c[:,:,None]*np.array([0.02,-0.01,0.03]))
    albedo = np.clip(albedo + wash_col + vein_mask[:,:,None]*0.04 + rng.randn(size,size,3)*0.011, 0, 1)
    # pearl dust speckles in mortar: tiny bright flecks
    fleck_prob = 0.004
    fleck = (rng.rand(size,size) < fleck_prob).astype(float)
    fleck = fleck * mortar_mask  # only in mortar lace
    fleck_col = np.array([0.98,0.97,0.95])
    albedo = np.clip(albedo + fleck[:,:,None]*0.55* (fleck_col - albedo)*0.7, 0,1)
    albedo = np.clip(albedo,0,1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # ----- ROUGHNESS (detailed) -----
    # cobble glossy 0.2 on top, mortar rough 0.65, edge bevel intermediate 0.35
    # top = center area (t small), bottom/mortar high
    # use height and distance
    rough = np.zeros((size,size), dtype=np.float32)
    # base per region
    # cobble centre glossy
    rough = np.where(t < 0.35, 0.20, 0.20 + (t-0.35)/0.65*0.18)  # 0.20 at center -> ~0.38 at edge before mortar
    # bevel zone (near mortar edge)
    bevel_zone = smoothstep(mortar_w*0.6, mortar_w*1.3, edge)  # 0 near mortar, 1 inside
    rough = rough * (0.92 + 0.08*bevel_zone)  # slight
    # mortar rough
    rough = rough * (1 - mortar_mask) + 0.65 * mortar_mask
    # edge bevel intermediate: where mortar_mask transitioning, force 0.33-0.42
    edge_ring = smoothstep(0.2,0.78, 1-bevel_zone) * (1-mortar_mask)  # ring around stone edge
    # blend edge ring roughness toward 0.34
    rough = np.where(edge_ring>0.25, rough*0.55 + 0.34*0.45, rough)
    # add wash + micro
    rough = rough + wash_a*0.04 + rng.randn(size,size)*0.015
    rough = np.clip(rough, 0.14, 0.85)
    rough_u8 = (np.clip(rough,0,1)*255).astype(np.uint8)

    # ----- METALLIC -----
    # stones dielectric 0, tiny pearl dust has faint
    metallic = np.zeros((size,size), dtype=np.float32)
    metallic = metallic + fleck*0.06 + mortar_mask*pearl_noise*0.015
    metallic = np.clip(metallic,0,0.08)
    metal_u8 = (metallic*255).astype(np.uint8)

    # ----- HEIGHT already computed -----
    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)
    ao = np.clip(1.0 - (1-height)*0.52, 0, 1)  # AO darker in mortar
    ao_u8 = (ao*255).astype(np.uint8)

    # ----- NORMAL tilable gradient -----
    # use wrapped gradient to keep tilable seams
    # roll method
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1))*0.5
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 0, axis=0))*0.5
    nscale = 13.0
    dx = dx * nscale
    dy = dy * nscale
    # micro perturbation
    dx += rng.randn(size,size)*0.04
    dy += rng.randn(size,size)*0.04
    nx_ = -dx
    ny_ = -dy
    nz_ = np.ones_like(nx_)
    nlen = np.sqrt(nx_*nx_ + ny_*ny_ + nz_*nz_)
    nx_ /= nlen; ny_ /= nlen; nz_ /= nlen
    normal = np.stack([(nx_*0.5+0.5)*255,(ny_*0.5+0.5)*255,nz_*255], axis=-1).astype(np.uint8)

    # ----- IRIDESCENCE mask on stone crests for perfect light catch -----
    # crest where height high and edge large (center), not mortar
    crest = np.clip((height - 0.58)*2.8, 0, 1)  # high plateau on tops
    crest = crest * (1 - mortar_mask)  # remove mortar
    # additional dome radial: strongest at center
    crest = crest * np.clip(1 - t*0.7, 0.3, 1)
    # thin-film interference pattern on crests (subtle rainbow strength map)
    interference = 0.55 + 0.30*np.sin(x*0.018 + y*0.015 + phase*0.2) + 0.15*np.sin(x*0.032 - y*0.020)
    iri = crest * (0.55 + 0.45*interference)
    # large wash modulates
    iri = iri * (0.85 + 0.15*np.sin(x*0.0013 + y*0.0011))
    # lace pearl dust in mortar gets faint iri too but much lower
    iri = iri + mortar_mask*pearl_noise*0.08
    iri = np.clip(iri + rng.randn(size,size)*0.012, 0, 1)
    iri = np.clip(iri*0.90 + 0.02, 0, 1)
    iri_u8 = (iri*255).astype(np.uint8)

    # ----- ORM -----
    orm = np.stack([ao_u8, rough_u8, metal_u8], axis=-1)

    # ----- OPACITY -----
    opacity_u8 = np.full((size,size), 255, dtype=np.uint8)

    return albedo_u8, normal, rough_u8, metal_u8, height_u8, orm, iri_u8, opacity_u8

palettes = [
    ("Moonstone",    (232,235,242),(250,248,242),(200,215,235),(240,236,228), 12, 19),
    ("RoseQuartz",   (244,210,214),(255,232,232),(218,148,168),(245,225,220), 11, 21),
    ("Opal",         (245,243,238),(255,250,245),(210,200,225),(238,235,230), 13, 18),
    ("LavenderVein", (230,220,238),(240,230,250),(170,145,205),(232,228,240), 12, 20),
    ("PearlSand",    (242,236,222),(250,245,230),(200,185,160),(238,230,210), 10, 22),
    ("ShellStone",   (248,235,225),(255,248,238),(242,180,165),(245,235,220), 12, 19),
]

for name, base, hi, acc, mortar, nx, mow in palettes:
    tag = name
    print(f"cobble AAA {tag} 4K nx={nx} mortar={mow} ...")
    albedo, normal, rough, metal, height, orm, iri, opacity = gen_cobble(tag, base, hi, acc, mortar, nx=nx, mortar_width=mow, size=4096)
    prefix = f"T_SurrealCobble_{tag}"
    Image.fromarray(albedo).save(f"{out_dir}/{prefix}_BaseColor.png")
    Image.fromarray(normal).save(f"{out_dir}/{prefix}_Normal.png")
    Image.fromarray(orm).save(f"{out_dir}/{prefix}_ORM.png")
    Image.fromarray(rough).save(f"{out_dir}/{prefix}_Roughness.png")
    Image.fromarray(metal).save(f"{out_dir}/{prefix}_Metallic.png")
    Image.fromarray(height).save(f"{out_dir}/{prefix}_Height.png")
    Image.fromarray(iri).save(f"{out_dir}/{prefix}_Iridescence.png")
    Image.fromarray(opacity).save(f"{out_dir}/{prefix}_Opacity.png")
    print(f"  -> {prefix} done (8 maps, 7 required + extra Roughness)")

print(f"All cobble done total {len(palettes)} variants x 8 maps = {len(palettes)*8} files in {out_dir}")
print("Maps: BaseColor/Normal/ORM/Roughness/Metallic/Height/Iridescence/Opacity at 4096 tilable")
