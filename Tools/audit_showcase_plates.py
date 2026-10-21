#!/usr/bin/env python3
"""Plate liveness audit for my-site-kit showcase heroes.

A 1920x1080 plate that is black, empty or a flat gradient compresses to a
tiny WebP. This flags any showcase plate whose WebP is implausibly small
(flat / empty / black) and reports the mean-luma + unique-colour count so a
plate can be triaged without opening it.

Exit code 1 if any plate is flagged, so it can gate a deploy.

    python Tools/audit_showcase_plates.py
    python Tools/audit_showcase_plates.py --min-webp-kb 40
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageStat

# my-site-kit is a sibling of BS_GodFile under the portfolio root, not inside it.
PORTFOLIO = Path(__file__).resolve().parents[2]
SITE_ROOT = PORTFOLIO / "my-site-kit"
SHOWCASE = SITE_ROOT / "public" / "melodia" / "vfx-showcase-2026-09-28"
ASSETS = SITE_ROOT / "generated" / "assets" / "unreal"

# Known-good plate may legitimately be flatter (e.g. a clean sky gradient),
# but anything under this many kilobytes at 1920x1080 is almost certainly
# black / empty / broken.
DEFAULT_MIN_WEBP_KB = 40


def audit_plate(png_path: Path, webp_path: Path, min_kb: int) -> dict:
    rec = {"name": png_path.stem, "png": str(png_path), "flags": []}

    if not png_path.is_file():
        rec["flags"].append("MISSING_PNG")
        rec["status"] = "MISSING"
        return rec
    rec["png_kb"] = png_path.stat().st_size // 1024

    if webp_path.is_file():
        rec["webp_kb"] = webp_path.stat().st_size // 1024
        if rec["webp_kb"] < min_kb:
            rec["flags"].append(f"FLAT_WEBP({rec['webp_kb']}KB<{min_kb}KB)")
    else:
        rec["flags"].append("MISSING_WEBP")

    try:
        im = Image.open(png_path).convert("RGB")
        rec["size"] = list(im.size)
        small = im.copy()
        small.thumbnail((320, 180), Image.LANCZOS)
        stat = ImageStat.Stat(small.convert("L"))
        rec["mean_luma"] = round(stat.mean[0], 1)
        rec["unique_colors"] = len(set(small.getdata()))
        if rec["mean_luma"] < 12:
            rec["flags"].append("NEAR_BLACK")
        if rec["unique_colors"] < 400:
            rec["flags"].append("FLAT_IMAGE")
        # Missing-material magenta: high red+blue, low green, and a large
        # share of the frame in that hue. This is the UE "default material"
        # tell and is invisible to a luma-only check.
        px = list(small.getdata())
        magenta = sum(1 for r, g, b in px if r > 90 and b > 90 and g < 60 and (r + b) > 2.2 * max(g, 1))
        pct = 100.0 * magenta / max(1, len(px))
        rec["magenta_pct"] = round(pct, 1)
        if pct > 12.0:
            rec["flags"].append(f"MISSING_MATERIAL_MAGENTA({pct:.0f}%)")
    except Exception as exc:  # noqa: BLE001
        rec["flags"].append(f"READ_ERROR:{exc}")

    rec["status"] = "OK" if not rec["flags"] else "FLAGGED"
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-webp-kb", type=int, default=DEFAULT_MIN_WEBP_KB)
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    if not SHOWCASE.is_dir():
        print(f"showcase dir missing: {SHOWCASE}")
        return 2

    results = []
    for png in sorted(SHOWCASE.glob("hero-*.png")):
        webp = png.with_suffix(".webp")
        results.append(audit_plate(png, webp, args.min_webp_kb))

    flagged = [r for r in results if r["status"] != "OK"]
    for r in results:
        mark = "FAIL" if r["status"] != "OK" else "ok  "
        detail = ",".join(r["flags"]) if r["flags"] else ""
        extra = ""
        if "webp_kb" in r:
            extra = f"webp={r['webp_kb']}KB"
        if "mean_luma" in r:
            extra += f" luma={r['mean_luma']} colors={r['unique_colors']}"
        print(f"[{mark}] {r['name']:<44} {extra}  {detail}")

    print()
    print(f"plates={len(results)} flagged={len(flagged)}")

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"wrote {args.json}")

    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
