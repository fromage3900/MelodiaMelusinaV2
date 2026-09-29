"""Capture high-end beauty plates and orbit turntable frames for the Gemstone family.

Runs inside UE Editor via Monolith in L_MaterialPreview_Studio.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import unreal
import mi_preview_apply as apply_mod
import mi_preview_scenecapture as sc
import mi_preview_studio as studio

PROJECT_ROOT = studio.PROJECT_ROOT
OUT_BASE = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "MaterialLoops"
PREVIEW_FRAMES_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "MaterialLoops" / "PreviewFrames"

GEMSTONE_TARGETS = [
    {
        "id": "MI_Gemstone_CelestialDiamond",
        "asset_path": "/Game/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_CelestialDiamond.MI_Gemstone_CelestialDiamond",
        "backdrop": "Cosmic_DeepField",
        "preview_mesh": "sphere",
        "mesh_scale": [1.55, 1.55, 1.55],
    },
    {
        "id": "MI_Gemstone_Aquamarine_Circlet",
        "asset_path": "/Game/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_Aquamarine_Circlet.MI_Gemstone_Aquamarine_Circlet",
        "backdrop": "Sakura_SoftVoid",
        "preview_mesh": "sphere",
        "mesh_scale": [1.55, 1.55, 1.55],
    },
    {
        "id": "MI_Gemstone_VoidOrchid_Earrings",
        "asset_path": "/Game/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_VoidOrchid_Earrings.MI_Gemstone_VoidOrchid_Earrings",
        "backdrop": "Cosmic_DeepField",
        "preview_mesh": "sphere",
        "mesh_scale": [1.55, 1.55, 1.55],
    },
    {
        "id": "MI_Gemstone_RosyQuartz_Chladni",
        "asset_path": "/Game/EnvSandbox/Materials/Instances/Gemstone/MI_Gemstone_RosyQuartz_Chladni.MI_Gemstone_RosyQuartz_Chladni",
        "backdrop": "Sakura_SoftVoid",
        "preview_mesh": "sphere",
        "mesh_scale": [1.55, 1.55, 1.55],
    },
]


def run_gemstone_studio_captures() -> dict:
    world = sc.get_editor_world()
    if not world:
        return {"ok": False, "error": "world_not_found"}

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    camera = None
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() in ("CineCamera_StillBeauty", "CineCamera_PreviewLoop"):
            camera = actor
            break

    if not camera:
        return {"ok": False, "error": "camera_not_found"}

    swatch = apply_mod._find_actor_by_tag(eas, studio.TAG_SWATCH) or apply_mod._find_actor_by_label(eas, "MI_Preview_Swatch")
    if not swatch:
        return {"ok": False, "error": "swatch_not_found"}

    results = []
    PREVIEW_FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    for entry in GEMSTONE_TARGETS:
        mi_id = entry["id"]
        out_dir = OUT_BASE / mi_id
        out_dir.mkdir(parents=True, exist_ok=True)

        unreal.log(f"[Gemstone Studio] Staging {mi_id}...")
        # 1. Apply swatch & backdrop
        apply_mod.apply_backdrop(eas, entry["backdrop"])
        apply_mod.apply_swatch(eas, entry)

        # 2. Warm up rendering pipeline
        sc._warmup(world, camera)

        # 3. Capture Beauty Still (1080x1080)
        beauty_path = out_dir / "beauty_still.png"
        preview_copy = PREVIEW_FRAMES_DIR / f"{mi_id}.png"
        res = sc.capture_still_from_camera(world, camera, beauty_path, width=1080, height=1080)

        # Copy to preview frame dir for web preview
        if beauty_path.is_file():
            import shutil
            shutil.copyfile(beauty_path, preview_copy)

        # 4. Capture 8-frame turntable orbit sequence for loop creation
        turntable_frames = []
        original_rot = swatch.get_actor_rotation()
        num_frames = 12

        for f_idx in range(num_frames):
            angle = (f_idx / num_frames) * 360.0
            swatch.set_actor_rotation(unreal.Rotator(0.0, angle, 0.0), False)
            time.sleep(0.05)
            frame_path = out_dir / f"frame_{f_idx:04d}.png"
            f_res = sc.capture_still_from_camera(world, camera, frame_path, width=720, height=720)
            if frame_path.is_file():
                turntable_frames.append(str(frame_path))

        swatch.set_actor_rotation(original_rot, False)

        results.append({
            "id": mi_id,
            "beauty_still": str(beauty_path),
            "preview_frame": str(preview_copy),
            "turntable_frames": len(turntable_frames),
            "capture_result": res,
        })
        unreal.log(f"[Gemstone Studio] Finished {mi_id}: beauty still + {len(turntable_frames)} turntable frames.")

    return {
        "ok": True,
        "count": len(results),
        "captures": results,
    }


if __name__ == "__main__":
    import json
    res = run_gemstone_studio_captures()
    print(json.dumps(res, indent=2))
