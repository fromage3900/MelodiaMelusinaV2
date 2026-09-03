# -*- coding: utf-8 -*-
"""Assign a render PNG to a named site plate slot (content/site-plates.json).

Usage:
  python Tools/assign_plate.py list
  python Tools/assign_plate.py index.hero generated/assets/character/melusina_beauty_nikki_20260714_01.png
  python Tools/assign_plate.py scan
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from melodia_website_root import resolve_website_root  # noqa: E402

SITE = resolve_website_root(ROOT)
PLATES = SITE / "content" / "site-plates.json"
CHAR = SITE / "generated" / "assets" / "character"
WIX_REL_PREFIX = "../"

MAUVE_BLANKS = {
    "melusina_beauty_nikki_001.png",
    "melusina_beauty_jewelry_001.png",
    "melusina_low_nikki_001.png",
    "melusina_water_splash_001.png",
    "melusina_glam_audvis_001.png",
}


def _load() -> dict:
    if not PLATES.is_file():
        return {"version": 1, "slots": {}}
    return json.loads(PLATES.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    PLATES.parent.mkdir(parents=True, exist_ok=True)
    PLATES.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _entropy_ok(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    if path.name in MAUVE_BLANKS:
        return False, "mauve_blank_forbidden"
    if path.stat().st_size < 40_000:
        return False, "too_small"
    if Image is None:
        return True, "size_ok_no_pil"
    try:
        with Image.open(path) as im:
            im = im.convert("RGB").resize((96, 120))
            colors = im.getcolors(maxcolors=96 * 120) or []
            if len(colors) < 48:
                return False, f"low_entropy_{len(colors)}"
            dom = max(c[0] for c in colors) / float(96 * 120)
            if dom > 0.92:
                return False, f"dominant_{dom:.2f}"
    except Exception as exc:
        return False, f"read_error:{exc}"
    return True, "ok"


def _to_web_path(path: Path) -> str:
    path = path.resolve()
    site = SITE.resolve()
    try:
        rel = path.relative_to(site)
    except ValueError as exc:
        raise SystemExit(f"Path must be under my-site-clean: {path}") from exc
    # web paths from wix/
    return "../" + rel.as_posix()


def cmd_list(data: dict) -> int:
    slots = data.get("slots") or {}
    if not slots:
        print("(no slots)")
        return 0
    for key, slot in sorted(slots.items()):
        print(f"{key:28} {slot.get('path', '')}")
    return 0


def cmd_assign(data: dict, slot: str, file_arg: str, alt: str | None) -> int:
    raw = Path(file_arg)
    if not raw.is_absolute():
        # try relative to SITE, then CWD, then CHAR
        candidates = [SITE / file_arg, Path.cwd() / file_arg, CHAR / file_arg]
        path = next((c for c in candidates if c.is_file()), None)
        if path is None:
            raise SystemExit(f"File not found: {file_arg}")
    else:
        path = raw
    ok, reason = _entropy_ok(path)
    if not ok:
        raise SystemExit(f"Refuse assign ({reason}): {path}")
    web = _to_web_path(path)
    slots = data.setdefault("slots", {})
    prev = slots.get(slot) or {}
    slots[slot] = {
        "path": web,
        "alt": alt or prev.get("alt") or path.stem.replace("_", " "),
    }
    if prev.get("caption"):
        slots[slot]["caption"] = prev["caption"]
    _save(data)
    print(f"assigned {slot} -> {web}")
    return 0


def cmd_scan() -> int:
    print("=== character PNGs ===")
    for p in sorted(CHAR.glob("melusina_*.png")):
        ok, reason = _entropy_ok(p)
        flag = "OK" if ok else "NO"
        print(f"  [{flag}] {p.name}  {p.stat().st_size}  {reason}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slot_or_cmd", help="Slot key, or list|scan")
    ap.add_argument("file", nargs="?", help="PNG path under my-site-clean")
    ap.add_argument("--alt", default=None, help="Alt text for the plate")
    args = ap.parse_args()
    data = _load()
    cmd = args.slot_or_cmd.lower()
    if cmd == "list":
        return cmd_list(data)
    if cmd == "scan":
        return cmd_scan()
    if not args.file:
        ap.error("file path required when assigning a slot")
    return cmd_assign(data, args.slot_or_cmd, args.file, args.alt)


if __name__ == "__main__":
    raise SystemExit(main())
