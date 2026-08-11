"""Retake NikkiPriority material stills on L_MaterialPreview_Studio.

Melodia void + soft 3-point (no WP / no UDS). SceneCapture2D sync export.

  py Content/Python/retake_material_stills.py
  py Content/Python/retake_material_stills.py --batch nikki
  py Content/Python/retake_material_stills.py --only MI_Show_NikkiHero
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mi_preview_apply as apply_mod
import mi_preview_manifest as manifest_mod
import mi_preview_scenecapture as capture_mod
import mi_preview_studio as studio

PROJECT_ROOT = studio.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "Materials" / "Retake"
NIGHTSHIFT_DIR = PROJECT_ROOT / "Saved" / "Portfolio" / "Renders" / "NightShift"
SITE_NIGHTSHIFT = PROJECT_ROOT / "my-site-clean" / "generated" / "assets" / "nightshift"
AUDIT = PROJECT_ROOT / "Saved" / "Audit" / "material_stills_retake.json"
WIDTH = studio.LOOP_RESOLUTION
HEIGHT = studio.LOOP_RESOLUTION

# Alias for callers / encode tools
NIKKI_PRIORITY = list(studio.NIKKI_PRIORITY)
SITE_BATCH = list(studio.NIKKI_PRIORITY)  # legacy name → Nikki lens


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_studio() -> dict:
    import setup_material_preview_studio as setup

    return setup.build_studio(backdrop=studio.DEFAULT_BACKDROP)


def _find_camera(eas):
    for actor in eas.get_all_level_actors() or []:
        if actor.get_actor_label() == studio.TAG_CAMERA:
            return actor
        if studio.TAG_CAMERA in list(getattr(actor, "tags", []) or []):
            return actor
    return None


def _position_camera(camera, frame: int = 30, target=(0.0, 0.0, 0.0)) -> None:
    import unreal

    loc = studio.orbit_camera_position(frame)
    # Aim at swatch origin (was 0,0,40 — framed void only, sphere off-screen)
    rot = studio.look_at_rotation(loc, tuple(target))
    camera.set_actor_location(unreal.Vector(*loc), False, False)
    camera.set_actor_rotation(studio.ue_rotator(rot), False)
    try:
        cine = camera.get_cine_camera_component()
        if cine:
            cine.set_editor_property("current_focal_length", studio.CAMERA_FOCAL_LENGTH)
    except Exception:
        pass


def _swatch_aim_target(eas) -> tuple[float, float, float]:
    import unreal

    for actor in eas.get_all_level_actors() or []:
        label = actor.get_actor_label() or ""
        tags = list(getattr(actor, "tags", []) or [])
        if studio.TAG_SWATCH in tags or label == "MI_Preview_Swatch":
            try:
                actor.set_actor_hidden_in_game(False)
                actor.set_is_temporarily_hidden_in_editor(False)
            except Exception:
                pass
            try:
                sm = actor.static_mesh_component
                if sm:
                    sm.set_visibility(True)
                    sm.set_hidden_in_game(False)
            except Exception:
                pass
            loc = actor.get_actor_location()
            return (float(loc.x), float(loc.y), float(loc.z))
    return (0.0, 0.0, 0.0)


def _prepare_camera(eas, *, water: bool = False):
    """Reset the studio camera to the swatch after a level reload."""
    aim = _swatch_aim_target(eas)
    camera = _find_camera(eas)
    if not camera:
        return None, aim
    if water:
        # Water reads as a surface, not a flat square swatch.  Give the hero
        # plates a controlled three-quarter horizon while keeping the same
        # studio backdrop and lighting rig.
        import unreal

        loc = (300.0, -340.0, 260.0)
        camera.set_actor_location(unreal.Vector(*loc), False, False)
        camera.set_actor_rotation(
            studio.ue_rotator(studio.look_at_rotation(loc, aim)), False
        )
        return camera, aim

    _position_camera(camera, frame=studio.LOOP_FRAMES // 4, target=aim)
    try:
        import unreal

        # Pull the camera toward the subject while retaining the corrected
        # pitch/yaw produced by ue_rotator().
        loc = camera.get_actor_location()
        camera.set_actor_location(
            unreal.Vector(
                loc.x * 0.62 + aim[0] * 0.38,
                loc.y * 0.62 + aim[1] * 0.38,
                loc.z * 0.62 + aim[2] * 0.38,
            ),
            False,
            False,
        )
        rot = studio.look_at_rotation(
            (
                float(camera.get_actor_location().x),
                float(camera.get_actor_location().y),
                float(camera.get_actor_location().z),
            ),
            aim,
        )
        camera.set_actor_rotation(studio.ue_rotator(rot), False)
    except Exception:
        pass
    try:
        import unreal

        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if les and hasattr(les, "pilot_level_actor"):
            les.pilot_level_actor(camera)
    except Exception:
        pass
    return camera, aim


def _recreate_swatch_actor(eas):
    """Create a fresh preview proxy so each MI gets a new scene render state."""
    import unreal

    old = None
    for actor in eas.get_all_level_actors() or []:
        if studio.TAG_SWATCH in list(getattr(actor, "tags", []) or []):
            old = actor
            break
    loc = old.get_actor_location() if old else unreal.Vector(0.0, 0.0, 0.0)
    rot = old.get_actor_rotation() if old else unreal.Rotator()
    scale = old.get_actor_scale3d() if old else unreal.Vector(*studio.SWATCH_SPHERE_SCALE)
    if old:
        try:
            eas.destroy_actor(old)
        except Exception:
            pass
    actor = eas.spawn_actor_from_class(unreal.StaticMeshActor.static_class(), loc, rot)
    if not actor:
        return None
    actor.set_actor_label("MI_Preview_Swatch")
    actor.tags = [studio.TAG_SWATCH]
    actor.set_actor_scale3d(scale)
    return actor


def _promote(src: Path, mi_id: str) -> list[str]:
    import shutil
    import time

    promoted = []
    for dest_dir in (NIGHTSHIFT_DIR, SITE_NIGHTSHIFT):
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{mi_id}.png"
        tmp = dest.with_suffix(".png.tmp")
        # Windows/OneDrive can fail mid-overwrite — write temp then replace
        last_err = None
        for attempt in range(4):
            try:
                if tmp.is_file():
                    tmp.unlink()
                shutil.copy2(src, tmp)
                os_replace = getattr(__import__("os"), "replace")
                os_replace(tmp, dest)
                promoted.append(str(dest))
                last_err = None
                break
            except OSError as exc:
                last_err = exc
                time.sleep(0.2 * (attempt + 1))
        if last_err is not None:
            raise last_err
    preview = studio.PREVIEW_FRAME_DIR / f"{mi_id}_preview_frame.png"
    preview.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, preview)
    promoted.append(str(preview))
    return promoted


def _entry_for(mi_id: str, manifest: dict) -> dict | None:
    for row in manifest.get("entries") or []:
        if row.get("id") == mi_id:
            return row
    return manifest_mod.route_preview(name=mi_id, source="retake_nikki")


def capture_batch(ids: list[str], *, promote: bool = True) -> dict[str, Any]:
    import unreal

    studio_info = _ensure_studio()
    world = capture_mod.get_editor_world()
    if not world:
        return {"ok": False, "error": "no_editor_world", "studio": studio_info}

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    camera, aim = _prepare_camera(eas)
    if not camera:
        return {"ok": False, "error": "camera_missing", "studio": studio_info}

    manifest = manifest_mod.load_manifest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")

    results: list[dict] = []
    for mi_id in ids:
        entry = _entry_for(mi_id, manifest)
        if not entry:
            results.append({"id": mi_id, "ok": False, "error": "no_entry"})
            continue
        is_water = str(entry.get("profile") or "") == "WaterV10"
        # A StaticMeshComponent material override can remain in the editor's
        # render proxy for the rest of a batch.  A fresh actor gives each plate
        # an unambiguous scene proxy while staying entirely inside the
        # project-owned render-studio level.
        if not _recreate_swatch_actor(eas):
            results.append({"id": mi_id, "ok": False, "error": "swatch_recreate_failed"})
            continue
        camera, aim = _prepare_camera(eas, water=is_water)
        if not world or not camera:
            results.append({"id": mi_id, "ok": False, "error": "studio_camera_missing"})
            continue
        if is_water:
            entry = dict(entry)
            entry["mesh_scale"] = [4.0, 4.0, 1.0]
        # Melodia void tint from routing — never UE HQ
        applied = apply_mod.apply_preview_entry(entry)
        if not (applied.get("swatch") or {}).get("ok"):
            results.append(
                {"id": mi_id, "ok": False, "error": "apply_failed", "applied": applied}
            )
            continue

        out_path = OUT_DIR / f"{mi_id}_{stamp}_{WIDTH}x{HEIGHT}.png"
        shot = capture_mod.capture_still_from_camera(
            world, camera, out_path, width=WIDTH, height=HEIGHT
        )
        # Prefer asset thumbnail in unattended — SceneCapture often sees void only (no swatch).
        asset_path = (entry.get("asset_path") or "").strip()
        if asset_path:
            thumb_path = OUT_DIR / f"{mi_id}_{stamp}_{WIDTH}x{HEIGHT}_thumb.png"
            thumb = capture_mod.capture_thumbnail_fallback(
                asset_path, thumb_path, size=max(WIDTH, HEIGHT)
            )
            if thumb.get("ok"):
                try:
                    import shutil

                    shutil.copy2(thumb_path, out_path)
                except Exception:
                    out_path = thumb_path
                shot = {**thumb, "studio_capture": shot, "path": str(out_path)}
            else:
                shot = {**shot, "thumbnail_fallback": thumb}
        row = {"id": mi_id, **shot, "applied": applied, "backdrop": entry.get("backdrop")}
        quality = (
            capture_mod.plate_quality(out_path)
            if out_path.is_file()
            else {"ok": False, "luma": 0.0, "uniq": 0, "reason": "missing"}
        )
        if shot.get("ok") and out_path.is_file() and not quality.get("ok"):
            # Safety: never promote void-only / black duds over live site plates
            row["ok"] = False
            row["error"] = f"rejected_{quality.get('reason') or 'quality'}"
            row["luma"] = quality.get("luma")
            row["uniq"] = quality.get("uniq")
            try:
                out_path.rename(out_path.with_suffix(".reject.png"))
            except Exception:
                pass
        elif shot.get("ok") and promote and out_path.is_file() and quality.get("ok"):
            row["promoted"] = _promote(out_path, mi_id)
            row["luma"] = quality.get("luma")
            row["uniq"] = quality.get("uniq")
        results.append(row)
        unreal.log(
            f"[MIStillRetake] {mi_id} ok={row.get('ok')} bytes={shot.get('bytes')} "
            f"luma={row.get('luma')} method={shot.get('method')}"
        )

    # Leave the saved studio level clean and reusable for the next pass.
    try:
        swatch = _recreate_swatch_actor(eas)
        if swatch:
            sm = swatch.static_mesh_component
            sm.set_static_mesh(unreal.load_asset(studio.SPHERE))
            sm.set_material(0, None)
        les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if les:
            les.save_current_level()
    except Exception as exc:
        unreal.log_warning(f"[MIStillRetake] studio restore skipped: {exc}")

    ok_count = sum(1 for r in results if r.get("ok"))
    report = {
        "ok": ok_count > 0,
        "generated_at": _now(),
        "level": studio.LEVEL,
        "doctrine": "melodia_void_nikki_lens",
        "method": "SceneCapture2D+MaterialPreviewStudio",
        "requested": ids,
        "ok_count": ok_count,
        "fail_count": len(results) - ok_count,
        "results": results,
        "studio": studio_info,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "ok_count": ok_count, "fail_count": report["fail_count"]}))
    return report


def _parse_ids() -> list[str]:
    only = None
    batch = "nikki"
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--only" and i + 1 < len(args):
            only = args[i + 1]
            i += 2
            continue
        if arg.startswith("--only="):
            only = arg.split("=", 1)[1]
            i += 1
            continue
        if arg == "--batch" and i + 1 < len(args):
            batch = args[i + 1]
            i += 2
            continue
        if arg.startswith("--batch="):
            batch = arg.split("=", 1)[1]
            i += 1
            continue
        if arg == "--proof":
            only = studio.NIKKI_PRIORITY[0]
            i += 1
            continue
        i += 1
    if only:
        return [only]
    if batch in ("nikki", "site", "top5", "priority"):
        if batch == "top5":
            return list(studio.NIKKI_PRIORITY[:5])
        return list(studio.NIKKI_PRIORITY)
    if batch == "proof":
        return [studio.NIKKI_PRIORITY[0]]
    return list(studio.NIKKI_PRIORITY)


def main() -> int:
    report = capture_batch(_parse_ids())
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
