# SDF.R - Blender Add-on
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (c) 2026 hinata_hugu (Replace '2024' with the current year if different)
# All Rights Reserved.


#
# =============================================================================
# DEVELOPMENT NOTES / 髢狗匱繝弱・繝・# =============================================================================
#
#
# [English]
# This add-on, SDF.R, was developed with transparency through a collaboration 
# between myself (hinata_hugu), a human developer, and an AI:
#
# - DESIGN INTENT: All design principles, policies, and instructions were 
#   entirely driven by me. This add-on was developed to make SDF modeling 
#   in Blender as lightweight and intuitive as possible. 
#   By offloading the heavy lifting to a custom Rust-based GPU engine, 
#   it eliminates the need for complex Geometry Nodes setups. 
#   Real-time "Ghost Previews" via Blender's GPU module ensure a stress-free 
#   modeling experience. Currently in Beta, striving for further evolution.
#
# - ITERATIVE DEVELOPMENT: This is unmistakably an add-on created by me, 
#   refined through hundreds of cycles of coding, testing, debugging, 
#   and improvement.
#
# - RESPONSIBILITY: All debugging, user feedback, and support are handled 
#   exclusively by the human developer.
#
# - CODE FORMATTING: AI assisted with final code organization to improve 
#   readability. This benefits GPL users who wish to learn from this codebase. 
#   The Rust source code is also prepared for release upon request, 
#   honoring the spirit of free software.
#
# -----------------------------------------------------------------------------
#
# [譌･譛ｬ隱枉
# 縺薙・繧｢繝峨が繝ｳSDF.R縺ｯ莠ｺ髢薙〒縺ゅｋ遘・hinata_hugu)縺ｨAI縺ｮ蜊泌ロ縺ｫ繧医ｊ縲・乗・諤ｧ繧呈戟縺｣縺ｦ髢狗匱縺輔ｌ縺ｾ縺励◆・・#
# - 蛻ｶ菴懈э蝗ｳ: 蜈ｨ縺ｦ縺ｮ險ｭ險域欠驥昴・譁ｹ驥昴・謖・､ｺ縺ｯ蜈ｨ縺ｦ遘√′陦後▲縺ｦ縺・∪縺吶・#   縺薙・繧｢繝峨が繝ｳ縺ｯBlender蜀・〒SDF繝｢繝・Μ繝ｳ繧ｰ繧貞ｰ代＠縺ｧ繧りｻｽ蠢ｫ縺ｫ陦後≧縺溘ａ髢狗匱縺励※縺・∪縺吶・#   險ｭ險域欠驥昴→縺励※縲；PU縺ｮ荳ｦ蛻怜・逅・ｒ豢ｻ逕ｨ縺吶ｋ縺溘ａRust繧貞､冶｣・＠蜀・Κ縺ｧ蜃ｦ逅・ｒ陦後ｏ縺帙ｋ縺薙→縺ｧSDF繝｢繝・Μ繝ｳ繧ｰ繧・#   繧医ｊ霆ｽ蠢ｫ縺ｫ陦後∴繧九ｈ縺・↓縺励∪縺励◆縲・  
#   縺薙ｌ縺ｫ繧医▲縺ｦ縲∝ｾ捺擂縺ｮBlender縺ｮ繧ｸ繧ｪ繝｡繝医Μ繝ｼ繝弱・繝峨☆繧臥ｵ・・蠢・ｦ√′縺ｪ縺上↑繧翫・#   逶ｴ諢溽噪縺ｪ繧､繝ｳ繧ｿ繝ｼ繝輔ぉ繝ｼ繧ｹ縺ｧSDF繝｢繝・Μ繝ｳ繧ｰ繧定｡後∴繧九ｈ縺・↓縺励∪縺励◆縲・#   bpy縺ｫ縺ゅｋgpu謠冗判縺ｫ繧医ｊ繧ｴ繝ｼ繧ｹ繝医・繝ｬ繝薙Η繝ｼ繧偵Μ繧｢繝ｫ繧ｿ繧､繝縺ｧ陦後＞縲・#   繝ｦ繝ｼ繧ｶ繝ｼ縺ｮ繧ｹ繝医Ξ繧ｹ繧定ｻｽ貂帙☆繧九ｈ縺・↓縺励∪縺励◆縲・#   迴ｾ蝨ｨ縺ｯ繝吶・繧ｿ迚医→縺励※繝ｪ繝ｪ繝ｼ繧ｹ縺励√＆繧峨↑繧狗匱螻輔ｒ逶ｮ謖・＠縺ｦ縺・∪縺吶・#
# - 蜿榊ｾｩ髢狗匱: 繧ｳ繝ｼ繝・ぅ繝ｳ繧ｰ縲√ユ繧ｹ繝医√ョ繝舌ャ繧ｰ縲∵隼濶ｯ縺ｮ繧ｵ繧､繧ｯ繝ｫ繧呈焚逋ｾ蝗樔ｻ･荳翫↓繧上◆繧願｡後▲縺ｦ縺・∪縺吶・#   邏帙ｌ繧ゅ↑縺・∫ｧ√↓繧医ｋ遘√′菴懈・縺励◆繧｢繝峨が繝ｳ縺ｧ縺吶・#
# - 雋ｬ莉ｻ: 繝・ヰ繝・げ縲√Θ繝ｼ繧ｶ繝ｼ繝輔ぅ繝ｼ繝峨ヰ繝・け縲√し繝昴・繝医・蜈ｨ縺ｦ莠ｺ髢薙・髢狗匱閠・′諡・ｽ薙＠縺ｾ縺吶・#
# - 繧ｳ繝ｼ繝画紛蠖｢: 譛邨ら噪縺ｪ繧ｳ繝ｼ繝画紛逅・↓縺ｯAI繧呈ｴｻ逕ｨ縺励∝庄隱ｭ諤ｧ繧貞髄荳翫＆縺帙※縺・∪縺吶・#   縺薙ｌ縺ｯGPL繝ｩ繧､繧ｻ繝ｳ繧ｹ縺ｮ荳九〒縺薙・繧ｳ繝ｼ繝峨°繧牙ｭｦ縺ｳ縺溘＞繝ｦ繝ｼ繧ｶ繝ｼ縺ｫ繧よ怏逶翫→閠・∴縺ｦ縺・∪縺吶・#   Rust縺ｮ繧ｳ繝ｼ繝峨↓縺､縺・※繧ょｿ・ｦ√↓蠢懊§縺ｦ蜈ｬ髢九☆繧区ｺ門ｙ縺後≠繧翫∪縺吶・#
# -----------------------------------------------------------------------------
#
# 繧ｯ繝ｪ繧ｨ繧､繧ｿ繝ｼ螳｣隱・/ Creator's Oath
#
# In the spirit of free software and the GNU GPL:
# May Blender forever remain free under the GPL!
# This addon guarantees all users the freedom to learn from,
# modify, and share this source code 窶・forever.
#
# GPL縺ｨ閾ｪ逕ｱ繧ｽ繝輔ヨ繧ｦ繧ｧ繧｢縺ｮ邊ｾ逾槭ｒ閭ｸ縺ｫ・・# Blender繧医；PL縺ｮ蜷阪・荳九↓豌ｸ驕縺ｫ閾ｪ逕ｱ縺ｧ縺ゅｌ・・# 縺薙・繧｢繝峨が繝ｳ縺ｯ縲√た繝ｼ繧ｹ繧ｳ繝ｼ繝峨ｒ騾壹§縺ｦ蟄ｦ縺ｳ縲∵隼螟峨＠縲∝・譛峨☆繧玖・逕ｱ繧・# 蜈ｨ縺ｦ縺ｮ繝ｦ繝ｼ繧ｶ繝ｼ縺ｫ豌ｸ驕縺ｫ菫晁ｨｼ縺励∪縺吶・#
# =============================================================================

bl_info = {
    "name": "SDF.R",
    "author": "hinata_hugu",
    "version": (15, 9, 8, 1),  # V15.9.8.1: Stack Partitioning Grouping
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > SDF-R",
    "description": "Next-gen SDF Modeling Tool with Professional Workflow",
    "category": "Mesh",
}

if "bpy" in locals():
    import importlib
    importlib.reload(constants)
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
    importlib.reload(handlers)
    importlib.reload(engine)
    importlib.reload(shader)
else:
    import bpy
    import os
    from . import constants
    from . import properties
    from . import operators
    from . import ui
    from . import handlers
    from . import engine
    from . import shader

from .engine import _update_preview

_LAYOUT_FLAG_FILE = os.path.join(os.path.dirname(__file__), "SDF_DEBUG_LAYOUT.ON")
_LAYOUT_DEBUG_ENV = os.environ.get("SDF_DEBUG_LAYOUT", "").strip().lower() in {"1", "true", "yes", "on"}
_LAYOUT_DEBUG_ON = _LAYOUT_DEBUG_ENV or os.path.exists(_LAYOUT_FLAG_FILE)
print(f"SDF.R: Loader Marker V15.9.8.1 (__init__.py loaded from: {__file__})")
print(f"SDF.R: Layout Debug Switch = {_LAYOUT_DEBUG_ON} (env={_LAYOUT_DEBUG_ENV}, flag_file={os.path.exists(_LAYOUT_FLAG_FILE)})")


_draw_handler = None
_gpu_init_finished = False

classes = (
    properties.SDF_DeformItem,
    properties.SDF_StackItem,
    properties.SDF_SceneProperties,
    properties.SDF_ObjectProperties,
    operators.SDF_OT_add_primitive,
    operators.SDF_OT_toggle_display,
    operators.SDF_OT_move_to_sdf_collection,
    operators.SDF_OT_duplicate_collection,
    operators.SDF_OT_bake_mesh,
    operators.SDF_OT_setup_material,
    operators.SDF_OT_reset_material,
    operators.SDF_OT_generate_mesh,
    operators.SDF_OT_add_selected,
    operators.SDF_OT_make_output,
    operators.SDF_OT_stack_move,
    operators.SDF_OT_stack_remove,
    operators.SDF_OT_add_collection_divider,
    operators.SDF_OT_select_stack_obj,
    operators.SDF_OT_setup_post_process,
    operators.SDF_OT_update_normals,
    operators.SDF_OT_finalize,
    operators.SDF_OT_all_clear,
    operators.SDF_OT_set_resolution_preset,
    operators.SDF_OT_switch_algo,
    operators.SDF_OT_deform_add,
    operators.SDF_OT_deform_remove,
    operators.SDF_OT_deform_move,
    ui.SDF_UL_stack_list,
    ui.SDF_UL_deform_list,
    ui.SDF_PT_main,
)


def update_result_visibility(self, context):
    """SDF_Result 繝｡繝・す繝･縺ｮ陦ｨ遉ｺ/髱櫁｡ｨ遉ｺ繧貞・繧頑崛縺医ｋ"""
    from . import engine
    for obj in context.scene.objects:
        if getattr(obj, "sdf_props", None) and obj.sdf_props.is_output:
            obj.hide_viewport = not self.sdf_show_result
            obj.hide_render = not self.sdf_show_result
            
            # V15.9.9: ONになった瞬間に強制的にメッシュ再生成をトリガーする
            if self.sdf_show_result:
                if obj.name in engine._last_state_hashes:
                    del engine._last_state_hashes[obj.name]
                engine.update_sdf_mesh(obj)

def update_primitives_visibility(self, context):
    """SDF_Collection 縺ｮ陦ｨ遉ｺ繝｢繝ｼ繝会ｼ・ire/Bounds・峨ｒ蛻・ｊ譖ｿ縺医ｋ"""
    col = bpy.data.collections.get("SDF_Collection")
    if col:
        col.hide_viewport = False
        display_mode = 'WIRE' if self.sdf_show_primitives else 'BOUNDS'
        for obj in col.objects:
            obj.display_type = display_mode

def register():
    global _draw_handler, _gpu_init_finished
    _gpu_init_finished = False
    
    import bpy
    import os
    import threading
    import time
    from . import rust_gpu_sdf
    print("SDF.R: --- Initializing GPU Engine (V15.9.8.1) ---")
    
    cache_dir = os.path.join(bpy.utils.user_resource('DATAFILES'), "rust_gpu_sdf")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, "shader_cache.bin")
    
    cache_data = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                cache_data = f.read()
        except Exception as e:
            print(f"SDF.R: Failed to load cache: {e}")
            
    if cache_data is None:
        print("SDF.R: No shader cache. This initial compilation may take a few minutes...")
    else:
        print(f"SDF.R: Shader cache found ({len(cache_data)} bytes).")

    def background_init():
        global _gpu_init_finished
        start_time = time.time()
        print(f"SDF.R: --- Starting GPU Warming-up (V15.9.8.1) ---")
        try:
            # Initialize GPU engine in Rust.
            success = rust_gpu_sdf.init_gpu(cache_path)
            elapsed = time.time() - start_time
            if success:
                print(f"SDF.R: GPU Engine Ready! (Warming-up finished in {elapsed:.2f} seconds)")
            else:
                print(f"SDF.R: GPU Engine warming-up failed in {elapsed:.2f} seconds.")
            _gpu_init_finished = True # 完了フラグ
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"SDF.R: GPU Engine initialization error after {elapsed:.2f}s: {e}")
            
            if os.path.exists(cache_path):
                print("SDF.R: Removing potentially corrupted shader cache and retrying...")
                try:
                    os.remove(cache_path)
                    success = rust_gpu_sdf.init_gpu(cache_path)
                    elapsed_retry = time.time() - start_time - elapsed
                    if success:
                        print(f"SDF.R: GPU Engine Ready after retry! ({elapsed_retry:.2f} seconds)")
                    else:
                        print(f"SDF.R: GPU Engine warming-up failed after retry.")
                except Exception as retry_e:
                    print(f"SDF.R: GPU Engine initialization error on retry: {retry_e}")

            _gpu_init_finished = True

    def init_checker():
        """Check async GPU warm-up status and update scene flags."""
        global _gpu_init_finished
        if _gpu_init_finished:
            for scene in bpy.data.scenes:
                if hasattr(scene, "sdf_scene_props"):
                    scene.sdf_scene_props.is_gpu_ready = True
            return None
        return 0.1
    def delayed_start():
        init_thread = threading.Thread(target=background_init, daemon=True)
        init_thread.start()
        bpy.app.timers.register(init_checker)
        return None
    # Delay start slightly so Blender UI setup can settle.
    bpy.app.timers.register(delayed_start, first_interval=0.5)
    print("SDF.R: Addon registered. Warming-up will start in 0.5s...")

    # 2. 繧ｯ繝ｩ繧ｹ逋ｻ骭ｲ
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Object.sdf_props = bpy.props.PointerProperty(type=properties.SDF_ObjectProperties)
    bpy.types.Scene.sdf_scene_props = bpy.props.PointerProperty(type=properties.SDF_SceneProperties)
    bpy.types.Scene.sdf_live_update = bpy.props.BoolProperty(name="Live Update", default=True)
    bpy.types.Scene.sdf_show_preview = bpy.props.BoolProperty(
        name="Show GPU Preview", default=True, update=_update_preview
    )
    bpy.types.Scene.sdf_show_result = bpy.props.BoolProperty(
        name="Show Result Mesh", default=True, update=update_result_visibility
    )
    bpy.types.Scene.sdf_show_primitives = bpy.props.BoolProperty(
        name="Show Source Primitives", default=True, update=update_primitives_visibility
    )
    
    bpy.app.handlers.depsgraph_update_post.append(handlers.sdf_depsgraph_handler)
    bpy.app.handlers.undo_post.append(handlers.sdf_undo_handler)
    bpy.app.handlers.redo_post.append(handlers.sdf_undo_handler)
    _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
        handlers.draw_callback_3d, (None, None), 'WINDOW', 'POST_VIEW'
    )

def unregister():
    global _draw_handler
    if _draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None
    
    if handlers.sdf_depsgraph_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(handlers.sdf_depsgraph_handler)
    if handlers.sdf_undo_handler in bpy.app.handlers.undo_post:
        bpy.app.handlers.undo_post.remove(handlers.sdf_undo_handler)
    if handlers.sdf_undo_handler in bpy.app.handlers.redo_post:
        bpy.app.handlers.redo_post.remove(handlers.sdf_undo_handler)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Object.sdf_props
    del bpy.types.Scene.sdf_scene_props
    del bpy.types.Scene.sdf_live_update
    del bpy.types.Scene.sdf_show_preview
    del bpy.types.Scene.sdf_show_result
    del bpy.types.Scene.sdf_show_primitives

    handlers.clear_batch()
    shader.clear_shader()
