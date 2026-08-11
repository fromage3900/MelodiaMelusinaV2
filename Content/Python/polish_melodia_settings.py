"""Polish and complete the native-backed Melodia settings WBP through Monolith.

Preserves every UMelodiaSettingsPanelWidget BindWidget name and settings authority.
Adds visual hierarchy, correct child order, and an informative controls page only.
"""
from __future__ import annotations

import json
from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/WBP_MelodiaSettings"
PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise"
SOFT_MG = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment"
DIVIDER = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_DividerScroll"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result)}")
    return result


def ui(action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=ASSET, **arguments)


def names() -> set[str]:
    tree = json.loads(ui("get_widget_tree")["content"][0]["text"])
    queue = [tree["root"]]
    found: set[str] = set()
    for node in queue:
        found.add(node.get("name", ""))
        queue.extend(node.get("children", []))
    return found


def ensure(widget_class: str, name: str, parent: str):
    if name not in names():
        ui("add_widget", widget_class=widget_class, widget_name=name, parent_name=parent, compile=False)


def text(name: str, value: str, size: int, color: str, justification: str = "Left"):
    ui("set_text", widget_name=name, text=value, text_color=color, font_size=size,
       justification=justification, compile=False)
    ui("set_font", widget_name=name, font_size=size, typeface="Regular", compile=False)


def skin_button(name: str):
    for state, tint in (("Normal", "#3B2C49D8"), ("Hovered", "#8F6AA6F5"),
                        ("Pressed", "#4B3659FF"), ("Disabled", "#25202C70")):
        ui("set_brush", widget_name=name, property_name=f"WidgetStyle.{state}",
           texture_path=SOFT_MG, draw_type="Box",
           margin={"left": 0.30, "top": 0.30, "right": 0.30, "bottom": 0.30},
           tint_color=tint, compile=False)


ensure("Image", "SettingsBackdrop", "OverlayRoot")
ensure("Image", "SettingsSurface", "OverlayRoot")
ensure("Image", "SettingsDivider", "OverlayRoot")
# Backgrounds were appended to OverlayRoot; move them behind the existing PanelVBox.
ui("move_widget", widget_name="SettingsBackdrop", new_parent_name="OverlayRoot", slot_index=0, compile=False)
ui("move_widget", widget_name="SettingsSurface", new_parent_name="OverlayRoot", slot_index=1, compile=False)
ui("move_widget", widget_name="SettingsDivider", new_parent_name="OverlayRoot", slot_index=2, compile=False)
ui("set_brush", widget_name="SettingsBackdrop", property_name="Brush", draw_type="Image",
   tint_color="#090715F5", compile=False)
ui("set_brush", widget_name="SettingsSurface", property_name="Brush", texture_path=PARCHMENT,
   draw_type="Image", tint_color="#F4ECE5F5", compile=False)
ui("set_brush", widget_name="SettingsDivider", property_name="Brush", texture_path=DIVIDER,
   draw_type="Image", tint_color="#B99559C8", compile=False)
for image in ("SettingsBackdrop", "SettingsSurface", "SettingsDivider"):
    ui("set_widget_property", widget_name=image, property_name="Visibility", value="HitTestInvisible",
       raw_mode=True, compile=False)

# Correct reading order: title, tabs, content, back.
for child, index in (("TitleText", 0), ("SettingsTabBar", 1), ("ContentSwitcher", 2), ("Btn_SettingsBack", 3)):
    ui("move_widget", widget_name=child, new_parent_name="PanelVBox", slot_index=index, compile=False)

text("TitleText", "SETTINGS · TUNE YOUR EXPERIENCE", 38, "#392D43FF", "Center")
for name, label in (
    ("Label_TabAudio", "AUDIO"),
    ("Label_TabDisplay", "DISPLAY"),
    ("Label_TabAccessibility", "ACCESSIBILITY"),
    ("Label_TabControls", "CONTROLS"),
    ("BtnLabel_SettingsBack", "BACK"),
):
    text(name, label, 17, "#FFF7EEFF", "Center")
for name in ("Btn_TabAudio", "Btn_TabDisplay", "Btn_TabAccessibility", "Btn_TabControls", "Btn_SettingsBack"):
    skin_button(name)

for name, label in (
    ("AudioHeading", "Audio Mix"),
    ("DisplayHeading", "Display & Interface"),
    ("AccessibilityHeading", "Accessibility"),
):
    text(name, label, 27, "#735778FF")
for name, label in (
    ("Label_MasterVolume", "Master Volume"),
    ("Label_MusicVolume", "Music Volume"),
    ("Label_SFXVolume", "Effects Volume"),
    ("Label_UIScale", "Interface Scale · 80%–130%"),
    ("Label_ReduceMotion", "Reduce ornamental motion"),
    ("Label_HighContrast", "High-contrast text"),
    ("Label_MinimalHUD", "Minimal reactive battle HUD"),
):
    text(name, label, 19, "#493C50FF")

# Complete the previously empty Controls tab with authoritative current bindings.
for cls, name in (
    ("TextBlock", "ControlsHeading"),
    ("TextBlock", "ControlsHint"),
    ("TextBlock", "ControlsExplore"),
    ("TextBlock", "ControlsBattle"),
    ("TextBlock", "ControlsConfirm"),
    ("TextBlock", "ControlsGamepadNote"),
):
    ensure(cls, name, "Tab_Controls_Content")
text("ControlsHeading", "Controls", 27, "#735778FF")
text("ControlsHint", "Current compatibility bindings", 17, "#8D688EFF")
text("ControlsExplore", "EXPLORE   F  Interact     E  Menu     Esc  Back", 19, "#493C50FF")
text("ControlsBattle", "BATTLE    J  Attack      K  Skill     I  Item      F  Flee", 19, "#493C50FF")
text("ControlsConfirm", "CONFIRM   Enter / Space", 19, "#493C50FF")
text("ControlsGamepadNote", "Gamepad prompts follow the active input device when CommonInput glyph data is available.",
     17, "#6B5A70FF")
for name in ("ControlsHint", "ControlsExplore", "ControlsBattle", "ControlsConfirm", "ControlsGamepadNote"):
    ui("set_widget_property", widget_name=name, property_name="AutoWrapText", value=True,
       raw_mode=True, compile=False)

compiled = json.loads(ui("compile_widget")["content"][0]["text"])
if compiled.get("error_count", 0) or compiled.get("errors"):
    raise RuntimeError(json.dumps(compiled, indent=2))
invoke("blueprint_query", action="save_asset", asset_path=ASSET)
print(json.dumps({"asset": ASSET, "status": "compiled_and_saved",
                  "errors": compiled.get("error_count", 0),
                  "warnings": compiled.get("warning_count", 0)}, indent=2))
