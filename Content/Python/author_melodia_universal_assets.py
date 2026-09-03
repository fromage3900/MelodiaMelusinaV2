"""Create the universal Melodia token pickup and registry-driven wallet widget assets.

The native classes own economy behavior. These assets only provide stable parent classes and
named presentation containers so a designer can replace the look without creating another
wallet or another currency list.
"""
from __future__ import annotations

import unreal


BLUEPRINT_DIR = "/Game/Melodia/Blueprints"
UI_DIR = "/Game/Melodia/UI"
PICKUP_ASSET = f"{BLUEPRINT_DIR}/BP_MelodyToken_Universal"
ROW_ASSET = f"{UI_DIR}/WBP_MelodiaCurrencyRow"
HUD_ASSET = f"{UI_DIR}/WBP_MelodiaWallet_Universal"


def _log(message: str) -> None:
    unreal.log(f"[MelodiaUniversal] {message}")


def _warn(message: str) -> None:
    unreal.log_warning(f"[MelodiaUniversal] {message}")


def _ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def _reparent(bp, parent_class) -> None:
    if not bp or not parent_class:
        return
    try:
        unreal.BlueprintEditorLibrary.reparent_blueprint(bp, parent_class)
    except Exception:
        try:
            bp.set_editor_property("parent_class", parent_class)
        except Exception as exc:  # noqa: BLE001
            _warn(f"could not set parent class: {exc}")


def _ensure_blueprint(asset_path: str, asset_name: str, directory: str, parent_class):
    full_path = f"{asset_path}.{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        _reparent(bp, parent_class)
        return bp, "exists"

    _ensure_dir(directory)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, directory, unreal.Blueprint, factory
    )
    if not bp:
        raise RuntimeError(f"could not create Blueprint {asset_path}")
    _reparent(bp, parent_class)
    unreal.EditorAssetLibrary.save_asset(asset_path)
    return bp, "created"


def _ensure_widget_blueprint(asset_path: str, asset_name: str, directory: str, parent_class):
    full_path = f"{asset_path}.{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        bp = unreal.EditorAssetLibrary.load_asset(asset_path)
        _reparent(bp, parent_class)
        return bp, "exists"

    _ensure_dir(directory)
    factory = unreal.WidgetBlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, directory, unreal.WidgetBlueprint, factory
    )
    if not bp:
        raise RuntimeError(f"could not create WidgetBlueprint {asset_path}")
    _reparent(bp, parent_class)
    unreal.EditorAssetLibrary.save_asset(asset_path)
    return bp, "created"


def _name(widget, name: str) -> None:
    try:
        widget.rename(name)
    except Exception:
        try:
            widget.set_editor_property("widget_name", name)
        except Exception as exc:  # noqa: BLE001
            _warn(f"could not name widget {name}: {exc}")


def _tree(bp):
    for key in ("widget_tree", "WidgetTree"):
        try:
            tree = bp.get_editor_property(key)
            if tree:
                return tree
        except Exception:
            pass
        tree = getattr(bp, key, None)
        if tree:
            return tree
    raise AttributeError("WidgetBlueprint has no accessible widget tree")


def _root_canvas(tree):
    try:
        root = tree.root_widget
    except Exception:
        root = tree.get_editor_property("root_widget")
    if root is None or not isinstance(root, unreal.CanvasPanel):
        root = unreal.new_object(unreal.CanvasPanel, tree)
        _name(root, "RootCanvas")
        try:
            tree.root_widget = root
        except Exception:
            tree.set_editor_property("root_widget", root)
    while root.get_children_count() > 0:
        root.remove_child_at(0)
    return root


def _fill(root, child, margin=(16, 16, 16, 16)):
    slot = root.add_child_to_canvas(child)
    slot.set_anchors(unreal.Anchors(minimum=unreal.Vector2D(0, 0), maximum=unreal.Vector2D(1, 1)))
    slot.set_offsets(unreal.Margin(*margin))
    return slot


def _text(tree, name: str, value: str, size: int = 14):
    widget = unreal.new_object(unreal.TextBlock, tree)
    _name(widget, name)
    widget.set_text(value)
    try:
        widget.set_editor_property("font", unreal.SlateFontInfo(size=size))
    except Exception:
        pass
    return widget


def _author_row(bp) -> None:
    tree = _tree(bp)
    root = _root_canvas(tree)
    row = unreal.new_object(unreal.HorizontalBox, tree)
    _name(row, "RowRoot")
    icon = unreal.new_object(unreal.Image, tree)
    _name(icon, "IMG_Icon")
    icon.set_desired_size_override(unreal.Vector2D(28, 28))
    row.add_child_to_horizontal_box(icon)
    display = _text(tree, "TXT_DisplayName", "Currency", 14)
    row.add_child_to_horizontal_box(display)
    balance = _text(tree, "TXT_Balance", "0", 14)
    row.add_child_to_horizontal_box(balance)
    _fill(root, row)
    unreal.EditorAssetLibrary.save_asset(ROW_ASSET)


def _author_hud(bp) -> None:
    tree = _tree(bp)
    root = _root_canvas(tree)
    content = unreal.new_object(unreal.VerticalBox, tree)
    _name(content, "WalletContent")
    _fill(root, content, (18, 14, 18, 14))

    title = _text(tree, "TXT_Title", "MELODIA WALLET", 16)
    content.add_child_to_vertical_box(title)

    container = unreal.new_object(unreal.VerticalBox, tree)
    _name(container, "CurrencyContainer")
    content.add_child_to_vertical_box(container)
    for currency_id in ("Forte", "Tide", "Gale", "Stone", "Radiant", "Umbral", "Arcane"):
        row = unreal.new_object(unreal.HorizontalBox, tree)
        _name(row, f"Row_{currency_id}")
        content.add_child_to_vertical_box(row)
        label = _text(tree, f"Lbl_{currency_id}", currency_id, 13)
        row.add_child_to_horizontal_box(label)
        value = _text(tree, f"TXT_{currency_id}", "0", 13)
        row.add_child_to_horizontal_box(value)

    for name, label in (
        ("TXT_Mana", "MANA 0"),
        ("TXT_GoldenTokens", "GOLDEN 0"),
        ("TXT_TotalCollected", "COLLECTED 0"),
    ):
        content.add_child_to_vertical_box(_text(tree, name, label, 12))
    unreal.EditorAssetLibrary.save_asset(HUD_ASSET)


def main() -> None:
    pickup_parent = unreal.load_class(None, "/Script/BS_GodFile.MelodiaTokenPickup")
    if not pickup_parent:
        raise RuntimeError("native parent unavailable: /Script/BS_GodFile.MelodiaTokenPickup")

    pickup, pickup_status = _ensure_blueprint(
        PICKUP_ASSET, "BP_MelodyToken_Universal", BLUEPRINT_DIR, pickup_parent
    )
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(pickup)
    except Exception as exc:  # noqa: BLE001
        _warn(f"Blueprint compile request failed: {exc}")
    unreal.EditorAssetLibrary.save_asset(PICKUP_ASSET)
    for asset_path in (ROW_ASSET, HUD_ASSET):
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            _warn(
                f"missing {asset_path}; author it with Monolith ui::build_ui_from_spec "
                "because UE 5.8 Python does not expose WidgetTree on WidgetBlueprint"
            )
    print(
        "MELODIA_UNIVERSAL_ASSETS",
        {
            "pickup": pickup_status,
            "row": "present" if unreal.EditorAssetLibrary.does_asset_exist(ROW_ASSET) else "missing",
            "hud": "present" if unreal.EditorAssetLibrary.does_asset_exist(HUD_ASSET) else "missing",
        },
    )


if __name__ == "__main__":
    main()
