"""Operators and scene properties for Resonant World Studio."""

import bpy
import os
import json

from . import bridge
from . import build


def _preset_items(self, context):
    try:
        ww, _td = bridge.load_modules()
        items = []
        for key, val in sorted(ww.WALKABLE_PRESETS.items()):
            items.append((key, val.get("label", key),
                          val.get("description", "")))
        return items or [("walkable_valley", "Walkable Valley", "")]
    except Exception:
        return [("walkable_valley", "Walkable Valley", "")]


def _style_items(self, context):
    try:
        _ww, td = bridge.load_modules()
        items = []
        for key, val in sorted(td.DRESSING_STYLES.items()):
            items.append((key, val.get("label", key),
                          val.get("description", "")))
        return items or [("bare", "Bare", "")]
    except Exception:
        return [("bare", "Bare", "")]


def _midi_items(self, context):
    found = bridge.discover_midi()
    if not found:
        return [("", "No MIDI found", "")]
    root = bridge.repo_root()
    out = []
    for path in found[:64]:
        try:
            desc = os.path.relpath(path, root)
        except ValueError:
            desc = path
        out.append((path, os.path.basename(path), desc))
    return out


class RWProps(bpy.types.PropertyGroup):
    midi: bpy.props.EnumProperty(name="MIDI", items=_midi_items)
    preset: bpy.props.EnumProperty(name="Terrain", items=_preset_items)
    style: bpy.props.EnumProperty(name="Dressing", items=_style_items)
    eye_level: bpy.props.BoolProperty(
        name="Stand On Surface", default=False,
        description="Place the camera at eye height on the terrain instead of "
                    "an establishing view")
    with_melusina: bpy.props.BoolProperty(
        name="Melusina", default=False,
        description="Place Melusina on the terrain column beneath her")
    report_json: bpy.props.StringProperty(default="")


class RW_OT_build(bpy.types.Operator):
    """Generate a walkable level from the selected MIDI"""
    bl_idname = "resonant_world.build"
    bl_label = "Build Level"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.resonant_world
        midi = props.midi
        if not midi or not os.path.exists(midi):
            self.report({'WARNING'}, "No MIDI selected")
            return {'CANCELLED'}

        try:
            ww, td = bridge.load_modules()
            field, preset, metrics = bridge.build_field(midi, props.preset)
        except Exception as exc:
            self.report({'ERROR'}, "Generator failed: %s" % exc)
            return {'CANCELLED'}

        if not field:
            self.report({'ERROR'}, "MIDI produced no notes")
            return {'CANCELLED'}

        tmp = os.path.join(
            os.environ.get("LOCALAPPDATA", bridge.repo_root()),
            "Temp", "resonant_world_studio.obj")
        voxels, verts, faces = bridge.export_obj(field, tmp)

        build.clear_generated()
        terrain = build.terrain_from_obj(tmp)
        if terrain is None:
            self.report({'ERROR'}, "OBJ produced no geometry")
            return {'CANCELLED'}

        centre, size, _mn, mx = build.bounds_of([terrain])
        span = max(size)

        props_plan, pstats = td.plan_dressing(field, props.style)
        n_props = build.instance_props(props_plan)

        build.build_world()
        build.build_lights(centre, span)

        report = {
            "midi": os.path.basename(midi),
            "preset": props.preset,
            "style": props.style,
            "voxels": voxels,
            "verts": verts,
            "faces": faces,
            "props": n_props,
            "props_by_kind": pstats.get("by_kind", {}),
            "footprint": metrics["footprint"],
            "aspect_ratio": metrics["aspect_ratio"],
            "height_span": metrics["height_span"],
            "walkable_fraction": metrics["walkable_fraction"],
            "largest_region_fraction": metrics["largest_region_fraction"],
            "cells": metrics["cells"],
        }

        if props.with_melusina:
            mel_ok, mel_ground = build.add_melusina(field, centre)
            report["melusina"] = mel_ok
            if mel_ok:
                report["melusina_ground_z"] = mel_ground
        else:
            report["melusina"] = False

        def height_at(x, y):
            return td.surface_height_at(field, x, y)

        build.build_camera(centre, size, height_fn=height_at,
                          eye_level=props.eye_level)
        build.configure_render()

        props.report_json = json.dumps(report)

        self.report({'INFO'}, "%dx%d cells | walkable %.0f%% | %d props" % (
            metrics["footprint"][0], metrics["footprint"][1],
            metrics["walkable_fraction"] * 100, n_props))
        return {'FINISHED'}


class RW_OT_clear(bpy.types.Operator):
    """Remove everything this addon generated"""
    bl_idname = "resonant_world.clear"
    bl_label = "Clear"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        build.clear_generated()
        context.scene.resonant_world.report_json = ""
        self.report({'INFO'}, "Cleared generated collections")
        return {'FINISHED'}


class RW_OT_export_report(bpy.types.Operator):
    """Write the measured walkability report next to the project audits"""
    bl_idname = "resonant_world.export_report"
    bl_label = "Export Report"

    def execute(self, context):
        raw = context.scene.resonant_world.report_json
        if not raw:
            self.report({'WARNING'}, "Build a level first")
            return {'CANCELLED'}
        dest_dir = os.path.join(bridge.repo_root(), "Saved", "Audit")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "resonant_world_studio_report.json")
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(raw)
        self.report({'INFO'}, "Wrote %s" % dest)
        return {'FINISHED'}


CLASSES = (RWProps, RW_OT_build, RW_OT_clear, RW_OT_export_report)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.resonant_world = bpy.props.PointerProperty(type=RWProps)


def unregister():
    if hasattr(bpy.types.Scene, "resonant_world"):
        del bpy.types.Scene.resonant_world
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
