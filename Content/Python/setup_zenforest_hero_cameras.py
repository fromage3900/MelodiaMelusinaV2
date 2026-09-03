"""Place tagged portfolio hero cameras in ZenForestTest.

Run in-editor (ZenForestTest open or will be loaded):
  py Content/Python/setup_zenforest_hero_cameras.py

Optional:
  py Content/Python/setup_zenforest_hero_cameras.py --level /Game/ZenForestTest
  py Content/Python/setup_zenforest_hero_cameras.py --snap-viewport Cam_Hero_Route

After setup, capture all heroes:
  py Content/Python/render_exporter.py --all-heroes
  # or LiveLink > Capture > All Hero Cameras
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import render_exporter as rex

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "zenforest_hero_cameras.json"
DEFAULT_LEVEL = "/Game/ZenForestTest"

CAMERA_PREFIX = "Cam_Hero_"
BREAKDOWN_PREFIX = "Cam_Breakdown_"


@dataclass(frozen=True)
class CameraSpec:
    label: str
    tags: tuple[str, ...]
    focal_length: float
    # Offset from scene focal point, scaled by scene half-extent (x, y, z).
    offset: tuple[float, float, float]
    look_at_offset: tuple[float, float, float]


HERO_CAMERAS: tuple[CameraSpec, ...] = (
    CameraSpec(
        "Cam_Hero_Establishing",
        (rex.TAG_HERO,),
        28.0,
        (-1.35, -1.15, 0.95),
        (0.0, 0.35, 0.12),
    ),
    CameraSpec(
        "Cam_Hero_Route",
        (rex.TAG_HERO,),
        40.0,
        (0.0, -1.55, 0.18),
        (0.0, 0.65, 0.05),
    ),
    CameraSpec(
        "Cam_Hero_Materials",
        (rex.TAG_HERO,),
        75.0,
        (0.42, -0.28, 0.14),
        (-0.05, 0.15, 0.0),
    ),
)

BREAKDOWN_CAMERA = CameraSpec(
    "Cam_Breakdown_Shader",
    (rex.TAG_BREAKDOWN,),
    50.0,
    (0.55, -0.75, 0.22),
    (0.0, 0.2, 0.08),
)


def _parse_args() -> dict:
    level = DEFAULT_LEVEL
    snap_label = ""
    argv = list(sys.argv)
    for index, arg in enumerate(argv):
        if arg == "--level" and index + 1 < len(argv):
            level = argv[index + 1]
        if arg == "--snap-viewport" and index + 1 < len(argv):
            snap_label = argv[index + 1]
    return {"level": level, "snap_label": snap_label}


def _load_level(level_path: str) -> None:
    import unreal

    asset = f"{level_path}.{level_path.rsplit('/', 1)[-1]}"
    if not unreal.EditorAssetLibrary.does_asset_exist(asset):
        raise RuntimeError(f"level missing: {level_path}")
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    les.load_level(level_path)


def _destroy_existing_cameras(eas) -> int:
    removed = 0
    for actor in list(eas.get_all_level_actors() or []):
        label = actor.get_actor_label()
        if not (label.startswith(CAMERA_PREFIX) or label.startswith(BREAKDOWN_PREFIX)):
            continue
        eas.destroy_actor(actor)
        removed += 1
    return removed


def _find_focal_point(eas):
    import unreal

    keywords = ("TORII", "SANDO", "SHRINE", "HAIDEN", "GB_ZEN")
    for actor in eas.get_all_level_actors() or []:
        label = actor.get_actor_label().upper()
        if any(key in label for key in keywords):
            return actor.get_actor_location(), f"actor:{actor.get_actor_label()}"

    for actor in eas.get_all_level_actors() or []:
        try:
            if actor.is_a(unreal.Landscape.static_class()):
                origin, _extent = actor.get_actor_bounds(False)
                return origin, f"landscape:{actor.get_actor_label()}"
        except Exception:
            continue

    # World origin fallback for empty/dev levels.
    return unreal.Vector(0.0, 0.0, 0.0), "origin"


def _scene_half_extent(eas, focal) -> tuple:
    import unreal

    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")
    found = False
    for actor in eas.get_all_level_actors() or []:
        try:
            origin, extent = actor.get_actor_bounds(False)
        except Exception:
            continue
        if extent.x <= 1.0 and extent.y <= 1.0 and extent.z <= 1.0:
            continue
        found = True
        min_x = min(min_x, origin.x - extent.x)
        max_x = max(max_x, origin.x + extent.x)
        min_y = min(min_y, origin.y - extent.y)
        max_y = max(max_y, origin.y + extent.y)
        min_z = min(min_z, origin.z - extent.z)
        max_z = max(max_z, origin.z + extent.z)

    if not found:
        return (6000.0, 6000.0, 1200.0)

    half_x = max(2500.0, (max_x - min_x) * 0.5)
    half_y = max(2500.0, (max_y - min_y) * 0.5)
    half_z = max(400.0, (max_z - min_z) * 0.5)
    return (half_x, half_y, half_z)


def _offset_position(focal, half_extent, offset: tuple[float, float, float]):
    import unreal

    hx, hy, hz = half_extent
    ox, oy, oz = offset
    return unreal.Vector(
        focal.x + ox * hx,
        focal.y + oy * hy,
        focal.z + oz * hz,
    )


def _look_rotation(location, target):
    import unreal

    return unreal.MathLibrary.find_look_at_rotation(location, target)


def _configure_cine_camera(cam, focal_length: float) -> None:
    comp = cam.get_cine_camera_component()
    if not comp:
        return
    comp.set_editor_property("current_focal_length", float(focal_length))
    comp.set_editor_property("focus_settings", comp.get_editor_property("focus_settings"))
    try:
        focus = comp.get_editor_property("focus_settings")
        focus.set_editor_property("focus_method", unreal.CameraFocusMethod.DISABLE)
        comp.set_editor_property("focus_settings", focus)
    except Exception:
        pass


def _set_tags(actor, tags: tuple[str, ...]) -> None:
    actor.set_editor_property("tags", list(tags))


def _spawn_camera(eas, spec: CameraSpec, focal, half_extent):
    import unreal

    location = _offset_position(focal, half_extent, spec.offset)
    look_target = _offset_position(focal, half_extent, spec.look_at_offset)
    rotation = _look_rotation(location, look_target)
    cam = eas.spawn_actor_from_class(
        unreal.CineCameraActor.static_class(),
        location,
        rotation,
    )
    if not cam:
        raise RuntimeError(f"failed to spawn {spec.label}")
    cam.set_actor_label(spec.label)
    _set_tags(cam, spec.tags)
    _configure_cine_camera(cam, spec.focal_length)
    return {
        "label": spec.label,
        "tags": list(spec.tags),
        "focal_length": spec.focal_length,
        "location": [location.x, location.y, location.z],
        "rotation": [rotation.pitch, rotation.yaw, rotation.roll],
    }


def snap_selected_viewport_to_camera(label: str) -> dict:
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    selected = eas.get_selected_level_actors() or []
    if not selected:
        raise RuntimeError("Select a CineCameraActor first")

    cam = selected[0]
    cls = cam.get_class()
    if not cls or not cls.is_child_of(unreal.CineCameraActor.static_class()):
        raise RuntimeError("Selected actor is not a CineCameraActor")

    loc, rot = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
    cam.set_actor_location(loc, False, False)
    cam.set_actor_rotation(rot, False)
    cam.set_actor_label(label)

    tags = list(cam.get_editor_property("tags") or [])
    if rex.TAG_HERO not in tags and rex.TAG_BREAKDOWN not in tags:
        tags.append(rex.TAG_HERO)
    cam.set_editor_property("tags", tags)

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {
        "label": label,
        "location": [loc.x, loc.y, loc.z],
        "rotation": [rot.pitch, rot.yaw, rot.roll],
        "tags": tags,
    }


def setup_hero_cameras(*, level: str = DEFAULT_LEVEL) -> dict:
    import unreal

    _load_level(level)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

    removed = _destroy_existing_cameras(eas)
    focal, focal_source = _find_focal_point(eas)
    half_extent = _scene_half_extent(eas, focal)

    cameras: list[dict] = []
    for spec in HERO_CAMERAS:
        cameras.append(_spawn_camera(eas, spec, focal, half_extent))
    cameras.append(_spawn_camera(eas, BREAKDOWN_CAMERA, focal, half_extent))

    les.save_current_level()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "focal_source": focal_source,
        "focal_point": [focal.x, focal.y, focal.z],
        "half_extent": list(half_extent),
        "removed_existing": removed,
        "cameras": cameras,
        "next_steps": [
            "Pilot each camera and nudge framing if needed.",
            "py Content/Python/render_exporter.py --all-heroes",
            "Run ingest_unreal_portfolio.ps1 after capture.",
        ],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[HeroCameras] placed {len(cameras)} cameras -> {REPORT}")
    return report


def main() -> int:
    args = _parse_args()
    if args["snap_label"]:
        result = snap_selected_viewport_to_camera(args["snap_label"])
    else:
        result = setup_hero_cameras(level=args["level"])
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
