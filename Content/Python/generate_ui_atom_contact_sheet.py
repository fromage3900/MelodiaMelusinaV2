"""Build a deterministic review sheet for canonical generated Melodia UI atoms.

This is an offline QA artifact. It never imports or modifies Unreal assets.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "Content" / "Melodia" / "UI" / "Textures" / "Generated"
OUTPUT = PROJECT_ROOT / "Saved" / "Audit" / "UI" / "ui_atom_contact_sheet.png"

CANVAS = (24, 21, 34, 255)
CARD = (43, 37, 54, 255)
CHECKER_A = (236, 229, 214, 255)
CHECKER_B = (194, 185, 199, 255)
TEXT = (247, 239, 232, 255)
SUBTEXT = (201, 184, 212, 255)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default(size=size)


def _checkerboard(width: int, height: int, cell: int = 12) -> Image.Image:
    image = Image.new("RGBA", (width, height), CHECKER_A)
    draw = ImageDraw.Draw(image)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, min(x + cell, width), min(y + cell, height)), fill=CHECKER_B)
    return image


def _alpha_summary(image: Image.Image) -> str:
    alpha = image.getchannel("A")
    histogram = alpha.histogram()
    return f"alpha 0:{histogram[0]} partial:{sum(histogram[1:255])} 255:{histogram[255]}"


def main() -> Path:
    sources = sorted(SOURCE_DIR.glob("*.png"))
    if not sources:
        raise RuntimeError(f"No generated UI atoms found in {SOURCE_DIR}")

    columns = 2
    card_width = 500
    card_height = 280
    margin = 28
    header = 88
    rows = (len(sources) + columns - 1) // columns
    sheet = Image.new(
        "RGBA",
        (margin * 2 + columns * card_width, header + margin + rows * card_height),
        CANVAS,
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 18), "Melodia UI Atoms - Alpha and Edge Review", fill=TEXT, font=_font(26, True))
    draw.text((margin, 53), "Canonical PNG sources; checkerboard is review-only.", fill=SUBTEXT, font=_font(15))

    for index, source in enumerate(sources):
        column = index % columns
        row = index // columns
        x = margin + column * card_width
        y = header + row * card_height
        draw.rounded_rectangle((x, y, x + card_width - 16, y + card_height - 16), radius=14, fill=CARD)

        atom = Image.open(source).convert("RGBA")
        preview_size = 176
        checker = _checkerboard(preview_size, preview_size)
        scale = min(preview_size / atom.width, preview_size / atom.height, 4.0)
        rendered = atom.resize(
            (max(1, round(atom.width * scale)), max(1, round(atom.height * scale))),
            Image.Resampling.NEAREST,
        )
        px = (preview_size - rendered.width) // 2
        py = (preview_size - rendered.height) // 2
        checker.alpha_composite(rendered, (px, py))
        sheet.alpha_composite(checker, (x + 18, y + 48))

        text_x = x + 214
        draw.text((x + 18, y + 14), source.name, fill=TEXT, font=_font(17, True))
        draw.text((text_x, y + 60), f"native {atom.width} x {atom.height}", fill=TEXT, font=_font(15))
        draw.text((text_x, y + 90), _alpha_summary(atom), fill=SUBTEXT, font=_font(13))
        draw.text((text_x, y + 128), "Review at native size and 4x nearest", fill=SUBTEXT, font=_font(13))
        draw.text((text_x, y + 154), "to expose real pixel stair-stepping.", fill=SUBTEXT, font=_font(13))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(OUTPUT, "PNG", optimize=True)
    print(f"Contact sheet: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    main()
