# -*- coding: utf-8 -*-
"""Resume cross + zen lantern glam stills on Melodia stage (NO SAVE).

Designed for interactive Blender (MCP / GUI) or:
  blender -b KitbashExport/Melodia_Portfolio_Stage_v14.blend -P Tools/render_cross_zenlantern_mcp_resume.py

Respects MELUSINA_SHADER_AGENT_STOP — never save_mainfile.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT_CROSS = ROOT / "my-site-clean" / "generated" / "assets" / "cross"
OUT_PROPS = ROOT / "my-site-clean" / "generated" / "assets" / "props"
AUDIT = ROOT / "Saved" / "Audit" / "cross_zenlantern_glam_render.json"


def log(msg: str) -> None:
    print(f"[cross-lantern] {msg}", flush=True)


def block_saves() -> None:
    def _blocked(*_a, **_k):
        raise RuntimeError("Stage save blocked while STOP / glam prop render is active")

    bpy.ops.wm.save_mainfile = _blocked  # type: ignore[assignment]
    bpy.ops.wm.save_as_mainfile = _blocked  # type: ignore[assignment]


def setup_eevee() -> None:
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
    scene.render.use_compositing = False
    scene.use_nodes = False
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 48


def hide_noise() -> None:
    for name in (
        "Asset_melusina",
        "FX_Hero",
        "Set_Diorama",
        "Melusina_WaterFX",
        "Melusina_HairDrip",
        "FX_Grease_Scene4",
        "Asset_sirmelodious",
        "MusicalOrnaments_Review",
        "Review_Queue",
        "Surreal_Regen_Starlight",
        "RenderSubject",
    ):
        coll = bpy.data.collections.get(name)
        if coll:
            coll.hide_render = True
    for o in bpy.data.objects:
        if o.type == "VOLUME" or "FLIP" in o.name.upper() or "Domain" in o.name:
            o.hide_render = True
        if o.name.startswith(("Graph_", "_lib_", "_edit_")):
            o.hide_render = True
    for name in ("L_KeyWarm", "L_RimPink", "L_FillCool", "L_GoldKick", "Ground", "Studio_FloorCard", "Studio_Backdrop"):
        o = bpy.data.objects.get(name)
        if o:
            o.hide_render = False


def mesh_center_radius(objs: list[bpy.types.Object]) -> tuple[Vector, float]:
    coords: list[Vector] = []
    for o in objs:
        for c in o.bound_box:
            coords.append(o.matrix_world @ Vector(c))
    mins = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
    maxs = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
    mid = (mins + maxs) * 0.5
    size = maxs - mins
    return mid, max(max(size.x, size.y, size.z) * 0.5, 0.25)


def aim(cam: bpy.types.Object, mid: Vector, radius: float, elev: float, azim: float, lens: float, height_frac: float = 0.45) -> None:
    look = Vector((mid.x, mid.y, mid.z))
    er = math.radians(elev)
    ar = math.radians(azim)
    dist = radius * 2.6
    offset = Vector(
        (
            dist * math.cos(er) * math.sin(ar),
            -dist * math.cos(er) * math.cos(ar),
            dist * math.sin(er) + radius * (height_frac - 0.5) * 0.4,
        )
    )
    cam.location = look + offset
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens


def render_to(path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp.png")
    bpy.context.scene.render.filepath = str(tmp)
    bpy.ops.render.render(write_still=True)
    if tmp.is_file() and tmp.stat().st_size > 80_000:
        try:
            tmp.replace(path)
        except OSError:
            import shutil

            shutil.copy2(tmp, path)
            try:
                tmp.unlink()
            except OSError:
                pass
    ok = path.is_file() and path.stat().st_size > 80_000
    log(f"{'OK' if ok else 'FAIL'} {path.name} ({path.stat().st_size if path.is_file() else 0})")
    return {"path": str(path), "ok": ok, "bytes": path.stat().st_size if path.is_file() else 0}


def set_asset(name: str, on: bool) -> None:
    coll = bpy.data.collections.get(name)
    if coll:
        coll.hide_render = not on


def main() -> int:
    block_saves()
    setup_eevee()
    hide_noise()
    cam = bpy.data.objects.get("Cam_Beauty")
    if not cam:
        log("FATAL Cam_Beauty missing")
        return 1
    bpy.context.scene.camera = cam
    cam_bak = (cam.location.copy(), cam.rotation_euler.copy(), cam.data.lens)

    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    want_cross = "--cross" in argv or "--all" in argv or not argv
    want_lantern = "--lantern" in argv or "--all" in argv or not argv
    force = "--force" in argv

    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "saved_stage": False,
        "cross": [],
        "zenlantern": [],
    }

    if want_cross:
        set_asset("Asset_zenlantern", False)
        set_asset("Asset_cross", True)
        meshes = [
            o
            for o in bpy.data.objects
            if o.type == "MESH" and any(c.name == "Asset_cross" for c in o.users_collection)
        ]
        for o in meshes:
            o.hide_render = False
        mid, radius = mesh_center_radius(meshes)
        log(f"cross meshes={len(meshes)} r={radius:.3f}")
        shots = [
            ("beauty_34", 14, 38, 50, 0.45),
            ("front", 8, 5, 55, 0.5),
            ("macro", 22, 28, 85, 0.7),
            ("low_angle", 4, 40, 35, 0.3),
            ("silhouette", 14, 38, 50, 0.45),
        ]
        for shot_id, elev, azim, lens, hf in shots:
            out = OUT_CROSS / f"cross_komikaze_{shot_id}.png"
            if out.is_file() and out.stat().st_size > 500_000 and not force and shot_id != "silhouette":
                # Re-do silhouette always if missing/old; skip recent good plates unless --force
                if shot_id in ("beauty_34", "front", "macro") and out.stat().st_mtime > 1.7525e9:
                    log(f"skip existing fresh {out.name}")
                    results["cross"].append({"path": str(out), "ok": True, "bytes": out.stat().st_size, "shot": shot_id, "skipped": True})
                    continue
            if shot_id == "silhouette":
                for name, energy in (("L_KeyWarm", 80), ("L_RimPink", 900), ("L_FillCool", 60), ("L_GoldKick", 30)):
                    lit = bpy.data.objects.get(name)
                    if lit and lit.type == "LIGHT":
                        lit.data.energy = energy
            else:
                # leave authored glam energies; gently ensure on
                for name in ("L_KeyWarm", "L_RimPink", "L_FillCool", "L_GoldKick"):
                    lit = bpy.data.objects.get(name)
                    if lit:
                        lit.hide_render = False
            aim(cam, mid, radius, elev, azim, lens, hf)
            r = render_to(out)
            r["shot"] = shot_id
            results["cross"].append(r)

    if want_lantern:
        set_asset("Asset_cross", False)
        set_asset("Asset_zenlantern", True)
        # Prefer high-poly lanternfinal
        show = []
        for o in bpy.data.objects:
            if any(c.name == "Asset_zenlantern" for c in o.users_collection) and o.type == "MESH":
                if o.name == "zenlantern_lanternfinal":
                    o.hide_render = False
                    show.append(o)
                else:
                    o.hide_render = True
        if not show:
            o = bpy.data.objects.get("zenlantern_Retopo_lanternfinal")
            if o:
                o.hide_render = False
                show = [o]
        # turn off lantern's own light — use stage glam
        zl = bpy.data.objects.get("zenlantern_Light")
        if zl:
            zl.hide_render = True
        mid, radius = mesh_center_radius(show)
        log(f"lantern objs={[o.name for o in show]} r={radius:.3f}")
        for shot_id, elev, azim, lens, hf in (
            ("beauty_34", 12, 36, 50, 0.48),
            ("three_quarter", 10, 48, 50, 0.45),
            ("front", 6, 4, 55, 0.5),
        ):
            aim(cam, mid, radius, elev, azim, lens, hf)
            out = OUT_PROPS / f"zenlantern_komikaze_{shot_id}.png"
            r = render_to(out)
            r["shot"] = shot_id
            results["zenlantern"].append(r)

    cam.location, cam.rotation_euler, cam.data.lens = cam_bak[0], cam_bak[1], cam_bak[2]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    ok_c = sum(1 for r in results["cross"] if r.get("ok"))
    ok_l = sum(1 for r in results["zenlantern"] if r.get("ok"))
    log(f"done cross_ok={ok_c}/{len(results['cross'])} lantern_ok={ok_l}/{len(results['zenlantern'])}")
    log(f"report {AUDIT}")
    return 0 if (ok_c + ok_l) > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
