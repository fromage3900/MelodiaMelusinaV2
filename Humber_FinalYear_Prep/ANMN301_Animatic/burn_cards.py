"""
Shorewake animatic — panel numbering + real title/end cards.

WHY THIS EXISTS
---------------
The ANMN 301 brief requires: "panels labeled+numbered, no gaps" and
"TITLE CARD + END CARD required". The v3 cut shipped pure-black slugs for
both cards and no numbering on any panel, so all three requirements failed.

This is a pure-pixel pass. It does not touch Blender, the VSE, or the render —
it reads the finished 1920x1080 panels and writes submission-ready copies into
panels_final/. Numbering is burned into the corner of each panel; the title
and end cards are generated as real typographic cards.

Run:  python burn_cards.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = r"P:\MelodiaMelusinaV2-Laptop\Humber_FinalYear_Prep\ANMN301_Animatic"
# v5 = the canonical-rig pass: all 17 panels rendered against character_rig
# with real textures. v4/v3 are the earlier grey / empty-deck passes and
# are kept only as fallbacks for a shot v5 is missing.
SRC = os.path.join(ROOT, "proxy", "panels_v5")
FALLBACK = os.path.join(ROOT, "proxy", "panels_v4")
OUT = os.path.join(ROOT, "panels_final")

W, H = 1920, 1080
FPS = 24

TITLE = "SHOREWAKE CALLING"
SUBTITLE = "ANMN 301 — Animatic Story Edit"
NAME = "Brennan Shepherd"
ENDLINE = "FIN"
END_SUB = "ANMN 301  ·  Animatic Story Edit  ·  Brennan Shepherd"

FONT_BIG = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REG = r"C:\Windows\Fonts\arial.ttf"
FONT_NUM = r"C:\Windows\Fonts\consolab.ttf"

# Palette pulled from the beat board's own description of the film: night
# water, lantern warm, pearl-pink sky. The cards must read as the same film.
INK = (14, 18, 30)
LANTERN = (255, 214, 154)
PEARL = (238, 226, 240)


def font(path, size):
    return ImageFont.truetype(path, size)


def resolve(num):
    """Prefer the re-rendered v4 panel, fall back to v3 for the shots the fix
    did not touch. Probing per-panel, not per-directory: panels_v4 is a
    PARTIAL set (only the 6 that were duplicates), so a directory-level
    existence check silently drops the other 11 and produces a short cut.
    """
    v4 = os.path.join(SRC, "panel_%02d.png" % num)
    if os.path.exists(v4):
        return v4, "v4"
    v3 = os.path.join(FALLBACK, "panel_%02d.png" % num)
    if os.path.exists(v3):
        return v3, "v3"
    return None, "MISSING"


def source_dir():
    """Retained for the log line only — resolution is per-panel."""
    if os.path.isdir(SRC) and os.listdir(SRC):
        return SRC
    return FALLBACK


def text_width(draw, s, f):
    return int(draw.textbbox((0, 0), s, font=f)[2])


def make_title():
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)

    # a faint horizon band so the card is not a dead rectangle
    for y in range(int(H * 0.62), H):
        t = (y - H * 0.62) / (H * 0.38)
        d.line([(0, y), (W, y)],
               fill=(int(14 + 26 * t), int(18 + 30 * t), int(30 + 40 * t)))

    f_title = font(FONT_BIG, 128)
    f_sub = font(FONT_REG, 44)
    f_name = font(FONT_REG, 38)

    d.text(((W - text_width(d, TITLE, f_title)) // 2, int(H * 0.36)),
           TITLE, font=f_title, fill=LANTERN)
    d.text(((W - text_width(d, SUBTITLE, f_sub)) // 2, int(H * 0.36) + 160),
           SUBTITLE, font=f_sub, fill=PEARL)
    d.text(((W - text_width(d, NAME, f_name)) // 2, int(H * 0.36) + 232),
           NAME, font=f_name, fill=PEARL)
    return im


def make_end():
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    f_end = font(FONT_BIG, 150)
    f_sub = font(FONT_REG, 36)
    d.text(((W - text_width(d, ENDLINE, f_end)) // 2, int(H * 0.42)),
           ENDLINE, font=f_end, fill=LANTERN)
    d.text(((W - text_width(d, END_SUB, f_sub)) // 2, int(H * 0.42) + 190),
           END_SUB, font=f_sub, fill=PEARL)
    return im


def burn_number(im, label):
    """Bottom-left slate: a filled box plus the panel number, so it stays
    legible over a bright water plate and a dark hull alike."""
    d = ImageDraw.Draw(im)
    f = font(FONT_NUM, 52)
    tw = text_width(d, label, f)
    box = (36, H - 108, 36 + tw + 44, H - 36)
    d.rectangle(box, fill=(0, 0, 0))
    d.rectangle(box, outline=LANTERN, width=3)
    d.text((box[0] + 22, box[1] + 12), label, font=f, fill=LANTERN)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    src = source_dir()
    print("CARDS source=%s" % src)

    n = 0
    primarycount = 0
    for i in range(1, 18):
        p, src = resolve(i)
        if p is None:
            print("CARDS MISSING panel_%02d" % i)
            continue
        if src == "v4":
            primarycount += 1
        im = Image.open(p).convert("RGB")
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
        burn_number(im, "%02d" % i)
        im.save(os.path.join(OUT, "panel_%02d.png" % i))
        n += 1
    # 17 is the contract. Anything less is a short cut, not a warning.
    if n != 17:
        print("CARDS FATAL only %d/17 panels written" % n)
        raise SystemExit(1)
    print("CARDS numbered %d panels (%d from %s, %d from fallback %s)"
          % (n, primarycount, os.path.basename(SRC),
             n - primarycount, os.path.basename(FALLBACK)))

    make_title().save(os.path.join(OUT, "title.png"))
    make_end().save(os.path.join(OUT, "end.png"))
    print("CARDS wrote title.png + end.png")
    print("CARDS DONE -> %s" % OUT)


main()
