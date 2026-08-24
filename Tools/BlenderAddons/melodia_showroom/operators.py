# Operators for Melodia Showroom
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

import os
import sys
import math
import traceback

try:
    import bpy
    from bpy.types import Operator
except Exception:
    bpy = None
    Operator = object

try:
    import mathutils
except Exception:
    mathutils = None

from . import showroom_bridge as mb


def _preset_parts(preset_id):
    mapping = {
        "verdant_default": ("resonant_default", "verdant"),
        "cathedral_wide_crystalline": ("cathedral_wide", "crystalline"),
        "toccata_spires_toccata": ("toccata_spires", "toccata_surface"),
        "waltz_garden_waltz": ("waltz_corridors", "waltz_garden"),
        "ballad_plaza_ballad": ("ballad_broadstage", "ballad_plaza"),
        "fugue_maze_fugue": ("fugue_labyrinth", "fugue_maze"),
        "nocturne_reflection_nocturne": ("nocturne_ribbon", "nocturne_reflection"),
        "lullaby_cave_lullaby": ("lullaby_undergrowth", "lullaby_cave"),
    }
    return mapping.get(preset_id, ("resonant_default", "verdant"))


def _midi_for_props(repo_root_path, props):
    path = props.midi_file.strip()
    if path:
        if os.path.exists(path):
            return path
        abs_path = os.path.join(repo_root_path, "Content", "MelodiaIntegration", "MIDI", path)
        if os.path.exists(abs_path):
            return abs_path
    midi_dir = mb.content_dir()
    if midi_dir:
        cand = os.path.join(midi_dir, "128BPMarpeggiomelody.mid")
        if os.path.exists(cand):
            return cand
    fallback_roots = [
        os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "EnvironmentPortfolio", "BS_GodFile")),
        r"C:\EnvironmentPortfolio\BS_GodFile",
        "/c/EnvironmentPortfolio/BS_GodFile",
    ]
    for root in fallback_roots:
        cand = os.path.join(root, "Content", "MelodiaIntegration", "MIDI", "128BPMarpeggiomelody.mid")
        if os.path.exists(cand):
            return cand
    return ""


class SHOWROOM_OT_run_pipeline(Operator):
    bl_idname = "melodia_showroom.run_pipeline"
    bl_label = "Run Showroom Pipeline"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.melodia_showroom
        preset_id = props.preset
        terrain_preset, dressing_style = _preset_parts(preset_id)

        try:
            report = _run_pipeline(context, preset_id, terrain_preset, dressing_style, props)
        except Exception as exc:
            self.report({"ERROR"}, "Pipeline failed: %s" % exc)
            print(traceback.format_exc())
            props.last_report = "Failed: %s" % exc
            return {"CANCELLED"}

        if not report.get("ok"):
            reason = report.get("reason", "unknown")
            self.report({"ERROR"}, reason)
            props.last_report = reason
            return {"CANCELLED"}

        props.last_report = "%s | terrain=%s | dress=%s | render=%s" % (
            preset_id, report.get("terrain", ""), report.get("dressing", ""), report.get("render", ""))

        self.report({"INFO"}, props.last_report)
        return {"FINISHED"}


def _run_pipeline(context, preset_id, terrain_preset, dressing_style, props):
    repo_root_path = mb.repo_root()
    midi = _midi_for_props(repo_root_path, props)

    if not midi or not os.path.exists(midi):
        return {"ok": False, "reason": "MIDI not found: %s" % midi}

    showroom_dir = os.path.join(repo_root_path, "Tools", "MelodiaProceduralStudio", "GeneratedScenes", "showroom")
    out_obj = os.path.join(showroom_dir, "terrain.obj")
    os.makedirs(showroom_dir, exist_ok=True)

    report = mb.generate_world(midi, preset_id=terrain_preset, out_obj=out_obj)
    if not report.get("ok"):
        return report

    report["terrain"] = "%dv/%df" % (report.get("voxels", 0), report.get("verts", 0))

    dressing = mb.dress_terrain(None, out_obj, style_id=dressing_style)
    report["dressing"] = dressing or ""

    obj = _build_terrain_mesh(out_obj, "Showroom_Terrain")
    if obj is None:
        return {"ok": False, "reason": "Terrain mesh build failed"}

    _frame_scene(obj)

    render_path = os.path.join(showroom_dir, preset_id + ".png")
    render_ok = _render_viewport(context, render_path, props)
    report["render"] = render_path if render_ok else "failed"
    return report


def _build_terrain_mesh(obj_path, mesh_name):
    if not os.path.exists(obj_path):
        return None

    verts, faces, colors = [], [], []
    with open(obj_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                if len(parts) >= 7:
                    colors.append((float(parts[4]), float(parts[5]), float(parts[6]), 1.0))
                else:
                    colors.append((0.5, 0.5, 0.5, 1.0))
            elif parts[0] == "f":
                faces.append([int(p.split("/")[0]) - 1 for p in parts[1:]])

    if not verts:
        return None

    mesh = bpy.data.meshes.new(mesh_name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    if colors:
        attr = mesh.color_attributes.new(name="AuraColor", type='FLOAT_COLOR', domain='CORNER')
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                vidx = mesh.loops[loop_idx].vertex_index
                if vidx < len(colors):
                    attr.data[loop_idx].color = colors[vidx]

    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(_aura_material())
    return obj


def _aura_material():
    name = "M_ShowroomAura"
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (620, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (320, 0)

    col = nt.nodes.new('ShaderNodeVertexColor')
    col.layer_name = "AuraColor"
    col.location = (-320, 0)

    lum = nt.nodes.new('ShaderNodeRGBToBW')
    lum.location = (-100, -220)

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (120, -220)
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.95

    nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(col.outputs['Color'], lum.inputs['Color'])
    nt.links.new(lum.outputs['Val'], ramp.inputs['Fac'])
    if 'Emission Color' in bsdf.inputs:
        nt.links.new(col.outputs['Color'], bsdf.inputs['Emission Color'])
    if 'Emission Strength' in bsdf.inputs:
        nt.links.new(ramp.outputs['Color'], bsdf.inputs['Emission Strength'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat


def _frame_scene(terrain_obj):
    if bpy is None or mathutils is None:
        raise RuntimeError("bpy/mathutils required for scene framing")
    for name in ("SR_Camera", "SR_Key", "SR_Fill", "SR_Rim", "SR_Back"):
        existing = bpy.data.objects.get(name)
        if existing:
            bpy.data.objects.remove(existing, do_unlink=True)

    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data]
    mn = [1e18] * 3
    mx = [-1e18] * 3
    for o in meshes:
        for corner in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])

    centre = mathutils.Vector([(mn[i] + mx[i]) / 2 for i in range(3)])
    size = mathutils.Vector([mx[i] - mn[i] for i in range(3)])
    span = max(size)
    if span < 1e-6:
        return

    cam_data = bpy.data.cameras.new("SR_Camera")
    cam_data.lens = 50
    cam_data.clip_end = span * 20
    cam = bpy.data.objects.new("SR_Camera", cam_data)
    bpy.context.collection.objects.link(cam)

    fov = 2 * math.atan((cam_data.sensor_width * 0.5) / cam_data.lens)
    dist = (max(size.x, size.z * 1.4) * 0.5) / math.tan(fov * 0.5) * 1.25
    cam.location = (centre.x - span * 0.28, centre.y - dist * 0.82, centre.z + span * 0.42)
    direction = centre - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam

    unit = span * span
    for name, energy, colour, loc in (
        ("SR_Key", unit * 2.2, (1.0, 0.94, 0.86), (centre.x + span * 0.6, centre.y - span * 0.75, centre.z + span * 0.7)),
        ("SR_Fill", unit * 0.55, (0.62, 0.75, 1.0), (centre.x - span * 0.8, centre.y - span * 0.5, centre.z + span * 0.25)),
        ("SR_Rim", unit * 1.5, (1.0, 0.55, 0.85), (centre.x, centre.y + span * 0.85, centre.z + span * 0.55)),
        ("SR_Back", unit * 0.8, (0.85, 0.85, 0.90), (centre.x, centre.y + span * 1.1, centre.z + span * 0.2)),
    ):
        data = bpy.data.lights.new(name, type='AREA')
        data.energy = energy
        data.color = colour
        data.size = span * 0.55
        obj = bpy.data.objects.new(name, data)
        obj.location = loc
        bpy.context.collection.objects.link(obj)
        d = centre - mathutils.Vector(loc)
        obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def _render_viewport(context, path, props):
    scene = context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.filepath = path
    scene.render.image_settings.file_format = 'PNG'
    render_pct = int(getattr(props, "resolution_percent", 100))
    if hasattr(scene.render, "resolution_percent"):
        scene.render.resolution_percent = render_pct
    elif hasattr(scene.render, "resolution_percentage"):
        scene.render.resolution_percentage = render_pct
    scene.eevee.taa_samples = int(props.samples)
    scene.render.film_transparent = bool(props.transparent)

    prev = scene.camera
    try:
        cam = bpy.data.objects.get("SR_Camera")
        if cam:
            scene.camera = cam
        bpy.ops.render.render(write_still=True)
        return True
    except Exception as exc:
        print("render_failed=%s" % repr(exc))
        return False
    finally:
        scene.camera = prev


classes = (SHOWROOM_OT_run_pipeline,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
