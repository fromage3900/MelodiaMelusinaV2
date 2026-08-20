"""Melodia Studio — Render & Upload beauty plates to the live website repo.

N-panel operators under Stage:
  surreal_arch.render_and_upload_plate
  surreal_arch.push_last_plate_to_site

Writes PNGs under MELODIA_WEBSITE_ROOT/generated/assets/ and updates
content/site-plates.json. Optional git push is OFF by default.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup

from .branding import N_PANEL_CATEGORY, PRODUCT_NAME

# Publish contract: git push is OFF unless the artist ticks the N-panel box.
GIT_PUSH_DEFAULT = False


def _project_root() -> Path:
    # deploy/surreal_arch/stage_publish.py → deploy → BS_GodFile
    return Path(__file__).resolve().parents[2]


def resolve_website_root() -> Path:
    env = os.environ.get("MELODIA_WEBSITE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    project = _project_root()
    workspace = Path(
        os.environ.get("MELODIA_WORKSPACE_ROOT", str(project.parent))
    ).expanduser().resolve()
    live = workspace / "my-site-clean"
    if live.is_dir():
        return live
    return (project / "my-site-clean").resolve()


def _audit_path() -> Path:
    return _project_root() / "Saved" / "Audit" / "stage_publish_last.json"


def _write_audit(payload: dict) -> None:
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _assign_plate_slot(site: Path, slot: str, png: Path, alt: str = "") -> None:
    plates_path = site / "content" / "site-plates.json"
    data = {"version": 1, "slots": {}}
    if plates_path.is_file():
        try:
            data = json.loads(plates_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    slots = data.setdefault("slots", {})
    try:
        rel_str = "../" + png.resolve().relative_to(site.resolve()).as_posix()
    except Exception:
        rel_str = f"../generated/assets/character/{png.name}"
    slots[slot] = {
        "path": rel_str.replace("\\", "/"),
        "alt": alt or slots.get(slot, {}).get("alt", slot),
    }
    plates_path.parent.mkdir(parents=True, exist_ok=True)
    plates_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _git_push_live(site: Path, paths: list[Path], message: str) -> tuple[bool, str]:
    try:
        rels = []
        for p in paths:
            try:
                rels.append(str(p.resolve().relative_to(site.resolve())))
            except Exception:
                rels.append(str(p))
        subprocess.run(
            ["git", "-C", str(site), "add", "--", *rels],
            check=True,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "-C", str(site), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            return True, "nothing to commit"
        subprocess.run(
            ["git", "-C", str(site), "commit", "-m", message],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(site), "push", "origin", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, "pushed"
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc))[:300]
        return False, err
    except Exception as exc:
        return False, str(exc)[:300]


def _pick_camera() -> bpy.types.Object | None:
    for name in ("Cam_Beauty", "Camera", "Cam_Front"):
        cam = bpy.data.objects.get(name)
        if cam and cam.type == "CAMERA":
            return cam
    for obj in bpy.data.objects:
        if obj.type == "CAMERA":
            return obj
    return None


def _newest_png(site: Path) -> Path | None:
    char = site / "generated" / "assets" / "character"
    if not char.is_dir():
        return None
    pngs = sorted(char.glob("melusina*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return pngs[0] if pngs else None


class MEL_StagePublishSettings(PropertyGroup):
    push_live: BoolProperty(
        name="Push live (git)",
        description="After upload, git add/commit/push the website repo (GitHub Pages). Default OFF.",
        default=GIT_PUSH_DEFAULT,
    )
    plate_slot: EnumProperty(
        name="Plate slot",
        items=(
            ("stage.beauty", "stage.beauty", "Hero beauty plate"),
            ("hub.melusina", "hub.melusina", "Hub Melusina plate"),
            ("index.hero", "index.hero", "Index hero"),
            ("recruiter.hero", "recruiter.hero", "Recruiter hero"),
        ),
        default="stage.beauty",
    )
    website_root: StringProperty(
        name="Website root",
        description="Override MELODIA_WEBSITE_ROOT (leave empty for auto)",
        default="",
        subtype="DIR_PATH",
    )
    last_status: StringProperty(name="Last status", default="Never")


class SURREAL_ARCH_OT_render_and_upload_plate(Operator):
    """Apply beauty_clean, render still, write site assets + site-plates.json."""

    bl_idname = "surreal_arch.render_and_upload_plate"
    bl_label = "Render & Upload"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = getattr(context.scene, "mel_stage_publish", None)
        site = resolve_website_root()
        if settings and settings.website_root.strip():
            site = Path(bpy.path.abspath(settings.website_root)).resolve()

        slot = settings.plate_slot if settings else "stage.beauty"
        push_live = bool(settings.push_live) if settings else False

        # Soft stage preset if operator exists
        if hasattr(bpy.ops.surreal_arch, "set_stage_visibility_preset"):
            try:
                bpy.ops.surreal_arch.set_stage_visibility_preset(preset="beauty_clean")
            except Exception:
                pass

        cam = _pick_camera()
        if cam is None:
            self.report({"ERROR"}, "No camera in scene")
            return {"CANCELLED"}
        context.scene.camera = cam

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = site / "generated" / "assets" / "character"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"melusina_stage_beauty_{stamp}.png"

        context.scene.render.filepath = str(out)
        try:
            bpy.ops.render.render(write_still=True)
        except Exception as exc:
            msg = f"Render failed: {exc}"
            if settings:
                settings.last_status = msg
            _write_audit({"ok": False, "error": msg, "site": str(site)})
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        if not out.is_file() or out.stat().st_size < 1000:
            msg = f"Empty render: {out}"
            if settings:
                settings.last_status = msg
            _write_audit({"ok": False, "error": msg, "site": str(site)})
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        _assign_plate_slot(site, slot, out, alt=f"Hero beauty · {stamp}")
        plates = site / "content" / "site-plates.json"
        git_msg = ""
        if push_live:
            ok, git_msg = _git_push_live(
                site,
                [out, plates],
                f"Stage beauty plate {stamp}",
            )
            if not ok:
                status = f"Uploaded {out.name} ({slot}); git push failed: {git_msg}"
                if settings:
                    settings.last_status = status
                _write_audit({
                    "ok": True,
                    "uploaded": True,
                    "pushed": False,
                    "path": str(out),
                    "slot": slot,
                    "bytes": out.stat().st_size,
                    "site": str(site),
                    "git_error": git_msg,
                    "timestamp": stamp,
                })
                self.report({"WARNING"}, status)
                return {"FINISHED"}

        status = f"Uploaded {slot} → {out.name}" + (" + pushed" if push_live else "")
        if settings:
            settings.last_status = status
        _write_audit({
            "ok": True,
            "uploaded": True,
            "pushed": push_live,
            "path": str(out),
            "slot": slot,
            "bytes": out.stat().st_size,
            "site": str(site),
            "git": git_msg,
            "timestamp": stamp,
        })
        self.report({"INFO"}, status)
        return {"FINISHED"}


class SURREAL_ARCH_OT_push_last_plate_to_site(Operator):
    """Assign the newest melusina*.png under website assets to the selected slot."""

    bl_idname = "surreal_arch.push_last_plate_to_site"
    bl_label = "Push Last Plate"
    bl_options = {"REGISTER"}

    def execute(self, context):
        settings = getattr(context.scene, "mel_stage_publish", None)
        site = resolve_website_root()
        if settings and settings.website_root.strip():
            site = Path(bpy.path.abspath(settings.website_root)).resolve()
        slot = settings.plate_slot if settings else "stage.beauty"
        push_live = bool(settings.push_live) if settings else False

        # Prefer last render filepath if it points at a recent PNG
        candidates = []
        fp = bpy.path.abspath(context.scene.render.filepath or "")
        if fp and fp.lower().endswith(".png") and os.path.isfile(fp):
            candidates.append(Path(fp))
        newest = _newest_png(site)
        if newest:
            candidates.append(newest)
        if not candidates:
            msg = "No melusina*.png found under website assets"
            if settings:
                settings.last_status = msg
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        src = max(candidates, key=lambda p: p.stat().st_mtime)
        dest_dir = site / "generated" / "assets" / "character"
        dest_dir.mkdir(parents=True, exist_ok=True)
        if src.resolve().parent != dest_dir.resolve():
            dest = dest_dir / src.name
            dest.write_bytes(src.read_bytes())
        else:
            dest = src

        _assign_plate_slot(site, slot, dest, alt=f"Last plate · {dest.name}")
        plates = site / "content" / "site-plates.json"
        git_msg = ""
        if push_live:
            ok, git_msg = _git_push_live(
                site, [dest, plates], f"Push last plate {dest.name}"
            )
            if not ok:
                status = f"Assigned {slot} → {dest.name}; git failed: {git_msg}"
                if settings:
                    settings.last_status = status
                self.report({"WARNING"}, status)
                return {"FINISHED"}

        status = f"Assigned {slot} → {dest.name}" + (" + pushed" if push_live else "")
        if settings:
            settings.last_status = status
        _write_audit({
            "ok": True,
            "uploaded": True,
            "pushed": push_live,
            "path": str(dest),
            "slot": slot,
            "bytes": dest.stat().st_size,
            "site": str(site),
            "git": git_msg,
            "mode": "push_last",
        })
        self.report({"INFO"}, status)
        return {"FINISHED"}


class SURREAL_ARCH_PT_stage_publish(Panel):
    bl_label = "Site Publish"
    bl_idname = "SURREAL_ARCH_PT_stage_publish"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 7

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "mel_stage_publish", None)
        box = layout.box()
        box.label(text=f"{PRODUCT_NAME} → website", icon="WORLD")
        if settings:
            box.prop(settings, "plate_slot", text="Slot")
            box.prop(settings, "push_live")
            box.prop(settings, "website_root", text="Root")
        row = box.row(align=True)
        row.scale_y = 1.35
        row.operator("surreal_arch.render_and_upload_plate", icon="RENDER_STILL")
        row2 = box.row(align=True)
        row2.operator("surreal_arch.push_last_plate_to_site", icon="EXPORT")
        if settings and settings.last_status:
            box.label(text=settings.last_status, icon="INFO")
        try:
            root = resolve_website_root()
            box.label(text=str(root), icon="FILE_FOLDER")
        except Exception:
            pass


CLASSES = (
    MEL_StagePublishSettings,
    SURREAL_ARCH_OT_render_and_upload_plate,
    SURREAL_ARCH_OT_push_last_plate_to_site,
    SURREAL_ARCH_PT_stage_publish,
)


def register_props():
    bpy.types.Scene.mel_stage_publish = PointerProperty(type=MEL_StagePublishSettings)


def unregister_props():
    try:
        del bpy.types.Scene.mel_stage_publish
    except AttributeError:
        pass
