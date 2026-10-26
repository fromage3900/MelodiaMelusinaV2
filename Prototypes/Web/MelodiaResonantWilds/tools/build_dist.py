"""Package Resonant Wilds as a self-contained static folder for a website section.

Copies index.html, style.css, js/ and vendor/ into dist/ (no tools/, no README).
Drop dist/ into any static host (GitHub Pages, a plain web server) and open index.html.
Run from anywhere: python Prototypes/Web/MelodiaResonantWilds/tools/build_dist.py
"""
import shutil
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
DIST = GAME / "dist"
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
for name in ["index.html", "style.css"]:
    shutil.copy2(GAME / name, DIST / name)
shutil.copytree(GAME / "js", DIST / "js", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(GAME / "vendor", DIST / "vendor")
print(f"wrote {DIST.relative_to(GAME.parents[2])}")
