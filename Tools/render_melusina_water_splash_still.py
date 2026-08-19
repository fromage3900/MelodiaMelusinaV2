# -*- coding: utf-8 -*-
"""EEVEE WaterFX splash still after FLIP bake (frames with visible drips).

Requires Melusina_WaterFX tip-tuned + baked (see Tools/tune_melusina_hair_drip.py).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import bpy

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
OUT_DIR = ROOT / "my-site-clean" / "generated" / "assets" / "character"
FLOOR_Z = -0.2935


def main() -> str:
    scene = bpy.context.scene
    floor = bpy.data.objects.get("Studio_FloorCard")
    if floor and abs(floor.location.z - FLOOR_Z) > 0.001:
        raise RuntimeError(f"FloorCard Z drift {floor.location.z}")

    wfx = bpy.data.collections.get("Melusina_WaterFX")
    if not wfx:
        raise RuntimeError("Melusina_WaterFX missing")
    wfx.hide_render = False
    wfx.hide_viewport = False

    scene.render.engine = "BLENDER_EEVEE"
    cam = bpy.data.objects.get("Cam_Beauty") or bpy.data.objects.get("Cam_Macro")
    if cam:
        scene.camera = cam
    scene.frame_set(min(48, scene.frame_end))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().strftime("%Y%m%d")
    out = OUT_DIR / f"melusina_water_splash_{stamp}_01.png"
    n = 1
    while out.exists() and n < 99:
        n += 1
        out = OUT_DIR / f"melusina_water_splash_{stamp}_{n:02d}.png"

    scene.render.filepath = str(out)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    wfx.hide_render = True
    print(f"[splash-still] wrote {out}", flush=True)
    return str(out)


if __name__ == "__main__":
    main()
