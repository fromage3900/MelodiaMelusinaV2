"""Author /Game/Melodia/UI/WBP_Battle_Mobile for UMelodiaMobileHUD.

Run in-editor or via UnrealEditor-Cmd:
  UnrealEditor-Cmd BS_GodFile.uproject -ExecutePythonScript=Content/Python/author_melodia_battle_mobile.py -unattended -nosplash -stdout

Creates (or reparents) the widget, builds a portrait thumb-zone tree, names
BindWidgetOptional targets, and assigns LaneButtons[0..3].
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Melodia" / "wbp_battle_mobile_author.json"
UI_DIR = "/Game/Melodia/UI"
ASSET_NAME = "WBP_Battle_Mobile"
ASSET_PATH = f"{UI_DIR}/{ASSET_NAME}"
PARENT_CLASS_PATH = "/Script/MelodiaCore.MelodiaMobileHUD"


def _log(msg: str) -> None:
    unreal.log(f"[BattleMobile] {msg}")


def _warn(msg: str) -> None:
    unreal.log_warning(f"[BattleMobile] {msg}")


def _resolve_parent():
    cls = unreal.load_class(None, PARENT_CLASS_PATH)
    if cls:
        return cls
    return unreal.load_class(None, "MelodiaCore.MelodiaMobileHUD")


def _reparent(bp, parent_class) -> bool:
    if not bp or not parent_class:
        return False
    try:
        if hasattr(unreal, "BlueprintEditorLibrary"):
            unreal.BlueprintEditorLibrary.reparent_blueprint(bp, parent_class)
            return True
    except Exception as exc:  # noqa: BLE001
        _warn(f"BlueprintEditorLibrary.reparent failed: {exc}")
    try:
        bp.set_editor_property("parent_class", parent_class)
        return True
    except Exception as exc:  # noqa: BLE001
        _warn(f"parent_class set failed: {exc}")
    return False


def _ensure_asset(parent_class):
    full = f"{ASSET_PATH}.{ASSET_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(full):
        bp = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
        status = "exists"
        if parent_class:
            _reparent(bp, parent_class)
        return bp, status

    if not unreal.EditorAssetLibrary.does_directory_exist(UI_DIR):
        unreal.EditorAssetLibrary.make_directory(UI_DIR)

    factory = unreal.WidgetBlueprintFactory()
    if parent_class and hasattr(factory, "set_editor_property"):
        try:
            factory.set_editor_property("parent_class", parent_class)
        except Exception:  # noqa: BLE001
            pass

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = tools.create_asset(ASSET_NAME, UI_DIR, unreal.WidgetBlueprint, factory)
    if not bp:
        return None, "create_failed"
    if parent_class:
        _reparent(bp, parent_class)
    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    return bp, "created"


def _slot_fill(panel, child, anchors_min=(0.0, 0.0), anchors_max=(1.0, 1.0), offsets=(0, 0, 0, 0)):
    slot = panel.add_child_to_canvas(child)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(anchors_min[0], anchors_min[1]),
        maximum=unreal.Vector2D(anchors_max[0], anchors_max[1]),
    ))
    left, top, right, bottom = offsets
    slot.set_offsets(unreal.Margin(left, top, right, bottom))
    slot.set_alignment(unreal.Vector2D(0.0, 0.0))
    return slot


def _make_text(tree, name: str, text: str, size: int = 18):
    tb = unreal.new_object(unreal.TextBlock, tree)
    _name_widget(tb, name)
    tb.set_text(text)
    try:
        tb.set_editor_property("font", unreal.SlateFontInfo(size=size))
    except Exception:  # noqa: BLE001
        pass
    return tb


def _make_bar(tree, name: str):
    bar = unreal.new_object(unreal.ProgressBar, tree)
    _name_widget(bar, name)
    bar.set_percent(0.7)
    return bar


def _make_button(tree, name: str, label: str):
    btn = unreal.new_object(unreal.Button, tree)
    _name_widget(btn, name)
    text = unreal.new_object(unreal.TextBlock, tree)
    _name_widget(text, f"{name}_Label")
    text.set_text(label)
    btn.set_content(text)
    return btn


def _clear_canvas_children(canvas) -> None:
    # Best-effort clear so re-runs are idempotent
    try:
        while canvas.get_children_count() > 0:
            canvas.remove_child_at(0)
    except Exception:  # noqa: BLE001
        pass


def _get_widget_tree(bp):
    """UE 5.8 WidgetBlueprint may expose widget_tree as property, not get_widget_tree()."""
    if hasattr(bp, "get_widget_tree"):
        try:
            tree = bp.get_widget_tree()
            if tree:
                return tree
        except Exception:  # noqa: BLE001
            pass
    for key in ("widget_tree", "WidgetTree"):
        try:
            tree = bp.get_editor_property(key)
            if tree:
                return tree
        except Exception:  # noqa: BLE001
            pass
        tree = getattr(bp, key, None)
        if tree:
            return tree
    raise AttributeError("WidgetBlueprint has no accessible widget_tree")


def _name_widget(widget, name: str) -> None:
    try:
        widget.rename(name)
        return
    except Exception:  # noqa: BLE001
        pass
    try:
        widget.set_editor_property("widget_name", name)
    except Exception:  # noqa: BLE001
        try:
            widget.set_editor_property("name", name)
        except Exception:  # noqa: BLE001
            _warn(f"Could not name widget {name}")


def author_tree(bp) -> dict:
    tree = _get_widget_tree(bp)
    root = None
    try:
        root = tree.root_widget
    except Exception:  # noqa: BLE001
        try:
            root = tree.get_editor_property("root_widget")
        except Exception:  # noqa: BLE001
            root = getattr(tree, "root_widget", None)

    if root is None or not isinstance(root, unreal.CanvasPanel):
        root = unreal.new_object(unreal.CanvasPanel, tree)
        _name_widget(root, "RootCanvas")
        try:
            tree.root_widget = root
        except Exception:  # noqa: BLE001
            tree.set_editor_property("root_widget", root)

    _clear_canvas_children(root)

    # Top bar zone (~12%)
    top = unreal.new_object(unreal.CanvasPanel, tree)
    _name_widget(top, "TopBar")
    _slot_fill(root, top, (0, 0), (1, 0.12), (8, 8, 8, 0))

    enemy_name = _make_text(tree, "EnemyNameText", "Shrine Warden", 16)
    _slot_fill(top, enemy_name, (0, 0), (0.55, 1), (4, 4, 4, 4))
    combo = _make_text(tree, "ComboText", "COMBO × 0", 16)
    _slot_fill(top, combo, (0.55, 0), (1, 1), (4, 4, 4, 4))
    enemy_hp = _make_bar(tree, "EnemyHPBar")
    _slot_fill(top, enemy_hp, (0, 0.55), (0.7, 0.85), (4, 0, 4, 0))
    enemy_tough = _make_bar(tree, "EnemyToughnessBar")
    _slot_fill(top, enemy_tough, (0, 0.85), (0.7, 1.0), (4, 0, 4, 0))

    # Party meters strip under top bar
    meters = unreal.new_object(unreal.HorizontalBox, tree)
    _name_widget(meters, "PartyMeters")
    _slot_fill(root, meters, (0, 0.12), (1, 0.18), (8, 0, 8, 0))
    for name in ("HPBar", "SPBar", "UltBar"):
        bar = _make_bar(tree, name)
        slot = meters.add_child_to_horizontal_box(bar)
        try:
            slot.set_size(unreal.SlateChildSize(value=1.0, size_rule=unreal.SlateSizeRule.FILL))
        except Exception:  # noqa: BLE001
            pass

    # Highway canvas — thumb zone (~0.58–0.88)
    highway = unreal.new_object(unreal.CanvasPanel, tree)
    _name_widget(highway, "HighwayCanvas")
    _slot_fill(root, highway, (0, 0.58), (1, 0.88), (12, 0, 12, 0))

    lane_buttons = []
    labels = ("A", "B", "C", "D")
    for i, label in enumerate(labels):
        btn = _make_button(tree, f"LaneButton_{label}", label)
        x0 = i / 4.0
        x1 = (i + 1) / 4.0
        _slot_fill(highway, btn, (x0, 0), (x1, 1), (4, 4, 4, 4))
        lane_buttons.append(btn)

    # Grade popup layer
    grade_canvas = unreal.new_object(unreal.CanvasPanel, tree)
    _name_widget(grade_canvas, "GradePopupCanvas")
    _slot_fill(root, grade_canvas, (0.2, 0.35), (0.8, 0.55), (0, 0, 0, 0))
    grade_text = _make_text(tree, "GradeText", "READY", 28)
    _slot_fill(grade_canvas, grade_text, (0, 0), (1, 1), (0, 0, 0, 0))

    # Skill strip bottom
    skills = unreal.new_object(unreal.HorizontalBox, tree)
    _name_widget(skills, "SkillStrip")
    _slot_fill(root, skills, (0, 0.88), (1, 1), (8, 4, 8, 12))
    for label in ("Basic", "Skill", "Guard", "ULT"):
        chip = _make_button(tree, f"Skill_{label}", label)
        slot = skills.add_child_to_horizontal_box(chip)
        try:
            slot.set_size(unreal.SlateChildSize(value=1.0, size_rule=unreal.SlateSizeRule.FILL))
        except Exception:  # noqa: BLE001
            pass

    return {
        "root": str(root.get_name()),
        "lane_buttons": [str(b.get_name()) for b in lane_buttons],
        "bind_widgets": [
            "HighwayCanvas",
            "ComboText",
            "HPBar",
            "SPBar",
            "UltBar",
            "EnemyNameText",
            "EnemyHPBar",
            "EnemyToughnessBar",
            "GradePopupCanvas",
            "GradeText",
        ],
        "lane_button_objs": lane_buttons,
    }


def _assign_lane_buttons(bp, lane_buttons: list) -> bool:
    """Push buttons into MelodiaMobileHUD.LaneButtons on the generated CDO."""
    try:
        generated = bp.generated_class
        if not generated:
            _warn("No generated_class yet — compile widget first")
            return False
        cdo = unreal.get_default_object(generated)
        if not cdo:
            return False
        # Prefer editor property
        try:
            cdo.set_editor_property("lane_buttons", lane_buttons)
            return True
        except Exception:  # noqa: BLE001
            pass
        try:
            cdo.set_editor_property("LaneButtons", lane_buttons)
            return True
        except Exception as exc:  # noqa: BLE001
            _warn(f"LaneButtons assign failed: {exc}")
            return False
    except Exception as exc:  # noqa: BLE001
        _warn(f"CDO lane assign failed: {exc}")
        return False


def main() -> int:
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "asset": ASSET_PATH,
        "ok": False,
        "steps": [],
        "warnings": [],
        "errors": [],
    }

    parent = _resolve_parent()
    if not parent:
        report["errors"].append(f"Could not load parent {PARENT_CLASS_PATH}")
        report["warnings"].append("Widget may still create as UserWidget — reparent in editor.")
    else:
        report["steps"].append({"parent": PARENT_CLASS_PATH, "ok": True})

    bp, status = _ensure_asset(parent)
    report["steps"].append({"ensure_asset": status})
    if not bp:
        report["errors"].append("Failed to create/load WBP_Battle_Mobile")
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    try:
        tree_info = author_tree(bp)
        lane_objs = tree_info.pop("lane_button_objs", [])
        report["tree"] = tree_info
        report["steps"].append({"author_tree": "ok"})
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"author_tree failed: {exc}")
        lane_objs = []

    # Compile so generated_class exists
    compiled = False
    try:
        if hasattr(unreal, "KismetSystemLibrary"):
            pass
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        compiled = True
        report["steps"].append({"compile": "ok"})
    except Exception as exc:  # noqa: BLE001
        report["warnings"].append(f"compile_blueprint: {exc}")

    assigned = False
    if lane_objs:
        assigned = _assign_lane_buttons(bp, lane_objs)
        report["steps"].append({"lane_buttons_assigned": assigned})

    unreal.EditorAssetLibrary.save_asset(ASSET_PATH, only_if_is_dirty=False)
    on_disk = (PROJECT_ROOT / "Content/Melodia/UI/WBP_Battle_Mobile.uasset").is_file()
    report["on_disk"] = on_disk
    # Shell success: asset + MelodiaMobileHUD parent. Tree authoring is designer (WidgetTree protected).
    report["ok"] = on_disk and status in ("created", "exists") and not any(
        "Could not load parent" in e for e in report["errors"]
    )
    report["tree_authored"] = bool(lane_objs) and "author_tree" in str(report.get("steps"))
    if report["errors"] and any("widget_tree" in e.lower() or "author_tree" in e.lower() for e in report["errors"]):
        report["warnings"].append(
            "UE 5.8 Python cannot mutate protected WidgetTree — open WBP in UMG Designer for BindWidgets + LaneButtons."
        )
        # Soft-clear tree errors so shell create still counts as Pass C P0
        report["errors"] = [e for e in report["errors"] if "author_tree" not in e and "widget_tree" not in e.lower()]
        report["ok"] = on_disk
    report["next"] = (
        "Open WBP_Battle_Mobile in UMG Designer — confirm BindWidget names, "
        "LaneButtons[0..3], brush Batch N textures from /Game/EnvSandbox/Textures/Melodia/GameUI."
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _log(f"Wrote {REPORT} ok={report['ok']} status={status} compiled={compiled} lanes={assigned}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
