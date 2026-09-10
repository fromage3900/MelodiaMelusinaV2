from pathlib import Path
import html

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "sources"
OUT.mkdir(exist_ok=True)

CARDS = [
    {
        "slug": "melodia-zbrush-sculpt-square",
        "size": (1080, 1080),
        "theme": "dark",
        "kicker": "ZBrush Sculpt Study",
        "title": "Sculpt Study",
        "subtitle": "silhouette, form language, and surface pass",
        "slot": "Drop sculpt render here",
        "tags": ["Sculpt", "ZBrush", "WIP"],
        "footer": "Melodia Asset Plate",
        "layout": "art",
    },
    {
        "slug": "melodia-sketch-study-square",
        "size": (1080, 1080),
        "theme": "light",
        "kicker": "Sketch Study",
        "title": "Shape Notes",
        "subtitle": "gesture, rhythm, motif exploration",
        "slot": "Drop sketch scan here",
        "tags": ["Sketch", "Ideation", "Linework"],
        "footer": "Ivory Editorial",
        "layout": "art",
    },
    {
        "slug": "melodia-shader-breakdown-square",
        "size": (1080, 1080),
        "theme": "dark",
        "kicker": "Shader Passport",
        "title": "Pear-fect Sheen Pass",
        "subtitle": "iridescence, satin gloss, sparkle mask",
        "tags": ["Shader", "Texture Breakdown", "UE"],
        "footer": "Technical Read",
        "layout": "spec",
        "specs": [("Surface", "Petal Satin"), ("Inputs", "Ramp / Fresnel / Mask"), ("Engine", "Unreal Material")],
    },
    {
        "slug": "melodia-geometry-nodes-square",
        "size": (1080, 1080),
        "theme": "light",
        "kicker": "Geometry Nodes",
        "title": "Procedural Scatter",
        "subtitle": "node graph, masks, variation, handoff",
        "tags": ["Geometry Nodes", "PCG", "Tooling"],
        "footer": "Process Plate",
        "layout": "spec",
        "specs": [("Tool", "Blender"), ("Handoff", "PCG / Unreal"), ("Output", "Scatter Kit")],
    },
    {
        "slug": "melodia-process-carousel-portrait",
        "size": (1080, 1350),
        "theme": "dark",
        "kicker": "Process Carousel",
        "title": "Breakdown Sequence",
        "subtitle": "beauty plate, wireframe, shader graph, final notes",
        "slot": "Cover image slot",
        "tags": ["01 / 05", "Breakdown", "Portfolio"],
        "footer": "Swipe for Process",
        "layout": "art",
    },
    {
        "slug": "melodia-blender-retopo-square",
        "size": (1080, 1080),
        "theme": "light",
        "kicker": "Blender Retopology",
        "title": "Clean Topology Pass",
        "subtitle": "silhouette preservation, loops, UV-ready mesh",
        "tags": ["Retopo", "Blender", "Mesh Study"],
        "footer": "Topology Read",
        "layout": "spec",
        "specs": [("Tool", "Blender"), ("Focus", "Loops / Normals / UV Seams"), ("Output", "Game-Ready Mesh")],
    },
    {
        "slug": "melodia-blender-trimsheet-square",
        "size": (1080, 1080),
        "theme": "dark",
        "kicker": "Blender / Substance",
        "title": "Trim Sheet Study",
        "subtitle": "ornament strips, UV layout, material reuse",
        "slot": "Drop trimsheet preview here",
        "tags": ["Trim Sheet", "UV", "Substance"],
        "footer": "Material Economy",
        "layout": "art",
    },
    {
        "slug": "melodia-ue-material-instance-square",
        "size": (1080, 1080),
        "theme": "dark",
        "kicker": "Unreal Material Instance",
        "title": "Stylized Surface Controls",
        "subtitle": "ramp tint, fresnel, sparkle, wetness",
        "tags": ["Unreal", "Shader", "Lookdev"],
        "footer": "UE Breakdown",
        "layout": "spec",
        "specs": [("Master", "Toon Universal"), ("Params", "Ramp / Fresnel / Sheen"), ("Capture", "Beauty + Graph")],
    },
    {
        "slug": "melodia-ue-niagara-ambience-square",
        "size": (1080, 1080),
        "theme": "dark",
        "kicker": "Unreal Niagara",
        "title": "Ambient VFX Pass",
        "subtitle": "petals, motes, glow sprites, timing",
        "slot": "Drop Niagara capture here",
        "tags": ["Niagara", "VFX", "Ambience"],
        "footer": "Motion Plate",
        "layout": "art",
    },
    {
        "slug": "melodia-ue-pcg-route-square",
        "size": (1080, 1080),
        "theme": "light",
        "kicker": "Unreal PCG",
        "title": "Route-Safe Scatter",
        "subtitle": "density masks, path clearance, foliage rhythm",
        "tags": ["PCG", "Unreal", "Debug View"],
        "footer": "World Layout",
        "layout": "spec",
        "specs": [("System", "PCG Graph"), ("Proof", "Heatmap / Scatter / Route"), ("Output", "Walkable Garden")],
    },
    {
        "slug": "melodia-blender-geometry-nodes-portrait",
        "size": (1080, 1350),
        "theme": "light",
        "kicker": "Blender Geometry Nodes",
        "title": "Procedural Tool Walkthrough",
        "subtitle": "inputs, masks, variations, Unreal handoff",
        "slot": "Drop node graph / result here",
        "tags": ["01 / 04", "Nodes", "Breakdown"],
        "footer": "Swipe for Setup",
        "layout": "art",
    },
]


def esc(value):
    return html.escape(str(value), quote=True)


def tag_group(tags, y, dark):
    x = 64
    parts = ['<g id="Metadata/Tags">']
    for tag in tags:
        width = max(78, len(tag) * 9 + 34)
        fill = "#FCFBF8" if dark else "#FFFFFF"
        text = "#C9A86A" if dark else "#241B2E"
        parts.append(f'<g id="Tag/{esc(tag)}"><rect x="{x}" y="{y}" width="{width}" height="30" fill="{fill}" stroke="#C9A86A" stroke-opacity=".62"/>')
        parts.append(f'<text x="{x + 17}" y="{y + 20}" fill="{text}" font-family="IBM Plex Mono, monospace" font-size="11" letter-spacing="1.1">{esc(tag.upper())}</text></g>')
        x += width + 10
    parts.append("</g>")
    return "\n".join(parts)


def star(x, y, r=16, color="#C9A86A", opacity=".9"):
    points = f"{x},{y-r} {x+r*.22},{y-r*.22} {x+r},{y} {x+r*.22},{y+r*.22} {x},{y+r} {x-r*.22},{y+r*.22} {x-r},{y} {x-r*.22},{y-r*.22}"
    return f'<polygon points="{points}" fill="{color}" opacity="{opacity}"/>'


def line_stars(dark):
    color = "#FCFBF8" if dark else "#C9A86A"
    opacity = ".55" if dark else ".3"
    dots = [
        (330, 88, 2), (564, 92, 1.4), (760, 78, 1.4), (824, 190, 2.2),
        (452, 156, 1.4), (688, 340, 2.4), (842, 372, 1.3), (910, 448, 2.5),
        (196, 752, 1.4), (422, 754, 2.4), (705, 753, 2.4), (944, 773, 1.3),
    ]
    parts = [f'<g id="Motifs/ConstellationField" opacity="{opacity}">']
    for x, y, r in dots:
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')
    parts.append(star(462, 156, 16, "#DDC79B", ".82"))
    parts.append(star(540, 854, 16, "#DDC79B", ".72"))
    parts.append("</g>")
    return "\n".join(parts)


def art_slot(card, dark):
    w, h = card["size"]
    y1 = int(h * .49)
    y2 = int(h * .79)
    fill = "#080B13" if dark else "#FFFFFF"
    opacity = ".62" if dark else ".84"
    label = esc(card.get("slot", "Drop artwork here").upper())
    return f'''
<g id="ArtworkSlot/ReplaceMe">
  <rect x="64" y="{y1}" width="{w - 128}" height="{y2 - y1}" fill="{fill}" fill-opacity="{opacity}" stroke="#C9A86A" stroke-width="2"/>
  <pattern id="diagonal-{card["slug"]}" width="24" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <line x1="0" y1="0" x2="0" y2="24" stroke="#C9A86A" stroke-opacity=".38" stroke-width="1"/>
  </pattern>
  <rect x="64" y="{y1}" width="{w - 128}" height="{y2 - y1}" fill="url(#diagonal-{card["slug"]})" opacity=".7"/>
  <text x="{w/2}" y="{(y1+y2)/2}" text-anchor="middle" fill="{"#DDC79B" if dark else "#5A6170"}" font-family="IBM Plex Mono, monospace" font-size="13" letter-spacing="1.3">{label}</text>
</g>'''


def spec_slot(card, dark):
    w, h = card["size"]
    y = int(h * .48)
    panel_fill = "#080B13" if dark else "#FFFFFF"
    panel_opacity = ".72" if dark else ".86"
    label_fill = "#C2BAE0" if dark else "#5A6170"
    value_fill = "#FCFBF8" if dark else "#241B2E"
    parts = [f'<g id="BreakdownSpecs/EditRows"><rect x="48" y="{y - 24}" width="{w - 96}" height="232" fill="{panel_fill}" fill-opacity="{panel_opacity}" stroke="#C9A86A" stroke-opacity=".46"/>']
    parts.append(f'<line x1="64" y1="{y}" x2="{w-64}" y2="{y}" stroke="#C9A86A" stroke-width="2"/>')
    row_y = y + 52
    for label, value in card["specs"]:
        parts.append(f'<text x="64" y="{row_y}" fill="{label_fill}" font-family="IBM Plex Mono, monospace" font-size="13" letter-spacing="1.1">{esc(label.upper())}</text>')
        parts.append(f'<text x="{w-64}" y="{row_y}" fill="{value_fill}" font-family="IBM Plex Mono, monospace" font-size="13" letter-spacing="1.1" text-anchor="end">{esc(value.upper())}</text>')
        parts.append(f'<line x1="64" y1="{row_y+22}" x2="{w-64}" y2="{row_y+22}" stroke="#C9A86A" stroke-opacity=".34"/>')
        row_y += 42
    parts.append("</g>")
    return "\n".join(parts)


def svg(card):
    w, h = card["size"]
    dark = card["theme"] == "dark"
    bg = "#141A30" if dark else "#F7F4EF"
    fg = "#FCFBF8" if dark else "#241B2E"
    accent = "#DDC79B" if dark else "#A7884E"
    footer = "#C2BAE0" if dark else "#5A6170"
    title_size = 74 if h <= 1100 else 64
    subtitle_size = 34 if h <= 1100 else 32
    content = art_slot(card, dark) if card["layout"] == "art" else spec_slot(card, dark)
    y_tags = h - 110
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<title>{esc(card["title"])}</title>
<defs>
  <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{bg}"/>
    <stop offset=".62" stop-color="{"#2A254A" if dark else "#FCFBF8"}"/>
    <stop offset="1" stop-color="{"#1C1426" if dark else "#EFEAE1"}"/>
  </linearGradient>
  <linearGradient id="iridescentShader" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#F5E8EA" stop-opacity=".0"/>
    <stop offset=".28" stop-color="#E7C9CE" stop-opacity=".32"/>
    <stop offset=".54" stop-color="#A99AD0" stop-opacity=".28"/>
    <stop offset=".78" stop-color="#8AA9D6" stop-opacity=".24"/>
    <stop offset="1" stop-color="#DDC79B" stop-opacity=".16"/>
  </linearGradient>
</defs>
<g id="Background">
  <rect width="{w}" height="{h}" fill="url(#background)"/>
  <ellipse cx="{w*.78}" cy="{h*.13}" rx="{w*.34}" ry="{h*.22}" fill="#6E5AA6" opacity="{'.26' if dark else '.08'}"/>
  <rect id="IridescentShaderOverlay/FigmaEditable" width="{w}" height="{h}" fill="url(#iridescentShader)" opacity="{'.72' if dark else '.58'}"/>
</g>
{line_stars(dark)}
<g id="FrameAndFiligree">
  <rect x="44" y="44" width="{w-88}" height="{h-88}" fill="none" stroke="#C9A86A" stroke-opacity=".55"/>
  <path d="M44 130V44h86 M950 44h86v86 M44 {h-130}v86h86 M950 {h-44}h86v-86" fill="none" stroke="#C9A86A" stroke-width="3"/>
</g>
<g id="Brand">
  {star(78, 76, 18, "#C9A86A")}
  <text x="104" y="83" fill="{fg}" font-family="Cinzel, Georgia, serif" font-size="21" letter-spacing="3">MELODIA</text>
</g>
<g id="Text/EditMe">
  <text x="64" y="154" fill="{accent}" font-family="IBM Plex Mono, monospace" font-size="12" letter-spacing="1.5">{esc(card["kicker"].upper())}</text>
  <text x="64" y="264" fill="{fg}" font-family="Fraunces, Georgia, serif" font-size="{title_size}">{esc(card["title"])}</text>
  <text x="64" y="320" fill="{accent}" font-family="Fraunces, Georgia, serif" font-size="{subtitle_size}">{esc(card["subtitle"])}</text>
</g>
{content}
{tag_group(card["tags"], y_tags, dark)}
<g id="Metadata/Footer">
  <text x="{w-64}" y="{h-86}" fill="{footer}" font-family="IBM Plex Mono, monospace" font-size="12" letter-spacing="1.4" text-anchor="end">{esc(card["footer"].upper())}</text>
</g>
</svg>'''


def main():
    for card in CARDS:
        path = OUT / f'{card["slug"]}.svg'
        path.write_text(svg(card), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
