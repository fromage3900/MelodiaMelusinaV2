"""
UI tools - UMG Widget Blueprints, Layout Containers, Interactive Controls, and Animations.
"""

import json
from typing import Any
from ..mcp_types import Tool, TextContent

from ..connection import get_connection


def _send_command(command_type: str, params: dict | None = None) -> list[TextContent]:
    """Helper to send command and format response."""
    conn = get_connection()
    if not conn.is_connected:
        conn.connect()
    result = conn.send_command(command_type, params)
    return [TextContent(type="text", text=json.dumps(result.to_dict(), indent=2))]


def get_tools() -> list[Tool]:
    """Get all UI and UMG tools."""
    return [
        Tool(
            name="create_umg_widget_blueprint",
            description="Create a new UMG Widget Blueprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the widget blueprint"},
                    "parent_class": {"type": "string", "description": "Parent class (default: UserWidget)"},
                    "path": {"type": "string", "description": "Content browser path (default: /Game/UI)"}
                },
                "required": ["widget_name"]
            }
        ),
        Tool(
            name="add_text_block_to_widget",
            description="Add a Text Block widget to a UMG Widget Blueprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "text_block_name": {"type": "string", "description": "Name for the Text Block"},
                    "text": {"type": "string", "description": "Initial text content"},
                    "position": {"type": "array", "items": {"type": "number"}, "description": "[X, Y] position"},
                    "size": {"type": "array", "items": {"type": "number"}, "description": "[Width, Height]"},
                    "font_size": {"type": "integer", "description": "Font size in points"},
                    "color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B, A] values 0.0-1.0"}
                },
                "required": ["widget_name", "text_block_name"]
            }
        ),
        Tool(
            name="add_button_to_widget",
            description="Add a Button widget to a UMG Widget Blueprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "button_name": {"type": "string", "description": "Name for the Button"},
                    "text": {"type": "string", "description": "Button text"},
                    "position": {"type": "array", "items": {"type": "number"}, "description": "[X, Y] position"},
                    "size": {"type": "array", "items": {"type": "number"}, "description": "[Width, Height]"},
                    "font_size": {"type": "integer", "description": "Font size"},
                    "color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B, A] text color"},
                    "background_color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B, A] background"}
                },
                "required": ["widget_name", "button_name"]
            }
        ),
        Tool(
            name="add_progress_bar_to_widget",
            description="Add a Progress Bar widget (health bar, rhythm gauge, cooldown meter) to a Widget Blueprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "progress_bar_name": {"type": "string", "description": "Name for the Progress Bar"},
                    "percent": {"type": "number", "description": "Initial fill percentage (0.0 to 1.0, default: 1.0)"},
                    "fill_color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B, A] bar color"},
                    "position": {"type": "array", "items": {"type": "number"}, "description": "[X, Y] position"},
                    "size": {"type": "array", "items": {"type": "number"}, "description": "[Width, Height]"}
                },
                "required": ["widget_name", "progress_bar_name"]
            }
        ),
        Tool(
            name="add_image_to_widget",
            description="Add an Image / Brush widget (portrait, status icon, rhythm marker) to a Widget Blueprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "image_name": {"type": "string", "description": "Name for the Image widget"},
                    "texture_path": {"type": "string", "description": "Path to Texture2D or Material asset"},
                    "tint_color": {"type": "array", "items": {"type": "number"}, "description": "[R, G, B, A] tint color"},
                    "position": {"type": "array", "items": {"type": "number"}, "description": "[X, Y] position"},
                    "size": {"type": "array", "items": {"type": "number"}, "description": "[Width, Height]"}
                },
                "required": ["widget_name", "image_name"]
            }
        ),
        Tool(
            name="add_canvas_panel_slot",
            description="Configure Canvas Panel slot properties (anchors, alignment, layout offsets, z-order) for responsive UI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "child_widget_name": {"type": "string", "description": "Target child widget component name"},
                    "anchors": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[MinX, MinY, MaxX, MaxY] normalized anchors (0.0 to 1.0)"
                    },
                    "alignment": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[AlignX, AlignY] pivot (e.g. [0.5, 0.5] for centered)"
                    },
                    "offsets": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[Left, Top, Right, Bottom] margin offsets"
                    },
                    "z_order": {"type": "integer", "description": "Z-order layer priority"}
                },
                "required": ["widget_name", "child_widget_name"]
            }
        ),
        Tool(
            name="create_widget_animation",
            description="Create a timeline widget animation track (e.g. FadeIn, ComboPulse, DamageFlash).",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "animation_name": {"type": "string", "description": "Name for the animation asset"},
                    "duration": {"type": "number", "description": "Animation duration in seconds (default: 1.0)"},
                    "loop_count": {"type": "integer", "description": "Number of loops (0 = infinite, default: 1)"}
                },
                "required": ["widget_name", "animation_name"]
            }
        ),
        Tool(
            name="add_widget_animation_track",
            description="Add keyframed property tracks to a widget animation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "animation_name": {"type": "string", "description": "Name of the target animation"},
                    "widget_component_name": {"type": "string", "description": "Target widget component"},
                    "property_name": {
                        "type": "string",
                        "description": "Property path (e.g. RenderOpacity, ColorAndOpacity, Transform.Translation, Scale)"
                    },
                    "key_frames": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Array of keyframe dicts with 'time' (float) and 'value'"
                    }
                },
                "required": ["widget_name", "animation_name", "widget_component_name", "property_name"]
            }
        ),
        Tool(
            name="play_widget_animation",
            description="Trigger playback of a widget animation sequence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "animation_name": {"type": "string", "description": "Name of the animation to play"},
                    "start_at_time": {"type": "number", "description": "Start offset in seconds (default: 0.0)"},
                    "num_loops_to_play": {"type": "integer", "description": "Number of loops (default: 1)"},
                    "play_mode": {
                        "type": "string",
                        "description": "Playback mode",
                        "enum": ["Forward", "Reverse", "PingPong"]
                    }
                },
                "required": ["widget_name", "animation_name"]
            }
        ),
        Tool(
            name="bind_widget_event",
            description="Bind an event on a widget component (e.g., button OnClicked). Creates a Component Bound Event node.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "widget_component_name": {"type": "string", "description": "Name of the widget component (e.g., RestartButton)"},
                    "event_name": {"type": "string", "description": "Event to bind (OnClicked, OnPressed, OnReleased, OnHovered, etc.)"}
                },
                "required": ["widget_name", "widget_component_name", "event_name"]
            }
        ),
        Tool(
            name="add_widget_to_viewport",
            description="Add a Widget Blueprint instance to the viewport.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "z_order": {"type": "integer", "description": "Z-order (higher = on top)"}
                },
                "required": ["widget_name"]
            }
        ),
        Tool(
            name="set_text_block_binding",
            description="Set up a property binding for a Text Block widget.",
            inputSchema={
                "type": "object",
                "properties": {
                    "widget_name": {"type": "string", "description": "Name of the Widget Blueprint"},
                    "text_block_name": {"type": "string", "description": "Name of the Text Block"},
                    "binding_property": {"type": "string", "description": "Property to bind to"},
                    "binding_type": {"type": "string", "description": "Type of binding (Text, Visibility, etc.)"}
                },
                "required": ["widget_name", "text_block_name", "binding_property"]
            }
        ),
    ]


TOOL_HANDLERS = {
    "create_umg_widget_blueprint": "create_umg_widget_blueprint",
    "add_text_block_to_widget": "add_text_block_to_widget",
    "add_button_to_widget": "add_button_to_widget",
    "add_progress_bar_to_widget": "add_progress_bar_to_widget",
    "add_image_to_widget": "add_image_to_widget",
    "add_canvas_panel_slot": "add_canvas_panel_slot",
    "create_widget_animation": "create_widget_animation",
    "add_widget_animation_track": "add_widget_animation_track",
    "play_widget_animation": "play_widget_animation",
    "bind_widget_event": "bind_widget_event",
    "add_widget_to_viewport": "add_widget_to_viewport",
    "set_text_block_binding": "set_text_block_binding",
}


async def handle_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle a UI tool call."""
    command_type = TOOL_HANDLERS.get(name)
    if not command_type:
        return [TextContent(type="text", text=f'{{"success": false, "error": "Unknown tool: {name}"}}')]

    return _send_command(command_type, arguments if arguments else None)
