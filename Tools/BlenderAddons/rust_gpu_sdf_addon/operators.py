import bpy
import os
import colorsys
from .engine import update_sdf_mesh, trigger_normal_update
from .constants import _PRIM_COLORS, PRIMITIVE_UI_DEFS

_prim_color_idx = 0


def _get_next_primitive_color(context):
    global _prim_color_idx

    scene_props = getattr(context.scene, "sdf_scene_props", None)
    mode = getattr(scene_props, "color_mode", "FIXED")

    if mode == 'AUTO_HUE':
        sat = scene_props.auto_hue_saturation
        val = scene_props.auto_hue_value
        step = scene_props.auto_hue_step_deg / 360.0
        offset = scene_props.auto_hue_offset / 360.0
        hue = (offset + (_prim_color_idx * step)) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        c = (r, g, b, 1.0)
    elif mode == 'SINGLE':
        base = scene_props.single_color
        c = (base[0], base[1], base[2], 1.0)
    else:
        c = _PRIM_COLORS[_prim_color_idx % len(_PRIM_COLORS)]

    _prim_color_idx += 1
    return c

def get_or_create_collection(name, parent_col=None):
    """指定した名前のコレクションを取得または作成し、親にリンクする"""
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
    
    if parent_col:
        if name not in parent_col.children:
            parent_col.children.link(col)
    else:
        # 親が指定されない場合はScene Collectionにリンク
        if name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(col)
    return col

def get_sdf_output_obj(context):
    """アクティブオブジェクトまたはシーン内の最初の出力オブジェクトを返す"""
    active = context.active_object
    if active and getattr(active, "sdf_props", None) and active.sdf_props.is_output:
        return active
    for obj in context.scene.objects:
        p = getattr(obj, "sdf_props", None)
        if p and p.is_output:
            return obj
    return None

class SDF_OT_add_primitive(bpy.types.Operator):
    bl_idname = "sdf.add_primitive"
    bl_label = "Add SDF Primitive"
    bl_description = "Adds an SDF primitive (automatically creates a workspace if none exists)"
    shape: bpy.props.StringProperty()

    def execute(self, context):
        global _prim_color_idx
        col_name = "SDF_Collection"
        col = get_or_create_collection(col_name)

        has_output = any(
            getattr(o, 'sdf_props', None) and o.sdf_props.is_output
            for o in context.scene.objects
        )
        if not has_output:
            mesh = bpy.data.meshes.new("SDF_Result_Mesh")
            out_obj = bpy.data.objects.new("SDF_Result", mesh)
            context.scene.collection.objects.link(out_obj)
            out_obj.sdf_props.is_output = True
            out_obj.sdf_props.target_collection = col

        if self.shape == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0)
        elif self.shape == 'box' or self.shape == 'rounded_box':
            bpy.ops.mesh.primitive_cube_add(size=2.0)
        elif self.shape == 'torus':
            bpy.ops.mesh.primitive_torus_add(major_radius=0.65, minor_radius=0.35)
        elif self.shape == 'cylinder' or self.shape == 'capsule':
            bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0)
        elif self.shape == 'hex_prism':
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1.0, depth=2.0)
        elif self.shape == 'pyramid':
            bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.0, depth=2.0)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0)

        obj = context.active_object
        obj.sdf_props.is_primitive = True
        obj.sdf_props.shape_type = self.shape
        obj.display_type = 'WIRE' if context.scene.sdf_show_primitives else 'BOUNDS'
        
        # V13: 初期値の適用
        if self.shape in PRIMITIVE_UI_DEFS:
            ui_def = PRIMITIVE_UI_DEFS[self.shape]
            for i, (_, _, default_val) in enumerate(ui_def['params']):
                prop_name = f"p{i+1}"
                if hasattr(obj.sdf_props, prop_name):
                    setattr(obj.sdf_props, prop_name, default_val)

        c = _get_next_primitive_color(context)
        obj.color = c
        obj.sdf_props.color = c[:3]

        if obj.name not in col.objects:
            col.objects.link(obj)
        for c_col in obj.users_collection:
            if c_col != col:
                c_col.objects.unlink(obj)

        for o in context.scene.objects:
            if getattr(o, 'sdf_props', None) and o.sdf_props.is_output:
                update_sdf_mesh(o)
        return {'FINISHED'}

class SDF_OT_toggle_display(bpy.types.Operator):
    bl_idname = "sdf.toggle_display"
    bl_label = "Toggle Wire/Solid"
    bl_description = "Toggle display mode of selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for obj in context.selected_objects:
            if obj.display_type == 'WIRE':
                obj.display_type = 'TEXTURED'
            else:
                obj.display_type = 'WIRE'
        return {'FINISHED'}

class SDF_OT_move_to_sdf_collection(bpy.types.Operator):
    bl_idname = "sdf.move_to_sdf_collection"
    bl_label = "Move to SDF Collection"
    bl_description = "Move selected objects to the SDF collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        target_col = None
        for o in context.scene.objects:
            p = getattr(o, "sdf_props", None)
            if p and p.is_output and p.target_collection:
                target_col = p.target_collection
                break
        
        if not target_col:
            target_col = bpy.data.collections.get("SDF_Collection")
            
        if not target_col:
            self.report({'WARNING'}, "SDF Collection not found")
            return {'CANCELLED'}
            
        for obj in context.selected_objects:
            if obj.name not in target_col.objects:
                for col in obj.users_collection:
                    col.objects.unlink(obj)
                target_col.objects.link(obj)
            
            obj.sdf_props.is_primitive = True
            obj.display_type = 'WIRE'
            
            name_lower = obj.name.lower()
            if 'box' in name_lower or 'cube' in name_lower: obj.sdf_props.shape_type = 'box'
            elif 'torus' in name_lower: obj.sdf_props.shape_type = 'torus'
            elif 'cylinder' in name_lower: obj.sdf_props.shape_type = 'cylinder'
            else: obj.sdf_props.shape_type = 'sphere'
                
        return {'FINISHED'}

class SDF_OT_duplicate_collection(bpy.types.Operator):
    bl_idname = "sdf.duplicate_collection"
    bl_label = "Duplicate Collection"
    bl_description = "Duplicate this collection and its contained primitives"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return get_sdf_output_obj(context) is not None

    def execute(self, context):
        from .engine import update_sdf_mesh, sync_sdf_stack
        from . import engine
        
        # 複製処理中は一切の自動同期・Depsgraph評価を遮断する
        engine._duplicate_cooldown = True
        
        out_obj = get_sdf_output_obj(context)
        if not out_obj:
            engine._duplicate_cooldown = False
            return {'CANCELLED'}
            
        stack = out_obj.sdf_props.sdf_stack
        if self.index < 0 or self.index >= len(stack):
            engine._duplicate_cooldown = False
            return {'CANCELLED'}
            
        target_item = stack[self.index]
        if target_item.item_type != 'COLLECTION':
            engine._duplicate_cooldown = False
            return {'CANCELLED'}
            
        target_col = out_obj.sdf_props.target_collection
        if not target_col:
            engine._duplicate_cooldown = False
            return {'CANCELLED'}
            
        # 複製対象の収集（下から上へ）
        # ターゲットのEmpty（フォルダ）
        objs_to_duplicate = []
        target_empty = target_item.empty_ptr
        if not target_empty and target_item.obj_name:
            target_empty = target_col.objects.get(target_item.obj_name)
        if target_empty:
            objs_to_duplicate.append(target_empty)
            
        # 上にあるプリミティブを次のコレクション区切りまで収集
        for i in range(self.index - 1, -1, -1):
            item = stack[i]
            
            # アイテムが指すオブジェクトを確実に取得
            o = item.object_ptr
            if not o and item.obj_name:
                o = target_col.objects.get(item.obj_name)
                
            # 万が一item_typeがプリミティブになっていても実体がEMPTYならコレクション区切りとして扱う
            if o and o.type == 'EMPTY':
                break
            elif item.item_type == 'COLLECTION':
                break
                
            if o:
                objs_to_duplicate.append(o)
            elif item.empty_ptr:
                objs_to_duplicate.append(item.empty_ptr)
                
        if not objs_to_duplicate:
            engine._duplicate_cooldown = False
            return {'CANCELLED'}
            
        bpy.ops.object.select_all(action='DESELECT')
        
        # 逆順にして上からの順番に戻す
        objs_to_duplicate.reverse()
        seen = set()
        unique_objs = []
        for obj in objs_to_duplicate:
            if obj not in seen:
                seen.add(obj)
                unique_objs.append(obj)
        
        # 複製とリンク、およびスタックへの直接追加
        new_active_obj = None
        for idx, obj in enumerate(unique_objs):
            new_obj = obj.copy()
            if obj.data:
                new_obj.data = obj.data.copy()
            target_col.objects.link(new_obj)
            
            # APIベースで直接スタックに追加（sync_sdf_stackのポインタ喪失や並び替えバグを排除）
            new_item = stack.add()
            new_item.object_ptr = new_obj
            new_item.obj_name = new_obj.name
            
            # カスタムプロパティ（レイアウト設定等）はobj.copy()でコピー済み
            if new_obj.type == 'EMPTY':
                new_item.item_type = 'COLLECTION'
                new_item.empty_ptr = new_obj
                new_item.name_override = new_obj.name
                new_active_obj = new_obj
                # エンプティのみ選択状態にする
                new_obj.select_set(True)
            else:
                new_item.item_type = 'PRIMITIVE'
                # プリミティブは選択状態にしない
                new_obj.select_set(False)
                
        # フォルダがあればアクティブにする（すぐにGキーで移動できるようにするため）
        if new_active_obj:
            context.view_layer.objects.active = new_active_obj
            
        # 複製完了後、1フレーム遅延してメッシュ更新と親子関係の再構築を行う
        def delayed_sync():
            if out_obj:
                # 親子関係の再同期（これをしないとGキーで移動した時にプリミティブがついてこない）
                engine.sync_sdf_parents(out_obj)
                
                # 既にスタックに直接追加したので、sync_sdf_stackは不要だが、念のため呼び出す
                engine.sync_sdf_stack(out_obj)
                engine.update_sdf_mesh(out_obj)
            engine._duplicate_cooldown = False
            return None
            
        bpy.app.timers.register(delayed_sync, first_interval=0.05)
        
        return {'FINISHED'}


class SDF_OT_bake_mesh(bpy.types.Operator):
    bl_idname = "sdf.bake_mesh"
    bl_label = "Bake to Static Mesh"
    bl_description = "Convert current SDF shape into an independent static mesh"
    
    @classmethod
    def poll(cls, context):
        return get_sdf_output_obj(context) is not None

    def execute(self, context):
        source_obj = get_sdf_output_obj(context)
        if not source_obj: return {'CANCELLED'}
        new_mesh = source_obj.data.copy()
        new_obj = bpy.data.objects.new(name=f"{source_obj.name}_Baked", object_data=new_mesh)
        new_obj.matrix_world = source_obj.matrix_world
        new_obj.sdf_props.is_output = False
        new_obj.sdf_props.is_primitive = False
        context.collection.objects.link(new_obj)
        source_obj.select_set(False)
        new_obj.select_set(True)
        context.view_layer.objects.active = new_obj
        self.report({'INFO'}, f"Baked to {new_obj.name}")
        return {'FINISHED'}

def setup_material_nodes(mat):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = (400, 0)
    
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.location = (0, 0)
    
    node_attr_col = nodes.new(type='ShaderNodeAttribute')
    node_attr_col.attribute_name = "Color"
    node_attr_col.location = (-300, 100)
    links.new(node_attr_col.outputs['Color'], node_principled.inputs['Base Color'])
    
    node_attr_met = nodes.new(type='ShaderNodeAttribute')
    node_attr_met.attribute_name = "Metallic"
    node_attr_met.location = (-300, -100)
    links.new(node_attr_met.outputs['Fac'], node_principled.inputs['Metallic'])
    
    node_attr_rou = nodes.new(type='ShaderNodeAttribute')
    node_attr_rou.attribute_name = "Roughness"
    node_attr_rou.location = (-300, -300)
    links.new(node_attr_rou.outputs['Fac'], node_principled.inputs['Roughness'])
    
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

class SDF_OT_setup_material(bpy.types.Operator):
    bl_idname = "sdf.setup_material"
    bl_label = "Setup Color Material"
    bl_description = "Generate and apply material for vertex colors"
    
    def execute(self, context):
        obj = get_sdf_output_obj(context)
        if not obj:
            self.report({'WARNING'}, "Output object not found")
            return {'CANCELLED'}
        
        mat_name = f"SDF_Material_{obj.name}"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            setup_material_nodes(mat)
            
        if not any(slot.material == mat for slot in obj.material_slots):
            obj.data.materials.append(mat)
        return {'FINISHED'}

class SDF_OT_reset_material(bpy.types.Operator):
    bl_idname = "sdf.reset_material"
    bl_label = "Reset Shader Nodes"
    bl_description = "Reset shader nodes to default vertex color setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_sdf_output_obj(context)
        if not obj:
            self.report({'WARNING'}, "Output object not found")
            return {'CANCELLED'}
            
        mat_name = f"SDF_Material_{obj.name}"
        mat = bpy.data.materials.get(mat_name)
        if not mat:
            bpy.ops.sdf.setup_material()
            return {'FINISHED'}
        
        # Clear existing nodes and rebuild
        setup_material_nodes(mat)
        
        self.report({'INFO'}, "Shader nodes reset to default.")
        return {'FINISHED'}

class SDF_OT_update_normals(bpy.types.Operator):
    bl_idname = "sdf.update_normals"
    bl_label = "Update Normals"
    bl_description = "Calculate and apply high-quality normals"
    
    def execute(self, context):
        obj = get_sdf_output_obj(context)
        if obj:
            trigger_normal_update(obj)
            self.report({'INFO'}, "Normals update triggered")
        return {'FINISHED'}

class SDF_OT_generate_mesh(bpy.types.Operator):
    bl_idname = "sdf.generate_mesh"
    bl_label = "Generate SDF Mesh"
    def execute(self, context):
        for obj in context.scene.objects:
            if obj.sdf_props.is_output:
                if obj.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
                update_sdf_mesh(obj)
        return {'FINISHED'}

class SDF_OT_add_selected(bpy.types.Operator):
    bl_idname = "sdf.add_selected"
    bl_label = "Add Selected to SDF"
    bl_description = "Add the active object to the SDF calculation stack"
    @classmethod
    def poll(cls, context):
        return context.active_object and not context.active_object.sdf_props.is_output
    def execute(self, context):
        obj = context.active_object
        col_name = "SDF_Collection"
        col = bpy.data.collections.get(col_name) or bpy.data.collections.new(col_name)
        if col_name not in context.scene.collection.children:
            context.scene.collection.children.link(col)
        if obj.name not in col.objects:
            col.objects.link(obj)
        obj.sdf_props.is_primitive = True
        obj.display_type = 'WIRE'
        for o in context.scene.objects:
            if o.sdf_props.is_output:
                update_sdf_mesh(o)
        return {'FINISHED'}

class SDF_OT_make_output(bpy.types.Operator):
    bl_idname = "sdf.make_output"
    bl_label = "New SDF Workspace"
    
    def execute(self, context):
        scene = context.scene
        
        # 1. Check existing work (check if archiving is needed)
        active_col = bpy.data.collections.get("SDF_Collection")
        current_result = get_sdf_output_obj(context)
        
        # Archive if parts exist (and not baked)
        if (active_col and active_col.objects) or current_result:
            history_root = get_or_create_collection("SDF_History")
            count = 1
            while bpy.data.collections.get(f"Iteration_{count:03}"):
                count += 1
            iter_col = get_or_create_collection(f"Iteration_{count:03}", history_root)
            
            # Archive primitives
            if active_col and active_col.objects:
                used_col = get_or_create_collection(f"SDF_Used_{count:03}", iter_col)
                for obj in list(active_col.objects):
                    active_col.objects.unlink(obj)
                    used_col.objects.link(obj)
                    obj.hide_viewport = obj.hide_render = True
            
            # Archive result objects
            if current_result:
                res_col = get_or_create_collection("SDF_Results", history_root)
                if current_result.name in scene.collection.objects:
                    scene.collection.objects.unlink(current_result)
                if current_result.name not in res_col.objects:
                    res_col.objects.link(current_result)
                current_result.name = f"SDF_Result_{count:03}_Unbaked"
                current_result.sdf_props.is_output = False
            
            iter_col.hide_viewport = iter_col.hide_render = True

        # 2. Create fresh workspace
        col_name = "SDF_Collection"
        col = get_or_create_collection(col_name)
        
        mesh = bpy.data.meshes.new("SDF_Result_Mesh")
        out_obj = bpy.data.objects.new("SDF_Result", mesh)
        scene.collection.objects.link(out_obj)
        
        out_obj.sdf_props.is_output = True
        out_obj.sdf_props.target_collection = col
        context.view_layer.objects.active = out_obj
        
        # Resume live update
        scene.sdf_live_update = True
        
        update_sdf_mesh(out_obj)
        self.report({'INFO'}, "New Workspace created. Past work archived to SDF_History.")
        return {'FINISHED'}

# --- V7: Stack manipulation operators ---
class SDF_OT_stack_move(bpy.types.Operator):
    bl_idname = "sdf.stack_move"
    bl_label = "Move Stack Item"
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        master = None
        for o in context.scene.objects:
            if o.sdf_props.is_output:
                master = o
                break
        if not master: return {'CANCELLED'}
        
        props = master.sdf_props
        idx = props.sdf_stack_index
        size = len(props.sdf_stack)
        
        new_idx = idx - 1 if self.direction == 'UP' else idx + 1
        if 0 <= new_idx < size:
            props.sdf_stack.move(idx, new_idx)
            props.sdf_stack_index = new_idx
            update_sdf_mesh(master)
        return {'FINISHED'}

class SDF_OT_stack_remove(bpy.types.Operator):
    bl_idname = "sdf.stack_remove"
    bl_label = "Remove Stack Item"
    def execute(self, context):
        master = None
        for o in context.scene.objects:
            if o.sdf_props.is_output:
                master = o
                break
        if not master: return {'CANCELLED'}
        
        props = master.sdf_props
        if len(props.sdf_stack) > 0:
            item = props.sdf_stack[props.sdf_stack_index]
            if item.object_ptr:
                if item.item_type == 'COLLECTION':
                    empty_obj = item.empty_ptr
                    if empty_obj:
                        # 解除
                        for child in list(empty_obj.children):
                            child.parent = None
                        # オブジェクト削除
                        bpy.data.objects.remove(empty_obj, do_unlink=True)
                else:
                    col = props.target_collection
                    if col and item.object_ptr.name in col.objects:
                        col.objects.unlink(item.object_ptr)
            
            props.sdf_stack.remove(props.sdf_stack_index)
            props.sdf_stack_index = max(0, props.sdf_stack_index - 1)
            
            # 再同期
            try:
                from .engine import sync_sdf_parents
                sync_sdf_parents(master)
            except Exception as e:
                print(f"Parent sync failed on remove: {e}")
                
            update_sdf_mesh(master)
        return {'FINISHED'}


class SDF_OT_select_stack_obj(bpy.types.Operator):
    bl_idname = "sdf.select_stack_obj"
    bl_label = "Select SDF Object"
    obj_name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()

    def execute(self, context):
        # Update master object index
        master = get_sdf_output_obj(context)
        if master:
            master.sdf_props.sdf_stack_index = self.index

        obj = bpy.data.objects.get(self.obj_name)
        if obj:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
        return {'FINISHED'}

class SDF_OT_setup_post_process(bpy.types.Operator):
    bl_idname = "sdf.setup_post_process"
    bl_label = "Setup Post Process (GN)"
    bl_description = "Append GeoRemesh node group and apply to output object"

    def execute(self, context):
        obj = get_sdf_output_obj(context)
        if not obj:
            self.report({'WARNING'}, "Output object not found")
            return {'CANCELLED'}

        # Get asset path
        addon_dir = os.path.dirname(os.path.realpath(__file__))
        blend_path = os.path.join(addon_dir, "assets", "nodes.blend")

        if not os.path.exists(blend_path):
            self.report({'ERROR'}, f"Asset file not found: {blend_path}")
            return {'CANCELLED'}

        # Append NodeGroup
        node_group_name = "GeoRemesh_R"
        if node_group_name not in bpy.data.node_groups:
            with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
                if node_group_name in data_from.node_groups:
                    data_to.node_groups.append(node_group_name)
                else:
                    self.report({'ERROR'}, f"Node group {node_group_name} not found")
                    return {'CANCELLED'}

        # Add modifier
        mod_name = "GeoRemesh_R"
        mod = obj.modifiers.get(mod_name)
        if not mod:
            mod = obj.modifiers.new(name=mod_name, type='NODES')
        
        mod.node_group = bpy.data.node_groups.get(node_group_name)
        
        return {'FINISHED'}

class SDF_OT_finalize(bpy.types.Operator):
    bl_idname = "sdf.finalize"
    bl_label = "Finalize (Bake All)"
    bl_description = "Applies all SDF operations and modifiers, converting them to a standard mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_sdf_output_obj(context)
        if not obj:
            self.report({'WARNING'}, "Output object not found")
            return {'CANCELLED'}

        # 1. 歴史フォルダの確保
        history_root = get_or_create_collection("SDF_History")
        results_col = get_or_create_collection("SDF_Results", history_root)
        
        # 2. 原型の複製（バックアップ）
        count = 1
        while bpy.data.objects.get(f"SDF_Result_{count:03}_Backup"):
            count += 1
        
        backup_obj = obj.copy()
        backup_obj.data = obj.data.copy()
        backup_obj.name = f"SDF_Result_{count:03}_Backup"
        
        backup_sub = get_or_create_collection("SDF_Backups", history_root)
        backup_sub.objects.link(backup_obj)
        backup_obj.sdf_props.is_output = False
        backup_obj.hide_viewport = backup_obj.hide_render = True
        
        # 3. ライブ更新を一時停止
        context.scene.sdf_live_update = False
        
        # 4. 全モディファイアーを適用して確定
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to apply modifier {mod.name}: {e}")

        # 5. SDFプロパティのクリーンアップ（通常のメッシュ化）
        obj.sdf_props.is_output = False
        obj.sdf_props.sdf_stack.clear()
        
        # 成果物のリネームと移動
        obj.name = f"SDF_Result_{count:03}"
        if obj.name in context.scene.collection.objects:
            context.scene.collection.objects.unlink(obj)
        if obj.name not in results_col.objects:
            results_col.objects.link(obj)

        # 6. 【整理整頓】使用したプリミティブを履歴に退避し、作業場を空にする
        prim_col = obj.sdf_props.target_collection
        if prim_col:
            used_col = get_or_create_collection(f"SDF_Used_{count:03}", history_root)
            for p_obj in list(prim_col.objects):
                prim_col.objects.unlink(p_obj)
                used_col.objects.link(p_obj)
                p_obj.hide_viewport = p_obj.hide_render = True
            
            # 使用済みコレクションも一応隠しておく
            used_col.hide_viewport = used_col.hide_render = True
            
            # メインの SDF_Collection は可視のまま空っぽにする
            prim_col.hide_viewport = False 
        
        self.report({'INFO'}, f"Mesh finalized and moved to {results_col.name}.")
        return {'FINISHED'}

class SDF_OT_set_resolution_preset(bpy.types.Operator):
    bl_idname = "sdf.set_resolution_preset"
    bl_label = "Set Resolution Preset"
    bl_description = "Switches the resolution to the specified preset value"
    
    mode: bpy.props.EnumProperty(items=[('LOW', "Low", ""), ('HIGH', "High", "")])

    def execute(self, context):
        obj = get_sdf_output_obj(context)
        if not obj: return {'CANCELLED'}
        
        props = obj.sdf_props
        if self.mode == 'LOW':
            props.resolution = props.res_preset_low
            props.use_live_normals = False
        else:
            props.resolution = props.res_preset_high
            if props.res_mode_auto_normals:
                props.use_live_normals = True
        
        update_sdf_mesh(obj)
        return {'FINISHED'}

class SDF_OT_all_clear(bpy.types.Operator):
    bl_idname = "sdf.all_clear"
    bl_label = "All Clear"
    bl_description = "Delete all SDF-related objects and collections"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        props = scene.sdf_scene_props
        include_results = props.all_clear_include_history
        
        to_delete = []
        for obj in list(scene.objects):
            p = getattr(obj, "sdf_props", None)
            if p and (p.is_output or p.is_primitive):
                to_delete.append(obj)
                continue
            
            is_sdf_history_obj = any(x in obj.name for x in ["SDF_Result_", "SDF_Backup"])
            if is_sdf_history_obj:
                is_baked_result = "SDF_Result_" in obj.name and "_Backup" not in obj.name and "_Unbaked" not in obj.name
                if include_results or not is_baked_result:
                    to_delete.append(obj)

        if to_delete:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in to_delete:
                try: obj.select_set(True)
                except: pass
            bpy.ops.object.delete()

        if include_results:
            cols_to_remove = ["SDF_Collection", "SDF_History"]
            for name in cols_to_remove:
                col = bpy.data.collections.get(name)
                if col: self._recursive_delete_col(col)
        else:
            active_col = bpy.data.collections.get("SDF_Collection")
            if active_col:
                for obj in list(active_col.objects): bpy.data.objects.remove(obj, do_unlink=True)
            
            history_root = bpy.data.collections.get("SDF_History")
            if history_root:
                for sub in list(history_root.children):
                    if "SDF_Results" not in sub.name: self._recursive_delete_col(sub)
                
                results_col = bpy.data.collections.get("SDF_Results")
                if results_col:
                    for obj in list(results_col.objects):
                        if "_Unbaked" in obj.name: bpy.data.objects.remove(obj, do_unlink=True)

        self.report({'INFO'}, "SDF Workspace cleaned up.")
        return {'FINISHED'}

    def _recursive_delete_col(self, col):
        for child in list(col.children): self._recursive_delete_col(child)
        for obj in list(col.objects): bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(col)

# --- V15: Deform Stack Operators ---
class SDF_OT_deform_add(bpy.types.Operator):
    bl_idname = "sdf.deform_add"
    bl_label = "Add Deform"
    bl_description = "Add a new item to the deform stack (max 2)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or not getattr(obj, "sdf_props", None):
            return {'CANCELLED'}
        props = obj.sdf_props
        if len(props.deform_stack) >= 2:
            self.report({'WARNING'}, "Up to 2 deforms are allowed (lightweight version)")
            return {'CANCELLED'}
        item = props.deform_stack.add()
        props.deform_stack_index = len(props.deform_stack) - 1
        update_sdf_mesh(get_sdf_output_obj(context))
        return {'FINISHED'}

class SDF_OT_deform_remove(bpy.types.Operator):
    bl_idname = "sdf.deform_remove"
    bl_label = "Remove Deform"
    bl_description = "Remove the selected deform from the stack"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or not getattr(obj, "sdf_props", None):
            return {'CANCELLED'}
        props = obj.sdf_props
        if len(props.deform_stack) > 0:
            props.deform_stack.remove(props.deform_stack_index)
            props.deform_stack_index = max(0, props.deform_stack_index - 1)
            update_sdf_mesh(get_sdf_output_obj(context))
        return {'FINISHED'}

class SDF_OT_deform_move(bpy.types.Operator):
    bl_idname = "sdf.deform_move"
    bl_label = "Move Deform"
    bl_description = "Reorder the deforms in the stack"
    bl_options = {'REGISTER', 'UNDO'}
    direction: bpy.props.EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")])

    def execute(self, context):
        obj = context.active_object
        if not obj or not getattr(obj, "sdf_props", None):
            return {'CANCELLED'}
        props = obj.sdf_props
        idx = props.deform_stack_index
        size = len(props.deform_stack)
        new_idx = idx - 1 if self.direction == 'UP' else idx + 1
        if 0 <= new_idx < size:
            props.deform_stack.move(idx, new_idx)
            props.deform_stack_index = new_idx
            update_sdf_mesh(get_sdf_output_obj(context))
        return {'FINISHED'}


class SDF_OT_switch_algo(bpy.types.Operator):
    bl_idname = "sdf.switch_algo"
    bl_label = "Switch Algorithm"
    bl_description = "Switch between Marching Cubes and Dual Contouring"
    bl_options = {'REGISTER', 'UNDO'}
    
    target_type: bpy.props.EnumProperty(
        items=[('MC', "Marching Cubes", ""), ('DC', "Dual Contouring", "")],
        name="Target Algorithm"
    )

    def execute(self, context):
        scene = context.scene
        s_props = scene.sdf_scene_props
        output_obj = get_sdf_output_obj(context)
        if not output_obj:
            return {'CANCELLED'}
        
        m_props = output_obj.sdf_props
        
        if self.target_type == 'DC':
            # DC未コンパイルの場合はRust側を叩いてコンパイルを強制
            if not s_props.is_dc_compiled:
                self.report({'INFO'}, "Dual Contouring Pipelines are compiling... please wait.")
                # generate_mesh_gpu(または内部のensure_ready)でDCフラグを立てて実行するとコンパイルが走る
                # ここでは単にフラグを切り替えるだけで、次の描画時に Rust 側で ensure_dc_ready() が呼ばれる
                s_props.is_dc_compiled = True
            
        m_props.algo_type = self.target_type
        update_sdf_mesh(output_obj)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene
        s_props = scene.sdf_scene_props
        
        if self.target_type == 'DC' and not s_props.is_dc_compiled:
            return context.window_manager.invoke_props_dialog(self, width=400)
        
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.label(text="[Experimental] Switch to Dual Contouring", icon='ERROR')
        col.separator()
        col.label(text="- Compilation takes approx. 65 seconds only on the first run")
        col.label(text="- Blender will temporarily become unresponsive during this time")
        col.label(text="- Once complete, it is cached and can be switched instantly")
        col.separator()
        col.label(text="Are you sure you want to proceed?")

class SDF_OT_add_collection_divider(bpy.types.Operator):
    bl_idname = "sdf.add_collection_divider"
    bl_label = "Add Collection Divider"
    bl_description = "Add a collection divider item to group objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        master = get_sdf_output_obj(context)
        if not master:
            self.report({'WARNING'}, "Workspace output object not found")
            return {'CANCELLED'}
            
        props = master.sdf_props
        
        # 1. 新しいEmptyオブジェクトを作成
        empty_obj = bpy.data.objects.new("SDF_Group_Empty", None)
        empty_obj.empty_display_size = 1.0
        empty_obj.empty_display_type = 'PLAIN_AXES'
        
        col = props.target_collection
        if not col:
            col = bpy.data.collections.get("SDF_Collection")
        if col:
            col.objects.link(empty_obj)
            
        # 親Emptyのプロパティ設定
        empty_obj.sdf_props.is_primitive = False
        empty_obj.sdf_props.is_output = False
        
        # 2. スタックに仕切りアイテムを追加
        idx = props.sdf_stack_index
        item = props.sdf_stack.add()
        item.item_type = 'COLLECTION'
        item.object_ptr = empty_obj
        item.empty_ptr = empty_obj
        item.name_override = f"Collection {len(props.sdf_stack)}"
        
        # 選択位置(idx + 1)に移動
        stack_size = len(props.sdf_stack)
        if stack_size > 1:
            target_idx = min(idx + 1, stack_size - 1)
            props.sdf_stack.move(stack_size - 1, target_idx)
            props.sdf_stack_index = target_idx
        else:
            props.sdf_stack_index = 0
            
        # 親子関係の再同期
        try:
            from .engine import sync_sdf_parents
            sync_sdf_parents(master)
        except Exception as e:
            print(f"Parent sync failed on add: {e}")
        
        update_sdf_mesh(master)
        
        # ビューポート上でEmptyを選択
        bpy.ops.object.select_all(action='DESELECT')
        empty_obj.select_set(True)
        context.view_layer.objects.active = empty_obj
        
        return {'FINISHED'}

