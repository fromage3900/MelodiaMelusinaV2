"""Living Portrait Engine ΓÇö voice-driven character animation for Melusina.

N-panel UI for loading USTX/UST voice files, detecting viseme blendshapes on
the cinematic rig, and generating lip-synced portrait animations.

Integration:
  Registered alongside melodia_gn in integration.py ΓåÆ register_overhaul().
  Panel nests under SURREAL_ARCH_PT_genome_carousel in "Melodia Studio" tab.
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
from bpy.types import Panel, PropertyGroup, Operator

from ..branding import N_PANEL_CATEGORY


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Property group ΓÇö per-scene settings
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MPR_SceneSettings(PropertyGroup):
    """Living Portrait settings persisted on the scene."""

    voice_file: StringProperty(
        name="Voice File",
        subtype="FILE_PATH",
        default="",
        description="Path to .ustx, .ust, or .json voice timing file",
    )
    voice_track_name: StringProperty(
        name="Track Name",
        default="",
        description="Last loaded voice track name",
    )
    target_armature: StringProperty(
        name="Armature",
        default="",
        description="Name of the target armature object",
    )
    viseme_report: StringProperty(
        name="Viseme Report",
        default="",
        description="Detection result for the target rig",
    )
    portrait_fps: IntProperty(
        name="Frame Rate",
        default=24, min=12, max=60,
        description="Animation frames per second",
    )
    portrait_blend_strength: FloatProperty(
        name="Blend Strength",
        default=1.0, min=0.0, max=2.0, subtype="FACTOR",
        description="Overall blendshape intensity multiplier",
    )
    portrait_idle_amplitude: FloatProperty(
        name="Idle Amplitude",
        default=0.15, min=0.0, max=1.0, subtype="FACTOR",
        description="Breathing / blink / sway intensity",
    )
    portrait_eye_blink_rate: FloatProperty(
        name="Blink Rate",
        default=4.0, min=0.5, max=15.0,
        description="Average blinks per second",
    )
    portrait_smooth_frames: IntProperty(
        name="Smooth Frames",
        default=2, min=1, max=8,
        description="Interpolation window for viseme transitions",
    )
    portrait_status: StringProperty(
        name="Status",
        default="Ready.",
        description="Status of the last portrait generation",
    )
    portrait_expand_voice: BoolProperty(name="Expand Voice", default=True)
    portrait_expand_settings: BoolProperty(name="Expand Settings", default=True)
    portrait_expand_rig: BoolProperty(name="Expand Rig", default=True)


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Operators
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MPR_OT_load_voice(Operator):
    """Parse the selected voice file and display track info."""

    bl_idname = "melusina.load_voice"
    bl_label = "Load Voice File"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.melusina_portrait
        path = settings.voice_file
        if not path or not os.path.isfile(path):
            settings.portrait_status = "Voice file not found."
            self.report({"WARNING"}, "File not found")
            return {"CANCELLED"}

        try:
            from .phoneme_reader import parse_voice_file
            track = parse_voice_file(path)
            settings.voice_track_name = track.name
            settings.portrait_status = (
                f"Loaded '{track.name}' ΓÇö {len(track.events)} phonemes, "
                f"{track.total_duration_sec:.1f}s at {track.tempo:.0f} BPM "
                f"({track.format.upper()})"
            )
            self.report({"INFO"}, f"Loaded {track.name} ({len(track.events)} notes)")
        except Exception as exc:
            settings.portrait_status = f"Parse error: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        return {"FINISHED"}


class MPR_OT_detect_rig(Operator):
    """Auto-detect viseme blendshapes on the active armature."""

    bl_idname = "melusina.detect_rig"
    bl_label = "Detect Viseme Blendshapes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        settings = context.scene.melusina_portrait
        obj = context.active_object

        if obj.type != "ARMATURE":
            # Try to find an armature in selection
            for o in context.selected_objects:
                if o.type == "ARMATURE":
                    obj = o
                    break
            if obj.type != "ARMATURE":
                settings.portrait_status = "Select an armature first."
                self.report({"WARNING"}, "No armature selected")
                return {"CANCELLED"}

        settings.target_armature = obj.name

        try:
            from .viseme_mapper import rig_detection_report, detect_rig_blendshapes
            report = rig_detection_report(obj)
            bindings = detect_rig_blendshapes(obj)
            settings.viseme_report = report
            if bindings:
                settings.portrait_status = (
                    f"Detected {len(bindings)} visemes on '{obj.name}'. "
                    f"Ready to generate."
                )
            else:
                settings.portrait_status = (
                    f"No viseme blendshapes found on '{obj.name}'. "
                    f"See report for available shape keys."
                )
            self.report({"INFO"}, f"Found {len(bindings)} visemes")
        except Exception as exc:
            settings.portrait_status = f"Detection error: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        return {"FINISHED"}


class MPR_OT_generate_portrait(Operator):
    """Generate lip-synced portrait animation from voice data."""

    bl_idname = "melusina.generate_portrait"
    bl_label = "Generate Portrait"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.melusina_portrait
        return bool(settings.voice_file and settings.target_armature)

    def execute(self, context):
        settings = context.scene.melusina_portrait
        armature = bpy.data.objects.get(settings.target_armature)
        if armature is None:
            settings.portrait_status = "Target armature not found in scene."
            self.report({"ERROR"}, "Armature missing")
            return {"CANCELLED"}

        if armature.type != "ARMATURE":
            settings.portrait_status = "Target object is not an armature."
            self.report({"ERROR"}, "Not an armature")
            return {"CANCELLED"}

        # Parse voice file
        try:
            from .phoneme_reader import parse_voice_file
            track = parse_voice_file(settings.voice_file)
        except Exception as exc:
            settings.portrait_status = f"Parse error: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        # Build settings
        from .expression_mixer import (
            PortraitSettings,
            generate_portrait_animation,
        )
        ps = PortraitSettings(
            fps=settings.portrait_fps,
            blend_strength=settings.portrait_blend_strength,
            idle_amplitude=settings.portrait_idle_amplitude,
            eye_blink_rate=settings.portrait_eye_blink_rate,
            smooth_frames=settings.portrait_smooth_frames,
        )

        try:
            result = generate_portrait_animation(armature, track, ps)
        except Exception as exc:
            settings.portrait_status = f"Generation error: {exc}"
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if "error" in result:
            settings.portrait_status = result["error"]
            self.report({"WARNING"}, result["error"])
            return {"CANCELLED"}

        settings.voice_track_name = track.name
        settings.portrait_status = (
            f"Generated {result['frame_count']} frames "
            f"({result['duration_sec']:.1f}s) for '{track.name}' "
            f"using {result['viseme_count']} visemes."
        )
        self.report(
            {"INFO"},
            f"Portrait: {result['frame_count']} frames, "
            f"{result['viseme_count']} visemes"
        )
        return {"FINISHED"}


class MPR_OT_clear_portrait(Operator):
    """Remove all portrait animation from the rig."""

    bl_idname = "melusina.clear_portrait"
    bl_label = "Clear Animation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.melusina_portrait
        return bool(settings.target_armature)

    def execute(self, context):
        settings = context.scene.melusina_portrait
        armature = bpy.data.objects.get(settings.target_armature)
        if armature is None:
            return {"CANCELLED"}

        try:
            from .expression_mixer import clear_all_portrait_animation
            count = clear_all_portrait_animation(armature)
            settings.portrait_status = f"Cleared {count} shape key animations."
            self.report({"INFO"}, f"Cleared {count} shape key tracks")
        except Exception as exc:
            settings.portrait_status = f"Clear error: {exc}"
            self.report({"ERROR"}, str(exc))

        return {"FINISHED"}


class MPR_OT_preview_portrait(Operator):
    """Play/pause the portrait animation preview."""

    bl_idname = "melusina.preview_portrait"
    bl_label = "Play Preview"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
            self.report({"INFO"}, "Paused")
        else:
            bpy.ops.screen.animation_play()
            self.report({"INFO"}, "Playing")
        return {"FINISHED"}


class MPR_OT_export_timing_json(Operator):
    """Export the current voice track as a simplified timing JSON template."""

    bl_idname = "melusina.export_timing_json"
    bl_label = "Export Timing Template"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = context.scene.melusina_portrait
        return bool(settings.voice_file)

    def execute(self, context):
        settings = context.scene.melusina_portrait
        try:
            from .phoneme_reader import parse_voice_file, timing_json_example

            # If a voice file is loaded, convert it to timing JSON
            if settings.voice_file and os.path.isfile(settings.voice_file):
                track = parse_voice_file(settings.voice_file)
                events = [
                    {
                        "p": e.phoneme,
                        "start": round(e.start_sec, 3),
                        "end": round(e.end_sec, 3),
                        "tone": e.tone,
                    }
                    for e in track.events
                ]
                data = {
                    "name": track.name,
                    "tempo": track.tempo,
                    "events": events,
                }
            else:
                data = timing_json_example()

            out_path = Path(settings.voice_file).with_suffix(".timing.json")
            import json
            out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            settings.portrait_status = f"Exported to {out_path}"
            self.report({"INFO"}, f"Exported to {out_path.name}")
        except Exception as exc:
            settings.portrait_status = f"Export error: {exc}"
            self.report({"ERROR"}, str(exc))

        return {"FINISHED"}


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# N-Panel UI
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class SURREAL_ARCH_PT_living_portrait(Panel):
    """Living Portrait Engine — voice-driven character animation.

    bl_idname must not use MPR_PT_* — that prefix belongs to Modern Primitive.
    """

    bl_label = "Living Portrait"
    bl_idname = "SURREAL_ARCH_PT_living_portrait"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 14

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        settings = context.scene.melusina_portrait

        # ΓöÇΓöÇ Voice File ΓöÇΓöÇ
        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "voice_file", text="Voice")
        row.operator("melusina.load_voice", text="", icon="FILE_SOUND")

        if settings.voice_track_name:
            box.label(
                text=f"Track: {settings.voice_track_name}",
                icon="FILE_TEXT",
            )

        # ΓöÇΓöÇ Armature ΓöÇΓöÇ
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Armature:", icon="ARMATURE_DATA")
        if settings.target_armature:
            row.label(text=settings.target_armature, icon="CHECKBOX_HLT")
        row.operator("melusina.detect_rig", text="Detect", icon="VIEWZOOM")

        if settings.viseme_report:
            col = box.column(align=True)
            for line in settings.viseme_report.split("\n")[:6]:
                col.label(text=line, icon="SHAPEKEY_DATA")

        # ΓöÇΓöÇ Settings ΓöÇΓöÇ
        box = layout.box()
        row = box.row(align=True)
        row.prop(settings, "portrait_expand_settings", text="",
                 icon="DOWNARROW_HLT" if settings.portrait_expand_settings else "RIGHTARROW",
                 emboss=False)
        row.label(text="Settings", icon="PREFERENCES")

        if settings.portrait_expand_settings:
            col = box.column(align=True)
            col.prop(settings, "portrait_fps")
            row = col.row(align=True)
            row.prop(settings, "portrait_blend_strength", slider=True)
            row = col.row(align=True)
            row.prop(settings, "portrait_idle_amplitude", slider=True)
            row = col.row(align=True)
            row.prop(settings, "portrait_eye_blink_rate", slider=True)
            col.prop(settings, "portrait_smooth_frames")

        # ΓöÇΓöÇ Actions ΓöÇΓöÇ
        layout.separator()
        row = layout.row(align=True)
        row.operator("melusina.generate_portrait", text="Generate Portrait",
                     icon="RENDER_ANIMATION")
        row = layout.row(align=True)
        row.operator("melusina.preview_portrait", text="Play / Pause",
                     icon="PLAY")
        row.operator("melusina.clear_portrait", text="Clear",
                     icon="X")
        row = layout.row(align=True)
        row.operator("melusina.export_timing_json", text="Export Timing JSON",
                     icon="EXPORT")

        # ΓöÇΓöÇ Status ΓöÇΓöÇ
        if settings.portrait_status:
            layout.separator()
            box = layout.box()
            box.label(text=settings.portrait_status, icon="INFO")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Registration
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

CLASSES = [
    MPR_SceneSettings,
    MPR_OT_load_voice,
    MPR_OT_detect_rig,
    MPR_OT_generate_portrait,
    MPR_OT_clear_portrait,
    MPR_OT_preview_portrait,
    MPR_OT_export_timing_json,
    SURREAL_ARCH_PT_living_portrait,
]


def register_props():
    bpy.types.Scene.melusina_portrait = PointerProperty(type=MPR_SceneSettings)


def unregister_props():
    try:
        del bpy.types.Scene.melusina_portrait
    except AttributeError:
        pass
