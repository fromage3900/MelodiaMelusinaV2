# -*- coding: utf-8 -*-
"""Export Flip Fluids fluid_surface to Alembic for UE Geometry Cache (Layer C cine).

Uses the domain custom frame range (not a hardcoded 1-96). Does not save the
stage. Does not replace SK_MelusinaHair. Restores scene timeline after export.

GUI:
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\export_melusina_hair_flip_alembic.py").read())
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import bpy

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
CACHE = ROOT / "KitbashExport" / "flip_cache_melusina_waterhair"
SURFACE = "fluid_surface"


def _bobj_count() -> int:
    if not CACHE.is_dir():
        return 0
    return sum(1 for _ in CACHE.rglob("*.bobj"))


def _domain_frames() -> tuple[int, int]:
    domain = bpy.data.objects.get("FF_MelusinaHair_Domain")
    if domain is None or not getattr(domain, "flip_fluid", None):
        raise RuntimeError("Missing FF_MelusinaHair_Domain")
    sim = domain.flip_fluid.domain.simulation
    return int(sim.frame_start), int(sim.frame_end)


def main() -> None:
    n = _bobj_count()
    if n < 8:
        raise RuntimeError(
            f"Flip cache has {n} .bobj under {CACHE}. Bake into the SSOT cache before export."
        )
    frame_start, frame_end = _domain_frames()
    obj = bpy.data.objects.get(SURFACE)
    if obj is None:
        raise RuntimeError(f"Missing object {SURFACE}")

    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_abc = CACHE.parent / f"flip_melusina_waterhair_v22_{stamp}.abc"
    scene = bpy.context.scene
    saved = (scene.frame_start, scene.frame_end, scene.frame_current)
    win = bpy.context.window_manager.windows[0]
    area = next((a for a in win.screen.areas if a.type == "VIEW_3D"), None)
    region = next((r for r in area.regions if r.type == "WINDOW"), None) if area else None
    try:
        with bpy.context.temp_override(
            window=win,
            screen=win.screen,
            area=area,
            region=region,
            scene=scene,
            view_layer=bpy.context.view_layer,
            active_object=obj,
            selected_objects=[obj],
        ):
            bpy.ops.wm.alembic_export(
                filepath=str(out_abc),
                selected=True,
                uvs=True,
                normals=True,
                start=frame_start,
                end=frame_end,
                global_scale=100.0,
                evaluation_mode="VIEWPORT",
                as_background_job=False,
                init_scene_frame_range=False,
            )
    finally:
        scene.frame_start, scene.frame_end = saved[0], saved[1]
        scene.frame_set(saved[2])
    print(f"[hair-flip-abc] wrote {out_abc} bobj={n} frames={frame_start}-{frame_end}", flush=True)


main()
