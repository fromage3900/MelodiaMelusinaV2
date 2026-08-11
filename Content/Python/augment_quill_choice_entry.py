"""Augment WBP_MelodiaQuillChoiceEntry with a filigree divider top-strip and styled panels.

Targets only this file; avoids the working set to not collide with Kiro's battle boundaries.
Places a DividerScroll atop the ChoiceButton, anchors ChoiceButton to bottom-of-slot, and
applies the Universal parchment/button surface.
"""
import json
import sys

sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python")
from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/Quill/WBP_MelodiaQuillChoiceEntry"
UNIVERSAL = "/Game/Melodia/UI/Textures/Universal"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(json.dumps(result))
    text = (result.get("content") or [{}])[0].get("text", "") if isinstance(result.get("content"), list) else result.get("text", "")
    return json.loads(text) if text else result


def pp(result):
    return (result.get("initial_text") or "").strip()


def main():
    # preserve existing root/parent (already CanvasPanel root with ChoiceButton+ChoiceText)
    tree = invoke("ui_query", action="get_widget_tree", asset_path=ASSET)

    # ensure filigree divider at the top of the canvas root
    invoke("ui_query", action="add_widget", asset_path=ASSET,
           widget_class="Image", widget_name="FiligreeDivider", parent_name="CanvasPanel", compile=False)
    invoke("ui_query", action="set_anchor_preset", asset_path=ASSET,
           widget_name="FiligreeDivider", preset="top_right", compile=False)
    invoke("ui_query", action="set_slot_property", asset_path=ASSET, widget_name="FiligreeDivider",
           offsets={"left": 0, "top": 0, "right": 0, "bottom": 28}, z_order=5, compile=False)
    invoke("ui_query", action="set_brush", asset_path=ASSET, widget_name="FiligreeDivider",
           property_name="Brush", texture_path=f"{UNIVERSAL}/T_Melodia_Universal_DividerScroll",
           draw_type="Image", tint_color="#8C6C48E8", compile=False)
    invoke("ui_query", action="set_widget_is_variable", asset_path=ASSET, widget_name="FiligreeDivider",
           is_variable=True, compile=False)

    # leave choice button/sticky layout alone (Kiro may still own) but anchor bottom-right for consistency
    # only if the button exists
    names = {n["name"] for n in [tree.get("root", {})] + tree.get("root", {}).get("children", [])}
    names |= {c["name"] for c in tree.get("root", {}).get("children", [{}])[0].get("children", [])}
    if "ChoiceButton" in names:
        invoke("ui_query", action="set_anchor_preset", asset_path=ASSET,
               widget_name="ChoiceButton", preset="bottom_right", compile=False)
        invoke("ui_query", action="set_slot_property", asset_path=ASSET, widget_name="ChoiceButton",
               offsets={"left": 0, "top": -18, "right": 380, "bottom": 52}, z_order=6,
               alignment={"x": 1.0, "y": 1.0}, compile=False)
        invoke("ui_query", action="set_brush", asset_path=ASSET, widget_name="ChoiceButton",
               property_name="WidgetStyle.Normal", texture_path=f"{UNIVERSAL}/T_Melodia_Universal_ParchmentFrame",
               draw_type="Box", margin={"left": 0.2, "top": 0.2, "right": 0.2, "bottom": 0.2},
               tint_color="#725B82F2", compile=False)
        invoke("ui_query", action="set_brush", asset_path=ASSET, widget_name="ChoiceButton",
               property_name="WidgetStyle.Hovered", texture_path=f"{UNIVERSAL}/T_Melodia_Universal_ParchmentFrame",
               draw_type="Box", margin={"left": 0.2, "top": 0.2, "right": 0.2, "bottom": 0.2},
               tint_color="#9B78AAFF", compile=False)
        invoke("ui_query", action="set_brush", asset_path=ASSET, widget_name="ChoiceButton",
               property_name="WidgetStyle.Pressed", texture_path=f"{UNIVERSAL}/T_Melodia_Universal_ParchmentFrame",
               draw_type="Box", margin={"left": 0.2, "top": 0.2, "right": 0.2, "bottom": 0.2},
               tint_color="#584664FF", compile=False)
        invoke("ui_query", action="set_widget_property", asset_path=ASSET, widget_name="ChoiceButton",
               property_name="BackgroundColor", value="#00000000", raw_mode=True, compile=False)

    if "ChoiceText" in names:
        invoke("ui_query", action="set_widget_property", asset_path=ASSET, widget_name="ChoiceText",
               property_name="ColorAndOpacity", value="#FFFFFFFF", raw_mode=True, compile=False)
        invoke("ui_query", action="set_widget_property", asset_path=ASSET, widget_name="ChoiceText",
               property_name="AutoWrapText", value=True, raw_mode=True, compile=False)

    crc = invoke("ui_query", action="compile_widget", asset_path=ASSET)
    if crc.get("error_count"):
        raise RuntimeError(f"compile failed: {crc}")
    invoke("blueprint_query", action="save_asset", asset_path=ASSET)

    # readback
    tree2 = invoke("ui_query", action="get_widget_tree", asset_path=ASSET)

    def count_widgets(node, acc):
        if not isinstance(node, dict):
            return acc
        acc.append(node.get("name"))
        for c in node.get("children", []):
            count_widgets(c, acc)
        return acc

    all_widgets = sorted(filter(None, count_widgets(tree2.get("root", tree2), [])))
    return {
        "status": "authored",
        "asset": ASSET,
        "widget_count": len(all_widgets),
        "widgets": all_widgets,
        "has_filigree_divider": "FiligreeDivider" in all_widgets,
        "errors": crc.get("error_count", 0),
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
    print("DONE")