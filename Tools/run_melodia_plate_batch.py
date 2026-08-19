# -*- coding: utf-8 -*-
"""Batch Melodia Portfolio Stage plates (musical ornaments, outfit, hero).

Run inside Blender with the stage open (preferred):
  blender KitbashExport/Melodia_Portfolio_Stage_v4.blend -b -P Tools/run_melodia_plate_batch.py -- --musical
  blender ... -P Tools/run_melodia_plate_batch.py -- --hero
  blender ... -P Tools/run_melodia_plate_batch.py -- --musical --outfit fv2_accordion --hero

Outputs:
  my-site-clean/generated/assets/ornaments/musical_<date>/
  my-site-clean/generated/assets/character/hero_<date>/
  my-site-clean/generated/assets/character/melusina_outfit_<id>_stage_beauty.png
  Saved/Audit/melodia_plate_batch_manifest.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import melodia_stage_shot as shot  # noqa: E402

ASSETS = ROOT / "my-site-clean" / "generated" / "assets"
AUDIT = ROOT / "Saved" / "Audit" / "melodia_plate_batch_manifest.json"


def log(msg: str) -> None:
    print(f"[plate-batch] {msg}", flush=True)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def one(subject: str, preset: str, lights: str, out: Path, *, no_passport: bool) -> dict:
    shot.ensure_stage()
    # Leave render engine / samples as saved in the .blend
    shot.apply_lights(lights)
    cam = shot.select_camera(preset)
    sub = subject.strip().lower()
    auto = False
    if sub == "melusina":
        objs = shot.isolate_melusina()
    elif sub.startswith("outfit:"):
        objs = shot.isolate_outfit(sub.split(":", 1)[1])
    elif sub.startswith("ornament:"):
        objs = shot.import_ornament(sub.split(":", 1)[1])
        auto = True
    else:
        raise SystemExit(f"unknown subject {subject}")
    if auto:
        shot.aim_at(cam, objs)
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    ok = out.is_file() and out.stat().st_size > 1000
    log(f"{'OK' if ok else 'FAIL'} {out} ({out.stat().st_size if out.is_file() else 0} bytes)")
    if ok and not no_passport:
        try:
            shot.emit_passport(sub, objs, preset, out)
        except Exception as exc:
            log(f"passport warn: {exc}")
    return {
        "subject": subject,
        "preset": preset,
        "lights": lights,
        "out": str(out),
        "ok": ok,
        "bytes": out.stat().st_size if out.is_file() else 0,
    }


def main() -> int:
    args = _argv()
    want_musical = "--musical" in args
    want_hero = "--hero" in args
    no_passport = "--no-passport" in args
    outfit = None
    if "--outfit" in args:
        i = args.index("--outfit")
        if i + 1 < len(args):
            outfit = args[i + 1].strip()
    if not want_musical and not want_hero and not outfit:
        want_musical = True
        want_hero = True

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    results: list[dict] = []

    if want_musical:
        orn_dir = ASSETS / "ornaments" / f"musical_{stamp}"
        for subject, preset in (
            ("ornament:musical", "beauty"),
            ("ornament:treble_clef", "beauty"),
            ("ornament:sheet_music_rail", "three_quarter"),
        ):
            oid = subject.split(":", 1)[1]
            results.append(
                one(subject, preset, "nikki", orn_dir / f"{oid}_stage_{preset}.png", no_passport=no_passport)
            )

    if outfit:
        results.append(
            one(
                f"outfit:{outfit}",
                "beauty",
                "nikki",
                ASSETS / "character" / f"melusina_outfit_{outfit}_stage_beauty.png",
                no_passport=no_passport,
            )
        )

    if want_hero:
        hero_dir = ASSETS / "character" / f"hero_{stamp}"
        for preset, lights in (
            ("beauty", "nikki"),
            ("three_quarter", "jewelry"),
            ("front", "nikki"),
            ("silhouette", "silhouette"),
        ):
            results.append(
                one(
                    "melusina",
                    preset,
                    lights,
                    hero_dir / f"melusina_hero_{preset}_{lights}.png",
                    no_passport=no_passport,
                )
            )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": sum(1 for r in results if r["ok"]),
        "fail": sum(1 for r in results if not r["ok"]),
        "results": results,
        "hero_dir": str(ASSETS / "character" / f"hero_{stamp}") if want_hero else None,
        "musical_dir": str(ASSETS / "ornaments" / f"musical_{stamp}") if want_musical else None,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log(f"done {summary['ok']}/{len(results)} → {AUDIT}")
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
