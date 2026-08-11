"""Victory/Defeat screen UMG widget factory — Figma Game UI-aligned.

Creates a WidgetBlueprint asset at /Game/UI/Battle/WBP_VictoryScreen
with:
  - result banner (Victory! / Defeat...)
  - grade summary (Perfect/Great/Good/Miss counts)
  - reward stub (XP, loot placeholder)
  - auto-dismiss countdown

Usage:
    from gmm.ui.victory_screen import create_victory_screen_widget
    result = create_victory_screen_widget()
"""
from __future__ import annotations

from gmm.ui.colors import GameColors
from gmm.ui.builder import (
    WidgetBuildResult,
    new_widget_blueprint,
    set_widget_tree_root,
    make_text_block,
    make_progress_bar,
    make_button,
    save_widget_blueprint,
    _rgba,
    _margin,
)


WIDGET_PATH = "/Game/UI/Battle/WBP_VictoryScreen"


def create_victory_screen_widget(asset_path: str = WIDGET_PATH) -> WidgetBuildResult:
    """Create the victory/defeat screen widget blueprint.

    Layout:
        Frame overlay
        Victory/Defeat title centered
        Grade count row (P / G / G / M)
        Reward stub (XP, Loot)
        "Return to World" countdown/button
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

    canvas = unreal.CanvasPanelSlot(root)
    canvas.set_auto_size(False)
    canvas.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 1.0),
    ))
    canvas.set_offsets(_margin(0, 0, 0, 0))

    _build_overlay(tree, root)
    _build_title(tree, root)
    _build_grade_summary(tree, root)
    _build_reward_stub(tree, root)
    _build_countdown(tree, root)

    save_widget_blueprint(bp)
    return WidgetBuildResult(ok=True, path=asset_path, asset=bp)


def _build_overlay(tree, parent):
    """Semi-transparent overlay to dim the game view."""
    img = unreal.new_object(unreal.Image, tree)
    img.set_name("Overlay")
    parent.add_child(img)
    slot = unreal.CanvasPanelSlot(img)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 1.0),
    ))
    slot.set_offsets(_margin(0, 0, 0, 0))
    try:
        brush = unreal.SlateBrush()
        brush.tint_color = _rgba(0.051, 0.071, 0.141, 0.75)
        img.set_brush(brush)
    except Exception:
        pass


def _build_title(tree, parent):
    """Victory! or Defeat... title text."""
    title = make_text_block("VICTORY!", GameColors.GOLD, "Fraunces", 42)
    title.set_name("ResultTitle")
    parent.add_child(title)
    slot = unreal.CanvasPanelSlot(title)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.5, 0.0),
        maximum=unreal.Vector2D(0.5, 0.0),
    ))
    slot.set_offsets(_margin(-120, 80, 0, 0))
    slot.set_size(_vector2d_auto(240, 50))

    subtitle = make_text_block("Encounter Complete", GameColors.TEXT_SECONDARY, "IBM Plex Mono", 11)
    subtitle.set_name("ResultSubtitle")
    parent.add_child(subtitle)
    slot2 = unreal.CanvasPanelSlot(subtitle)
    slot2.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.5, 0.0),
        maximum=unreal.Vector2D(0.5, 0.0),
    ))
    slot2.set_offsets(_margin(-120, 135, 0, 0))
    slot2.set_size(_vector2d_auto(240, 20))


def _build_grade_summary(tree, parent):
    """Grade count row: PERFECT | GREAT | GOOD | MISS."""
    grade_box = unreal.new_object(unreal.HorizontalBox, tree)
    grade_box.set_name("GradeSummary")
    parent.add_child(grade_box)
    slot = unreal.CanvasPanelSlot(grade_box)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.5, 0.0),
        maximum=unreal.Vector2D(0.5, 0.0),
    ))
    slot.set_offsets(_margin(-160, 180, 0, 0))
    slot.set_size(_vector2d_auto(320, 30))

    grades = [
        ("PERFECT", GameColors.JUDGE_PERFECT),
        ("GREAT", GameColors.JUDGE_GREAT),
        ("GOOD", GameColors.JUDGE_GOOD),
        ("MISS", GameColors.JUDGE_MISS),
    ]
    for label, color in grades:
        g = make_text_block(f"{label}: 0", color, "IBM Plex Mono", 10)
        grade_box.add_child(g)


def _build_reward_stub(tree, parent):
    """Reward stub: XP +50, Loot placeholder."""
    vbox = unreal.new_object(unreal.VerticalBox, tree)
    vbox.set_name("RewardStub")
    parent.add_child(vbox)
    slot = unreal.CanvasPanelSlot(vbox)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.5, 0.0),
        maximum=unreal.Vector2D(0.5, 0.0),
    ))
    slot.set_offsets(_margin(-120, 230, 0, 0))
    slot.set_size(_vector2d_auto(240, 60))

    xp = make_text_block("XP +50", GameColors.CYAN, "Fraunces", 18)
    xp.set_name("XPGain")
    vbox.add_child(xp)

    loot = make_text_block("Loot: — None yet —", GameColors.TEXT_MUTED, "IBM Plex Mono", 10)
    loot.set_name("LootText")
    vbox.add_child(loot)


def _build_countdown(tree, parent):
    """Auto-return countdown or button."""
    countdown = make_text_block("Returning to world in 3...", GameColors.TEXT_SECONDARY, "IBM Plex Mono", 11)
    countdown.set_name("CountdownLabel")
    parent.add_child(countdown)
    slot = unreal.CanvasPanelSlot(countdown)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.5, 1.0),
        maximum=unreal.Vector2D(0.5, 1.0),
    ))
    slot.set_offsets(_margin(-120, -40, 0, 0))
    slot.set_size(_vector2d_auto(240, 20))


def _vector2d_auto(x=0, y=0):
    try:
        import unreal
        return unreal.Vector2D(x, y)
    except ImportError:
        return None
