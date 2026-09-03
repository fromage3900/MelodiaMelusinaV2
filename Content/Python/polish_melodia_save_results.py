"""Polish the populated save/load panel and native battle-results WBP.

Preserves runtime-bound names and gameplay/save authority; presentation only.
"""
from __future__ import annotations

import json
from monolith_mcp_client import call_tool

SAVE = "/Game/Melodia/UI/WBP_SaveLoadPanel"
RESULTS = "/Game/Melodia/UI/WBP_Battle_Results"
PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise"
SOFT_MG = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result)}")
    return result


def ui(asset: str, action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=asset, **arguments)


def anchor(asset: str, name: str, preset: str, offsets: dict, z: int, alignment=None):
    ui(asset, "set_anchor_preset", widget_name=name, preset=preset, compile=False)
    args = {"widget_name": name, "offsets": offsets, "z_order": z, "compile": False}
    if alignment is not None:
        args["alignment"] = alignment
    ui(asset, "set_slot_property", **args)


def text(asset: str, name: str, value: str | None, size: int, color: str, justification="Center"):
    if value is not None:
        ui(asset, "set_text", widget_name=name, text=value, text_color=color, font_size=size,
           justification=justification, compile=False)
    else:
        ui(asset, "set_font", widget_name=name, font_size=size, typeface="Regular", compile=False)


def skin_button(asset: str, name: str):
    for state, tint in (("Normal", "#4A3658E8"), ("Hovered", "#926DA9FF"),
                        ("Pressed", "#382941FF"), ("Disabled", "#25202C70")):
        ui(asset, "set_brush", widget_name=name, property_name=f"WidgetStyle.{state}",
           texture_path=SOFT_MG, draw_type="Box",
           margin={"left": 0.30, "top": 0.30, "right": 0.30, "bottom": 0.30},
           tint_color=tint, compile=False)


def finish(asset: str):
    compiled = json.loads(ui(asset, "compile_widget")["content"][0]["text"])
    if compiled.get("error_count", 0) or compiled.get("errors"):
        raise RuntimeError(f"{asset}: {json.dumps(compiled, indent=2)}")
    invoke("blueprint_query", action="save_asset", asset_path=asset)
    return {"asset": asset, "errors": compiled.get("error_count", 0),
            "warnings": compiled.get("warning_count", 0)}


# Save/load: repair full-screen backdrop and center the existing authoritative slot control.
anchor(SAVE, "Backdrop", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, 0)
ui(SAVE, "set_brush", widget_name="Backdrop", property_name="Brush", texture_path=PARCHMENT,
   draw_type="Image", tint_color="#17121FF2", compile=False)
anchor(SAVE, "SlotPanel", "center", {"left": -300, "top": -230, "right": 600, "bottom": 460}, 3,
       {"x": 0, "y": 0})
text(SAVE, "Title", "MEMORY ARCHIVE", 38, "#FFF4E8FF")
text(SAVE, "SlotDescription", "Choose a resonance to restore", 19, "#D8CADDFF")
text(SAVE, "BtnLabel_LoadSlot0", "LOAD MEMORY I", 20, "#FFF7EEFF")
skin_button(SAVE, "Btn_LoadSlot0")

# Results: fix the 100x30 stretched-border offsets and establish a readable hierarchy.
anchor(RESULTS, "BG_Border", "center", {"left": -340, "top": -330, "right": 680, "bottom": 660}, 0,
       {"x": 0, "y": 0})
ui(RESULTS, "set_brush", widget_name="BG_Border", property_name="Background", texture_path=PARCHMENT,
   draw_type="Box", margin={"left": 0.20, "top": 0.20, "right": 0.20, "bottom": 0.20},
   tint_color="#F5EEE8FA", compile=False)
for cls, name in (("TextBlock", "ResultsKicker"), ("TextBlock", "ResultsTitle")):
    # Add to the existing column only once.
    tree = json.loads(ui(RESULTS, "get_widget_tree")["content"][0]["text"])
    if name not in json.dumps(tree):
        ui(RESULTS, "add_widget", widget_class=cls, widget_name=name,
           parent_name="ResultsColumn", compile=False)
ui(RESULTS, "move_widget", widget_name="ResultsKicker", new_parent_name="ResultsColumn", slot_index=0, compile=False)
ui(RESULTS, "move_widget", widget_name="ResultsTitle", new_parent_name="ResultsColumn", slot_index=1, compile=False)
text(RESULTS, "ResultsKicker", "RESONANCE COMPLETE", 17, "#8D688EFF")
text(RESULTS, "ResultsTitle", "BATTLE VERSE", 34, "#3B3044FF")
text(RESULTS, "TXT_Rank", None, 52, "#735778FF")
for name in ("TXT_Score", "TXT_Perfect", "TXT_Hit", "TXT_Miss", "TXT_Damage", "TXT_MaxCombo"):
    text(RESULTS, name, None, 19, "#493C50FF")

print(json.dumps({"status": "compiled_and_saved", "assets": [finish(SAVE), finish(RESULTS)]}, indent=2))
