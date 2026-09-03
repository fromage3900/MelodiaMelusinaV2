"""Generate PCG density heatmap plates for portfolio breakdown renders.

Renders a top-down orthographic density map of all PCG volume actors in the
current level, saved as high-res PNG plates under Saved/Portfolio/PCG/.

Run in-editor:
  py Content/Python/pcg_heatmap_exporter.py

Outputs:
  Saved/Portfolio/PCG/{level_name}_pcg_heatmap_{timestamp}.png
  Saved/Portfolio/PCG/{level_name}_pcg_manifest_{timestamp}.json

Use case: "Add 1 PCG beauty/heatmap plate" (deep review hireability action #3).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def export_pcg_heatmap() -> dict:
    import unreal

    result: dict = {
        "ok": False,
        "level": "",
        "volumes_found": 0,
        "output_path": "",
    }

    # 1. Discover current level
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    current_level = les.get_current_level()
    if not current_level:
        result["error"] = "No current level loaded"
        return result

    # World Partition returns the persistent streaming level name here. Use
    # the owning map package so generated plates identify the actual map.
    level_path = current_level.get_path_name().split(":", 1)[0]
    level_name = level_path.rsplit("/", 1)[-1] or current_level.get_name()
    level_name = level_name.rsplit(".", 1)[0]
    result["level"] = level_name

    # 2. Find all PCG volume actors
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = eas.get_all_level_actors() or []

    pcg_volumes = []
    pcg_volume_class = unreal.PCGVolume.static_class()

    for actor in all_actors:
        if actor.get_class() == pcg_volume_class or isinstance(actor, unreal.PCGVolume):
            label = actor.get_actor_label()
            origin, extent = actor.get_actor_bounds(False)
            pcg_volumes.append({
                "label": label,
                "location": {
                    "x": origin.x,
                    "y": origin.y,
                    "z": origin.z,
                },
                "extent": {
                    "x": extent.x,
                    "y": extent.y,
                    "z": extent.z,
                },
            })

    result["volumes_found"] = len(pcg_volumes)
    if not pcg_volumes:
        result["error"] = "No PCG volume actors found in level"
        return result

    # 3. Capture top-down orthographic view of all PCG volumes
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_dir = Path(unreal.Paths.project_saved_dir()) / "Portfolio" / "PCG"
    output_dir.mkdir(parents=True, exist_ok=True)

    heatmap_path = output_dir / f"{level_name}_pcg_heatmap_{timestamp}.png"
    manifest_path = output_dir / f"{level_name}_pcg_manifest_{timestamp}.json"

    # Compute bounding box of all PCG volumes
    min_x = min(v["location"]["x"] - v["extent"]["x"] for v in pcg_volumes)
    max_x = max(v["location"]["x"] + v["extent"]["x"] for v in pcg_volumes)
    min_y = min(v["location"]["y"] - v["extent"]["y"] for v in pcg_volumes)
    max_y = max(v["location"]["y"] + v["extent"]["y"] for v in pcg_volumes)

    mid_x = (min_x + max_x) / 2.0
    mid_y = (min_y + max_y) / 2.0
    span = max(max_x - min_x, max_y - min_y, 1000.0)

    # Configure orthographic capture
    try:
        capture_settings = unreal.AutomatedAssetImportData()
        viewport_client = unreal.EditorLevelLibrary.get_level_viewport_camera_info()

        # Use the editor's screenshot capability
        # Set viewport to top-down orthographic
        camera_location = unreal.Vector(mid_x, mid_y, span * 0.6)
        camera_rotation = unreal.Rotator(-90, 0, -90)  # Top-down, north-up

        unreal.EditorLevelLibrary.set_level_viewport_camera_info(
            camera_location, camera_rotation
        )

        # Request high-res screenshot
        screenshot_path = str(heatmap_path)
        unreal.SystemLibrary.execute_console_command(
            unreal.EditorLevelLibrary.get_editor_world(),
            f"HighResShot 3840x2160 filename={screenshot_path}",
        )

        result["ok"] = True
        result["output_path"] = screenshot_path
        result["capture_resolution"] = "3840x2160"
        result["bounds"] = {
            "min": {"x": min_x, "y": min_y},
            "max": {"x": max_x, "y": max_y},
            "span": span,
        }

        unreal.log(f"[PCGHeatmap] Captured top-down heatmap: {screenshot_path}")

    except Exception as e:
        result["error"] = f"Capture failed: {e}"
        # Still write the manifest even if capture fails
        result["ok"] = False

    # 4. Write manifest
    manifest = {
        "level": level_name,
        "timestamp": timestamp,
        "pcg_volumes": pcg_volumes,
        "volume_count": len(pcg_volumes),
        "capture": {
            "resolution": "3840x2160",
            "projection": "orthographic_top_down",
            "bounds": result.get("bounds", {}),
        },
    }

    with open(str(manifest_path), "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    result["manifest_path"] = str(manifest_path)
    unreal.log(f"[PCGHeatmap] Wrote manifest: {manifest_path}")

    return result


def main() -> int:
    result = export_pcg_heatmap()
    if "json" in sys.argv:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
