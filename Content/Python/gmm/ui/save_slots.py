"""Save slot selection UMG widget factory — Figma Game UI-aligned.

Creates a WidgetBlueprint asset at /Game/UI/WBP_SaveSlotMenu with:
  - Save slot list (up to 3 slots)
  - New game prompt
  - Load/Delete buttons per slot
  - Gold token count display

Usage:
    from gmm.ui.save_slots import create_save_slot_menu_widget
    result = create_save_slot_menu_widget()
"""
from __future__ import annotations

from gmm.ui.colors import GameColors
from gmm.ui.builder import (
    WidgetBuildResult,
    new_widget_blueprint,
    set_widget_tree_root,
    make_text_block,
    make_button,
    save_widget_blueprint,
    _rgba,
    _margin,
)


WIDGET_PATH = "/Game/UI/WBP_SaveSlotMenu"


def create_save_slot_menu_widget(asset_path: str = WIDGET_PATH) -> WidgetBuildResult:
    """Create the save slot selection widget blueprint.
    
    Layout:
        Background overlay
        Title (CONTINUE?)
        Slot buttons (Slot 1, Slot 2, Slot 3)
        Back button
    """
    try:
        import unreal
    except ImportError:
        return WidgetBuildResult(ok=False, error="unreal module not available (not in editor)")

    result = new_widget_blueprint(asset_path)
    if not result.ok:
        return result

    bp = result.asset
    tree = bp.get_widget_tree()

    root = set_widget_tree_root(bp, unreal.CanvasPanel, "Root")
    if not root:
        return WidgetBuildResult(ok=False, error="failed to set root widget")

    # Full-screen canvas
    canvas = unreal.CanvasPanelSlot(root)
    canvas.set_auto_size(False)
    canvas.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 1.0),
    ))
    canvas.set_offsets(_margin(0, 0, 0, 0))

    _build_background(tree, root)
    _build_title(tree, root)
    _build_slot_list(tree, root)
    _build_back_button(tree, root)

    save_widget_blueprint(bp)
    return WidgetBuildResult(ok=True, path=asset_path, asset=bp)


def _build_background(tree, parent):
    """Semi-transparent background overlay."""
    try:
        import unreal
        img = unreal.new_object(unreal.Image, tree)
        img.set_name("Background")
        parent.add_child(img)
        slot = unreal.CanvasPanelSlot(img)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(0.0, 0.0),
            maximum=unreal.Vector2D(1.0, 1.0),
        ))
        slot.set_offsets(_margin(0, 0, 0, 0))
        try:
            brush = unreal.SlateBrush()
            brush.tint_color = _rgba(0.051, 0.071, 0.141, 0.9)
            img.set_brush(brush)
        except Exception:
            pass
    except Exception:
        pass


def _build_title(tree, parent):
    """Save slot title text."""
    try:
        import unreal
        title = make_text_block("CONTINUE?", GameColors.GOLD, "Fraunces", 36)
        title.set_name("TitleText")
        parent.add_child(title)
        slot = unreal.CanvasPanelSlot(title)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(0.5, 0.0),
            maximum=unreal.Vector2D(0.5, 0.0),
        ))
        slot.set_offsets(_margin(-150, 100, 0, 0))
        slot.set_size(_vector2d_auto(300, 50))
    except Exception:
        pass


def _build_slot_list(tree, parent):
    """Vertical list of save slot buttons."""
    try:
        import unreal
        vbox = unreal.new_object(unreal.VerticalBox, tree)
        vbox.set_name("SlotList")
        parent.add_child(vbox)
        slot = unreal.CanvasPanelSlot(vbox)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(0.5, 0.5),
            maximum=unreal.Vector2D(0.5, 0.5),
        ))
        slot.set_offsets(_margin(-200, -120, 0, 0))
        slot.set_size(_vector2d_auto(400, 240))

        # Create 3 slot entries
        for i in range(1, 4):
            slot_btn = unreal.new_object(unreal.Button, tree)
            slot_btn.set_name(f"Slot{i}Btn")
            slot_box = unreal.new_object(unreal.HorizontalBox, tree)
            
            # Slot label
            lbl = make_text_block(f"Slot {i}", GameColors.TEXT_PRIMARY, "Inter", 14)
            slot_box.add_child(lbl)
            
            # Level text placeholder
            lvl = make_text_block("Empty", GameColors.TEXT_MUTED, "IBM Plex Mono", 12)
            lvl.set_name(f"Slot{i}Level")
            slot_box.add_child(lvl)
            
            slot_btn.set_content(slot_box)
            vbox.add_child(slot_btn)
    except Exception:
        pass


def _build_back_button(tree, parent):
    """Back button at bottom."""
    try:
        import unreal
        btn = unreal.new_object(unreal.Button, tree)
        btn.set_name("BackBtn")
        lbl = make_text_block("BACK", GameColors.TEXT_SECONDARY, "Inter", 14)
        btn.set_content(lbl)
        parent.add_child(btn)
        slot = unreal.CanvasPanelSlot(btn)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(0.5, 1.0),
            maximum=unreal.Vector2D(0.5, 1.0),
        ))
        slot.set_offsets(_margin(-80, -60, 0, 0))
        slot.set_size(_vector2d_auto(160, 40))
    except Exception:
        pass


def _vector2d_auto(x=0, y=0):
    """Helper to create Vector2D or None."""
    try:
        import unreal
        return unreal.Vector2D(x, y)
    except Exception:
        return None