"""
Audio tools - Sound Cues, MetaSound generation, DSP operators, and interactive audio triggers.
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
    """Get all audio and MetaSound tools."""
    return [
        Tool(
            name="create_sound_cue",
            description="Create a new Sound Cue asset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cue_name": {"type": "string", "description": "Name of the Sound Cue"},
                    "path": {"type": "string", "description": "Content path (default: /Game/Audio)"}
                },
                "required": ["cue_name"]
            }
        ),
        Tool(
            name="add_sound_node_wave_player",
            description="Add a SoundWave player node to a Sound Cue graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cue_name": {"type": "string", "description": "Name of the Sound Cue"},
                    "sound_wave_path": {"type": "string", "description": "Path to Sound Wave asset"},
                    "looping": {"type": "boolean", "description": "Whether wave should loop (default: false)"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["cue_name", "sound_wave_path"]
            }
        ),
        Tool(
            name="add_sound_node_modulator",
            description="Add a pitch and volume modulator node to a Sound Cue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cue_name": {"type": "string", "description": "Name of the Sound Cue"},
                    "pitch_min": {"type": "number", "description": "Minimum pitch multiplier (default: 0.9)"},
                    "pitch_max": {"type": "number", "description": "Maximum pitch multiplier (default: 1.1)"},
                    "volume_min": {"type": "number", "description": "Minimum volume multiplier (default: 0.8)"},
                    "volume_max": {"type": "number", "description": "Maximum volume multiplier (default: 1.0)"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["cue_name"]
            }
        ),
        Tool(
            name="add_sound_node_random",
            description="Add a Random node for selecting among multiple audio variations in a Sound Cue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cue_name": {"type": "string", "description": "Name of the Sound Cue"},
                    "weights": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Weights for randomized input slots"
                    },
                    "randomize_without_replacement": {"type": "boolean", "description": "Avoid playing same sound twice in a row"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["cue_name"]
            }
        ),
        Tool(
            name="add_sound_node_attenuation",
            description="Configure spatial 3D attenuation settings on a Sound Cue.",
            inputSchema={
                "type": "object",
                "properties": {
                    "cue_name": {"type": "string", "description": "Name of the Sound Cue"},
                    "inner_radius": {"type": "number", "description": "Inner radius in unreal units (default: 400.0)"},
                    "outer_radius": {"type": "number", "description": "Outer radius falloff boundary (default: 3000.0)"},
                    "falloff_distance": {"type": "number", "description": "Falloff distance curve (default: 2600.0)"},
                    "spatialization_algorithm": {
                        "type": "string",
                        "description": "Binaural / panning spatialization mode",
                        "enum": ["SPATIALIZATION_Default", "SPATIALIZATION_HRTF"]
                    }
                },
                "required": ["cue_name"]
            }
        ),
        Tool(
            name="create_metasound_source",
            description="Create a procedural MetaSound Source asset for real-time DSP and generative music/SFX.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metasound_name": {"type": "string", "description": "Name of the MetaSound asset"},
                    "output_format": {
                        "type": "string",
                        "description": "Channel format (Mono, Stereo, Quad, 5.1, 7.1)",
                        "enum": ["Mono", "Stereo", "Quad", "5.1", "7.1"]
                    },
                    "path": {"type": "string", "description": "Content path (default: /Game/Audio/MetaSounds)"}
                },
                "required": ["metasound_name"]
            }
        ),
        Tool(
            name="add_metasound_node",
            description="Add an operator, generator, DSP filter, or trigger node to a MetaSound graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metasound_name": {"type": "string", "description": "Name of the MetaSound asset"},
                    "node_type": {
                        "type": "string",
                        "description": "Operator type (SineGenerator, SawGenerator, ADEnvelope, LowPassFilter, HighPassFilter, BPMClock, TriggerRepeat, WaveTable, Mixer)"
                    },
                    "node_name": {"type": "string", "description": "Unique identifier for this node"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    },
                    "default_inputs": {
                        "type": "object",
                        "description": "Dictionary of initial pin values (e.g. {'Frequency': 440.0, 'Cutoff': 1200.0})"
                    }
                },
                "required": ["metasound_name", "node_type", "node_name"]
            }
        ),
        Tool(
            name="connect_metasound_nodes",
            description="Connect audio, trigger, float, or frequency pins between nodes in a MetaSound graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metasound_name": {"type": "string", "description": "Name of the MetaSound asset"},
                    "source_node": {"type": "string", "description": "Source node name (or 'Inputs')"},
                    "source_pin": {"type": "string", "description": "Source output pin name (e.g. Audio, OutTrigger, OutFrequency)"},
                    "target_node": {"type": "string", "description": "Target node name (or 'Outputs')"},
                    "target_pin": {"type": "string", "description": "Target input pin name (e.g. InAudio, InTrigger, Frequency, Cutoff)"}
                },
                "required": ["metasound_name", "source_node", "source_pin", "target_node", "target_pin"]
            }
        ),
        Tool(
            name="set_metasound_parameter",
            description="Declare or update a public input/output parameter in a MetaSound graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "metasound_name": {"type": "string", "description": "Name of the MetaSound asset"},
                    "parameter_name": {"type": "string", "description": "Parameter name (e.g. PitchMultiplier, FilterCutoff, AttackTime)"},
                    "parameter_type": {
                        "type": "string",
                        "description": "Data type (Float, Int32, Boolean, Audio, Trigger, String)",
                        "enum": ["Float", "Int32", "Boolean", "Audio", "Trigger", "String"]
                    },
                    "default_value": {"description": "Initial default value"}
                },
                "required": ["metasound_name", "parameter_name", "parameter_type"]
            }
        ),
        Tool(
            name="play_sound_at_location",
            description="Trigger spatial audio playback of a Sound Cue or MetaSound at a world position.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sound_asset": {"type": "string", "description": "Path or name of Sound Cue or MetaSound"},
                    "location": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y, Z] world location"
                    },
                    "volume_multiplier": {"type": "number", "description": "Volume scalar (default: 1.0)"},
                    "pitch_multiplier": {"type": "number", "description": "Pitch scalar (default: 1.0)"}
                },
                "required": ["sound_asset", "location"]
            }
        )
    ]


TOOL_HANDLERS = {
    "create_sound_cue": "create_sound_cue",
    "add_sound_node_wave_player": "add_sound_node_wave_player",
    "add_sound_node_modulator": "add_sound_node_modulator",
    "add_sound_node_random": "add_sound_node_random",
    "add_sound_node_attenuation": "add_sound_node_attenuation",
    "create_metasound_source": "create_metasound_source",
    "add_metasound_node": "add_metasound_node",
    "connect_metasound_nodes": "connect_metasound_nodes",
    "set_metasound_parameter": "set_metasound_parameter",
    "play_sound_at_location": "play_sound_at_location",
}


async def handle_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle an audio tool call."""
    command_type = TOOL_HANDLERS.get(name)
    if not command_type:
        return [TextContent(type="text", text=f'{{"success": false, "error": "Unknown tool: {name}"}}')]

    return _send_command(command_type, arguments if arguments else None)
