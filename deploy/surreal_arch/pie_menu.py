"""Melodia Studio radial pie menus - main + room / window / genome sub-pies + hotkeys."""

from __future__ import annotations

import bpy

_addon_keymaps: list = []
_handle_ctx_menu = None


def _has_surreal_mesh(context):
    obj = context.active_object
    return bool(obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props"))


# ── Operators that set a property and optionally generate ──────────────

class SURREAL_ARCH_OT_set_room_shape(bpy.types.Operator):
    bl_idname = "surreal_arch.set_room_shape"
    bl_label = "Set Room Shape"
    bl_options = {"REGISTER", "UNDO"}
    shape: bpy.props.StringProperty(name="Shape", default="RECTANGLE")
    do_generate: bpy.props.BoolProperty(name="Generate", default=False)

    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, "surreal_arch_props"):
            self.report({"ERROR"}, "No Melodia mesh active")
            return {"CANCELLED"}
        props = obj.surreal_arch_props
        # New shapes map to legacy gb_room_shape where possible; new ones stored on dynamic prop
        legacy_map = {
            "RECTANGLE": "RECTANGLE", "L_SHAPE": "L_SHAPE", "T_SHAPE": "T_SHAPE", "U_SHAPE": "U_SHAPE",
            "CIRCULAR": "CIRCULAR", "APSIDAL": "APSIDAL", "OCTAGON": "OCTAGON", "HEX": "HEX",
            "ELLIPSE": "ELLIPSE", "SUPERELLIPSE": "SUPERELLIPSE", "FREEFORM": "FREEFORM",
        }
        target = legacy_map.get(self.shape, "RECTANGLE")
        # gb_room_shape now supports extended enum (patched in Phase B)
        try:
            props.gb_room_shape = target
        except Exception:
            # fallback: store on custom property if enum not yet extended
            obj["melodia_room_shape"] = target
        # Also ensure we are on a room arch type
        try:
            if getattr(props, "arch_type", "") not in ("GREYBOX_ROOM", "GB_ROOM_COMPOSITE", "GB_ROOM_CIRCULAR", "GB_ROOM_APSIDAL"):
                props.arch_type = "GREYBOX_ROOM"
        except Exception:
            pass
        if self.do_generate:
            bpy.ops.surreal_arch.generate()
        return {"FINISHED"}


class SURREAL_ARCH_OT_set_window_shape(bpy.types.Operator):
    bl_idname = "surreal_arch.set_window_shape"
    bl_label = "Set Window Shape"
    bl_options = {"REGISTER", "UNDO"}
    shape: bpy.props.StringProperty(name="Shape", default="RECT")
    do_generate: bpy.props.BoolProperty(name="Generate", default=False)

    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, "surreal_arch_props"):
            self.report({"ERROR"}, "No Melodia mesh active")
            return {"CANCELLED"}
        props = obj.surreal_arch_props
        # gb_window_shape is new enum (Phase C); store gracefully if missing
        try:
            props.gb_window_shape = self.shape
        except Exception:
            obj["melodia_window_shape"] = self.shape
        # ensure windows enabled
        try:
            props.gb_windows_enabled = True
            if not getattr(props, "gb_window_count_ns", 0) and not getattr(props, "gb_window_count", 0):
                props.gb_window_count_ns = 2
                props.gb_window_count_ew = 1
        except Exception:
            pass
        if self.do_generate:
            bpy.ops.surreal_arch.generate()
        return {"FINISHED"}


class SURREAL_ARCH_OT_nudge_genome(bpy.types.Operator):
    bl_idname = "surreal_arch.nudge_genome"
    bl_label = "Nudge Genome"
    bl_options = {"REGISTER", "UNDO"}
    attr: bpy.props.StringProperty(name="Genome Attr")
    delta: bpy.props.FloatProperty(name="Delta", default=0.1)

    def execute(self, context):
        obj = context.active_object
        if not obj or not hasattr(obj, "surreal_arch_props"):
            return {"CANCELLED"}
        props = obj.surreal_arch_props
        if not hasattr(props, self.attr):
            return {"CANCELLED"}
        v = getattr(props, self.attr)
        setattr(props, self.attr, max(0.0, min(1.0, v + self.delta)))
        return {"FINISHED"}


# ── Pie menus ───────────────────────────────────────────────────────────

class SURREAL_ARCH_MT_pie_main(bpy.types.Menu):
    bl_label = "Melodia Studio"
    bl_idname = "SURREAL_ARCH_MT_pie_main"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        has_props = _has_surreal_mesh(context)

        # 4 - West : Generate (big action)
        pie.operator("surreal_arch.generate", text="Generate", icon="SHADERFX")
        # 6 - East : Room shape sub-pie
        pie.operator("surreal_arch.pie_room", text="Room Shape", icon="MESH_CUBE")
        # 2 - South : Window sub-pie
        pie.operator("surreal_arch.pie_window", text="Window", icon="WINDOW")
        # 8 - North : Genome sub-pie
        pie.operator("surreal_arch.pie_genome", text="Genome", icon="RNA")
        # 7 - NW : Trim / Bake
        col = pie.column()
        col.operator("surreal_arch.trim_preset_zen_stone", text="Zen Stone Trim", icon="MOD_BOOLEAN")
        col.operator("surreal_arch.bake_trim_attributes", text="Bake Trim", icon="GROUP_VCOL")
        # 1 - NE : Snap
        col2 = pie.column()
        col2.operator("surreal_arch.snap_to_selected", text="Snap", icon="SNAP_VERTEX")
        col2.operator("surreal_arch.toggle_snap_overlay", text="Snap Overlay", icon="HIDE_OFF")
        # 5 - SW : Export
        pie.operator("surreal_arch.export_ue5", text="Export UE5", icon="EXPORT")
        # 3 - SE : Plan / Graph
        col3 = pie.column()
        if has_props:
            col3.operator("surreal_arch.spawn_graph_zen_sakura_walk", text="Sakura Walk", icon="OUTLINER_OB_GROUP_INSTANCE")
        else:
            col3.label(text="Select mesh", icon="ERROR")
        col3.operator("surreal_arch.plan_spawn_zen_sakura", text="Zen Sakura Plan", icon="WORLD")


class SURREAL_ARCH_MT_pie_room(bpy.types.Menu):
    bl_label = "Room Shape"
    bl_idname = "SURREAL_ARCH_MT_pie_room"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 8 shapes + generate center-ish. Order: W,E,S,N,NW,NE,SW,SE
        ops = [
            ("RECTANGLE", "Rectangle", "MESH_PLANE"),
            ("L_SHAPE", "L-Shape", "MESH_CUBE"),
            ("T_SHAPE", "T-Shape", "MESH_CUBE"),
            ("U_SHAPE", "U-Shape", "MESH_CUBE"),
            ("CIRCULAR", "Circular", "MESH_CIRCLE"),
            ("APSIDAL", "Apsidal", "MESH_CAPSULE"),
            ("OCTAGON", "Octagon", "MESH_CUBE"),
            ("HEX", "Hex / Ellipse", "MESH_CIRCLE"),
        ]
        for shape, label, icon in ops:
            op = pie.operator("surreal_arch.set_room_shape", text=label, icon=icon)
            op.shape = shape
            op.do_generate = False
        # Extra row for advanced shapes (superellipse / freeform) as nested buttons below pie
        # Blender pies are capped at 8 - superellipse & freeform live in the main room operators
        # Add a hint label in the remaining slot if available
        pie.separator()
        pie.separator()


class SURREAL_ARCH_MT_pie_window(bpy.types.Menu):
    bl_label = "Window Cutouts"
    bl_idname = "SURREAL_ARCH_MT_pie_window"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        has_props = _has_surreal_mesh(context)
        shapes = [
            ("RECT", "Rect", "WINDOW"),
            ("ARCH_ROUND", "Round Arch", "MESH_CIRCLE"),
            ("GOTHIC", "Gothic", "HEART"),
            ("OGEE", "Ogee", "CURVE_BEZCURVE"),
            ("CIRCLE", "Circle", "MESH_CIRCLE"),
            ("ROSETTE", "Rosette", "MESH_ICOSPHERE"),
            ("LINTEL", "Lintel", "MESH_PLANE"),
            ("SEGMENTAL", "Segmental", "MESH_CAPSULE"),
        ]
        for shape, label, icon in shapes:
            op = pie.operator("surreal_arch.set_window_shape", text=label, icon=icon)
            op.shape = shape
            op.do_generate = False
        if has_props:
            # Quick window toggle + count nudge row (drawn as extra pie items - Blender clips at 8, so add as column)
            pass


class SURREAL_ARCH_MT_pie_genome(bpy.types.Menu):
    bl_label = "Style Genome"
    bl_idname = "SURREAL_ARCH_MT_pie_genome"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 6 DNA axes as paired +/- wedges + 2 style picks
        axes = [
            ("genome_verticality", "Vertical", "SORTSIZE"),
            ("genome_symmetry", "Symmetry", "MOD_MIRROR"),
            ("genome_ornament_density", "Ornament", "BRUSH_DATA"),
            ("genome_structural_logic", "Structure", "MOD_BUILD"),
            ("genome_organic_growth", "Organic", "OUTLINER_OB_ARMATURE"),
            ("genome_cosmic_influence", "Cosmic", "LIGHT_SUN"),
        ]
        for attr, label, icon in axes:
            col = pie.column(align=True)
            op_up = col.operator("surreal_arch.nudge_genome", text=f"{label} +", icon=icon)
            op_up.attr = attr
            op_up.delta = 0.15
            op_dn = col.operator("surreal_arch.nudge_genome", text=f"{label} −", icon=icon)
            op_dn.attr = attr
            op_dn.delta = -0.15
        # Two extra style genome quick picks
        col = pie.column(align=True)
        col.operator("surreal_arch.select_style_genome", text="Zen Shrine").genome_id = "zen_shrine_v1"
        col.operator("surreal_arch.select_style_genome", text="Gothic Cloister").genome_id = "gothic_cloister_v1"


# ── Pie caller operators ────────────────────────────────────────────────

class SURREAL_ARCH_OT_pie_menu(bpy.types.Operator):
    bl_idname = "surreal_arch.pie_menu"
    bl_label = "Melodia Studio Pie"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=SURREAL_ARCH_MT_pie_main.bl_idname)
        return {"FINISHED"}


class SURREAL_ARCH_OT_pie_room(bpy.types.Operator):
    bl_idname = "surreal_arch.pie_room"
    bl_label = "Room Shape Pie"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=SURREAL_ARCH_MT_pie_room.bl_idname)
        return {"FINISHED"}


class SURREAL_ARCH_OT_pie_window(bpy.types.Operator):
    bl_idname = "surreal_arch.pie_window"
    bl_label = "Window Pie"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=SURREAL_ARCH_MT_pie_window.bl_idname)
        return {"FINISHED"}


class SURREAL_ARCH_OT_pie_genome(bpy.types.Operator):
    bl_idname = "surreal_arch.pie_genome"
    bl_label = "Genome Pie"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=SURREAL_ARCH_MT_pie_genome.bl_idname)
        return {"FINISHED"}


# ── Keymaps + context menu ─────────────────────────────────────────────

def _ctx_menu_draw(self, context):
    layout = self.layout
    layout.separator()
    layout.label(text="Melodia Studio", icon="SHADERFX")
    layout.operator("surreal_arch.pie_menu", text="Melodia Pie  (Shift+Q)", icon="SHADERFX")
    layout.operator("surreal_arch.pie_room", text="Room Shape Pie  (Alt+Q)", icon="MESH_CUBE")
    layout.operator("surreal_arch.pie_window", text="Window Pie  (Ctrl+Shift+Q)", icon="WINDOW")
    layout.operator("surreal_arch.pie_score", text="* Score Pie  (Shift+M)", icon="PLAY")


def _register_keymaps():
    if _addon_keymaps:
        return
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    # Shift+Q - main pie (most used; MACHIN3tools uses Q alone, so Shift+Q is safe)
    kmi = km.keymap_items.new("surreal_arch.pie_menu", "Q", "PRESS", shift=True)
    _addon_keymaps.append((km, kmi))
    # Alt+Q - room shape pie
    kmi2 = km.keymap_items.new("surreal_arch.pie_room", "Q", "PRESS", alt=True)
    _addon_keymaps.append((km, kmi2))
    # Ctrl+Shift+Q - window pie
    kmi3 = km.keymap_items.new("surreal_arch.pie_window", "Q", "PRESS", shift=True, ctrl=True)
    _addon_keymaps.append((km, kmi3))
    # Shift+Alt+Q - genome pie
    kmi4 = km.keymap_items.new("surreal_arch.pie_genome", "Q", "PRESS", shift=True, alt=True)
    _addon_keymaps.append((km, kmi4))


def _unregister_keymaps():
    for km, kmi in list(_addon_keymaps):
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    _addon_keymaps.clear()


def register_keymaps_and_menus():
    _register_keymaps()
    # Object context menu (right-click in 3D View) - idempotent
    try:
        global _handle_ctx_menu
        if _handle_ctx_menu is None:
            bpy.types.VIEW3D_MT_object_context_menu.append(_ctx_menu_draw)
            _handle_ctx_menu = _ctx_menu_draw
    except Exception:
        pass


def unregister_keymaps_and_menus():
    _unregister_keymaps()
    try:
        if _handle_ctx_menu:
            bpy.types.VIEW3D_MT_object_context_menu.remove(_handle_ctx_menu)
    except Exception:
        pass


def register_pie_menu():
    classes = (
        SURREAL_ARCH_OT_set_room_shape,
        SURREAL_ARCH_OT_set_window_shape,
        SURREAL_ARCH_OT_nudge_genome,
        SURREAL_ARCH_MT_pie_main,
        SURREAL_ARCH_MT_pie_room,
        SURREAL_ARCH_MT_pie_window,
        SURREAL_ARCH_MT_pie_genome,
        SURREAL_ARCH_OT_pie_menu,
        SURREAL_ARCH_OT_pie_room,
        SURREAL_ARCH_OT_pie_window,
        SURREAL_ARCH_OT_pie_genome,
    )
    return classes


def register_pie_menu_with_keymaps():
    """Called from integration.register_overhaul after classes are registered."""
    register_keymaps_and_menus()


def unregister_pie_menu_with_keymaps():
    unregister_keymaps_and_menus()
