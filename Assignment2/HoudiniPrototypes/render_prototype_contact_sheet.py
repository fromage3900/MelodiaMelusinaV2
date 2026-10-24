"""spike: true
Render an orthographic, flat-shaded review sheet from the three Houdini OBJ outputs.
This is a geometry-inspection aid, not a final beauty render or UE material preview.
Requires Pillow in the workstation Python, not in the Houdini runtime.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "prototype_contact_sheet.png"
SIZE = 1800, 720
SCALE = 2

PALETTE = {
    "stone_frame": (207, 193, 171),
    "gold_came": (225, 183, 111),
    "opal_glass": (132, 174, 216),
    "stone_mullion": (194, 176, 153),
    "cymatic_lead": (233, 196, 246),
    "lissajous_ribbon": (245, 151, 219),
    "lissajous_filament": (255, 226, 250),
    "carved_basin": (204, 193, 176),
    "receiving_pool": (69, 182, 224),
    "fluted_support": (181, 168, 150),
    "fountain_jet": (100, 214, 246),
    "falling_water_sheet": (66, 185, 233),
    "lissajous_flow_ribbon": (55, 236, 226),
    "lissajous_flow_filament": (207, 255, 251),
    "spillway_coping": (230, 205, 164),
    "walkable_deck": (202, 183, 158),
    "deck_underside": (156, 140, 123),
    "gold_guardrail": (225, 178, 97),
    "stone_support_arch": (181, 166, 148),
    "tracery_post": (218, 195, 163),
    "aeolian_silk_veil": (224, 157, 194),
    "silk_edge_cord": (242, 205, 143),
    "listening_court_ring": (239, 205, 133),
    "court_inlay": (222, 195, 142),
    "orb_suspension": (255, 232, 180),
    "resonance_orb": (211, 230, 255),
    "orb_halo": (255, 220, 129),
    "lissajous_orbit_ribbon": (255, 180, 93),
    "lissajous_orbit_filament": (255, 246, 212),
    "bridge_gate_pier": (197, 178, 153),
    "pier_crown": (231, 192, 116),
}


def parse_obj(path: Path):
    vertices = []
    faces = []
    role = "prototype"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("v "):
            vertices.append(tuple(float(v) for v in line.split()[1:4]))
        elif line.startswith("g "):
            role = line[2:].strip()
        elif line.startswith("f "):
            ids = [int(token.split("/")[0])-1 for token in line.split()[1:]]
            if len(ids) >= 3:
                faces.append((role, ids))
    return vertices, faces


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def norm(a):
    d = math.sqrt(dot(a, a))
    return tuple(v/d for v in a)


def draw_mesh(draw, panel, path, camera, front=False):
    x0, y0, x1, y1 = panel
    vertices, faces = parse_obj(path)
    world_up = (0.0, 0.0, 1.0)
    camera = norm(camera)
    right = norm((world_up[1]*camera[2]-world_up[2]*camera[1],
                  world_up[2]*camera[0]-world_up[0]*camera[2],
                  world_up[0]*camera[1]-world_up[1]*camera[0]))
    up = norm((camera[1]*right[2]-camera[2]*right[1],
               camera[2]*right[0]-camera[0]*right[2],
               camera[0]*right[1]-camera[1]*right[0]))
    projected = [(dot(v, right), dot(v, up), dot(v, camera)) for v in vertices]
    minx = min(v[0] for v in projected); maxx = max(v[0] for v in projected)
    miny = min(v[1] for v in projected); maxy = max(v[1] for v in projected)
    mind = min(v[2] for v in projected); maxd = max(v[2] for v in projected)
    pad = 34*SCALE
    usable_w = (x1-x0)-2*pad
    usable_h = (y1-y0)-2*pad
    scale = min(usable_w/max(1e-4,maxx-minx), usable_h/max(1e-4,maxy-miny))
    cx = (minx+maxx)*0.5; cy = (miny+maxy)*0.5

    def screen(p):
        return (x0+(x1-x0)*0.5+(p[0]-cx)*scale,
                y0+(y1-y0)*0.5-(p[1]-cy)*scale)

    ordered = []
    for role, ids in faces:
        depth = sum(projected[i][2] for i in ids)/len(ids)
        highlight = role.startswith("lissajous") or role in ("resonance_orb", "orb_halo")
        ordered.append((int(highlight), depth, role, ids))
    # Render musical focal strands last in this review aid so they remain
    # legible over dense generated glass, water and silk tessellation.
    ordered.sort(key=lambda item: (item[0], item[1]))
    for highlight, depth, role, ids in ordered:
        points = [screen(projected[i]) for i in ids]
        base = PALETTE.get(role, (198, 193, 184))
        light = 0.78 + 0.22*(max(0.0, min(1.0, (depth-mind)/(maxd-mind+1e-5))))
        color = tuple(round(channel*light) for channel in base)
        outline = None if highlight else ((100, 82, 106) if role == "aeolian_silk_veil" else (58, 62, 76))
        draw.polygon(points, fill=color, outline=outline)


def main():
    img = Image.new("RGB", (SIZE[0]*SCALE, SIZE[1]*SCALE), (18, 24, 39))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", 22*SCALE)
    small = ImageFont.truetype("arial.ttf", 13*SCALE)
    entries = [
        ("01  RESONANT TRACERY", "8 rose ribbons | mode_m 5 -> 6 drives the nodal lead", "01_ResonantTracery.obj", (0.0,-1.0,0.0)),
        ("02  GRAVITY FOUNTAIN", "8 Lissajous strands per spill | three descending bowls", "02_GravityFountainCascade.obj", (1.0,-1.0,0.65)),
        ("03  AEOLIAN SILK BRIDGE", "8 orbital ribbons | walkable deck + three silk veils", "03_AeolianSilkBridge.obj", (0.0,-1.0,0.18)),
    ]
    margin=34*SCALE; gap=24*SCALE; panel_w=(SIZE[0]*SCALE-2*margin-2*gap)//3
    panel_top=96*SCALE; panel_bottom=SIZE[1]*SCALE-36*SCALE
    for index,(title,subtitle,filename,camera) in enumerate(entries):
        x0=margin+index*(panel_w+gap)
        panel=(x0,panel_top,x0+panel_w,panel_bottom)
        draw.rounded_rectangle(panel,radius=15*SCALE,fill=(29,38,57),outline=(76,91,118),width=2*SCALE)
        draw.text((x0+20*SCALE,28*SCALE),title,font=font,fill=(248,231,196))
        draw.text((x0+20*SCALE,66*SCALE),subtitle,font=small,fill=(188,202,224))
        draw_mesh(draw,panel,ROOT/filename,camera,front=index==0)
    img=img.resize(SIZE,Image.Resampling.LANCZOS)
    img.save(OUT)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
