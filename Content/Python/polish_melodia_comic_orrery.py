"""Polish the existing Comic Orrery navigator through Monolith.

This script preserves every existing sphere/menu widget name and changes only UMG
presentation. DA_OrreryRegistry and runtime handlers remain the sole destination,
unlock, and travel authority. No PPV, material, map, or native source is modified.
"""
from __future__ import annotations

import json

from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/WBP_ComicOrrery"
PARCHMENT = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise"
SOFT_MG = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_Melodia_SoftMG_Parchment"
DIVIDER = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_DividerScroll"
CREST = "/Game/EnvSandbox/Textures/Melodia/GameUI/BatchO/T_Filigree_CrestBaroque"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result)}")
    return result


def ui(action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=ASSET, **arguments)


def names() -> set[str]:
    payload = json.loads(ui("get_widget_tree")["content"][0]["text"])
    result: set[str] = set()

    def visit(node):
        result.add(node.get("name", ""))
        for child in node.get("children", []):
            visit(child)

    visit(payload["root"])
    return result


def ensure(widget_class: str, name: str, parent: str = "Root"):
    if name not in names():
        ui("add_widget", widget_class=widget_class, widget_name=name, parent_name=parent, compile=False)


def anchor(name: str, preset: str, offsets: dict, z: int, alignment: dict | None = None):
    ui("set_anchor_preset", widget_name=name, preset=preset, compile=False)
    args = {"widget_name": name, "offsets": offsets, "z_order": z, "compile": False}
    if alignment is not None:
        args["alignment"] = alignment
    ui("set_slot_property", **args)


def text(name: str, value: str, size: int, color: str, justification: str = "Center"):
    ui("set_text", widget_name=name, text=value, text_color=color, font_size=size,
       justification=justification, compile=False)
    ui("set_font", widget_name=name, font_size=size, typeface="Regular", compile=False)


def skin_button(name: str, compact: bool = False):
    states = (
        ("Normal", "#291F3AA8" if compact else "#4C375CC8"),
        ("Hovered", "#8E68A6F2"),
        ("Pressed", "#3D2C49FF"),
        ("Disabled", "#24202A70"),
    )
    for state, tint in states:
        ui("set_brush", widget_name=name, property_name=f"WidgetStyle.{state}",
           texture_path=SOFT_MG, draw_type="Box",
           margin={"left": 0.30, "top": 0.30, "right": 0.30, "bottom": 0.30},
           tint_color=tint, compile=False)


# New noninteractive atmosphere and framing layers.
for cls, name in (
    ("Image", "CosmicBackdrop"),
    ("Image", "NebulaVeil"),
    ("Image", "OrreryConstellationLineH"),
    ("Image", "OrreryConstellationLineV"),
    ("Image", "OrreryTitleCrest"),
    ("TextBlock", "OrreryKicker"),
    ("TextBlock", "OrreryTitle"),
    ("TextBlock", "OrreryInstruction"),
    ("Image", "OrreryFooterPanel"),
    ("Image", "OrreryFooterDivider"),
):
    ensure(cls, name)

anchor("CosmicBackdrop", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, -20)
anchor("IMG_VoidBG", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, -19)
anchor("NebulaVeil", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, -18)
ui("set_brush", widget_name="CosmicBackdrop", property_name="Brush", draw_type="Image",
   tint_color="#090715FF", compile=False)
ui("set_brush", widget_name="NebulaVeil", property_name="Brush", texture_path=PARCHMENT,
   draw_type="Image", tint_color="#5B42735C", compile=False)
ui("set_widget_property", widget_name="CosmicBackdrop", property_name="Visibility",
   value="HitTestInvisible", raw_mode=True, compile=False)
ui("set_widget_property", widget_name="NebulaVeil", property_name="Visibility",
   value="HitTestInvisible", raw_mode=True, compile=False)

# Responsive title hierarchy.
anchor("OrreryKicker", "top_center", {"left": -360, "top": 42, "right": 720, "bottom": 28}, 20)
anchor("OrreryTitle", "top_center", {"left": -440, "top": 74, "right": 880, "bottom": 74}, 20)
anchor("OrreryTitleCrest", "top_center", {"left": -82, "top": 146, "right": 164, "bottom": 62}, 19)
anchor("OrreryInstruction", "top_center", {"left": -410, "top": 188, "right": 820, "bottom": 34}, 20)
text("OrreryKicker", "THE CELESTIAL ATLAS", 17, "#C5A86AE8")
text("OrreryTitle", "Choose a Resonant World", 46, "#FFF4E8FF")
text("OrreryInstruction", "Follow the constellation · locked worlds remain visible", 19, "#D8CADCEF")
ui("set_brush", widget_name="OrreryTitleCrest", property_name="Brush", texture_path=CREST,
   draw_type="Image", tint_color="#C5A86AE0", compile=False)

# Crossed filigree lines imply the HTML constellation network without a web runtime.
anchor("OrreryConstellationLineH", "center", {"left": -420, "top": -18, "right": 840, "bottom": 36}, 1)
anchor("OrreryConstellationLineV", "center", {"left": -420, "top": -18, "right": 840, "bottom": 36}, 1)
for line in ("OrreryConstellationLineH", "OrreryConstellationLineV"):
    ui("set_brush", widget_name=line, property_name="Brush", texture_path=DIVIDER,
       draw_type="Image", tint_color="#B9955960", compile=False)
ui("set_widget_property", widget_name="OrreryConstellationLineV", property_name="RenderTransform.Angle",
   value="90", raw_mode=True, compile=False)

# Four-world orbit around the existing core. Existing names remain untouched.
anchor("IMG_CoreOrnament", "center", {"left": -92, "top": -92, "right": 184, "bottom": 184}, 8)
for name, offsets in {
    "SPH_Sakura": {"left": -105, "top": -330, "right": 210, "bottom": 210},
    "SPH_Stage": {"left": 270, "top": -105, "right": 210, "bottom": 210},
    "SPH_Celestial": {"left": -105, "top": 145, "right": 210, "bottom": 210},
    "SPH_Village": {"left": -480, "top": -105, "right": 210, "bottom": 210},
}.items():
    anchor(name, "center", offsets, 10)

for key, label in {
    "Sakura": "SAKURA DREAM",
    "Stage": "GRAND STAGE",
    "Celestial": "CELESTIAL NAVE",
    "Village": "MELODIA VILLAGE",
}.items():
    skin_button(f"BTN_SPH_{key}")
    text(f"TXT_SPH_{key}", label, 18, "#FFF7EEFF")
    # Preserve the ring's existing resource; only the button skin/text is standardized.

# Restrained responsive footer for existing meta actions.
anchor("OrreryFooterPanel", "stretch_bottom", {"left": 260, "top": -128, "right": 260, "bottom": 104}, 14)
anchor("OrreryFooterDivider", "stretch_bottom", {"left": 390, "top": -132, "right": 390, "bottom": 24}, 15)
ui("set_brush", widget_name="OrreryFooterPanel", property_name="Brush", texture_path=PARCHMENT,
   draw_type="Image", tint_color="#181321D8", compile=False)
ui("set_brush", widget_name="OrreryFooterDivider", property_name="Brush", texture_path=DIVIDER,
   draw_type="Image", tint_color="#B99559A8", compile=False)
anchor("IMG_PersonaAccent", "bottom_center", {"left": -130, "top": -132, "right": 260, "bottom": 48}, 16)
for name, left in (("BTN_Menu_QuestJournal", -250), ("BTN_Menu_SkillCodex", -75), ("BTN_Menu_Settings", 100)):
    anchor(name, "bottom_center", {"left": left, "top": -86, "right": 150, "bottom": 52}, 18)
    skin_button(name, compact=True)
for name, label in (
    ("TXT_Menu_QuestJournal", "QUESTS"),
    ("TXT_Menu_SkillCodex", "CODEX"),
    ("TXT_Menu_Settings", "SETTINGS"),
):
    text(name, label, 16, "#FFF4E8FF")

result = ui("compile_widget")
compiled = json.loads(result["content"][0]["text"])
if compiled.get("error_count", 0) or compiled.get("errors"):
    raise RuntimeError(json.dumps(compiled, indent=2))
invoke("blueprint_query", action="save_asset", asset_path=ASSET)
print(json.dumps({"asset": ASSET, "status": "compiled_and_saved",
                  "errors": compiled.get("error_count", 0),
                  "warnings": compiled.get("warning_count", 0)}, indent=2))
