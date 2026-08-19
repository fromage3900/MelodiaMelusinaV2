"""Author WBP_MelodiaTokenWallet against UMelodiaWalletHUDWidget + DA_MelodiaTokenCatalog.

Parented on the native UMelodiaWalletHUDWidget (MelodiaTokenPresentation.h), which
auto-binds OnWalletChanged -> PresentSnapshot and fills the named TXT_* text fields.
The Blueprint contributes the visual bubble rows (icon + name + value) and the
native C++ renders balances. Single-wallet rule: binds to UMelodiaTokenWalletSubsystem,
never creates a second wallet.
"""
from __future__ import annotations

import unreal

UI_DIR = "/Game/Melodia/UI"
ASSET_NAME = "WBP_MelodiaTokenWallet"
ASSET_PATH = f"{UI_DIR}/{ASSET_NAME}"
PARENT_CLASS_PATH = "/Script/BS_GodFile.MelodiaWalletHUDWidget"

PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment"

ICONS = {
    "Forte": "/Game/EnvSandbox/Textures/melodsytoken/Textures/T_MelodyToken_Heart_BaseColor",
    "Radiant": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Star_BaseColor",
    "Arcane": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Swirl_BaseColor",
    "Tide": "/Game/EnvSandbox/Textures/melodsytoken_textures/MelodyToken_Water_BaseColor",
}

ROWS = [
    ("Forte", "Forte Shard", "10"),
    ("Radiant", "Radiant Shard", "12"),
    ("Arcane", "Arcane Shard", "15"),
    ("Tide", "Tide Shard", "12"),
]

BALANCE_NAMES = ["TXT_Forte", "TXT_Tide", "TXT_Gale", "TXT_Stone", "TXT_Radiant", "TXT_Umbral", "TXT_Arcane"]


def _log(msg: str) -> None:
    unreal.log(f"[TokenWallet] {msg}")


def _warn(msg: str) -> None:
    unreal.log_warning(f"[TokenWallet] {msg}")


def _reparent(bp, parent_class) -> bool:
    if not bp or not parent_class:
        return False
    try:
        if hasattr(unreal, "BlueprintEditorLibrary"):
            unreal.BlueprintEditorLibrary.reparent_blueprint(bp, parent_class)
            return True
    except Exception as exc:  # noqa: BLE001
        _warn(f"reparent failed: {exc}")
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
        _reparent(bp, parent_class)
        return bp, "exists"
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
    _reparent(bp, parent_class)
    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    return bp, "created"


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


def _get_widget_tree(bp):
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


def _clear_children(panel) -> None:
    try:
        while panel.get_children_count() > 0:
            panel.remove_child_at(0)
    except Exception:  # noqa: BLE001
        pass


def _slot_fill(panel, child, anchors_min=(0.0, 0.0), anchors_max=(1.0, 1.0), offsets=(0, 0, 0, 0)):
    slot = panel.add_child_to_canvas(child)
    slot.set_anchors(unreal.Anchors(
        minimum=unreal.Vector2D(anchors_min[0], anchors_min[1]),
        maximum=unreal.Vector2D(anchors_max[0], anchors_max[1]),
    ))
    slot.set_offsets(unreal.Margin(offsets[0], offsets[1], offsets[2], offsets[3]))
    slot.set_alignment(unreal.Vector2D(0.0, 0.0))
    return slot


def _make_text(tree, name: str, text: str, size: int = 15, color=None):
    tb = unreal.new_object(unreal.TextBlock, tree)
    _name_widget(tb, name)
    tb.set_text(text)
    try:
        tb.set_editor_property("font", unreal.SlateFontInfo(size=size))
    except Exception:  # noqa: BLE001
        pass
    if color:
        try:
            tb.set_color_and_opacity(color)
        except Exception:  # noqa: BLE001
            try:
                tb.set_editor_property("color_and_opacity", color)
            except Exception:  # noqa: BLE001
                pass
    return tb


def _make_icon(tree, name: str, tex_path: str, size_px: float = 26.0):
    img = unreal.new_object(unreal.Image, tree)
    _name_widget(img, name)
    try:
        tex = unreal.EditorAssetLibrary.load_asset(tex_path)
        brush = unreal.SlateBrush()
        brush.set_editor_property("resource_object", tex)
        img.set_editor_property("brush", brush)
    except Exception as exc:  # noqa: BLE001
        _warn(f"icon brush failed for {name}: {exc}")
    img.set_desired_size_override(unreal.Vector2D(size_px, size_px))
    return img


def _make_row(tree, vbox, element: str, label: str, value: str):
    row = unreal.new_object(unreal.HorizontalBox, tree)
    _name_widget(row, f"Row_{element}")
    icon = _make_icon(tree, f"Icon_{element}", ICONS[element], 22.0)
    icon_slot = row.add_child_to_horizontal_box(icon)
    icon_slot.set_padding(unreal.Margin(0, 0, 8, 0))
    icon_slot.set_vertical_alignment(unreal.EVerticalAlignment.VAlign_Center)

    name_tb = _make_text(tree, f"Txt_{element}Name", label, 13)
    name_slot = row.add_child_to_horizontal_box(name_tb)
    name_slot.set_vertical_alignment(unreal.EVerticalAlignment.VAlign_Center)
    name_slot.set_padding(unreal.Margin(0, 0, 10, 0))

    balance_tb = _make_text(tree, f"TXT_{element}", "0", 15)
    bal_slot = row.add_child_to_horizontal_box(balance_tb)
    bal_slot.set_vertical_alignment(unreal.EVerticalAlignment.VAlign_Center)
    bal_slot.set_padding(unreal.Margin(0, 0, 10, 0))
    bal_slot.set_horizontal_alignment(unreal.EHorizontalAlignment.HAlign_Right)

    val_tb = _make_text(tree, f"Txt_{element}Value", value, 12)
    val_slot = row.add_child_to_horizontal_box(val_tb)
    val_slot.set_vertical_alignment(unreal.EVerticalAlignment.VAlign_Center)
    val_slot.set_horizontal_alignment(unreal.EHorizontalAlignment.HAlign_Right)

    vbox_slot = vbox.add_child_to_vertical_box(row)
    vbox_slot.set_padding(unreal.Margin(0, 3, 0, 3))
    return row


def author_tree(bp) -> dict:
    tree = _get_widget_tree(bp)
    root = None
    try:
        root = tree.root_widget
    except Exception:  # noqa: BLE001
        root = tree.get_editor_property("root_widget")

    if root is None or not isinstance(root, unreal.CanvasPanel):
        root = unreal.new_object(unreal.CanvasPanel, tree)
        _name_widget(root, "RootCanvas")
        try:
            tree.root_widget = root
        except Exception:  # noqa: BLE001
            tree.set_editor_property("root_widget", root)
    _clear_children(root)

    fill = unreal.new_object(unreal.Border, tree)
    _name_widget(fill, "ParchmentFill")
    try:
        tex = unreal.EditorAssetLibrary.load_asset(PARCHMENT)
        brush = unreal.SlateBrush()
        brush.set_editor_property("resource_object", tex)
        brush.set_editor_property("margin", unreal.Margin(0.28, 0.28, 0.28, 0.28))
        brush.set_editor_property("draw_as", unreal.ESlateBrushDrawType.BOX)
        fill.set_editor_property("brush", brush)
    except Exception as exc:  # noqa: BLE001
        _warn(f"parchment brush failed: {exc}")
    _slot_fill(root, fill, (0, 0), (1, 1), (0, 0, 0, 0))

    content = unreal.new_object(unreal.VerticalBox, tree)
    _name_widget(content, "Content")
    _slot_fill(root, content, (0, 0), (1, 1), (18, 14, 18, 14))

    title = _make_text(tree, "Txt_Title", "MELODY SHARDS", 16)
    title_slot = content.add_child_to_vertical_box(title)
    title_slot.set_horizontal_alignment(unreal.EHorizontalAlignment.HAlign_Center)
    title_slot.set_padding(unreal.Margin(0, 0, 0, 6))

    divider = unreal.new_object(unreal.Image, tree)
    _name_widget(divider, "Divider")
    try:
        dbrush = unreal.SlateBrush()
        dbrush.set_editor_property("draw_as", unreal.ESlateBrushDrawType.BOX)
        dbrush.set_editor_property("tint_color", unreal.LinearColor(0.788, 0.635, 0.153, 1.0))
        divider.set_editor_property("brush", dbrush)
    except Exception:  # noqa: BLE001
        pass
    divider.set_desired_size_override(unreal.Vector2D(0.0, 2.0))
    div_slot = content.add_child_to_vertical_box(divider)
    div_slot.set_padding(unreal.Margin(0, 0, 0, 6))

    rows_made = []
    for element, label, value in ROWS:
        rows_made.append(_make_row(tree, content, element, label, value))

    spacer = unreal.new_object(unreal.Spacer, tree)
    _name_widget(spacer, "SpacerBottom")
    spacer.set_size(unreal.Vector2D(0.0, 4.0))
    content.add_child_to_vertical_box(spacer)

    meta_row = unreal.new_object(unreal.HorizontalBox, tree)
    _name_widget(meta_row, "Row_Meta")
    mana_lbl = _make_text(tree, "Lbl_Mana", "MANA", 11)
    mana_slot = meta_row.add_child_to_horizontal_box(mana_lbl)
    mana_slot.set_padding(unreal.Margin(0, 0, 6, 0))
    mana_tb = _make_text(tree, "TXT_Mana", "0", 13)
    m2 = meta_row.add_child_to_horizontal_box(mana_tb)
    m2.set_padding(unreal.Margin(0, 0, 12, 0))

    gold_lbl = _make_text(tree, "Lbl_Golden", "GOLDEN", 11)
    g1 = meta_row.add_child_to_horizontal_box(gold_lbl)
    g1.set_padding(unreal.Margin(0, 0, 6, 0))
    gold_tb = _make_text(tree, "TXT_GoldenTokens", "0", 13)
    g2 = meta_row.add_child_to_horizontal_box(gold_tb)
    g2.set_padding(unreal.Margin(0, 0, 12, 0))

    tot_lbl = _make_text(tree, "Lbl_Total", "COLLECTED", 11)
    t1 = meta_row.add_child_to_horizontal_box(tot_lbl)
    t1.set_padding(unreal.Margin(0, 0, 6, 0))
    tot_tb = _make_text(tree, "TXT_TotalCollected", "0", 13)
    meta_row.add_child_to_horizontal_box(tot_tb)

    meta_slot = content.add_child_to_vertical_box(meta_row)
    meta_slot.set_padding(unreal.Margin(0, 6, 0, 0))

    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    return {
        "rows": [r[0] for r in ROWS],
        "balance_names": BALANCE_NAMES,
        "meta_names": ["TXT_Mana", "TXT_GoldenTokens", "TXT_TotalCollected"],
    }


def main():
    cls = unreal.load_class(None, PARENT_CLASS_PATH)
    if not cls:
        cls = unreal.load_class(None, "BS_GodFile.MelodiaWalletHUDWidget")
    if not cls:
        raise RuntimeError(f"Could not resolve parent {PARENT_CLASS_PATH}")

    bp, status = _ensure_asset(cls)
    if not bp:
        raise RuntimeError(f"WidgetBlueprint create failed: {status}")
    _log(f"asset {status}")

    summary = author_tree(bp)
    _log(f"tree authored: {summary}")
    unreal.EditorAssetLibrary.save_asset(ASSET_PATH)
    print("AUTHORED", ASSET_PATH, summary)


if __name__ == "__main__":
    main()