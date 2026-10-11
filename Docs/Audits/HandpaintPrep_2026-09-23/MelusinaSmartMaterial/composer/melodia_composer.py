#!/usr/bin/env python
"""Melodia Composer — MIDI -> SMS variant parameters + score maps.

The Composer reads a MIDI theme and produces, for N musical variants:

  * out/composer_params.json      — per-variant SMS parameter set for Painter
  * out/score_<Name>.png          — piano-roll MASKS (white notes on black)
  * out/sheet_<Name>.png          — pretty notation sheets for humans
  * out/ContactSheet_MrSheep_Scores_<date>.png — all variants, one page

The Painter-side runner (melodia_build_sms_composer.py) consumes the JSON:
each variant's mask becomes a score-engrave folder in the SMS stack, and the
parameter set retunes the existing SMS layers. Variant names are musical
transforms of the theme, computed from the real notes — nothing invented.

Melodia / Melusina naming only. No Grok*.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import random

import mido
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ----------------------------------------------------------------- palette
CREAM = (245, 236, 215)        # paper
CEDAR = (139, 94, 60)          # ink
CEDAR_DARK = (96, 62, 38)
ACCENT = (255, 201, 120)       # glow
NAVY = (30, 26, 46)

# ------------------------------------------------------------------ notes


def load_notes(path: str):
    """Return (notes, ticks_per_beat, length_beats) from a MIDI file.
    notes = list of dicts: start, dur, pitch, vel  (times in beats)"""
    mid = mido.MidiFile(path)
    tpb = mid.ticks_per_beat
    notes = []
    for track in mid.tracks:
        t = 0
        active = {}
        for msg in track:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                active.setdefault(msg.note, []).append((t, msg.velocity))
            elif msg.type in ("note_off",) or (msg.type == "note_on"
                                               and msg.velocity == 0):
                if active.get(msg.note):
                    st, vel = active[msg.note].pop(0)
                    notes.append({"start": st / tpb, "dur": max(
                        0.05, (t - st) / tpb), "pitch": msg.note,
                        "vel": vel / 127.0})
    notes.sort(key=lambda n: (n["start"], n["pitch"]))
    if not notes:
        raise SystemExit(f"no notes found in {path}")
    length = max(n["start"] + n["dur"] for n in notes)
    return notes, tpb, length


# --------------------------------------------------------------- variants


def transform(notes, kind, rng=None):
    """Musical transforms — each is an honest variation of the theme.
    rng (optional) seeds per-run variation of the transform parameters so
    Night Shift pages differ night to night."""
    out = [dict(n) for n in notes]

    def pick(options, default):
        if rng is None:
            return default
        return rng.choice(options)

    if kind == "verse":
        return out
    if kind == "inversion":
        offset = pick([-2, -1, 0, 1, 2], 0)
        anchor = round(sum(n["pitch"] for n in notes) / len(notes)) + offset
        for n in out:
            n["pitch"] = max(24, min(108, 2 * anchor - n["pitch"]))
        return sorted(out, key=lambda n: (n["start"], n["pitch"]))
    if kind == "moonlight":                      # interval down, softened
        iv = pick([2, 3, 4, 5], 3)
        for n in out:
            n["pitch"] = max(24, n["pitch"] - iv)
            n["vel"] *= 0.85
        return out
    if kind == "ember":                          # hotter, shorter strokes
        heat = pick([1.15, 1.25, 1.4], 1.25)
        for n in out:
            n["vel"] = min(1.0, n["vel"] * heat)
            n["dur"] *= 0.8
        return out
    if kind == "lullaby":                        # sparser, longer
        stride = pick([2, 3], 2)
        out = [n for i, n in enumerate(out) if i % stride == 0]
        for n in out:
            n["dur"] *= 1.6
            n["vel"] *= 0.9
        return out
    if kind == "storm":                          # doubling
        iv = pick([7, 12, 12, 12], 12)
        prob = pick([0.5, 0.65, 0.8, 1.0], 1.0)
        dup = [dict(n, pitch=min(108, n["pitch"] + iv),
                    vel=n["vel"] * 0.75) for n in out
               if rng is None or rng.random() <= prob]
        return sorted(out + dup, key=lambda n: (n["start"], n["pitch"]))
    raise SystemExit(f"unknown transform {kind}")


def window(notes, t0, t1):
    return [n for n in notes
            if n["start"] < t1 and n["start"] + n["dur"] > t0]


def features(notes, t0, t1):
    span = max(1e-6, t1 - t0)
    n = len(notes)
    if not n:
        return dict(density=0.0, mean_vel=0.5, vel_range=0.0, contour=0.0,
                    pitch_min=60, pitch_max=72, bright=0.5, key_pc=0,
                    mode="major")
    beats = span
    density = n / beats
    vels = [x["vel"] for x in notes]
    mean_vel = sum(vels) / n
    vel_range = max(vels) - min(vels)
    # linear regression of pitch over time -> contour slope (semitones/beat)
    xs = [(x["start"] + 0.5 * x["dur"] - t0) for x in notes]
    ys = [x["pitch"] for x in notes]
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((x - mx) ** 2 for x in xs) or 1e-6
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    contour = max(-1.0, min(1.0, slope))
    pitch_min, pitch_max = min(ys), max(ys)
    bright = sum(1 for y in ys if y >= 64) / n
    # weighted pitch-class histogram -> key guess
    hist = [0.0] * 12
    for x in notes:
        hist[x["pitch"] % 12] += x["vel"] * x["dur"]
    key_pc = hist.index(max(hist))
    maj3 = hist[(key_pc + 4) % 12]
    min3 = hist[(key_pc + 3) % 12]
    mode = "major" if maj3 >= min3 else "minor"
    return dict(density=density, mean_vel=mean_vel, vel_range=vel_range,
                contour=contour, pitch_min=pitch_min, pitch_max=pitch_max,
                bright=bright, key_pc=key_pc, mode=mode)


def norm(value, lo, hi):
    if hi <= lo:
        return 0.5
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def rotate_hue(rgb, deg):
    """Rotate an RGB triple's hue in HSV space (per-variant accent identity)."""
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[max(0.0, min(1.0, c)) for c in rgb])
    h = (h + deg / 360.0) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return [round(r, 4), round(g, 4), round(b, 4)]


def params_from(feat, spread):
    """Map musical features -> SMS parameters (all clamped, documented)."""
    d = norm(feat["density"], spread["density"][0], spread["density"][1])
    v = norm(feat["mean_vel"], spread["vel"][0], spread["vel"][1])
    vr = norm(feat["vel_range"], 0.0, 0.9)
    c = 0.5 + 0.5 * feat["contour"]           # 0 falling .. 1 rising
    b = feat["bright"]
    # warm accent, cooled when minor / darker registers
    warm = (1.00, 0.79, 0.47)
    cool = (0.92, 0.95, 1.08)
    k = 0.75 - 0.5 * b + (0.15 if feat["mode"] == "minor" else 0.0)
    k = max(0.0, min(1.0, k))
    accent = tuple(max(0.0, min(1.0, warm[i] * (1 - k) + ACCENT[i] / 255.0
                                      * cool[i] * k)) for i in range(3))
    return {
        "accent": [round(x, 4) for x in accent],
        "roughness_base": round(0.42 + 0.26 * (1 - v), 3),
        "roughness_min": round(0.30 + 0.12 * (1 - v), 3),
        "roughness_max": round(0.62 + 0.14 * v, 3),
        "cavity_intensity": round(0.32 + 0.36 * (1 - d), 3),
        "decoration_intensity": round(0.22 + 0.46 * d, 3),
        "cym_intensity": round(0.18 + 0.34 * d, 3),
        "beat_emissive": round(0.26 + 0.42 * d, 3),
        "resonance_core": round(0.40 + 0.33 * v, 3),
        "moonglow_halo": round(0.24 + 0.30 * (1 - vr) + 0.10 * (1 - c), 3),
        "charm_flash": round(0.16 + 0.44 * b, 3),
        "grade_bottom": round(0.16 + 0.30 * (1 - c), 3),
        "grade_top": round(0.12 + 0.30 * c, 3),
        "score_engrave_op": round(0.34 + 0.30 * d, 3),
        "score_glow_op": round(min(0.95, 0.22 + 0.70 * d), 3),
        "wash_op": round(0.34 + 0.34 * d, 3),
        "tint_op": 0.32,
        "score_tint": [round(min(1.0, x * 1.06), 4) for x in accent],
    }


# ----------------------------------------------------------------- render


def _font(size):
    for cand in ("C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/segoeui.ttf"):
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ------------------------------------------------------- notation glyphs
HERE = os.path.dirname(os.path.abspath(__file__))
NOTE_FONT_PATH = None          # set by --note-font
_MF_CACHE = {}
_INK_CACHE = {}

# duration (beats) -> glyph, with a BMP fallback when the SMuFL codepoint
# is missing from the resolved font
NOTE_GLYPHS = {
    "whole":     ("\U0001D15D", "\u2669"),
    "half":      ("\U0001D15E", "\u2669"),
    "quarter":   ("\U0001D15F", "\u2669"),
    "eighth":    ("\U0001D160", "\u266A"),
    "sixteenth": ("\U0001D161", "\u266C"),
}


def _ink(f, ch):
    key = (id(f), ch)
    v = _INK_CACHE.get(key)
    if v is None:
        try:
            m = f.getmask(ch)
            v = sum(1 for x in m if x > 16)
        except Exception:
            v = 0
        _INK_CACHE[key] = v
    return v


def find_note_font(size):
    """Resolve the notation font (cached): --note-font > composer/fonts/ >
    user fonts named music/noto > Segoe UI Symbol (verified full coverage)."""
    import glob
    cands = []
    if NOTE_FONT_PATH:
        cands.append(NOTE_FONT_PATH)
    uf = os.path.join(os.path.expanduser("~"), "AppData", "Local",
                      "Microsoft", "Windows", "Fonts")
    for pat in ("*.otf", "*.ttf"):
        cands += sorted(glob.glob(os.path.join(HERE, "fonts", pat)))
        for fp in sorted(glob.glob(os.path.join(uf, pat))):
            low = os.path.basename(fp).lower()
            if "music" in low or "noto" in low:
                cands.append(fp)
    cands += ["C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/arial.ttf"]
    for fp in cands:
        try:
            f = ImageFont.truetype(fp, max(10, int(size)))
        except Exception:
            continue
        if _ink(f, "\u2669") > 60 and _ink(f, "\u266A") > 60:
            return f, fp
    return _font(max(10, int(size))), "fallback-sans"


def _music_font(size):
    key = int(size)
    if key not in _MF_CACHE:
        _MF_CACHE[key] = find_note_font(key)[0]
    return _MF_CACHE[key]


def _pick_glyph(f, dur):
    key = ("whole" if dur >= 3.5 else "half" if dur >= 1.5 else
           "quarter" if dur >= 0.7 else "eighth" if dur >= 0.3 else
           "sixteenth")
    first, fb = NOTE_GLYPHS[key]
    if _ink(f, first) > 60:
        return first
    if _ink(f, fb) > 60:
        return fb
    return "\u266A"


# ---------------------------------------------------- v2 canvases (SMS2)

def make_ramp(accent, path, w=1024, h=1024):
    """Vertical ombre ramp canvas (Nikki fade): deep plum shadow -> accent
    -> cream -> warm light. Drives SMS2 base colour per variant."""
    import colorsys

    def hexc(c):
        return tuple(int(round(255 * max(0.0, min(1.0, x)))) for x in c)

    a = hexc(accent)
    deep = tuple(max(0.0, min(1.0, x * 0.22 + 0.03)) for x in accent)
    # push the shadow end slightly violet for the fantasy grade
    deep = (deep[0] * 0.88 + 0.09, deep[1] * 0.75 + 0.02,
            min(1.0, deep[2] + 0.14))
    stops = [deep, tuple(accent), (0.97, 0.92, 0.84), (1.0, 0.98, 0.92)]
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        t *= (len(stops) - 1)
        i = min(len(stops) - 2, int(t))
        f = t - i
        c = [round((stops[i][k] * (1 - f) + stops[i + 1][k] * f) * 255)
             for k in range(3)]
        c = [max(0, min(255, v)) for v in c]
        for x in range(w):
            px[x, y] = tuple(c)
    img.save(path)
    return path


def make_iri(accent, path, w=2048, h=512):
    """Aurora sweep for SpecularEdgeColor / Coat (hue across U, slight
    value falloff downward) — the iridescence carrier."""
    shifts = [-120, -45, 40, 130]
    cols = [rotate_hue(accent, s) for s in shifts]
    img = Image.new("RGB", (w, h))
    px = img.load()
    for x in range(w):
        t = x / max(1, w - 1) * (len(cols) - 1)
        i = min(len(cols) - 2, int(t))
        f = t - i
        c = [cols[i][k] * (1 - f) + cols[i + 1][k] * f for k in range(3)]
        for y in range(h):
            v = 0.72 + 0.28 * (1 - y / max(1, h - 1)) * 0.9
            px[x, y] = tuple(int(max(0, min(255, round(255 * c[k] * v))))
                             for k in range(3))
    img.save(path)
    return path


def render_bold(notes, t0, t1, w, h, note_font=None):
    """Sparse READABLE notation band: one large glyph per 2-beat window
    (strongest note), white on black — the notes that must read on the
    sheep at render scale."""
    img = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(img)
    vis = [n for n in notes if t0 <= n["start"] < t1]
    if not vis:
        return img
    lo = min(n["pitch"] for n in vis) - 2
    hi = max(n["pitch"] for n in vis) + 2
    span = max(1, hi - lo)
    pad = 12
    fps = []
    t = t0
    while t < t1:
        chunk = [n for n in vis if t <= n["start"] < t + 2.0]
        if chunk:
            fps.append(max(chunk, key=lambda n: n["vel"]))
        t += 2.0
    for i, n in enumerate(fps):
        x = pad + (n["start"] - t0) / max(1e-6, t1 - t0) * (w - 2 * pad)
        y = pad + (hi - n["pitch"]) / span * (h - 2 * pad)
        fsz = 150
        nf = note_font if note_font is not None else _music_font(fsz)
        ch = _pick_glyph(nf, n["dur"])
        dr.text((x + fsz * 0.16, y), ch, font=nf, fill=255, anchor="mm")
    return img


def render_hero(notes, path, w=2048, h=2048):
    """Tier-1 hero band (chest zone): 5 staff lines + clef + giant motif
    notes. Placed at the UV zone the CHEST mesh part actually samples
    (u 0.635-0.911, v 0.001-0.224 -> rows 1589-2046). Five parallel lines
    + a clef read as 'music' at any distance."""
    img = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(img)
    x0, x1 = 1320, 1850
    y0 = 1795
    lines_y = [y0 + i * 22 for i in range(5)]
    for y in lines_y:
        dr.rectangle([x0, y, x1, y + 4], fill=200)
    try:
        clef_font = _music_font(150)
        dr.text((x0 + 45, lines_y[2] + 4), "\U0001D11E", font=clef_font,
                fill=255, anchor="mm")
    except Exception:
        pass
    if notes:
        length = max(n["start"] + n["dur"] for n in notes)
        k = 5
        picks = []
        for i in range(k):
            a = length * i / k
            b = length * (i + 1) / k
            chunk = [n for n in notes if a <= n["start"] < b]
            if chunk:
                picks.append(max(chunk, key=lambda n: n["vel"]))
        nf = _music_font(120)
        span_x = (x1 - x0 - 160)
        for i, n in enumerate(picks):
            fx = (x0 + 130 + span_x * i / max(1, len(picks) - 1)
                  if len(picks) > 1 else x0 + 160)
            fy = lines_y[1 + (i % 4)] - 4
            ch = _pick_glyph(nf, n["dur"])
            dr.text((fx, fy), ch, font=nf, fill=255, anchor="mm")
    img.save(path)
    return path


def render_roll(notes, t0, t1, w, h, pretty, vel_visible=True,
                title=None, pitch_range=None, style="note",
                note_font=None):
    """Piano-roll image. pretty=False -> crisp mask (white on black).
    pretty=True -> cream page, cedar notation, faint staff lines.
    pitch_range: optional fixed (lo, hi) so sibling variants share one
    pitch axis (transpositions stay visible)."""
    bg = CREAM if pretty else (0, 0, 0)
    ink = CEDAR_DARK if pretty else (255, 255, 255)
    img = Image.new("RGB", (w, h), bg)
    dr = ImageDraw.Draw(img)
    if pretty:
        for i in range(1, 12):
            y = int(h * i / 12)
            dr.line([(0, y), (w, y)], fill=(210, 196, 172), width=1)
        if title:
            dr.text((14, 8), title, font=_font(22), fill=CEDAR)
    vis = [n for n in notes if n["start"] < t1 and n["start"] + n["dur"] > t0]
    if not vis:
        return img
    if pitch_range is not None:
        lo, hi = pitch_range
    else:
        lo = min(n["pitch"] for n in vis) - 2
        hi = max(n["pitch"] for n in vis) + 2
    span = max(1, hi - lo)
    pad = 10
    for n in vis:
        x0 = pad + (n["start"] - t0) / max(1e-6, t1 - t0) * (w - 2 * pad)
        y1 = pad + (hi - n["pitch"]) / span * (h - 2 * pad)
        thick = max(6.0, (h - 2 * pad) / span * 0.62)
        y1 = max(pad, min(h - pad - thick, y1 - thick / 2))
        if pretty:
            col = ink
        else:
            g = int(140 + 115 * n["vel"]) if vel_visible else 255
            col = (g, g, g)
        if style == "note":
            # cap glyph width to the note spacing so dense runs stay read-
            # able instead of fusing into blobs; cap height inside the pad
            dx = (w - 2 * pad) / max(1, len(vis))
            fsz = max(12, int(min(thick * 2.4, dx * 2.6)))
            nf = note_font if note_font is not None else _music_font(fsz)
            ch = _pick_glyph(nf, n["dur"])
            # noteheads sit low-left in note glyphs: nudge so the head lands
            # on the pitch row and the stem/flag rises through it
            ty = min(y1 + thick * 0.58, h - pad - fsz * 0.55)
            dr.text((x0 + fsz * 0.16, ty), ch, font=nf,
                    fill=col, anchor="mm")
        else:
            x1 = x0 + max(6.0, n["dur"] / max(1e-6, t1 - t0) * (w - 2 * pad))
            dr.rounded_rectangle([x0, y1, min(w - pad, x1), y1 + thick],
                                 radius=3, fill=col)
    if pretty:
        img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img


def build_contact_sheet(cells, out_path, header, sub):
    """cells: list of (variant_name, PIL.Image). 3 x 2 layout."""
    cw, ch = 640, 300
    cols, rows = 3, 2
    margin, cap = 18, 56
    W = margin + cols * (cw + margin)
    H = 150 + rows * (ch + cap + margin)
    page = Image.new("RGB", (W, H), (24, 20, 34))
    dr = ImageDraw.Draw(page)
    dr.rectangle([0, 0, W, 108], fill=(32, 27, 46))
    dr.text((margin, 18), header, font=_font(34), fill=CREAM)
    dr.text((margin, 62), sub, font=_font(20), fill=ACCENT)
    for i, (name, img) in enumerate(cells):
        r, c = divmod(i, cols)
        x = margin + c * (cw + margin)
        y = 130 + r * (ch + cap + margin)
        page.paste(img.resize((cw, ch)), (x, y))
        dr.text((x + 2, y + ch + 8), name, font=_font(24), fill=CREAM)
    page.save(out_path)
    return out_path


# ------------------------------------------------------------------- main

VARIANTS = [
    ("Verse", "verse", "theme as written"),
    ("Inversion", "inversion", "melodic mirror — rising becomes falling"),
    ("Moonlight", "moonlight", "minor third down, softened — grief verse"),
    ("Ember", "ember", "hotter dynamics, shorter strokes — hearth verse"),
    ("Lullaby", "lullaby", "half notes, longer strokes — rest verse"),
    ("Storm", "storm", "octave doubling — the ensemble joins"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--midi", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", type=int, default=6)
    ap.add_argument("--windows", type=int, default=6,
                    help="musical windows sliced from the theme")
    ap.add_argument("--jitter-seed", type=int, default=None,
                    help="seed for per-run variation (Night Shift passes the "
                         "date; transforms + amplitudes vary, layout stays)")
    ap.add_argument("--note-style", choices=["note", "bar"], default="note",
                    help="draw notes as music glyphs (default) or classic bars")
    ap.add_argument("--note-font", default=None,
                    help="path to a notation font (default: auto — NotoMusic/"
                         "music-named user fonts, else Segoe UI Symbol)")
    args = ap.parse_args()
    global NOTE_FONT_PATH
    NOTE_FONT_PATH = args.note_font
    if args.note_style == "note":
        print("note font:", find_note_font(48)[1])

    os.makedirs(args.out, exist_ok=True)
    notes, tpb, length = load_notes(args.midi)
    print(f"theme: {len(notes)} notes, {length:.2f} beats")

    # window the theme uniformly -> per-window features/palette
    steps = min(args.windows, max(1, args.variants))
    bounds = [(length * i / steps, length * (i + 1) / steps)
              for i in range(steps)]
    win_feats = [features(window(notes, a, b), a, b) for a, b in bounds]
    density_all = [f["density"] for f in win_feats]
    vel_all = [f["mean_vel"] for f in win_feats]
    spread = dict(density=(min(density_all), max(density_all)),
                  vel=(min(vel_all), max(vel_all)))
    mid_feat = features(notes, 0.0, length)
    mid_feat["density"] = sum(density_all) / steps
    mid_feat["mean_vel"] = sum(vel_all) / steps
    base_params = params_from(mid_feat, spread)

    date = _dt.date.today().isoformat()
    theme_name = os.path.splitext(os.path.basename(args.midi))[0]
    variants_json = []
    cells = []
    rng = None
    if args.jitter_seed is not None:
        rng = random.Random(args.jitter_seed)
    var_list = list(VARIANTS[:args.variants])
    if rng is not None:
        rng.shuffle(var_list)
    # Render all score maps on ONE shared pitch axis so transpositions
    # (e.g. Moonlight's minor-3rd shift) stay visible instead of being
    # silently re-normalized away by per-image ranges.
    all_vnotes = {name: transform(notes, kind, rng)
                  for name, kind, desc in var_list}
    pitch_range = (
        min(n["pitch"] for ns in all_vnotes.values() for n in ns) - 2,
        max(n["pitch"] for ns in all_vnotes.values() for n in ns) + 2)
    for i, (name, kind, desc) in enumerate(var_list):
        vnotes = all_vnotes[name]
        # variant gets its own window emphasis: rotate windows by index
        a, b = bounds[i % steps]
        f = features(window(vnotes, 0, length), 0, length)
        sub = f
        p = dict(base_params)
        p.update(params_from(f, spread))
        # rotate the palette per window for family resemblance
        wf = win_feats[i % steps]
        p["accent"] = params_from(wf, spread)["accent"]
        p["score_tint"] = params_from(wf, spread)["score_tint"]
        # per-variant hue identity so the six stay distinguishable at a glance
        ang = (0, -20, -38, 14, -8, 26)[i % 6]
        if rng is not None:
            ang += rng.randint(-14, 14)
            p["wash_op"] = round(max(0.25, min(0.85,
                p["wash_op"] + rng.uniform(-0.10, 0.10))), 3)
            p["score_glow_op"] = round(max(0.15, min(0.95,
                p["score_glow_op"] + rng.uniform(-0.15, 0.15))), 3)
        p["accent"] = rotate_hue(p["accent"], ang)
        p["score_tint"] = rotate_hue(p["score_tint"], ang)
        mask = render_roll(vnotes, 0, length, 2048, 2048, pretty=False,
                           pitch_range=pitch_range, style=args.note_style)
        sheet = render_roll(
            vnotes, 0, length, 640, 300, pretty=True,
            pitch_range=pitch_range, style=args.note_style,
            title=f"{name} — {f['mode']} on pc{f['key_pc']} — "
                  f"{len(vnotes)} notes, vel {f['mean_vel']:.2f}")
        mask_path = os.path.join(args.out, f"score_{name}.png")
        sheet_path = os.path.join(args.out, f"sheet_{name}.png")
        ramp_path = os.path.join(args.out, f"ramp_{name}.png")
        iri_path = os.path.join(args.out, f"iri_{name}.png")
        bold_path = os.path.join(args.out, f"scoreBold_{name}.png")
        hero_path = os.path.join(args.out, f"hero_{name}.png")
        mask.save(mask_path)
        sheet.save(sheet_path)
        if args.note_style == "note":
            make_ramp(p["accent"], ramp_path)
            make_iri(p["accent"], iri_path)
            render_bold(vnotes, 0, length, 2048, 2048).convert("RGB").save(
                bold_path)
            render_hero(vnotes, hero_path)
            Image.open(hero_path).convert("RGB").save(hero_path)

            # Self-contained canvases (blend-mode driven). Painter 11.1.1
            # mask fills do NOT bind imported bitmaps, so content layers
            # carry their own backgrounds: white bg = no-op under Multiply,
            # black bg = no-op under Add, 0.5 gray = neutral for Height.
            smask = mask.convert("L")
            boldL = Image.open(bold_path).convert("L")
            heroL = Image.open(hero_path).convert("L")
            iri = Image.open(iri_path).convert("RGB")
            accent255 = tuple(int(round(255 * min(1.0, c))) for c in
                              p["accent"])
            cedar = (148, 102, 66)
            gold = (217, 168, 77)

            def recolor(m, fg, bg=(0, 0, 0)):
                return Image.composite(
                    Image.new("RGB", m.size, tuple(fg)),
                    Image.new("RGB", m.size, tuple(bg)), m)

            def tinted(m, src):
                src = src.convert("RGB").resize(m.size)
                out = Image.new("RGB", m.size, (0, 0, 0))
                out.paste(src, (0, 0), m)
                return out

            recolor(smask, cedar, (255, 255, 255)).save(
                os.path.join(args.out, f"ink_{name}.png"))
            recolor(smask, accent255).save(
                os.path.join(args.out, f"glowFine_{name}.png"))
            recolor(smask, (255, 255, 255), (128, 128, 128)).save(
                os.path.join(args.out, f"hFine_{name}.png"))
            recolor(boldL, gold, (255, 255, 255)).save(
                os.path.join(args.out, f"boldInk_{name}.png"))
            recolor(boldL, accent255).save(
                os.path.join(args.out, f"boldGlow_{name}.png"))
            tinted(boldL, iri).save(
                os.path.join(args.out, f"boldGlint_{name}.png"))
            recolor(heroL, gold, (255, 255, 255)).save(
                os.path.join(args.out, f"heroGold_{name}.png"))
            recolor(heroL, accent255).save(
                os.path.join(args.out, f"heroGlow_{name}.png"))
            recolor(heroL, (255, 255, 255), (128, 128, 128)).save(
                os.path.join(args.out, f"heroH_{name}.png"))
            recolor(heroL, (204, 204, 204)).save(
                os.path.join(args.out, f"heroMet_{name}.png"))
            tinted(heroL, iri).save(
                os.path.join(args.out, f"heroGlint_{name}.png"))
        cells.append((f"{name} — {desc}", sheet))
        entry = dict(
            name=name, kind=kind, desc=desc,
            notes=len(vnotes),
            features={k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in sub.items()},
            params=p, score_mask_png=os.path.abspath(mask_path))
        for key, fp in (("ramp_png", ramp_path), ("iri_png", iri_path),
                        ("score_bold_png", bold_path),
                        ("hero_png", hero_path),
                        ("ink_png", os.path.join(args.out, f"ink_{name}.png")),
                        ("glow_fine_png",
                         os.path.join(args.out, f"glowFine_{name}.png")),
                        ("h_fine_png",
                         os.path.join(args.out, f"hFine_{name}.png")),
                        ("bold_ink_png",
                         os.path.join(args.out, f"boldInk_{name}.png")),
                        ("bold_glow_png",
                         os.path.join(args.out, f"boldGlow_{name}.png")),
                        ("bold_glint_png",
                         os.path.join(args.out, f"boldGlint_{name}.png")),
                        ("hero_gold_png",
                         os.path.join(args.out, f"heroGold_{name}.png")),
                        ("hero_glow_png",
                         os.path.join(args.out, f"heroGlow_{name}.png")),
                        ("hero_h_png",
                         os.path.join(args.out, f"heroH_{name}.png")),
                        ("hero_met_png",
                         os.path.join(args.out, f"heroMet_{name}.png")),
                        ("hero_glint_png",
                         os.path.join(args.out, f"heroGlint_{name}.png"))):
            if os.path.isfile(fp):
                entry[key] = os.path.abspath(fp)
        variants_json.append(entry)
        print(f"variant {name:10s} notes={len(vnotes):4d} "
              f"density={f['density']:.2f} vel={f['mean_vel']:.2f} "
              f"mode={f['mode']}")

    header_roll = render_roll(notes, 0, length, 1980, 340, pretty=True,
                              pitch_range=pitch_range,
                              style=args.note_style,
                              title=f"Melusina — {theme_name} — "
                                    f"{len(notes)} notes")
    head_path = os.path.join(args.out, "theme_header.png")
    header_roll.save(head_path)

    sheet_path = os.path.join(
        args.out, f"ContactSheet_MrSheep_Scores_{date}.png")
    build_contact_sheet(
        cells, sheet_path,
        header=f"MR. SHEEP — SMS Composer — {theme_name}",
        sub=f"{len(notes)} notes / {length:.0f} beats — "
            f"{len(cells)} variants — {date} — Melodia/Melusina")

    params_path = os.path.join(args.out, "composer_params.json")
    with open(params_path, "w", encoding="utf-8") as fh:
        json.dump(dict(
            theme=theme_name, midi=os.path.abspath(args.midi),
            generated=_dt.datetime.now().isoformat(timespec="seconds"),
            note_count=len(notes), length_beats=round(length, 3),
            variants=variants_json), fh, indent=2)
    print("wrote", params_path)
    print("wrote", sheet_path)


if __name__ == "__main__":
    main()
