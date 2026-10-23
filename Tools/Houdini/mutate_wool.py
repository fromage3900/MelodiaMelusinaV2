#!/usr/bin/env python3
"""
Stateless wool mutation + render + score — one task, zero state.

Used by overnight_orchestrator.py for each wool_evolve task.

Input (via args or stdin JSON):
  {
    "mode": "B_worley12",
    "pc": 4,
    "params": {"worley": 0.12, "sat": 0.38, "glow": 0.09, "fibers": 0.0, "hue_shift": 0.0},
    "mutation": {"worley": +0.02, "sat": 0.0}
  }

Output (stdout JSON):
  {
    "mode": "B_worley12",
    "pc": 4,
    "new_params": {...},
    "render_path": "Saved/Audit/overnight/generation_001/renders/B_worley12_PC04_E.png",
    "scores": {"wool_reading": 7.2, "glow_subtlety": 8.1, "nissi_softness": 7.8, "uv_stability": 9.0, "emission_balance": 7.5},
    "promoted": false
  }

Run:
  python Tools/Houdini/mutate_wool.py --mode B_worley12 --pc 4 --params '{"worley":0.12,"sat":0.38,"glow":0.09}' --mutation '{"worley":0.02}'
  # or piped JSON:
  echo '{"mode":"B_worley12","pc":4,"params":...}' | python Tools/Houdini/mutate_wool.py
"""
import argparse
import colorsys
import json
import random
import sys
from pathlib import Path

# Reuse the sculpted source (your exported choralsheepbase)
SRC_BASE = Path("Content/Melodia/Companions/ChoralSheep/choralsheepbase_BaseColor.png")

PITCH_CLASS_HUES = {
    0: ("C", 0.000), 1: ("Cs", 0.083), 2: ("D", 0.167), 3: ("Ds", 0.250),
    4: ("E", 0.333), 5: ("F", 0.417), 6: ("Fs", 0.500), 7: ("G", 0.583),
    8: ("Gs", 0.667), 9: ("A", 0.750), 10: ("As", 0.833), 11: ("B", 0.917),
}
MODE_DEFAULTS = {
    "A_flat":       {"worley": 0.00, "sat": 0.38, "glow": 0.09, "fibers": 0.0, "hue_shift": 0.0},
    "B_worley12":   {"worley": 0.12, "sat": 0.38, "glow": 0.09, "fibers": 0.0, "hue_shift": 0.0},
    "C_worley25":   {"worley": 0.25, "sat": 0.38, "glow": 0.09, "fibers": 0.0, "hue_shift": 0.0},
    "D_pop_worley12": {"worley": 0.12, "sat": 0.52, "glow": 0.09, "fibers": 0.0, "hue_shift": 0.0},
}

PARAM_BOUNDS = {
    "worley": (0.0, 0.30),
    "sat": (0.35, 0.55),
    "glow": (0.04, 0.18),
    "fibers": (0.0, 1.0),
    "hue_shift": (-5.0, 5.0),  # degrees
}

def _pastel_pair(hue, sat=0.38, val=0.92):
    base = colorsys.hsv_to_rgb(hue, sat * 0.55, val)
    accent = colorsys.hsv_to_rgb(hue, sat, min(1.0, val * 1.06))
    return base, accent

def _load_source(size):
    from PIL import Image
    base = Image.open(SRC_BASE).convert("RGB")
    if base.size != (size, size):
        base = base.resize((size, size), Image.LANCZOS)
    gray = base.convert("L")
    return base, gray

def _tint_sculpt(base_img, gray_img, pastel_rgb, size):
    from PIL import Image
    pr, pg, pb = pastel_rgb
    dark = (int(pr*0.78), int(pg*0.78), int(pb*0.78))
    light = (int(min(255, pr*1.12)), int(min(255, pg*1.12)), int(min(255, pb*1.12)))
    dark_im = Image.new("RGB", (size, size), dark)
    light_im = Image.new("RGB", (size, size), light)
    tinted = Image.composite(light_im, dark_im, gray_img)
    final = Image.blend(base_img, tinted, 0.78)
    return final

def _worley_mottle(img, pastel_accent_rgb, size, seed, strength):
    if strength <= 0.001:
        return img
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    rnd = random.Random(seed * 1013 + 7)
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
    dark_im = ImageEnhance.Brightness(img).enhance(0.86)
    light_im = ImageEnhance.Brightness(img).enhance(1.12)
    ar, ag, ab = pastel_accent_rgb
    accent_tint = Image.new("RGB", (size, size), (ar, ag, ab))
    light_im = Image.blend(light_im, accent_tint, 0.07)
    dark_mask = noise.point(lambda p: int(max(0, min(255, (112 - p) * 1.5 * strength * 5))))
    light_mask = noise.point(lambda p: int(max(0, min(255, (p - 158) * 1.4 * strength * 5))))
    tmp = Image.composite(dark_im, img, dark_mask)
    result = Image.composite(light_im, tmp, light_mask)
    result = result.filter(ImageFilter.GaussianBlur(radius=0.6))
    final = Image.blend(img, result, 0.88)
    return final

def _make_glow_map(base_gray, size, seed, accent_rgb, glow_strength):
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    rnd = random.Random(seed * 2027 + 99)
    glow_mask = base_gray.point(lambda p: int(max(0, min(255, (p - 165) * 2.2))))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(radius=max(3, int(size/36))))
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
    glow_mask = ImageChops.add(glow_mask, orb_layer)
    glow_mask = glow_mask.point(lambda p: min(255, int(p * glow_strength * 9)))
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(radius=max(2, int(size/48))))
    ar, ag, ab = accent_rgb
    glow_rgb = Image.new("RGB", (size, size), (ar, ag, ab))
    black = Image.new("RGB", (size, size), (0,0,0))
    glow = Image.composite(glow_rgb, black, glow_mask)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=1))
    return glow

def _fake_lit_sphere(albedo, size):
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    # radial Lambert with top-left light
    light = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(light)
    cx, cy, r = size//2, size//2, size//2 - 4
    for rad in range(r, 0, -6):
        t = rad / r
        bright = int(210 + 45 * (1 - t)**0.7)
        d.ellipse([cx-rad, cy-rad-4, cx+rad, cy+rad-4], fill=bright)
    light = light.filter(ImageFilter.GaussianBlur(radius=4))
    lit = ImageChops.multiply(albedo, Image.merge('RGB', [light, light, light]))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([cx-r, cy-r, cx+r, cy+r], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1))
    out = Image.new("RGB", (size, size), (22, 22, 22))
    out.paste(lit, mask=mask)
    return out

def _score_heuristic(albedo_path, glow_path, mode, pc):
    """PIL heuristic scores (0-10) for automated feedback.
    These are rough proxies; real scoring uses your eye on the sheet.
    """
    from PIL import Image
    try:
        alb = Image.open(albedo_path).convert("RGB")
        glw = Image.open(glow_path).convert("RGB")
    except Exception:
        return {k: 5.0 for k in ["wool_reading", "glow_subtlety", "nissi_softness", "uv_stability", "emission_balance"]}
    # 1. wool_reading: variance in albedo (more texture = more wool-like)
    # compute local stddev in 16x16 windows
    import numpy as np
    arr = np.array(alb)
    # simple variance of luma
    luma = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
    var = float(np.var(luma))
    wool = min(10, var / 200)  # calibrate
    # 2. glow_subtlety: glow mean brightness low but non-zero
    glw_arr = np.array(glw)
    glw_luma = 0.299*glw_arr[:,:,0] + 0.587*glw_arr[:,:,1] + 0.114*glw_arr[:,:,2]
    glow_mean = float(np.mean(glw_luma))
    glow_sub = max(0, 10 - glow_mean / 15)  # lower mean = more subtle
    # 3. nissi_softness: saturation of albedo (lower = more Nikki)
    sat = np.std(arr, axis=2).mean()
    nissi = max(0, 10 - sat / 8)
    # 4. uv_stability: assume good if no obvious stretching (placeholder)
    uv = 9.0
    # 5. emission_balance: glow color harmony with albedo
    # accent hue vs base hue similarity
    alb_mean = arr.mean(axis=(0,1))
    glw_mean = glw_arr.mean(axis=(0,1))
    # hue difference in HSV
    def rgb2hue(r,g,b):
        r,g,b = r/255, g/255, b/255
        mx, mn = max(r,g,b), min(r,g,b)
        if mx == mn: return 0
        df = mx - mn
        if mx == r: h = (60 * ((g-b)/df) + 360) % 360
        elif mx == g: h = (60 * ((b-r)/df) + 120) % 360
        else: h = (60 * ((r-g)/df) + 240) % 360
        return h
    h1 = rgb2hue(*alb_mean)
    h2 = rgb2hue(*glw_mean)
    dh = min(abs(h1-h2), 360-abs(h1-h2))
    emission = max(0, 10 - dh / 20)
    return {
        "wool_reading": round(wool, 1),
        "glow_subtlety": round(glow_sub, 1),
        "nissi_softness": round(nissi, 1),
        "uv_stability": round(uv, 1),
        "emission_balance": round(emission, 1),
    }

def mutate_params(params, mutation):
    """Apply mutation, clamp to bounds."""
    new = params.copy()
    for k, delta in mutation.items():
        if k in new:
            new[k] = new[k] + delta
        else:
            new[k] = delta
    # clamp
    for k, (lo, hi) in PARAM_BOUNDS.items():
        if k in new:
            new[k] = max(lo, min(hi, new[k]))
    return new

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True)
    ap.add_argument("--pc", type=int, required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--mutation", required=True)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--gen", type=int, default=0)
    ap.add_argument("--out-root", default="Saved/Audit/overnight")
    args = ap.parse_args()

    params = json.loads(args.params)
    mutation = json.loads(args.mutation)
    new_params = mutate_params(params, mutation)

    # Determine mode defaults and merge
    base = MODE_DEFAULTS.get(args.mode, MODE_DEFAULTS["B_worley12"]).copy()
    base.update(new_params)
    params = base

    pc = args.pc
    label, hue = PITCH_CLASS_HUES[pc]
    # Apply hue shift
    hue = (hue + params.get("hue_shift", 0.0) / 360.0) % 1.0
    pastel_base, pastel_accent = _pastel_pair(hue, sat=params["sat"], val=0.92)
    prgb = tuple(int(c*255) for c in pastel_base)
    argb = tuple(int(c*255) for c in pastel_accent)

    size = args.size
    base_src, gray_src = _load_source(size)

    # Generate albedo
    albedo = _tint_sculpt(base_src, gray_src, prgb, size)
    albedo = _worley_mottle(albedo, argb, size, seed=pc*3+7, strength=params["worley"])

    # Generate glow
    glow = _make_glow_map(gray_src, size, seed=pc*5+13, accent_rgb=argb, glow_strength=params["glow"])

    # Lit render
    lit = _fake_lit_sphere(albedo, size)

    # Output paths
    out_root = Path(args.out_root) / f"generation_{args.gen:03d}" / "renders"
    out_root.mkdir(parents=True, exist_ok=True)
    albedo_path = out_root / f"{args.mode}_PC{pc:02d}_{label}.png"
    glow_path = out_root / f"glow_{args.mode}_PC{pc:02d}_{label}.png"
    lit_path = out_root / f"lit_{args.mode}_PC{pc:02d}_{label}.png"

    albedo.save(albedo_path, "PNG")
    glow.save(glow_path, "PNG")
    lit.save(lit_path, "PNG")

    # Score
    scores = _score_heuristic(albedo_path, glow_path, args.mode, pc)

    # Promoted if all >= 8.5 (heuristic)
    promoted = all(v >= 8.5 for v in scores.values())

    result = {
        "mode": args.mode,
        "pc": pc,
        "label": label,
        "params": params,
        "mutation": mutation,
        "render": str(lit_path),
        "albedo": str(albedo_path),
        "glow": str(glow_path),
        "scores": scores,
        "promoted": promoted,
        "size": size,
    }
    sys.stdout.write(json.dumps(result))

if __name__ == "__main__":
    main()