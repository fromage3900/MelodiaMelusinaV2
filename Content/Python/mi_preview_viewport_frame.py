"""One-frame viewport preview for selected MI (SceneCapture — no HighResShot).

Run in-editor with MI selected in Content Browser:
  py Content/Python/mi_preview_viewport_frame.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import mi_preview_apply as apply_mod
import mi_preview_manifest as manifest_mod
import mi_preview_scenecapture as capture_mod
import mi_preview_studio as studio

OUT_DIR = studio.PREVIEW_FRAME_DIR


def _selected_mi_path() -> str | None:
    import unreal

    utility = unreal.EditorUtilityLibrary
    selected = utility.get_selected_assets()
    for asset in selected or []:
        try:
            if asset.is_a(unreal.MaterialInterface.static_class()):
                return asset.get_path_name()
        except Exception:
            continue
    return None


def capture_preview_frame(*, mi_path: str | None = None) -> dict:
    import setup_material_preview_studio as studio_setup
    import unreal

    mi_game_path = mi_path or _selected_mi_path()
    if not mi_game_path:
        return {"ok": False, "error": "no_material_selected"}

    if "." not in mi_game_path.split("/")[-1]:
        name = mi_game_path.rsplit("/", 1)[-1]
        mi_game_path = f"{mi_game_path}.{name}"

    manifest = manifest_mod.load_manifest()
    entry = None
    for row in manifest.get("entries") or []:
        if row.get("asset_path") == mi_game_path or row.get("id") in mi_game_path:
            entry = row
            break
    if not entry:
        mi_name = mi_game_path.rsplit("/", 1)[-1].split(".")[0]
        entry = manifest_mod.route_preview(name=mi_name, source="viewport_adhoc")

    studio_setup.build_studio(backdrop=str(entry.get("backdrop") or studio.DEFAULT_BACKDROP))
    apply_mod.apply_preview_entry(entry)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    camera = None
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == studio.TAG_CAMERA:
            camera = actor
            break
    if camera:
        loc = studio.orbit_camera_position(studio.LOOP_FRAMES // 4)
        rot = studio.look_at_rotation(loc, (0.0, 0.0, 40.0))
        camera.set_actor_location(unreal.Vector(*loc), False, False)
        camera.set_actor_rotation(studio.ue_rotator(rot), False)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mi_id = entry.get("id") or "preview"
    out_path = OUT_DIR / f"{mi_id}_preview_frame.png"
    world = capture_mod.get_editor_world()
    if not world or not camera:
        return {"ok": False, "error": "world_or_camera_missing", "id": mi_id}

    shot = capture_mod.capture_still_from_camera(
        world,
        camera,
        out_path,
        width=studio.LOOP_RESOLUTION,
        height=studio.LOOP_RESOLUTION,
    )
    return {
        "ok": bool(shot.get("ok")),
        "id": mi_id,
        "output_path": str(out_path),
        "asset_path": mi_game_path,
        "preview_mesh": entry.get("preview_mesh"),
        "backdrop": entry.get("backdrop"),
        "capture": shot,
    }


def main() -> int:
    result = capture_preview_frame()
    if "json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
