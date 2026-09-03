# -*- coding: utf-8 -*-
"""GUI helper: EEVEE Beauty Nikki still -> dated PNG for site remount.

Run in Stage v7 Text Editor after Blender MCP reconnects (or alone):
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\render_melusina_beauty_still.py").read())

Does not move Studio_FloorCard. Leaves WaterFX / GP Scene4 render-off.
Then: python Tools/assign_plate.py index.hero <png>  (and remount --apply --passport)
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

    scene.render.engine = "BLENDER_EEVEE"
    cam = bpy.data.objects.get("Cam_Beauty")
    if cam:
        scene.camera = cam

    wfx = bpy.data.collections.get("Melusina_WaterFX")
    if wfx:
        wfx.hide_render = True
    gp = bpy.data.collections.get("FX_Grease_Scene4")
    if gp:
        gp.hide_render = True

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().strftime("%Y%m%d")
    out = OUT_DIR / f"melusina_beauty_nikki_{stamp}_01.png"
    # Avoid overwrite collision
    n = 1
    while out.exists() and n < 99:
        n += 1
        out = OUT_DIR / f"melusina_beauty_nikki_{stamp}_{n:02d}.png"

    scene.render.filepath = str(out)
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print(f"[beauty-still] wrote {out}", flush=True)
    return str(out)


if __name__ == "__main__":
    main()
