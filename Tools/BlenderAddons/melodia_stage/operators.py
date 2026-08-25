import bpy
import math
from mathutils import Vector


def _get_selection_bounds(context):
    """Return (center, max_dimension, min_corner, max_corner) of selected objects."""
    objs = [o for o in context.selected_objects if o.type != 'CAMERA' and o.type != 'LIGHT']
    if not objs:
        return None, 0, Vector((0, 0, 0)), Vector((0, 0, 0))

    min_corner = Vector((float('inf'),) * 3)
    max_corner = Vector((float('-inf'),) * 3)

    for obj in objs:
        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_corner = Vector(min(a, b) for a, b in zip(min_corner, world_corner))
            max_corner = Vector(max(a, b) for a, b in zip(max_corner, world_corner))

    center = (min_corner + max_corner) / 2
    dimensions = max_corner - min_corner
    max_dim = max(dimensions)

    return center, max_dim, min_corner, max_corner


def _create_camera(context, center, distance, height):
    """Create and return a camera looking at center."""
    cam_data = bpy.data.cameras.new(name="MelodiaStage_Cam")
    cam_data.lens = 85  # portrait lens
    cam_data.clip_start = 0.1
    cam_data.clip_end = 1000

    cam_obj = bpy.data.objects.new("MelodiaStage_Camera", cam_data)
    cam_obj.location = (0, -distance, height)
    context.collection.objects.link(cam_obj)

    # Point at center
    direction = center - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    return cam_obj


def _create_three_point_lighting(context, center, size):
    """Create key, fill, and rim lights around the subject."""
    lights = {}

    # Key light - main, bright, 45 deg up-right-front
    key_data = bpy.data.lights.new("MelodiaStage_Key", type='AREA')
    key_data.energy = 800
    key_data.size = size * 0.5
    key_obj = bpy.data.objects.new("MelodiaStage_Key", key_data)
    key_obj.location = (size * 1.5, -size * 1.5, size * 2)
    context.collection.objects.link(key_obj)
    direction = center - key_obj.location
    key_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    lights['key'] = key_obj

    # Fill light - softer, opposite side, lower
    fill_data = bpy.data.lights.new("MelodiaStage_Fill", type='AREA')
    fill_data.energy = 300
    fill_data.size = size * 0.8
    fill_obj = bpy.data.objects.new("MelodiaStage_Fill", fill_data)
    fill_obj.location = (-size * 2, -size * 1.2, size * 0.5)
    context.collection.objects.link(fill_obj)
    direction = center - fill_obj.location
    fill_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    lights['fill'] = fill_obj

    # Rim light - behind, for silhouette edge
    rim_data = bpy.data.lights.new("MelodiaStage_Rim", type='SPOT')
    rim_data.energy = 500
    rim_data.spot_size = math.radians(45)
    rim_obj = bpy.data.objects.new("MelodiaStage_Rim", rim_data)
    rim_obj.location = (0, size * 1.5, size * 1.5)
    context.collection.objects.link(rim_obj)
    direction = center - rim_obj.location
    rim_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    lights['rim'] = rim_obj

    return lights


def _create_shadow_catcher(context, center, size):
    """Create a large plane below the subject to catch shadows."""
    bpy.ops.mesh.primitive_plane_add(
        size=size * 6,
        location=(0, 0, center.z - size * 0.5)
    )
    plane = context.active_object
    plane.name = "MelodiaStage_ShadowCatcher"

    # Make it shadow catcher (Cycles) or shadow-only (EEVEE)
    plane.is_shadow_catcher = True
    plane.visible_camera = True
    plane.visible_diffuse = False
    plane.visible_glossy = False

    return plane


def _create_turntable_empty(context, center):
    """Create empty at selection center for turntable rotation."""
    empty = bpy.data.objects.new("MelodiaStage_Turntable", None)
    empty.location = center
    empty.empty_display_type = 'CIRCLE'
    empty.empty_display_size = 0.3
    context.collection.objects.link(empty)
    return empty


class STAGE_OT_stage_selected(bpy.types.Operator):
    """Create turntable + studio lighting rig around selected objects"""
    bl_idname = "melodia_stage.stage_selected"
    bl_label = "Stage Selected"
    bl_icon = 'CAMERA_DATA'
    bl_options = {'REGISTER', 'UNDO'}

    camera_distance_factor: bpy.props.FloatProperty(
        name="Camera Distance",
        default=3.0,
        min=1.0,
        max=10.0,
        description="How far the camera sits from the subject (x subject height)"
    )

    light_height_factor: bpy.props.FloatProperty(
        name="Light Height",
        default=1.5,
        min=0.5,
        max=5.0,
        description="How high the key light sits (x subject height)"
    )

    include_shadow_catcher: bpy.props.BoolProperty(
        name="Shadow Catcher",
        default=True,
        description="Add a shadow-catching floor plane"
    )

    def execute(self, context):
        center, max_dim, _, _ = _get_selection_bounds(context)

        if center is None:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}

        if max_dim < 0.001:
            self.report({'WARNING'}, "Selection is too small")
            return {'CANCELLED'}

        # Build the rig
        distance = max_dim * self.camera_distance_factor
        height = max_dim * self.light_height_factor

        cam = _create_camera(context, center, distance, height)
        lights = _create_three_point_lighting(context, center, max_dim)
        turntable = _create_turntable_empty(context, center)

        if self.include_shadow_catcher:
            _create_shadow_catcher(context, center, max_dim)

        # Set as active camera
        context.scene.camera = cam
        context.scene.render.resolution_x = 2048
        context.scene.render.resolution_y = 2048

        # Frame the camera view
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'
                break

        self.report({'INFO'}, f"Staged {len(context.selected_objects)} object(s)")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class STAGE_OT_animate_spin(bpy.types.Operator):
    """Add 360-degree turntable animation to staged rig"""
    bl_idname = "melodia_stage.animate_spin"
    bl_label = "Animate Spin"
    bl_icon = 'ANIM'
    bl_options = {'REGISTER', 'UNDO'}

    duration_seconds: bpy.props.FloatProperty(
        name="Duration (sec)",
        default=4.0,
        min=1.0,
        max=30.0,
        description="Time for one full rotation"
    )

    fps: bpy.props.IntProperty(
        name="FPS",
        default=24,
        min=12,
        max=120
    )

    reverse: bpy.props.BoolProperty(
        name="Reverse",
        default=False
    )

    def execute(self, context):
        turntable = bpy.data.objects.get("MelodiaStage_Turntable")
        if turntable is None:
            self.report({'WARNING'}, "No turntable rig found. Run Stage Selected first.")
            return {'CANCELLED'}

        # Calculate frames
        total_frames = int(self.duration_seconds * self.fps)
        start_angle = math.radians(360) if not self.reverse else math.radians(-360)

        # Set scene frame range
        context.scene.frame_start = 1
        context.scene.frame_end = total_frames
        context.scene.render.fps = self.fps

        # Clear existing animation
        turntable.animation_data_clear()

        # Frame 1: rotation = 0
        turntable.rotation_euler = (0, 0, 0)
        turntable.keyframe_insert(data_path="rotation_euler", frame=1)

        # Last frame: rotation = 360
        turntable.rotation_euler = (0, 0, start_angle)
        turntable.keyframe_insert(data_path="rotation_euler", frame=total_frames)

        # Set linear interpolation (constant speed)
        if turntable.animation_data and turntable.animation_data.action:
            for fc in turntable.animation_data.action.fcurves:
                for kfp in fc.keyframe_points:
                    kfp.interpolation = 'LINEAR'

        # Update scene
        context.scene.frame_set(1)

        self.report({'INFO'}, f"Spin animation: {total_frames} frames @ {self.fps} fps")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class STAGE_OT_clear_stage(bpy.types.Operator):
    """Remove all Melodia Stage objects from the scene"""
    bl_idname = "melodia_stage.clear_stage"
    bl_label = "Clear Stage"
    bl_icon = 'TRASH'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        names_to_remove = []
        for obj in bpy.data.objects:
            if obj.name.startswith("MelodiaStage_"):
                names_to_remove.append(obj)

        if not names_to_remove:
            self.report({'INFO'}, "No Melodia Stage objects found")
            return {'CANCELLED'}

        for obj in names_to_remove:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Also clear camera reference if it was our stage cam
        if context.scene.camera and context.scene.camera.name == "MelodiaStage_Camera":
            context.scene.camera = None

        self.report({'INFO'}, f"Removed {len(names_to_remove)} stage objects")
        return {'FINISHED'}


class STAGE_OT_render_animation(bpy.types.Operator):
    """Render the turntable animation to an image sequence"""
    bl_idname = "melodia_stage.render_animation"
    bl_label = "Render Spin"
    bl_icon = 'RENDER_ANIMATION'

    output_path: bpy.props.StringProperty(
        name="Output Path",
        default="//renders/turntable_",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        scene = context.scene
        if not scene.camera or scene.camera.name != "MelodiaStage_Camera":
            self.report({'WARNING'}, "No staged camera found. Run Stage Selected first.")
            return {'CANCELLED'}

        scene.render.filepath = self.output_path
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'

        bpy.ops.render.render(animation=True)

        self.report({'INFO'}, "Render complete")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


classes = [
    STAGE_OT_stage_selected,
    STAGE_OT_animate_spin,
    STAGE_OT_clear_stage,
    STAGE_OT_render_animation,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
