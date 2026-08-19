"""
Melusina Fade Day/Night world for portfolio stage.

*** DO NOT RUN ON LIVE STAGE WITHOUT ARTIST CONSENT ***
  - Calls world.node_tree.nodes.clear() (lookdev-destructive)
  - Honors Saved/Audit/MELUSINA_SHADER_AGENT_STOP — aborts if present
  - Never bpy.ops.wm.save_mainfile on Melodia_Portfolio_Stage_*.blend

Rebuilds ``W_Melodia_FadeDayNight`` by mixing Fade Assets
``Day Skydome`` + ``Night Skydome`` (from fadeassets/data/data.blend).

Night Mix value node: 0 = full day, 1 = full night (default 0.72 Melodia-forward).

Keeps ``W_MelodiaStudio_Fade`` (night-only) as a fallback datablock if present.

Usage (open stage in Blender 5.1):
  exec(open(r"G:\\EnvironmentPortfolio\\BS_GodFile\\Tools\\setup_melusina_fade_daynight_sky.py").read())
"""
from __future__ import annotations

import json
from pathlib import Path

import bpy

ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile")
STOP = ROOT / "Saved" / "Audit" / "MELUSINA_SHADER_AGENT_STOP"
FADE_DATA = Path(
    r"C:\Users\froma\AppData\Roaming\Blender Foundation\Blender\5.1"
    r"\extensions\user_default\fadeassets\data\data.blend"
)
WORLD_NAME = "W_Melodia_FadeDayNight"
DEFAULT_NIGHT = 0.72
AUDIT = ROOT / "Saved" / "Audit" / "melusina_fade_daynight_sky.json"


def _ensure_fade_groups() -> tuple[bpy.types.NodeTree, bpy.types.NodeTree]:
    day_g = bpy.data.node_groups.get("Day Skydome")
    night_g = bpy.data.node_groups.get("Night Skydome")
    if day_g and night_g:
        return day_g, night_g

    if not FADE_DATA.is_file():
        raise FileNotFoundError(f"Fade Assets missing: {FADE_DATA}")

    before = {w.name for w in bpy.data.worlds}
    with bpy.data.libraries.load(str(FADE_DATA), link=False) as (data_from, data_to):
        want = [n for n in ("Sky Day", "Sky Night") if n in data_from.worlds]
        data_to.worlds = want
    _ = [w for w in bpy.data.worlds if w.name not in before]

    day_g = bpy.data.node_groups.get("Day Skydome")
    night_g = bpy.data.node_groups.get("Night Skydome")
    if not day_g or not night_g:
        # Accept .00x suffixes
        for ng in bpy.data.node_groups:
            low = ng.name.lower()
            if day_g is None and "day" in low and "skydome" in low and "shadeless" not in low:
                day_g = ng
            if night_g is None and "night" in low and "skydome" in low and "shadeless" not in low:
                night_g = ng
    if not day_g or not night_g:
        raise RuntimeError("Could not load Day/Night Skydome groups from Fade Assets")
    return day_g, night_g


def setup_fade_daynight_sky(night_mix: float = DEFAULT_NIGHT) -> str:
    if STOP.is_file():
        msg = f"ABORT: {STOP} present — world nodes.clear blocked (lookdev freeze)."
        print(f"[fade-daynight] {msg}")
        return msg

    day_g, night_g = _ensure_fade_groups()

    old = bpy.data.worlds.get(WORLD_NAME)
    if old:
        bpy.data.worlds.remove(old, do_unlink=True)

    world = bpy.data.worlds.new(WORLD_NAME)
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (900, 0)

    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (650, 0)
    mix.label = "Day/Night Mix"

    bg_day = nt.nodes.new("ShaderNodeBackground")
    bg_day.location = (350, 180)
    bg_day.label = "Fade Sky Day"
    bg_day.inputs["Strength"].default_value = 0.85

    bg_night = nt.nodes.new("ShaderNodeBackground")
    bg_night.location = (350, -160)
    bg_night.label = "Fade Sky Night"
    bg_night.inputs["Strength"].default_value = 0.7

    g_day = nt.nodes.new("ShaderNodeGroup")
    g_day.node_tree = day_g
    g_day.location = (50, 180)
    g_day.label = "Day Skydome"

    g_night = nt.nodes.new("ShaderNodeGroup")
    g_night.node_tree = night_g
    g_night.location = (50, -160)
    g_night.label = "Night Skydome"

    fac = nt.nodes.new("ShaderNodeValue")
    fac.location = (-200, 0)
    fac.label = "Night Mix (0=Day, 1=Night)"
    fac.outputs[0].default_value = float(night_mix)

    nt.links.new(g_day.outputs["Color"], bg_day.inputs["Color"])
    nt.links.new(g_night.outputs["Color"], bg_night.inputs["Color"])
    nt.links.new(fac.outputs[0], mix.inputs["Fac"])
    nt.links.new(bg_day.outputs["Background"], mix.inputs[1])
    nt.links.new(bg_night.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    if hasattr(world, "mist_settings"):
        world.mist_settings.use_mist = True
        world.mist_settings.start = 4.0
        world.mist_settings.depth = 18.0

    bpy.context.scene.world = world

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(
        json.dumps(
            {
                "world": WORLD_NAME,
                "night_mix": night_mix,
                "day_group": day_g.name,
                "night_group": night_g.name,
                "fade_data": str(FADE_DATA),
                "fallback_kept": "W_MelodiaStudio_Fade" in bpy.data.worlds,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[fade-daynight] active={WORLD_NAME} night_mix={night_mix}")
    return WORLD_NAME


if __name__ == "__main__" or True:
    setup_fade_daynight_sky()
