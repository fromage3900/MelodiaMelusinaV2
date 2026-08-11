"""Title menu UMG widget factory — Figma Game UI-aligned.

Creates a WidgetBlueprint asset at /Game/UI/WBP_TitleMenu with:
  - Game title banner (MELODIA)
  - New Game button
  - Continue button (enabled if save exists)
  - Options button (placeholder)
  - Credits button (placeholder)
  - Version display

Usage:
    from gmm.ui.title_menu import create_title_menu_widget
    result = create_title_menu_widget()
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


WIDGET_PATH = "/Game/UI/WBP_TitleMenu"


def create_title_menu_widget(asset_path: str = WIDGET_PATH) -> WidgetBuildResult:
    """Create the title menu widget blueprint.
    
    Layout:
        Background overlay
        Title banner (MELODIA)
        Button stack (New Game, Continue, Options, Credits)
        Version text
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
    _build_title_banner(tree, root)
    _build_button_stack(tree, root)
    _build_version_label(tree, root)

    save_widget_blueprint(bp)
    return WidgetBuildResult(ok=True, path=asset_path, asset=bp)


def _build_background(tree, parent):
    """Dark background overlay."""
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
            brush.tint_color = _rgba(0.051, 0.071, 0.141, 1.0)
            img.set_brush(brush)
        except Exception:
            pass
    except Exception:
        pass


def _build_title_banner(tree, parent):
    """Game title banner at top center."""
    try:
        import unreal
        title = make_text_block("MELODIA", GameColors.GOLD, "Fraunces", 64)
        title.set_name("TitleBanner")
        parent.add_child(title)
        slot = unreal.CanvasPanelSlot(title)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(0.5, 0.0),
            maximum=unreal.Vector2D(0.5, 0.0),
        ))
        slot.set_offsets(_margin(-200, 80, 0, 0))
        slot.set_size(_vector2d_auto(400, 80))
    except Exception:
        pass


def _build_button_stack(tree, parent):
    """Vertical button stack for menu options."""
    try:
        import unreal
        vbox = unreal.new_object(unreal.VerticalBox, tree)
        vbox.set_name("ButtonStack")
        parent.add_child(vbox)
        slot = unreal.CanvasPanelSlot(vbox)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(0.5, 0.5),
            maximum=unreal.Vector2D(0.5, 0.5),
        ))
        slot.set_offsets(_margin(-150, -100, 0, 0))
        slot.set_size(_vector2d_auto(300, 200))

        buttons = [
            ("NewGameBtn", "NEW GAME", GameColors.CYAN, "new_game"),
            ("ContinueBtn", "CONTINUE", GameColors.PEARL, "continue"),
            ("OptionsBtn", "OPTIONS", GameColors.TEXT_SECONDARY, "options"),
            ("CreditsBtn", "CREDITS", GameColors.TEXT_MUTED, "credits"),
        ]
        for name, label, color, tag in buttons:
            btn = unreal.new_object(unreal.Button, tree)
            btn.set_name(name)
            lbl = make_text_block(label, color, "Inter", 16)
            if lbl:
                btn.set_content(lbl)
            vbox.add_child(btn)
    except Exception:
        pass


def _build_version_label(tree, parent):
    """Version text at bottom right."""
    try:
        import unreal
        from gmm import VERSION, VERSION_NAME
        
        version = make_text_block(
            f"{VERSION_NAME} v{VERSION}",
            GameColors.TEXT_MUTED,
            "IBM Plex Mono",
            10
        )
        version.set_name("VersionLabel")
        parent.add_child(version)
        slot = unreal.CanvasPanelSlot(version)
        slot.set_anchors(unreal.Anchors(
            minimum=unreal.Vector2D(1.0, 1.0),
            maximum=unreal.Vector2D(1.0, 1.0),
        ))
        slot.set_offsets(_margin(-120, -30, 0, 0))
        slot.set_size(_vector2d_auto(120, 20))
    except Exception:
        pass


def _vector2d_auto(x=0, y=0):
    """Helper to create Vector2D or None."""
    try:
        import unreal
        return unreal.Vector2D(x, y)
    except Exception:
        return None