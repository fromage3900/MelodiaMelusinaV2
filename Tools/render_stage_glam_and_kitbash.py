# -*- coding: utf-8 -*-
"""EEVEE stills from the live portfolio stage glam lighting - no stage save.

Respects MELUSINA_SHADER_AGENT_STOP / sheet_hud_loop_STOP:
  - never bpy.ops.wm.save_mainfile / save_as_mainfile
  - never clear Melusina materials or W_MelodiaStudio / stage worlds
  - leave studio lamp energies as authored in the .blend (current glam)

Usage:
  blender -b KitbashExport/Melodia_Portfolio_Stage_v14.blend ^
    -P Tools/render_stage_glam_and_kitbash.py -- --all

  blender -b ... -P Tools/render_stage_glam_and_kitbash.py -- --melusina
  blender -b ... -P Tools/render_stage_glam_and_kitbash.py -- --kitbash
  blender -b ... -P Tools/render_stage_glam_and_kitbash.py -- --kitbash --only rose_window,vault_ribs
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from melodia_stage_paths import resolve_stage_blend  # noqa: E402
import melodia_stage_shot as shot  # noqa: E402
import batch_eevee_komikaze_portfolio as batch  # noqa: E402

SITE_ASSETS = ROOT / "my-site-clean" / "generated" / "assets"
AUDIT = ROOT / "Saved" / "Audit"
STOP_FLAGS = (
    AUDIT / "MELUSINA_SHADER_AGENT_STOP",
    AUDIT / "sheet_hud_loop_STOP",
)

# Site hero kitbash set (beauty_34 + front where the lookbook uses them)
KITBASH_HEROES = (
    "rose_window",
    "vault_ribs",
    "spiral_stair",
    "filigree_ring",
    "column_capital",
    "corbel",
    "crown_molding",
    "torus_knot",
    "rosette",
    "quatrefoil",
    "door_archway",
    "pendant_finial",
    "woven_ring",
    "gothic_tracery",
    "oculus_frame",
)

MELUSINA_SHOTS = (
    ("beauty", "Cam_Beauty", "melusina_beauty_eevee_{stamp}_01.png"),
    ("glam_full", "Cam_Beauty", "melusina_eevee_glam_{stamp}_01.png"),
    ("glam_bust", "Cam_Front", "melusina_eevee_glam_{stamp}_02.png"),
    ("glam_tq", "Cam_Beauty", "melusina_eevee_glam_{stamp}_03.png"),
    ("glam_close", "Cam_Macro", "melusina_eevee_glam_{stamp}_04.png"),
    ("glam_portrait", "Cam_Front", "melusina_eevee_glam_{stamp}_05.png"),
)


def log(msg: str) -> None:
    print(f"[glam-kitbash] {msg}", flush=True)


def _argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def assert_no_save_context() -> None:
    for flag in STOP_FLAGS:
        if flag.exists():
            log(f"STOP present: {flag.name} - render-only, will not save stage")
            break
    # Hard guard: wrap save ops if someone imports us
    def _blocked(*_a, **_k):
        raise RuntimeError("Stage save blocked while STOP flags / glam update tool is active")

    if hasattr(bpy.ops.wm, "save_mainfile"):
        bpy.ops.wm.save_mainfile = _blocked  # type: ignore[assignment]
    if hasattr(bpy.ops.wm, "save_as_mainfile"):
        bpy.ops.wm.save_as_mainfile = _blocked  # type: ignore[assignment]


def ensure_stage_open() -> Path:
    stage = resolve_stage_blend()
    cur = Path(bpy.data.filepath or "")
    if cur.resolve() != stage.resolve():
        if not stage.is_file():
            raise FileNotFoundError(stage)
        log(f"opening {stage}")
        bpy.ops.wm.open_mainfile(filepath=str(stage))
    else:
        log(f"already on {stage.name}")
    return stage


def setup_eevee_preserve() -> None:
    """Set render output settings only - do not retouch world or Melusina mats."""
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 2000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    # AudVis/compositor mauve-blank trap - stills write raw View Layer only
    scene.render.use_compositing = False
    scene.use_nodes = False
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 64
    # Quiet FX that fill the frame mauve/brown in headless
    for name in (
        "Melusina_WaterFX",
        "Melusina_HairDrip",
        "FX_Hero",
        "FX_Grease_Scene4",
        "Set_Diorama",
        "Review_Queue",
    ):
        coll = bpy.data.collections.get(name)
        if coll:
            coll.hide_render = True
    for o in bpy.data.objects:
        if o.type == "VOLUME" or "FLIP" in o.name.upper() or "Domain" in o.name:
            o.hide_render = True


def stamp_from_args(args: list[str]) -> str:
    if "--stamp" in args:
        i = args.index("--stamp")
        if i + 1 < len(args):
            return args[i + 1].strip()
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def render_still(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    ok = path.is_file() and path.stat().st_size > 50_000
    log(f"{'OK' if ok else 'FAIL'} {path.name} ({path.stat().st_size if path.is_file() else 0} B)")
    return {
        "path": str(path),
        "ok": ok,
        "bytes": path.stat().st_size if path.is_file() else 0,
    }


def render_melusina(stamp: str) -> list[dict]:
    setup_eevee_preserve()
    shot.isolate_melusina()
    # Ensure studio lights collection visible - energies stay as authored
    lights = bpy.data.collections.get("Lights")
    if lights:
        lights.hide_render = False
    for name in ("L_KeyWarm", "L_RimPink", "L_FillCool", "L_GoldKick"):
        lit = bpy.data.objects.get(name)
        if lit and lit.type == "LIGHT":
            lit.hide_render = False
            log(f"  light {name} energy={lit.data.energy:.1f}")

    out_dir = SITE_ASSETS / "character"
    results: list[dict] = []
    for label, cam_name, template in MELUSINA_SHOTS:
        cam = bpy.data.objects.get(cam_name) or bpy.data.objects.get("Cam_Beauty")
        if cam is None:
            results.append({"label": label, "ok": False, "error": "no camera"})
            continue
        bpy.context.scene.camera = cam
        # Slight aim nudge for bust/portrait vs full - keep Cam transforms intact
        out = out_dir / template.format(stamp=stamp)
        r = render_still(out)
        r["label"] = label
        r["camera"] = cam.name
        results.append(r)
    return results


def _kitbash_entries(only: set[str] | None) -> list[dict]:
    # Flatten ornament assets from waves 1-3
    entries = []
    seen = set()
    for wave in (1, 2, 3):
        for e in batch.WAVES.get(wave, []):
            if e.get("group") != "ornament":
                continue
            if e["id"] in seen:
                continue
            if only and e["id"] not in only:
                continue
            if e["id"] not in KITBASH_HEROES and only is None:
                continue
            seen.add(e["id"])
            entries.append(e)
    return entries


def _aim_at(cam: bpy.types.Object, objs: list[bpy.types.Object], elev: float = 12.0, azim: float = 35.0) -> None:
    if not objs:
        return
    coords = [o.matrix_world.translation for o in objs]
    mid = sum(coords, Vector()) / len(coords)
    # radius from bounding-ish max distance
    radius = max((o.dimensions.length for o in objs), default=1.0) * 0.55
    radius = max(radius, 0.35)
    er = math.radians(elev)
    ar = math.radians(azim)
    offset = Vector(
        (
            radius * 2.2 * math.cos(er) * math.sin(ar),
            -radius * 2.2 * math.cos(er) * math.cos(ar),
            radius * 2.2 * math.sin(er) + mid.z * 0.05,
        )
    )
    cam.location = mid + offset
    direction = mid - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    if cam.data and hasattr(cam.data, "lens"):
        cam.data.lens = 50.0


def render_kitbash(only: set[str] | None) -> list[dict]:
    setup_eevee_preserve()
    if not os.path.isfile(batch.KOMIKAZE_BLEND):
        log("FATAL Komikaze blend missing")
        return [{"ok": False, "error": "komikaze missing"}]

    # Hide Melusina / diorama for ornament plates; keep glam world + lights
    for name in (
        "Asset_melusina",
        "FX_Hero",
        "Set_Diorama",
        "Melusina_WaterFX",
        "Asset_sirmelodious",
        "MusicalOrnaments_Review",
        "Review_Queue",
    ):
        coll = bpy.data.collections.get(name)
        if coll:
            coll.hide_render = True

    for name in ("L_KeyWarm", "L_RimPink", "L_FillCool", "L_GoldKick"):
        lit = bpy.data.objects.get(name)
        if lit and lit.type == "LIGHT":
            lit.hide_render = False
            log(f"  light {name} energy={lit.data.energy:.1f} (preserved)")

    cam = bpy.data.objects.get("Cam_Beauty")
    if cam is None:
        return [{"ok": False, "error": "Cam_Beauty missing"}]
    bpy.context.scene.camera = cam

    subject = batch.ensure_coll("RenderSubject")
    subject.hide_render = False
    results: list[dict] = []
    entries = _kitbash_entries(only)
    log(f"kitbash assets={len(entries)}")

    for entry in entries:
        fbx = entry["fbx"]
        if not os.path.isfile(fbx):
            results.append({"id": entry["id"], "ok": False, "error": f"missing {fbx}"})
            continue
        log(f"=== {entry['id']}")
        batch.clear_render_subject()
        meshes = batch.import_fbx(fbx)
        if not meshes:
            results.append({"id": entry["id"], "ok": False, "error": "no meshes"})
            continue
        for o in meshes:
            batch.link_to_coll(o, subject)

        mat = batch.komikaze_append(entry["shader"])
        if mat is None:
            mat = bpy.data.materials.new(f"M_Fallback_{entry['id']}")
            mat.use_nodes = True
        for o in meshes:
            batch.assign_material(o, mat)

        mid, radius = batch.ground_and_measure(meshes)
        _ = mid, radius
        _aim_at(cam, meshes, elev=14.0, azim=38.0)

        out_root = SITE_ASSETS / entry["out_dir"]
        shots = entry.get("shots") or ["beauty_34", "front"]
        # Always ensure beauty_34 for site heroes
        if "beauty_34" not in shots:
            shots = ["beauty_34"] + list(shots)

        for shot_id in shots:
            if shot_id == "front":
                _aim_at(cam, meshes, elev=8.0, azim=5.0)
            elif shot_id == "macro":
                _aim_at(cam, meshes, elev=25.0, azim=20.0)
            elif shot_id == "three_quarter":
                _aim_at(cam, meshes, elev=12.0, azim=48.0)
            else:
                _aim_at(cam, meshes, elev=14.0, azim=38.0)
            filename = f"{entry['id']}_komikaze_{shot_id}.png"
            path = out_root / filename
            r = render_still(path)
            r["id"] = entry["id"]
            r["shot"] = shot_id
            results.append(r)

    batch.clear_render_subject()
    return results


def main() -> int:
    args = _argv()
    want_m = "--melusina" in args or "--all" in args
    want_k = "--kitbash" in args or "--all" in args
    if not want_m and not want_k:
        want_m = want_k = True

    only: set[str] | None = None
    if "--only" in args:
        i = args.index("--only")
        if i + 1 < len(args):
            only = {x.strip() for x in args[i + 1].split(",") if x.strip()}

    stamp = stamp_from_args(args)
    assert_no_save_context()
    stage = ensure_stage_open()
    setup_eevee_preserve()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": str(stage),
        "stamp": stamp,
        "preserved_lights": True,
        "saved_stage": False,
        "melusina": [],
        "kitbash": [],
    }

    if want_m:
        log("--- Melusina glam (lights preserved) ---")
        report["melusina"] = render_melusina(stamp)
    if want_k:
        log("--- Kitbash heroes (lights preserved) ---")
        report["kitbash"] = render_kitbash(only)

    AUDIT.mkdir(parents=True, exist_ok=True)
    out_json = AUDIT / "glam_kitbash_render_report.json"
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ok_m = sum(1 for r in report["melusina"] if r.get("ok"))
    ok_k = sum(1 for r in report["kitbash"] if r.get("ok"))
    log(f"done melusina_ok={ok_m}/{len(report['melusina'])} kitbash_ok={ok_k}/{len(report['kitbash'])}")
    log(f"report {out_json}")
    # Fail if majority blank
    total = ok_m + ok_k
    need = max(1, (len(report["melusina"]) + len(report["kitbash"])) // 2)
    return 0 if total >= need else 2


if __name__ == "__main__":
    raise SystemExit(main())
