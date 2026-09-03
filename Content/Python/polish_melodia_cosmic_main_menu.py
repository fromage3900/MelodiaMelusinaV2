"""Author the production Cosmic Orrery main-menu presentation.

Preserves AOrreryMainMenuGameMode's runtime-bound widget names and native action
ownership. This is presentation-only: no save, travel, registry, map, material,
or native gameplay mutations occur here.
"""
from __future__ import annotations

import json

from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/WBP_MainMenu"
PARCHMENT_NOISE = "/Game/EnvSandbox/Textures/Melodia/GameUI/T_ParchmentNoise"
PARCHMENT_FRAME = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_ParchmentFrame"
CORNER = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CornerBaroque"
DIVIDER = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_DividerScroll"
CREST = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CrestBaroque"
ROSETTE = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_MedallionRosette"

REQUIRED_RUNTIME_WIDGETS = {
    "RootCanvas",
    "Btn_NewGame",
    "Btn_Continue",
    "Btn_LoadGame",
    "Btn_Settings",
    "SaveStateText",
}


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments, timeout=180)
    if result.get("isError"):
        raise RuntimeError(f"{tool} failed: {json.dumps(result, indent=2)}")
    return result


def payload(result):
    return json.loads(result["content"][0]["text"])


def ui(action: str, **arguments):
    return invoke("ui_query", action=action, asset_path=ASSET, **arguments)


def current_tree():
    return payload(ui("get_widget_tree"))


def current_names() -> set[str]:
    tree = current_tree()
    found: set[str] = set()
    queue = [tree["root"]]
    while queue:
        node = queue.pop()
        found.add(node.get("name", ""))
        queue.extend(node.get("children", []))
    return found


def ensure(widget_class: str, name: str, parent: str = "RootCanvas"):
    if name not in current_names():
        ui(
            "add_widget",
            widget_class=widget_class,
            widget_name=name,
            parent_name=parent,
            compile=False,
        )


def anchor(name: str, preset: str, offsets: dict, z: int, alignment: dict | None = None):
    ui("set_anchor_preset", widget_name=name, preset=preset, compile=False)
    params = {"widget_name": name, "offsets": offsets, "z_order": z, "compile": False}
    if alignment is not None:
        params["alignment"] = alignment
    ui("set_slot_property", **params)


def set_visibility(name: str, value: str):
    ui(
        "set_widget_property",
        widget_name=name,
        property_name="Visibility",
        value=value,
        raw_mode=True,
        compile=False,
    )


def set_text(
    name: str,
    value: str,
    size: int,
    color: str,
    justification: str = "Left",
    typeface: str = "Regular",
):
    ui(
        "set_text",
        widget_name=name,
        text=value,
        text_color=color,
        font_size=size,
        justification=justification,
        compile=False,
    )
    ui(
        "set_font",
        widget_name=name,
        font_size=size,
        typeface=typeface,
        compile=False,
    )


def set_image(name: str, texture: str, tint: str, draw_type: str = "Image", margin=None):
    params = {
        "widget_name": name,
        "property_name": "Brush",
        "texture_path": texture,
        "draw_type": draw_type,
        "tint_color": tint,
        "compile": False,
    }
    if margin is not None:
        params["margin"] = margin
    ui("set_brush", **params)


def skin_button(name: str):
    states = (
        ("Normal", "#21162CDE"),
        ("Hovered", "#62466FF7"),
        ("Pressed", "#130D1CFF"),
        ("Disabled", "#17121D78"),
    )
    for state, tint in states:
        ui(
            "set_brush",
            widget_name=name,
            property_name=f"WidgetStyle.{state}",
            texture_path=PARCHMENT_FRAME,
            draw_type="Box",
            margin={"left": 0.28, "top": 0.28, "right": 0.28, "bottom": 0.28},
            tint_color=tint,
            compile=False,
        )

    # Size the action rows through FButtonStyle, never UButtonSlot.Padding. The
    # latter is known to deadlock this UE 5.8 editor build.
    for property_name, padding in (
        ("WidgetStyle.NormalPadding", {"left": 30, "top": 15, "right": 30, "bottom": 15}),
        ("WidgetStyle.PressedPadding", {"left": 30, "top": 17, "right": 30, "bottom": 13}),
    ):
        ui(
            "set_widget_property",
            widget_name=name,
            property_name=property_name,
            value=padding,
            raw_mode=True,
            compile=False,
        )

    # The parent is a VerticalBox, so this is safe inter-row spacing rather than
    # the problematic UButtonSlot mutation above.
    ui(
        "set_slot_property",
        widget_name=name,
        padding={"left": 0, "top": 5, "right": 0, "bottom": 5},
        compile=False,
    )


for widget_class, name in (
    ("Image", "CosmicVoid"),
    ("Image", "NebulaParchment"),
    ("Image", "MenuPanelWash"),
    ("Image", "MenuReadingPanel"),
    ("Image", "MenuCornerTop"),
    ("Image", "MenuCornerBottom"),
    ("Image", "MenuDivider"),
    ("Image", "MenuCrest"),
    ("Image", "MenuWorldRosette"),
    ("TextBlock", "MenuKicker"),
    ("TextBlock", "MenuSubtitle"),
    ("TextBlock", "MenuSectionLabel"),
    ("TextBlock", "MenuWorldKicker"),
    ("TextBlock", "MenuWorldTitle"),
    ("TextBlock", "MenuCornerNote"),
):
    ensure(widget_class, name)

# Preserve the old runtime-bound Background name but remove both legacy full-
# screen artwork layers. The level's authored 3D Cosmic Orrery must remain the
# dominant background rather than being hidden under an opaque UMG rectangle.
anchor("Background", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, -30)
anchor("CosmicVoid", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, -29)
set_visibility("Background", "Collapsed")
set_visibility("CosmicVoid", "Collapsed")

# A very light parchment haze binds UI and world without flattening the scene.
anchor("NebulaParchment", "stretch_fill", {"left": 0, "top": 0, "right": 0, "bottom": 0}, -20)
set_visibility("NebulaParchment", "HitTestInvisible")
set_image(
    "NebulaParchment",
    PARCHMENT_NOISE,
    "#39284224",
    "Box",
    {"left": 0.32, "top": 0.32, "right": 0.32, "bottom": 0.32},
)

# The menu is a single, legible reading surface. It deliberately occupies only
# the left side so the Orrery remains visible and spatially important.
panel_offsets = {"left": 46, "top": 44, "right": 674, "bottom": 44}
anchor("MenuPanelWash", "stretch_left", panel_offsets, 0)
anchor("MenuReadingPanel", "stretch_left", panel_offsets, 1)
set_image(
    "MenuPanelWash",
    PARCHMENT_NOISE,
    "#2A1B35E8",
    "Box",
    {"left": 0.30, "top": 0.30, "right": 0.30, "bottom": 0.30},
)
set_image(
    "MenuReadingPanel",
    PARCHMENT_FRAME,
    "#D6B875E8",
    "Box",
    {"left": 0.31, "top": 0.31, "right": 0.31, "bottom": 0.31},
)

anchor("MenuCornerTop", "top_left", {"left": 60, "top": 58, "right": 126, "bottom": 126}, 2)
anchor("MenuCornerBottom", "bottom_left", {"left": 60, "top": -184, "right": 126, "bottom": 126}, 2)
set_image("MenuCornerTop", CORNER, "#E0C27CD6")
set_image("MenuCornerBottom", CORNER, "#E0C27C8F")

anchor("MenuCrest", "top_left", {"left": 102, "top": 104, "right": 72, "bottom": 72}, 4)
anchor("MenuKicker", "top_left", {"left": 190, "top": 111, "right": 430, "bottom": 24}, 5)
anchor("TitleText", "top_left", {"left": 100, "top": 172, "right": 520, "bottom": 82}, 5)
anchor("MenuSubtitle", "top_left", {"left": 104, "top": 263, "right": 510, "bottom": 54}, 5)
anchor("MenuDivider", "top_left", {"left": 101, "top": 328, "right": 520, "bottom": 35}, 4)
anchor("MenuSectionLabel", "top_left", {"left": 104, "top": 367, "right": 510, "bottom": 22}, 5)

set_image("MenuCrest", CREST, "#E4C982F2")
set_image("MenuDivider", DIVIDER, "#D8B86FC7")
set_text("MenuKicker", "THE COSMIC ORRERY", 16, "#D9BC78FF", "Left", "Bold")
set_text("TitleText", "MELODIA", 68, "#FFF7EDFF", "Left", "Bold")
set_text("MenuSubtitle", "Tune a fractured world back into harmony.", 21, "#DED2E5FF")
set_text("MenuSectionLabel", "CHOOSE YOUR RESONANCE", 14, "#BFA9C9E8", "Left", "Bold")

# Keep all four native callback names and their current hierarchy. Styling and
# padding are presentation-only; AOrreryMainMenuGameMode still clears/binds the
# delegates and controls enabled state at runtime.
anchor(
    "ButtonContainer",
    "center_left",
    {"left": 103, "top": 90, "right": 510, "bottom": 330},
    7,
    {"x": 0, "y": 0.5},
)
for button, label, display in (
    ("Btn_Continue", "BtnLabel_Continue", "CONTINUE"),
    ("Btn_NewGame", "BtnLabel_NewGame", "BEGIN A NEW DREAM"),
    ("Btn_LoadGame", "BtnLabel_LoadGame", "LOAD A MEMORY"),
    ("Btn_Settings", "BtnLabel_Settings", "SETTINGS"),
):
    skin_button(button)
    set_text(label, display, 19, "#FFF8EFFF", "Center", "Bold")

anchor("SaveStateText", "bottom_left", {"left": 104, "top": -150, "right": 510, "bottom": 50}, 8)
set_text("SaveStateText", "Listening for your last resonance…", 16, "#D7CADDEB")

# Right-side typography and watermark provide hierarchy without competing with
# the 3D level. Their low alpha allows the Orrery to remain the hero image.
anchor("MenuWorldRosette", "center_right", {"left": -440, "top": -220, "right": 430, "bottom": 430}, -1)
anchor("MenuWorldKicker", "top_right", {"left": -540, "top": 80, "right": 470, "bottom": 22}, 3)
anchor("MenuWorldTitle", "top_right", {"left": -660, "top": 111, "right": 590, "bottom": 52}, 3)
anchor("MenuCornerNote", "bottom_right", {"left": -610, "top": -72, "right": 550, "bottom": 28}, 8)
set_image("MenuWorldRosette", ROSETTE, "#D7B97320")
set_text("MenuWorldKicker", "A WORLD OUT OF TUNE", 14, "#D6B974A8", "Right", "Bold")
set_text("MenuWorldTitle", "LISTEN · REMEMBER · RESTORE", 21, "#F3E8F0C7", "Right")
set_text("MenuCornerNote", "ENTER  SELECT     ·     ESC  BACK", 14, "#E4D7E09C", "Right", "Bold")

compiled = payload(ui("compile_widget"))
if compiled.get("error_count", 0) or compiled.get("errors"):
    raise RuntimeError(json.dumps(compiled, indent=2))
invoke("blueprint_query", action="save_asset", asset_path=ASSET)

# Mandatory readback: callback names must survive and the production ornament
# set must be serialized before the transaction is considered complete.
readback_names = current_names()
missing_runtime = sorted(REQUIRED_RUNTIME_WIDGETS - readback_names)
expected_presentation = {
    "MenuPanelWash",
    "MenuReadingPanel",
    "MenuCornerTop",
    "MenuCornerBottom",
    "MenuWorldRosette",
    "MenuWorldTitle",
}
missing_presentation = sorted(expected_presentation - readback_names)
if missing_runtime or missing_presentation:
    raise RuntimeError(
        json.dumps(
            {
                "missing_runtime": missing_runtime,
                "missing_presentation": missing_presentation,
            },
            indent=2,
        )
    )

print(
    json.dumps(
        {
            "asset": ASSET,
            "status": "compiled_saved_and_read_back",
            "widget_count": len(readback_names),
            "errors": compiled.get("error_count", 0),
            "warnings": compiled.get("warning_count", 0),
            "runtime_contract": sorted(REQUIRED_RUNTIME_WIDGETS),
        },
        indent=2,
    )
)
