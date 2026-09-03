"""* Living Portrait - voice-driven viseme animation for Melusina rigs.

Reconstructed 2026-08-23 from surviving bytecode after the untracked original
was lost in a deploy-tree mirror. Pipeline:
  load voice file (USTX/UST/TimingJSON) -> PhonemeEvents
  detect rig blendshapes -> VisemeBindings
  generate -> expression_mixer bakes shape-key f-curves per frame
"""

from __future__ import annotations

import os
from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

try:
    from .branding import N_PANEL_CATEGORY
except ImportError:  # pragma: no cover - standalone fallback
    N_PANEL_CATEGORY = "Melodia Studio"

from .expression_mixer import clear_all_portrait_animation, generate_portrait_animation
from .phoneme_reader import parse_voice_file, timing_json_example
from .viseme_mapper import detect_rig_blendshapes, rig_detection_report


# ── Property groups ─────────────────────────────────────────────────────

class MPR_SceneSettings(bpy.types.PropertyGroup):
    voice_path: StringProperty(
        name="Voice File",
        description="USTX / UST / timing JSON file driving the portrait",
        subtype="FILE_PATH",
    )
    tempo_override: FloatProperty(
        name="Tempo Override", description="0 = use file tempo",
        default=0.0, min=0.0, max=300.0)
    intensity: FloatProperty(
        name="Intensity", description="Viseme weight scale",
        default=1.0, min=0.0, max=2.0)
    idle_amount: FloatProperty(
        name="Idle Overlay", description="Blink/breathe overlay strength",
        default=0.35, min=0.0, max=1.0)
    fps: IntProperty(name="FPS", default=24, min=1, max=120)
    start_frame: IntProperty(name="Start Frame", default=1, min=-10000, max=100000)
    armature_name: StringProperty(name="Armature", description="Target rig (blank = active)")
    last_report: StringProperty(name="Status", default="", options={"HIDDEN"})


class MPR_OT_load_voice(bpy.types.Operator):
    bl_idname = "mpr.load_voice"
    bl_label = "Load Voice"
    bl_description = "Parse USTX/UST/timing JSON into phoneme events"
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        settings = context.scene.melodia_portrait
        path = self.filepath or settings.voice_path
        if not path:
            self.report({"ERROR"}, "No voice file selected")
            return {"CANCELLED"}
        try:
            track = parse_voice_file(
                Path(bpy.path.abspath(path)),
                tempo=settings.tempo_override or None,
            )
            settings.voice_path = path
            settings.last_report = (
                f"{track.name or 'voice'}: {len(track.events)} phonemes, "
                f"{track.total_duration_sec:.2f}s @ {track.tempo:g} BPM ({track.format})"
            )
            self.report({"INFO"}, settings.last_report)
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Voice parse failed: {exc}")
            return {"CANCELLED"}


def _resolve_armature(context):
    settings = context.scene.melodia_portrait
    if settings.armature_name:
        obj = bpy.data.objects.get(settings.armature_name)
        if obj is None:
            return None, f"Armature '{settings.armature_name}' not found"
        return obj, None
    obj = context.active_object
    if obj is None or obj.type != "ARMATURE":
        return None, "Select an armature (or set one in the panel)"
    return obj, None


class MPR_OT_detect_rig(bpy.types.Operator):
    bl_idname = "mpr.detect_rig"
    bl_label = "Detect Rig Blendshapes"
    bl_description = "Scan the rig's meshes for viseme-ready shape keys"
    bl_options = {"REGISTER"}

    def execute(self, context):
        arm, err = _resolve_armature(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        report = rig_detection_report(arm)
        context.scene.melodia_portrait.last_report = report.splitlines()[0] if report else "No bindings"
        print("[LivingPortrait]\n" + report)
        self.report({"INFO"}, f"{len(detect_rig_blendshapes(arm))} viseme binding(s) - see System Console")
        return {"FINISHED"}


class MPR_OT_preview_portrait(bpy.types.Operator):
    bl_idname = "mpr.preview_portrait"
    bl_label = "Preview Viseme"
    bl_description = "Snap the rig to the viseme of the first phoneme for a quick check"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from .viseme_mapper import get_viseme_weights
        from .expression_mixer import _apply_shape_keys  # noqa: F401 - kept internal

        arm, err = _resolve_armature(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        settings = context.scene.melodia_portrait
        try:
            track = parse_voice_file(
                Path(bpy.path.abspath(settings.voice_path)),
                tempo=settings.tempo_override or None,
            )
        except Exception as exc:
            self.report({"ERROR"}, f"Load a voice file first ({exc})")
            return {"CANCELLED"}
        if not track.events:
            self.report({"WARNING"}, "Track has no phonemes")
            return {"CANCELLED"}
        first = track.events[0]
        weights = get_viseme_weights(first.phoneme)
        self.report({"INFO"}, f"'{first.phoneme}' -> {weights}")
        settings.last_report = f"preview {first.phoneme}: {weights}"
        return {"FINISHED"}


class MPR_OT_generate_portrait(bpy.types.Operator):
    bl_idname = "mpr.generate_portrait"
    bl_label = "Generate Portrait Animation"
    bl_description = "Bake shape-key viseme animation across the timeline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm, err = _resolve_armature(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        settings = context.scene.melodia_portrait
        if not settings.voice_path:
            self.report({"ERROR"}, "Load a voice file first")
            return {"CANCELLED"}
        try:
            track = parse_voice_file(
                Path(bpy.path.abspath(settings.voice_path)),
                tempo=settings.tempo_override or None,
            )
            count = generate_portrait_animation(arm, track, settings)
            self.report({"INFO"}, f"Portrait baked: {count} keyframe set(s), {len(track.events)} phonemes")
            return {"FINISHED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Generate failed: {exc}")
            return {"CANCELLED"}


class MPR_OT_export_timing_json(bpy.types.Operator):
    bl_idname = "mpr.export_timing_json"
    bl_label = "Export Timing JSON Example"
    bl_description = "Write an example timing-JSON template next to the blend file"
    bl_options = {"REGISTER"}

    def execute(self, context):
        import json

        example = timing_json_example()
        base = bpy.path.abspath("//") or os.path.dirname(bpy.data.filepath) or "."
        out = os.path.join(base, "portrait_timing_example.json")
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(example, handle, indent=2)
        self.report({"INFO"}, f"Wrote {out}")
        return {"FINISHED"}


class MPR_OT_clear_portrait(bpy.types.Operator):
    bl_idname = "mpr.clear_portrait"
    bl_label = "Clear Portrait Animation"
    bl_description = "Remove all baked portrait shape-key animation from the rig"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm, err = _resolve_armature(context)
        if err:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        removed = clear_all_portrait_animation(arm)
        self.report({"INFO"}, f"Cleared {removed} animated shape key(s)")
        return {"FINISHED"}


class SURREAL_ARCH_PT_living_portrait(bpy.types.Panel):
    bl_label = "Living Portrait"
    bl_idname = "SURREAL_ARCH_PT_living_portrait"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_order = 10
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "melodia_portrait", None)
        if settings is None:
            layout.label(text="Portrait unavailable", icon="ERROR")
            return
        col = layout.column(align=True)
        col.prop(settings, "voice_path")
        row = layout.row(align=True)
        row.operator("mpr.load_voice", icon="PLAY")
        row.operator("mpr.detect_rig", icon="VIEWZOOM")
        col = layout.column(align=True)
        col.prop(settings, "intensity")
        col.prop(settings, "idle_amount")
        row2 = layout.row(align=True)
        row2.prop(settings, "fps")
        row2.prop(settings, "start_frame")
        gen = layout.row(align=True)
        gen.scale_y = 1.2
        gen.operator("mpr.generate_portrait", icon="NLA_PUSHDOWN")
        row3 = layout.row(align=True)
        row3.operator("mpr.preview_portrait", text="Preview")
        row3.operator("mpr.clear_portrait", text="Clear")
        layout.operator("mpr.export_timing_json", icon="FILE_TICK")
        if settings.last_report:
            box = layout.box()
            box.label(text=settings.last_report[:80], icon="INFO")


CLASSES = (
    MPR_SceneSettings,
    MPR_OT_load_voice,
    MPR_OT_detect_rig,
    MPR_OT_preview_portrait,
    MPR_OT_generate_portrait,
    MPR_OT_export_timing_json,
    MPR_OT_clear_portrait,
    SURREAL_ARCH_PT_living_portrait,
)


def register_props():
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except RuntimeError:
            pass
    if not hasattr(bpy.types.Scene, "melodia_portrait"):
        bpy.types.Scene.melodia_portrait = PointerProperty(type=MPR_SceneSettings)


def unregister_props():
    if hasattr(bpy.types.Scene, "melodia_portrait"):
        del bpy.types.Scene.melodia_portrait
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
