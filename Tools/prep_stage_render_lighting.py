# -*- coding: utf-8 -*-
"""Print / optionally apply Melodia stage lighting recipes without saving.

Usage (stage open in Blender or headless):
  blender -b KitbashExport/Melodia_Portfolio_Stage_v14.blend -P Tools/prep_stage_render_lighting.py
  blender ... -P Tools/prep_stage_render_lighting.py -- --preset nikki --apply
  blender ... -P Tools/prep_stage_render_lighting.py -- --preset jewelry --apply --no-compositor

Never calls save_mainfile. Honors MELUSINA_SHADER_AGENT_STOP.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
AUDIT = ROOT / "Saved" / "Audit" / "stage_lighting_preflight.json"
STOP = ROOT / "Saved" / "Audit" / "MELUSINA_SHADER_AGENT_STOP"

# Mirror melodia_stage_shot.LIGHT_RECIPES — single place artists can check before shoot
LIGHT_RECIPES = {
    "Nikki": {
        "L_KeyWarm": (900, (1.0, 0.92, 0.85)),
        "L_RimPink": (550, (1.0, 0.55, 0.75)),
        "L_FillCool": (280, (0.7, 0.85, 1.0)),
        "L_GoldKick": (140, (1.0, 0.85, 0.45)),
    },
    "Jewelry": {
        "L_KeyWarm": (1100, (1.0, 0.95, 0.9)),
        "L_RimPink": (320, (0.9, 0.7, 1.0)),
        "L_FillCool": (180, (0.75, 0.9, 1.0)),
        "L_GoldKick": (420, (1.0, 0.88, 0.5)),
    },
    "Silhouette": {
        "L_KeyWarm": (40, (1.0, 0.9, 0.8)),
        "L_RimPink": (900, (1.0, 0.45, 0.7)),
        "L_FillCool": (60, (0.5, 0.6, 0.9)),
        "L_GoldKick": (20, (1.0, 0.8, 0.4)),
    },
}

CAMERAS = ("Cam_Beauty", "Cam_Front", "Cam_Back", "Cam_Macro", "Cam_Low")


def log(msg: str) -> None:
    print(f"[light-prep] {msg}", flush=True)


def argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return []


def block_saves() -> None:
    def _blocked(*_a, **_k):
        raise RuntimeError("Stage save blocked (STOP / lighting prep)")

    bpy.ops.wm.save_mainfile = _blocked  # type: ignore[assignment]
    bpy.ops.wm.save_as_mainfile = _blocked  # type: ignore[assignment]


def snapshot_lights() -> dict:
    out = {}
    for name in ("L_KeyWarm", "L_RimPink", "L_FillCool", "L_GoldKick"):
        o = bpy.data.objects.get(name)
        if o and o.type == "LIGHT":
            out[name] = {
                "energy": float(o.data.energy),
                "color": tuple(round(c, 4) for c in o.data.color),
                "hide_render": bool(o.hide_render),
            }
    return out


def apply_preset(name: str) -> None:
    recipe = LIGHT_RECIPES[name]
    for light_name, (energy, color) in recipe.items():
        o = bpy.data.objects.get(light_name)
        if o and o.type == "LIGHT":
            o.data.energy = float(energy)
            o.data.color = color
            o.hide_render = False
    lights = bpy.data.collections.get("Lights")
    if lights:
        lights.hide_render = False


def quiet_noise() -> None:
    for name in (
        "Melusina_WaterFX",
        "Melusina_HairDrip",
        "FX_Grease_Scene4",
        "Review_Queue",
        "Surreal_Regen_Starlight",
    ):
        coll = bpy.data.collections.get(name)
        if coll:
            coll.hide_render = True


def main() -> int:
    block_saves()
    args = argv()
    apply = "--apply" in args
    quiet = "--quiet-fx" in args or apply
    no_comp = "--no-compositor" in args or apply
    preset = "Nikki"
    if "--preset" in args:
        i = args.index("--preset")
        if i + 1 < len(args):
            key = args[i + 1].strip().lower()
            preset = {"nikki": "Nikki", "jewelry": "Jewelry", "silhouette": "Silhouette"}.get(key, "Nikki")

    before = snapshot_lights()
    cams = {n: (bpy.data.objects.get(n) is not None) for n in CAMERAS}
    world = bpy.context.scene.world.name if bpy.context.scene.world else None

    if no_comp:
        bpy.context.scene.render.use_compositing = False
        bpy.context.scene.use_nodes = False
        log("compositor disabled (mauve-blank guard)")
    if quiet:
        quiet_noise()
        log("quieted WaterFX / Grease / Review noise collections")
    if apply:
        apply_preset(preset)
        log(f"applied preset {preset}")

    after = snapshot_lights()
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filepath": bpy.data.filepath,
        "stop_flag": STOP.exists(),
        "saved_stage": False,
        "world": world,
        "cameras": cams,
        "preset_requested": preset,
        "applied": apply,
        "lights_before": before,
        "lights_after": after,
        "recipes": {k: {ln: {"energy": e, "color": c} for ln, (e, c) in v.items()} for k, v in LIGHT_RECIPES.items()},
        "status_doc": "Saved/Audit/PORTFOLIO_PLATE_STATUS_20260715.md",
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log(f"wrote {AUDIT}")
    for n, ok in cams.items():
        log(f"  camera {n}: {'ok' if ok else 'MISSING'}")
    for n, info in after.items():
        log(f"  {n} energy={info['energy']:.1f} hide_r={info['hide_render']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
