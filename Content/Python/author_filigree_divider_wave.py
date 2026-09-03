"""Create WBP_MelodiaFiligreeDividerWave — one reusable stretched divider image
purely using the existing universal DividerScroll texture. Self-contained."""
import json
import sys

sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python")
from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/Foundation/WBP_MelodiaFiligreeDividerWave"
UNIVERSAL = "/Game/Melodia/UI/Textures/Universal"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(json.dumps(result))
    text = (result.get("content") or [{}])[0].get("text", "") if isinstance(result.get("content"), list) else result.get("text", "")
    return json.loads(text) if text else result


def main():
    # create the WBP if missing
    existing = call_tool("ui_query", {"action": "get_widget_tree", "asset_path": ASSET})
    if existing.get("isError"):
        invoke("ui_query", action="create_widget_blueprint", save_path=ASSET,
               parent_class="UserWidget", compile=False)

    # clear/add canvas root
    try:
        invoke("ui_query", action="add_widget", asset_path=ASSET,
               widget_class="CanvasPanel", widget_name="CanvasRoot", compile=False)
    except RuntimeError:
        pass

    # stretch image with divider texture
    try:
        invoke("ui_query", action="add_widget", asset_path=ASSET, widget_class="Image",
               widget_name="DividerImage", parent_name="CanvasRoot", compile=False)
    except RuntimeError:
        pass

    invoke("ui_query", action="set_anchor_preset", asset_path=ASSET, widget_name="DividerImage",
           preset="stretch_fill", compile=False)
    invoke("ui_query", action="set_slot_property", asset_path=ASSET, widget_name="DividerImage",
           offsets={"left": 0, "top": 0, "right": 0, "bottom": 0}, z_order=0, compile=False)
    invoke("ui_query", action="set_brush", asset_path=ASSET, widget_name="DividerImage",
           property_name="Brush", texture_path=f"{UNIVERSAL}/T_Melodia_Universal_DividerScroll",
           draw_type="Image", tint_color="#8C6C48E8", compile=False)
    invoke("ui_query", action="set_widget_is_variable", asset_path=ASSET, widget_name="DividerImage",
           is_variable=True, compile=False)

    crc = invoke("ui_query", action="compile_widget", asset_path=ASSET)
    if crc.get("error_count"):
        raise RuntimeError(f"compile failed: {crc}")
    invoke("blueprint_query", action="save_asset", asset_path=ASSET)

    tree2 = invoke("ui_query", action="get_widget_tree", asset_path=ASSET)
    return {"status": "authored", "asset": ASSET, "error_count": crc.get("error_count", 0), "widgets": tree2.get("widget_count")}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
    print("DONE")