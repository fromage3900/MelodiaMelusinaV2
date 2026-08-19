"""
Animation tools - Animation Blueprint creation, State Machines, BlendSpaces, and Skeletal Controls.
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
    """Get all animation tools."""
    return [
        Tool(
            name="create_animation_blueprint",
            description="Create a new Animation Blueprint targeting a specific Skeleton.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "target_skeleton": {"type": "string", "description": "Path or name of the target Skeleton asset"},
                    "parent_class": {"type": "string", "description": "Parent class (default: AnimInstance)"},
                    "path": {"type": "string", "description": "Content path (default: /Game/Animations)"}
                },
                "required": ["blueprint_name", "target_skeleton"]
            }
        ),
        Tool(
            name="add_anim_state_machine",
            description="Add a State Machine node to an Animation Blueprint's AnimGraph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "state_machine_name": {"type": "string", "description": "Name for the state machine node"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["blueprint_name", "state_machine_name"]
            }
        ),
        Tool(
            name="add_anim_state",
            description="Add an animation state inside a State Machine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "state_machine_name": {"type": "string", "description": "Name of the parent State Machine"},
                    "state_name": {"type": "string", "description": "Name of the state (e.g. Idle, Walk, Run, JumpStart, Falling, Land)"},
                    "animation_asset": {"type": "string", "description": "Path or name of the Animation Sequence or BlendSpace asset"},
                    "is_blend_space": {"type": "boolean", "description": "Whether the animation asset is a BlendSpace"}
                },
                "required": ["blueprint_name", "state_machine_name", "state_name"]
            }
        ),
        Tool(
            name="add_anim_transition",
            description="Add a transition rule between two states in an Animation State Machine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "state_machine_name": {"type": "string", "description": "Name of the parent State Machine"},
                    "source_state": {"type": "string", "description": "Source state name"},
                    "target_state": {"type": "string", "description": "Target state name"},
                    "transition_rule": {"type": "string", "description": "Condition expression or rule name"},
                    "blend_time": {"type": "number", "description": "Crossfade blend duration in seconds (default: 0.2)"},
                    "automatic_rule_based_on_sequence": {"type": "boolean", "description": "Auto transition when sequence finishes"}
                },
                "required": ["blueprint_name", "state_machine_name", "source_state", "target_state"]
            }
        ),
        Tool(
            name="add_blend_space_player",
            description="Add a BlendSpace player evaluator node to the AnimGraph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "blend_space_asset": {"type": "string", "description": "Path to BlendSpace asset (e.g. BS_Melusina_Locomotion)"},
                    "node_name": {"type": "string", "description": "Unique name for the node"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["blueprint_name", "blend_space_asset"]
            }
        ),
        Tool(
            name="add_sequence_player",
            description="Add an Animation Sequence player node to the AnimGraph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "sequence_asset": {"type": "string", "description": "Path to Animation Sequence asset"},
                    "node_name": {"type": "string", "description": "Unique name for the node"},
                    "loop_animation": {"type": "boolean", "description": "Whether sequence should loop (default: true)"},
                    "play_rate": {"type": "number", "description": "Play rate multiplier (default: 1.0)"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["blueprint_name", "sequence_asset"]
            }
        ),
        Tool(
            name="add_bone_transform_node",
            description="Add a Modify Bone / Skeletal Control node for procedural secondary motion and bone physics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "bone_name": {"type": "string", "description": "Target skeletal bone name (e.g. spine_02, tail_01, hair_strand_L)"},
                    "transform_mode": {
                        "type": "string",
                        "description": "Transform mode (ReplaceExisting, Additive, Ignore)",
                        "enum": ["ReplaceExisting", "Additive", "Ignore"]
                    },
                    "translation_space": {"type": "string", "description": "Space (WorldSpace, ComponentSpace, ParentBoneSpace)"},
                    "rotation_space": {"type": "string", "description": "Space (WorldSpace, ComponentSpace, ParentBoneSpace)"},
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["blueprint_name", "bone_name"]
            }
        ),
        Tool(
            name="add_two_bone_ik_node",
            description="Add a Two-Bone IK skeletal control node for procedural ground alignment and foot/hand IK.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "ik_foot_bone": {"type": "string", "description": "IK bone name (e.g. ik_foot_l, ik_foot_r)"},
                    "joint_target": {"type": "string", "description": "Knee / elbow joint target location bone or vector"},
                    "effector_location": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y, Z] effector location offset"
                    },
                    "node_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "[X, Y] position in graph"
                    }
                },
                "required": ["blueprint_name", "ik_foot_bone"]
            }
        ),
        Tool(
            name="add_anim_notify",
            description="Add an Animation Notify trigger to an Animation Sequence asset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sequence_name": {"type": "string", "description": "Path or name of Animation Sequence"},
                    "notify_name": {"type": "string", "description": "Name of notify (e.g. Footstep_L, Footstep_R, CastMagic, AttackHit)"},
                    "trigger_time": {"type": "number", "description": "Time in seconds where notify triggers"},
                    "track_index": {"type": "integer", "description": "Notify track index (default: 0)"}
                },
                "required": ["sequence_name", "notify_name", "trigger_time"]
            }
        ),
        Tool(
            name="connect_anim_nodes",
            description="Connect pose, sync, or value pins between animation nodes in the AnimGraph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "source_node": {"type": "string", "description": "Source node name or GUID"},
                    "source_pin": {"type": "string", "description": "Output pin name (e.g. Pose, Output)"},
                    "target_node": {"type": "string", "description": "Target node name or GUID"},
                    "target_pin": {"type": "string", "description": "Input pin name (e.g. ComponentPose, BasePose, Alpha)"}
                },
                "required": ["blueprint_name", "source_node", "source_pin", "target_node", "target_pin"]
            }
        ),
        Tool(
            name="get_anim_state_machine_states",
            description="Query the list of states and transitions in an Animation State Machine.",
            inputSchema={
                "type": "object",
                "properties": {
                    "blueprint_name": {"type": "string", "description": "Name of the Animation Blueprint"},
                    "state_machine_name": {"type": "string", "description": "Name of the State Machine"}
                },
                "required": ["blueprint_name", "state_machine_name"]
            }
        )
    ]


TOOL_HANDLERS = {
    "create_animation_blueprint": "create_animation_blueprint",
    "add_anim_state_machine": "add_anim_state_machine",
    "add_anim_state": "add_anim_state",
    "add_anim_transition": "add_anim_transition",
    "add_blend_space_player": "add_blend_space_player",
    "add_sequence_player": "add_sequence_player",
    "add_bone_transform_node": "add_bone_transform_node",
    "add_two_bone_ik_node": "add_two_bone_ik_node",
    "add_anim_notify": "add_anim_notify",
    "connect_anim_nodes": "connect_anim_nodes",
    "get_anim_state_machine_states": "get_anim_state_machine_states",
}


async def handle_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle an animation tool call."""
    command_type = TOOL_HANDLERS.get(name)
    if not command_type:
        return [TextContent(type="text", text=f'{{"success": false, "error": "Unknown tool: {name}"}}')]

    return _send_command(command_type, arguments if arguments else None)
