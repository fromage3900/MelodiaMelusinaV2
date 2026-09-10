from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import random

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "exports"
OUT.mkdir(exist_ok=True)

COLORS = {
    "ivory": "#F7F4EF",
    "ivory_light": "#FCFBF8",
    "ivory_mid": "#EFEAE1",
    "plum": "#241B2E",
    "plum_dark": "#1C1426",
    "gold": "#C9A86A",
    "gold_light": "#DDC79B",
    "gold_dark": "#A7884E",
    "lavender": "#C2BAE0",
    "iris": "#6E5AA6",
    "astral": "#141A30",
    "astral_mid": "#26365E",
    "sakura": "#E7C9CE",
    "slate": "#5A6170",
    "white": "#FCFBF8",
}


def font(size, bold=False, serif=False, mono=False):
    candidates = []
    if mono:
        candidates = [
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
        ]
    elif serif:
        candidates = [
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/times.ttf",
        ]
    elif bold:
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


F_SERIF_XL = font(78, serif=True)
F_SERIF_L = font(58, serif=True)
F_SERIF_M = font(36, serif=True)
F_BODY = font(24)
F_BODY_S = font(19)
F_MONO = font(17, mono=True)
F_MONO_S = font(14, mono=True)
F_MONO_XS = font(12, mono=True)
F_BRAND = font(20, serif=True)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    a = hex_to_rgb(top)
    b = hex_to_rgb(bottom)
    for y in range(h):
        draw.line([(0, y), (w, y)], fill=lerp(a, b, y / max(1, h - 1)))
    return img.convert("RGBA")


def radial_overlay(img, center, radius, color, alpha=110):
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pixels = overlay.load()
    cr, cg, cb = hex_to_rgb(color)
    cx, cy = center
    for y in range(max(0, cy - radius), min(h, cy + radius)):
        for x in range(max(0, cx - radius), min(w, cx + radius)):
            d = math.hypot(x - cx, y - cy) / radius
            if d < 1:
                a = int(alpha * (1 - d) ** 1.8)
                pixels[x, y] = (cr, cg, cb, a)
    img.alpha_composite(overlay)


def iridescent_wash(img, dark=True, strength=1.0):
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pixels = overlay.load()
    stops = [
        (0.00, hex_to_rgb("#F5E8EA"), 0),
        (0.25, hex_to_rgb("#E7C9CE"), 46),
        (0.52, hex_to_rgb("#A99AD0"), 40),
        (0.74, hex_to_rgb("#8AA9D6"), 34),
        (1.00, hex_to_rgb("#DDC79B"), 26),
    ]
    alpha_scale = (.72 if dark else .52) * strength
    for y in range(h):
        for x in range(w):
            t = ((x / max(1, w - 1)) * .68 + (y / max(1, h - 1)) * .32)
            for idx in range(len(stops) - 1):
                a_pos, a_col, a_alpha = stops[idx]
                b_pos, b_col, b_alpha = stops[idx + 1]
                if a_pos <= t <= b_pos:
                    local = (t - a_pos) / max(.001, b_pos - a_pos)
                    col = lerp(a_col, b_col, local)
                    alpha = int((a_alpha + (b_alpha - a_alpha) * local) * alpha_scale)
                    pixels[x, y] = (*col, alpha)
                    break
    sheen = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen, "RGBA")
    for offset in range(-h, w, 240):
        sheen_draw.polygon(
            [(offset, h), (offset + 155, h), (offset + h + 155, 0), (offset + h, 0)],
            fill=(255, 255, 255, int(13 * strength if dark else 18 * strength)),
        )
    overlay.alpha_composite(sheen.filter(ImageFilter.GaussianBlur(18)))
    img.alpha_composite(overlay)


def starfield(draw, w, h, dark=True, seed=4):
    random.seed(seed)
    for _ in range(96 if dark else 44):
        x = random.randint(50, w - 50)
        y = random.randint(50, h - 50)
        r = random.choice([1, 1, 1, 2])
        col = COLORS["gold_light"] if random.random() < .22 else COLORS["white"]
        alpha = random.randint(55, 155) if dark else random.randint(35, 88)
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(*hex_to_rgb(col), alpha))
    for _ in range(6 if dark else 4):
        x = random.randint(90, w - 90)
        y = random.randint(90, h - 90)
        four_star(draw, x, y, random.randint(12, 22), COLORS["gold_light"], 150 if dark else 100)


def four_star(draw, x, y, r, color, alpha=210):
    fill = (*hex_to_rgb(color), alpha)
    pts = [(x, y-r), (x+int(r*.22), y-int(r*.22)), (x+r, y), (x+int(r*.22), y+int(r*.22)),
           (x, y+r), (x-int(r*.22), y+int(r*.22)), (x-r, y), (x-int(r*.22), y-int(r*.22))]
    draw.polygon(pts, fill=fill)


def line(draw, xy, fill, width=2):
    draw.line(xy, fill=fill, width=width)


def corners(draw, w, h, inset=54, length=92, color=None):
    color = color or COLORS["gold"]
    fill = (*hex_to_rgb(color), 190)
    for sx, sy in [(inset, inset), (w-inset, inset), (inset, h-inset), (w-inset, h-inset)]:
        hx = length if sx < w/2 else -length
        vy = length if sy < h/2 else -length
        line(draw, [(sx, sy), (sx+hx, sy)], fill, 3)
        line(draw, [(sx, sy), (sx, sy+vy)], fill, 3)


def text(draw, pos, value, fill, font_obj, anchor=None, spacing=4):
    draw.multiline_text(pos, value, fill=fill, font=font_obj, anchor=anchor, spacing=spacing)


def fit_lines(draw, value, font_obj, max_width, max_lines=3):
    words = value.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        box = draw.textbbox((0, 0), test, font=font_obj)
        if box[2] - box[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines[:max_lines])


def tag(draw, x, y, label, dark=True):
    label = label.upper()
    pad_x, pad_y = 18, 10
    box = draw.textbbox((0, 0), label, font=F_MONO_XS)
    tw, th = box[2]-box[0], box[3]-box[1]
    border = (*hex_to_rgb(COLORS["gold"]), 150)
    fill = (255, 255, 255, 10) if dark else (255, 255, 255, 210)
    draw.rectangle([x, y, x+tw+pad_x*2, y+th+pad_y*2], outline=border, fill=fill, width=1)
    text(draw, (x+pad_x, y+pad_y-1), label, COLORS["gold_light"] if dark else COLORS["plum"], F_MONO_XS)
    return x + tw + pad_x*2 + 10


def artbox(draw, rect, label, dark=True):
    x1, y1, x2, y2 = rect
    outline = (*hex_to_rgb(COLORS["gold"]), 150)
    fill = (8, 11, 19, 118) if dark else (255, 255, 255, 210)
    draw.rectangle(rect, outline=outline, fill=fill, width=2)
    for i in range(-500, 900, 34):
        line(draw, [(x1+i, y2), (x1+i+(y2-y1), y1)], (*hex_to_rgb(COLORS["gold"]), 42), 1)
    box = draw.textbbox((0, 0), label.upper(), font=F_MONO_S)
    text(draw, ((x1+x2)//2, (y1+y2)//2), label.upper(), COLORS["gold_light"] if dark else COLORS["slate"], F_MONO_S, anchor="mm")


def brand(draw, x, y, dark=True):
    four_star(draw, x+13, y+11, 14, COLORS["gold"], 220)
    text(draw, (x+40, y), "MELODIA", COLORS["white"] if dark else COLORS["plum"], F_BRAND)


def base_card(size=(1080, 1080), dark=True, seed=4):
    if dark:
        img = gradient(size, COLORS["astral"], COLORS["plum_dark"])
        radial_overlay(img, (int(size[0]*.78), int(size[1]*.12)), int(size[0]*.42), COLORS["iris"], 95)
        radial_overlay(img, (int(size[0]*.12), int(size[1]*.88)), int(size[0]*.36), COLORS["astral_mid"], 75)
    else:
        img = gradient(size, COLORS["ivory_light"], COLORS["ivory"])
        radial_overlay(img, (int(size[0]*.82), int(size[1]*.14)), int(size[0]*.34), COLORS["sakura"], 55)
        radial_overlay(img, (int(size[0]*.14), int(size[1]*.9)), int(size[0]*.32), COLORS["gold_light"], 35)
    iridescent_wash(img, dark=dark, strength=.95)
    draw = ImageDraw.Draw(img, "RGBA")
    starfield(draw, size[0], size[1], dark=dark, seed=seed)
    return img, draw


def render_card(card):
    w, h = card["size"]
    dark = card["theme"] == "dark"
    img, draw = base_card((w, h), dark=dark, seed=card.get("seed", 4))
    fg = COLORS["white"] if dark else COLORS["plum"]
    accent = COLORS["gold_light"] if dark else COLORS["gold_dark"]
    muted = COLORS["lavender"] if dark else COLORS["slate"]
    margin = 64
    corners(draw, w, h, inset=44, length=86, color=COLORS["gold"])
    if card.get("frame", True):
        draw.rectangle([44, 44, w-44, h-44], outline=(*hex_to_rgb(COLORS["gold"]), 88), width=1)
    brand(draw, margin, margin, dark=dark)
    text(draw, (margin, margin+82), card["kicker"].upper(), accent, F_MONO_XS)
    title_font = F_SERIF_XL if h <= 1100 else F_SERIF_L
    title = fit_lines(draw, card["title"], title_font, w - margin*2, 3)
    title_y = margin + 130
    text(draw, (margin, title_y), title, fg, title_font, spacing=2)
    sub_y = title_y + 92 * (title.count("\n") + 1)
    text(draw, (margin, sub_y), fit_lines(draw, card["subtitle"], F_SERIF_M, w - margin*2, 2), accent, F_SERIF_M, spacing=4)
    if card["layout"] == "artbox":
        artbox(draw, [margin, int(h*.49), w-margin, int(h*.79)], card["slot"], dark=dark)
    elif card["layout"] == "passport":
        y = int(h*.48)
        panel_fill = (8, 11, 19, 165) if dark else (255, 255, 255, 215)
        panel_border = (*hex_to_rgb(COLORS["gold"]), 70)
        draw.rectangle([margin-16, y-24, w-margin+16, y+208], fill=panel_fill, outline=panel_border, width=1)
        draw.line([margin, y, w-margin, y], fill=(*hex_to_rgb(COLORS["gold"]), 180), width=2)
        for label, value in card["specs"]:
            y += 42
            text(draw, (margin, y), label.upper(), muted, F_MONO_S)
            text(draw, (w-margin, y), value.upper(), fg, F_MONO_S, anchor="ra")
            draw.line([margin, y+30, w-margin, y+30], fill=(*hex_to_rgb(COLORS["gold"]), 55), width=1)
    x = margin
    for label in card["tags"]:
        x = tag(draw, x, h - margin - 46, label, dark=dark)
    text(draw, (w-margin, h-margin-35), card["footer"].upper(), muted, F_MONO_XS, anchor="ra")
    return img.convert("RGB")


CARDS = [
    {
        "filename": "melodia-zbrush-sculpt-square.png",
        "size": (1080, 1080),
        "theme": "dark",
        "layout": "artbox",
        "kicker": "ZBrush sculpt study",
        "title": "Sculpt Study",
        "subtitle": "silhouette, form language, and surface pass",
        "slot": "drop sculpt render here",
        "tags": ["sculpt", "zbrush", "wip"],
        "footer": "Melodia asset plate",
        "seed": 8,
    },
    {
        "filename": "melodia-sketch-study-square.png",
        "size": (1080, 1080),
        "theme": "light",
        "layout": "artbox",
        "kicker": "Sketch study",
        "title": "Shape Notes",
        "subtitle": "gesture, rhythm, motif exploration",
        "slot": "drop sketch scan here",
        "tags": ["sketch", "ideation", "linework"],
        "footer": "Ivory editorial",
        "seed": 3,
    },
    {
        "filename": "melodia-shader-breakdown-square.png",
        "size": (1080, 1080),
        "theme": "dark",
        "layout": "passport",
        "kicker": "Shader passport",
        "title": "Pear-fect Sheen Pass",
        "subtitle": "iridescence, satin gloss, sparkle mask",
        "specs": [("surface", "petal satin"), ("inputs", "ramp / fresnel / mask"), ("engine", "unreal material")],
        "tags": ["shader", "texture breakdown", "UE"],
        "footer": "Technical read",
        "seed": 12,
    },
    {
        "filename": "melodia-geometry-nodes-square.png",
        "size": (1080, 1080),
        "theme": "light",
        "layout": "passport",
        "kicker": "Geometry nodes",
        "title": "Procedural Scatter",
        "subtitle": "node graph, masks, variation, handoff",
        "specs": [("tool", "blender"), ("handoff", "pcg / unreal"), ("output", "scatter kit")],
        "tags": ["geometry nodes", "pcg", "tooling"],
        "footer": "Process plate",
        "seed": 16,
    },
    {
        "filename": "melodia-process-carousel-portrait.png",
        "size": (1080, 1350),
        "theme": "dark",
        "layout": "artbox",
        "kicker": "Process carousel",
        "title": "Breakdown Sequence",
        "subtitle": "beauty plate, wireframe, shader graph, final notes",
        "slot": "cover image slot",
        "tags": ["01 / 05", "breakdown", "portfolio"],
        "footer": "Swipe for process",
        "seed": 21,
    },
    {
        "filename": "melodia-blender-retopo-square.png",
        "size": (1080, 1080),
        "theme": "light",
        "layout": "passport",
        "kicker": "Blender retopology",
        "title": "Clean Topology Pass",
        "subtitle": "silhouette preservation, loops, UV-ready mesh",
        "specs": [("tool", "blender"), ("focus", "loops / normals / UV seams"), ("output", "game-ready mesh")],
        "tags": ["retopo", "blender", "mesh study"],
        "footer": "Topology read",
        "seed": 27,
    },
    {
        "filename": "melodia-blender-trimsheet-square.png",
        "size": (1080, 1080),
        "theme": "dark",
        "layout": "artbox",
        "kicker": "Blender / Substance",
        "title": "Trim Sheet Study",
        "subtitle": "ornament strips, UV layout, material reuse",
        "slot": "drop trimsheet preview here",
        "tags": ["trim sheet", "uv", "substance"],
        "footer": "Material economy",
        "seed": 31,
    },
    {
        "filename": "melodia-ue-material-instance-square.png",
        "size": (1080, 1080),
        "theme": "dark",
        "layout": "passport",
        "kicker": "Unreal material instance",
        "title": "Stylized Surface Controls",
        "subtitle": "ramp tint, fresnel, sparkle, wetness",
        "specs": [("master", "toon universal"), ("params", "ramp / fresnel / sheen"), ("capture", "beauty + graph")],
        "tags": ["unreal", "shader", "lookdev"],
        "footer": "UE breakdown",
        "seed": 35,
    },
    {
        "filename": "melodia-ue-niagara-ambience-square.png",
        "size": (1080, 1080),
        "theme": "dark",
        "layout": "artbox",
        "kicker": "Unreal Niagara",
        "title": "Ambient VFX Pass",
        "subtitle": "petals, motes, glow sprites, timing",
        "slot": "drop niagara capture here",
        "tags": ["niagara", "vfx", "ambience"],
        "footer": "Motion plate",
        "seed": 39,
    },
    {
        "filename": "melodia-ue-pcg-route-square.png",
        "size": (1080, 1080),
        "theme": "light",
        "layout": "passport",
        "kicker": "Unreal PCG",
        "title": "Route-Safe Scatter",
        "subtitle": "density masks, path clearance, foliage rhythm",
        "specs": [("system", "PCG graph"), ("proof", "heatmap / scatter / route"), ("output", "walkable garden")],
        "tags": ["pcg", "unreal", "debug view"],
        "footer": "World layout",
        "seed": 43,
    },
    {
        "filename": "melodia-blender-geometry-nodes-portrait.png",
        "size": (1080, 1350),
        "theme": "light",
        "layout": "artbox",
        "kicker": "Blender Geometry Nodes",
        "title": "Procedural Tool Walkthrough",
        "subtitle": "inputs, masks, variations, Unreal handoff",
        "slot": "drop node graph / result here",
        "tags": ["01 / 04", "nodes", "breakdown"],
        "footer": "Swipe for setup",
        "seed": 47,
    },
]


def main():
    for card in CARDS:
        img = render_card(card)
        path = OUT / card["filename"]
        img.save(path, "PNG", optimize=True)
        print(path)


if __name__ == "__main__":
    main()
