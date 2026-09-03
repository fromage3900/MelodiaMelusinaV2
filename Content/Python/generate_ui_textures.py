"""Generate crisp, alpha-safe Melodia UI atoms with deterministic output."""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_DIR = Path(r"c:\EnvironmentPortfolio\BS_GodFile\Content\Melodia\UI\Textures\Generated")
SUPERSAMPLE = 4

DESIGN_TOKENS = {
    "gold_500": "#C9A86A",
    "gold_700": "#A7884E",
    "rose": "#E8A9A1",
    "amber": "#D9A566",
    "lavender": "#B6A6D9",
    "seafoam": "#8FC9BD",
    "parchment": "#F2E6CF",
    "ink": "#3B2A22",
    "iris": "#6E5AA6",
}

DrawCallback = Callable[[ImageDraw.ImageDraw, int], None]


def _rgba_canvas(width: int, height: int, draw_callback: DrawCallback) -> Image.Image:
    """Draw at 4x and downsample once in premultiplied-alpha space."""
    scale = SUPERSAMPLE
    canvas = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    draw_callback(ImageDraw.Draw(canvas), scale)
    premultiplied = canvas.convert("RGBa")
    return premultiplied.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")


def _star_points(size: int, point_count: int, inner_ratio: float, scale: int, rotation: float = 0.0):
    center = size * scale / 2.0
    outer = (size / 2.0 - 2.0) * scale
    inner = size * inner_ratio * scale
    points = []
    for index in range(point_count * 2):
        angle = rotation + index * math.pi / point_count
        radius = outer if index % 2 == 0 else inner
        points.append((center + radius * math.cos(angle), center + radius * math.sin(angle)))
    return points


def create_4pt_star(size: int = 64, color: str = "#C9A86A", outline_color: str = "#A7884E") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        points = _star_points(size, 4, 0.25, scale, -math.pi / 8.0)
        draw.polygon(points, fill=color)
        draw.line(points + [points[0]], fill=outline_color, width=2 * scale, joint="curve")

    return _rgba_canvas(size, size, draw_atom)


def create_8pt_star(size: int = 64, color: str = "#C9A86A", outline_color: str = "#A7884E") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        points = _star_points(size, 8, 0.20, scale)
        draw.polygon(points, fill=color)
        draw.line(points + [points[0]], fill=outline_color, width=scale, joint="curve")

    return _rgba_canvas(size, size, draw_atom)


def create_filigree_corner(size: int = 64, color: str = "#C9A86A") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        for index in range(3):
            inset = index * 8 * scale
            radius = (size - index * 16 - 4) * scale
            draw.arc((inset, inset, radius, radius), 0, 90, fill=color, width=2 * scale)

        center = 8 * scale
        rosette_radius = 6 * scale
        dot_radius = max(2, scale)
        for index in range(8):
            angle = index * math.pi / 4.0
            x = center + rosette_radius * math.cos(angle)
            y = center + rosette_radius * math.sin(angle)
            draw.ellipse((x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius), fill=color)

    return _rgba_canvas(size, size, draw_atom)


def create_filigree_scroll(width: int = 128, height: int = 16, color: str = "#C9A86A") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        points = [
            (x * scale, (height / 2.0 + 4.0 * math.sin(x * 0.2)) * scale)
            for x in range(0, width + 1, 2)
        ]
        draw.line(points, fill=color, width=2 * scale, joint="curve")
        dot_radius = scale
        for x in range(0, width, 16):
            y = (height / 2.0 + 4.0 * math.sin(x * 0.2)) * scale
            sx = x * scale
            draw.ellipse((sx - dot_radius, y - dot_radius, sx + dot_radius, y + dot_radius), fill=color)

    return _rgba_canvas(width, height, draw_atom)


def create_clef_watermark(size: int = 256, color: str = "#C9A86A") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        center_x = center_y = size / 2.0
        spiral = []
        for degrees in range(0, 721, 2):
            angle = math.radians(degrees)
            radius = 20.0 + degrees * 0.045
            x = (center_x + radius * math.cos(angle)) * scale
            y = (center_y - 20.0 + radius * math.sin(angle)) * scale
            spiral.append((x, y))
        draw.line(spiral, fill=color, width=3 * scale, joint="curve")
        draw.line(
            ((center_x * scale, (center_y - 72) * scale), (center_x * scale, (center_y + 52) * scale)),
            fill=color,
            width=3 * scale,
        )
        draw.arc(
            ((center_x - 30) * scale, (center_y + 20) * scale, (center_x + 30) * scale, (center_y + 80) * scale),
            0,
            180,
            fill=color,
            width=3 * scale,
        )

    return _rgba_canvas(size, size, draw_atom)


def create_parchment_noise(size: int = 512) -> Image.Image:
    """Create deterministic opaque parchment grain."""
    image = Image.new("RGBA", (size, size), (242, 230, 207, 255))
    rng = random.Random(0)
    pixels = image.load()
    for x in range(size):
        for y in range(size):
            noise = rng.randint(-10, 10)
            r, g, b, _ = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
                255,
            )
    return image.filter(ImageFilter.GaussianBlur(radius=0.5))


def create_cursor_default(size: int = 32, color: str = "#C9A86A") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        points = _star_points(size, 8, 0.20, scale, math.pi / 8.0)
        draw.polygon(points, fill=color)
        draw.line(points + [points[0]], fill=DESIGN_TOKENS["gold_700"], width=scale, joint="curve")

    return _rgba_canvas(size, size, draw_atom)


def create_cursor_interact(size: int = 40, color: str = "#E8A9A1") -> Image.Image:
    def draw_atom(draw: ImageDraw.ImageDraw, scale: int) -> None:
        points = _star_points(size, 8, 0.20, scale)
        draw.polygon(points, fill=color)
        draw.line(points + [points[0]], fill=DESIGN_TOKENS["gold_700"], width=scale, joint="curve")

        badge_size = 16 * scale
        badge_x = (size - 20) * scale
        badge_y = (size - 20) * scale
        draw.ellipse(
            (badge_x, badge_y, badge_x + badge_size, badge_y + badge_size),
            fill=DESIGN_TOKENS["gold_500"],
            outline=DESIGN_TOKENS["gold_700"],
            width=2 * scale,
        )
        try:
            font = ImageFont.truetype("arialbd.ttf", 10 * scale)
        except OSError:
            font = ImageFont.load_default(size=10 * scale)
        label = "F"
        bounds = draw.textbbox((0, 0), label, font=font)
        text_width = bounds[2] - bounds[0]
        text_height = bounds[3] - bounds[1]
        draw.text(
            (
                badge_x + (badge_size - text_width) / 2.0,
                badge_y + (badge_size - text_height) / 2.0 - bounds[1],
            ),
            label,
            fill=DESIGN_TOKENS["ink"],
            font=font,
        )

    return _rgba_canvas(size, size, draw_atom)


def save_texture(image: Image.Image, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / filename, "PNG", optimize=True)
    print(f"Generated: {filename}")


def main() -> None:
    outputs = {
        "T_Star4pt_Gold.png": create_4pt_star(color=DESIGN_TOKENS["gold_500"], outline_color=DESIGN_TOKENS["gold_700"]),
        "T_Star4pt_Rose.png": create_4pt_star(color=DESIGN_TOKENS["rose"], outline_color=DESIGN_TOKENS["gold_700"]),
        "T_Star8pt_Gold.png": create_8pt_star(color=DESIGN_TOKENS["gold_500"], outline_color=DESIGN_TOKENS["gold_700"]),
        "T_Star8pt_Iris.png": create_8pt_star(color=DESIGN_TOKENS["iris"], outline_color=DESIGN_TOKENS["gold_700"]),
        "T_FiligreeCorner.png": create_filigree_corner(color=DESIGN_TOKENS["gold_500"]),
        "T_FiligreeScroll.png": create_filigree_scroll(color=DESIGN_TOKENS["gold_500"]),
        "T_ClefWatermark.png": create_clef_watermark(color=DESIGN_TOKENS["gold_500"]),
        "T_ParchmentNoise.png": create_parchment_noise(),
        "Cursor_Default.png": create_cursor_default(color=DESIGN_TOKENS["gold_500"]),
        "Cursor_Interact.png": create_cursor_interact(color=DESIGN_TOKENS["rose"]),
    }
    for filename, image in outputs.items():
        save_texture(image, filename)

    print(f"Generated {len(outputs)} textures in {OUTPUT_DIR}")
    print("Reimport in Unreal: import import_generated_ui_atoms as atoms; atoms.main()")


if __name__ == "__main__":
    main()
