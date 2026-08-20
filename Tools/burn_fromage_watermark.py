# -*- coding: utf-8 -*-
"""Burn fromage_art cockatiel watermark onto portfolio PNGs.

Usage:
  python Tools/burn_fromage_watermark.py --targets character nightshift --inplace
  python Tools/burn_fromage_watermark.py path/to/plate.png --inplace
  python Tools/burn_fromage_watermark.py --targets character --glob "melusina*20260715*" --inplace
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
SITE = ROOT / "my-site-clean"
BRAND = SITE / "generated" / "assets" / "brand" / "fromage_art_cockatiel.png"
AUDIT = ROOT / "Saved" / "Audit" / "fromage_watermark_burn.json"
MARKER = SITE / "generated" / "assets" / "brand" / ".fromage_wm_index.json"

TARGET_DIRS = {
    "character": SITE / "generated" / "assets" / "character",
    "nightshift": SITE / "generated" / "assets" / "nightshift",
    "unreal": SITE / "generated" / "assets" / "unreal",
    "ornaments": SITE / "generated" / "assets" / "ornaments",
    "cross": SITE / "generated" / "assets" / "cross",
    "sculpt": SITE / "generated" / "assets" / "sculpt",
}

SKIP_NAMES = {
    "fromage_art_cockatiel_mark.png",
    "melusina_beauty_depth_color.png",
}
SKIP_SUBSTR = ("_depth", "_mask", "heatmap")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_index() -> dict:
    if MARKER.is_file():
        try:
            return json.loads(MARKER.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_index(data: dict) -> None:
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _should_skip(path: Path) -> bool:
    name = path.name.lower()
    if name in SKIP_NAMES:
        return True
    if "fromage_art_cockatiel" in name:
        return True
    if any(s in name for s in SKIP_SUBSTR):
        return True
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        return True
    # Skip raw AudVis frame dumps; use promoted stills only
    if "glam_audvis_001.png0" in name:
        return True
    return False


def burn_one(
    src: Path,
    *,
    mark: Image.Image,
    opacity: float,
    scale: float,
    margin: float,
    inplace: bool,
    dry_run: bool,
    index: dict,
) -> dict:
    if not src.is_file():
        return {"path": str(src), "ok": False, "error": "missing"}
    if _should_skip(src):
        return {"path": str(src), "ok": False, "skipped": "filter"}

    key = str(src.resolve())
    try:
        mtime = src.stat().st_mtime
    except OSError:
        mtime = 0
    if index.get(key) == mtime:
        return {"path": str(src), "ok": False, "skipped": "already"}

    with Image.open(src) as im:
        base = im.convert("RGBA")

        mw = max(48, int(min(base.size) * scale))
        mh = int(mw * (mark.height / max(1, mark.width)))
        wm = mark.resize((mw, mh), Image.Resampling.LANCZOS)

        if opacity < 1.0:
            r, g, b, a = wm.split()
            a = a.point(lambda v: int(v * opacity))
            wm = Image.merge("RGBA", (r, g, b, a))

        mx = max(0, int(base.width - mw - base.width * margin))
        my = max(0, int(base.height - mh - base.height * margin))

        out = base.copy()
        out.alpha_composite(wm, (mx, my))

        dest = src if inplace else src.with_name(src.stem + "_wm" + src.suffix)
        if dry_run:
            return {
                "path": str(src),
                "ok": True,
                "dry_run": True,
                "dest": str(dest),
                "mark_px": [mw, mh],
            }

        if dest.suffix.lower() == ".png":
            tmp = dest.with_suffix(".png.tmp")
            out.save(tmp, format="PNG", optimize=True)
            import os

            for attempt in range(5):
                try:
                    os.replace(tmp, dest)
                    break
                except OSError:
                    import time

                    time.sleep(0.25 * (attempt + 1))
            else:
                # last resort: alternate filename then copy back later
                alt = dest.with_name(dest.stem + "_wm_new.png")
                os.replace(tmp, alt)
                dest = alt
        else:
            out.convert("RGB").save(dest, quality=92, optimize=True)

        index[key] = dest.stat().st_mtime
        return {
            "path": str(src),
            "ok": True,
            "dest": str(dest),
            "bytes": dest.stat().st_size,
            "mark_px": [mw, mh],
        }


def collect_paths(targets: list[str], globs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for t in targets:
        root = TARGET_DIRS.get(t)
        if not root or not root.is_dir():
            continue
        if globs:
            for g in globs:
                paths.extend(sorted(root.glob(g)))
        else:
            paths.extend(sorted(p for p in root.iterdir() if p.is_file()))
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="Burn fromage_art cockatiel mark onto plates")
    ap.add_argument("paths", nargs="*", type=Path, help="Explicit image paths")
    ap.add_argument(
        "--targets",
        nargs="+",
        choices=sorted(TARGET_DIRS),
        default=[],
        help="Named asset folders under generated/assets/",
    )
    ap.add_argument(
        "--glob",
        action="append",
        default=[],
        help="Glob under each target (repeatable).",
    )
    ap.add_argument("--opacity", type=float, default=0.22)
    ap.add_argument("--scale", type=float, default=0.14)
    ap.add_argument("--margin", type=float, default=0.03)
    ap.add_argument("--inplace", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Ignore already-burned index")
    ap.add_argument("--mark", type=Path, default=BRAND)
    args = ap.parse_args()

    if not args.mark.is_file():
        print(json.dumps({"ok": False, "error": f"mark_missing:{args.mark}"}))
        return 1

    with Image.open(args.mark) as raw:
        mark = raw.convert("RGBA")

    files: list[Path] = [p.resolve() for p in args.paths]
    files.extend(collect_paths(args.targets, args.glob))
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in files:
        if p in seen:
            continue
        seen.add(p)
        uniq.append(p)

    index = {} if args.force else _load_index()
    results = []
    for path in uniq:
        results.append(
            burn_one(
                path,
                mark=mark,
                opacity=args.opacity,
                scale=args.scale,
                margin=args.margin,
                inplace=args.inplace,
                dry_run=args.dry_run,
                index=index,
            )
        )

    if not args.dry_run:
        _save_index(index)

    ok = sum(1 for r in results if r.get("ok") and not r.get("dry_run"))
    dry = sum(1 for r in results if r.get("dry_run"))
    skipped = sum(1 for r in results if r.get("skipped"))
    report = {
        "ok": True,
        "generated_at": _now(),
        "mark": str(args.mark),
        "opacity": args.opacity,
        "scale": args.scale,
        "inplace": args.inplace,
        "dry_run": args.dry_run,
        "count": len(results),
        "burned": ok,
        "dry_run_count": dry,
        "skipped": skipped,
        "results": results,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "burned": ok,
                "dry_run_count": dry,
                "skipped": skipped,
                "count": len(results),
                "audit": str(AUDIT),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
