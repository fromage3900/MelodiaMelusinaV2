"""Create WBP_MelodiaFiligreeGradeHalo — a centered grade-halo ring image wrapped
in a mostly-transparent border, using the universal Crest texture."""
import json
import sys

sys.path.insert(0, r"C:\EnvironmentPortfolio\BS_GodFile\Content\Python")
from monolith_mcp_client import call_tool

ASSET = "/Game/Melodia/UI/Foundation/WBP_MelodiaFiligreeGradeHalo"
TEXTURE = "/Game/Melodia/UI/Textures/Universal/T_Melodia_Universal_CrestBaroque"


def invoke(tool: str, **arguments):
    result = call_tool(tool, arguments)
    if result.get("isError"):
        raise RuntimeError(json.dumps(result))
    text = (result.get("content") or [{}])[0].get("text", "") if isinstance(result.get("content"), list) else result.get("text", "")
    return json.loads(text) if text else result


def main():
    existing = call_tool("ui_query", {"action": "get_widget_tree", "asset_path": ASSET})
    if existing.get("isError"):
        invoke("ui_query", action="create_widget_blueprint", save_path=ASSET,
               parent_class="UserWidget", compile=False)

    try:
        invoke("ui_query", action="add_widget", asset_path=ASSET,
               widget_class="CanvasPanel", widget_name="CanvasRoot", compile=False)
    except RuntimeError:
        pass

    try:
        invoke("ui_query", action="add_widget", asset_path=ASSET, widget_class="Image",
               widget_name="GradeHaloImage", parent_name="CanvasRoot", compile=False)
    except RuntimeError:
        pass

    invoke("ui_query", action="set_anchor_preset", asset_path=ASSET, widget_name="GradeHaloImage",
           preset="center", compile=False)
    invoke("ui_query", action="set_slot_property", asset_path=ASSET, widget_name="GradeHaloImage",
           offsets={"left": -128, "top": -128, "right": 256, "bottom": 256}, z_order=0, compile=False)
    invoke("ui_query", action="set_brush", asset_path=ASSET, widget_name="GradeHaloImage",
           property_name="Brush", texture_path=TEXTURE, draw_type="Image", tint_color="#F6D888EE",
           compile=False)
    invoke("ui_query", action="set_widget_is_variable", asset_path=ASSET, widget_name="GradeHaloImage",
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