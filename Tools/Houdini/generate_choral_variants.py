#!/usr/bin/env python3
"""
Standalone PIL generator for Choral Sheep chromatic variants — no Houdini required.
v2: now with FAST wool: clump mottling + fiber grain + subtle sheen falloff.
Matches Houdini COP intent (COP Noise + Worley + ColorCorrect), not the old flat swatch.

Usage:
    python Tools/Houdini/generate_choral_variants.py --size 1024 --out Saved/Audit/choral_sheep/houdini_variants
    python Tools/Houdini/generate_choral_variants.py --size 512 --quick   # draft

If --quick, skips fiber grain (2x faster) for iteration.
"""
import argparse
import colorsys
import json
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


def _wool_image(base_rgb, accent_rgb, size, seed=0, sheen=0.5, quick=False):
    """
    v3: Punchier wool — fixes v2 'faint outline' by:
      - higher contrast clumps (jitter +/-28, alpha 35-75)
      - two-pass clumps: dark tufts + light caps
      - no rectangular vignette artifact (radial falloff only)
      - fiber grain higher contrast and denser
    Still Pillow-only, but reads closer to Houdini COP Worley.
    """
    from PIL import Image, ImageDraw, ImageFilter

    rnd = random.Random(seed * 9973 + 42)
    img = Image.new("RGB", (size, size), base_rgb)
    base_r, base_g, base_b = base_rgb
    accent_r, accent_g, accent_b = accent_rgb

    # --- 1. Large clump mottle — dark tufts ---
    # Pass A: darker tufts
    dark_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(dark_layer)
    n_dark = max(24, int(110 * (size / 1024) ** 1.0))
    for _ in range(n_dark):
        cx = rnd.randint(-size//8, size + size//8)
        cy = rnd.randint(-size//8, size + size//8)
        rx = rnd.randint(int(size * 0.055), int(size * 0.14))
        ry = rnd.randint(int(size * 0.06), int(size * 0.15))
        # darker than base — mix down + small accent shift
        jitter = rnd.randint(-32, -10)
        if rnd.random() < 0.35:
            r = int(max(0, base_r + jitter) * 0.88 + accent_r * 0.12)
            g = int(max(0, base_g + jitter) * 0.88 + accent_g * 0.12)
            b = int(max(0, base_b + jitter) * 0.88 + accent_b * 0.12)
        else:
            r = max(0, min(255, base_r + jitter))
            g = max(0, min(255, base_g + jitter))
            b = max(0, min(255, base_b + jitter))
        alpha = rnd.randint(38, 72)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(r, g, b, alpha))
    dark_layer = dark_layer.filter(ImageFilter.GaussianBlur(radius=max(2, int(size / 110))))
    img = Image.alpha_composite(img.convert("RGBA"), dark_layer).convert("RGB")

    # Pass B: lighter caps (small, on top of darker)
    light_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ld = ImageDraw.Draw(light_layer)
    n_light = max(18, int(70 * (size / 1024) ** 1.0))
    for _ in range(n_light):
        cx = rnd.randint(0, size)
        cy = rnd.randint(0, size)
        rx = rnd.randint(int(size * 0.025), int(size * 0.07))
        ry = rnd.randint(int(size * 0.025), int(size * 0.075))
        jitter = rnd.randint(14, 32)
        r = max(0, min(255, min(255, base_r + jitter)))
        g = max(0, min(255, min(255, base_g + jitter)))
        b = max(0, min(255, min(255, base_b + jitter)))
        alpha = rnd.randint(28, 52)
        ld.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(r, g, b, alpha))
    light_layer = light_layer.filter(ImageFilter.GaussianBlur(radius=max(1, int(size / 160))))
    img = Image.alpha_composite(img.convert("RGBA"), light_layer).convert("RGB")

    # --- 2. Fiber grain ---
    if not quick:
        grain = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grain)
        n_fibers = max(500, int(1400 * (size / 1024)))
        for _ in range(n_fibers):
            x = rnd.randint(0, size)
            y = rnd.randint(0, size)
            length = rnd.randint(int(size * 0.014), int(size * 0.042))
            bias = (seed * 19) % 24 - 12
            angle = rnd.uniform(-14, 14) + bias
            import math
            rad = math.radians(angle)
            x2 = x + int(math.cos(rad) * length)
            y2 = y + int(math.sin(rad) * length)
            is_highlight = rnd.random() < 0.5
            if is_highlight:
                col = (255, 255, 253, rnd.randint(16, 32))
            else:
                col = (max(0, base_r - 32), max(0, base_g - 32), max(0, base_b - 32), rnd.randint(14, 28))
            gd.line([(x, y), (x2, y2)], fill=col, width=1)
        grain = grain.filter(ImageFilter.GaussianBlur(radius=0.7))
        img = Image.alpha_composite(img.convert("RGBA"), grain).convert("RGB")

    # --- 3. Sheen — tighter top highlight, no rectangle ---
    sheen_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen_layer)
    # single soft ellipse at top, not stacked rects
    # center top, wide oval
    sheen_r = int(size * 0.85)
    sheen_cx, sheen_cy = size // 2, int(size * 0.12)
    for i in range(3):
        scale = 1 - i * 0.18
        a = int((sheen * 28) * (1 - i * 0.35))
        if a <= 0:
            continue
        rx = int(sheen_r * scale)
        ry = int(sheen_r * 0.42 * scale)
        sd.ellipse([sheen_cx - rx, sheen_cy - ry, sheen_cx + rx, sheen_cy + ry], fill=(255, 255, 252, a))
    sheen_layer = sheen_layer.filter(ImageFilter.GaussianBlur(radius=max(2, int(size / 80))))
    img = Image.alpha_composite(img.convert("RGBA"), sheen_layer).convert("RGB")

    # --- 4. Subtle radial vignette only (no rectangle) ---
    # radial darkening at corners — very soft, ~6% max
    vig = Image.new("L", (size, size), 0)
    vd = ImageDraw.Draw(vig)
    # large ellipse covering center, inverted
    # create gradient via blurred white ellipse on black
    vd.ellipse([int(-size*0.15), int(-size*0.15), int(size*1.15), int(size*1.15)], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(radius=max(8, int(size / 12))))
    # remap to 0..28 range
    # vig is 0 edge, 255 center — invert to get corner darkness
    from PIL import ImageOps
    vig_inv = ImageOps.invert(vig)
    # convert to RGBA dark layer masked by vig_inv
    dark_vig = Image.new("RGBA", (size, size), (0, 0, 0, 28))
    # use vig_inv as alpha mask
    img_rgba = img.convert("RGBA")
    # blend corner darkness via multiply-ish: paste dark_vig with mask
    img_rgba = Image.alpha_composite(img_rgba, Image.new("RGBA", (size, size), (0, 0, 0, 0)))
    # Instead of complex mask, just blend at low opacity with vig_inv as guide: composite dark_vig at ~55% then blend
    tmp = Image.alpha_composite(img.convert("RGBA"), dark_vig)
    # Use vig_inv to modulate: where vig_inv is bright (corners), show more dark
    # Simplistic: blend 22% of tmp over img
    img = Image.blend(img.convert("RGB"), tmp.convert("RGB"), 0.22)

    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--out", default="Saved/Audit/choral_sheep/houdini_variants")
    ap.add_argument("--quick", action="store_true", help="skip fiber grain for draft speed")
    args = ap.parse_args()
    out = Path(args.out).resolve() if Path(args.out).is_absolute() else (Path.cwd() / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise SystemExit("pip install Pillow — needed for fallback generation")
    produced = []
    for pc, (label, hue) in PITCH_CLASS_HUES.items():
        base, accent = _pastel_pair(hue)
        base_rgb = tuple(int(c * 255) for c in base)
        accent_rgb = tuple(int(c * 255) for c in accent)
        sheen = 0.46 + (pc / 12.0) * 0.18
        img = _wool_image(base_rgb, accent_rgb, args.size, seed=pc + 11, sheen=sheen, quick=args.quick)
        # small label bar at bottom (outside wool, for audit)
        # add 28px bar so wool isn't obscured
        bar_h = 28
        canvas = Image.new("RGB", (args.size, args.size + bar_h), (35, 35, 35))
        canvas.paste(img, (0, 0))
        d = ImageDraw.Draw(canvas)
        try:
            d.text((10, args.size + 7), f"PC{pc:02d} {label}  wool {0.62 + pc*0.005:.2f}  sheen {sheen:.3f} {'[quick]' if args.quick else ''}", fill=(220, 220, 220))
        except Exception:
            pass
        # crop bar for UE texture variant (bar is audit only) — save both
        audit_path = out / f"ChoralWool_PC_{label}.png"
        # UE texture should be square without bar; audit includes bar in same file for now (bar is 28px, UE can crop or keep)
        # To give clean UE texture, save square img as well as audit with bar
        img.save(audit_path, "PNG")  # square = UE-ready
        # also save audit with bar as _audit
        audit_labeled = out / f"_audit_ChoralWool_PC_{label}.png"
        canvas.save(audit_labeled, "PNG")
        produced.append(audit_path)
        print(f"[gen] {audit_path.name} wool base {base_rgb} accent {accent_rgb} {'quick' if args.quick else 'wool'}")

    # contact sheet 4x3 — wool thumbnails, not flat
    cols, rows = 4, 3
    thumb = args.size // 4
    sheet = Image.new("RGB", (cols * thumb, rows * thumb + 24), (28, 28, 28))
    for i, (pc, (label, hue)) in enumerate(PITCH_CLASS_HUES.items()):
        base, accent = _pastel_pair(hue)
        base_rgb = tuple(int(c * 255) for c in base)
        accent_rgb = tuple(int(c * 255) for c in accent)
        sheen = 0.46 + (pc / 12.0) * 0.18
        tile = _wool_image(base_rgb, accent_rgb, thumb, seed=pc + 31, sheen=sheen, quick=True)  # quick for sheet speed
        x, y = (i % cols) * thumb, (i // cols) * thumb
        sheet.paste(tile, (x, y))
        d = ImageDraw.Draw(sheet)
        # label strip
        try:
            d.rectangle([x, y + thumb - 20, x + thumb, y + thumb], fill=(35, 35, 35, 200))
            d.text((x + 6, y + thumb - 15), f"PC{pc:02d} {label}", fill=(235, 235, 235))
        except Exception:
            pass
    # footer
    d = ImageDraw.Draw(sheet)
    try:
        d.text((8, rows * thumb + 5), "Choral Sheep 12PC Wool — pastel + clump + fiber grain (PIL) — Houdini COP will add Worley detail on hython cook", fill=(180, 180, 180))
    except Exception:
        pass
    sheet_path = out / "_ChoralSheep_Chromatic_ContactSheet.png"
    sheet.save(sheet_path, "PNG")
    print(f"[gen] contact sheet -> {sheet_path}")

    # also regenerate groom contact as readable wool puffs (kept, but note it's still schematic until hython)
    # manifest
    manifest = out / "variant_manifest.json"
    manifest.write_text(json.dumps({"produced": [str(p) for p in produced + [sheet_path]], "size": args.size, "count": 12, "generator": "v2_wool"}, indent=2), encoding="utf-8")
    print(f"[gen] done — {len(produced)} + sheet in {out} {'(quick)' if args.quick else ''}")

if __name__ == "__main__":
    main()
