"""Sync SceneCapture2D still helper for Melodia material studio.

Bypasses async HighResShot. Used by retake_material_stills + viewport frame.
"""
from __future__ import annotations

import math
import time
from pathlib import Path
from typing import Any

import mi_preview_studio as studio


def get_editor_world():
    import unreal

    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if ues and hasattr(ues, "get_editor_world"):
        try:
            w = ues.get_editor_world()
            if w:
                return w
        except Exception:
            pass
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if eas:
        for actor in eas.get_all_level_actors() or []:
            try:
                w = actor.get_world()
                if w:
                    return w
            except Exception:
                continue
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def _capture_component(capture):
    """Resolve SceneCaptureComponent2D across UE Python API variants."""
    import unreal

    for attr in ("get_capture_component_2d", "get_capture_component"):
        fn = getattr(capture, attr, None)
        if callable(fn):
            try:
                cc = fn()
                if cc:
                    return cc
            except Exception:
                pass
    for prop in ("capture_component_2d", "capture_component"):
        try:
            cc = capture.get_editor_property(prop)
            if cc:
                return cc
        except Exception:
            pass
        try:
            cc = getattr(capture, prop, None)
            if cc:
                return cc
        except Exception:
            pass
    for getter in ("get_components_by_class", "GetComponentsByClass"):
        fn = getattr(capture, getter, None)
        if not callable(fn):
            continue
        try:
            comps = fn(unreal.SceneCaptureComponent2D)
            if comps:
                return comps[0]
        except Exception:
            pass
    try:
        root = capture.get_editor_property("root_component")
        if root and isinstance(root, unreal.SceneCaptureComponent2D):
            return root
    except Exception:
        pass
    return None


def _fov_from_camera(camera, default: float = 40.0) -> float:
    try:
        cine = camera.get_cine_camera_component()
        fl = float(cine.get_editor_property("current_focal_length") or studio.CAMERA_FOCAL_LENGTH)
        return math.degrees(2.0 * math.atan(18.0 / max(fl, 1.0)))
    except Exception:
        return default


def file_mean_luma(path: Path) -> float:
    """0–255 mean luminance; used to reject black dud frames."""
    q = plate_quality(path)
    return float(q.get("luma") or 0.0)


def plate_quality(path: Path) -> dict[str, Any]:
    """Score a still: reject black + flat void-only plates (no swatch)."""
    try:
        from PIL import Image

        with Image.open(path) as im:
            im = im.convert("RGB").resize((64, 64))
        px = list(im.getdata())
        if not px:
            return {"luma": 0.0, "uniq": 0, "ok": False, "reason": "empty"}
        luma = sum((0.2126 * r + 0.7152 * g + 0.0722 * b) for r, g, b in px) / len(px)
        uniq = len(set(px))
        clipped = sum(1 for r, g, b in px if r >= 250 and g >= 250 and b >= 250) / len(px)
        # Solid void / empty studio ≈ uniq < ~30 on 64² sample
        ok = luma >= 12.0 and uniq >= 48 and clipped < 0.78
        reason = None
        if luma < 12.0:
            reason = "too_dark"
        elif uniq < 48:
            reason = "too_flat"
        elif clipped >= 0.78:
            reason = "overexposed"
        return {
            "luma": luma,
            "uniq": uniq,
            "clipped_ratio": round(clipped, 4),
            "ok": ok,
            "reason": reason,
        }
    except Exception as exc:
        try:
            size = path.stat().st_size
        except Exception:
            size = 0
        return {
            "luma": 40.0 if size > 120_000 else 0.0,
            "uniq": -1,
            "ok": size > 120_000,
            "reason": f"pil:{exc}",
        }


def _warmup(world, camera=None) -> None:
    import unreal

    cmds = [
        "r.ForceHighestMip 1",
        "r.Streaming.FullyLoadUsedTextures 1",
        "r.ScreenPercentage 100",
    ]
    for cmd in cmds:
        try:
            unreal.SystemLibrary.execute_console_command(world, cmd)
        except Exception:
            pass
    try:
        if camera:
            les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            if les and hasattr(les, "pilot_level_actor"):
                les.pilot_level_actor(camera)
    except Exception:
        pass
    # Pump a few frames so materials stream + PPV applies
    for _ in range(12):
        try:
            unreal.SystemLibrary.execute_console_command(world, "Stat None")
        except Exception:
            pass
        time.sleep(0.05)


def _capture_sources():
    import unreal

    names = [
        # The portfolio output is a display-referred PNG.  Prefer LDR so the
        # render target/export path cannot reinterpret HDR values as white.
        "SCS_FINAL_COLOR_LDR",
        "SCS_FINAL_TONE_CURVE_HDR",
        "SCS_FINAL_COLOR_HDR",
        "SCS_SCENE_COLOR_HDR",
        "SCS_BASE_COLOR",
    ]
    out = []
    for n in names:
        val = getattr(unreal.SceneCaptureSource, n, None)
        if val is not None:
            out.append((n, val))
    return out


def capture_still_from_camera(
    world,
    camera,
    out_path: Path,
    *,
    width: int = 1080,
    height: int = 1080,
    min_luma: float = 12.0,
    min_uniq: int = 48,
) -> dict[str, Any]:
    import unreal

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    loc = camera.get_actor_location()
    rot = camera.get_actor_rotation()
    fov = _fov_from_camera(camera)
    _warmup(world, camera)

    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    capture = None
    attempts: list[dict] = []
    try:
        capture = eas.spawn_actor_from_class(
            unreal.SceneCapture2D.static_class(), loc, rot
        )
        if not capture:
            return {"ok": False, "error": "spawn_capture_null"}
        capture.set_actor_label("TMP_MI_StillCapture")
        cc = _capture_component(capture)
        if not cc:
            return {"ok": False, "error": "capture_component_missing", "attempts": attempts}

        try:
            cc.set_editor_property("fov_angle", float(fov))
        except Exception:
            pass
        try:
            cc.set_editor_property("always_persist_rendering_state", True)
        except Exception:
            pass
        cc.set_editor_property("capture_on_movement", False)
        # SceneCapture often ignores unbound PPV — push exposure on the capture itself
        try:
            cc.set_editor_property("post_process_blend_weight", 1.0)
            pps = cc.get_editor_property("post_process_settings")
            if pps:
                for flag, val in (
                    ("override_auto_exposure_method", True),
                    ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
                    ("override_auto_exposure_bias", True),
                    ("auto_exposure_bias", 0.0),
                    ("override_auto_exposure_apply_physical_camera_exposure", True),
                    ("auto_exposure_apply_physical_camera_exposure", False),
                ):
                    try:
                        pps.set_editor_property(flag, val)
                    except Exception:
                        try:
                            # UE property names sometimes use b_ prefix
                            pps.set_editor_property("b_" + flag, val)
                        except Exception:
                            pass
                cc.set_editor_property("post_process_settings", pps)
        except Exception:
            pass

        # Stream a few frames with capture_every_frame before single-shot export
        try:
            cc.set_editor_property("capture_every_frame", True)
            time.sleep(0.35)
        except Exception:
            pass

        for src_name, src_val in _capture_sources():
            rt = unreal.RenderingLibrary.create_render_target2d(
                world,
                width,
                height,
                unreal.TextureRenderTargetFormat.RTF_RGBA8,
                unreal.LinearColor(0.0, 0.0, 0.0, 1.0),
                False,
            )
            if not rt:
                attempts.append({"source": src_name, "error": "rt_null"})
                continue
            try:
                cc.set_editor_property("texture_target", rt)
                cc.set_editor_property("capture_source", src_val)
            except Exception as exc:
                attempts.append({"source": src_name, "error": f"set:{exc}"})
                continue
            try:
                if hasattr(cc, "capture_scene"):
                    cc.capture_scene()
                    # Second capture after a short settle often fixes black first frame
                    time.sleep(0.05)
                    cc.capture_scene()
            except Exception as exc:
                attempts.append({"source": src_name, "error": f"capture_scene:{exc}"})
                continue

            stem = out_path.stem
            # Write to a probe path first so we don't clobber a good file with black
            probe = out_path.with_name(f"{stem}__probe_{src_name}.png")
            if probe.is_file():
                try:
                    probe.unlink()
                except Exception:
                    pass
            exported = unreal.RenderingLibrary.export_render_target(
                world, rt, str(probe.parent), probe.name
            )
            # export_render_target may append .png already
            if not probe.is_file():
                alt = Path(str(probe) + ".png")
                if alt.is_file():
                    probe = alt
            ok_file = probe.is_file() and probe.stat().st_size > 8_000
            q = plate_quality(probe) if ok_file else {"luma": 0.0, "uniq": 0, "ok": False}
            attempts.append(
                {
                    "source": src_name,
                    "bytes": probe.stat().st_size if probe.is_file() else 0,
                    "luma": round(float(q.get("luma") or 0.0), 2),
                    "uniq": q.get("uniq"),
                    "export_return": bool(exported),
                    "reason": q.get("reason"),
                }
            )
            if (
                ok_file
                and q.get("ok")
                and float(q.get("luma") or 0.0) >= min_luma
                and int(q.get("uniq") or 0) >= min_uniq
            ):
                try:
                    if out_path.is_file():
                        out_path.unlink()
                except Exception:
                    pass
                probe.replace(out_path)
                try:
                    cc.set_editor_property("capture_every_frame", False)
                except Exception:
                    pass
                return {
                    "ok": True,
                    "bytes": out_path.stat().st_size,
                    "path": str(out_path),
                    "fov": fov,
                    "luma": round(float(q["luma"]), 2),
                    "uniq": q.get("uniq"),
                    "method": f"SceneCapture2D:{src_name}",
                    "attempts": attempts,
                }
            # Salvage underexposed-but-structured frames (swatch visible, exposure crushed)
            if ok_file and int(q.get("uniq") or 0) >= 100 and float(q.get("luma") or 0.0) < min_luma:
                salvaged = _autolevel_salvage(probe, out_path)
                if salvaged.get("ok"):
                    try:
                        cc.set_editor_property("capture_every_frame", False)
                    except Exception:
                        pass
                    return {
                        **salvaged,
                        "fov": fov,
                        "method": f"SceneCapture2D:{src_name}+autolevel",
                        "attempts": attempts,
                    }
            try:
                if probe.is_file():
                    probe.unlink()
            except Exception:
                pass

        try:
            cc.set_editor_property("capture_every_frame", False)
        except Exception:
            pass
        return {
            "ok": False,
            "error": "all_capture_sources_black_or_failed",
            "attempts": attempts,
            "fov": fov,
        }
    except Exception as exc:
        return {"ok": False, "error": f"capture:{exc}", "attempts": attempts}
    finally:
        try:
            if capture and eas:
                eas.destroy_actor(capture)
        except Exception:
            pass


def _autolevel_salvage(src: Path, dest: Path) -> dict[str, Any]:
    """Brighten crushed SceneCapture frames that still have sphere structure."""
    try:
        from PIL import Image, ImageEnhance, ImageOps

        with Image.open(src) as im:
            im = im.convert("RGB")
            im = ImageOps.autocontrast(im, cutoff=0.4)
            im = ImageEnhance.Brightness(im).enhance(2.4)
            im = ImageEnhance.Contrast(im).enhance(1.15)
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, format="PNG", optimize=True)
        q = plate_quality(dest)
        if q.get("ok"):
            return {
                "ok": True,
                "bytes": dest.stat().st_size,
                "path": str(dest),
                "luma": round(float(q["luma"]), 2),
                "uniq": q.get("uniq"),
            }
        return {"ok": False, "error": q.get("reason") or "autolevel_reject", **q}
    except Exception as exc:
        return {"ok": False, "error": f"autolevel:{exc}"}


def capture_thumbnail_fallback(
    asset_path: str,
    out_path: Path,
    *,
    size: int = 1024,
    min_luma: float = 12.0,
) -> dict[str, Any]:
    """Content-browser style thumbnail — better than black studio dud."""
    import unreal

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not asset:
        return {"ok": False, "error": "asset_missing", "asset_path": asset_path}
    if not hasattr(unreal, "AutomationLibrary") or not hasattr(
        unreal.AutomationLibrary, "take_thumbnail"
    ):
        return {"ok": False, "error": "take_thumbnail_unavailable"}
    try:
        options = unreal.AssetThumbnailCaptureOptions()
        options.size = unreal.IntPoint(size, size)
        options.render_background = True
        options.background_color = unreal.LinearColor(0.051, 0.071, 0.141, 1.0)
        unreal.AutomationLibrary.take_thumbnail(asset, str(out_path), options)
    except Exception as exc:
        return {"ok": False, "error": f"take_thumbnail:{exc}"}
    for _ in range(40):
        time.sleep(0.1)
        if out_path.is_file() and out_path.stat().st_size > 8_000:
            q = plate_quality(out_path)
            if q.get("ok") and float(q.get("luma") or 0.0) >= min_luma:
                return {
                    "ok": True,
                    "bytes": out_path.stat().st_size,
                    "path": str(out_path),
                    "luma": round(float(q["luma"]), 2),
                    "uniq": q.get("uniq"),
                    "method": "AutomationLibrary.take_thumbnail",
                    "asset_path": asset_path,
                }
            return {
                "ok": False,
                "error": q.get("reason") or "thumbnail_reject",
                "luma": round(float(q.get("luma") or 0.0), 2),
                "uniq": q.get("uniq"),
                "bytes": out_path.stat().st_size,
            }
    return {"ok": False, "error": "thumbnail_timeout"}
