"""Restore EnvSandbox SDF textures from _PROJECT/04_Materials/Textures."""
from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials" / "Textures"
DST = PROJECT_ROOT / "Content" / "EnvSandbox" / "Materials" / "SDF" / "Textures"

TEXTURES = [
    "Marble/Marble_1_-_512x512",
    "Marble/Marble_3_-_512x512",
    "Marble/Marble_5_-_512x512",
    "Marble/Marble_6_-_512x512",
    "Marble/Marble_7_-_512x512",
    "Marble/Marble_9_-_512x512",
    "Perlin/Perlin_1_-_512x512",
    "Voronoi/Voronoi_2_-_512x512",
    "Voronoi/Voronoi_11_-_512x512",
]


def main() -> int:
    restored = 0
    for rel in TEXTURES:
        src = SRC / f"{rel}.uasset"
        dst = DST / f"{rel}.uasset"
        if not src.exists():
            print(f"Missing: {src}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        restored += 1
        print(f"Restored {rel}")
    print(f"Done: {restored} textures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
