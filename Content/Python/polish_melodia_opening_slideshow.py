"""Author the project-owned Melodia opening slideshow presentation through Monolith.

Safe to run while Unreal Editor is open. The script is idempotent and preserves the
six UMelodiaStorySequenceWidget BindWidget names that own slideshow behavior.
"""
from __future__ import annotations

import json

from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/WBP_MelodiaOpeningSlideshow"
PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment"
PANEL_FILL = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise"
DIVIDER = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_DividerScroll"
CREST = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_CrestBaroque"
CORNER = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_CornerBaroque"
# set_font resolves explicit object paths more reliably than package-only paths.
FONT_DISPLAY = "/Game/Melodia/UI/Fonts/F_Syne.F_Syne"
FONT_BODY = "/Game/Melodia/UI/Fonts/F_InstrumentSerif.F_InstrumentSerif"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result)}")
    return result


def ui(action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=ASSET, **arguments)


def ensure_image(name: str):
    tree = ui("get_widget_tree")
    payload = json.loads(tree["content"][0]["text"])
    names: list[str] = []

    def visit(node):
        names.append(node.get("name", ""))
        for child in node.get("children", []):
            visit(child)

    visit(payload["root"])
    if name not in names:
        ui("add_widget", widget_class="Image", widget_name=name, parent_name="CanvasPanel", compile=False)


def anchor(name: str, preset: str, offsets: dict, z_order: int, alignment: dict | None = None):
    ui("set_anchor_preset", widget_name=name, preset=preset, compile=False)
    args = {"widget_name": name, "offsets": offsets, "z_order": z_order, "compile": False}
    if alignment is not None:
        args["alignment"] = alignment
    ui("set_slot_property", **args)


# Full-screen cinematic layers and a lower-third SoftMG reading surface.
# The SoftMG ScrollEdge texture is intentionally not used: its large internal arch
# motif is an ornamental cap, not a stretchable rail. Existing legacy instances are
# collapsed below so rerunning this script also repairs previously-authored assets.
for widget_name in (
    "ReadabilityVeil",
    "SoftMGNarrativePanel",
    "BaroqueDivider",
    "BaroqueCrest",
    "BaroqueCornerLeft",
    "BaroqueCornerRight",
):
    ensure_image(widget_name)

anchor("SlideArtwork", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, 0)
anchor("ReadabilityVeil", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, 1)
anchor("SoftMGNarrativePanel", "stretch_bottom", {"left": 118, "top": -430, "right": 118, "bottom": 368}, 2)
anchor("BaroqueDivider", "stretch_bottom", {"left": 250, "top": -408, "right": 250, "bottom": 28}, 3)
anchor("BaroqueCrest", "bottom_center", {"left": -96, "top": -454, "right": 192, "bottom": 92}, 4)
anchor("BaroqueCornerLeft", "bottom_left", {"left": 132, "top": -394, "right": 96, "bottom": 96}, 4)
anchor("BaroqueCornerRight", "bottom_right", {"left": -228, "top": -394, "right": 96, "bottom": 96}, 4)

for legacy_edge in ("SoftMGScrollEdge", "SoftMGBottomEdge"):
    ui("set_widget_property", widget_name=legacy_edge, property_name="Visibility", value="Collapsed", raw_mode=True, compile=False)

ui("set_brush", widget_name="ReadabilityVeil", property_name="Brush", draw_type="Image", tint_color="#09071578", compile=False)
ui("set_brush", widget_name="SoftMGNarrativePanel", property_name="Brush", texture_path=PANEL_FILL, draw_type="Image", tint_color="#F5EEEAFA", compile=False)
ui("set_brush", widget_name="BaroqueDivider", property_name="Brush", texture_path=DIVIDER, draw_type="Image", tint_color="#B99559B8", compile=False)
ui("set_brush", widget_name="BaroqueCrest", property_name="Brush", texture_path=CREST, tint_color="#B99559E8", compile=False)
ui("set_brush", widget_name="BaroqueCornerLeft", property_name="Brush", texture_path=CORNER, tint_color="#B99559C8", compile=False)
ui("set_brush", widget_name="BaroqueCornerRight", property_name="Brush", texture_path=CORNER, tint_color="#B99559C8", compile=False)
ui("set_widget_property", widget_name="BaroqueCornerRight", property_name="RenderTransform.Angle", value="180", raw_mode=True, compile=False)

# Render-safe 16:9 typography inside the lower-third panel.
anchor("KickerText", "bottom_left", {"left": 224, "top": -360, "right": 1040, "bottom": 34}, 6)
anchor("TitleText", "bottom_left", {"left": 216, "top": -316, "right": 1180, "bottom": 72}, 6)
anchor("BodyText", "stretch_bottom", {"left": 220, "top": -226, "right": 360, "bottom": 108}, 6)
anchor("AdvanceButton", "bottom_right", {"left": -332, "top": -116, "right": 220, "bottom": 58}, 7)
anchor("SkipButton", "top_right", {"left": -192, "top": 48, "right": 144, "bottom": 46}, 7)

ui("set_text", widget_name="KickerText", text_color="#8D688E", font_size=18, justification="Left", compile=False)
ui("set_text", widget_name="TitleText", text_color="#33283E", font_size=48, justification="Left", compile=False)
ui("set_text", widget_name="BodyText", text_color="#4C4054", font_size=25, justification="Left", compile=False)
ui("set_text", widget_name="AdvanceLabel", text_color="#FFF9F3", font_size=20, justification="Center", compile=False)
ui("set_text", widget_name="SkipLabel", text_color="#F8EEF7", font_size=17, justification="Center", compile=False)
# These checked-in F_* assets are FontFace assets, while Monolith set_font currently
# resolves only UFont families. Keep the project's inherited font object and author
# the intended display/body hierarchy without replacing it with a default engine font.
ui("set_font", widget_name="KickerText", font_size=18, typeface="Bold", letter_spacing=180, compile=False)
ui("set_font", widget_name="TitleText", font_size=48, typeface="Bold", letter_spacing=20, compile=False)
ui("set_font", widget_name="BodyText", font_size=25, typeface="Regular", compile=False)
ui("set_font", widget_name="AdvanceLabel", font_size=20, typeface="Bold", letter_spacing=60, compile=False)
ui("set_font", widget_name="SkipLabel", font_size=17, typeface="Regular", letter_spacing=80, compile=False)
ui("set_widget_property", widget_name="BodyText", property_name="AutoWrapText", value=True, raw_mode=True, compile=False)
ui("set_widget_property", widget_name="BodyText", property_name="LineHeightPercentage", value="1.18", raw_mode=True, compile=False)

# SoftMG button treatments retain the existing native click bindings.
for state, tint in (("Normal", "#745A83F2"), ("Hovered", "#9975A7FF"), ("Pressed", "#5B4668FF")):
    ui("set_brush", widget_name="AdvanceButton", property_name=f"WidgetStyle.{state}", texture_path=PARCHMENT, draw_type="Box", margin={"left": 0.28, "top": 0.28, "right": 0.28, "bottom": 0.28}, tint_color=tint, compile=False)
for state, tint in (("Normal", "#251F3199"), ("Hovered", "#745A83DD"), ("Pressed", "#251F31EE")):
    ui("set_brush", widget_name="SkipButton", property_name=f"WidgetStyle.{state}", texture_path=PARCHMENT, draw_type="Box", margin={"left": 0.28, "top": 0.28, "right": 0.28, "bottom": 0.28}, tint_color=tint, compile=False)

ui("compile_widget")
invoke("blueprint_query", action="save_asset", asset_path=ASSET)
print(json.dumps({"asset": ASSET, "status": "compiled_and_saved"}, indent=2))
