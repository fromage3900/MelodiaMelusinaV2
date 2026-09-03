"""Battle command menu UMG widget factory — Figma Game UI-aligned.

Creates a WidgetBlueprint asset at /Game/UI/Battle/WBP_BattleCommandMenu
with the full battle HUD layout:
  - topbar (phase + combo)
  - enemy card (name, HP, toughness, element)
  - player meters (HP, SP, Ultimate)
  - command skill grid (6 buttons)
  - dialogue area
  - rhythm lane hints

Usage:
    from gmm.ui.battle_menu import create_battle_menu_widget
    result = create_battle_menu_widget()
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


WIDGET_PATH = "/Game/UI/Battle/WBP_BattleCommandMenu"


def create_battle_menu_widget(asset_path: str = WIDGET_PATH) -> WidgetBuildResult:
    """Create the battle command menu widget blueprint.

    Layout (vertical stack):
        Topbar (phase | combo)
        Enemy Card Area
        Player Meter Row (HP | SP | Ult)
        Skill Command Grid (2x3 buttons)
        Dialogue / Hint Area
        Lane Hint Bar
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

    _build_topbar(tree, root)
    _build_enemy_card(tree, root)
    _build_player_meters(tree, root)
    _build_skill_grid(tree, root)
    _build_dialogue_area(tree, root)
    _build_lane_hints(tree, root)

    save_widget_blueprint(bp)
    return WidgetBuildResult(ok=True, path=asset_path, asset=bp)


def _build_topbar(tree, parent):
    """Phase + combo bar across the top."""
    box = unreal.new_object(unreal.HorizontalBox, tree)
    box.set_name("Topbar")
    parent.add_child(box)
    slot = unreal.CanvasPanelSlot(box)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 0.0),
    ))
    slot.set_offsets(_margin(0, 0, 0, 0))
    slot.set_size(_vector2d_auto(0, 36))

    phase_label = make_text_block("PHASE: AWAITING", GameColors.CYAN, "IBM Plex Mono", 11)
    phase_label.set_name("PhaseLabel")
    box.add_child(phase_label)

    combo_label = make_text_block("COMBO x 0", GameColors.GOLD, "Fraunces", 16)
    combo_label.set_name("ComboLabel")
    box.add_child(combo_label)


def _build_enemy_card(tree, parent):
    """Enemy display card with name, HP bar, toughness bar, element."""
    vbox = unreal.new_object(unreal.VerticalBox, tree)
    vbox.set_name("EnemyCard")
    parent.add_child(vbox)
    slot = unreal.CanvasPanelSlot(vbox)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 0.0),
    ))
    slot.set_offsets(_margin(12, 44, 12, 0))
    slot.set_size(_vector2d_auto(0, 100))

    name_label = make_text_block("ENEMY NAME", GameColors.PEARL, "Fraunces", 18)
    name_label.set_name("EnemyName")
    vbox.add_child(name_label)

    hp_bar = make_progress_bar(1.0, GameColors.HP_FILL, GameColors.HP_BG, "EnemyHPBar")
    vbox.add_child(hp_bar)

    toughness_bar = make_progress_bar(1.0, GameColors.TOUGHNESS_FILL, GameColors.TRACK_BG, "ToughnessBar")
    vbox.add_child(toughness_bar)

    element_label = make_text_block("ELEMENT", GameColors.GOLD, "IBM Plex Mono", 10)
    element_label.set_name("ElementLabel")
    vbox.add_child(element_label)


def _build_player_meters(tree, parent):
    """Player HP, SP, Ultimate bars in a row."""
    hbox = unreal.new_object(unreal.HorizontalBox, tree)
    hbox.set_name("PlayerMeters")
    parent.add_child(hbox)
    slot = unreal.CanvasPanelSlot(hbox)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 0.0),
    ))
    slot.set_offsets(_margin(12, 152, 12, 0))
    slot.set_size(_vector2d_auto(0, 28))

    hp = make_progress_bar(0.75, GameColors.HP_FILL, GameColors.TRACK_BG, "PlayerHP")
    hp.set_name("PlayerHPBar")
    hbox.add_child(hp)

    sp = make_progress_bar(0.5, GameColors.SP_FILL, GameColors.TRACK_BG, "PlayerSP")
    sp.set_name("PlayerSPBar")
    hbox.add_child(sp)

    ult = make_progress_bar(0.3, GameColors.ULT_FILL, GameColors.TRACK_BG, "PlayerUlt")
    ult.set_name("PlayerUltBar")
    hbox.add_child(ult)

    sp_label = make_text_block("SP", GameColors.CYAN, "IBM Plex Mono", 9)
    sp_label.set_name("SPLabel")
    hbox.add_child(sp_label)


def _build_skill_grid(tree, parent):
    """2x3 skill command grid."""
    grid = unreal.new_object(unreal.GridPanel, tree)
    grid.set_name("SkillGrid")
    parent.add_child(grid)
    slot = unreal.CanvasPanelSlot(grid)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 0.0),
    ))
    slot.set_offsets(_margin(12, 188, 12, 0))
    slot.set_size(_vector2d_auto(0, 120))

    skill_names = ["Basic Attack", "Skill 1", "Skill 2", "Skill 3", "Skill 4", "Ultimate"]
    for i, name in enumerate(skill_names):
        btn = unreal.new_object(unreal.Button, tree)
        btn.set_name(f"SkillBtn_{i}")
        lbl = make_text_block(name, GameColors.TEXT_PRIMARY, "Inter", 11)
        if lbl:
            btn.set_content(lbl)
        grid.add_child(btn)
        gslot = unreal.GridSlot(btn)
        gslot.set_row(i // 3)
        gslot.set_column(i % 3)


def _build_dialogue_area(tree, parent):
    """Enemy dialogue / telegraph text area."""
    dialogue = make_text_block(
        "Enemy telegraph area...",
        GameColors.TEXT_SECONDARY, "Fraunces", 13, name="DialogueArea",
    )
    dialogue.set_name("DialogueArea")
    parent.add_child(dialogue)
    slot = unreal.CanvasPanelSlot(dialogue)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 0.0),
        maximum=unreal.Vector2D(1.0, 0.0),
    ))
    slot.set_offsets(_margin(12, 316, 12, 0))
    slot.set_size(_vector2d_auto(0, 40))


def _build_lane_hints(tree, parent):
    """Rhythm lane keyboard hints at the bottom."""
    hbox = unreal.new_object(unreal.HorizontalBox, tree)
    hbox.set_name("LaneHints")
    parent.add_child(hbox)
    slot = unreal.CanvasPanelSlot(hbox)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(0.0, 1.0),
        maximum=unreal.Vector2D(1.0, 1.0),
    ))
    slot.set_offsets(_margin(12, 0, 12, 8))
    slot.set_size(_vector2d_auto(0, 24))

    for key, color in zip(GameColors.LANE_KEYS, GameColors.LANE_COLORS):
        hint = make_text_block(f"[{key}]", color, "IBM Plex Mono", 10)
        hbox.add_child(hint)


def _vector2d_auto(x=0, y=0):
    try:
        import unreal
        return unreal.Vector2D(x, y)
    except ImportError:
        return None
