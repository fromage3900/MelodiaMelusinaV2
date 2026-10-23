# Melodia Sky Forge - equirectangular bake + TD sidecar (bpy).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Bakes the current MEL_SkyForge world to an equirectangular EXR (Cycles
# panoramic camera) plus the flat theme sidecar JSON. Staging only: nothing is
# written into Content/; UE/TD import is a separate, deliberate step.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bpy


def _apply_beat_values(w_base: float, w_off: float, aur_base: float, aur_mult: float) -> None:
    """Push one bar-loop frame's motion values onto every sky surface.

    Dome material uses named nodes (authored by sky_builder); the world
    node group path updates the interface defaults its instances mirror.
    Missing surfaces are skipped: a frame with no motion surfaces still
    renders the static sky.
    """
    from . import sky_builder

    mat = bpy.data.materials.get(sky_builder.DOME_MATERIAL_NAME)
    if mat is not None and mat.use_nodes:
        nt = mat.node_tree
        noise = nt.nodes.get("MELSKY_Noise")
        if noise is not None:
            noise.inputs["W"].default_value = w_base + w_off
        aur = nt.nodes.get("MELSKY_AuroraStrength")
        if aur is not None:
            aur.inputs[1].default_value = aur_base * aur_mult
    ng = bpy.data.node_groups.get(sky_builder.GROUP_NAME)
    if ng is not None:
        for item in ng.interface.items_tree:
            if getattr(item, "in_out", "") != "INPUT":
                continue
            try:
                if item.name == "CloudSeed":
                    item.default_value = w_base + w_off
                elif item.name == "AuroraStrength":
                    item.default_value = aur_base * aur_mult
            except (TypeError, ValueError):
                pass


def bake_equirect(
    out_dir: Path | str,
    theme: dict[str, Any] | None = None,
    resolution: tuple[int, int] = (2048, 1024),
    samples: int = 16,
    frames: int = 1,
) -> dict[str, Any]:
    """Render the scene world as equirect EXR frame(s) + optional sidecar JSON.

    frames=1 renders one static EXR (classic filename, byte-identical to the
    original bake contract). frames>1 bakes one 4/4 BAR as
    `<theme_id>_sky_f00.exr..fNN.exr`, driving cloud drift / aurora pulse
    from the theme's bpm + sky.motion. Frame 0 is always the static sky.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    from . import sky_builder

    report: dict[str, Any] = {"blender": bpy.app.version_string, "resolution": list(resolution)}

    theme_id = theme.get("theme_id", "custom") if theme else "custom"
    n_frames = max(1, int(frames)) if theme is not None else 1
    flat = None
    beats = None
    if theme is not None:
        from . import sky_core

        flat = sky_core.flatten_for_td(theme)
        beats = sky_core.beat_offsets(
            n_frames,
            bpm=int(flat.get("bpm") or 0),
            drift_per_beat=float(flat.get("cloud_drift_per_beat", 0.0)),
            aurora_pulse=float(flat.get("aurora_pulse_per_beat", 0.0)),
        )

    if n_frames == 1:
        frame_specs = [(beats[0] if beats else {"frame": 0}, out / f"{theme_id}_sky.exr")]
    else:
        frame_specs = [(b, out / f"{theme_id}_sky_f{b['frame']:02d}.exr") for b in beats]

    # Panoramic camera looking at +Y; Cycles is the reliable equirect path.
    # clip_end must reach past the dome (default 100 would clip it away);
    # use 10x the dome radius or a huge fallback when no dome exists.
    dome = bpy.data.objects.get(sky_builder.DOME_OBJECT_NAME)
    dome_radius = max(
        (abs(s) for s in dome.scale), default=0.0,
    ) if dome is not None else 0.0
    cam_data = bpy.data.cameras.new("_MELSkyForgeCam")
    cam_data.type = 'PANO'
    cam_data.clip_end = max(dome_radius * 10.0, 10000.0)
    try:
        cam_data.panorama_type = 'EQUIRECTANGULAR'
    except AttributeError:  # pre-3.5 layout differs; Cycles still pans via type
        pass
    cam = bpy.data.objects.new("_MELSkyForgeCam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    prev_cam = bpy.context.scene.camera
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    prev_engine = scene.render.engine
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'

    # Camera spawns at (0,0,0); any scene mesh containing that point (the
    # factory-startup cube does!) swallows every ray and bakes a black dome.
    # A sky bake must capture the sky dome (when present) and the world only:
    # hide all scene objects except the dome for the render, restore after.
    prev_hidden = [(obj, obj.hide_render) for obj in scene.objects]
    for obj in scene.objects:
        if obj is not cam and obj.name != sky_builder.DOME_OBJECT_NAME:
            obj.hide_render = True
    try:
        report_frames: list[dict[str, Any]] = []
        weak_visited = False
        for beat, exr_path in frame_specs:
            scene.render.filepath = str(exr_path)
            if beats is not None:
                w_base = float(flat["cloud_seed"])
                aur_base = float(flat["aurora_strength"])
                _apply_beat_values(
                    w_base, float(beat["cloud_w_offset"]),
                    aur_base, float(beat["aurora_pulse_multiplier"]),
                )
            bpy.ops.render.render(write_still=True)
            ok = exr_path.is_file()
            entry: dict[str, Any] = {"frame": beat["frame"], "exr": str(exr_path), "ok": ok}
            if ok:
                img = bpy.data.images.load(str(exr_path), check_existing=False)
                try:
                    px = list(img.pixels)
                    if len(px) // 4:
                        entry["render_max_rgb"] = max(px[0::4] + px[1::4] + px[2::4])
                        if entry["render_max_rgb"] < 1e-4:
                            entry["ok"] = False
                            entry["error"] = "render is uniformly black (max_rgb ~ 0)"
                finally:
                    bpy.data.images.remove(img)
            report_frames.append(entry)
            if not ok and not weak_visited:
                report["ok"] = False
                report["error"] = entry.get("error", "frame bake failed")
                weak_visited = True
        if "ok" not in report:
            report["ok"] = all(e.get("ok") for e in report_frames)
        report["frames"] = report_frames
        if n_frames > 1:
            report["exr"] = str(frame_specs[0][1])
            report["bar_loop"] = {
                "frames": n_frames,
                "phase_of_first": beats[0]["phase"],
                "seconds_per_beat": (60.0 / flat["bpm"]) if flat.get("bpm") else None,
                "note": "frame 0 == static sky; TD maps Beatphase 0..1 to frame index",
            }
        else:
            report["exr"] = str(exr_path)
            if report_frames and report_frames[0].get("ok"):
                report["render_max_rgb"] = report_frames[0].get("render_max_rgb")
    finally:
        for obj, was_hidden in prev_hidden:
            obj.hide_render = was_hidden
        scene.render.engine = prev_engine
        bpy.context.scene.camera = prev_cam
        bpy.data.objects.remove(cam, do_unlink=True)
        bpy.data.cameras.remove(cam_data)

    if flat is not None:
        sidecar = out / f"{theme_id}_sky.params.json"
        sidecar.write_text(json.dumps(flat, indent=2), encoding="utf-8")
        report["sidecar"] = str(sidecar)
        if n_frames > 1 and beats is not None:
            beat_json = out / f"{theme_id}_sky.beat.json"
            beat_json.write_text(json.dumps({"schema": "melodia.sky_beat.v1", "theme_id": theme_id, "beats": beats}, indent=2), encoding="utf-8")
            report["beat_json"] = str(beat_json)

    (out / "bake_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
