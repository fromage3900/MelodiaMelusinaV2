# -*- coding: utf-8 -*-
"""Melodia Melusina Shot Deck - reproducible varied renders + cutscene stills.

A shot deck is a JSON file describing named shots. Each shot picks:
  * camera (scene object name, must be a CAMERA)
  * frame (scene frame to set; None = current frame)
  * accessories (list of slot indexes for surreal_arch_accessory_toggles,
    or "ALL_VISIBLE" / "ALL_HIDDEN"; None = leave untouched)
  * resolution (width/height/percentage; None = current render settings)
  * output (subfolder + filename template, {frame}/{shot} placeholders)

Two entry points:
  * N-panel addon: deploy/surreal_arch/melodia_shotdeck.py (View3D > Sidebar > Melodia Shotdeck)
  * Headless CLI: blender -b <stage.blend> -P Tools/melodia_shotdeck.py -- <deck.json>

Writes PNG plates to Saved/Renders/ShotDecks/<deck_name>/<shot>_<frame>.png
and a deck manifest JSON next to the plates (ShotDeck/<deck>_manifest.json).

Read-only for scene data other than: frame, camera selection, accessory
toggles, and render output settings while rendering each shot (restored after).
Never saves the stage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import bpy

DECK_DIR_NAME = "ShotDecks"
OUTPUT_ROOT = Path(r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Renders") if os.path.isdir(r"G:\EnvironmentPortfolio\BS_GodFile\Saved\Renders") else Path(__file__).resolve().parents[2] / "Saved" / "Renders"

ACCESSORY_PROP = "surreal_arch_accessory_toggles"


class MelodiaShotDeckError(Exception):
    pass


def _resolve_deck_path(raw: str) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p
    candidates = [
        Path(__file__).resolve().parent / raw,
        Path(__file__).resolve().parent / "shotdecks" / raw,
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise MelodiaShotDeckError(f"deck file not found: {raw}")


def _load_deck(raw: str) -> dict:
    path = _resolve_deck_path(raw)
    try:
        with open(path, "r", encoding="utf-8") as f:
            deck = json.load(f)
    except Exception as exc:
        raise MelodiaShotDeckError(f"cannot read deck {path}: {exc}")
    if "shots" not in deck or not isinstance(deck["shots"], list):
        raise MelodiaShotDeckError(f"deck {path} has no 'shots' list")
    for i, shot in enumerate(deck["shots"]):
        if "camera" not in shot:
            raise MelodiaShotDeckError(f"shot {i} missing 'camera'")
    return deck


def _apply_accessories(shot: dict) -> list:
    scene = bpy.context.scene
    if not hasattr(scene, ACCESSORY_PROP):
        return []
    toggles = getattr(scene, ACCESSORY_PROP)
    if shot.get("accessories") is None:
        return []
    spec = shot["accessories"]
    if spec == "ALL_VISIBLE":
        return [t for t in toggles]
    if spec == "ALL_HIDDEN":
        return [t for t in toggles]
    changed = []
    for idx in spec:
        if 0 <= idx < len(toggles) and toggles[idx] != (not shot.get("hide", False)):
            toggles[idx] = not shot.get("hide", False)
            changed.append(idx)
    return changed


def _apply_camera(name: str) -> None:
    cam = bpy.data.objects.get(name)
    if cam is None or cam.type != "CAMERA":
        raise MelodiaShotDeckError(f"camera not found: {name}")
    for s in bpy.data.scenes:
        s.camera = cam


def _shot_filename(shot: dict, frame: int) -> str:
    tpl = shot.get("template", "{shot}_{frame}")
    return tpl.format(shot=shot.get("name", "shot"), frame=str(frame).zfill(4))


def render_shot(shot: dict) -> dict:
    scene = bpy.context.scene
    saved = {
        "camera": scene.camera.name if scene.camera else None,
        "frame": scene.frame_current,
        "res": (scene.render.resolution_x, scene.render.resolution_y,
                scene.render.resolution_percentage),
        "filepath": scene.render.filepath,
        "toggles": list(getattr(scene, ACCESSORY_PROP)) if hasattr(scene, ACCESSORY_PROP) else None,
    }
    try:
        frame = shot.get("frame")
        if frame is not None:
            scene.frame_set(int(frame))
        _apply_camera(shot["camera"])
        changed = _apply_accessories(shot)
        if shot.get("resolution"):
            scene.render.resolution_x = int(shot["resolution"][0])
            scene.render.resolution_y = int(shot["resolution"][1])
            scene.render.resolution_percentage = int(shot.get("resolution_percentage", 100))
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = shot.get("color_mode", "RGB")
        deck_name = shot.get("deck", "deck")
        outdir = OUTPUT_ROOT / DECK_DIR_NAME / deck_name
        outdir.mkdir(parents=True, exist_ok=True)
        fname = _shot_filename(shot, scene.frame_current)
        outpath = outdir / f"{fname}.png"
        scene.render.filepath = str(outpath)
        bpy.ops.render.render(write_still=True)
        return {
            "shot": shot.get("name", "?"),
            "camera": shot["camera"],
            "frame": scene.frame_current,
            "file": str(outpath),
            "accessory_changed": changed,
            "size": outpath.stat().st_size if outpath.exists() else None,
        }
    finally:
        if saved["camera"]:
            scene.camera = bpy.data.objects.get(saved["camera"])
        scene.frame_set(saved["frame"])
        (scene.render.resolution_x, scene.render.resolution_y,
         scene.render.resolution_percentage) = saved["res"]
        scene.render.filepath = saved["filepath"]
        if saved["toggles"] is not None and hasattr(scene, ACCESSORY_PROP):
            for i, v in enumerate(saved["toggles"]):
                if i < len(getattr(scene, ACCESSORY_PROP)):
                    getattr(scene, ACCESSORY_PROP)[i] = v


def run_deck(raw: str, report: bool = True) -> dict:
    deck = _load_deck(raw)
    deck_name = deck.get("name", Path(_resolve_deck_path(raw)).stem)
    results = []
    for shot in deck["shots"]:
        shot = dict(shot)
        shot["deck"] = deck_name
        try:
            results.append(render_shot(shot))
        except Exception as exc:
            results.append({"shot": shot.get("name", "?"), "error": str(exc)})
    manifest = {
        "deck": deck_name,
        "generated_at": datetime.now().isoformat(),
        "shots_total": len(deck["shots"]),
        "shots_ok": sum(1 for r in results if r.get("file")),
        "shots": results,
    }
    outdir = OUTPUT_ROOT / DECK_DIR_NAME / deck_name
    outdir.mkdir(parents=True, exist_ok=True)
    mp = outdir / f"{deck_name}_manifest.json"
    with open(mp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    if report:
        for r in results:
            if r.get("error"):
                print(f"[SHOTDECK] FAIL {r.get('shot')}: {r['error']}")
            else:
                print(f"[SHOTDECK] OK {r.get('shot')} {r.get('file')}")
        print(f"[SHOTDECK] {manifest['shots_ok']}/{manifest['shots_total']} shots -> {outdir}")
    return manifest


# ---------------------------------------------------------------------------
# Blender operator + panel
# ---------------------------------------------------------------------------

class MELODIA_OT_render_shotdeck(bpy.types.Operator):
    bl_idname = "melodia.render_shotdeck"
    bl_label = "Render Melodia Shot Deck"
    bl_description = "Render every shot in the selected deck JSON to named plates"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            run_deck(self.filepath)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, "Shot deck rendered")
        return {"FINISHED"}


class MELODIA_PT_shotdeck(bpy.types.Panel):
    bl_label = "Melodia Shotdeck"
    bl_idname = "MELODIA_PT_shotdeck"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia Shotdeck"

    def draw(self, context):
        self.layout.operator(MELODIA_OT_render_shotdeck.bl_idname, text="Render Shot Deck...", icon="RENDER_STILL")


CLASSES = (MELODIA_OT_render_shotdeck, MELODIA_PT_shotdeck)


def register():
    for cls in CLASSES:
        if not hasattr(bpy.types, cls.bl_idname):
            bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        if hasattr(bpy.types, cls.bl_idname):
            bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description="Render a Melodia shot deck")
    parser.add_argument("deck", help="path to deck JSON (or name inside deploy/surreal_arch/shotdecks)")
    args = parser.parse_args(argv)
    try:
        run_deck(args.deck)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
