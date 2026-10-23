#!/usr/bin/env python3
"""
Generate chromatic variants FROM your sculpted choralsheepbase textures,
with subtle magical glow underneath.

Source: Content/Melodia/Companions/ChoralSheep/choralsheepbase_*.png (you just exported)
- BaseColor (sculpted AO + spirals/hearts) — tinted per PC
- Normal / Roughness / etc. — shared (or per-PC if you want)
- Emission (currently black) — replaced with subtle per-PC glow that peeks through sparse wool

Variants (all 4, as you asked):
  A_flat       : tinted BaseColor only, clean
  B_worley12   : + 12% Worley mottle (Houdini intent)
  C_worley25   : + 25% Worley (editorial)
  D_pop        : sat 0.52 pop + 12% Worley (Infinity Nikki pop)

Glow: per-PC accent color, soft, masked by where BaseColor is brightest/thinnest (simulates light through fluff gaps),
      blurred, at ~8-10% emission strength — subtle, not rave. Visible when you peer under the fleece or in dim.

Output:
  Saved/Audit/choral_sheep/sculpted_variants/albedo_{A,B,C,D}/ChoralWool_PC_{C..B}.png
  Saved/Audit/choral_sheep/sculpted_variants/glow_{A,B,C,D}/T_ChoralSheep_Glow_PC_{C..B}.png
  + contact sheets

Run:
  python Tools/Houdini/generate_sculpted_variants_with_glow.py --size 1024 --modes A,B,C,D --glow 0.09
  python Tools/Houdini/generate_sculpted_variants_with_glow.py --size 512 --quick  # draft
"""
import argparse
import colorsys
from pathlib import Path

PITCH_CLASS_HUES = {
    0: ("C", 0.000), 1: ("Cs", 0.083), 2: ("D", 0.167), 3: ("Ds", 0.250),
    4: ("E", 0.333), 5: ("F", 0.417), 6: ("Fs", 0.500), 7: ("G", 0.583),
    8: ("Gs", 0.667), 9: ("A", 0.750), 10: ("As", 0.833), 11: ("B", 0.917),
}
SRC_BASE = Path("Content/Melodia/Companions/ChoralSheep/choralsheepbase_BaseColor.png")
SRC_NORMAL = Path("Content/Melodia/Companions/ChoralSheep/choralsheepbase_Normal.png")
SRC_EMISSION = Path("Content/Melodia/Companions/ChoralSheep/choralsheepbase_Emission.png")

def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def _load_source(size):
    from PIL import Image
    # Fast load + resize to target size to keep memory low
    base = Image.open(SRC_BASE).convert("RGB")
    # Preserve aspect, resize with LANCZOS quickly at 1024
    if base.size != (size, size):
        base = base.resize((size, size), Image.LANCZOS)
    # Precompute grayscale of base for tinting and glow mask
    gray = base.convert("L")
    return base, gray

def _tint_sculpt(base_img, gray_img, pastel_rgb, size):
    """Tint sculpted base: lerp between dark pastel and light pastel by gray."""
    from PIL import Image
    pr, pg, pb = pastel_rgb
    # Dark and light variants of pastel
    dark = (int(pr*0.78), int(pg*0.78), int(pb*0.78))
    light = (int(min(255, pr*1.12)), int(min(255, pg*1.12)), int(min(255, pb*1.12)))
    # Build tinted via per-pixel using PIL's blend with gray as mask
    # Create dark/light images
    dark_im = Image.new("RGB", (size, size), dark)
    light_im = Image.new("RGB", (size, size), light)
    # gray is 0..255 mask: blend dark->light by gray
    # Use gray as alpha for composite light over dark, then multiply base shading?
    # First, make tinted base = composite(light, dark, gray)
    # gray normalized: use gray directly as mask for light
    # light where gray bright, dark where gray dark
    tinted = Image.composite(light_im, dark_im, gray_img)
    final = Image.blend(base_img, tinted, 0.78)
    return final

def _worley_mottle(img, pastel_accent_rgb, size, seed, strength):
    """Add Worley-like mottle at strength 0.12-0.25, subtle, as before but tinted with accent."""
    if strength <= 0.001:
        return img
    from PIL import Image, ImageDraw, ImageFilter
    import random
    rnd = random.Random(seed * 1013 + 7)
    # create noise field via sparse dots -> blur -> Worley cells
    noise = Image.new("L", (size, size), 128)
    nd = ImageDraw.Draw(noise)
    n_seeds = max(40, int(140 * (size / 512) ** 1.0))
    for _ in range(n_seeds):
        x = rnd.randint(0, size)
        y = rnd.randint(0, size)
        r = rnd.randint(int(size*0.02), int(size*0.06))
        v = rnd.randint(30, 230)
        nd.ellipse([x-r, y-r, x+r, y+r], fill=v)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=max(2, int(size/26))))
    # create mottle layers as before but strength-scaled
    # dark and light tints relative to base
    # Use noise as mask for subtle dark/light shift
    # Build dark/light shifts relative to pastel-accent
    # Instead of recomputing per pixel, use PIL composite trick at low strength
    # We'll tint a duplicate of img darker and lighter then composite
    # Darker version
    dark = Image.new("RGB", (size,size), (0,0,0))
    # Quick: adjust brightness via ImageEnhance
    from PIL import ImageEnhance
    dark_im = ImageEnhance.Brightness(img).enhance(0.86)
    light_im = ImageEnhance.Brightness(img).enhance(1.12)
    # Mix with accent tint slightly for accent hue
    # Tint light_im toward accent by 10%
    ar, ag, ab = pastel_accent_rgb
    accent_tint = Image.new("RGB", (size,size), (ar, ag, ab))
    light_im = Image.blend(light_im, accent_tint, 0.07)
    # Masks from noise
    dark_mask = noise.point(lambda p: int(max(0, min(255, (112 - p) * 1.5 * strength * 5))))
    light_mask = noise.point(lambda p: int(max(0, min(255, (p - 158) * 1.4 * strength * 5))))
    tmp = Image.composite(dark_im, img, dark_mask)
    result = Image.composite(light_im, tmp, light_mask)
    result = result.filter(ImageFilter.GaussianBlur(radius=0.6))
    # Blend back at 88% to keep subtlety (strength already scaled masks, but blend again for safety)
    final = Image.blend(img, result, 0.88)
    return final

def _make_glow_map(base_gray, size, seed, accent_rgb, glow_strength=0.09):
    """Subtle under-fluff glow: soft, warm, follows sparse wool gaps.
    Use base_gray bright areas as 'thin wool' where glow peeks through.
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    import random
    rnd = random.Random(seed * 2027 + 99)
    # Build glow source as blurred bright mask
    # Where base is bright (thin wool / highlight), glow is stronger
    # Threshold bright
    glow_mask = base_gray.point(lambda p: int(max(0, min(255, (p - 165) * 2.2))))  # only bright >165
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(radius=max(3, int(size/36))))
    # Add a few soft orbs for magical heart/spiral accents (where your sculpt has swirls, glow clusters)
    orb_layer = Image.new("L", (size, size), 0)
    od = ImageDraw.Draw(orb_layer)
    n_orbs = max(6, int(14 * (size/512)))
    for _ in range(n_orbs):
        x = rnd.randint(int(size*0.08), int(size*0.92))
        y = rnd.randint(int(size*0.08), int(size*0.92))
        r = rnd.randint(int(size*0.04), int(size*0.12))
        alpha = rnd.randint(40, 110)
        od.ellipse([x-r, y-r, x+r, y+r], fill=alpha)
    orb_layer = orb_layer.filter(ImageFilter.GaussianBlur(radius=max(4, int(size/28))))
    # Combine masks
    glow_mask = ImageChops.add(glow_mask, orb_layer)
    glow_mask = glow_mask.point(lambda p: min(255, int(p * glow_strength * 9)))  # scale to subtle
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(radius=max(2, int(size/48))))
    # Colorize mask with accent color
    ar, ag, ab = accent_rgb
    glow_rgb = Image.new("RGB", (size, size), (ar, ag, ab))
    # Apply pastel accent at ~90% of mask, with falloff
    # Create black base for glow
    black = Image.new("RGB", (size, size), (0,0,0))
    glow = Image.composite(glow_rgb, black, glow_mask)
    # Add a softer outer bloom
    glow = glow.filter(ImageFilter.GaussianBlur(radius=1))
    return glow, glow_mask

def main():
    import argparse
    from PIL import Image, ImageDraw
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--modes", default="A,B,C,D", help="comma list A,B,C,D")
    ap.add_argument("--glow", type=float, default=0.09, help="glow strength 0..0.2, 0.09 subtle")
    ap.add_argument("--quick", action="store_true", help="512 draft")
    args = ap.parse_args()
    size = 512 if args.quick else args.size
    modes = [m.strip().upper() for m in args.modes.split(",")]
    # Load source once at target size
    print(f"[sculpt] loading source {SRC_BASE} at {size}...")
    base_src, gray_src = _load_source(size)
    # Prepare output roots
    out_root = Path("Saved/Audit/choral_sheep/sculpted_variants")
    # Mode defs: (worley_strength, sat, label)
    mode_cfg = {
        "A": (0.00, 0.38, "A_flat"),
        "B": (0.12, 0.38, "B_worley12"),
        "C": (0.25, 0.38, "C_worley25"),
        "D": (0.12, 0.52, "D_pop_worley12"),
    }
    for mode in modes:
        if mode not in mode_cfg:
            print(f"[sculpt] unknown mode {mode}, skipping")
            continue
        worley, sat, label = mode_cfg[mode]
        out_albedo = out_root / f"albedo_{label}"
        out_glow = out_root / f"glow_{label}"
        out_albedo.mkdir(parents=True, exist_ok=True)
        out_glow.mkdir(parents=True, exist_ok=True)
        print(f"[sculpt] MODE {mode} -> {label} sat={sat} worley={worley} glow={args.glow}")
        for pc, (lab, hue) in PITCH_CLASS_HUES.items():
            pastel_base, pastel_accent = _pastel_pair(hue, sat=sat, val=0.92)
            prgb = tuple(int(c*255) for c in pastel_base)
            argb = tuple(int(c*255) for c in pastel_accent)
            # Tint sculpt
            albedo = _tint_sculpt(base_src, gray_src, prgb, size)
            # Worley
            albedo = _worley_mottle(albedo, argb, size, seed=pc*3+7, strength=worley)
            albedo_path = out_albedo / f"ChoralWool_PC_{lab}.png"
            albedo.save(albedo_path, "PNG")
            # Glow map: subtle under-fluff
            glow_img, mask = _make_glow_map(gray_src, size, seed=pc*5+13, accent_rgb=argb, glow_strength=args.glow)
            glow_path = out_glow / f"T_ChoralSheep_Glow_PC_{lab}.png"
            glow_img.save(glow_path, "PNG")
            print(f"  PC{pc:02d} {lab:2s} -> {albedo_path.name} + {glow_path.name} base {prgb} accent {argb}")
        # Contact sheets per mode
        # Albedo sheet 4x3
        sheet = Image.new("RGB", (size, size*3//4*3 + 24 if False else 0), (0,0,0))
        # Simpler: reuse thumb logic
        cols, rows, thumb = 4, 3, size//4 if size>=1024 else size//2
        sheet_w, sheet_h = cols*thumb, rows*thumb + 24
        sheet = Image.new("RGB", (sheet_w, sheet_h), (18,18,18))
        sd = ImageDraw.Draw(sheet)
        for i, (pc,(lab,hue)) in enumerate(PITCH_CLASS_HUES.items()):
            p = out_albedo / f"ChoralWool_PC_{lab}.png"
            if p.is_file():
                im = Image.open(p).resize((thumb, thumb), Image.LANCZOS)
                x, y = (i%cols)*thumb, (i//cols)*thumb
                sheet.paste(im, (x, y))
                try: sd.text((x+4, y+thumb-14), f"PC{pc:02d} {lab}", fill=(255,255,255))
                except: pass
        try: sd.text((6, sheet_h-16), f"albedo_{label} sat={sat} worley={worley} — sculpted base tinted", fill=(200,200,200))
        except: pass
        sheet_path = out_root / f"_CONTACT_albedo_{label}.png"
        sheet.save(sheet_path, "PNG")
        print(f"[sculpt] sheet {sheet_path}")
        # Glow sheet
        gsheet = Image.new("RGB", (sheet_w, sheet_h), (0,0,0))
        gd = ImageDraw.Draw(gsheet)
        for i, (pc,(lab,hue)) in enumerate(PITCH_CLASS_HUES.items()):
            p = out_glow / f"T_ChoralSheep_Glow_PC_{lab}.png"
            if p.is_file():
                im = Image.open(p).resize((thumb, thumb), Image.LANCZOS)
                x, y = (i%cols)*thumb, (i//cols)*thumb
                gsheet.paste(im, (x, y))
                try: gd.text((x+4, y+thumb-14), f"PC{pc:02d} {lab}", fill=(255,255,255))
                except: pass
        try: gd.text((6, sheet_h-16), f"glow_{label} accent glow {args.glow*100:.1f}% — subtle under-fluff", fill=(200,200,200))
        except: pass
        gsheet_path = out_root / f"_CONTACT_glow_{label}.png"
        gsheet.save(gsheet_path, "PNG")
        print(f"[sculpt] glow sheet {gsheet_path}")
    print(f"[sculpt] done — {out_root} — all modes {modes}")

if __name__ == "__main__":
    main()
