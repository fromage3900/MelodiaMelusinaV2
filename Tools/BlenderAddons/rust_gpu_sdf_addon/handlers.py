import bpy
import gpu
import mathutils
import math
from bpy.app.handlers import persistent
from gpu_extras.batch import batch_for_shader
from .shader import get_shader
from .engine import update_sdf_mesh, sync_sdf_stack, get_layout_matrices
from .constants import _SHAPE_MAP, _fsq_coords, _fsq_indices

_batch = None

def _get_shape_extent(p_props):
    """プリミティブのシェイプ半径を計算する（ドメイン計算用）"""
    if not p_props or not p_props.is_primitive:
        return getattr(p_props, "radius", 1.0) if p_props else 1.0
    shape = p_props.shape_type
    if shape == 'torus': return p_props.p1 + p_props.p2
    elif shape in ('cylinder', 'capsule', 'hex_prism'): return max(p_props.p1, p_props.p2)
    elif shape == 'capped_cone': return max(p_props.p1, p_props.p2, p_props.p3)
    elif shape == 'pyramid': return max(p_props.p1, p_props.p2)
    elif shape == 'ngon_prism': return max(p_props.p1, p_props.p3)
    elif shape == 'rounded_box': return max(p_props.radius, 1.0 + p_props.p1)
    elif shape == 'ellipsoid': return max(p_props.p1, p_props.p2, p_props.p3)
    elif shape == 'rounded_cylinder': return max(p_props.p1, p_props.p3 + p_props.p2)
    elif shape == 'capped_torus': return p_props.p1 + p_props.p2
    elif shape == 'octahedron': return p_props.p1
    elif shape == 'cut_sphere': return p_props.radius
    else: return p_props.radius

def _get_layout_r(p_props):
    """レイアウト展開による追加半径を計算する"""
    layout_r = 0.0
    if not p_props: return layout_r
    if p_props.layout_use_mirror:
        layout_r = max(layout_r, abs(p_props.mirror_offset))
    if p_props.layout_use_radial or p_props.layout_use_spiral:
        layout_r = max(layout_r, abs(p_props.radial_radius))
    if p_props.layout_use_grid:
        gx = (p_props.grid_count_x - 1) * p_props.grid_spacing_x
        gy = (p_props.grid_count_y - 1) * p_props.grid_spacing_y
        gz = (p_props.grid_count_z - 1) * p_props.grid_spacing_z
        layout_r = max(layout_r, math.sqrt(gx * gx + gy * gy + gz * gz) * 0.5)
    if p_props.layout_use_jitter:
        layout_r = max(layout_r, abs(p_props.jitter_strength))
    return layout_r

def _compute_preview_domain_size(output_obj, o_props, inv_world_output, flat_elements):
    """展開済み要素リストからプレビュードメインサイズを計算する"""
    base_domain = o_props.domain_size * 2.0
    if not getattr(o_props, "auto_domain", False):
        return base_domain

    max_extent = 0.001
    for el in flat_elements:
        loc = el['loc']
        sc = el['scale']
        p_props = el['p_props']
        max_s = max(abs(sc.x), abs(sc.y), abs(sc.z))
        smoothness = getattr(p_props, "smoothness", 0.2) if p_props else 0.2
        noise_strength = getattr(p_props, "noise_strength", 0.0) if p_props else 0.0
        shape_extent = _get_shape_extent(p_props)
        prim_r = (max_s * shape_extent) + (smoothness + noise_strength) * max_s
        layout_r = _get_layout_r(p_props) if (p_props and p_props.is_primitive) else 0.0
        dist_from_origin = math.sqrt(loc.x * loc.x + loc.y * loc.y + loc.z * loc.z)
        max_extent = max(max_extent, dist_from_origin + layout_r + prim_r)

    auto_domain = max_extent * 2.4
    return max(base_domain, auto_domain)

def _build_prim_data_for_element(el, o_props):
    """展開済み要素辞書から64floatのテクスチャデータを構築して返す"""
    o = el['obj_orig']
    p_props = el['p_props']
    loc = el['loc']
    rot = el['rot']
    sc = el['scale']

    if p_props and p_props.is_primitive:
        shape_type = _SHAPE_MAP.get(p_props.shape_type, 0.0)
        smoothness = p_props.smoothness
        op_type = float(int(p_props.operation))
        color = list(p_props.color)
        metallic = p_props.metallic
        roughness = p_props.roughness
        noise_strength = p_props.noise_strength
        noise_scale = p_props.noise_scale
    else:
        name_lower = o.name.lower()
        if 'sphere' in name_lower: shape_type = 0.0
        elif 'box' in name_lower or 'cube' in name_lower: shape_type = 1.0
        elif 'torus' in name_lower: shape_type = 2.0
        elif 'cylinder' in name_lower: shape_type = 3.0
        else: shape_type = 0.0
        smoothness = 0.5
        op_type = 0.0
        color = [1.0, 1.0, 1.0]
        metallic = 0.0
        roughness = 0.5
        noise_strength = 0.0
        noise_scale = 5.0

    sym_loc = [abs(loc.x) if o_props.sym_x else loc.x,
               abs(loc.y) if o_props.sym_y else loc.y,
               abs(loc.z) if o_props.sym_z else loc.z]

    # V12 Phase 2: Layout Data Stacking (16-slot Packing)
    if p_props and p_props.is_primitive:
        mode_flags = 0
        if p_props.layout_use_mirror: mode_flags |= 1
        if p_props.layout_use_radial: mode_flags |= 2
        if p_props.layout_use_spiral: mode_flags |= 4
        if p_props.layout_use_grid:   mode_flags |= 8
        if p_props.layout_use_jitter: mode_flags |= 32

        mirror_mask = (1 if p_props.mirror_x else 0) | (2 if p_props.mirror_y else 0) | (4 if p_props.mirror_z else 0)
        radial_axis = int(p_props.radial_axis)
        radial_count = max(1, p_props.radial_count)

        packed1 = float(mode_flags | (mirror_mask << 8) | (radial_count << 12) | (radial_axis << 20))
        grid_packed = float(p_props.grid_count_x + 100 * p_props.grid_count_y + 10000 * p_props.grid_count_z)

        ld1 = [packed1, p_props.mirror_offset, p_props.radial_radius, p_props.spiral_pitch]
        ld2 = [p_props.jitter_seed, p_props.jitter_strength, grid_packed, p_props.grid_spacing_x]
        ld3 = [p_props.grid_spacing_y, p_props.grid_spacing_z, p_props.instance_rot_x, p_props.instance_rot_y]
        ld4 = [p_props.instance_rot_z, p_props.step_rot_x, p_props.step_rot_y, p_props.step_rot_z]

        # --- V15: Deform Stack Packing ---
        _DEFORM_TYPE_MAP = {'ELONGATE': 1, 'BEND': 2, 'TWIST': 3, 'TAPER': 4}
        packed_meta = 0
        slot_params = [[0.0]*4, [0.0]*4, [0.0]*4, [0.0]*4]
        for si, d_item in enumerate(p_props.deform_stack):
            if si >= 4: break
            if not d_item.enabled: continue
            d_type = _DEFORM_TYPE_MAP.get(d_item.deform_type, 0)
            d_axis = int(d_item.axis)
            packed_meta |= (d_type | (d_axis << 4)) << (si * 6)
            if d_item.deform_type == 'ELONGATE':
                slot_params[si] = [d_item.elongate_x, d_item.elongate_y, d_item.elongate_z, 0.0]
            else:
                slot_params[si] = [d_item.factor, d_item.origin[0], d_item.origin[1], d_item.origin[2]]

        dd1 = [float(packed_meta), slot_params[0][0], slot_params[0][1], slot_params[0][2]]
        dd2 = [slot_params[0][3], slot_params[1][0], slot_params[1][1], slot_params[1][2]]
        dd3 = [slot_params[1][3], slot_params[2][0], slot_params[2][1], slot_params[2][2]]
        dd4 = [slot_params[2][3], slot_params[3][0], slot_params[3][1], slot_params[3][2]]
        
        blend_prof = float(int(p_props.blend_profile))
        cham_smooth = p_props.chamfer_smooth
    else:
        ld1 = [0.0] * 4
        ld2 = [0.0] * 4
        ld3 = [0.0] * 4
        ld4 = [0.0] * 4
        dd1 = [0.0] * 4
        dd2 = [0.0] * 4
        dd3 = [0.0] * 4
        dd4 = [0.0] * 4
        blend_prof = 0.0
        cham_smooth = 0.0

    data = []
    # 0: center_and_shape
    data.extend([sym_loc[0], sym_loc[1], sym_loc[2], shape_type])
    # 1: rotation
    data.extend([rot.x, rot.y, rot.z, rot.w])
    # 2: size_and_op
    radius = 0.0
    size = (sc.x, sc.y, sc.z)
    extra_p = [0.0, 0.0, 0.0, 0.0]

    if p_props and p_props.is_primitive:
        radius = p_props.radius
        extra_p = [p_props.p1, p_props.p2, p_props.p3, p_props.p4]
        if p_props.shape_type == 'ngon_prism':
            extra_p[1] = float(p_props.ngon_sides)
    else:
        if shape_type == 0.0: radius = sc.x
        elif shape_type == 2.0: radius = sc.z
        elif shape_type == 3.0: radius = sc.x

    data.extend([size[0], size[1], size[2], op_type])
    # 3: params [radius, smoothness, metallic, roughness]
    data.extend([radius, smoothness, metallic, roughness])
    # 4: noise_params [str, scale, r, g]
    data.extend([noise_strength, noise_scale, color[0], color[1]])
    # 5: color_b_and_extra [b, blend_profile, chamfer_smooth, 0]
    data.extend([color[2], blend_prof, cham_smooth, 0.0])
    # 6-9: layouts
    data.extend(ld1)
    data.extend(ld2)
    data.extend(ld3)
    data.extend(ld4)
    # 10: extra_params (V13)
    data.extend(extra_p)
    # 11-14: deform_data (V15)
    data.extend(dd1)
    data.extend(dd2)
    data.extend(dd3)
    data.extend(dd4)
    # 15: modifier_params (V16)
    if p_props and p_props.is_primitive:
        data.extend([float(p_props.edge_profile), p_props.shell_thickness, p_props.edge_chamfer_smooth, p_props.edge_profile_size])
    else:
        data.extend([0.0, 0.0, 0.0, 0.0])

    return data


def _flatten_stack_for_preview(output_obj, inv_world_output):
    """engine.pyのupdate_sdf_meshと同等のロジックでスタックを走査し、
    コレクション展開を適用した要素辞書のリストを返す（Ghost Preview用）"""
    o_props = output_obj.sdf_props
    working_group = []
    flat_elements = []

    for i, item in enumerate(o_props.sdf_stack):
        if not item.enabled:
            continue

        if item.item_type == 'COLLECTION':
            empty_obj = item.empty_ptr
            if not empty_obj:
                continue

            empty_props = getattr(empty_obj, "sdf_props", None)
            if not empty_props:
                continue

            layout_mats = get_layout_matrices(empty_props)
            P = empty_obj.matrix_world
            try:
                P_inv = P.inverted()
            except:
                P_inv = mathutils.Matrix.Identity(4)

            expanded_group = []
            for element in working_group:
                C = element['matrix_world']
                L = P_inv @ C
                for M in layout_mats:
                    C_new = P @ M @ L
                    local_mat = inv_world_output @ C_new
                    loc, rot, scale = local_mat.decompose()
                    copied_el = element.copy()
                    copied_el['matrix_world'] = C_new.copy()
                    copied_el['loc'] = loc
                    copied_el['rot'] = rot
                    copied_el['scale'] = scale
                    expanded_group.append(copied_el)

            if item.start_new_group:
                flat_elements.extend(expanded_group)
                working_group = []
            else:
                working_group = expanded_group

        else:
            # プリミティブ
            obj_orig = item.object_ptr
            if not obj_orig:
                continue
            if obj_orig.name == output_obj.name:
                continue
            if o_props.use_solo and i > o_props.sdf_stack_index:
                break

            p_props = getattr(obj_orig, "sdf_props", None)
            local_mat = inv_world_output @ obj_orig.matrix_world
            loc, rot, scale = local_mat.decompose()

            element = {
                'obj_orig': obj_orig,
                'matrix_world': obj_orig.matrix_world.copy(),
                'p_props': p_props,
                'loc': loc,
                'rot': rot,
                'scale': scale
            }
            working_group.append(element)

    # ループ後の残りを追加
    flat_elements.extend(working_group)
    return flat_elements


def draw_callback_3d(self, context):
    """ビューポートにレイマーチングオーバーレイを描画"""
    global _batch
    if context is None: context = bpy.context
    try:
        scene = context.scene
        if not scene.sdf_live_update or not getattr(scene, "sdf_show_preview", True):
            return
    except Exception:
        return
    shader = get_shader()
    if not shader: return

    output_obj = None
    target_col = None
    for o in scene.objects:
        props = getattr(o, "sdf_props", None)
        if props and props.is_output:
            output_obj = o
            target_col = props.target_collection
            break

    if not output_obj or not target_col: return

    inv_world_output = output_obj.matrix_world.inverted()

    # V7: スタック順序に従う
    sync_sdf_stack(output_obj)

    o_props = output_obj.sdf_props

    # V15.9.8.1: コレクション展開対応 — engine.pyと同等のフラット展開
    flat_elements = _flatten_stack_for_preview(output_obj, inv_world_output)

    prim_data = []
    for el in flat_elements:
        data = _build_prim_data_for_element(el, o_props)
        prim_data.extend(data)

    if not prim_data: return
    # V16: 16 pixels per primitive (64 floats)
    prim_count = len(prim_data) // 64

    if _batch is None:
        _batch = batch_for_shader(shader, 'TRIS', {"pos": _fsq_coords}, indices=_fsq_indices)

    rv3d = context.region_data
    if not rv3d: return

    inv_proj_view_local = inv_world_output @ rv3d.perspective_matrix.inverted()

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('ALWAYS')
    gpu.state.face_culling_set('NONE')
    shader.bind()
    try:
        shader.uniform_float("invProjViewLocal", inv_proj_view_local)
        domain_size = _compute_preview_domain_size(output_obj, o_props, inv_world_output, flat_elements)
        shader.uniform_float("domainSize", domain_size)
        shader.uniform_int("primCount", prim_count)

        sym_mask = (1 if output_obj.sdf_props.sym_x else 0) | \
                   (2 if output_obj.sdf_props.sym_y else 0) | \
                   (4 if output_obj.sdf_props.sym_z else 0)
        shader.uniform_int("symmetryFlags", sym_mask)

        # 描画品質（ステップ数）の決定
        q_map = {'LOW': 128, 'MID': 256, 'HIGH': 512}
        max_steps = q_map.get(output_obj.sdf_props.preview_quality, 256)
        auto_steps = int(domain_size * 24.0)
        max_steps = max(max_steps, min(auto_steps, 2048))
        shader.uniform_int("maxSteps", max_steps)

        data_buf = gpu.types.Buffer('FLOAT', len(prim_data), prim_data)
        prim_tex = gpu.types.GPUTexture((16, prim_count), format='RGBA32F', data=data_buf)
        shader.uniform_sampler("primTex", prim_tex)
        _batch.draw(shader)
    except Exception as e:
        print(f"SDF Draw Error: {e}")
        import traceback; traceback.print_exc()
    gpu.state.blend_set('NONE')
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.face_culling_set('BACK')

@persistent
def sdf_depsgraph_handler(scene, depsgraph):
    if getattr(sdf_depsgraph_handler, "_is_running", False): return
    from . import engine
    if getattr(engine, "_in_update", False): return
    if getattr(engine, "_duplicate_cooldown", False): return

    # 1. 選択状態の同期 (Viewport -> UI List)
    # これは Live Update の ON/OFF に関わらず実行する
    active_obj = bpy.context.active_object
    if active_obj:
        active_orig = active_obj.original if hasattr(active_obj, "original") else active_obj
        for obj in bpy.data.objects:
            props = getattr(obj, "sdf_props", None)
            if props and props.is_output:
                for i, item in enumerate(props.sdf_stack):
                    if item.object_ptr and item.object_ptr.name == active_orig.name:
                        if props.sdf_stack_index != i:
                            props.sdf_stack_index = i
                        break

    # 2. メッシュの更新判定 (Live Update が ON の場合のみ)
    if not scene.sdf_live_update: return

    is_relevant = False
    for update in depsgraph.updates:
        id_orig = update.id.original if hasattr(update.id, "original") else update.id
        if isinstance(id_orig, bpy.types.Object):
            # 更新されたオブジェクトがスタック内の仕切りEmptyであるか確認
            is_empty_divider = False
            for o in scene.objects:
                out_p = getattr(o.original, "sdf_props", None)
                if out_p and out_p.is_output:
                    for item in out_p.sdf_stack:
                        if item.item_type == 'COLLECTION' and item.empty_ptr and item.empty_ptr.name == id_orig.name:
                            is_empty_divider = True
                            break
                if is_empty_divider:
                    break

            p = getattr(id_orig, "sdf_props", None)
            if p and (p.is_primitive or (p.is_output and update.is_updated_transform) or is_empty_divider):
                is_relevant = True
            if not is_relevant:
                for o in scene.objects:
                    out_p = getattr(o.original, "sdf_props", None)
                    if out_p and out_p.is_output and out_p.target_collection:
                        if id_orig.name in out_p.target_collection.objects:
                            is_relevant = True; break
        if is_relevant: break

    if is_relevant:
        sdf_depsgraph_handler._is_running = True
        try:
            # メッシュの更新
            for obj_orig in scene.objects:
                props = getattr(obj_orig.original, "sdf_props", None)
                if props and props.is_output and obj_orig.mode == 'OBJECT':
                    update_sdf_mesh(obj_orig, depsgraph=depsgraph)
        except Exception as e:
            print(f"SDF Handler Error: {e}")
        finally:
            sdf_depsgraph_handler._is_running = False

def sdf_undo_handler(scene):
    """Undo/Redo 時に状態ハッシュキャッシュをクリアし、再計算を強制する"""
    from . import engine
    engine._last_state_hashes.clear()
    # 必要に応じて即座に更新をトリガー
    for obj in scene.objects:
        if getattr(obj, "sdf_props", None) and obj.sdf_props.is_output:
            engine.update_sdf_mesh(obj)

def clear_batch():
    global _batch
    _batch = None
