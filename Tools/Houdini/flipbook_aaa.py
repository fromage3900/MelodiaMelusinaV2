"""
flipbook_aaa.py — AAA Pearl/Silk woven flipbook sequence (8 frames x 5 maps)
for M_Master_Nikki flipbook shimmer.

Generates into Content/EnvSandbox/Textures/PearlWoven_Flipbook/
Each frame shifts iridescence hue + wash phase so flipbooking animates
nacre shimmer without popping normals.

Maps per frame (5):
  T_PearlFlipbook_FrameNN_BaseColor.png  (RGB8)
  T_PearlFlipbook_FrameNN_Normal.png      (RGB8, tangent-space)
  T_PearlFlipbook_FrameNN_Iridescence.png (R8, mask+phase)
  T_PearlFlipbook_FrameNN_Roughness.png   (R8)
  T_PearlFlipbook_FrameNN_Height.png      (R8)

Defaults to 2048 to keep flipbook light (~16 MB per frame uncompressed,
~4-6MB PNG). Pass --size 4096 for full 4K. Run via hython.

  hython Tools/Houdini/flipbook_aaa.py [--size 2048] [--frames 8]
"""
import os, sys, argparse, math
import numpy as np
from PIL import Image

OUT_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Textures/PearlWoven_Flipbook"

# canonical AAA pearl/silk palette (Moon painterly - most neutral, reads under iridescence)
BASE_RGB    = (245, 242, 235)
BLUSH_RGB   = (230, 228, 222)
ACCENT_RGB  = (255, 240, 230)  # warm pearl dust
ROUGH_BASE  = 0.31

def smoothstep(a,b,x):
    t = np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)

def gen_flipbook_frame(frame, num_frames, size):
    """Generate one flipbook frame. phase in [0, 2pi)."""
    phase = (frame / num_frames) * math.pi * 2.0
    # sub-phases for different layers so they drift at different rates (parallax shimmer)
    phase_wash = phase * 0.65
    phase_s1   = phase * 1.20
    phase_s2   = phase * -0.90
    phase_s3   = phase * 0.75
    phase_iri  = phase * 1.40

    # hue rotation for iridescence: subtle 18 deg per frame (~144 deg total loop)
    # implemented as tint shift on accent contribution
    hue_shift = (frame / num_frames) * 0.18  # 0..0.18 amplitude drift
    # deterministic seed per frame but stable noise field base
    np.random.seed(1337)  # fixed base so weave structure does NOT pop per-frame
    # we want stable structural noise but per-frame micro jitter
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)

    # --- woven satin structure (STABLE across frames — only wash/shimmer animate) ---
    warp_period = 18
    weft_period = 18
    twist = (y * 0.00008)
    x_twisted = x + np.sin(twist*15)*2.5
    offset = (y // weft_period) % 7
    warp_shift = ((x_twisted - offset*3.2) % warp_period) < 13
    weft = (y % weft_period) < 5
    over = warp_shift.astype(float)*0.95 + weft.astype(float)*0.18

    # structural micro-noise — stable (same seed, same field for all frames)
    # using a cached noise field derived from hash of coordinates + fixed seed
    # generate once: white noise then smooth slightly for thread fiber
    fn = np.random.randn(size, size)*0.018
    # wash — ANIMATED per frame (low-freq watercolor drift)
    wash_x = np.sin(x*0.002 + y*0.0015 + phase_wash)*0.04
    wash_y = np.cos(y*0.003 - x*0.001 + phase_wash*0.7)*0.03
    thick = 0.03*np.sin(x*0.08 + y*0.05)
    height_base = np.clip(over + fn + wash_x + wash_y*0.5 + thick, 0, 1)
    height_base = smoothstep(0.2, 0.85, height_base)
    # brush grain — slightly phase-shifted per frame so highlight crawls
    brush = np.sin(x*0.15 + phase_s1*0.3)*np.cos(y*0.12 + phase_s2*0.2)*0.015
    height_base = np.clip(height_base + brush, 0, 1)
    height = height_base

    # --- normal from height (stable but with crawling micro-jitter) ---
    dy, dx = np.gradient(height)
    dx *= 14; dy *= 14
    # per-frame micro normal jitter with phase offset — subtle crawl, not pop
    # use deterministic sin-based jitter instead of randn per frame to avoid flicker
    jitter_amp = 0.06
    jx = np.sin(x*0.07 + phase*2.1 + y*0.03)*jitter_amp
    jy = np.cos(y*0.07 - phase*1.7 + x*0.02)*jitter_amp
    dx += jx
    dy += jy
    nx = -dx; ny = -dy; nz = np.ones_like(nx)
    nlen = np.sqrt(nx*nx + ny*ny + nz*nz)
    nx/=nlen; ny/=nlen; nz/=nlen
    normal = np.stack([(nx*0.5+0.5)*255,(ny*0.5+0.5)*255,nz*255], axis=-1).astype(np.uint8)

    # --- albedo — pearl nacre with drifting shimmer + hue wash ---
    base  = np.array(BASE_RGB, float)/255.0
    blush = np.array(BLUSH_RGB, float)/255.0
    accent= np.array(ACCENT_RGB,float)/255.0
    # accent hue drift per frame: push accent slightly pink->peach->mint->lavender
    # small sinusoidal offset in log RGB
    accent_drift = np.array([
        0.015*math.sin(phase*1.0),
        0.012*math.sin(phase*1.3 + 1.1),
        0.015*math.cos(phase*0.9 + 0.4),
    ])
    accent_frame = np.clip(accent + accent_drift, 0, 1)

    tint = np.where(warp_shift[:,:,None], base, blush)
    s1 = 0.035*np.sin(x*0.018 + y*0.012 + phase_s1)[:,:,None]
    s2 = 0.025*np.sin(x*0.009 - y*0.022 + phase_s2)[:,:,None]
    s3 = 0.018*np.sin((x+y)*0.006 + phase_s3)[:,:,None]
    # pearl dust flecks — stable positions but intensity shimmers per frame
    # use fixed random field modulated by phase
    np.random.seed(4242)
    fleck_field = (np.random.rand(size,size) > 0.985).astype(float)
    np.random.seed(1337)  # restore
    fleck_intensity = 0.02 * (0.7 + 0.3*math.sin(phase*1.6))
    fleck = fleck_intensity * fleck_field[:,:,None] * (accent_frame - tint)
    # wash color hue drifts per frame
    wash_color = 0.03*np.sin(x*0.001 + y*0.002 + phase_wash)[:,:,None] * np.array([0.02 + hue_shift*0.04, 0.01 - hue_shift*0.02, -0.01 + hue_shift*0.03])
    albedo = np.clip(tint + s1 + s2 + s3 + fleck + wash_color, 0, 1)
    # hand-mixed pigment jitter — stable + tiny phase-modulated amount
    np.random.seed(999 + frame)  # slight per-frame variation but low amplitude
    jitter = np.random.randn(size,size,3)*0.010
    albedo = np.clip(albedo + jitter, 0, 1)
    albedo_u8 = (albedo*255).astype(np.uint8)

    # --- roughness — crest glossy, valley soft, wash-driven crawl ---
    rough = np.where(height>0.62, ROUGH_BASE-0.09, ROUGH_BASE+0.07)
    rough += wash_x*0.12
    # tiny per-frame rough shimmer
    rough += 0.006*math.sin(phase*1.1) * np.sin(x*0.005 + y*0.003)
    np.random.seed(2024 + frame)
    rough += np.random.randn(size,size)*0.015
    rough = np.clip(rough, 0.12, 0.88)
    rough_u8 = (rough*255).astype(np.uint8)

    # --- height ---
    height_u8 = (np.clip(height,0,1)*255).astype(np.uint8)

    # --- iridescence mask — crest-weighted + crawling wave + hue shift ---
    # base: crest highlight
    iri = np.clip((height - 0.5)*1.8, 0, 1) * (0.70 + 0.30*np.sin(x*0.020 + phase_iri + y*0.001))
    # secondary crawling iridescent band (thin-film interference approximation)
    band = 0.12*np.sin(x*0.030 - y*0.018 + phase_iri*1.2) + 0.08*np.sin((x+y)*0.012 + phase_s3)
    iri = np.clip(iri + band, 0, 1)
    # per-frame global intensity breathe (shimmer)
    breathe = 0.06*math.sin(phase*0.9 + 0.5)
    iri = np.clip(iri + breathe, 0, 1)
    iri_u8 = (iri*255).astype(np.uint8)

    return albedo_u8, normal, iri_u8, rough_u8, height_u8

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=2048, help="texture size (2048 or 4096)")
    ap.add_argument("--frames", type=int, default=8, help="frame count")
    ap.add_argument("--out", type=str, default=OUT_DIR, help="output dir")
    args = ap.parse_args()
    size = args.size
    num_frames = args.frames
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    print(f"Flipbook AAA — {num_frames} frames x 5 maps @ {size}x{size} -> {out_dir}")

    for f in range(num_frames):
        print(f"  frame {f:02d}/{num_frames-1} phase={(f/num_frames)*360:.1f} deg ...")
        albedo, normal, iri_u8, rough_u8, height_u8 = gen_flipbook_frame(f, num_frames, size)
        prefix = f"T_PearlFlipbook_Frame{f:02d}"
        Image.fromarray(albedo).save(os.path.join(out_dir, f"{prefix}_BaseColor.png"))
        Image.fromarray(normal).save(os.path.join(out_dir, f"{prefix}_Normal.png"))
        Image.fromarray(iri_u8).save(os.path.join(out_dir, f"{prefix}_Iridescence.png"))
        Image.fromarray(rough_u8).save(os.path.join(out_dir, f"{prefix}_Roughness.png"))
        Image.fromarray(height_u8).save(os.path.join(out_dir, f"{prefix}_Height.png"))
        print(f"    saved {prefix} (5 maps)")

    # verify
    files = sorted(os.listdir(out_dir))
    expected = num_frames * 5
    actual = len([x for x in files if x.startswith("T_PearlFlipbook_Frame")])
    print(f"DONE — {actual}/{expected} files in {out_dir}")
    for fn in files:
        if fn.startswith("T_PearlFlipbook_Frame"):
            print(f"  {fn}")
    if actual != expected:
        print(f"WARNING expected {expected} got {actual}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
