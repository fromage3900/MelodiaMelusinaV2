"""Melodia Studio panel — MIDI-driven Resonant World generation.

Rewritten to use midi_bridge instead of a bare `from midi_voxel_v3 import`
that could never resolve. Also fixes: mesh built with no material and no
vertex-colour hookup, a stub agent button, and hardcoded lights/camera that
ignored terrain scale.
"""

import bpy
import os

from . import midi_bridge


# ------------------------------------------------------------- properties

def _preset_enum(self, context):
    items = midi_bridge.preset_items()
    return items if items else [("resonant_default", "Resonant Default", "")]


def _midi_enum(self, context):
    found = midi_bridge.discover_midi()
    if not found:
        return [("", "No MIDI found", "")]
    root = midi_bridge.repo_root()
    items = []
    for path in found[:64]:
        try:
            label = os.path.relpath(path, root)
        except ValueError:
            label = os.path.basename(path)
        items.append((path, os.path.basename(path), label))
    return items


class StudioProps(bpy.types.PropertyGroup):
    midi_file: bpy.props.EnumProperty(
        name="MIDI",
        description="Project MIDI to build terrain from",
        items=_midi_enum,
    )
    preset: bpy.props.EnumProperty(
        name="Preset",
        description="Musical to spatial mapping preset",
        items=_preset_enum,
    )
    custom_midi: bpy.props.StringProperty(
        name="Custom MIDI",
        description="Override with a MIDI file outside the project",
        subtype='FILE_PATH',
        default="",
    )
    dressing_style: bpy.props.EnumProperty(
        name="Dressing",
        description="Musical expansion preset applied to the terrain mesh",
        items=[
            ("bare", "Bare", "Control case"),
            ("verdant", "Verdant Resonance", "Lush walkable ground, soft magic"),
            ("crystalline", "Crystalline Choir", "Hard glowing mineral world, dramatic sky"),
            ("cathedral", "Sunken Cathedral", "Flooded basin, tall pillars, reflective water"),
            ("full_bloom", "Full Bloom", "Everything on"),
            ("waltz_garden", "Waltz Garden", "Triple-meter flow; soft paths with gentle water"),
            ("ballad_plaza", "Ballad Plaza", "Slow open ground; sparse, monumental markers"),
            ("toccata_surface", "Toccata Surface", "Fast, dense ornament; exposed sky effects"),
            ("lullaby_cave", "Lullaby Cave", "Soft underground feel; minimal objects, ambient light"),
            ("fugue_maze", "Fugue Maze", "Dense layered walk; repeating markers and light"),
            ("nocturne_reflection", "Nocturne Reflection", "Single reflective route; quiet and minimal"),
            ("pavane_grotto", "Pavane Grotto", "Slow processional route; flooded chambers and underlight"),
            ("saltarello_ledges", "Saltarello Ledges", "Leaping rhythmic motion; exposed sky and bright markers"),
            ("madrigal_canopy", "Madrigal Canopy", "Layered vocal richness; soft growths and drifting light"),
            ("chaconne_weave", "Chaconne Weave", "Repeating ground bass; monumental route with water and light"),
            ("aria_mist", "Aria Mist", "Solo vocal clarity; sparse, atmospheric, and vertical"),
        ],
        default="verdant",
    )
    last_report: bpy.props.StringProperty(name="Last Report", default="")


# ------------------------------------------------------------- mesh build

def build_terrain_mesh(obj_path, mesh_name="Terrain"):
    """Build a mesh from the generator's OBJ (v x y z r g b) format.

    Vertex colours carry note velocity. The old builder wrote them to a
    layer nothing sampled; here they go into a named colour attribute that
    the material reads.
    """
    if not os.path.exists(obj_path):
        return None

    verts, faces, colors = [], [], []
    with open(obj_path, "r") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
                if len(parts) >= 7:
                    colors.append((float(parts[4]), float(parts[5]),
                                   float(parts[6]), 1.0))
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
        attr = mesh.color_attributes.new(
            name="AuraColor", type='FLOAT_COLOR', domain='CORNER')
        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                vidx = mesh.loops[loop_idx].vertex_index
                if vidx < len(colors):
                    attr.data[loop_idx].color = colors[vidx]

    if len(mesh.uv_layers) == 0:
        mesh.uv_layers.new(name="UVMap")

    obj = bpy.data.objects.new(mesh_name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(build_aura_material())
    return obj


def build_aura_material(name="M_ResonantAura"):
    """Material that actually samples AuraColor for base colour + emission."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)

    col = nt.nodes.new('ShaderNodeVertexColor')
    col.layer_name = "AuraColor"
    col.location = (-300, 0)

    lum = nt.nodes.new('ShaderNodeRGBToBW')
    lum.location = (-100, -200)

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (60, -200)
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


def _selected_midi(props):
    if props.custom_midi:
        path = bpy.path.abspath(props.custom_midi)
        if os.path.exists(path):
            return path
    return props.midi_file or None


# ------------------------------------------------------------- operators

class STUDIO_OT_generate_from_midi(bpy.types.Operator):
    """Generate Resonant World terrain from the selected MIDI"""
    bl_idname = "melodia_studio.generate_from_midi"
    bl_label = "Generate Terrain"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.melodia_studio
        midi = _selected_midi(props)
        if not midi:
            self.report({'WARNING'}, "No MIDI selected")
            return {'CANCELLED'}

        try:
            report = midi_bridge.generate_world(midi, preset_id=props.preset)
        except Exception as exc:
            self.report({'ERROR'}, "Generation failed: %s" % exc)
            return {'CANCELLED'}

        if not report.get("ok"):
            self.report({'ERROR'}, report.get("reason", "unknown failure"))
            return {'CANCELLED'}

        obj = build_terrain_mesh(report["obj"], "Terrain")
        if obj is None:
            self.report({'ERROR'}, "OBJ produced no geometry")
            return {'CANCELLED'}

        try:
            dressing = midi_bridge.dress_terrain(obj, report.get("obj", ""), props.dressing_style)
        except Exception as exc:
            self.report({'WARNING'}, "Dressing failed: %s" % exc)
            dressing = None

        summary = "%d voxels | %d verts | %d faces" % (
            report["voxels"], report["verts"], report["faces"])
        if dressing:
            summary += " | %s" % dressing

        props.last_report = summary
        self.report({'INFO'}, "%s from %s" % (summary, os.path.basename(midi)))
        return {'FINISHED'}


class STUDIO_OT_frame_terrain(bpy.types.Operator):
    """Add camera and lights scaled to the terrain bounds"""
    bl_idname = "melodia_studio.frame_terrain"
    bl_label = "Frame + Light"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import math
        import mathutils

        meshes = [o for o in context.scene.objects
                  if o.type == 'MESH' and o.data]
        if not meshes:
            self.report({'WARNING'}, "No mesh to frame")
            return {'CANCELLED'}

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
            self.report({'WARNING'}, "Degenerate bounds")
            return {'CANCELLED'}

        for name in ("MS_Camera", "MS_Key", "MS_Fill", "MS_Rim"):
            existing = bpy.data.objects.get(name)
            if existing:
                bpy.data.objects.remove(existing, do_unlink=True)

        cam_data = bpy.data.cameras.new("MS_Camera")
        cam_data.lens = 50
        cam_data.clip_end = span * 20
        cam = bpy.data.objects.new("MS_Camera", cam_data)
        context.collection.objects.link(cam)

        fov = 2 * math.atan((cam_data.sensor_width * 0.5) / cam_data.lens)
        dist = (max(size.x, size.z * 1.4) * 0.5) / math.tan(fov * 0.5) * 1.25
        cam.location = (centre.x - span * 0.28,
                        centre.y - dist * 0.82,
                        centre.z + span * 0.42)
        direction = centre - cam.location
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        context.scene.camera = cam

        unit = span * span
        for name, energy, colour, loc in (
            ("MS_Key", unit * 2.2, (1.0, 0.94, 0.86),
             (centre.x + span * 0.6, centre.y - span * 0.75,
              centre.z + span * 0.7)),
            ("MS_Fill", unit * 0.55, (0.62, 0.75, 1.0),
             (centre.x - span * 0.8, centre.y - span * 0.5,
              centre.z + span * 0.25)),
            ("MS_Rim", unit * 1.5, (1.0, 0.55, 0.85),
             (centre.x, centre.y + span * 0.85, centre.z + span * 0.55)),
        ):
            data = bpy.data.lights.new(name, type='AREA')
            data.energy = energy
            data.color = colour
            data.size = span * 0.55
            obj = bpy.data.objects.new(name, data)
            obj.location = loc
            context.collection.objects.link(obj)
            d = centre - mathutils.Vector(loc)
            obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

        self.report({'INFO'}, "Framed span %.1f units" % span)
        return {'FINISHED'}


class STUDIO_OT_write_presets(bpy.types.Operator):
    """Write the preset file so it can be edited outside Blender"""
    bl_idname = "melodia_studio.write_presets"
    bl_label = "Export Presets"

    def execute(self, context):
        path = midi_bridge.write_presets()
        self.report({'INFO'}, "Presets -> %s" % path)
        return {'FINISHED'}


class STUDIO_OT_save_scene(bpy.types.Operator):
    """Save the current scene into GeneratedScenes"""
    bl_idname = "melodia_studio.save_scene"
    bl_label = "Save Scene"

    scene_name: bpy.props.StringProperty(name="Name", default="")

    def execute(self, context):
        import time
        name = self.scene_name.strip() or time.strftime("scene_%Y%m%d_%H%M%S")
        target = os.path.join(midi_bridge.scenes_dir(), name)
        os.makedirs(target, exist_ok=True)
        blend = os.path.join(target, "scene.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend, compress=True)
        self.report({'INFO'}, "Saved %s" % blend)
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


# ------------------------------------------------------------- panel

class STUDIO_PT_panel(bpy.types.Panel):
    bl_label = "Melodia Studio"
    bl_idname = "STUDIO_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia Studio"

    def draw(self, context):
        layout = self.layout
        props = context.scene.melodia_studio

        box = layout.box()
        box.label(text="Resonant World", icon='FILE_SOUND')
        box.prop(props, "midi_file", text="")
        box.prop(props, "preset", text="")
        box.prop(props, "custom_midi", text="Custom")

        col = box.column(align=True)
        col.scale_y = 1.4
        col.operator("melodia_studio.generate_from_midi", icon='MOD_BUILD')

        box = layout.box()
        box.label(text="Presentation", icon='LIGHT')
        col = box.column(align=True)
        col.operator("melodia_studio.frame_terrain", icon='CAMERA_DATA')
        col.operator("melodia_studio.save_scene", icon='FILE_TICK')

        box = layout.box()
        box.label(text="Config", icon='PREFERENCES')
        box.operator("melodia_studio.write_presets", icon='EXPORT')

        if props.last_report:
            layout.separator()
            layout.label(text=props.last_report, icon='CHECKMARK')


classes = [
    StudioProps,
    STUDIO_OT_generate_from_midi,
    STUDIO_OT_frame_terrain,
    STUDIO_OT_write_presets,
    STUDIO_OT_save_scene,
    STUDIO_PT_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.melodia_studio = bpy.props.PointerProperty(type=StudioProps)


def unregister():
    if hasattr(bpy.types.Scene, "melodia_studio"):
        del bpy.types.Scene.melodia_studio
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
