import bpy
from .engine import update_sdf_callback, _update_preview

# --- V15: Deform Stack Item ---
class SDF_DeformItem(bpy.types.PropertyGroup):
    """デフォームスタックの各項目"""
    deform_type: bpy.props.EnumProperty(
        items=[
            ('ELONGATE', "Elongate", "Stretch space along axes"),
            ('BEND', "Bend", "Bend space around axis"),
            ('TWIST', "Twist", "Twist space along axis"),
            ('TAPER', "Taper", "Taper space along axis"),
        ],
        name="Type", default='BEND', update=update_sdf_callback
    )
    axis: bpy.props.EnumProperty(
        items=[('0', "X", ""), ('1', "Y", ""), ('2', "Z", "")],
        name="Axis", default='2', update=update_sdf_callback
    )
    factor: bpy.props.FloatProperty(name="Factor", default=0.0, update=update_sdf_callback)
    origin: bpy.props.FloatVectorProperty(name="Origin Offset", default=(0.0, 0.0, 0.0), update=update_sdf_callback)
    # Elongate用（XYZ個別）
    elongate_x: bpy.props.FloatProperty(name="X", default=0.0, min=0.0, update=update_sdf_callback)
    elongate_y: bpy.props.FloatProperty(name="Y", default=0.0, min=0.0, update=update_sdf_callback)
    elongate_z: bpy.props.FloatProperty(name="Z", default=0.0, min=0.0, update=update_sdf_callback)
    enabled: bpy.props.BoolProperty(name="Enabled", default=True, update=update_sdf_callback)

def update_res_preset(self, context):
    """Updates the resolution immediately if the preset value is currently applied"""
    if self.resolution == self.res_preset_low or self.resolution == self.res_preset_high:
        # If the current resolution matches one of the presets, synchronize the values
        # Note: Since full automatic synchronization is a matter of preference, 
        # only the convenience during "slider operation" is considered here
        pass
    update_sdf_callback(self, context)

class SDF_SceneProperties(bpy.types.PropertyGroup):
    """Global SDF Settings"""
    all_clear_include_history: bpy.props.BoolProperty(
        name="Include Baked Results",
        description="Check to also delete all baked meshes and history collections",
        default=False
    )
    is_gpu_ready: bpy.props.BoolProperty(name="GPU Ready", default=False)
    is_dc_compiled: bpy.props.BoolProperty(name="DC Compiled", default=False)
    color_mode: bpy.props.EnumProperty(
        items=[
            ('FIXED', "Fixed Palette", "Use the built-in color palette in sequence"),
            ('AUTO_HUE', "Auto Hue", "Rotate hue while keeping saturation/value fixed"),
            ('SINGLE', "Single Color", "Use one shared color for all newly added primitives"),
        ],
        name="Color Mode",
        default='FIXED'
    )
    auto_hue_saturation: bpy.props.FloatProperty(name="Saturation", default=0.55, min=0.0, max=1.0)
    auto_hue_value: bpy.props.FloatProperty(name="Value", default=0.95, min=0.0, max=1.0)
    auto_hue_step_deg: bpy.props.FloatProperty(name="Hue Step (deg)", default=120.0, min=0.0, max=360.0)
    auto_hue_offset: bpy.props.FloatProperty(name="Hue Offset (deg)", default=0.0, min=0.0, max=360.0)
    single_color: bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype='COLOR',
        default=(0.8, 0.8, 0.8),
        min=0.0,
        max=1.0
    )

class SDF_StackItem(bpy.types.PropertyGroup):
    """計算順序リストの各項目"""
    object_ptr: bpy.props.PointerProperty(name="Object", type=bpy.types.Object)
    obj_name: bpy.props.StringProperty(name="Object Name Cache", default="")
    enabled: bpy.props.BoolProperty(name="Enabled", default=True, update=update_sdf_callback)
    item_type: bpy.props.EnumProperty(
        items=[
            ('PRIMITIVE', "Primitive", "Standard SDF Primitive Object"),
            ('COLLECTION', "Collection", "Collection divider for grouping")
        ],
        name="Type", default='PRIMITIVE', update=update_sdf_callback
    )
    name_override: bpy.props.StringProperty(name="Name Override", default="Collection", update=update_sdf_callback)
    empty_ptr: bpy.props.PointerProperty(name="Group Empty", type=bpy.types.Object)
    start_new_group: bpy.props.BoolProperty(name="Start New Group", default=False, update=update_sdf_callback)


class SDF_ObjectProperties(bpy.types.PropertyGroup):
    is_primitive: bpy.props.BoolProperty(name="Is SDF Primitive", default=False, update=update_sdf_callback)
    shape_type: bpy.props.EnumProperty(
        items=[
            ('sphere', "Sphere", ""),
            ('box', "Box", ""),
            ('rounded_box', "Rounded Box", ""),
            ('torus', "Torus", ""),
            ('cylinder', "Cylinder", ""),
            ('capsule', "Capsule", ""),
            ('hex_prism', "Hex Prism", ""),
            ('pyramid', "Pyramid", ""),
            ('capped_cone', "Tapered Cylinder", ""),
            ('ngon_prism', "N-gon Prism", ""),
            ('ellipsoid', "Ellipsoid", "Axis-aligned ellipsoid"),
            ('rounded_cylinder', "Rounded Cylinder", "Cylinder with rounded edges"),
            ('capped_torus', "Capped Torus", "Partial torus (arc)"),
            ('octahedron', "Octahedron", "Regular octahedron"),
            ('cut_sphere', "Cut Sphere", "Sphere cut by a plane")
        ],
        name="Shape", default='sphere', update=update_sdf_callback
    )
    operation: bpy.props.EnumProperty(
        items=[
            ('0', "Union", "", 'ADD', 0), 
            ('1', "Subtract", "", 'REMOVE', 1), 
            ('2', "Intersect", "", 'BOOL_INTERSECT', 2)
        ],
        name="Op", default='0', update=update_sdf_callback
    )
    blend_profile: bpy.props.EnumProperty(
        items=[
            ('0', "Round", "Standard smooth min"),
            ('1', "Sharp", "Pulls in toward the corner"),
            ('2', "Soft", "Gentle, smoothly continuous"),
            ('3', "Tight", "Squared, deep but tight"),
            ('4', "Chamfer", "Flat 45 degree bevel")
        ],
        name="Profile", default='0', update=update_sdf_callback
    )
    chamfer_smooth: bpy.props.FloatProperty(name="Chamfer Smooth", default=0.0, min=0.0, max=2.0, update=update_sdf_callback)
    
    # --- V16: Primitive Edge Profile & Modifiers ---
    edge_profile: bpy.props.EnumProperty(
        items=[
            ('0', "Round", "Standard radius rounding"),
            ('1', "Sharp", "Pulls in toward the corner"),
            ('2', "Soft", "Gentle, smoothly continuous"),
            ('3', "Tight", "Squared, deep but tight"),
            ('4', "Chamfer", "Flat 45 degree bevel")
        ],
        name="Edge Profile", default='0', update=update_sdf_callback
    )
    edge_profile_size: bpy.props.FloatProperty(name="Edge Size", default=0.1, min=0.0, max=100.0, update=update_sdf_callback)
    edge_chamfer_smooth: bpy.props.FloatProperty(name="Edge Chamfer Smooth", default=0.0, min=0.0, max=2.0, update=update_sdf_callback)
    shell_thickness: bpy.props.FloatProperty(name="Shell Thickness", default=0.0, min=0.0, max=100.0, update=update_sdf_callback)
    
    radius: bpy.props.FloatProperty(name="Radius", default=1.0, min=0.01, max=100.0, update=update_sdf_callback)
    smoothness: bpy.props.FloatProperty(name="Smoothness", default=0.2, min=0.0, max=2.0, update=update_sdf_callback)
    color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', default=(1.0, 1.0, 1.0), min=0.0, max=1.0, update=update_sdf_callback)
    metallic: bpy.props.FloatProperty(name="Metallic", default=0.0, min=0.0, max=1.0, update=update_sdf_callback)
    roughness: bpy.props.FloatProperty(name="Roughness", default=0.5, min=0.0, max=1.0, update=update_sdf_callback)
    noise_strength: bpy.props.FloatProperty(name="Noise", default=0.0, min=0.0, max=2.0, update=update_sdf_callback)
    noise_scale: bpy.props.FloatProperty(name="Noise Scale", default=5.0, min=0.1, max=50.0, update=update_sdf_callback)
    is_output: bpy.props.BoolProperty(name="Is SDF Output", default=False, update=update_sdf_callback)
    target_collection: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection, update=update_sdf_callback)
    resolution: bpy.props.IntProperty(name="Res", default=48, min=16, max=1024, update=update_sdf_callback)
    domain_size: bpy.props.FloatProperty(name="Domain", default=5.0, min=1.0, max=50.0, update=update_sdf_callback)
    auto_domain: bpy.props.BoolProperty(name="Auto Expand Domain", default=True, description="Automatically expand calculation area to fit all primitives", update=update_sdf_callback)

    preview_quality: bpy.props.EnumProperty(
        items=[
            ('LOW', "Low (128)", "Low load. Suitable for simple shapes"),
            ('MID', "Mid (256)", "Balanced. Suitable for standard deformation"),
            ('HIGH', "High (512)", "High quality. Minimizes rendering artifacts for complex deformation")
        ],
        name="Preview Quality", default='LOW', update=_update_preview
    )
    use_live_normals: bpy.props.BoolProperty(name="Real-time Normals", default=False, update=update_sdf_callback)
    algo_type: bpy.props.EnumProperty(
        items=[
            ('MC', "Marching Cubes", "Standard (GPU Sparse Accelerated) - Fast feedback"), 
            ('DC', "Dual Contouring", "Sharp Edges (GPU Sparse Accelerated) - High quality")
        ],
        name="Algo", default='MC', update=update_sdf_callback
    )
    sym_x: bpy.props.BoolProperty(name="X", default=False, update=update_sdf_callback)
    sym_y: bpy.props.BoolProperty(name="Y", default=False, update=update_sdf_callback)
    sym_z: bpy.props.BoolProperty(name="Z", default=False, update=update_sdf_callback)
    
    # --- V13.1: Resolution Presets ---
    res_preset_low: bpy.props.IntProperty(name="Low Preset", default=64, min=16, max=1024, update=update_res_preset)
    res_preset_high: bpy.props.IntProperty(name="High Preset", default=256, min=16, max=1024, update=update_res_preset)
    res_mode_auto_normals: bpy.props.BoolProperty(name="Auto-enable Live Normals on High", default=True, update=update_sdf_callback)
    
    # --- V12: Placement ---
    # --- V12: Reinforced Layout (Layout Stacking) ---
    layout_use_mirror: bpy.props.BoolProperty(name="Mirror", default=False, update=update_sdf_callback)
    layout_use_radial: bpy.props.BoolProperty(name="Radial", default=False, update=update_sdf_callback)
    layout_use_spiral: bpy.props.BoolProperty(name="Spiral", default=False, update=update_sdf_callback)
    layout_use_jitter: bpy.props.BoolProperty(name="Jitter", default=False, update=update_sdf_callback)
    
    # Mirror settings
    mirror_offset: bpy.props.FloatProperty(name="Offset", default=0.0, update=update_sdf_callback)
    mirror_x: bpy.props.BoolProperty(name="X", default=False, update=update_sdf_callback)
    mirror_y: bpy.props.BoolProperty(name="Y", default=False, update=update_sdf_callback)
    mirror_z: bpy.props.BoolProperty(name="Z", default=False, update=update_sdf_callback)
    
    # Radial/Spiral settings
    radial_count: bpy.props.IntProperty(name="Count", default=4, min=1, max=64, update=update_sdf_callback)
    radial_radius: bpy.props.FloatProperty(name="Radius", default=1.0, update=update_sdf_callback)
    radial_axis: bpy.props.EnumProperty(
        items=[('0', "X", ""), ('1', "Y", ""), ('2', "Z", "")],
        name="Axis", default='2', update=update_sdf_callback
    )
    spiral_pitch: bpy.props.FloatProperty(name="Pitch (Height)", default=0.0, update=update_sdf_callback)
    
    # Jitter settings
    jitter_seed: bpy.props.FloatProperty(name="Seed", default=1.0, update=update_sdf_callback)
    jitter_strength: bpy.props.FloatProperty(name="Strength", default=0.0, update=update_sdf_callback)

    # --- V12 Phase 2: Grid & Advanced Rotation ---
    layout_use_grid: bpy.props.BoolProperty(name="Grid", default=False, update=update_sdf_callback)
    grid_count_x: bpy.props.IntProperty(name="Count X", default=1, min=1, max=20, update=update_sdf_callback)
    grid_count_y: bpy.props.IntProperty(name="Count Y", default=1, min=1, max=20, update=update_sdf_callback)
    grid_count_z: bpy.props.IntProperty(name="Count Z", default=1, min=1, max=20, update=update_sdf_callback)
    grid_spacing_x: bpy.props.FloatProperty(name="Spacing X", default=2.0, update=update_sdf_callback)
    grid_spacing_y: bpy.props.FloatProperty(name="Spacing Y", default=2.0, update=update_sdf_callback)
    grid_spacing_z: bpy.props.FloatProperty(name="Spacing Z", default=2.0, update=update_sdf_callback)

    instance_rot_x: bpy.props.FloatProperty(name="Rotation X", default=0.0, subtype='ANGLE', update=update_sdf_callback)
    instance_rot_y: bpy.props.FloatProperty(name="Rotation Y", default=0.0, subtype='ANGLE', update=update_sdf_callback)
    instance_rot_z: bpy.props.FloatProperty(name="Rotation Z", default=0.0, subtype='ANGLE', update=update_sdf_callback)

    step_rot_x: bpy.props.FloatProperty(name="Accum Rot X", default=0.0, subtype='ANGLE', update=update_sdf_callback)
    step_rot_y: bpy.props.FloatProperty(name="Accum Rot Y", default=0.0, subtype='ANGLE', update=update_sdf_callback)
    step_rot_z: bpy.props.FloatProperty(name="Accum Rot Z", default=0.0, subtype='ANGLE', update=update_sdf_callback)
    
    # --- V15: Deform Stack ---
    deform_stack: bpy.props.CollectionProperty(type=SDF_DeformItem)
    deform_stack_index: bpy.props.IntProperty(name="Deform Stack Index", default=0)

    # --- V13: Generic Parameters ---
    p1: bpy.props.FloatProperty(name="Param 1", default=1.0, min=-100.0, max=100.0, update=update_sdf_callback)
    p2: bpy.props.FloatProperty(name="Param 2", default=1.0, min=-100.0, max=100.0, update=update_sdf_callback)
    p3: bpy.props.FloatProperty(name="Param 3", default=1.0, min=-100.0, max=100.0, update=update_sdf_callback)
    p4: bpy.props.FloatProperty(name="Param 4", default=1.0, min=-100.0, max=100.0, update=update_sdf_callback)

    # --- V13: Individual Corrections ---
    ngon_sides: bpy.props.IntProperty(name="Sides", default=6, min=3, max=64, update=update_sdf_callback)

    # --- V13.2: Weld (Merge by Distance) ---
    use_weld: bpy.props.BoolProperty(name="Weld (Merge Verts)", default=True, update=update_sdf_callback)
    weld_threshold: bpy.props.FloatProperty(name="Weld Threshold (Scale)", default=0.001, min=0.0, max=1.0, precision=4, update=update_sdf_callback)

    # --- V7: スタック管理 ---
    sdf_stack: bpy.props.CollectionProperty(type=SDF_StackItem)
    sdf_stack_index: bpy.props.IntProperty(name="Stack Index", default=0, update=update_sdf_callback)
    use_solo: bpy.props.BoolProperty(name="Solo Mode", default=False, update=update_sdf_callback)
