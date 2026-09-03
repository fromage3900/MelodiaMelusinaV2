"""Author project-owned Quill presentation WBPs through Monolith after a native rebuild.

Run from a normal Python environment while Unreal Editor and Monolith are available.
This script owns presentation only. It does not modify Quill interpreter flow, saves,
travel, Persona state, or JRPG authority. Run assign_melodia_quill_presentation.py
inside Unreal afterward to write generated classes into the scene's FScriptSettings.
"""
from __future__ import annotations

import json

from monolith_mcp_client import call_tool

DIALOG = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog"
CHOICE = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry"
SELECTION = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection"
BACKGROUND = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillBackground"

PARENTS = {
    DIALOG: "/Script/BS_GodFile.MelodiaQuillDialogWidget",
    CHOICE: "/Script/BS_GodFile.MelodiaQuillChoiceEntryWidget",
    SELECTION: "/Script/BS_GodFile.MelodiaQuillSelectionWidget",
    BACKGROUND: "/Script/BS_GodFile.MelodiaQuillBackgroundWidget",
}

PARCHMENT = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
BUTTON_ORNAMENT = PARCHMENT
DIVIDER = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_DividerScroll"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result)}")
    return result


def ui(asset: str, action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=asset, **arguments)


def payload(result):
    return json.loads(result["content"][0]["text"])


def asset_exists(asset: str) -> bool:
    result = call_tool("ui_query", {"action": "get_widget_tree", "asset_path": asset})
    if result.get("isError"):
        message = result.get("content", [{}])[0].get("text", "")
        if "not found" in message.lower():
            return False
        raise RuntimeError(f"Widget existence check failed for {asset}: {json.dumps(result)}")
    return True


def ensure_blueprint(asset: str):
    if not asset_exists(asset):
        invoke("ui_query", action="create_widget_blueprint", save_path=asset, parent_class=PARENTS[asset])


def widget_names(asset: str) -> set[str]:
    tree = payload(ui(asset, "get_widget_tree"))
    names: set[str] = set()

    def visit(node):
        if not isinstance(node, dict):
            return
        if node.get("name"):
            names.add(node["name"])
        for child in node.get("children", []):
            visit(child)

    visit(tree.get("root", tree))
    return names


def ensure_widget(asset: str, widget_class: str, name: str, parent: str | None = None):
    if name in widget_names(asset):
        return
    args = dict(widget_class=widget_class, widget_name=name, compile=False)
    if parent:
        args["parent_name"] = parent
    ui(asset, "add_widget", **args)


def variable(asset: str, name: str):
    ui(asset, "set_widget_is_variable", widget_name=name, is_variable=True, compile=False)


def set_text(asset: str, name: str, text: str, size: int, color: str, justification: str = "Left"):
    ui(asset, "set_text", widget_name=name, text=text, text_color=color, font_size=size,
       justification=justification, compile=False)
    ui(asset, "set_font", widget_name=name, font_size=size, typeface="Regular", compile=False)


def place_canvas_widget(
    asset: str,
    name: str,
    preset: str,
    offsets: dict,
    z_order: int,
    alignment: dict | None = None,
):
    """Give every Canvas child an explicit viewport-scale layout.

    The previous authoring pass only added children to a CanvasPanel. Unreal's
    default 100x30 slots made the assigned Quill UI overlap and appear unreadable.
    """
    ui(asset, "set_anchor_preset", widget_name=name, preset=preset, compile=False)
    arguments = dict(widget_name=name, offsets=offsets, z_order=z_order, compile=False)
    if alignment is not None:
        arguments["alignment"] = alignment
    ui(asset, "set_slot_property", **arguments)


def set_button_skin(asset: str, name: str):
    for state, tint in (("Normal", "#725B82F2"), ("Hovered", "#9B78AAFF"), ("Pressed", "#584664FF"),
                        ("Disabled", "#4A44526E")):
        ui(asset, "set_brush", widget_name=name, property_name=f"WidgetStyle.{state}",
           texture_path=BUTTON_ORNAMENT, draw_type="Image",
           tint_color=tint, compile=False)


def compile_and_save(asset: str):
    result = payload(ui(asset, "compile_widget"))
    if result.get("error_count", 0) or result.get("errors"):
        raise RuntimeError(f"Compile failed for {asset}: {json.dumps(result, indent=2)}")
    invoke("blueprint_query", action="save_asset", asset_path=asset)
    return {"asset": asset, "errors": result.get("error_count", 0), "warnings": result.get("warning_count", 0)}


def author_dialog():
    asset = DIALOG
    ensure_blueprint(asset)
    ensure_widget(asset, "CanvasPanel", "DialogRoot")
    ensure_widget(asset, "Image", "ParchmentPanel", "DialogRoot")
    ensure_widget(asset, "Image", "BaroqueDivider", "DialogRoot")
    ensure_widget(asset, "TextBlock", "SpeakerText", "DialogRoot")
    ensure_widget(asset, "TextBlock", "BodyText", "DialogRoot")
    ensure_widget(asset, "Button", "AdvanceButton", "DialogRoot")
    ensure_widget(asset, "TextBlock", "AdvanceLabel", "AdvanceButton")
    for name in ("SpeakerText", "BodyText", "AdvanceButton"):
        variable(asset, name)

    place_canvas_widget(
        asset, "ParchmentPanel", "bottom_center",
        {"left": 0, "top": -20, "right": 1500, "bottom": 330}, 10,
        {"x": 0.5, "y": 1.0})
    place_canvas_widget(
        asset, "BaroqueDivider", "bottom_center",
        {"left": 0, "top": -264, "right": 1240, "bottom": 28}, 11,
        {"x": 0.5, "y": 1.0})
    place_canvas_widget(
        asset, "SpeakerText", "bottom_center",
        {"left": -650, "top": -228, "right": 520, "bottom": 34}, 12,
        {"x": 0.0, "y": 1.0})
    place_canvas_widget(
        asset, "BodyText", "bottom_center",
        {"left": -650, "top": -56, "right": 1190, "bottom": 148}, 12,
        {"x": 0.0, "y": 1.0})
    place_canvas_widget(
        asset, "AdvanceButton", "bottom_center",
        {"left": 650, "top": -18, "right": 190, "bottom": 52}, 13,
        {"x": 1.0, "y": 1.0})

    ui(asset, "set_brush", widget_name="ParchmentPanel", property_name="Brush", texture_path=PARCHMENT,
       draw_type="Box", margin={"left": 0.20, "top": 0.20, "right": 0.20, "bottom": 0.20},
       tint_color="#FFF6E8FC", compile=False)
    ui(asset, "set_brush", widget_name="BaroqueDivider", property_name="Brush", texture_path=DIVIDER,
       draw_type="Image", tint_color="#B99559E8", compile=False)
    set_text(asset, "SpeakerText", "MELODIA", 22, "#6B416F")
    set_text(asset, "BodyText", "Dialogue", 28, "#241B2C")
    set_text(asset, "AdvanceLabel", "CONTINUE", 18, "#FFF9F3", "Center")
    ui(asset, "set_widget_property", widget_name="BodyText", property_name="AutoWrapText", value=True,
       raw_mode=True, compile=False)
    set_button_skin(asset, "AdvanceButton")
    return compile_and_save(asset)


def author_choice():
    asset = CHOICE
    ensure_blueprint(asset)
    ensure_widget(asset, "Button", "ChoiceButton")
    ensure_widget(asset, "TextBlock", "ChoiceText", "ChoiceButton")
    for name in ("ChoiceButton", "ChoiceText"):
        variable(asset, name)
    set_text(asset, "ChoiceText", "Choice", 22, "#FFF9F3")
    for property_name in ("WidgetStyle.NormalPadding", "WidgetStyle.PressedPadding"):
        ui(asset, "set_widget_property", widget_name="ChoiceButton", property_name=property_name,
           value={"left": 28, "top": 16, "right": 28, "bottom": 16}, raw_mode=True,
           compile=False)
    ui(asset, "set_widget_property", widget_name="ChoiceText", property_name="AutoWrapText", value=True,
       raw_mode=True, compile=False)
    set_button_skin(asset, "ChoiceButton")
    return compile_and_save(asset)


def author_selection():
    asset = SELECTION
    ensure_blueprint(asset)
    ensure_widget(asset, "CanvasPanel", "SelectionRoot")
    ensure_widget(asset, "Image", "SelectionParchment", "SelectionRoot")
    ensure_widget(asset, "TextBlock", "PromptText", "SelectionRoot")
    ensure_widget(asset, "VerticalBox", "OptionsBox", "SelectionRoot")
    variable(asset, "OptionsBox")
    place_canvas_widget(
        asset, "SelectionParchment", "bottom_center",
        {"left": 0, "top": -24, "right": 1500, "bottom": 470}, 20,
        {"x": 0.5, "y": 1.0})
    place_canvas_widget(
        asset, "PromptText", "bottom_center",
        {"left": 0, "top": -396, "right": 1180, "bottom": 42}, 21,
        {"x": 0.5, "y": 1.0})
    place_canvas_widget(
        asset, "OptionsBox", "bottom_center",
        {"left": 0, "top": -56, "right": 1180, "bottom": 320}, 22,
        {"x": 0.5, "y": 1.0})
    ui(asset, "set_brush", widget_name="SelectionParchment", property_name="Brush", texture_path=PARCHMENT,
       draw_type="Box", margin={"left": 0.20, "top": 0.20, "right": 0.20, "bottom": 0.20},
       tint_color="#FFF6E8FC", compile=False)
    set_text(asset, "PromptText", "Choose your resonance", 22, "#6B416F", "Center")
    return compile_and_save(asset)


def author_background():
    asset = BACKGROUND
    ensure_blueprint(asset)
    ensure_widget(asset, "CanvasPanel", "BackgroundRoot")
    ensure_widget(asset, "Image", "BackgroundImage", "BackgroundRoot")
    variable(asset, "BackgroundImage")
    place_canvas_widget(
        asset, "BackgroundImage", "stretch_fill",
        {"left": 0, "top": 0, "right": 0, "bottom": 0}, 0,
        {"x": 0.0, "y": 0.0})
    ui(asset, "set_widget_property", widget_name="BackgroundImage",
       property_name="Visibility", value="HitTestInvisible", raw_mode=True, compile=False)
    return compile_and_save(asset)


if __name__ == "__main__":
    reports = [author_choice(), author_dialog(), author_selection(), author_background()]
    print(json.dumps({"status": "authored", "assets": reports,
                      "next": "Run assign_melodia_quill_presentation.py inside Unreal Editor"}, indent=2))
