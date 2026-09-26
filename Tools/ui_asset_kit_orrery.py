"""Generate the Orrery-hub SVG asset kit (editorial magical-girl lookbook) for import into Figma.

Deterministic (seeded). Output: Content/UI/AssetKit_20260926/*.svg
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "Content", "UI", "AssetKit_20260926")
INDIGO_DEEP, INDIGO, VIOLET = "#0B0920", "#17123A", "#2A1F5C"
PEARL, ROSE, ROSE_DEEP, LAVENDER, CYAN = "#F4EEE6", "#E8B4A0", "#C98F7A", "#B9A6F0", "#9EE7F7"


def write(name, body, w, h, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f"{rect}{body}</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def sparkle(x, y, r, color, opacity):
    # four-point magical-girl sparkle
    k = r * 0.22
    d = (f"M{x},{y - r} Q{x + k},{y - k} {x + r},{y} Q{x + k},{y + k} {x},{y + r} "
         f"Q{x - k},{y + k} {x - r},{y} Q{x - k},{y - k} {x},{y - r}Z")
    return f'<path d="{d}" fill="{color}" opacity="{opacity:.2f}"/>'


def starfield(size=1024, seed=3900):
    rnd = random.Random(seed)
    defs = (f'<defs><radialGradient id="n1" cx="30%" cy="35%" r="55%"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".9"/>'
            f'<stop offset="1" stop-color="{INDIGO_DEEP}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="n2" cx="75%" cy="70%" r="45%"><stop offset="0" stop-color="#3B2466" stop-opacity=".7"/>'
            f'<stop offset="1" stop-color="{INDIGO_DEEP}" stop-opacity="0"/></radialGradient></defs>')
    body = [defs, f'<rect width="{size}" height="{size}" fill="url(#n1)"/>', f'<rect width="{size}" height="{size}" fill="url(#n2)"/>']
    for _ in range(420):
        x, y = rnd.uniform(0, size), rnd.uniform(0, size)
        r = rnd.choice([0.6, 0.8, 1.0, 1.0, 1.4, 1.8])
        col = rnd.choice([PEARL, PEARL, PEARL, LAVENDER, CYAN, ROSE])
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" opacity="{rnd.uniform(.35, 1):.2f}"/>')
    for _ in range(22):
        body.append(sparkle(rnd.uniform(0, size), rnd.uniform(0, size), rnd.uniform(5, 14),
                            rnd.choice([PEARL, ROSE, LAVENDER]), rnd.uniform(.6, 1)))
    write("T_Starfield_Tile.svg", "".join(body), size, size, INDIGO_DEEP)


def medallion(state):
    s, c = 240, 120
    ring = {"locked": LAVENDER, "unlocked": ROSE, "focused": PEARL}[state]
    op = {"locked": .45, "unlocked": .9, "focused": 1}[state]
    parts = [f'<defs><radialGradient id="g" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="{VIOLET}"/>'
             f'<stop offset="1" stop-color="{INDIGO_DEEP}"/></radialGradient></defs>',
             f'<circle cx="{c}" cy="{c}" r="92" fill="url(#g)" opacity="{op}"/>',
             f'<circle cx="{c}" cy="{c}" r="96" fill="none" stroke="{ring}" stroke-width="2" opacity="{op}"/>',
             f'<circle cx="{c}" cy="{c}" r="104" fill="none" stroke="{ring}" stroke-width=".75" stroke-dasharray="2 6" opacity="{op}"/>']
    for i in range(12):  # hour ticks like an orrery dial
        a = math.radians(i * 30)
        r0, r1 = (108, 116) if i % 3 == 0 else (108, 112)
        parts.append(f'<line x1="{c + r0 * math.cos(a):.1f}" y1="{c + r0 * math.sin(a):.1f}" x2="{c + r1 * math.cos(a):.1f}" '
                     f'y2="{c + r1 * math.sin(a):.1f}" stroke="{ring}" stroke-width="1.2" opacity="{op}"/>')
    parts.append(sparkle(c, c, 26 if state != "locked" else 16, ring, op))
    if state == "focused":
        parts.append(f'<circle cx="{c}" cy="{c}" r="118" fill="none" stroke="{CYAN}" stroke-width="1" opacity=".8"/>')
    if state == "locked":
        parts.append(f'<path d="M{c - 9},{c + 40} h18 v14 h-18z M{c - 6},{c + 40} v-6 a6,6 0 0 1 12,0 v6" fill="none" '
                     f'stroke="{LAVENDER}" stroke-width="1.5" opacity=".7"/>')
    write(f"UI_Medallion_{state.capitalize()}.svg", "".join(parts), s, s)


def filigree_frame(w=600, h=800):
    m, cr = 18, 36
    parts = [f'<rect x="{m}" y="{m}" width="{w - 2 * m}" height="{h - 2 * m}" rx="2" fill="none" stroke="{ROSE}" stroke-width="1"/>',
             f'<rect x="{m + 8}" y="{m + 8}" width="{w - 2 * m - 16}" height="{h - 2 * m - 16}" fill="none" stroke="{ROSE}" '
             f'stroke-width=".5" opacity=".6"/>']
    for cx, cy, sx, sy in [(m, m, 1, 1), (w - m, m, -1, 1), (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
        parts.append(f'<path d="M{cx},{cy + sy * cr} q{sx * cr * .1},{-sy * cr * .9} {sx * cr},{-sy * cr} M{cx + sx * 10},{cy + sy * 10} '
                     f'q{sx * 14},{sy * 2} {sx * 18},{sy * 18}" fill="none" stroke="{ROSE}" stroke-width="1.2"/>')
        parts.append(sparkle(cx + sx * 22, cy + sy * 22, 6, PEARL, .9))
    parts.append(sparkle(w / 2, m, 9, ROSE, 1))
    parts.append(sparkle(w / 2, h - m, 9, ROSE, 1))
    write("UI_Filigree_Frame.svg", "".join(parts), w, h)


def divider(w=720, h=40):
    c = w / 2
    parts = [f'<line x1="40" y1="{h / 2}" x2="{c - 40}" y2="{h / 2}" stroke="{ROSE}" stroke-width="1"/>',
             f'<line x1="{c + 40}" y1="{h / 2}" x2="{w - 40}" y2="{h / 2}" stroke="{ROSE}" stroke-width="1"/>',
             f'<circle cx="{c}" cy="{h / 2}" r="10" fill="none" stroke="{ROSE}" stroke-width="1"/>',
             sparkle(c, h / 2, 7, PEARL, 1)]
    for x in (c - 58, c + 58):
        parts.append(f'<circle cx="{x}" cy="{h / 2}" r="2.2" fill="{ROSE}"/>')
    write("UI_Divider_Editorial.svg", "".join(parts), w, h)


def sigil(s=128):
    c = s / 2
    parts = [f'<circle cx="{c}" cy="{c}" r="54" fill="{INDIGO}" opacity=".85"/>',
             f'<ellipse cx="{c}" cy="{c}" rx="46" ry="18" fill="none" stroke="{ROSE}" stroke-width="1.4" transform="rotate(-25 {c} {c})"/>',
             f'<ellipse cx="{c}" cy="{c}" rx="46" ry="18" fill="none" stroke="{LAVENDER}" stroke-width="1.1" transform="rotate(35 {c} {c})"/>',
             f'<circle cx="{c}" cy="{c}" r="54" fill="none" stroke="{PEARL}" stroke-width="1"/>',
             sparkle(c, c, 12, PEARL, 1),
             f'<circle cx="{c + 38}" cy="{c - 18}" r="4" fill="{CYAN}"/>']
    write("UI_Orrery_Sigil.svg", "".join(parts), s, s)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    starfield()
    for st in ("locked", "unlocked", "focused"):
        medallion(st)
    filigree_frame()
    divider()
    sigil()
    print("KIT", sorted(os.listdir(OUT)))
