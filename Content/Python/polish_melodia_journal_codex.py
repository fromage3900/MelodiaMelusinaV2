"""Make the populated Quest Journal and Skill Codex responsive and Melodia-styled.

Presentation-only. Existing row names/content and runtime population seams are preserved.
"""
from __future__ import annotations

import json
from monolith_mcp_client import call_tool

PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise"
DIVIDER = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_DividerScroll"
CREST = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_CrestBaroque"
ASSETS = ("/Game/Melodia/UI/WBP_QuestJournal", "/Game/Melodia/UI/WBP_SkillCodex")


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result)}")
    return result


def ui(asset: str, action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=asset, **arguments)


def anchor(asset: str, name: str, preset: str, offsets: dict, z: int):
    ui(asset, "set_anchor_preset", widget_name=name, preset=preset, compile=False)
    ui(asset, "set_slot_property", widget_name=name, offsets=offsets, z_order=z, compile=False)


def text(asset: str, name: str, value: str, size: int, color: str, justification: str = "Left"):
    ui(asset, "set_text", widget_name=name, text=value, text_color=color, font_size=size,
       justification=justification, compile=False)
    ui(asset, "set_font", widget_name=name, font_size=size, typeface="Regular", compile=False)


def common_frame(asset: str, title: str):
    anchor(asset, "IMG_ParchmentBG", "stretch_fill", {"left": 42, "top": 34, "right": 42, "bottom": 34}, 0)
    ui(asset, "set_brush", widget_name="IMG_ParchmentBG", property_name="Brush", texture_path=PARCHMENT,
       draw_type="Image", tint_color="#F5EEE8FA", compile=False)
    anchor(asset, "IMG_CrestBaroque", "top_center", {"left": -100, "top": 42, "right": 200, "bottom": 78}, 3)
    ui(asset, "set_brush", widget_name="IMG_CrestBaroque", property_name="Brush", texture_path=CREST,
       draw_type="Image", tint_color="#B99559E0", compile=False)
    anchor(asset, "TXT_Title", "top_center", {"left": -360, "top": 120, "right": 720, "bottom": 58}, 4)
    text(asset, "TXT_Title", title, 38, "#3B3044FF", "Center")
    anchor(asset, "IMG_PersonaAccent", "top_center", {"left": -130, "top": 174, "right": 260, "bottom": 48}, 3)


def finish(asset: str):
    compiled = json.loads(ui(asset, "compile_widget")["content"][0]["text"])
    if compiled.get("error_count", 0) or compiled.get("errors"):
        raise RuntimeError(f"{asset}: {json.dumps(compiled, indent=2)}")
    invoke("blueprint_query", action="save_asset", asset_path=asset)
    return {"asset": asset, "errors": compiled.get("error_count", 0),
            "warnings": compiled.get("warning_count", 0)}


quest = ASSETS[0]
common_frame(quest, "RESONANCE JOURNAL")
anchor(quest, "TXT_ActiveHeader", "top_left", {"left": 110, "top": 226, "right": 690, "bottom": 38}, 4)
anchor(quest, "TXT_CompletedHeader", "top_right", {"left": -800, "top": 226, "right": 690, "bottom": 38}, 4)
text(quest, "TXT_ActiveHeader", "ACTIVE THREADS", 21, "#735778FF")
text(quest, "TXT_CompletedHeader", "COMPLETED VERSES", 21, "#735778FF")
anchor(quest, "SB_ActiveQuests", "stretch_left", {"left": 110, "top": 274, "right": 690, "bottom": 110}, 4)
anchor(quest, "SB_CompletedQuests", "stretch_right", {"left": -800, "top": 274, "right": 110, "bottom": 110}, 4)
for prefix in ("IMG_ActiveBG", "IMG_DoneBG"):
    for index in range(4):
        ui(quest, "set_brush", widget_name=f"{prefix}{index}", property_name="Brush", texture_path=PARCHMENT,
           draw_type="Image", tint_color="#FFFFFFC8" if "Active" in prefix else "#E8DFE6A0", compile=False)
for prefix in ("TXT_ActiveName", "TXT_DoneName"):
    for index in range(4):
        ui(quest, "set_font", widget_name=f"{prefix}{index}", font_size=19, typeface="Regular", compile=False)

codex = ASSETS[1]
common_frame(codex, "SKILL CODEX")
anchor(codex, "SB_SkillList", "stretch_fill", {"left": 150, "top": 230, "right": 150, "bottom": 110}, 4)
for index in range(6):
    ui(codex, "set_brush", widget_name=f"IMG_RowBG{index}", property_name="Brush", texture_path=PARCHMENT,
       draw_type="Image", tint_color="#FFFFFFC8", compile=False)
    ui(codex, "set_font", widget_name=f"TXT_SkillName{index}", font_size=20, typeface="Regular", compile=False)
    ui(codex, "set_font", widget_name=f"TXT_SkillElement{index}", font_size=17, typeface="Regular", compile=False)
    ui(codex, "set_font", widget_name=f"TXT_SkillLevel{index}", font_size=17, typeface="Regular", compile=False)

reports = [finish(quest), finish(codex)]
print(json.dumps({"status": "compiled_and_saved", "assets": reports}, indent=2))
