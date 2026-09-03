"""Capture portfolio renders from the editor viewport (no scene edits).

Run in-editor:
  py Content/Python/render_exporter.py
  py Content/Python/render_exporter.py --width 1920 --height 1080

Outputs:
  Saved/Portfolio/Renders/Hero/
  Saved/Portfolio/Renders/Breakdown/
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import portfolio_output_layout as portfolio_fs

HERO_DIR = portfolio_fs.HERO_DIR
BREAKDOWN_DIR = portfolio_fs.BREAKDOWN_DIR

TAG_HERO = "Portfolio_Hero"
TAG_BREAKDOWN = "Portfolio_Breakdown"
TAG_ALT = "Portfolio_Alt"

DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
VIEWPORT_SETTLE_SEC = 0.35


def _parse_resolution() -> tuple[int, int]:
    width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
    for index, arg in enumerate(sys.argv):
        if arg == "--width" and index + 1 < len(sys.argv):
            try:
                width = int(sys.argv[index + 1])
            except ValueError:
                pass
        if arg == "--height" and index + 1 < len(sys.argv):
            try:
                height = int(sys.argv[index + 1])
            except ValueError:
                pass
    return width, height


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _get_editor_world():
    """Return the editor world, preferring the UE 5.8 subsystem API."""
    import unreal

    try:
        ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if ues:
            world = ues.get_editor_world()
            if world:
                return world
    except Exception:
        pass
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def _get_level_slug() -> str:
    import unreal

    try:
        world = _get_editor_world()
        if world:
            level = world.get_current_level()
            if level:
                outer = level.get_outer()
                if outer:
                    return outer.get_name()
    except Exception:
        pass
    return "level"


def _level_editor_subsystem():
    import unreal

    return unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def _take_high_res_screenshot(path: Path, width: int, height: int) -> None:
    import unreal

    path.parent.mkdir(parents=True, exist_ok=True)
    filename = str(path)
    last_exc: Exception | None = None
    for call in (
        lambda: unreal.AutomationLibrary.take_high_res_screenshot(width, height, filename),
        lambda: unreal.AutomationLibrary.take_high_res_screenshot(
            width, height, filename, False
        ),
    ):
        try:
            call()
            return
        except Exception as exc:
            last_exc = exc
    if last_exc:
        raise last_exc


def _list_cine_cameras() -> list[dict]:
    import unreal

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cameras: list[dict] = []
    for actor in eas.get_all_level_actors() or []:
        try:
            if not actor.is_a(unreal.CineCameraActor.static_class()):
                continue
        except Exception:
            continue
        tags = [str(tag) for tag in list(getattr(actor, "tags", []) or [])]
        cameras.append(
            {
                "actor": actor,
                "label": actor.get_actor_label(),
                "tags": tags,
            }
        )
    cameras.sort(key=lambda entry: entry.get("label") or "")
    return cameras


def _pick_alternate_camera(cameras: list[dict]):
    import unreal

    for tag in (TAG_BREAKDOWN, TAG_ALT):
        for entry in cameras:
            if tag in entry["tags"]:
                return entry["actor"], f"tag:{tag}"

    pilot_actor = None
    try:
        les = _level_editor_subsystem()
        if les and hasattr(les, "get_pilot_level_actor"):
            pilot_actor = les.get_pilot_level_actor()
    except Exception:
        pilot_actor = None

    for entry in cameras:
        actor = entry["actor"]
        if pilot_actor and actor == pilot_actor:
            continue
        if TAG_HERO in entry["tags"] and len(cameras) > 1:
            continue
        return actor, "cine_camera"

    if len(cameras) >= 2:
        return cameras[1]["actor"], "second_cine_camera"

    if len(cameras) == 1:
        return cameras[0]["actor"], "only_cine_camera"

    return None, "none"


def _pilot_camera(actor) -> None:
    import unreal

    les = _level_editor_subsystem()
    if les and hasattr(les, "pilot_level_actor"):
        les.pilot_level_actor(actor)
        return
    unreal.EditorLevelLibrary.pilot_level_actor(actor)


def _eject_pilot() -> None:
    import unreal

    les = _level_editor_subsystem()
    if les and hasattr(les, "eject_pilot_level_actor"):
        les.eject_pilot_level_actor()
        return
    unreal.EditorLevelLibrary.eject_pilot_level_actor()


def capture_hero_render(*, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> dict:
    """Capture the current editor viewport as a hero image."""
    import unreal

    level_slug = _get_level_slug()
    ts = _timestamp_slug()
    filename = f"hero_{level_slug}_{ts}_{width}x{height}.png"
    out_path = HERO_DIR / filename

    try:
        _take_high_res_screenshot(out_path, width, height)
    except Exception as exc:
        unreal.log_warning(f"[RenderExporter] hero capture failed: {exc}")
        return {"ok": False, "error": str(exc), "kind": "hero"}

    unreal.log(f"[RenderExporter] hero -> {out_path}")
    return {
        "ok": True,
        "kind": "hero",
        "path": str(out_path),
        "filename": filename,
        "width": width,
        "height": height,
        "level": level_slug,
        "source": "current_viewport",
    }


def capture_breakdown_render(*, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> dict:
    """Capture an alternate camera angle when a CineCamera is available."""
    import unreal

    cameras = _list_cine_cameras()
    camera, reason = _pick_alternate_camera(cameras)
    if not camera:
        unreal.log("[RenderExporter] breakdown skipped — no alternate camera")
        return {
            "ok": False,
            "skipped": True,
            "kind": "breakdown",
            "reason": reason,
        }

    level_slug = _get_level_slug()
    ts = _timestamp_slug()
    label = camera.get_actor_label().replace(" ", "_")
    filename = f"breakdown_{level_slug}_{label}_{ts}_{width}x{height}.png"
    out_path = BREAKDOWN_DIR / filename

    piloted = False
    try:
        _pilot_camera(camera)
        piloted = True
        time.sleep(VIEWPORT_SETTLE_SEC)
        _take_high_res_screenshot(out_path, width, height)
    except Exception as exc:
        unreal.log_warning(f"[RenderExporter] breakdown capture failed: {exc}")
        return {
            "ok": False,
            "error": str(exc),
            "kind": "breakdown",
            "camera": camera.get_actor_label(),
            "selection": reason,
        }
    finally:
        if piloted:
            try:
                _eject_pilot()
            except Exception as exc:
                unreal.log_warning(f"[RenderExporter] pilot eject failed: {exc}")

    unreal.log(f"[RenderExporter] breakdown -> {out_path}")
    return {
        "ok": True,
        "kind": "breakdown",
        "path": str(out_path),
        "filename": filename,
        "width": width,
        "height": height,
        "level": level_slug,
        "camera": camera.get_actor_label(),
        "selection": reason,
        "source": "cine_camera_pilot",
    }


def export_renders(*, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> dict:
    """Capture hero (current viewport) and breakdown (alternate angle if available)."""
    portfolio_fs.ensure_portfolio_layout()
    portfolio_fs.organize_portfolio_outputs()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hero": capture_hero_render(width=width, height=height),
        "breakdown": capture_breakdown_render(width=width, height=height),
    }


def main() -> int:
    width, height = _parse_resolution()
    result = export_renders(width=width, height=height)
    if "json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    hero_ok = result["hero"].get("ok")
    breakdown_ok = result["breakdown"].get("ok") or result["breakdown"].get("skipped")
    return 0 if hero_ok and breakdown_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
