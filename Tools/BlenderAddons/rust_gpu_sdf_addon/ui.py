import bpy
from . import rust_gpu_sdf
from .constants import PRIMITIVE_UI_DEFS

class SDF_UL_stack_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            if item.item_type == 'COLLECTION':
                op = row.operator("sdf.select_stack_obj", text=f"== {item.name_override} ==", icon='FILE_FOLDER', emboss=False)
                op.obj_name = item.empty_ptr.name if item.empty_ptr else ""
                op.index = index
                op_dup = row.operator("sdf.duplicate_collection", text="", icon='DUPLICATE', emboss=False)
                op_dup.index = index
                row.prop(item, "start_new_group", text="", toggle=True, emboss=False, icon='LINKED' if not item.start_new_group else 'UNLINKED')
                row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT', emboss=False)
            elif item.object_ptr:
                o = item.object_ptr
                p = o.sdf_props
                shape_icon = 'MESH_UVSPHERE'
                if p.shape_type == 'box': shape_icon = 'MESH_CUBE'
                elif p.shape_type == 'torus': shape_icon = 'MESH_TORUS'
                elif p.shape_type == 'cylinder': shape_icon = 'MESH_CYLINDER'
                
                chip = row.row(align=True)
                chip.scale_x = 0.6
                chip.prop(p, "color", text="")
                row.label(text=f"{index+1:02d}", icon=shape_icon)
                op = row.operator("sdf.select_stack_obj", text=o.name, emboss=False)
                op.obj_name = o.name
                op.index = index
                row.prop(p, "operation", text="", icon_only=True, emboss=False)
                row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT', emboss=False)
            else:
                row.label(text="(Missing Object)", icon='ERROR')

# --- V15: Deform Stack UIList ---
_DEFORM_TYPE_ICONS = {
    'ELONGATE': 'FIXED_SIZE',
    'BEND': 'MOD_SIMPLEDEFORM',
    'TWIST': 'MOD_SCREW',
    'TAPER': 'MOD_TRIANGULATE',
}
_DEFORM_TYPE_LABELS = {
    'ELONGATE': "Elongate",
    'BEND': "Bend",
    'TWIST': "Twist",
    'TAPER': "Taper",
}

class SDF_UL_deform_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            d_icon = _DEFORM_TYPE_ICONS.get(item.deform_type, 'MODIFIER')
            label = _DEFORM_TYPE_LABELS.get(item.deform_type, "?")
            axis_labels = {0: "X", 1: "Y", 2: "Z"}
            axis_str = axis_labels.get(int(item.axis), "?")
            row.label(text=f"{index+1}. {label} ({axis_str})", icon=d_icon)
            row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT', emboss=False)

class SDF_PT_main(bpy.types.Panel):
    bl_label = "SDF.R Modeling"
    bl_idname = "SDF_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SDF-R"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.sdf_scene_props
        
        # --- UI Guard (Initialization status) ---
        if not props.is_gpu_ready:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="SDF.R Engine Warming-up...", icon='NODE_COMPOSITING')
            col.separator()
            col.label(text="Initializing (First time takes approx. 2 mins)")
            col.label(text="Please wait and do not operate Blender...")
            return
        
        # 1. Header & Status
        row = layout.row(align=True)
        row.prop(scene, "sdf_live_update", text="Live Update", icon='RENDER_STILL')
        row.prop(scene, "sdf_show_result", text="", icon='MESH_DATA')
        row.prop(scene, "sdf_show_primitives", text="", icon='SHADING_WIRE' if scene.sdf_show_primitives else 'SHADING_BBOX')
        row.prop(scene, "sdf_show_preview", text="", icon='GHOST_ENABLED' if scene.sdf_show_preview else 'GHOST_DISABLED')
        
        layout.label(text="GPU: Ready", icon='NODE_COMPOSITING')

        output_obj = None
        for o in scene.objects:
            if getattr(o, "sdf_props", None) and o.sdf_props.is_output:
                output_obj = o
                break

        if not output_obj:
            layout.separator()
            row = layout.row()
            row.scale_y = 1.5
            row.operator("sdf.make_output", text="New SDF Workspace", icon='FILE_NEW')
            self._draw_all_clear(layout, scene)
            return

        m_props = output_obj.sdf_props

        # SECTION 1: Output & Quality
        box = layout.box()
        box.label(text="Output & Quality", icon='MOD_MESHDEFORM')
        
        col = box.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.2
        is_low = (m_props.resolution == m_props.res_preset_low)
        op = row.operator("sdf.set_resolution_preset", text="Low", icon='PREVIEW_RANGE', depress=is_low)
        op.mode = 'LOW'
        is_high = (m_props.resolution == m_props.res_preset_high)
        op = row.operator("sdf.set_resolution_preset", text="High", icon='RENDER_STILL', depress=is_high)
        op.mode = 'HIGH'
        
        row = col.row(align=True)
        row.prop(m_props, "res_preset_low", text="L-Val")
        row.prop(m_props, "res_preset_high", text="H-Val")
        
        row = box.row(align=True)
        row.prop(m_props, "resolution", text="Res")
        row.prop(m_props, "domain_size", text="Domain")
        row.prop(m_props, "auto_domain", text="", icon='FULLSCREEN_ENTER' if m_props.auto_domain else 'FULLSCREEN_EXIT', toggle=True)

        
        box.prop(m_props, "preview_quality", text="Preview Quality")
        
        row = box.row(align=True)
        row.label(text="Symmetry:", icon='MOD_MIRROR')
        row.prop(m_props, "sym_x", text="X", toggle=True)
        row.prop(m_props, "sym_y", text="Y", toggle=True)
        row.prop(m_props, "sym_z", text="Z", toggle=True)
        
        row = box.row(align=True)
        op = row.operator("sdf.switch_algo", text="Marching Cubes", depress=(m_props.algo_type == 'MC'))
        op.target_type = 'MC'
        op = row.operator("sdf.switch_algo", text="Dual Contouring", depress=(m_props.algo_type == 'DC'))
        op.target_type = 'DC'
        
        col_weld = box.column(align=True)
        row = col_weld.row(align=True)
        row.prop(m_props, "use_weld", text="Weld (Merge)", icon='AUTOMERGE_ON')
        if m_props.use_weld:
            row.prop(m_props, "weld_threshold", text="Scale")
        
        col_quality = box.column(align=True)
        col_quality.prop(m_props, "use_live_normals", text="Live Normals (Heavy)", icon='IPO_CONSTANT')
        col_quality.prop(m_props, "res_mode_auto_normals", text="Auto-enable Live Normals on High")
        
        # SECTION 2: Post-Process (GN)
        box = layout.box()
        box.label(text="Post-Process (Smoothing)", icon='MOD_SMOOTH')
        georem_mod = output_obj.modifiers.get("GeoRemesh_R")
        if georem_mod:
            node_group = georem_mod.node_group
            if node_group and node_group.interface:
                col = box.column(align=True)
                for item in node_group.interface.items_tree:
                    if item.in_out == 'INPUT' and item.socket_type != 'NodeSocketGeometry':
                        if item.socket_type == 'NodeSocketMenu':
                            col.prop(georem_mod, f'["{item.identifier}"]', expand=True)
                        else:
                            col.prop(georem_mod, f'["{item.identifier}"]', text=item.name)
        else:
            box.operator("sdf.setup_post_process", text="Setup Post Process", icon='ADD')

        # SECTION 3: The Stack
        box = layout.box()
        box.label(text="The Stack", icon='OUTLINER')
        row = box.row()
        row.template_list("SDF_UL_stack_list", "", m_props, "sdf_stack", m_props, "sdf_stack_index")
        col = row.column(align=True)
        op = col.operator("sdf.stack_move", icon='TRIA_UP', text="")
        op.direction = 'UP'
        op = col.operator("sdf.stack_move", icon='TRIA_DOWN', text="")
        op.direction = 'DOWN'
        col.separator()
        col.prop(m_props, "use_solo", text="", icon='SOLO_ON' if m_props.use_solo else 'SOLO_OFF')
        col.operator("sdf.stack_remove", icon='X', text="")
        col.operator("sdf.add_collection_divider", icon='COLLECTION_NEW', text="")

        # SECTION 4: Material
        box = layout.box()
        row = box.row(align=True)
        row.operator("sdf.setup_material", text="Setup Nodes", icon='NODE_SEL')
        row.operator("sdf.reset_material", text="Reset", icon='FILE_REFRESH')
        
        # SECTION 5: Finalize (Bake)
        box = layout.box()
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("sdf.update_normals", text="Fix Normals", icon='MOD_SMOOTH')
        row.operator("sdf.generate_mesh", text="Force Update", icon='FILE_REFRESH')
        row.operator("sdf.finalize", text="Finalize (Bake)", icon='CHECKBOX_HLT')

        # --- Primitive Settings ---
        layout.separator()
        obj = context.active_object
        if obj and getattr(obj, "sdf_props", None) and not obj.sdf_props.is_output:
            props = obj.sdf_props
            active_stack_item = None
            if output_obj:
                stack = output_obj.sdf_props.sdf_stack
                idx = output_obj.sdf_props.sdf_stack_index
                if 0 <= idx < len(stack):
                    active_stack_item = stack[idx]
            
            if active_stack_item and active_stack_item.item_type == 'COLLECTION':
                box = layout.box()
                box.label(text=f"Group Settings: {active_stack_item.name_override}", icon='FILE_FOLDER')
                box.prop(active_stack_item, "name_override", text="Name")
                box.prop(active_stack_item, "start_new_group", text="Break Parent (Start New Group)")
                
                empty_props = obj.sdf_props
                col_place = box.column(align=True)
                col_place.label(text="Group Layout:", icon='MOD_ARRAY')
                row = col_place.row(align=True)
                row.prop(empty_props, "layout_use_mirror", text="Mirror", toggle=True)
                row.prop(empty_props, "layout_use_radial", text="Radial", toggle=True)
                row.prop(empty_props, "layout_use_spiral", text="Spiral", toggle=True)
                row.prop(empty_props, "layout_use_grid", text="Grid", toggle=True)
                row.prop(empty_props, "layout_use_jitter", text="Jitter", toggle=True)
                
                if empty_props.layout_use_mirror:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Mirror Settings", icon='MOD_MIRROR')
                    row = sub.row(align=True)
                    row.prop(empty_props, "mirror_x", text="X", toggle=True)
                    row.prop(empty_props, "mirror_y", text="Y", toggle=True)
                    row.prop(empty_props, "mirror_z", text="Z", toggle=True)
                    sub.prop(empty_props, "mirror_offset", text="Offset")

                if empty_props.layout_use_radial:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Radial Pattern", icon='MOD_ARRAY')
                    row = sub.row(align=True)
                    row.prop(empty_props, "radial_count", text="Count")
                    row.prop(empty_props, "radial_radius", text="Radius")
                    sub.row().prop(empty_props, "radial_axis", expand=True)

                if empty_props.layout_use_grid:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Grid Layout", icon='GRID')
                    row = sub.row(align=True)
                    row.prop(empty_props, "grid_count_x", text="X")
                    row.prop(empty_props, "grid_count_y", text="Y")
                    row.prop(empty_props, "grid_count_z", text="Z")
                    row = sub.row(align=True)
                    row.prop(empty_props, "grid_spacing_x", text="SpX")
                    row.prop(empty_props, "grid_spacing_y", text="SpY")
                    row.prop(empty_props, "grid_spacing_z", text="SpZ")

                if empty_props.layout_use_spiral:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Spiral Pattern", icon='MOD_CURVE')
                    row = sub.row(align=True)
                    row.prop(empty_props, "radial_count", text="Count")
                    row.prop(empty_props, "radial_radius", text="Radius")
                    sub.prop(empty_props, "spiral_pitch", text="Pitch")
                    sub.row().prop(empty_props, "radial_axis", expand=True)

                if empty_props.layout_use_radial or empty_props.layout_use_spiral:
                    col_rot = col_place.box().column(align=True)
                    col_rot.label(text="Rotation (Indiv & Accum):", icon='FILE_REFRESH')
                    row = col_rot.row(align=True)
                    row.prop(empty_props, "instance_rot_x", text="X")
                    row.prop(empty_props, "instance_rot_y", text="Y")
                    row.prop(empty_props, "instance_rot_z", text="Z")
                    row = col_rot.row(align=True)
                    row.prop(empty_props, "step_rot_x", text="X")
                    row.prop(empty_props, "step_rot_y", text="Y")
                    row.prop(empty_props, "step_rot_z", text="Z")

                if empty_props.layout_use_jitter:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Jitter Settings", icon='RNDCURVE')
                    sub.prop(empty_props, "jitter_seed", text="Seed")
                    sub.prop(empty_props, "jitter_strength", text="Strength")
            
            elif (props.is_primitive or (output_obj and output_obj.sdf_props.target_collection and obj.name in output_obj.sdf_props.target_collection.objects)) and obj.type != 'EMPTY':
                box = layout.box()
                box.label(text=f"Settings: {obj.name}", icon='MESH_UVSPHERE')
                box.prop(props, "shape_type")
                box.row().prop(props, "operation", expand=True)
                row_blend = box.row(align=True)
                row_blend.prop(props, "blend_profile", text="")
                if props.blend_profile == '4':
                    row_blend.prop(props, "chamfer_smooth", text="Factor")
                box.prop(props, "smoothness")
                row = box.row(align=True)
                row.prop(props, "noise_strength", text="Noise")
                row.prop(props, "noise_scale", text="Scale")
                box.prop(props, "color")

                scene_props = context.scene.sdf_scene_props
                col_color_mode = box.column(align=True)
                col_color_mode.prop(scene_props, "color_mode", text="Color Mode")
                if scene_props.color_mode == 'AUTO_HUE':
                    row = col_color_mode.row(align=True)
                    row.prop(scene_props, "auto_hue_saturation", text="Saturation")
                    row.prop(scene_props, "auto_hue_value", text="Value")
                    row = col_color_mode.row(align=True)
                    row.prop(scene_props, "auto_hue_step_deg", text="Hue Step (deg)")
                    row.prop(scene_props, "auto_hue_offset", text="Hue Offset (deg)")
                elif scene_props.color_mode == 'SINGLE':
                    col_color_mode.prop(scene_props, "single_color", text="Base Color")
                
                col_mat = box.column(align=True)
                col_mat.prop(props, "metallic", slider=True)
                col_mat.prop(props, "roughness", slider=True)
                
                # Dynamic Params
                shape_key = str(props.shape_type)
                if shape_key in PRIMITIVE_UI_DEFS:
                    ui_def = PRIMITIVE_UI_DEFS[shape_key]
                    if ui_def['params']:
                        sub = box.column(align=True)
                        for p_name, label, _ in ui_def['params']:
                            sub.prop(props, p_name, text=label)
                
                # --- V16: Primitive Edge Profile & Modifiers ---
                sub = box.column(align=True)
                sub.separator()
                
                row_edge = sub.row(align=True)
                row_edge.prop(props, "edge_profile", text="Edge")
                if props.edge_profile != '0':
                    row_edge.prop(props, "edge_profile_size", text="Size")
                
                if props.edge_profile == '4':
                    row_cs = sub.row(align=True)
                    row_cs.prop(props, "edge_chamfer_smooth", text="Smoothness")
                
                sub.prop(props, "shell_thickness", text="Shell (Hollow)")
                
                # Layout (Mirror, Radial, Grid)
                layout.separator()
                col_place = box.column(align=True)
                col_place.label(text="Layout (Instancing):", icon='MOD_ARRAY')
                row = col_place.row(align=True)
                row.prop(props, "layout_use_mirror", text="Mirror", toggle=True)
                row.prop(props, "layout_use_radial", text="Radial", toggle=True)
                row.prop(props, "layout_use_spiral", text="Spiral", toggle=True)
                row.prop(props, "layout_use_grid", text="Grid", toggle=True)
                row.prop(props, "layout_use_jitter", text="Jitter", toggle=True)

                # Advanced Rotation (Individual & Step)
                col_rot = box.column(align=True)
                col_rot.label(text="Rotation (Indiv & Accum):", icon='FILE_REFRESH')
                row = col_rot.row(align=True)
                row.prop(props, "instance_rot_x", text="X")
                row.prop(props, "instance_rot_y", text="Y")
                row.prop(props, "instance_rot_z", text="Z")
                row = col_rot.row(align=True)
                row.prop(props, "step_rot_x", text="X")
                row.prop(props, "step_rot_y", text="Y")
                row.prop(props, "step_rot_z", text="Z")

                if props.layout_use_mirror:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Mirror Settings", icon='MOD_MIRROR')
                    row = sub.row(align=True)
                    row.prop(props, "mirror_x", text="X", toggle=True)
                    row.prop(props, "mirror_y", text="Y", toggle=True)
                    row.prop(props, "mirror_z", text="Z", toggle=True)
                    sub.prop(props, "mirror_offset", text="Offset")

                if props.layout_use_radial:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Radial Pattern", icon='MOD_ARRAY')
                    row = sub.row(align=True)
                    row.prop(props, "radial_count", text="Count")
                    row.prop(props, "radial_radius", text="Radius")
                    sub.row().prop(props, "radial_axis", expand=True)

                if props.layout_use_grid:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Grid Layout", icon='GRID')
                    row = sub.row(align=True)
                    row.prop(props, "grid_count_x", text="X")
                    row.prop(props, "grid_count_y", text="Y")
                    row.prop(props, "grid_count_z", text="Z")
                    row = sub.row(align=True)
                    row.prop(props, "grid_spacing_x", text="SpX")
                    row.prop(props, "grid_spacing_y", text="SpY")
                    row.prop(props, "grid_spacing_z", text="SpZ")

                if props.layout_use_spiral:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Spiral Pattern", icon='MOD_CURVE')
                    row = sub.row(align=True)
                    row.prop(props, "radial_count", text="Count")
                    row.prop(props, "radial_radius", text="Radius")
                    sub.prop(props, "spiral_pitch", text="Pitch")
                    sub.row().prop(props, "radial_axis", expand=True)

                if props.layout_use_jitter:
                    sub = col_place.box().column(align=True)
                    sub.label(text="Jitter Settings", icon='RNDCURVE')
                    sub.prop(props, "jitter_seed", text="Seed")
                    sub.prop(props, "jitter_strength", text="Strength")

                # --- V15: Deform Stack ---
                layout.separator()
                col_deform = box.column(align=True)
                col_deform.label(text="Deform (Stack):", icon='MOD_SIMPLEDEFORM')
                
                row = col_deform.row()
                row.template_list("SDF_UL_deform_list", "", props, "deform_stack", props, "deform_stack_index", rows=3)
                col_btn = row.column(align=True)
                col_btn.operator("sdf.deform_add", icon='ADD', text="")
                col_btn.operator("sdf.deform_remove", icon='REMOVE', text="")
                col_btn.separator()
                op = col_btn.operator("sdf.deform_move", icon='TRIA_UP', text="")
                op.direction = 'UP'
                op = col_btn.operator("sdf.deform_move", icon='TRIA_DOWN', text="")
                op.direction = 'DOWN'
                
                if len(props.deform_stack) > 0 and props.deform_stack_index < len(props.deform_stack):
                    d_item = props.deform_stack[props.deform_stack_index]
                    sub = col_deform.box().column(align=True)
                    sub.prop(d_item, "deform_type", text="Type")
                    sub.prop(d_item, "enabled", text="Enabled")
                    
                    if d_item.deform_type == 'ELONGATE':
                        row = sub.row(align=True)
                        row.prop(d_item, "elongate_x", text="X")
                        row.prop(d_item, "elongate_y", text="Y")
                        row.prop(d_item, "elongate_z", text="Z")
                    else:
                        sub.prop(d_item, "factor", text="Angle" if d_item.deform_type in ('BEND', 'TWIST') else "Factor")
                        sub.row().prop(d_item, "axis", expand=True)
                        row = sub.row(align=True)
                        axis_val = d_item.axis
                        if axis_val == '2':  # Z
                            row.prop(d_item, "origin", index=0, text="X")
                            row.prop(d_item, "origin", index=1, text="Y")
                        elif axis_val == '1':  # Y
                            row.prop(d_item, "origin", index=2, text="Z")
                            row.prop(d_item, "origin", index=0, text="X")
                        else:  # X
                            row.prop(d_item, "origin", index=1, text="Y")
                            row.prop(d_item, "origin", index=2, text="Z")


        # --- Add New Primitives ---
        layout.separator()
        layout.label(text="Add New Primitives:")
        grid = layout.column(align=True)
        row = grid.row(align=True)
        row.operator("sdf.add_primitive", text="Sphere", icon='MESH_UVSPHERE').shape = 'sphere'
        row.operator("sdf.add_primitive", text="Box", icon='MESH_CUBE').shape = 'box'
        row.operator("sdf.add_primitive", text="R-Box", icon='MOD_BEVEL').shape = 'rounded_box'
        row = grid.row(align=True)
        row.operator("sdf.add_primitive", text="Torus", icon='MESH_TORUS').shape = 'torus'
        row.operator("sdf.add_primitive", text="Cylinder", icon='MESH_CYLINDER').shape = 'cylinder'
        row.operator("sdf.add_primitive", text="Capsule", icon='MESH_CAPSULE').shape = 'capsule'
        row = grid.row(align=True)
        row.operator("sdf.add_primitive", text="Hex", icon='MESH_CIRCLE').shape = 'hex_prism'
        row.operator("sdf.add_primitive", text="Pyramid", icon='MESH_CONE').shape = 'pyramid'
        row.operator("sdf.add_primitive", text="Taper", icon='MESH_CONE').shape = 'capped_cone'

        row = grid.row(align=True)
        row.operator("sdf.add_primitive", text="N-gon", icon='MESH_ICOSPHERE').shape = 'ngon_prism'
        row.operator("sdf.add_primitive", text="Ellipsoid", icon='META_ELLIPSOID').shape = 'ellipsoid'
        row.operator("sdf.add_primitive", text="R-Cylinder", icon='MESH_CAPSULE').shape = 'rounded_cylinder'
        row = grid.row(align=True)
        row.operator("sdf.add_primitive", text="C-Torus", icon='CURVE_BEZCIRCLE').shape = 'capped_torus'
        row.operator("sdf.add_primitive", text="Octahedron", icon='MESH_ICOSPHERE').shape = 'octahedron'
        row.operator("sdf.add_primitive", text="Cut Sphere", icon='SPHERE').shape = 'cut_sphere'

        # --- Object Utilities ---
        layout.separator()
        layout.label(text="Object Utilities:", icon='MODIFIER')
        row = layout.row(align=True)
        row.operator("sdf.toggle_display", text="Wire/Solid", icon='SHADING_WIRE')
        row.operator("sdf.move_to_sdf_collection", text="Move to SDF", icon='COLLECTION_NEW')

        # ALL CLEAR
        self._draw_all_clear(layout, scene)

    def _draw_all_clear(self, layout, scene):
        layout.separator()
        col_clear = layout.column(align=True)
        row = col_clear.row(align=True)
        row.prop(scene.sdf_scene_props, "all_clear_include_history", text="Include Baked Results")
        row.operator("sdf.all_clear", text="All Clear", icon='TRASH')
