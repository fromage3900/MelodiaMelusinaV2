"""Safe visual pass over the Melodia Quill widgets.

Only named image/text properties are touched. Runtime widget roots, plugin
parents, and Quill event/lifecycle graphs remain unchanged.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mcp_client import monolith

UNIVERSAL = "/Game/Melodia/UI/Textures/Universal"
FONT = "/Game/Melodia/UI/Fonts/F_Melodia_UI"


def call(tool: str, action: str, params: dict) -> str:
    last = ""
    for _ in range(10):
        result = monolith(tool, {"action": action, "params": params})
        if not result.startswith("ERROR:"):
            return result
        last = result
        time.sleep(8)
    raise RuntimeError(last)


def brush(asset: str, widget: str, texture: str, tint: str) -> None:
    result = call("ui_query", "set_brush", {
        "asset_path": asset,
        "widget_name": widget,
        "property_name": "Brush",
        "texture_path": f"{UNIVERSAL}/{texture}",
        "draw_type": "Image",
        "tint_color": tint,
        "compile": True,
    })
    print(f"brush {widget}: {result[:120]}")


def font(asset: str, widget: str, size: int, spacing: int = 40) -> None:
    result = call("ui_query", "set_font", {
        "asset_path": asset,
        "widget_name": widget,
        "font_family": FONT,
        "font_size": size,
        "typeface": "Bold" if size >= 18 else "Regular",
        "letter_spacing": spacing,
        "outline_size": 2,
        "outline_color": "#110C14",
        "compile": True,
    })
    print(f"font {widget}: {result[:120]}")


def main() -> None:
    dialog = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillDialog"
    selection = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillSelection"
    choice = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry"

    brush(dialog, "ParchmentPanel", "T_Melodia_Universal_ParchmentFrame", "1,1,1,0.94")
    brush(dialog, "BaroqueDivider", "T_Melodia_Universal_DividerScroll", "1,0.86,0.48,0.95")
    font(dialog, "SpeakerText", 19, 70)
    font(dialog, "BodyText", 17, 35)
    font(dialog, "AdvanceLabel", 17, 55)

    brush(selection, "SelectionParchment", "T_Melodia_Universal_ParchmentFrame", "1,1,1,0.94")
    font(selection, "PromptText", 19, 60)

    font(choice, "ChoiceText", 17, 45)
    call("ui_query", "compile_widget", {"asset_path": dialog})
    call("ui_query", "compile_widget", {"asset_path": selection})
    call("ui_query", "compile_widget", {"asset_path": choice})
    print("Quill visual pass complete")


if __name__ == "__main__":
    main()
