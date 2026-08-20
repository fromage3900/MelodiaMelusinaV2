"""Modifier stack system ΓÇö track GN state, expose N-panel UI for stacking.

Uses a CollectionProperty on the active object to store modifier configs,
mirrors Bagapie-style workflow: add modifier ΓåÆ select preset ΓåÆ adjust params.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Panel, PropertyGroup, Operator

from . import core as _gn_core
from ..branding import N_PANEL_CATEGORY


def _filter_tree(tree_name: str, filter_text: str) -> bool:
    """Check if a tree matches the current search filter."""
    if not filter_text:
        return True
    ft = filter_text.lower()
    label = _gn_core.TREE_LABEL_MAP.get(tree_name, tree_name).lower()
    desc = _gn_core.TREE_DESCRIPTIONS.get(tree_name, "").lower()
    return ft in tree_name.lower() or ft in label or ft in desc


def _all_tree_names() -> list[str]:
    show_hidden = bool(getattr(bpy.context.window_manager, "mel_gn_show_hidden", False))
    return [
        name for name, _ in _gn_core.TREE_TYPES
        if show_hidden or not _gn_core.is_hidden_builder(name)
    ]


# Back-compat alias (prefer _all_tree_names() — catalog rebuilds after import)
ALL_TREE_NAMES: list[str] = []


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Data Model
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MEL_GN_StackItem(PropertyGroup):
    """One stack entry: references a GN modifier + its preset."""

    name: StringProperty(name="Name", default="GN Modifier")
    modifier_name: StringProperty(name="Modifier Name")
    tree_name: StringProperty(name="Node Tree")
    enabled: BoolProperty(name="Enabled", default=True)
    expand: BoolProperty(name="Expand", default=True)


class MEL_GN_StackSettings(PropertyGroup):
    """Per-object stack settings."""

    items: CollectionProperty(type=MEL_GN_StackItem)
    active_index: IntProperty(name="Active Index", default=0)
    filter_text: StringProperty(
        name="Filter",
        description="Search GN trees by name or description",
        default="",
        options={"TEXTEDIT_UPDATE"},
    )


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Operators
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ


class MEL_GN_OT_apply_preset(Operator):
    """Apply a curated preset's group-input defaults onto an existing GN modifier tree."""

    bl_idname = "mel_gn.apply_preset"
    bl_label = "Apply GN Preset"
    bl_options = {"REGISTER", "UNDO"}

    tree_name: StringProperty(name="Tree", default="")
    preset_name: StringProperty(name="Preset", default="")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        from .presets import preset_param_sets, BUILDERS_PRESETS

        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        tree_name = self.tree_name
        preset_name = self.preset_name
        if not tree_name or not preset_name:
            self.report({"WARNING"}, "tree_name and preset_name required")
            return {"CANCELLED"}
        if tree_name not in BUILDERS_PRESETS:
            self.report({"WARNING"}, f"No presets for {tree_name}")
            return {"CANCELLED"}

        params = None
        for item in preset_param_sets(tree_name):
            if item["name"] == preset_name:
                params = item["params"]
                break
        if params is None:
            self.report({"WARNING"}, f"Unknown preset {preset_name}")
            return {"CANCELLED"}

        tree = bpy.data.node_groups.get(tree_name)
        stack = getattr(obj, "mel_gn_stack", None)
        if stack and 0 <= stack.active_index < len(stack.items):
            item = stack.items[stack.active_index]
            mod = obj.modifiers.get(item.modifier_name)
            if mod and getattr(mod, "node_group", None):
                tree = mod.node_group

        if tree is None:
            self.report({"WARNING"}, f"Node group {tree_name} not in scene - Add it first")
            return {"CANCELLED"}

        applied = 0
        items = []
        try:
            items = list(tree.interface.items_tree)
        except Exception:
            items = []
        for sock_name, value in params.items():
            target = None
            for it in items:
                if getattr(it, "name", None) == sock_name and getattr(it, "in_out", "") == "INPUT":
                    target = it
                    break
            if target is not None and hasattr(target, "default_value"):
                try:
                    target.default_value = value
                    applied += 1
                    continue
                except Exception:
                    pass
            for node in tree.nodes:
                if getattr(node, "type", "") != "GROUP_INPUT":
                    continue
                sock = None
                try:
                    sock = node.outputs.get(sock_name)
                except Exception:
                    sock = None
                if sock is None:
                    for s in node.outputs:
                        if s.name == sock_name:
                            sock = s
                            break
                if sock is not None and hasattr(sock, "default_value"):
                    try:
                        sock.default_value = value
                        applied += 1
                    except Exception:
                        pass
        self.report({"INFO"}, f"Applied {preset_name} ({applied} params) to {tree.name}")
        return {"FINISHED"}


class MEL_GN_OT_stack_add(Operator):
    """Add a GN modifier to the stack with the selected preset."""

    bl_idname = "mel_gn.stack_add"
    bl_label = "Add GN Modifier"
    bl_options = {"REGISTER", "UNDO"}

    tree_name: StringProperty(
        name="Tree",
        description="GN tree preset to add. Leave empty for quick-add dialog",
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({"WARNING"}, "No active object selected")
            return {"CANCELLED"}

        tree_name = self.tree_name
        if not tree_name and hasattr(self, "tree_enum"):
            tree_name = self.tree_enum

        nt = bpy.data.node_groups.get(tree_name)
        if not nt:
            # Try to build it on demand
            built = _build_tree_on_demand(tree_name)
            nt = built if built else None
            if nt is None:
                self.report({"ERROR"}, f"GN tree '{tree_name}' not found and could not be built")
                return {"CANCELLED"}

        mod = obj.modifiers.new(name=nt.name, type="NODES")
        mod.node_group = nt

        stack = getattr(obj, "mel_gn_stack", None)
        if stack is None:
            try:
                register_props()
            except Exception:
                pass
            stack = getattr(obj, "mel_gn_stack", None)
        if stack is not None:
            item = stack.items.add()
            item.name = nt.name
            item.modifier_name = mod.name
            item.tree_name = nt.name
            stack.active_index = len(stack.items) - 1
            item.expand = True

        self.report({"INFO"}, f"Added '{nt.name}' to modifier stack")
        return {"FINISHED"}


class MEL_GN_OT_stack_remove(Operator):
    """Remove selected GN modifier from the stack."""

    bl_idname = "mel_gn.stack_remove"
    bl_label = "Remove GN Modifier"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mel_gn_stack.items

    def execute(self, context):
        obj = context.active_object
        stack = obj.mel_gn_stack
        idx = stack.active_index
        if idx < 0 or idx >= len(stack.items):
            return {"CANCELLED"}
        item = stack.items[idx]

        mod = obj.modifiers.get(item.modifier_name)
        if mod:
            obj.modifiers.remove(mod)

        stack.items.remove(idx)
        stack.active_index = min(idx, len(stack.items) - 1)

        return {"FINISHED"}


class MEL_GN_OT_stack_move(Operator):
    """Move stack item up/down (also reorders the modifier stack)."""

    bl_idname = "mel_gn.stack_move"
    bl_label = "Move Modifier"
    bl_options = {"REGISTER", "UNDO"}

    direction: EnumProperty(
        name="Direction",
        items=[("UP", "Up", ""), ("DOWN", "Down", "")],
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mel_gn_stack.items

    def execute(self, context):
        obj = context.active_object
        stack = obj.mel_gn_stack
        idx = stack.active_index
        target = idx - 1 if self.direction == "UP" else idx + 1
        if target < 0 or target >= len(stack.items):
            return {"CANCELLED"}

        # Reorder stack items
        item = stack.items[idx]
        mod = obj.modifiers.get(item.modifier_name)
        if mod and hasattr(obj.modifiers, "move"):
            cur_mod_idx = list(obj.modifiers).index(mod)
            target_mod_idx = max(0, min(len(obj.modifiers) - 1, cur_mod_idx - 1 if self.direction == "UP" else cur_mod_idx + 1))
            try:
                obj.modifiers.move(cur_mod_idx, target_mod_idx)
            except Exception:
                pass

        stack.items.move(idx, target)
        stack.active_index = target
        return {"FINISHED"}


class MEL_GN_OT_stack_clear(Operator):
    """Remove all GN modifiers from the stack."""

    bl_idname = "mel_gn.stack_clear"
    bl_label = "Clear All Modifiers"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.mel_gn_stack.items

    def execute(self, context):
        obj = context.active_object
        stack = obj.mel_gn_stack
        for item in list(stack.items):
            mod = obj.modifiers.get(item.modifier_name)
            if mod:
                obj.modifiers.remove(mod)
        stack.items.clear()
        stack.active_index = 0
        return {"FINISHED"}


class MEL_GN_OT_stack_reveal_modifier(Operator):
    """Reveal this modifier in the modifier stack and select it."""

    bl_idname = "mel_gn.stack_reveal_modifier"
    bl_label = "Reveal Modifier"
    bl_options = {"REGISTER", "UNDO"}

    item_index: IntProperty(name="Item Index", default=0)

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        stack = obj.mel_gn_stack
        if self.item_index < 0 or self.item_index >= len(stack.items):
            return {"CANCELLED"}
        item = stack.items[self.item_index]
        mod = obj.modifiers.get(item.modifier_name)
        if mod:
            # Collapse all other modifiers, expand this one
            for m in obj.modifiers:
                m.show_expanded = (m == mod)
            # Move it to top of visibility
            try:
                obj.modifiers.active = mod
            except Exception:
                pass
        stack.active_index = self.item_index
        return {"FINISHED"}


class MEL_GN_OT_stack_toggle_enabled(Operator):
    """Toggle the enabled state of a stack modifier."""

    bl_idname = "mel_gn.stack_toggle_enabled"
    bl_label = "Toggle Enabled"
    bl_options = {"REGISTER", "UNDO"}

    item_index: IntProperty(name="Item Index", default=0)

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        stack = obj.mel_gn_stack
        if self.item_index < 0 or self.item_index >= len(stack.items):
            return {"CANCELLED"}
        item = stack.items[self.item_index]
        item.enabled = not item.enabled
        mod = obj.modifiers.get(item.modifier_name)
        if mod:
            mod.show_viewport = item.enabled
            mod.show_render = item.enabled
        return {"FINISHED"}


class MEL_GN_OT_stack_select_active(Operator):
    """Set the active stack item by index."""

    bl_idname = "mel_gn.stack_select_active"
    bl_label = "Select Stack Item"
    bl_options = {"REGISTER", "UNDO"}

    item_index: IntProperty(name="Item Index", default=0)

    def execute(self, context):
        obj = context.active_object
        if not obj:
            return {"CANCELLED"}
        stack = obj.mel_gn_stack
        if 0 <= self.item_index < len(stack.items):
            stack.active_index = self.item_index
        return {"FINISHED"}


class MEL_GN_OT_open_gn_editor(Operator):
    """Focus a NODE_EDITOR on the active MEL_* Geometry Nodes modifier."""

    bl_idname = "mel_gn.open_gn_editor"
    bl_label = "Open GN editor"
    bl_options = {"REGISTER"}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({"WARNING"}, "No active object")
            return {"CANCELLED"}
        tree = None
        stack = getattr(obj, "mel_gn_stack", None)
        if stack and 0 <= stack.active_index < len(stack.items):
            item = stack.items[stack.active_index]
            mod = obj.modifiers.get(item.modifier_name)
            if mod and getattr(mod, "node_group", None):
                tree = mod.node_group
        if tree is None:
            for mod in obj.modifiers:
                if getattr(mod, "type", "") != "NODES":
                    continue
                ng = getattr(mod, "node_group", None)
                if ng is not None and str(ng.name).startswith("MEL_"):
                    tree = ng
                    break
        if tree is None:
            self.report({"WARNING"}, "No MEL_* Geometry Nodes modifier on the object")
            return {"CANCELLED"}
        for window in context.window_manager.windows:
            screen = getattr(window, "screen", None)
            if screen is None:
                continue
            for area in screen.areas:
                if area.type != "NODE_EDITOR":
                    continue
                for space in area.spaces:
                    if space.type != "NODE_EDITOR":
                        continue
                    space.tree_type = "GeometryNodeTree"
                    space.node_tree = tree
                    try:
                        space.pin = True
                    except Exception:
                        pass
                    self.report({"INFO"}, f"Opened {tree.name}")
                    return {"FINISHED"}
        self.report({"INFO"}, "Split an editor to Geometry Node Editor, then click again")
        return {"CANCELLED"}


def _sync_stack_from_mel_modifiers(obj):
    """Keep GN Stack rows aligned with MEL_* NODES modifiers on the object."""
    stack = getattr(obj, "mel_gn_stack", None)
    if stack is None:
        return
    known = {item.modifier_name for item in stack.items}
    for mod in obj.modifiers:
        if getattr(mod, "type", "") != "NODES":
            continue
        ng = getattr(mod, "node_group", None)
        if ng is None or not str(ng.name).startswith("MEL_"):
            continue
        if mod.name in known:
            continue
        item = stack.items.add()
        item.name = ng.name
        item.modifier_name = mod.name
        item.tree_name = ng.name
        item.expand = True
    active_mod = getattr(obj.modifiers, "active", None)
    if active_mod is None or getattr(active_mod, "type", "") != "NODES":
        return
    ng = getattr(active_mod, "node_group", None)
    if ng is None or not str(ng.name).startswith("MEL_"):
        return
    for i, item in enumerate(stack.items):
        if item.modifier_name == active_mod.name:
            stack.active_index = i
            break


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Panel UI ΓÇö Melodia GN Stack (N-panel, nested under genome carousel)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

class MEL_GN_PT_stack(Panel):
    """Melodia GN Stack ΓÇö nested under Melodia Studio carousel."""

    bl_label = "GN Stack"
    bl_idname = "MEL_GN_PT_stack"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = N_PANEL_CATEGORY
    bl_parent_id = "SURREAL_ARCH_PT_genome_carousel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 13

    @classmethod
    def poll(cls, context):
        # Always show under Melodia Studio — categories must remain browsable
        # even before an object is selected (stack apply still needs an object).
        return True

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        # Catalog browser is always drawn from live core.TREE_* (post-rebuild).
        class _EmptyStack:
            filter_text = ""
            items = []
            active_index = 0

        stack = getattr(obj, "mel_gn_stack", None) if obj is not None else None
        if stack is None:
            layout.label(text="Select a mesh/curve to add GN builders", icon="INFO")
            wm = bpy.context.window_manager
            if hasattr(wm, "mel_gn_show_hidden"):
                layout.prop(wm, "mel_gn_show_hidden", text="Show hidden / factory clones")
            self._draw_tree_browser(layout, _EmptyStack())
            n_trees = len(_gn_core.TREE_TYPES)
            n_cats = sum(1 for c in _gn_core.TREE_CATEGORIES.values() if c.get("trees"))
            layout.label(text=f"Catalog: {n_trees} builders · {n_cats} sections", icon="NODETREE")
            return

        _sync_stack_from_mel_modifiers(obj)

        # ΓöÇΓöÇ Header row: search + stats ΓöÇΓöÇ
        self._draw_header(layout, stack)

        # ΓöÇΓöÇ Categorised tree browser ΓöÇΓöÇ
        self._draw_tree_browser(layout, stack)

        # ΓöÇΓöÇ Active stack items ΓöÇΓöÇ
        if stack.items:
            layout.separator(factor=0.4)
            self._draw_stack_items(layout, stack, obj)
            self._draw_presets(layout, stack)
        else:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="No modifiers on stack", icon="INFO")
            col.label(text="Choose a GN tree above to begin", icon="BLANK1")

        # ΓöÇΓöÇ Utility row ΓöÇΓöÇ
        if stack.items:
            row = layout.row(align=True)
            row.operator("mel_gn.stack_clear", text="Clear All", icon="TRASH")
            row.operator(
                "mel_gn.stack_add",
                text="Quick Add",
                icon="ADD",
            ).tree_name = "MEL_circular_array"

    # ΓöÇΓöÇ Sub-drawing helpers ΓöÇΓöÇ

    def _draw_header(self, layout, stack):
        """Search filter and stack count summary."""
        box = layout.box()
        col = box.column(align=True)

        # Filter row
        row = col.row(align=True)
        row.prop(stack, "filter_text", text="", icon="VIEWZOOM")
        if stack.filter_text:
            op = row.operator(
                "mel_gn.stack_add",
                text="",
                icon="ADD",
            )
            op.tree_name = stack.filter_text
        hide_row = col.row(align=True)
        wm = bpy.context.window_manager
        if hasattr(wm, "mel_gn_show_hidden"):
            hide_row.prop(wm, "mel_gn_show_hidden", text="Show hidden / factory clones")

        # Stats row
        item_count = len(stack.items)
        if item_count:
            row = col.row(align=True)
            row.label(text=f"Stack: {item_count} modifier{'s' if item_count != 1 else ''}", icon="MODIFIER")
            if stack.active_index < item_count:
                active_item = stack.items[stack.active_index]
                category_id = _gn_core.TREE_CATEGORY_MAP.get(active_item.tree_name)
                if category_id:
                    cat_info = _gn_core.TREE_CATEGORIES.get(category_id, {})
                    row.label(text=f"  |  {cat_info.get('label', '')}", icon=cat_info.get("icon", "DOT"))

    def _draw_tree_browser(self, layout, stack):
        """Draw categorised tree browser with search filtering."""
        ft = stack.filter_text
        from ..icon_loader import icon_kwargs

        # ΓöÇΓöÇ Compact add bar ΓöÇΓöÇ
        row = layout.row(align=True)
        row.operator("mel_gn.stack_add", text="Add Modifier", icon="ADD")
        if not ft:
            op = row.operator("mel_gn.stack_add", text="", icon="SHADERFX")
            op.tree_name = "MEL_circular_array"

        # ΓöÇΓöÇ Categorised sections ΓöÇΓöÇ
        box = layout.box()
        any_visible = False
        for category_id, cat_info in _gn_core.TREE_CATEGORIES.items():
            trees = cat_info["trees"]
            # Skip empty category shells (keeps panel focused on live sections)
            if not trees and not ft:
                continue
            # Filter
            if ft:
                matching = [t for t in trees if _filter_tree(t, ft)]
                if not matching:
                    continue
            else:
                matching = trees
            show_hidden = bool(getattr(bpy.context.window_manager, "mel_gn_show_hidden", False))
            if not show_hidden:
                matching = [t for t in matching if not _gn_core.is_hidden_builder(t)]
            if not matching:
                continue

            any_visible = True
            col = box.column(align=True)

            # Category header
            header = col.row(align=True)
            n_match = len(matching)
            n_total = len(trees)
            header.label(
                text=f"{cat_info['label']}  ({n_match}/{n_total})",
                icon=cat_info["icon"],
            )

            # Tree buttons for this category
            flow = col.box()
            sub = flow.column(align=True)
            for i, tree_name in enumerate(matching):
                display_label = _gn_core.TREE_LABEL_MAP.get(tree_name, tree_name)
                desc = _gn_core.TREE_DESCRIPTIONS.get(tree_name, "")
                exists = tree_name in bpy.data.node_groups
                status_icon = "CHECKBOX_HLT" if exists else "CHECKBOX_DEHLT"

                btn_row = sub.row(align=True)
                op = btn_row.operator(
                    "mel_gn.stack_add",
                    text=display_label,
                    icon=cat_info.get("icon", "GEOMETRY_NODES"),
                    depress=False,
                )
                op.tree_name = tree_name

                # Status indicator (Green check if node group is built in memory)
                btn_row.label(text="", icon=status_icon)

        if not any_visible and ft:
            col = box.column(align=True)
            col.label(text=f"No trees match '{ft}'", icon="ERROR")


    def _draw_presets(self, layout, stack):
        """Curated presets for the active stack item's builder."""
        if not stack.items or stack.active_index < 0 or stack.active_index >= len(stack.items):
            return
        item = stack.items[stack.active_index]
        tree_name = item.tree_name
        try:
            from .presets import preset_param_sets, BUILDERS_PRESETS
        except Exception:
            return
        if tree_name not in BUILDERS_PRESETS:
            return
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Presets", icon="PRESET")
        for preset in preset_param_sets(tree_name):
            row = col.row(align=True)
            op = row.operator(
                "mel_gn.apply_preset",
                text=preset.get("label", preset["name"]),
                icon="CHECKMARK",
            )
            op.tree_name = tree_name
            op.preset_name = preset["name"]

    def _draw_stack_items(self, layout, stack, obj):
        """Draw stack items ΓÇö each is one GN modifier on the object."""
        box = layout.box()
        col = box.column(align=True)

        # Header
        row = col.row(align=True)
        row.label(text="Active Modifiers", icon="MODIFIER_DATA")

        # Items
        for i, item in enumerate(stack.items):
            is_active = (i == stack.active_index)
            mod = obj.modifiers.get(item.modifier_name)
            category_id = _gn_core.TREE_CATEGORY_MAP.get(item.tree_name, "")
            cat_info = _gn_core.TREE_CATEGORIES.get(category_id, {})

            # ΓöÇΓöÇ Item row ΓöÇΓöÇ
            item_box = col.box()
            if is_active:
                item_box = item_box.column()
                item_box = item_box.box()  # Double-box highlight

            # Top row: label + controls
            top_row = item_box.row(align=True)

            # Expand/collapse
            expand_icon = "DOWNARROW_HLT" if item.expand else "RIGHTARROW"
            top_row.prop(item, "expand", text="", icon=expand_icon, emboss=False)

            # Index badge
            top_row.label(text=str(i + 1))

            # Name field
            if is_active:
                top_row.prop(item, "name", text="")
            else:
                op = top_row.operator(
                    "mel_gn.stack_select_active",
                    text=item.name,
                    emboss=False,
                )
                op.item_index = i

            # Category tag
            if cat_info:
                top_row.label(text=cat_info.get("label", ""), icon=cat_info.get("icon", "DOT"))

            # Enabled toggle
            if item.enabled:
                op = top_row.operator(
                    "mel_gn.stack_toggle_enabled",
                    text="",
                    icon="HIDE_OFF",
                    emboss=False,
                )
            else:
                op = top_row.operator(
                    "mel_gn.stack_toggle_enabled",
                    text="",
                    icon="HIDE_ON",
                    emboss=False,
                    depress=True,
                )
            op.item_index = i

            # Reveal modifier button
            op = top_row.operator(
                "mel_gn.stack_reveal_modifier",
                text="",
                icon="RESTRICT_SELECT_OFF" if mod else "RESTRICT_SELECT_ON",
                emboss=False,
            )
            op.item_index = i

            # ΓöÇΓöÇ Expanded info ΓöÇΓöÇ
            if item.expand:
                info_col = item_box.column(align=True)

                # Description
                desc = _gn_core.TREE_DESCRIPTIONS.get(item.tree_name, "")
                if desc:
                    info_col.label(text=desc, icon="INFO")

                if is_active and item.tree_name.startswith("MEL_"):
                    info_col.operator(
                        "mel_gn.open_gn_editor",
                        text="Open GN editor",
                        icon="NODETREE",
                    )

                # Status line
                status_row = info_col.row(align=True)
                if mod:
                    status_row.label(text=f"Modifier: {mod.name}", icon="MODIFIER")
                else:
                    status_row.label(text="Modifier missing!", icon="ERROR")

                if category_id:
                    status_row.label(text=cat_info.get("label", category_id), icon=cat_info.get("icon", "DOT"))

            # ΓöÇΓöÇ Move/remove controls row ΓöÇΓöÇ
            ctrl_row = item_box.row(align=True)

            # Move up
            if i > 0:
                op = ctrl_row.operator(
                    "mel_gn.stack_move",
                    text="",
                    icon="TRIA_UP",
                )
                op.direction = "UP"
            else:
                ctrl_row.label(text="", icon="BLANK1")

            # Move down
            if i < len(stack.items) - 1:
                op = ctrl_row.operator(
                    "mel_gn.stack_move",
                    text="",
                    icon="TRIA_DOWN",
                )
                op.direction = "DOWN"
            else:
                ctrl_row.label(text="", icon="BLANK1")

            # Remove
            op = ctrl_row.operator(
                "mel_gn.stack_remove",
                text="",
                icon="X",
                emboss=False,
            )

            # Spacer
            ctrl_row.label(text="")


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Helpers
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

from .core import GROUP_BUILDERS as _GB

def _build_tree_on_demand(tree_name: str):
    """Try to build a single GN tree by name via GROUP_BUILDERS or imports."""
    from . import bake as _bake_mod
    builders = getattr(_bake_mod, "builders", None)
    # Walk bake module's internal list
    import importlib
    try:
        src = importlib.import_module("." + tree_name.split("_")[0], package="surreal_arch.melodia_gn")
    except Exception:
        src = None

    if _GB:
        builder = _GB.get(tree_name)
        if builder:
            try:
                return builder(tree_name)
            except Exception:
                return None
    return None


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Registration helpers
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

CLASSES = [
    MEL_GN_StackItem,
    MEL_GN_StackSettings,
    MEL_GN_OT_apply_preset,
    MEL_GN_OT_stack_add,
    MEL_GN_OT_stack_remove,
    MEL_GN_OT_stack_move,
    MEL_GN_OT_stack_clear,
    MEL_GN_OT_stack_reveal_modifier,
    MEL_GN_OT_stack_toggle_enabled,
    MEL_GN_OT_stack_select_active,
    MEL_GN_OT_open_gn_editor,
    MEL_GN_PT_stack,
]


def register_props():
    if not hasattr(bpy.types.Object, "mel_gn_stack"):
        bpy.types.Object.mel_gn_stack = PointerProperty(
            type=MEL_GN_StackSettings,
            name="Melodia GN Stack",
        )
    if not hasattr(bpy.types.WindowManager, "mel_gn_show_hidden"):
        bpy.types.WindowManager.mel_gn_show_hidden = BoolProperty(
            name="Show hidden / factory clones",
            description="Show hidden factory clones (them_* / PCG aliases) in the GN Stack browser",
            default=False,
        )


def unregister_props():
    try:
        del bpy.types.Object.mel_gn_stack
    except AttributeError:
        pass
    try:
        del bpy.types.WindowManager.mel_gn_show_hidden
    except AttributeError:
        pass
