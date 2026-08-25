# -*- coding: utf-8 -*-
"""Scan / apply Melusina dated plate remounts -> site-plates.json slots + optional path rewrite.

Never remounts solid-mauve *_001 blanks. Prefers dated melusina_*_YYYYMMDD_nn.png.
Writes named slots (SSOT) - pages hydrate via data-plate + content/site-plates.json.

Usage:
  python Tools/remount_melusina_plates.py --scan
  python Tools/remount_melusina_plates.py --apply
  python Tools/remount_melusina_plates.py --apply --passport
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
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
CHAR = SITE / "generated" / "assets" / "character"
WIX = SITE / "wix"
PLATES = SITE / "content" / "site-plates.json"
AUDIT = ROOT / "Saved" / "Audit" / "melusina_remount_scan.json"

SHOT_ROLES = {
    "beauty_nikki": ["hero_beauty", "stage_lead"],
    "beauty": ["hero_beauty", "stage_lead"],
    "front_nikki": ["hero_front"],
    "beauty_jewelry": ["hero_jewelry"],
    "jewelry": ["hero_jewelry"],
    "low_nikki": ["hero_low"],
    "water_splash": ["hero_splash"],
    "glam_audvis": ["hero_audvis"],
}

# shot -> plate slot keys
SHOT_TO_SLOTS = {
    "beauty_nikki": ["index.hero", "recruiter.hero", "hub.melusina", "stage.beauty"],
    "beauty": ["index.hero", "recruiter.hero", "hub.melusina", "stage.beauty"],
    "front_nikki": ["stage.front"],
    "beauty_jewelry": ["stage.jewelry"],
    "jewelry": ["stage.jewelry"],
}

MAUVE_BLANK_GLOBS = (
    "melusina_beauty_nikki_001.png",
    "melusina_beauty_jewelry_001.png",
    "melusina_low_nikki_001.png",
    "melusina_water_splash_001.png",
    "melusina_glam_audvis_001.png",
)

DATED_RE = re.compile(
    r"^melusina_(?P<shot>[a-z0-9_]+)_(?P<ymd>\d{8})_(?P<nn>\d{2})\.png$",
    re.I,
)
WEB_PREFIX = "../generated/assets/character"


def _png_entropy_ok(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
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


def scan_plates() -> dict:
    dated: dict[str, list[dict]] = defaultdict(list)
    interim = {
        "void_iri": CHAR / "melusina_beauty_void_iri.png",
        "hero_pack": sorted((CHAR / "hero_20260712").glob("*.png"))
        if (CHAR / "hero_20260712").is_dir()
        else [],
    }
    for path in sorted(CHAR.glob("melusina_*.png")):
        name = path.name
        if name in MAUVE_BLANK_GLOBS:
            ok, reason = _png_entropy_ok(path)
            dated["_blocked_mauve"].append(
                {"file": name, "ok": ok, "reason": reason, "bytes": path.stat().st_size}
            )
            continue
        m = DATED_RE.match(name)
        if not m:
            continue
        shot = m.group("shot").lower()
        ok, reason = _png_entropy_ok(path)
        dated[shot].append(
            {
                "file": name,
                "path": str(path),
                "web_path": f"{WEB_PREFIX}/{name}",
                "ymd": m.group("ymd"),
                "nn": m.group("nn"),
                "ok": ok,
                "reason": reason,
                "bytes": path.stat().st_size,
                "roles": SHOT_ROLES.get(shot, []),
            }
        )

    chosen: dict[str, dict] = {}
    for shot, rows in dated.items():
        if shot.startswith("_"):
            continue
        good = [r for r in rows if r["ok"]]
        if not good:
            continue
        good.sort(key=lambda r: (r["ymd"], r["nn"]), reverse=True)
        chosen[shot] = good[0]

    ready = bool(chosen.get("beauty_nikki") or chosen.get("beauty"))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "char_dir": str(CHAR),
        "dated_found": {k: v for k, v in dated.items()},
        "chosen": chosen,
        "interim_void_iri_present": interim["void_iri"].is_file(),
        "hero_pack_count": len(interim["hero_pack"]),
        "beauty_ready_to_remount": ready,
        "blocked_mauve": dated.get("_blocked_mauve", []),
        "next_actions": [],
    }
    if not ready:
        report["next_actions"].append(
            "Render melusina_beauty_nikki_YYYYMMDD_nn.png into generated/assets/character/"
        )
    else:
        report["next_actions"].append(
            "Run with --apply to write site-plates.json slots + soft HTML fallbacks"
        )
    return report


def _load_plates() -> dict:
    if PLATES.is_file():
        return json.loads(PLATES.read_text(encoding="utf-8"))
    return {"version": 1, "slots": {}}


def apply_remount(chosen: dict[str, dict]) -> dict:
    """Write plate slots + soft-replace interim paths in key HTML as fallback before JS hydrate."""
    plates = _load_plates()
    slots = plates.setdefault("slots", {})
    notes: list[str] = []
    mapping: dict[str, str] = {}

    for shot, slot_keys in SHOT_TO_SLOTS.items():
        row = chosen.get(shot)
        if not row:
            continue
        for key in slot_keys:
            prev = slots.get(key) or {}
            slots[key] = {
                "path": row["web_path"],
                "alt": prev.get("alt") or row["file"].replace("_", " "),
            }
            if prev.get("caption"):
                slots[key]["caption"] = prev["caption"]
        notes.append(f"{shot} -> {row['file']} ({', '.join(slot_keys)})")

    beauty = chosen.get("beauty_nikki") or chosen.get("beauty")
    if beauty:
        mapping["../generated/assets/character/melusina_beauty_void_iri.png"] = beauty["web_path"]
        mapping[
            "../generated/assets/character/hero_20260712/melusina_hero_beauty_nikki.png"
        ] = beauty["web_path"]

    front = chosen.get("front_nikki")
    if front:
        mapping[
            "../generated/assets/character/hero_20260712/melusina_hero_front_nikki.png"
        ] = front["web_path"]

    jewelry = chosen.get("beauty_jewelry") or chosen.get("jewelry")
    if jewelry:
        mapping[
            "../generated/assets/character/hero_20260712/melusina_hero_three_quarter_jewelry.png"
        ] = jewelry["web_path"]

    PLATES.write_text(json.dumps(plates, indent=2) + "\n", encoding="utf-8")

    targets = [
        WIX / "melodia-stage-passport.js",
        WIX / "melodia-stage-character.html",
        WIX / "index.html",
        WIX / "application-hub.html",
        WIX / "melodia-melusina.html",
        WIX / "hero-renders.html",
        WIX / "recruiter-one-sheet.html",
    ]
    edits = {}
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        n = 0
        for old, new in mapping.items():
            if old in text and old != new:
                text = text.replace(old, new)
                n += 1
        if n:
            path.write_text(text, encoding="utf-8")
        edits[path.name] = n

    # Stage JS beauty constants
    js = WIX / "melodia-stage-passport.js"
    if beauty and js.is_file():
        text = js.read_text(encoding="utf-8")
        for const in ("BEAUTY_URL", "FULL_BEAUTY_URL", "HERO_BEAUTY"):
            # Replace string after = for known interim constants when still void
            pass
        beauty_web = beauty["web_path"]
        text = re.sub(
            r"(const BEAUTY_URL = )'[^']+'",
            rf"\1'{beauty_web}'",
            text,
        )
        text = re.sub(
            r"(const FULL_BEAUTY_URL = )'[^']+'",
            rf"\1'{beauty_web}'",
            text,
        )
        text = re.sub(
            r"(const HERO_BEAUTY = ).+",
            rf"\1'{beauty_web}';",
            text,
            count=1,
        )
        js.write_text(text, encoding="utf-8")
        edits["melodia-stage-passport.js_const"] = 1

    return {"slots_written": notes, "mapping": mapping, "edits": edits, "notes": notes}


def refresh_passport_capture(beauty_web: str | None) -> dict | None:
    if not beauty_web:
        return None
    sys.path.insert(0, str(ROOT / "Tools"))
    try:
        from melodia_asset_passport import write_passport_files
    except ImportError as exc:
        return {
            "error": (
                "melodia_asset_passport module is missing (lost 2026-07-31, only .pyc "
                f"+ a known-bad reconstruction remain - see _TASK_QUEUE.md): {exc}"
            )
        }

    pp_path = SITE / "generated" / "passports" / "melusina_passport.json"
    if not pp_path.is_file():
        return None
    old = json.loads(pp_path.read_text(encoding="utf-8"))
    rows = old.get("rows") or []
    new_rows = []
    for label, value in rows:
        if label == "Capture":
            fname = Path(beauty_web).name
            new_rows.append([label, f"beauty Nikki dated - {fname}"])
        elif label == "Software" and ("v4" in str(value) or "v7" not in str(value)):
            new_rows.append([label, "Blender - Melodia Portfolio Stage v7"])
        elif label == "Engine" and "Cycles" in str(value):
            new_rows.append([label, "Blender EEVEE"])
        else:
            new_rows.append([label, value])
    passport = dict(old)
    passport["rows"] = new_rows
    passport["version"] = "stage-v7"
    passport["generated_at"] = datetime.now(timezone.utc).isoformat()
    paths = write_passport_files(passport)

    # passport_config Capture if present
    pc = SITE / "generated" / "passport_config.json"
    if pc.is_file():
        cfg = json.loads(pc.read_text(encoding="utf-8"))
        # soft update nested capture fields when shape matches
        if isinstance(cfg, dict):
            for key in ("capture", "Capture", "still"):
                if key in cfg:
                    cfg[key] = f"beauty Nikki dated - {Path(beauty_web).name}"
            # rows-like
            if isinstance(cfg.get("rows"), list):
                cfg["rows"] = [
                    [a, (f"beauty Nikki dated - {Path(beauty_web).name}" if a == "Capture" else b)]
                    for a, b in cfg["rows"]
                ]
            pc.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    return {"passport_paths": paths, "capture": beauty_web}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--passport", action="store_true")
    args = ap.parse_args()
    if not (args.scan or args.apply or args.passport):
        args.scan = True

    report = scan_plates()
    AUDIT.parent.mkdir(parents=True, exist_ok=True)

    if args.apply:
        if not report["beauty_ready_to_remount"]:
            report["apply"] = {"skipped": True, "reason": "no entropy-ok dated beauty plate"}
        else:
            report["apply"] = apply_remount(report["chosen"])

    if args.passport:
        beauty = report["chosen"].get("beauty_nikki") or report["chosen"].get("beauty")
        web = beauty["web_path"] if beauty else None
        report["passport"] = refresh_passport_capture(web)

    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
