#!/usr/bin/env python3
"""
Wool Lab — experiment suite for Choral Sheep coats

Generates side-by-side comparisons:
  - clean flat albedo (shipping candidate)
  - 12% Worley-like mottle (subtle, Houdini-intent)
  - 25% Worley (more editorial, Infinity Nikki pop test)
  - 12% + fiber grain vs flat
Each variant per PC, plus a super-sheet for review.

Run:
  python Tools/Houdini/experiment_wool_lab.py --size 512 --out Saved/Audit/choral_sheep/experiments
"""
import argparse
import colorsys
import random
from pathlib import Path

PITCH_CLASS_HUES = {
    0:  ("C",  0.000), 1:  ("Cs", 0.083), 2:  ("D",  0.167), 3:  ("Ds", 0.250),
    4:  ("E",  0.333), 5:  ("F",  0.417), 6:  ("Fs", 0.500), 7:  ("G",  0.583),
    8:  ("Gs", 0.667), 9:  ("A",  0.750), 10: ("As", 0.833), 11: ("B",  0.917),
}
def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def _flat(base_rgb, size):
    from PIL import Image
    return Image.new("RGB", (size, size), base_rgb)

def _worley_mottle(base_rgb, accent_rgb, size, seed=0, strength=0.12):
    """Single-layer soft mottle approximating Worley F1 via blurred random threshold.
    strength 0.12 = 12% overlay, very subtle
    """
    from PIL import Image, ImageDraw, ImageFilter, ImageOps
    import random
    rnd = random.Random(seed * 1013 + 7)
    # start from base
    from PIL import Image
    img = Image.new("RGB", (size, size), base_rgb)
    base_r, base_g, base_b = base_rgb
    # Create a grayscale noise field via sparse dots then heavy blur -> organic
    # Instead of ellipses, use point scatter + Voronoi-like via blurred dots
    noise = Image.new("L", (size, size), 128)
    nd = ImageDraw.Draw(noise)
    # scatter ~180 seeds at size 512 scaled
    n_seeds = max(60, int(220 * (size / 512) ** 1.1))
    for _ in range(n_seeds):
        x = rnd.randint(0, size)
        y = rnd.randint(0, size)
        r = rnd.randint(int(size*0.018), int(size*0.055))
        # random gray patch — will be blurred into Worley-like cells
        v = rnd.randint(40, 220)
        nd.ellipse([x-r, y-r, x+r, y+r], fill=v)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=max(2, int(size/28))))
    # remap noise to -1..1 via LUT and use to tint base toward accent/darken
    # apply as overlay: pixel = base * (1-strength) + tinted * strength where tinted = base lerp accent by noise
    # Build tint map
    tint = Image.new("RGB", (size, size))
    acc_r, acc_g, acc_b = accent_rgb
    # Use per-pixel via PIL's point + composite: create two tint layers
    # Darker lerp and lighter lerp, blend by noise
    dark = tuple(max(0, min(255, int(base_r*0.78 + acc_r*0.08))) for base_r in [base_r]*1)
    # We'll just use ImageChops style: create dark and light images and blend via noise as mask
    dark_rgb = (max(0, int(base_r*0.82 - 14)), max(0, int(base_g*0.82 - 14)), max(0, int(base_b*0.82 - 14)))
    light_rgb = (min(255, int(base_r + 22)), min(255, int(base_g + 22)), min(255, int(base_b + 22)))
    # Occasionally tint toward accent for 20% of area where noise > 180
    # Create dark/light blended image via noise threshold
    # Convert noise to mask for dark
    # mask_dark = noise point < 90 -> dark, > 165 -> light, else base
    # Instead of per-pixel python loop (slow), use PIL LUT + compositing trick:
    # Make two layers and composite with noise as alpha
    dark_layer = Image.new("RGB", (size, size), dark_rgb)
    light_layer = Image.new("RGB", (size, size), light_rgb)
    # Use noise as blend factor: normalize noise 0..255 -> 0..strength
    # Build strength-scaled mask: mask = (noise - 128) * strength*2
    # For performance, do: result = blend(base, dark_layer, mask_dark_strength) then blend with light
    # mask as 'L' image opacity
    # dark mask: where noise < 100, stronger
    dark_mask = noise.point(lambda p: int(max(0, min(255, (110 - p) * 1.4 * strength * 6))))
    light_mask = noise.point(lambda p: int(max(0, min(255, (p - 160) * 1.3 * strength * 6))))
    # composite dark
    tmp = Image.composite(dark_layer, img, dark_mask)
    # composite light
    result = Image.composite(light_layer, tmp, light_mask)
    # subtle overall blur to soften Worley edges
    result = result.filter(ImageFilter.GaussianBlur(radius=0.7))
    # blend result back over base at overall strength to keep subtlety
    # Actually result already contains base via masks, but blend 85% result + 15% base to soften
    from PIL import Image
    final = Image.blend(img, result, 0.88)
    return final

def _add_fibers(img, seed=0, strength=0.5):
    from PIL import Image, ImageDraw, ImageFilter
    import math, random
    rnd = random.Random(seed * 7919 + 3)
    size = img.size[0]
    grain = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    n = max(400, int(1100 * (size / 512) * strength))
    base_r, base_g, base_b = img.getpixel((size//2, size//2)) if hasattr(img, 'getpixel') else (200,200,200)
    for _ in range(n):
        x = rnd.randint(0, size)
        y = rnd.randint(0, size)
        length = rnd.randint(int(size*0.012), int(size*0.038))
        bias = (seed * 13) % 18 - 9
        angle = rnd.uniform(-10, 10) + bias
        rad = math.radians(angle)
        x2 = x + int(math.cos(rad) * length)
        y2 = y + int(math.sin(rad) * length)
        if rnd.random() < 0.52:
            col = (255, 255, 253, rnd.randint(9, 18))
        else:
            # shadow fiber
            col = (max(0, base_r - 28), max(0, base_g - 28), max(0, base_b - 28), rnd.randint(7, 14))
        gd.line([(x, y), (x2, y2)], fill=col, width=1)
    grain = grain.filter(ImageFilter.GaussianBlur(radius=0.55))
    return Image.alpha_composite(img.convert("RGBA"), grain).convert("RGB")

def build_experiment(size=512, out_root="Saved/Audit/choral_sheep/experiments"):
    from PIL import Image, ImageDraw
    out = Path(out_root).resolve()
    out.mkdir(parents=True, exist_ok=True)
    variants = ["flat", "worley12", "worley25", "worley12_fibers"]
    # Also add a saturated pop test: same but pastel sat 0.52 instead of 0.38
    # We'll generate a second sheet for saturation experiment
    rows = []
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue, sat=0.38, val=0.92)
        base_rgb = tuple(int(c*255) for c in base)
        accent_rgb = tuple(int(c*255) for c in accent)
        row_imgs = []
        # flat
        row_imgs.append(_flat(base_rgb, size))
        # worley 12
        row_imgs.append(_worley_mottle(base_rgb, accent_rgb, size, seed=pc*3+1, strength=0.12))
        # worley 25
        row_imgs.append(_worley_mottle(base_rgb, accent_rgb, size, seed=pc*3+1, strength=0.25))
        # worley 12 + fibers
        w12 = _worley_mottle(base_rgb, accent_rgb, size, seed=pc*3+1, strength=0.12)
        row_imgs.append(_add_fibers(w12, seed=pc*7+11, strength=1.0))
        rows.append((label, pc, row_imgs))

    # Super sheet: rows = PCs, cols = variants
    cols_n = len(variants)
    rows_n = len(rows)
    thumb = size // 2  # sheet thumbnails to keep sheet readable
    # Resize rows_imgs to thumb for sheet
    sheet_w = cols_n * thumb
    sheet_h = rows_n * thumb + 36  # header + footer
    sheet = Image.new("RGB", (sheet_w, sheet_h), (22, 22, 22))
    draw = ImageDraw.Draw(sheet)
    # header
    header_labels = ["01 Flat (shipping albedo)", "02 Worley 12% (Houdini intent)", "03 Worley 25% (editorial pop)", "04 Worley 12% + fibers"]
    for ci, h in enumerate(header_labels):
        x = ci * thumb
        try: draw.text((x + 6, 4), h, fill=(230, 230, 230))
        except: pass
    # paste
    for ri, (label, pc, imgs) in enumerate(rows):
        y0 = 20 + ri * thumb
        for ci, im in enumerate(imgs):
            thumb_im = im.resize((thumb, thumb), Image.LANCZOS)
            sheet.paste(thumb_im, (ci * thumb, y0))
        # row label on left edge
        try: draw.text((4, y0 + thumb - 14), f"PC{pc:02d} {label}", fill=(255, 255, 255))
        except: pass
        # separator
        draw.line([(0, y0), (sheet_w, y0)], fill=(50, 50, 50), width=1)
    # footer note
    try:
        draw.text((6, sheet_h - 16), "Experiment: flat vs subtle Worley vs editorial vs fibers — albedos only, no lighting. Groom/Normal/Sheen will carry wool in UE.", fill=(180, 180, 180))
    except: pass
    sheet_path = out / "_EXPERIMENT_WoolLab_SuperSheet.png"
    sheet.save(sheet_path, "PNG")
    print(f"[lab] super sheet -> {sheet_path} {sheet_w}x{sheet_h}")

    # Also save per-PC 2x2 comparison strips for close inspection (for E, Fs, B as heroes)
    for label in ["E", "Fs", "B"]:
        pc = next(pc for pc,(lab,_) in PITCH_CLASS_HUES.items() if lab==label)
        base, accent = _pastel_pair(PITCH_CLASS_HUES[pc][1], sat=0.38, val=0.92)
        base_rgb = tuple(int(c*255) for c in base)
        accent_rgb = tuple(int(c*255) for c in accent)
        flat = _flat(base_rgb, size)
        w12 = _worley_mottle(base_rgb, accent_rgb, size, seed=pc*3+1, strength=0.12)
        w25 = _worley_mottle(base_rgb, accent_rgb, size, seed=pc*3+1, strength=0.25)
        w12f = _add_fibers(w12.copy(), seed=pc*7+11, strength=1.0)
        strip = Image.new("RGB", (size*4, size + 24), (30, 30, 30))
        for i, im in enumerate([flat, w12, w25, w12f]):
            strip.paste(im, (i*size, 0))
            try:
                ImageDraw.Draw(strip).text((i*size+8, size+4), ["flat","worley12","worley25","worley12+fibers"][i], fill=(240,240,240))
            except: pass
        strip_path = out / f"_COMPARE_PC{pc:02d}_{label}.png"
        strip.save(strip_path, "PNG")
        print(f"[lab] {label} strip -> {strip_path}")

    # Saturation pop experiment sheet: compare sat 0.38 vs 0.52 at Worley12
    sat_sheet = Image.new("RGB", (thumb*2, thumb*len(rows)+24), (22,22,22))
    sd = ImageDraw.Draw(sat_sheet)
    try: sd.text((6,4), "LEFT: pastel 0.38 (current)  |  RIGHT: pop 0.52 (Infinity Nikki test) — both Worley12", fill=(230,230,230))
    except: pass
    for ri, (label, pc, _) in enumerate(rows):
        hue = PITCH_CLASS_HUES[pc][1]
        b38, a38 = _pastel_pair(hue, sat=0.38, val=0.92)
        b52, a52 = _pastel_pair(hue, sat=0.52, val=0.92)
        b38rgb = tuple(int(c*255) for c in b38); a38rgb = tuple(int(c*255) for c in a38)
        b52rgb = tuple(int(c*255) for c in b52); a52rgb = tuple(int(c*255) for c in a52)
        left = _worley_mottle(b38rgb, a38rgb, thumb, seed=pc*3+1, strength=0.12)
        right = _worley_mottle(b52rgb, a52rgb, thumb, seed=pc*3+1, strength=0.12)
        y0 = 18 + ri * thumb
        sat_sheet.paste(left, (0, y0))
        sat_sheet.paste(right, (thumb, y0))
        try: sd.text((4, y0+thumb-14), f"PC{pc:02d} {label}", fill=(255,255,255))
        except: pass
    sat_path = out / "_EXPERIMENT_Saturation_Pop.png"
    sat_sheet.save(sat_path, "PNG")
    print(f"[lab] saturation -> {sat_path}")

    # Write manifest
    import json
    (out / "experiment_manifest.json").write_text(json.dumps({
        "size": size, "variants": variants,
        "super_sheet": str(sheet_path), "saturation_sheet": str(sat_path),
        "note": "flat = shipping albedo intent; worley12 = Houdini COP Worley approximation at 12%; worley25 = editorial; fibers = directional grain. Choose one to promote to houdini_variants/"
    }, indent=2), encoding="utf-8")
    print(f"[lab] done — {out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--out", default="Saved/Audit/choral_sheep/experiments")
    args = ap.parse_args()
    build_experiment(size=args.size, out_root=args.out)
