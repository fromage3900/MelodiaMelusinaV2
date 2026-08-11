"""Camera-only prep for L_MaterialPreview_Studio.

- Removes Melodia void backdrop (no cyclorama)
- Does NOT touch lighting, PPV, materials, or set-dress
- Ensures + pilots orbit / still / orbit-A / orbit-B cine cameras

  py Content/Python/prep_nikki_material_studio.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "nikki_material_studio_prep.json"

# Camera labels — framing only
CAM_ORBIT = studio.TAG_CAMERA  # CineCamera_PreviewLoop
CAM_STILL = "CineCamera_StillBeauty"
CAM_DETAIL = "CineCamera_Detail"

BACKDROP_LABELS = (
    "Backdrop_MelodiaVoid",
    "Backdrop_Cyclorama",
    "MI_Preview_Backdrop",
)


def _find_by_label(eas, label: str):
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == label:
            return actor
    return None


def _destroy_backdrops(eas) -> list[str]:
    removed = []
    for actor in list(eas.get_all_level_actors() or []):
        label = actor.get_actor_label() or ""
        tags = list(getattr(actor, "tags", []) or [])
        if (
            label in BACKDROP_LABELS
            or studio.TAG_BACKDROP in tags
            or "Backdrop" in label
            or "Cyclorama" in label
            or "MelodiaVoid" in label
        ):
            try:
                eas.destroy_actor(actor)
                removed.append(label)
            except Exception:
                pass
    return removed


def _spawn_or_get_camera(eas, label: str, loc, rot):
    import unreal

    cam = _find_by_label(eas, label)
    if not cam:
        cam = eas.spawn_actor_from_class(
            unreal.CineCameraActor.static_class(),
            unreal.Vector(*loc),
            unreal.Rotator(*rot),
        )
        if cam:
            cam.set_actor_label(label)
    if not cam:
        return None
    cam.set_actor_location(unreal.Vector(*loc), False, False)
    cam.set_actor_rotation(unreal.Rotator(*rot), False)
    cine = cam.get_cine_camera_component()
    if cine:
        try:
            cine.set_editor_property("current_focal_length", float(studio.CAMERA_FOCAL_LENGTH))
        except Exception:
            pass
        try:
            cine.set_editor_property("current_aperture", 4.0)
        except Exception:
            pass
        for prop in ("filmback_settings", "filmback"):
            try:
                settings = cine.get_editor_property(prop)
                settings.set_editor_property("sensor_width", 24.0)
                settings.set_editor_property("sensor_height", 24.0)
                cine.set_editor_property(prop, settings)
                break
            except Exception:
                continue
    return cam


def _look_target() -> tuple[float, float, float]:
    """Aim at existing swatch if present, else origin."""
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    swatch = _find_by_label(eas, "MI_Preview_Swatch") or _find_by_label(eas, studio.TAG_SWATCH)
    if swatch:
        loc = swatch.get_actor_location()
        return (float(loc.x), float(loc.y), float(loc.z))
    return (0.0, 0.0, 40.0)


def prep_cameras() -> dict:
    import unreal

    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not les or not eas:
        return {"ok": False, "error": "no_editor_subsystems"}

    # Load studio map if needed — do not rebuild lighting/PP/backdrop
    try:
        world = None
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            world = ues.get_editor_world()
        world_name = world.get_name() if world else ""
        if "MaterialPreview_Studio" not in str(world_name):
            les.load_level(studio.LEVEL)
    except Exception as exc:
        return {"ok": False, "error": f"load:{exc}"}

    removed = _destroy_backdrops(eas)
    target = _look_target()

    # Three framings around the swatch — lights/materials untouched
    orbit_loc = studio.orbit_camera_position(studio.LOOP_FRAMES // 4)
    still_loc = studio.orbit_camera_position(0)
    detail_loc = (
        orbit_loc[0] * 0.72,
        orbit_loc[1] * 0.72,
        orbit_loc[2] * 0.85 + 20.0,
    )

    cams = {}
    for label, loc in (
        (CAM_ORBIT, orbit_loc),
        (CAM_STILL, still_loc),
        (CAM_DETAIL, detail_loc),
    ):
        rot = studio.look_at_rotation(loc, target)
        cam = _spawn_or_get_camera(eas, label, loc, rot)
        cams[label] = {
            "ok": cam is not None,
            "loc": list(loc),
            "rot": list(rot),
            "look_at": list(target),
        }

    pilot = _find_by_label(eas, CAM_ORBIT)
    if pilot and hasattr(les, "pilot_level_actor"):
        try:
            les.pilot_level_actor(pilot)
        except Exception:
            pass

    les.save_current_level()

    report = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "level": studio.LEVEL,
        "scope": "cameras_only",
        "void_backdrop_removed": removed,
        "cameras": cams,
        "piloted": CAM_ORBIT,
        "note": "No lighting / PPV / material / void changes.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "removed_backdrop": removed, "cameras": list(cams.keys())}))
    unreal.log(f"[MIStudioPrep] Cameras only. Removed backdrop: {removed}")
    return report


def main() -> int:
    report = prep_cameras()
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
